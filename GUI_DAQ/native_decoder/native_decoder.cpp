#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <algorithm>
#include <cstdint>
#include <cstring>
#include <map>
#include <mutex>
#include <optional>
#include <set>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

namespace py = pybind11;

namespace {

constexpr int kWordSize = 5;
constexpr int kMaxIssuesPerBatch = 100;
constexpr int kMaxChambers = 2;
constexpr int kEventHitCountMax = 20;
constexpr int kEventHitCountBins = kEventHitCountMax + 2;

struct Hit {
    int csmid = 0;
    int tdcid = 0;
    int channel = 0;
    int mode = 0;
    int ledge = 0;
    int width = 0;
};

struct CompletedEvent {
    int event_id20 = 0;
    int event_id12 = 0;
    int rd_bank_sel = 0;
    int trigger_count = 0;
    int hit_count_expected = 0;
    std::optional<int> trigger_ledge;
    int trigger_overflow = 0;
    int tdc_header_count = 0;
    int tdc_trailer_count = 0;
    int header_count_error = 0;
    int trailer_count_error = 0;
    std::vector<Hit> hits;
};

template <typename T>
py::array_t<T> copy_array(const std::vector<T> &source, std::vector<py::ssize_t> shape) {
    py::array_t<T> output(shape);
    std::memcpy(output.mutable_data(), source.data(), source.size() * sizeof(T));
    return output;
}

class NativeDecoder {
  public:
    NativeDecoder(
        int acquisition_mode,
        int noise_test_mode,
        int max_tdcs,
        int max_channels,
        std::vector<int> tdc_chamber_ids,
        int adc_bins,
        int tdc_bins,
        int tdc_shift,
        int ch_tdc_bins,
        int ch_tdc_shift,
        double tdc_min_ns,
        double tdc_max_ns,
        double ch_tdc_min_ns,
        double ch_tdc_max_ns,
        int decode_error_stop_threshold)
        : acquisition_mode_(acquisition_mode),
          noise_test_mode_(noise_test_mode),
          raw_hit_mode_((noise_test_mode & 0x1) != 0),
          max_tdcs_(max_tdcs),
          max_channels_(max_channels),
          tdc_chamber_ids_(std::move(tdc_chamber_ids)),
          adc_bins_(adc_bins),
          tdc_bins_(tdc_bins),
          tdc_shift_(tdc_shift),
          ch_adc_bins_(adc_bins),
          ch_tdc_bins_(ch_tdc_bins),
          ch_tdc_shift_(ch_tdc_shift),
          tdc_min_ns_(tdc_min_ns),
          tdc_max_ns_(tdc_max_ns),
          ch_tdc_min_ns_(ch_tdc_min_ns),
          ch_tdc_max_ns_(ch_tdc_max_ns),
          decode_error_stop_threshold_(decode_error_stop_threshold),
          tdc_min_count_(static_cast<int>(tdc_min_ns / 0.78125 + 0.5)),
          ch_tdc_min_count_(static_cast<int>(ch_tdc_min_ns / 0.78125 + 0.5)),
          adc_(static_cast<std::size_t>(max_tdcs) * adc_bins),
          tdc_(static_cast<std::size_t>(max_tdcs) * tdc_bins),
          adc_ch_(static_cast<std::size_t>(max_tdcs) * max_channels * adc_bins),
          tdc_ch_(static_cast<std::size_t>(max_tdcs) * max_channels * ch_tdc_bins),
          hit_ch_all_(static_cast<std::size_t>(max_tdcs) * max_channels),
          event_hit_count_hist_(
              static_cast<std::size_t>(kMaxChambers) * kEventHitCountBins),
          overflow_(max_tdcs),
          decode_errors_(max_tdcs),
          noise_total_(static_cast<std::size_t>(max_tdcs) * max_channels),
          noise_rate_(static_cast<std::size_t>(max_tdcs) * max_channels),
          noise_prev_total_(static_cast<std::size_t>(max_tdcs) * max_channels),
          noise_prev_seconds_(static_cast<std::size_t>(max_tdcs) * max_channels),
          noise_decode_error_count_(max_tdcs),
          noise_invalid_channel_count_(max_tdcs) {
        tdc_chamber_ids_.resize(static_cast<std::size_t>(max_tdcs_), -1);
    }

    py::dict process(
        py::bytes input,
        int max_completed_events,
        int min_event_hits) {
        const std::string bytes = input;
        std::vector<CompletedEvent> events;
        std::vector<std::string> issues;
        bool limit_exceeded = false;
        {
            py::gil_scoped_release release;
            std::lock_guard<std::mutex> lock(mutex_);
            process_bytes(bytes, events, issues, limit_exceeded);
        }

        py::list py_events;
        const int minimum_hits = std::max(0, min_event_hits);
        std::size_t eligible_events = 0;
        std::size_t converted_events = 0;
        for (const auto &event : events) {
            if (event.hit_count_expected < minimum_hits) {
                continue;
            }
            ++eligible_events;
            if (
                max_completed_events >= 0
                && converted_events >= static_cast<std::size_t>(max_completed_events)) {
                continue;
            }
            py::dict out;
            out["event_id20"] = event.event_id20;
            out["event_id12"] = event.event_id12;
            out["chamber_id"] = acquisition_mode_ == 1
                ? ((event.event_id20 >> 19) & 0x1)
                : 0;
            out["chamber_event_id"] = acquisition_mode_ == 1
                ? (event.event_id20 & 0x7ffff)
                : event.event_id20;
            out["rd_bank_sel"] = event.rd_bank_sel;
            out["trigger_count"] = event.trigger_count;
            out["hit_count_expected"] = event.hit_count_expected;
            out["trigger_ledge"] = event.trigger_ledge.has_value()
                ? py::cast(*event.trigger_ledge)
                : py::none();
            out["trigger_overflow"] = event.trigger_overflow;
            out["tdc_header_count"] = event.tdc_header_count;
            out["tdc_trailer_count"] = event.tdc_trailer_count;
            out["header_count_error"] = event.header_count_error;
            out["trailer_count_error"] = event.trailer_count_error;

            py::list hits;
            for (const auto &hit : event.hits) {
                hits.append(py::make_tuple(
                    hit.csmid,
                    hit.tdcid,
                    hit.channel,
                    hit.mode,
                    hit.ledge,
                    hit.width));
            }
            out["hits"] = std::move(hits);
            py_events.append(std::move(out));
            ++converted_events;
        }

        py::dict result;
        result["events"] = std::move(py_events);
        result["completed_events_total"] = eligible_events;
        result["issues"] = issues;
        result["decode_error_limit_exceeded"] = limit_exceeded;
        result["decode_error_total"] = decode_error_total_;
        return result;
    }

    py::dict snapshot(py::object requested_fields) const {
        const bool copy_all = requested_fields.is_none();
        std::set<std::string> requested;
        if (!copy_all) {
            const auto fields = requested_fields.cast<std::vector<std::string>>();
            requested.insert(fields.begin(), fields.end());
        }
        const auto wants = [&](const std::string &field) {
            return copy_all || requested.count(field) != 0;
        };

        std::lock_guard<std::mutex> lock(mutex_);
        py::dict out;
        out["adc_hist"] = py::none();
        out["tdc_hist"] = py::none();
        out["adc_ch_hist"] = py::none();
        out["tdc_ch_hist"] = py::none();
        out["raw_hit_ch_count"] = py::none();
        out["event_hit_count_hist"] = py::none();
        out["noise_counter_total"] = py::none();
        out["noise_counter_rate"] = py::none();

        if (wants("adc")) {
            out["adc_hist"] = copy_array(adc_, {max_tdcs_, adc_bins_});
        }
        if (wants("tdc")) {
            out["tdc_hist"] = copy_array(tdc_, {max_tdcs_, tdc_bins_});
        }
        if (wants("adc_ch")) {
            out["adc_ch_hist"] =
                copy_array(adc_ch_, {max_tdcs_, max_channels_, ch_adc_bins_});
        }
        if (wants("tdc_ch")) {
            out["tdc_ch_hist"] =
                copy_array(tdc_ch_, {max_tdcs_, max_channels_, ch_tdc_bins_});
        }
        if (wants("ch_hits")) {
            out["raw_hit_ch_count"] =
                copy_array(hit_ch_all_, {max_tdcs_, max_channels_});
            out["noise_counter_total"] =
                copy_array(noise_total_, {max_tdcs_, max_channels_});
            out["noise_counter_rate"] =
                copy_array(noise_rate_, {max_tdcs_, max_channels_});
        }
        if (wants("event_hits")) {
            out["event_hit_count_hist"] = copy_array(
                event_hit_count_hist_, {kMaxChambers, kEventHitCountBins});
        }
        out["overflow_cnt"] = copy_array(overflow_, {max_tdcs_});
        out["decode_err_cnt"] = copy_array(decode_errors_, {max_tdcs_});
        out["noise_decode_error_count"] =
            copy_array(noise_decode_error_count_, {max_tdcs_});
        out["noise_invalid_channel_count"] =
            copy_array(noise_invalid_channel_count_, {max_tdcs_});

        out["headers"] = headers_;
        out["events_fifoA"] = events_fifo_a_;
        out["events_fifoB"] = events_fifo_b_;
        out["trailers"] = trailers_;
        out["triggers"] = triggers_;
        out["hits_total"] = hits_total_;
        out["valid_events"] = valid_events_;
        out["decode_error_total"] = decode_error_total_;
        out["err_event_id"] = err_event_id_;
        out["err_hit_count"] = err_hit_count_;
        out["err_missing_trailer"] = err_missing_trailer_;
        out["err_missing_header"] = err_missing_header_;
        out["abort_burst"] = abort_burst_;
        out["abort_watchdog"] = abort_watchdog_;
        out["noise_headers"] = noise_headers_;
        out["noise_counters"] = noise_counters_;
        out["noise_error_words"] = noise_error_words_;
        out["noise_trailers"] = noise_trailers_;
        out["noise_last_seconds"] = noise_last_seconds_;
        out["noise_last_total"] = noise_last_total_;

        py::list watchdog_types;
        static const std::vector<std::string> watchdog_order = {
            "IDLE",
            "TRIG_ONLY",
            "START_EVENT",
            "CAPTURE_PRE",
            "SEND_HEAD",
            "FLUSH_BUF",
            "STREAM_LIVE",
            "SEND_TRAIL",
            "ABORT_MARK",
            "ABORT_TRAIL",
            "ABORT_CLEAN",
            "legacy/unknown",
        };
        for (const auto &name : watchdog_order) {
            const auto found = abort_watchdog_types_.find(name);
            if (found != abort_watchdog_types_.end() && found->second != 0) {
                watchdog_types.append(py::make_tuple(found->first, found->second));
            }
        }
        out["abort_watchdog_types"] = std::move(watchdog_types);
        return out;
    }

  private:
    static std::uint64_t read_word(const char *data) {
        std::uint64_t value = 0;
        for (int i = 0; i < kWordSize; ++i) {
            value = (value << 8) | static_cast<unsigned char>(data[i]);
        }
        return value;
    }

    static int tdc_id(std::uint64_t word) {
        return static_cast<int>(((word >> 32) & 0x1f) + ((word >> 37) & 0x7) * 20);
    }

    static int rollover_diff_17bit(int a, int b) {
        constexpr int rollover = 1 << 17;
        constexpr int half = rollover >> 1;
        int difference = a - b;
        if (difference > half) {
            difference -= rollover;
        } else if (difference < -half) {
            difference += rollover;
        }
        return difference;
    }

    static std::string watchdog_name(int state_bits) {
        static const std::map<int, std::string> names = {
            {1 << 0, "IDLE"},
            {1 << 1, "TRIG_ONLY"},
            {1 << 2, "START_EVENT"},
            {1 << 3, "CAPTURE_PRE"},
            {1 << 4, "SEND_HEAD"},
            {1 << 5, "FLUSH_BUF"},
            {1 << 6, "STREAM_LIVE"},
            {1 << 7, "SEND_TRAIL"},
            {1 << 8, "ABORT_MARK"},
            {1 << 9, "ABORT_TRAIL"},
            {1 << 10, "ABORT_CLEAN"},
        };
        const auto found = names.find(state_bits);
        return found == names.end() ? "legacy/unknown" : found->second;
    }

    static std::string hex40(std::uint64_t word) {
        std::ostringstream output;
        output << "0x" << std::hex << std::uppercase;
        output.width(10);
        output.fill('0');
        output << (word & ((1ULL << 40) - 1));
        return output.str();
    }

    void issue(std::vector<std::string> &issues, const std::string &message) {
        if (static_cast<int>(issues.size()) < kMaxIssuesPerBatch) {
            issues.push_back(message);
        }
    }

    void reset_event() {
        event_open_ = false;
        current_hits_.clear();
        current_hit_count_ = 0;
        current_trigger_count_ = 0;
        current_tdc_header_count_ = 0;
        current_tdc_trailer_count_ = 0;
        current_trigger_ledge_.reset();
    }

    void start_event(
        int event_id20,
        int event_id12,
        int rd_bank_sel,
        std::optional<int> trigger_ledge,
        int trigger_overflow) {
        event_open_ = true;
        current_event_id20_ = event_id20;
        current_event_id12_ = event_id12;
        current_rd_bank_sel_ = rd_bank_sel;
        current_trigger_ledge_ = trigger_ledge;
        current_trigger_overflow_ = trigger_overflow;
        current_trigger_count_ = 0;
        current_tdc_header_count_ = 0;
        current_tdc_trailer_count_ = 0;
        current_hit_count_ = 0;
        current_hits_.clear();
    }

    std::size_t idx2(int a, int b, int dim_b) const {
        return static_cast<std::size_t>(a) * dim_b + b;
    }

    std::size_t idx3(int a, int b, int c, int dim_b, int dim_c) const {
        return (static_cast<std::size_t>(a) * dim_b + b) * dim_c + c;
    }

    void fill_valid_event_histograms() {
        for (const auto &hit : current_hits_) {
            const int tdc = hit.tdcid;
            const int channel = hit.channel;
            if (tdc < 0 || tdc >= max_tdcs_) {
                continue;
            }

            if (hit.width >= 0 && hit.width < adc_bins_) {
                ++adc_[idx2(tdc, hit.width, adc_bins_)];
            }

            int ledge = hit.ledge;
            if (current_trigger_ledge_.has_value()) {
                ledge = rollover_diff_17bit(ledge, *current_trigger_ledge_);
            }
            const int tdc_delta = ledge - tdc_min_count_;
            if (tdc_delta >= 0) {
                const int bin = tdc_delta >> tdc_shift_;
                if (bin < tdc_bins_) {
                    ++tdc_[idx2(tdc, bin, tdc_bins_)];
                }
            }

            if (channel < 0 || channel >= max_channels_) {
                continue;
            }
            if (hit.width >= 0 && hit.width < ch_adc_bins_) {
                ++adc_ch_[idx3(tdc, channel, hit.width, max_channels_, ch_adc_bins_)];
            }
            const int ch_delta = ledge - ch_tdc_min_count_;
            if (ch_delta >= 0) {
                const int bin = ch_delta >> ch_tdc_shift_;
                if (bin < ch_tdc_bins_) {
                    ++tdc_ch_[idx3(tdc, channel, bin, max_channels_, ch_tdc_bins_)];
                }
            }
        }
    }

    void fill_raw_hit_adc(const Hit &hit) {
        const int tdc = hit.tdcid;
        const int channel = hit.channel;
        if (tdc < 0 || tdc >= max_tdcs_) {
            return;
        }
        if (hit.width >= 0 && hit.width < adc_bins_) {
            ++adc_[idx2(tdc, hit.width, adc_bins_)];
        }
        if (channel >= 0 && channel < max_channels_ &&
            hit.width >= 0 && hit.width < ch_adc_bins_) {
            ++adc_ch_[idx3(tdc, channel, hit.width, max_channels_, ch_adc_bins_)];
        }
    }

    void record_event_hit_count(int event_id20, int hit_count) {
        const auto increment = [&](int chamber_id, int count) {
            if (chamber_id < 0 || chamber_id >= kMaxChambers) {
                return;
            }
            count = std::clamp(count, 0, kEventHitCountMax + 1);
            ++event_hit_count_hist_[idx2(
                chamber_id, count, kEventHitCountBins)];
        };

        if (acquisition_mode_ == 1) {
            increment((event_id20 >> 19) & 0x1, hit_count);
            return;
        }

        int hits_by_chamber[kMaxChambers] = {0, 0};
        bool configured[kMaxChambers] = {false, false};
        for (const int chamber_id : tdc_chamber_ids_) {
            if (chamber_id >= 0 && chamber_id < kMaxChambers) {
                configured[chamber_id] = true;
            }
        }
        for (const auto &hit : current_hits_) {
            if (hit.tdcid < 0 || hit.tdcid >= max_tdcs_) {
                continue;
            }
            const int chamber_id = tdc_chamber_ids_[hit.tdcid];
            if (chamber_id >= 0 && chamber_id < kMaxChambers) {
                ++hits_by_chamber[chamber_id];
            }
        }

        bool any_configured = false;
        for (int chamber_id = 0; chamber_id < kMaxChambers; ++chamber_id) {
            if (configured[chamber_id]) {
                increment(chamber_id, hits_by_chamber[chamber_id]);
                any_configured = true;
            }
        }
        if (!any_configured) {
            increment(0, hit_count);
        }
    }

    void finalize_event(
        int event_id20,
        int event_id12,
        int trigger_count,
        int hit_count,
        int tdc_header_count,
        int tdc_trailer_count,
        int header_count_error,
        int trailer_count_error,
        std::vector<CompletedEvent> &events,
        std::vector<std::string> &issues) {
        const bool id_mismatch = acquisition_mode_ == 1
            ? current_event_id20_ != event_id20
            : current_event_id12_ != event_id12;
        if (id_mismatch) {
            ++err_event_id_;
            issue(
                issues,
                "[ERROR] event_id mismatch: header_event_id12=" +
                    std::to_string(current_event_id12_) +
                    " trailer_event_id12=" + std::to_string(event_id12) +
                    " header_event_id20=" + std::to_string(current_event_id20_) +
                    " trailer_event_id20=" + std::to_string(event_id20));
            reset_event();
            return;
        }
        if (current_hit_count_ != hit_count) {
            ++err_hit_count_;
            issue(
                issues,
                "[ERROR] hit_count mismatch: event_id20=" +
                    std::to_string(current_event_id20_) +
                    " hits_seen=" + std::to_string(current_hit_count_) +
                    " trailer_hit_count=" + std::to_string(hit_count));
            reset_event();
            return;
        }
        if (header_count_error != 0 || trailer_count_error != 0) {
            issue(issues, "[WARN] TDC count flag in event trailer");
        }

        record_event_hit_count(current_event_id20_, hit_count);
        fill_valid_event_histograms();
        CompletedEvent event;
        event.event_id20 = current_event_id20_;
        event.event_id12 = current_event_id12_;
        event.rd_bank_sel = current_rd_bank_sel_;
        event.trigger_count = std::max(trigger_count, current_trigger_count_);
        event.hit_count_expected = hit_count;
        event.trigger_ledge = current_trigger_ledge_;
        event.trigger_overflow = current_trigger_overflow_;
        event.tdc_header_count = tdc_header_count;
        event.tdc_trailer_count = tdc_trailer_count;
        event.header_count_error = header_count_error;
        event.trailer_count_error = trailer_count_error;
        event.hits = current_hits_;
        events.push_back(std::move(event));
        ++valid_events_;
        reset_event();
    }

    void process_noise_word(
        std::uint64_t word,
        std::vector<std::string> &issues,
        bool &limit_exceeded) {
        const int top4 = static_cast<int>((word >> 36) & 0xf);
        if (top4 == 0xe) {
            in_noise_packet_ = false;
            ++noise_trailers_;
            noise_last_total_ += static_cast<std::uint64_t>(word & ((1ULL << 30) - 1));
            return;
        }
        if (top4 == 0xf) {
            ++noise_error_words_;
            const int tdc = noise_tdc_local_ + noise_csmid_ * 20;
            const int kind = static_cast<int>((word >> 31) & 0x1f);
            const std::uint64_t total = word & ((1ULL << 31) - 1);
            if (tdc < 0 || tdc >= max_tdcs_ || (kind != 0 && kind != 1)) {
                issue(
                    issues,
                    "[ERROR] invalid noise error counter: tdc=" + std::to_string(tdc) +
                        " kind=" + std::to_string(kind) +
                        " total=" + std::to_string(total) +
                        " raw=" + hex40(word));
                return;
            }

            auto &totals =
                kind == 0 ? noise_decode_error_count_ : noise_invalid_channel_count_;
            const std::uint64_t previous = totals[tdc];
            std::uint64_t delta = 0;
            if (total >= previous) {
                delta = total - previous;
            } else {
                const std::uint64_t wrapped =
                    (total - previous) & ((1ULL << 31) - 1);
                delta = wrapped <= (1ULL << 30) ? wrapped : total;
            }
            totals[tdc] = total;
            if (delta == 0) {
                return;
            }

            decode_error_total_ += delta;
            decode_errors_[tdc] += static_cast<std::uint32_t>(delta);
            issue(
                issues,
                "[ERROR] noise error counter: reason=" +
                    std::string(kind == 0 ? "KERR/DErr" : "invalid_channel") +
                    " tdc=" + std::to_string(tdc) +
                    " delta=" + std::to_string(delta) +
                    " total=" + std::to_string(total) +
                    " raw=" + hex40(word));
            if (decode_error_stop_threshold_ > 0 &&
                decode_error_total_ >
                    static_cast<std::uint64_t>(decode_error_stop_threshold_) &&
                !decode_error_limit_emitted_) {
                decode_error_limit_emitted_ = true;
                limit_exceeded = true;
            }
            return;
        }
        if (top4 != 0x9) {
            return;
        }
        ++noise_counters_;
        const int tdc = noise_tdc_local_ + noise_csmid_ * 20;
        const int channel = static_cast<int>((word >> 31) & 0x1f);
        if (tdc < 0 || tdc >= max_tdcs_ || channel < 0 || channel >= max_channels_) {
            return;
        }
        const std::size_t index = idx2(tdc, channel, max_channels_);
        const std::uint64_t total = word & ((1ULL << 31) - 1);
        const std::uint64_t previous_total = noise_prev_total_[index];
        const std::uint64_t previous_seconds = noise_prev_seconds_[index];
        if (previous_seconds > 0 && noise_last_seconds_ > previous_seconds) {
            const std::uint64_t delta = (total - previous_total) & ((1ULL << 31) - 1);
            if (total < previous_total && delta > (1ULL << 30)) {
                noise_rate_[index] = 0.0;
            } else {
                noise_rate_[index] =
                    static_cast<double>(delta) /
                    static_cast<double>(noise_last_seconds_ - previous_seconds);
            }
        }
        noise_total_[index] = total;
        noise_prev_total_[index] = total;
        noise_prev_seconds_[index] = noise_last_seconds_;
    }

    void process_raw_hit_word(
        std::uint64_t word,
        std::vector<std::string> &issues,
        bool &limit_exceeded) {
        if (static_cast<std::uint32_t>(word) == 0) {
            return;
        }

        Hit hit;
        hit.csmid = static_cast<int>((word >> 37) & 0x7);
        hit.tdcid = tdc_id(word);
        hit.channel = static_cast<int>((word >> 27) & 0x1f);
        hit.mode = static_cast<int>((word >> 25) & 0x3);
        hit.ledge = static_cast<int>((word >> 8) & 0x1ffff);
        hit.width = static_cast<int>(word & 0xff);
        if (hit.channel >= 24) {
            record_decode_error(
                hit.tdcid,
                word,
                "invalid_hit_channel",
                issues,
                limit_exceeded);
            return;
        }

        ++hits_total_;
        if (hit.tdcid >= 0 && hit.tdcid < max_tdcs_ &&
            hit.channel >= 0 && hit.channel < max_channels_) {
            ++hit_ch_all_[idx2(hit.tdcid, hit.channel, max_channels_)];
        }
        fill_raw_hit_adc(hit);
    }

    void process_word(
        std::uint64_t word,
        std::vector<CompletedEvent> &events,
        std::vector<std::string> &issues,
        bool &limit_exceeded) {
        if (raw_hit_mode_) {
            process_raw_hit_word(word, issues, limit_exceeded);
            return;
        }

        const int top4 = static_cast<int>((word >> 36) & 0xf);
        if (in_noise_packet_) {
            process_noise_word(word, issues, limit_exceeded);
            return;
        }

        if (acquisition_mode_ == 1 && top4 == 0xd) {
            in_noise_packet_ = true;
            noise_csmid_ = static_cast<int>((word >> 35) & 0x1);
            noise_tdc_local_ = static_cast<int>((word >> 30) & 0x1f);
            const std::uint64_t seconds = word & ((1ULL << 30) - 1);
            ++noise_headers_;
            if (seconds != noise_last_seconds_) {
                std::fill(noise_rate_.begin(), noise_rate_.end(), 0.0);
                noise_last_total_ = 0;
                noise_last_seconds_ = seconds;
            }
            if (event_open_) {
                ++err_missing_trailer_;
                reset_event();
            }
            return;
        }

        if (top4 == 0xb) {
            const int subtype = static_cast<int>((word >> 32) & 0xf);
            if (subtype == 0xa && ((word >> 10) & ((1ULL << 22) - 1)) == 0x2aaaaa) {
                ++abort_burst_;
                issue(
                    issues,
                    "[WARN] burst abort marker: threshold=" +
                        std::to_string(word & 0x3ff) + " raw=" + hex40(word));
                return;
            }
            if (subtype == 0xd) {
                ++abort_watchdog_;
                const int state = static_cast<int>((word >> 21) & 0x7ff);
                const std::string name = watchdog_name(state);
                ++abort_watchdog_types_[name];
                issue(
                    issues,
                    "[WARN] watchdog abort marker: state=" + name +
                        " count=" + std::to_string(word & ((1ULL << 21) - 1)) +
                        " raw=" + hex40(word));
                return;
            }
        }

        if (top4 == 0xa) {
            ++headers_;
            if (event_open_) {
                ++err_missing_trailer_;
                issue(
                    issues,
                    "[ERROR] missing trailer before new header: previous_event_id20=" +
                        std::to_string(current_event_id20_));
                reset_event();
            }
            if (acquisition_mode_ == 1) {
                const int event_id20 = static_cast<int>((word >> 16) & 0xfffff);
                const int bank = static_cast<int>((word >> 15) & 1);
                bank == 0 ? ++events_fifo_a_ : ++events_fifo_b_;
                start_event(event_id20, event_id20 & 0xfff, bank, std::nullopt, 0);
            } else {
                // Triggered-mode headers carry one trigger timestamp each.
                ++triggers_;
                ++events_fifo_a_;
                start_event(
                    static_cast<int>((word >> 17) & 0x3ffff),
                    static_cast<int>((word >> 17) & 0xfff),
                    0,
                    static_cast<int>(word & 0x1ffff),
                    static_cast<int>((word >> 35) & 1));
            }
            return;
        }

        if (top4 == 0xc) {
            ++trailers_;
            if (!event_open_) {
                ++err_missing_header_;
                issue(
                    issues,
                    "[ERROR] missing header before trailer: raw=" + hex40(word));
                return;
            }
            if (acquisition_mode_ == 1) {
                const int event_id20 = static_cast<int>((word >> 16) & 0xfffff);
                finalize_event(
                    event_id20,
                    event_id20 & 0xfff,
                    static_cast<int>((word >> 10) & 0x3f),
                    static_cast<int>(word & 0x3ff),
                    0,
                    0,
                    0,
                    0,
                    events,
                    issues);
            } else {
                const int event_id12 = static_cast<int>((word >> 16) & 0xfff);
                finalize_event(
                    event_id12,
                    event_id12,
                    0,
                    static_cast<int>(word & 0x3ff),
                    static_cast<int>((word >> 32) & 0xf),
                    static_cast<int>((word >> 28) & 0xf),
                    static_cast<int>((word >> 15) & 1),
                    static_cast<int>((word >> 14) & 1),
                    events,
                    issues);
            }
            return;
        }

        if (top4 == 0xe && ((word >> 30) & 0x3f) == 0) {
            ++triggers_;
            if (event_open_) {
                current_trigger_ledge_ = static_cast<int>(word & 0x1ffff);
                current_trigger_overflow_ = static_cast<int>((word >> 29) & 1);
                ++current_trigger_count_;
            }
            return;
        }

        const std::uint32_t low32 = static_cast<std::uint32_t>(word);
        const int ident = static_cast<int>((word >> 24) & 0xff);
        if (ident == 0xf8) {
            if (event_open_) {
                ++current_tdc_header_count_;
            }
            return;
        }
        if (ident == 0xf0) {
            if (event_open_) {
                ++current_tdc_trailer_count_;
            }
            if (((word >> 11) & 1) != 0 || ((word >> 10) & 1) != 0) {
                issue(
                    issues,
                    "[WARN] TDC trailer flag: tdc=" + std::to_string(tdc_id(word)) +
                        " trigger_lost=" + std::to_string((word >> 11) & 1) +
                        " timeout=" + std::to_string((word >> 10) & 1) +
                        " raw=" + hex40(word));
            }
            return;
        }
        if (low32 == 0xf7411111U || ident == 0xf7) {
            record_decode_error(tdc_id(word), word, "decode_error", issues, limit_exceeded);
            return;
        }
        if (ident == 0xe8) {
            const int tdc = tdc_id(word);
            if (tdc >= 0 && tdc < max_tdcs_) {
                ++overflow_[tdc];
            }
            issue(
                issues,
                "[WARN] TDC overflow word: tdc=" + std::to_string(tdc) +
                    " raw=" + hex40(word));
            return;
        }
        if (low32 == 0) {
            return;
        }

        Hit hit;
        hit.csmid = static_cast<int>((word >> 37) & 0x7);
        hit.tdcid = tdc_id(word);
        hit.channel = static_cast<int>((word >> 27) & 0x1f);
        hit.mode = static_cast<int>((word >> 25) & 0x3);
        hit.ledge = static_cast<int>((word >> 8) & 0x1ffff);
        hit.width = static_cast<int>(word & 0xff);
        if (hit.channel >= 24) {
            record_decode_error(
                hit.tdcid,
                word,
                "invalid_hit_channel",
                issues,
                limit_exceeded);
            return;
        }

        ++hits_total_;
        if (hit.tdcid >= 0 && hit.tdcid < max_tdcs_ &&
            hit.channel >= 0 && hit.channel < max_channels_) {
            ++hit_ch_all_[idx2(hit.tdcid, hit.channel, max_channels_)];
        }
        if (event_open_) {
            current_hits_.push_back(hit);
            ++current_hit_count_;
        }
    }

    void record_decode_error(
        int tdc,
        std::uint64_t word,
        const std::string &reason,
        std::vector<std::string> &issues,
        bool &limit_exceeded) {
        ++decode_error_total_;
        if (tdc >= 0 && tdc < max_tdcs_) {
            ++decode_errors_[tdc];
        }
        issue(
            issues,
            "[ERROR] decode error word: reason=" + reason +
                " tdc=" + std::to_string(tdc) + " raw=" + hex40(word));
        if (decode_error_stop_threshold_ > 0 &&
            decode_error_total_ >
                static_cast<std::uint64_t>(decode_error_stop_threshold_) &&
            !decode_error_limit_emitted_) {
            decode_error_limit_emitted_ = true;
            limit_exceeded = true;
        }
    }

    void process_bytes(
        const std::string &input,
        std::vector<CompletedEvent> &events,
        std::vector<std::string> &issues,
        bool &limit_exceeded) {
        carry_.append(input);
        const std::size_t words = carry_.size() / kWordSize;
        for (std::size_t index = 0; index < words; ++index) {
            process_word(
                read_word(carry_.data() + index * kWordSize),
                events,
                issues,
                limit_exceeded);
            if (limit_exceeded) {
                break;
            }
        }
        carry_.erase(0, words * kWordSize);
    }

    int acquisition_mode_;
    int noise_test_mode_;
    bool raw_hit_mode_;
    int max_tdcs_;
    int max_channels_;
    std::vector<int> tdc_chamber_ids_;
    int adc_bins_;
    int tdc_bins_;
    int tdc_shift_;
    int ch_adc_bins_;
    int ch_tdc_bins_;
    int ch_tdc_shift_;
    double tdc_min_ns_;
    double tdc_max_ns_;
    double ch_tdc_min_ns_;
    double ch_tdc_max_ns_;
    int decode_error_stop_threshold_;
    int tdc_min_count_;
    int ch_tdc_min_count_;

    std::vector<std::uint32_t> adc_;
    std::vector<std::uint32_t> tdc_;
    std::vector<std::uint32_t> adc_ch_;
    std::vector<std::uint32_t> tdc_ch_;
    std::vector<std::uint32_t> hit_ch_all_;
    std::vector<std::uint64_t> event_hit_count_hist_;
    std::vector<std::uint32_t> overflow_;
    std::vector<std::uint32_t> decode_errors_;
    std::vector<std::uint64_t> noise_total_;
    std::vector<double> noise_rate_;
    std::vector<std::uint64_t> noise_prev_total_;
    std::vector<std::uint64_t> noise_prev_seconds_;
    std::vector<std::uint64_t> noise_decode_error_count_;
    std::vector<std::uint64_t> noise_invalid_channel_count_;

    std::uint64_t headers_ = 0;
    std::uint64_t events_fifo_a_ = 0;
    std::uint64_t events_fifo_b_ = 0;
    std::uint64_t trailers_ = 0;
    std::uint64_t triggers_ = 0;
    std::uint64_t hits_total_ = 0;
    std::uint64_t valid_events_ = 0;
    std::uint64_t decode_error_total_ = 0;
    std::uint64_t err_event_id_ = 0;
    std::uint64_t err_hit_count_ = 0;
    std::uint64_t err_missing_trailer_ = 0;
    std::uint64_t err_missing_header_ = 0;
    std::uint64_t abort_burst_ = 0;
    std::uint64_t abort_watchdog_ = 0;
    std::map<std::string, std::uint64_t> abort_watchdog_types_;
    std::uint64_t noise_headers_ = 0;
    std::uint64_t noise_counters_ = 0;
    std::uint64_t noise_error_words_ = 0;
    std::uint64_t noise_trailers_ = 0;
    std::uint64_t noise_last_seconds_ = 0;
    std::uint64_t noise_last_total_ = 0;

    bool event_open_ = false;
    int current_event_id20_ = 0;
    int current_event_id12_ = 0;
    int current_rd_bank_sel_ = 0;
    std::optional<int> current_trigger_ledge_;
    int current_trigger_overflow_ = 0;
    int current_trigger_count_ = 0;
    int current_tdc_header_count_ = 0;
    int current_tdc_trailer_count_ = 0;
    int current_hit_count_ = 0;
    std::vector<Hit> current_hits_;

    bool in_noise_packet_ = false;
    int noise_csmid_ = 0;
    int noise_tdc_local_ = 0;
    bool decode_error_limit_emitted_ = false;
    std::string carry_;
    mutable std::mutex mutex_;
};

}  // namespace

PYBIND11_MODULE(native_decoder_cpp, module) {
    module.doc() = "Ordered native MiniDAQ word decoder and event assembler";
    py::class_<NativeDecoder>(module, "NativeDecoder")
        .def(
            py::init<
                int,
                int,
                int,
                int,
                std::vector<int>,
                int,
                int,
                int,
                int,
                int,
                double,
                double,
                double,
                double,
                int>(),
            py::arg("acquisition_mode"),
            py::arg("noise_test_mode"),
            py::arg("max_tdcs"),
            py::arg("max_channels"),
            py::arg("tdc_chamber_ids"),
            py::arg("adc_bins"),
            py::arg("tdc_bins"),
            py::arg("tdc_shift"),
            py::arg("ch_tdc_bins"),
            py::arg("ch_tdc_shift"),
            py::arg("tdc_min_ns"),
            py::arg("tdc_max_ns"),
            py::arg("ch_tdc_min_ns"),
            py::arg("ch_tdc_max_ns"),
            py::arg("decode_error_stop_threshold"))
        .def(
            "process",
            &NativeDecoder::process,
            py::arg("data"),
            py::arg("max_completed_events") = -1,
            py::arg("min_event_hits") = 0)
        .def(
            "snapshot",
            &NativeDecoder::snapshot,
            py::arg("requested_fields") = py::none());
}
