#include <pcap/pcap.h>

#include <arpa/inet.h>
#include <cerrno>
#include <csignal>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <poll.h>
#include <string>
#include <unistd.h>
#include <vector>

namespace {

constexpr int kSnaplen = 65535;
constexpr int kCaptureTimeoutMs = 20;
constexpr int kPollTimeoutMs = 100;
constexpr std::size_t kMaximumFrameBytes = 65535;
constexpr const char *kAckFilter =
    "(ether proto 0x88b5 or ether proto 0x88b6) and "
    "ether src 02:00:00:c7:05:01";

volatile std::sig_atomic_t g_stop_requested = 0;

void request_stop(int) {
    g_stop_requested = 1;
}

struct Options {
    std::string device;
    bool self_test = false;
};

void print_usage(const char *program) {
    std::fprintf(
        stderr,
        "Usage: %s (--device DEV | --self-test)\n",
        program);
}

bool parse_options(int argc, char **argv, Options &options) {
    for (int index = 1; index < argc; ++index) {
        const std::string argument(argv[index]);
        if (argument == "--help" || argument == "-h") {
            print_usage(argv[0]);
            std::exit(0);
        }
        if (argument == "--self-test") {
            options.self_test = true;
            continue;
        }
        if (argument != "--device" || index + 1 >= argc) {
            std::fprintf(
                stderr,
                "MINIDAQ_ETH_ERROR invalid_option value=%s\n",
                argument.c_str());
            return false;
        }
        options.device = argv[++index];
    }
    if (options.self_test == !options.device.empty()) {
        std::fprintf(
            stderr,
            "MINIDAQ_ETH_ERROR select_exactly_one_mode\n");
        return false;
    }
    return true;
}

bool run_self_test() {
    // Compile the production ACK filter against an offline Ethernet capture
    // handle. This verifies the executable, libpcap linkage, Ethernet link type,
    // and filter expression without opening an interface or sending a frame.
    pcap_t *handle = pcap_open_dead(DLT_EN10MB, kSnaplen);
    if (handle == nullptr) {
        std::fprintf(stderr, "MINIDAQ_ETH_ERROR self_test_open_dead_failed\n");
        return false;
    }

    bpf_program program{};
    const int compile_result = pcap_compile(
        handle,
        &program,
        kAckFilter,
        1,
        PCAP_NETMASK_UNKNOWN);
    if (compile_result < 0) {
        std::fprintf(
            stderr,
            "MINIDAQ_ETH_ERROR self_test_filter_failed message=%s\n",
            pcap_geterr(handle));
        pcap_close(handle);
        return false;
    }

    pcap_freecode(&program);
    pcap_close(handle);

    // The stdin/stdout protocol prefixes every frame with a network-order
    // 32-bit length. Verify that conversion independently of host endianness.
    constexpr std::uint32_t test_length = 1408;
    if (ntohl(htonl(test_length)) != test_length) {
        std::fprintf(stderr, "MINIDAQ_ETH_ERROR self_test_length_failed\n");
        return false;
    }

    std::fprintf(stderr, "MINIDAQ_ETH_STATUS self_test_passed\n");
    return true;
}

bool write_fd_all(int fd, const void *data, std::size_t size) {
    const auto *bytes = static_cast<const std::uint8_t *>(data);
    std::size_t offset = 0;
    while (offset < size) {
        const ssize_t count = ::write(fd, bytes + offset, size - offset);
        if (count > 0) {
            offset += static_cast<std::size_t>(count);
            continue;
        }
        if (count < 0 && errno == EINTR) {
            continue;
        }
        return false;
    }
    return true;
}

struct CaptureOutput {
    bool failed = false;
};

void forward_packet(
    u_char *user,
    const pcap_pkthdr *header,
    const u_char *packet) {
    auto &output = *reinterpret_cast<CaptureOutput *>(user);
    if (header->caplen < 14 || header->caplen > kMaximumFrameBytes) {
        return;
    }

    const std::uint32_t network_length = htonl(header->caplen);
    if (!write_fd_all(STDOUT_FILENO, &network_length, sizeof(network_length)) ||
        !write_fd_all(STDOUT_FILENO, packet, header->caplen)) {
        std::fprintf(
            stderr,
            "MINIDAQ_ETH_ERROR stdout_write_failed errno=%d message=%s\n",
            errno,
            std::strerror(errno));
        std::fflush(stderr);
        output.failed = true;
        g_stop_requested = 1;
    }
}

bool configure_filter(pcap_t *handle) {
    bpf_program program{};
    if (pcap_compile(
            handle,
            &program,
            kAckFilter,
            1,
            PCAP_NETMASK_UNKNOWN) < 0) {
        std::fprintf(
            stderr,
            "MINIDAQ_ETH_ERROR pcap_compile_failed message=%s\n",
            pcap_geterr(handle));
        return false;
    }
    const int result = pcap_setfilter(handle, &program);
    pcap_freecode(&program);
    if (result < 0) {
        std::fprintf(
            stderr,
            "MINIDAQ_ETH_ERROR pcap_setfilter_failed message=%s\n",
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
            "MINIDAQ_ETH_ERROR pcap_create_failed message=%s\n",
            error_buffer);
        return nullptr;
    }

    auto require_option = [handle](int result, const char *name) {
        if (result == 0) {
            return true;
        }
        std::fprintf(
            stderr,
            "MINIDAQ_ETH_ERROR %s_failed message=%s\n",
            name,
            pcap_geterr(handle));
        return false;
    };

    if (!require_option(pcap_set_snaplen(handle, kSnaplen), "pcap_set_snaplen") ||
        !require_option(pcap_set_promisc(handle, 1), "pcap_set_promisc") ||
        !require_option(
            pcap_set_timeout(handle, kCaptureTimeoutMs),
            "pcap_set_timeout") ||
        !require_option(
            pcap_set_immediate_mode(handle, 1),
            "pcap_set_immediate_mode")) {
        pcap_close(handle);
        return nullptr;
    }

    const int activate_result = pcap_activate(handle);
    if (activate_result < 0) {
        std::fprintf(
            stderr,
            "MINIDAQ_ETH_ERROR pcap_activate_failed result=%d message=%s\n",
            activate_result,
            pcap_geterr(handle));
        pcap_close(handle);
        return nullptr;
    }
    if (activate_result > 0) {
        std::fprintf(
            stderr,
            "MINIDAQ_ETH_WARN pcap_activate_warning result=%d message=%s\n",
            activate_result,
            pcap_geterr(handle));
    }

    char nonblock_error[PCAP_ERRBUF_SIZE] = {};
    if (pcap_setnonblock(handle, 1, nonblock_error) < 0) {
        std::fprintf(
            stderr,
            "MINIDAQ_ETH_ERROR pcap_setnonblock_failed message=%s\n",
            nonblock_error);
        pcap_close(handle);
        return nullptr;
    }

    if (!configure_filter(handle)) {
        pcap_close(handle);
        return nullptr;
    }
    return handle;
}

bool inject_complete_frames(
    pcap_t *handle,
    std::vector<std::uint8_t> &input_buffer) {
    while (input_buffer.size() >= sizeof(std::uint32_t)) {
        std::uint32_t network_length = 0;
        std::memcpy(
            &network_length,
            input_buffer.data(),
            sizeof(network_length));
        const std::size_t frame_length = ntohl(network_length);
        if (frame_length < 14 || frame_length > kMaximumFrameBytes) {
            std::fprintf(
                stderr,
                "MINIDAQ_ETH_ERROR invalid_frame_length value=%zu\n",
                frame_length);
            return false;
        }

        const std::size_t record_length =
            sizeof(std::uint32_t) + frame_length;
        if (input_buffer.size() < record_length) {
            return true;
        }

        const std::uint8_t *frame =
            input_buffer.data() + sizeof(std::uint32_t);
        const int injected = pcap_inject(handle, frame, frame_length);
        if (injected < 0 || static_cast<std::size_t>(injected) != frame_length) {
            std::fprintf(
                stderr,
                "MINIDAQ_ETH_ERROR pcap_inject_failed sent=%d expected=%zu "
                "message=%s\n",
                injected,
                frame_length,
                pcap_geterr(handle));
            return false;
        }

        input_buffer.erase(
            input_buffer.begin(),
            input_buffer.begin() + static_cast<std::ptrdiff_t>(record_length));
    }
    return true;
}

}  // namespace

int main(int argc, char **argv) {
    Options options;
    if (!parse_options(argc, argv, options)) {
        print_usage(argv[0]);
        return 2;
    }

    if (options.self_test) {
        return run_self_test() ? 0 : 1;
    }

    std::signal(SIGINT, request_stop);
    std::signal(SIGTERM, request_stop);
    std::signal(SIGPIPE, SIG_IGN);

    pcap_t *handle = open_live(options);
    if (handle == nullptr) {
        return 1;
    }

    std::fprintf(
        stderr,
        "MINIDAQ_ETH_STATUS started device=%s\n",
        options.device.c_str());
    std::fflush(stderr);

    const int pcap_fd = pcap_get_selectable_fd(handle);
    std::vector<std::uint8_t> input_buffer;
    input_buffer.reserve(4096);
    CaptureOutput output;
    int exit_code = 0;

    while (!g_stop_requested && !output.failed) {
        pollfd descriptors[2] = {
            {STDIN_FILENO, POLLIN | POLLHUP, 0},
            {
                pcap_fd,
                static_cast<short>(pcap_fd >= 0 ? POLLIN : 0),
                0,
            },
        };
        const nfds_t descriptor_count = pcap_fd >= 0 ? 2 : 1;
        const int poll_result =
            poll(descriptors, descriptor_count, kPollTimeoutMs);
        if (poll_result < 0) {
            if (errno == EINTR) {
                continue;
            }
            std::fprintf(
                stderr,
                "MINIDAQ_ETH_ERROR poll_failed errno=%d message=%s\n",
                errno,
                std::strerror(errno));
            exit_code = 1;
            break;
        }

        if (descriptors[0].revents & POLLIN) {
            std::uint8_t block[4096];
            const ssize_t count = read(STDIN_FILENO, block, sizeof(block));
            if (count > 0) {
                input_buffer.insert(input_buffer.end(), block, block + count);
                if (!inject_complete_frames(handle, input_buffer)) {
                    exit_code = 1;
                    break;
                }
            } else if (count == 0) {
                break;
            } else if (errno != EINTR && errno != EAGAIN) {
                std::fprintf(
                    stderr,
                    "MINIDAQ_ETH_ERROR stdin_read_failed errno=%d message=%s\n",
                    errno,
                    std::strerror(errno));
                exit_code = 1;
                break;
            }
        }
        if (descriptors[0].revents & (POLLHUP | POLLERR | POLLNVAL)) {
            break;
        }

        if (pcap_fd < 0 || (descriptors[1].revents & POLLIN)) {
            const int dispatch_result =
                pcap_dispatch(handle, -1, forward_packet,
                              reinterpret_cast<u_char *>(&output));
            if (dispatch_result < 0) {
                std::fprintf(
                    stderr,
                    "MINIDAQ_ETH_ERROR pcap_dispatch_failed message=%s\n",
                    pcap_geterr(handle));
                exit_code = 1;
                break;
            }
        }
    }

    pcap_close(handle);
    std::fprintf(stderr, "MINIDAQ_ETH_STATUS stopped\n");
    std::fflush(stderr);
    return exit_code;
}
