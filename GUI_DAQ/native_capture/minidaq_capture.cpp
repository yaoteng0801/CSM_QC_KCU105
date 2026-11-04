#include <pcap/pcap.h>

#include <cerrno>
#include <chrono>
#include <csignal>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fcntl.h>
#include <poll.h>
#include <string>
#include <unistd.h>
#include <vector>
#include "isolated_hits.h"

namespace {

constexpr std::size_t kWordSize = 5;
constexpr std::size_t kDataStart = 14;
constexpr std::size_t kPostload = 4;
constexpr std::size_t kFlushThreshold = 256 * 1024;
// Keep each non-blocking pipe write atomic and aligned to a complete word.
constexpr std::size_t kAnalysisWriteSize = 4095;
constexpr int kDefaultSnaplen = 65536;
constexpr int kDefaultTimeoutMs = 100;
constexpr int kDefaultRingBufferBytes = 64 << 20;
constexpr int kDefaultDispatchLimit = 4096;
constexpr int kDefaultStatsIntervalMs = 5000;

volatile std::sig_atomic_t g_stop_requested = 0;

void request_stop(int) {
    g_stop_requested = 1;
}

struct Options {
    std::string device;
    std::string input_pcap;
    std::string filter;
    std::string output;
    std::string isolation_map;
    int snaplen = kDefaultSnaplen;
    int timeout_ms = kDefaultTimeoutMs;
    int ring_buffer_bytes = kDefaultRingBufferBytes;
    int dispatch_limit = kDefaultDispatchLimit;
    int stats_interval_ms = kDefaultStatsIntervalMs;
};

struct CaptureContext {
    IsolatedHitFilter isolation;
    FILE *output = nullptr;
    std::vector<std::uint8_t> batch;
    std::uint64_t total_packets = 0;
    std::uint64_t lost_packets = 0;
    std::uint64_t total_bytes = 0;
    std::uint64_t analysis_dropped_chunks = 0;
    std::uint64_t analysis_dropped_bytes = 0;
    int last_packet = -1;
    bool file_error = false;
};

void print_usage(const char *program) {
    std::fprintf(
        stderr,
        "Usage: %s (--device DEV | --input-pcap FILE) --output FILE [options]\n"
        "Options:\n"
        "  --filter BPF\n"
        "  --isolation-map FILE (remove isolated hits in triggerless events)\n"
        "  --snaplen N\n"
        "  --timeout-ms N\n"
        "  --ring-buffer-bytes N\n"
        "  --dispatch-limit N\n"
        "  --stats-interval-ms N\n",
        program);
}

bool parse_positive_int(const char *text, int &value) {
    char *end = nullptr;
    errno = 0;
    const long parsed = std::strtol(text, &end, 10);
    if (errno != 0 || end == text || *end != '\0' || parsed <= 0 ||
        parsed > 0x7fffffffL) {
        return false;
    }
    value = static_cast<int>(parsed);
    return true;
}

bool parse_options(int argc, char **argv, Options &options) {
    for (int i = 1; i < argc; ++i) {
        const std::string arg(argv[i]);
        if (arg == "--help" || arg == "-h") {
            print_usage(argv[0]);
            std::exit(0);
        }
        if (i + 1 >= argc) {
            std::fprintf(stderr, "MINIDAQ_ERROR missing_value option=%s\n", arg.c_str());
            return false;
        }

        const char *value = argv[++i];
        if (arg == "--device") {
            options.device = value;
        } else if (arg == "--input-pcap") {
            options.input_pcap = value;
        } else if (arg == "--filter") {
            options.filter = value;
        } else if (arg == "--output") {
            options.output = value;
        } else if (arg == "--isolation-map") {
            options.isolation_map = value;
        } else if (arg == "--snaplen") {
            if (!parse_positive_int(value, options.snaplen)) {
                return false;
            }
        } else if (arg == "--timeout-ms") {
            if (!parse_positive_int(value, options.timeout_ms)) {
                return false;
            }
        } else if (arg == "--ring-buffer-bytes") {
            if (!parse_positive_int(value, options.ring_buffer_bytes)) {
                return false;
            }
        } else if (arg == "--dispatch-limit") {
            if (!parse_positive_int(value, options.dispatch_limit)) {
                return false;
            }
        } else if (arg == "--stats-interval-ms") {
            if (!parse_positive_int(value, options.stats_interval_ms)) {
                return false;
            }
        } else {
            std::fprintf(stderr, "MINIDAQ_ERROR unknown_option option=%s\n", arg.c_str());
            return false;
        }
    }

    if (options.output.empty() ||
        (options.device.empty() == options.input_pcap.empty())) {
        return false;
    }
    return true;
}

bool is_empty_word(const std::uint8_t *word) {
    bool idle = true;
    for (std::size_t i = 0; i < kWordSize; ++i) {
        idle = idle && word[i] == 0xff;
    }
    if (idle) {
        return true;
    }
    return word[0] < 0x20 && word[1] == 0 && word[2] == 0 && word[3] == 0 &&
           word[4] == 0;
}

bool write_all(FILE *output, const std::uint8_t *data, std::size_t size) {
    std::size_t written = 0;
    while (written < size) {
        const std::size_t count = std::fwrite(data + written, 1, size - written, output);
        if (count == 0) {
            return false;
        }
        written += count;
    }
    return true;
}

void flush_batch(CaptureContext &context) {
    if (context.batch.empty() || context.file_error) {
        return;
    }

    if (!write_all(context.output, context.batch.data(), context.batch.size())) {
        std::fprintf(
            stderr,
            "MINIDAQ_ERROR file_write_failed errno=%d message=%s\n",
            errno,
            std::strerror(errno));
        std::fflush(stderr);
        context.file_error = true;
        g_stop_requested = 1;
        return;
    }

    std::size_t dropped = 0;
    std::size_t offset = 0;
    while (offset < context.batch.size()) {
        const std::size_t remaining = context.batch.size() - offset;
        const std::size_t write_size =
            remaining < kAnalysisWriteSize ? remaining : kAnalysisWriteSize;
        const ssize_t sent = ::write(
            STDOUT_FILENO,
            context.batch.data() + offset,
            write_size);
        if (sent < 0) {
            if (errno != EAGAIN && errno != EWOULDBLOCK && errno != EPIPE) {
                std::fprintf(
                    stderr,
                    "MINIDAQ_WARN analysis_write_failed errno=%d message=%s\n",
                    errno,
                    std::strerror(errno));
            }
            dropped = context.batch.size() - offset;
            break;
        }
        if (static_cast<std::size_t>(sent) != write_size) {
            // Writes no larger than PIPE_BUF are atomic, so this is defensive.
            dropped = context.batch.size() - offset - static_cast<std::size_t>(sent);
            break;
        }
        offset += write_size;
    }

    if (dropped != 0) {
        ++context.analysis_dropped_chunks;
        context.analysis_dropped_bytes += dropped;
    }
    context.batch.clear();
}

void handle_packet(
    u_char *user,
    const pcap_pkthdr *header,
    const u_char *packet) {
    auto &context = *reinterpret_cast<CaptureContext *>(user);
    const std::size_t caplen = header->caplen;
    if (caplen < kDataStart + kPostload + 2) {
        return;
    }

    const int packet_number =
        (static_cast<int>(packet[caplen - 2]) << 8) |
        static_cast<int>(packet[caplen - 1]);
    if (context.last_packet != -1) {
        const int expected = (context.last_packet + 1) & 0xffff;
        if (packet_number != expected) {
            context.isolation.packet_loss();
            context.lost_packets +=
                static_cast<std::uint16_t>(packet_number - expected);
        }
    }
    context.last_packet = packet_number;
    ++context.total_packets;

    const std::size_t end = caplen - kPostload;
    const auto before = context.batch.size();
    for (std::size_t offset = kDataStart; offset + kWordSize <= end;
         offset += kWordSize) {
        const auto *word = reinterpret_cast<const std::uint8_t *>(packet + offset);
        if (!is_empty_word(word)) context.isolation.feed(word, context.batch);
    }
    context.total_bytes += context.batch.size() - before;
    if (header->len != header->caplen) context.isolation.packet_loss();

    if (context.batch.size() >= kFlushThreshold) {
        flush_batch(context);
    }
}

bool configure_filter(pcap_t *handle, const std::string &filter) {
    if (filter.empty()) {
        return true;
    }

    bpf_program program{};
    if (pcap_compile(
            handle,
            &program,
            filter.c_str(),
            1,
            PCAP_NETMASK_UNKNOWN) < 0) {
        std::fprintf(
            stderr,
            "MINIDAQ_ERROR pcap_compile_failed message=%s\n",
            pcap_geterr(handle));
        return false;
    }
    const int result = pcap_setfilter(handle, &program);
    pcap_freecode(&program);
    if (result < 0) {
        std::fprintf(
            stderr,
            "MINIDAQ_ERROR pcap_setfilter_failed message=%s\n",
            pcap_geterr(handle));
        return false;
    }
    return true;
}

pcap_t *open_live(const Options &options) {
    char error_buffer[PCAP_ERRBUF_SIZE] = {};
    pcap_t *handle = pcap_create(options.device.c_str(), error_buffer);
    if (handle == nullptr) {
        std::fprintf(
            stderr,
            "MINIDAQ_ERROR pcap_create_failed message=%s\n",
            error_buffer);
        return nullptr;
    }

    auto set_option = [handle](int result, const char *name) {
        if (result != 0) {
            std::fprintf(
                stderr,
                "MINIDAQ_ERROR %s_failed message=%s\n",
                name,
                pcap_geterr(handle));
            return false;
        }
        return true;
    };

    if (!set_option(pcap_set_snaplen(handle, options.snaplen), "pcap_set_snaplen") ||
        !set_option(pcap_set_promisc(handle, 1), "pcap_set_promisc") ||
        !set_option(pcap_set_timeout(handle, options.timeout_ms), "pcap_set_timeout") ||
        !set_option(
            pcap_set_buffer_size(handle, options.ring_buffer_bytes),
            "pcap_set_buffer_size")) {
        pcap_close(handle);
        return nullptr;
    }

    const int activate_result = pcap_activate(handle);
    if (activate_result < 0) {
        std::fprintf(
            stderr,
            "MINIDAQ_ERROR pcap_activate_failed result=%d message=%s\n",
            activate_result,
            pcap_geterr(handle));
        pcap_close(handle);
        return nullptr;
    }
    if (activate_result > 0) {
        std::fprintf(
            stderr,
            "MINIDAQ_WARN pcap_activate_warning result=%d message=%s\n",
            activate_result,
            pcap_geterr(handle));
    }
    return handle;
}

void emit_stats(pcap_t *handle, const CaptureContext &context, bool live) {
    unsigned int kernel_received = 0;
    unsigned int kernel_dropped = 0;
    unsigned int interface_dropped = 0;
    pcap_stat stats{};
    if (live && pcap_stats(handle, &stats) == 0) {
        kernel_received = stats.ps_recv;
        kernel_dropped = stats.ps_drop;
        interface_dropped = stats.ps_ifdrop;
    }
    std::fprintf(
        stderr,
        "MINIDAQ_STATS packets=%llu lost=%llu bytes=%llu "
        "analysis_dropped_chunks=%llu analysis_dropped_bytes=%llu "
        "isolated_dropped=%llu filtered_events=%llu preserved_events=%llu filter_rejected_events=%llu "
        "kernel_received=%u kernel_dropped=%u interface_dropped=%u\n",
        static_cast<unsigned long long>(context.total_packets),
        static_cast<unsigned long long>(context.lost_packets),
        static_cast<unsigned long long>(context.total_bytes),
        static_cast<unsigned long long>(context.analysis_dropped_chunks),
        static_cast<unsigned long long>(context.analysis_dropped_bytes),
        static_cast<unsigned long long>(context.isolation.dropped_hits),
        static_cast<unsigned long long>(context.isolation.filtered_events),
        static_cast<unsigned long long>(context.isolation.preserved_events),
        static_cast<unsigned long long>(context.isolation.rejected_events),
        kernel_received,
        kernel_dropped,
        interface_dropped);
    std::fflush(stderr);
}

}  // namespace

int main(int argc, char **argv) {
    Options options;
    if (!parse_options(argc, argv, options)) {
        print_usage(argv[0]);
        return 2;
    }

    CaptureContext context;
    if (!options.isolation_map.empty() && !context.isolation.load(options.isolation_map)) {
        std::fprintf(stderr, "MINIDAQ_ERROR invalid_isolation_map path=%s\n", options.isolation_map.c_str());
        return 2;
    }

    std::signal(SIGINT, request_stop);
    std::signal(SIGTERM, request_stop);
    std::signal(SIGPIPE, SIG_IGN);

    const int stdout_flags = fcntl(STDOUT_FILENO, F_GETFL, 0);
    if (stdout_flags >= 0) {
        fcntl(STDOUT_FILENO, F_SETFL, stdout_flags | O_NONBLOCK);
    }

    const bool live = !options.device.empty();
    pcap_t *handle = nullptr;
    if (live) {
        handle = open_live(options);
    } else {
        char error_buffer[PCAP_ERRBUF_SIZE] = {};
        handle = pcap_open_offline(options.input_pcap.c_str(), error_buffer);
        if (handle == nullptr) {
            std::fprintf(
                stderr,
                "MINIDAQ_ERROR pcap_open_offline_failed message=%s\n",
                error_buffer);
        }
    }
    if (handle == nullptr || !configure_filter(handle, options.filter)) {
        if (handle != nullptr) {
            pcap_close(handle);
        }
        return 1;
    }

    context.batch.reserve(kFlushThreshold + 4096);
    context.output = std::fopen(options.output.c_str(), "wb");
    if (context.output == nullptr) {
        std::fprintf(
            stderr,
            "MINIDAQ_ERROR output_open_failed errno=%d message=%s path=%s\n",
            errno,
            std::strerror(errno),
            options.output.c_str());
        pcap_close(handle);
        return 1;
    }
    std::vector<char> file_buffer(4 * 1024 * 1024);
    std::setvbuf(context.output, file_buffer.data(), _IOFBF, file_buffer.size());

    std::fprintf(
        stderr,
        "MINIDAQ_STATUS started source=%s output=%s\n",
        live ? options.device.c_str() : options.input_pcap.c_str(),
        options.output.c_str());
    std::fflush(stderr);

    auto last_stats = std::chrono::steady_clock::now();
    const int selectable_fd = live ? pcap_get_selectable_fd(handle) : -1;
    int exit_code = 0;
    while (!g_stop_requested && !context.file_error) {
        if (selectable_fd >= 0) {
            pollfd descriptor{selectable_fd, POLLIN, 0};
            const int poll_result = poll(&descriptor, 1, options.timeout_ms);
            if (poll_result < 0) {
                if (errno == EINTR) {
                    continue;
                }
                std::fprintf(
                    stderr,
                    "MINIDAQ_ERROR poll_failed errno=%d message=%s\n",
                    errno,
                    std::strerror(errno));
                exit_code = 1;
                break;
            }
            if (poll_result == 0) {
                const auto now = std::chrono::steady_clock::now();
                if (std::chrono::duration_cast<std::chrono::milliseconds>(
                        now - last_stats)
                        .count() >= options.stats_interval_ms) {
                    emit_stats(handle, context, live);
                    last_stats = now;
                }
                continue;
            }
        }

        const int result = pcap_dispatch(
            handle,
            options.dispatch_limit,
            handle_packet,
            reinterpret_cast<u_char *>(&context));
        flush_batch(context);

        if (result < 0) {
            if (result != PCAP_ERROR_BREAK) {
                std::fprintf(
                    stderr,
                    "MINIDAQ_ERROR pcap_dispatch_failed message=%s\n",
                    pcap_geterr(handle));
                exit_code = 1;
            }
            break;
        }
        if (!live && result == 0) {
            break;
        }

        const auto now = std::chrono::steady_clock::now();
        if (std::chrono::duration_cast<std::chrono::milliseconds>(now - last_stats)
                .count() >= options.stats_interval_ms) {
            emit_stats(handle, context, live);
            last_stats = now;
        }
    }

    const auto before = context.batch.size();
    context.isolation.finish(context.batch);
    context.total_bytes += context.batch.size() - before;
    flush_batch(context);
    if (std::fflush(context.output) != 0) {
        std::fprintf(
            stderr,
            "MINIDAQ_ERROR file_flush_failed errno=%d message=%s\n",
            errno,
            std::strerror(errno));
        exit_code = 1;
    }
    if (std::fclose(context.output) != 0) {
        std::fprintf(
            stderr,
            "MINIDAQ_ERROR file_close_failed errno=%d message=%s\n",
            errno,
            std::strerror(errno));
        exit_code = 1;
    }

    emit_stats(handle, context, live);
    pcap_close(handle);
    if (context.file_error) {
        exit_code = 1;
    }
    std::fprintf(stderr, "MINIDAQ_STATUS stopped exit_code=%d\n", exit_code);
    std::fflush(stderr);
    return exit_code;
}
