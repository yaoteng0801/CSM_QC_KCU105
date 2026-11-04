#!/usr/bin/env python3
"""Plot per-CSM hit multiplicity in UART triggerless (acquisition_mode=1) .dat files.

Reads bounded chunks of big-endian 40-bit words, preserving events across chunks.
Counts raw hit words and distinct (CSM, TDC, channel) addresses independently.
Only header/trailer pairs with matching IDs enter the histograms; count-mismatched
and aborted events remain included and are reported separately. No physics cuts
or minimum-hit cut are applied. This is not a triggered/noise-stream file reader.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

from Signal import SignalType, decode_word5


def scan_stream(stream, *, threshold=4, chunk_words=200_000, max_events=None,
                progress=False):
    """Scan a binary stream without retaining individual events in memory."""
    if chunk_words < 1 or threshold < 1 or (max_events is not None and max_events < 1):
        raise ValueError("chunk_words, threshold and max_events must be positive")
    histograms = [{name: Counter() for name in ("raw", "unique", "trailer")}
                  for _ in range(2)]
    counts = Counter()
    group_counts = [Counter(), Counter()]
    examples = {"raw_below_threshold": [], "unique_below_threshold": [], "errors": []}
    event_id = None
    raw_hits = 0
    unique = set()
    hit_csm_mask = 0
    triggers = 0
    aborted = False
    header_offset = 0
    consumed = 0
    bytes_read = 0
    carry = b""
    stopped = False
    last_progress = time.monotonic()

    def example(kind, detail):
        if len(examples[kind]) < 8:
            examples[kind].append(detail)

    while not stopped:
        data = stream.read(chunk_words * 5)
        if not data:
            break
        bytes_read += len(data)
        data = carry + data
        whole = len(data) // 5 * 5
        carry = data[whole:]
        octets = np.frombuffer(data[:whole], dtype=np.uint8).reshape(-1, 5)
        words = np.zeros(len(octets), dtype=np.uint64)
        for column in range(5):
            words = (words << 8) | octets[:, column]

        for word in words.tolist():
            offset = consumed
            consumed += 5
            tag = word >> 36
            if tag == 0xA:
                counts["headers"] += 1
                if event_id is not None:
                    counts["missing_trailer"] += 1
                    example("errors", {"kind": "missing_trailer", "offset": header_offset})
                event_id = (word >> 16) & 0xFFFFF
                header_offset = offset
                raw_hits = 0
                unique.clear()
                hit_csm_mask = 0
                triggers = 0
                aborted = False
                continue

            if tag == 0xC:
                counts["trailers"] += 1
                if event_id is None:
                    counts["missing_header"] += 1
                    continue
                trailer_id = (word >> 16) & 0xFFFFF
                trailer_hits = word & 0x3FF
                group = (event_id >> 19) & 1
                detail = {"offset": header_offset, "event_id": f"0x{event_id:05x}",
                          "csm": group, "raw_hits": raw_hits,
                          "distinct_channels": len(unique), "trailer_hits": trailer_hits,
                          "triggers": triggers, "aborted": aborted}
                if trailer_id != event_id:
                    counts["event_id_mismatch"] += 1
                    example("errors", dict(detail, kind="event_id_mismatch",
                                            trailer_id=f"0x{trailer_id:05x}"))
                    event_id = None
                    continue
                if raw_hits != trailer_hits:
                    counts["hit_count_mismatch"] += 1
                    example("errors", dict(detail, kind="hit_count_mismatch"))
                if hit_csm_mask & ~(1 << group):
                    counts["wrong_or_mixed_csm_events"] += 1
                    example("errors", dict(detail, kind="wrong_or_mixed_csm",
                                            hit_csm_mask=hit_csm_mask))
                if (triggers & 0x3F) != ((word >> 10) & 0x3F):
                    counts["trigger_count_mismatch"] += 1
                counts["complete_events"] += 1
                for name, value in (("raw", raw_hits), ("unique", len(unique)),
                                    ("trailer", trailer_hits)):
                    histograms[group][name][value] += 1
                group_counts[group]["events"] += 1
                group_counts[group]["raw_hits"] += raw_hits
                group_counts[group]["events_with_repeated_channels"] += int(raw_hits > len(unique))
                group_counts[group]["aborted_events"] += int(aborted)
                group_counts[group]["events_with_triggers"] += int(triggers > 0)
                if raw_hits < threshold:
                    example("raw_below_threshold", detail)
                if raw_hits >= threshold and len(unique) < threshold:
                    detail["channels"] = [
                        {"csm": address >> 10, "tdc_local": (address >> 5) & 31,
                         "channel": address & 31} for address in sorted(unique)]
                    example("unique_below_threshold", detail)
                event_id = None
                if max_events is not None and counts["complete_events"] >= max_events:
                    stopped = True
                    break
                continue

            # Fast path for ordinary CSM0/1 hits. Control/error identifiers have
            # channel >=24, so they use the shared decoder below instead.
            channel = (word >> 27) & 31
            if tag < 4 and channel < 24 and (word & 0xFFFFFFFF) != 0:
                is_hit = True
            else:
                signal = decode_word5(word.to_bytes(5, "big"), acquisition_mode=1)
                is_hit = signal.type == SignalType.HIT
                if not is_hit:
                    counts[signal.type.name.lower() + "_words"] += 1
                    if signal.type == SignalType.NOISE_COUNTER_HEADER:
                        raise ValueError("Noise-counter data found; expected UART triggerless events")
                    if signal.type == SignalType.TRIGGER and event_id is not None:
                        triggers += 1
                    if signal.type == SignalType.ABORT:
                        counts["abort_" + signal.abort.kind] += 1
                        if event_id is not None:
                            aborted = True
            if is_hit:
                counts["raw_hit_words"] += 1
                if ((word >> 32) & 31) >= 20:
                    counts["invalid_tdc_hit_words"] += 1
                if event_id is None:
                    counts["hits_outside_events"] += 1
                else:
                    raw_hits += 1
                    unique.add(((word >> 32) << 5) | channel)
                    hit_csm_mask |= 1 << ((word >> 37) & 7)

        if progress and time.monotonic() - last_progress >= 10:
            print(f"Scanned {consumed / 1e6:.1f} MB; "
                  f"{counts['complete_events']:,} complete events", file=sys.stderr, flush=True)
            last_progress = time.monotonic()

    if event_id is not None:
        counts["missing_trailer"] += 1
        example("errors", {"kind": "missing_trailer_at_eof", "offset": header_offset})
    counts["trailing_bytes"] = len(carry) if not stopped else 0
    for name in ("complete_events", "headers", "trailers", "raw_hit_words",
                 "missing_header", "missing_trailer", "event_id_mismatch",
                 "hit_count_mismatch", "trigger_count_mismatch",
                 "wrong_or_mixed_csm_events", "hits_outside_events",
                 "decode_error_words", "overflow_words", "unknown_words",
                 "trigger_words", "abort_burst", "abort_watchdog",
                 "invalid_tdc_hit_words"):
        counts.setdefault(name, 0)

    groups = []
    for group, hist in enumerate(histograms):
        summary = dict(group_counts[group])
        summary.update(csm=group, events=sum(hist["raw"].values()),
                       raw_zero_hit_events=hist["raw"][0],
                       raw_below_threshold=sum(n for h, n in hist["raw"].items() if h < threshold),
                       unique_below_threshold=sum(n for h, n in hist["unique"].items() if h < threshold),
                       raw_min=min(hist["raw"], default=None),
                       raw_max=max(hist["raw"], default=None))
        groups.append(summary)
    return {"threshold_reference": threshold, "bytes_read": bytes_read,
            "bytes_scanned": consumed, "stopped_at_event_limit": stopped,
            "counts": dict(counts), "groups": groups, "examples": examples}, histograms


def write_outputs(prefix, report, histograms, *, zoom_max=20):
    prefix.parent.mkdir(parents=True, exist_ok=True)
    csv_path = Path(str(prefix) + ".csv")
    json_path = Path(str(prefix) + "_summary.json")
    with csv_path.open("w", newline="") as output:
        writer = csv.writer(output)
        writer.writerow(["csm", "hits_per_event", "raw_events", "distinct_channel_events", "trailer_events"])
        for group, hist in enumerate(histograms):
            maximum = max((max(values, default=0) for values in hist.values()), default=0)
            for hits in range(maximum + 1):
                writer.writerow([group, hits, hist["raw"][hits], hist["unique"][hits], hist["trailer"][hits]])
    json_path.write_text(json.dumps(report, indent=2) + "\n")

    # Keep the numeric results even if plotting dependencies are unavailable.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator

    fig, axes = plt.subplots(2, 2, figsize=(13, 8), constrained_layout=True)
    threshold = report["threshold_reference"]
    for group, hist in enumerate(histograms):
        maximum = max(max(hist["raw"], default=0), max(hist["unique"], default=0), threshold)
        maximum = max(maximum, zoom_max)
        x = np.arange(maximum + 1)
        edges = np.arange(maximum + 2) - 0.5
        for column, ax in enumerate(axes[group]):
            for name, label, color in (("raw", "Raw hit words", "#2369b3"),
                                        ("unique", "Distinct channels", "#d16b19")):
                values = np.array([hist[name][int(hits)] for hits in x])
                ax.stairs(values, edges, label=label, color=color, linewidth=1.6)
            ax.axvline(threshold - 0.5, color="#b32836", linestyle="--", linewidth=1,
                       label=f"Threshold {threshold} boundary")
            ax.set_xlim(-0.5, (zoom_max if column == 0 else maximum) + 0.5)
            ax.set_ylim(bottom=0.7, top=max(2, max(hist["raw"].values(), default=1),
                                           max(hist["unique"].values(), default=1)) * 2)
            ax.set_yscale("log")
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
            ax.grid(axis="y", alpha=0.2)
            ax.set_xlabel("Hits / distinct channels per event")
            ax.set_ylabel("Events (log scale)")
            total = report["groups"][group]["events"]
            scope = f"0–{zoom_max}" if column == 0 else "full range"
            ax.set_title(f"CSM {group} · {total:,} events · {scope}")
            if column == 0:
                raw_low = report["groups"][group]["raw_below_threshold"]
                unique_low = report["groups"][group]["unique_below_threshold"]
                ax.text(0.98, 0.95, f"Below {threshold}: raw {raw_low:,}\n"
                        f"distinct channels {unique_low:,}", ha="right", va="top",
                        transform=ax.transAxes, fontsize=10)
    axes[0, 1].legend(loc="upper right", fontsize=9)
    fig.suptitle(f"{Path(report['input_file']).stem}\n"
                 "UART triggerless events; no hit cuts; aborted events included", fontsize=13)
    png_path = Path(str(prefix) + ".png")
    pdf_path = Path(str(prefix) + ".pdf")
    fig.savefig(png_path, dpi=180)
    fig.savefig(pdf_path)
    plt.close(fig)
    return [png_path, pdf_path, csv_path, json_path]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dat_file", type=Path)
    parser.add_argument("--output-prefix", type=Path,
                        help="Output path without extension (default: INPUT_STEM_hit_counts in cwd)")
    parser.add_argument("--threshold", type=int, default=4,
                        help="Reference threshold for annotation, not an event cut (default: 4)")
    parser.add_argument("--zoom-max", type=int, default=20)
    parser.add_argument("--chunk-words", type=int, default=200_000)
    parser.add_argument("--max-events", type=int, help="Optional limit; default scans the whole file")
    args = parser.parse_args()
    if min(args.threshold, args.chunk_words, args.zoom_max) < 1 or (
            args.max_events is not None and args.max_events < 1):
        parser.error("numeric options must be positive")
    prefix = args.output_prefix or Path(args.dat_file.stem + "_hit_counts")
    prefix.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with args.dat_file.open("rb") as stream:
        report, histograms = scan_stream(stream, threshold=args.threshold,
                                        chunk_words=args.chunk_words, max_events=args.max_events,
                                        progress=True)
    report.update(input_file=str(args.dat_file.resolve()), input_bytes=args.dat_file.stat().st_size,
                  elapsed_scan_s=round(time.monotonic() - started, 3))
    outputs = write_outputs(prefix, report, histograms, zoom_max=args.zoom_max)
    print(json.dumps(report, indent=2))
    for path in outputs:
        print(f"Saved {path.resolve()}")


if __name__ == "__main__":
    main()
