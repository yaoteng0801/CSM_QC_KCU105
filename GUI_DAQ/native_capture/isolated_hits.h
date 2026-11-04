#pragma once

#include <array>
#include <cstdint>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

// Triggerless event filter. Buffer one complete event before classifying hits,
// so later hits can rescue earlier ones. Damaged/incomplete events pass through
// verbatim; filtering must not conceal acquisition errors or invent neighbors.
class IsolatedHitFilter {
public:
    bool enabled = false;
    std::uint64_t dropped_hits = 0, filtered_events = 0, preserved_events = 0, rejected_events = 0;

    bool load(const std::string &path) {
        channels_.fill(-1);
        chambers_.fill(-1);
        std::ifstream input(path);
        std::string line;
        if (!std::getline(input, line)) return false;
        reapply_filters_ = line == "MINIDAQ_NEIGHBORS_V2";
        if (!reapply_filters_ && line != "MINIDAQ_NEIGHBORS_V1") return false;
        if (reapply_filters_) {
            for (int chamber = 0; chamber < 2; ++chamber) {
                if (!std::getline(input, line)) return false;
                std::istringstream row(line);
                std::string tag, extra;
                int cid;
                auto &cfg = filters_[chamber];
                if (!(row >> tag >> cid >> cfg.enabled >> cfg.total >> cfg.per_ml >>
                      cfg.per_layer >> cfg.hit_layers) || tag != "FILTER" || cid != chamber ||
                    cfg.enabled < 0 || cfg.enabled > 15 || cfg.total < 0 || cfg.total > 256 ||
                    cfg.per_ml < 0 || cfg.per_ml > 256 || cfg.per_layer < 0 || cfg.per_layer > 256 ||
                    cfg.hit_layers < 0 || cfg.hit_layers > 256 || (row >> extra)) return false;
            }
        }
        tube_chambers_.fill(-1);
        for (auto &layers : layer_ml_) layers.fill(-1);
        int entries = 0;
        while (std::getline(input, line)) {
            std::istringstream row(line);
            int index, chamber, tube, count, ml = 0, layer = 0;
            if (!(row >> index >> chamber >> tube)) return false;
            if (reapply_filters_ && (!(row >> ml >> layer) || ml < 0 || ml >= 16 ||
                                    layer < 0 || layer >= 256)) return false;
            if (!(row >> count) || index < 0 || index >= 1280 ||
                index % 32 >= 24 || chamber < 0 || chamber > 1 || tube < 0 || tube >= 960 ||
                count < 0 || count > 959 || channels_[index] != -1) return false;
            std::vector<int> neighbors;
            for (int i = 0; i < count; ++i) {
                int n;
                if (!(row >> n) || n < 0 || n >= 960 || n == tube) return false;
                neighbors.push_back(n);
            }
            std::string extra;
            if (row >> extra) return false;
            if (reapply_filters_) {
                if ((tube_chambers_[tube] >= 0 && (tube_chambers_[tube] != chamber ||
                     tube_ml_[tube] != ml || tube_layer_[tube] != layer)) ||
                    (layer_ml_[chamber][layer] >= 0 && layer_ml_[chamber][layer] != ml)) return false;
                tube_chambers_[tube] = chamber;
                tube_ml_[tube] = ml;
                tube_layer_[tube] = layer;
                layer_ml_[chamber][layer] = ml;
                selected_mls_[chamber][ml] = true;
            }
            channels_[index] = tube;
            chambers_[index] = chamber;
            neighbors_[tube] = std::move(neighbors);
            ++entries;
        }
        enabled = entries > 0;
        return enabled;
    }

    void packet_loss() { if (!pending_.empty()) valid_ = false; }

    void feed(const std::uint8_t *bytes, std::vector<std::uint8_t> &output) {
        if (!enabled) {
            output.insert(output.end(), bytes, bytes + 5);
            return;
        }
        std::uint64_t word = 0;
        for (int i = 0; i < 5; ++i) word = (word << 8) | bytes[i];
        const int tag = word >> 36;
        if (tag == 0xa) {
            finish(output);
            valid_ = true;
            event_id_ = (word >> 16) & 0xfffff;
            hit_count_ = 0;
            pending_.push_back(word);
            return;
        }
        if (pending_.empty()) {
            append(output, word);
            return;
        }
        pending_.push_back(word);
        if (tag == 0xc) {
            if (((word >> 16) & 0xfffff) != event_id_ || (word & 1023) != hit_count_)
                valid_ = false;
            if (valid_) filter(output);
            else finish(output);
            return;
        }
        if (is_hit(word)) {
            ++hit_count_;
            const int index = channel_index(word);
            if (index < 0 || (channels_[index] >= 0 && chambers_[index] != int(event_id_ >> 19)))
                valid_ = false;
        } else if (!(tag == 0xe && ((word >> 30) & 63) == 0)) {
            // Abort, decoder error, noise data, or unexpected control word.
            valid_ = false;
        }
        if (pending_.size() >= 8192) finish(output); // bounded on missing trailer
    }

    void finish(std::vector<std::uint8_t> &output) {
        if (pending_.empty()) return;
        for (auto word : pending_) append(output, word);
        pending_.clear();
        ++preserved_events;
    }

private:
    struct FilterSettings { int enabled = 0, total = 0, per_ml = 0, per_layer = 0, hit_layers = 0; };
    std::array<FilterSettings, 2> filters_{};
    bool reapply_filters_ = false;
    std::array<int, 960> tube_chambers_{}, tube_ml_{}, tube_layer_{};
    std::array<std::array<int, 256>, 2> layer_ml_{};
    std::array<std::array<bool, 16>, 2> selected_mls_{};
    std::array<int, 1280> channels_{}, chambers_{};
    std::array<std::vector<int>, 960> neighbors_{};
    std::vector<std::uint64_t> pending_;
    std::uint64_t event_id_ = 0;
    unsigned hit_count_ = 0;
    bool valid_ = true;

    static bool is_hit(std::uint64_t word) {
        // Physical CSMs 0/1, local TDC 0..19, channel 0..23.
        return (word >> 36) < 4 && ((word >> 27) & 31) < 24 &&
            (word & 0xffffffffULL) != 0;
    }
    static int channel_index(std::uint64_t word) {
        const int csm = (word >> 37) & 7, tdc = (word >> 32) & 31;
        if (csm > 1 || tdc >= 20) return -1;
        return (csm * 20 + tdc) * 32 + ((word >> 27) & 31);
    }
    static void append(std::vector<std::uint8_t> &output, std::uint64_t word) {
        for (int shift = 32; shift >= 0; shift -= 8)
            output.push_back(static_cast<std::uint8_t>(word >> shift));
    }
    bool passes_filters(const std::array<bool, 960> &kept) const {
        if (!reapply_filters_) return true; // legacy V1 isolation-only snapshot
        const int chamber = event_id_ >> 19;
        const auto &cfg = filters_[chamber];
        int total = 0;
        std::array<int, 16> per_ml{}, hit_layers{};
        std::array<int, 256> per_layer{};
        for (int tube = 0; tube < 960; ++tube) {
            if (!kept[tube] || tube_chambers_[tube] != chamber) continue;
            ++total;
            ++per_ml[tube_ml_[tube]];
            if (per_layer[tube_layer_[tube]]++ == 0) ++hit_layers[tube_ml_[tube]];
        }
        // Match tube_event_filter.sv: distinct mapped tubes, all enabled cuts
        // ANDed, and even disabled cuts require a nonempty mapped-tube event.
        if (total == 0 || ((cfg.enabled & 1) && total < cfg.total)) return false;
        for (int ml = 0; ml < 16; ++ml) {
            if (!selected_mls_[chamber][ml]) continue;
            if ((cfg.enabled & 2) && per_ml[ml] < cfg.per_ml) return false;
            if ((cfg.enabled & 8) && hit_layers[ml] < cfg.hit_layers) return false;
        }
        for (int layer = 0; layer < 256; ++layer)
            if ((cfg.enabled & 4) && layer_ml_[chamber][layer] >= 0 &&
                per_layer[layer] < cfg.per_layer) return false;
        return true;
    }
    void filter(std::vector<std::uint8_t> &output) {
        std::array<bool, 960> occupied{};
        for (auto word : pending_) {
            if (!is_hit(word)) continue;
            const int tube = channels_[channel_index(word)];
            if (tube >= 0) occupied[tube] = true;
        }
        std::array<bool, 960> kept{};
        for (int tube = 0; tube < 960; ++tube)
            if (occupied[tube])
                for (int n : neighbors_[tube]) kept[tube] = kept[tube] || occupied[n];
        unsigned removed = 0;
        for (auto word : pending_) {
            if (!is_hit(word)) continue;
            const int tube = channels_[channel_index(word)];
            if (tube >= 0 && !kept[tube]) ++removed;
        }
        dropped_hits += removed;
        ++filtered_events;
        if (!passes_filters(kept)) {
            ++rejected_events;
            pending_.clear();
            return;
        }
        for (std::size_t i = 0; i + 1 < pending_.size(); ++i) {
            const auto word = pending_[i];
            if (is_hit(word)) {
                const int tube = channels_[channel_index(word)];
                if (tube >= 0 && !kept[tube]) continue;
            }
            append(output, word);
        }
        // Preserve event ID, trigger count and all framing, including empty events.
        append(output, (pending_.back() & ~1023ULL) | (hit_count_ - removed));
        pending_.clear();
    }
};
