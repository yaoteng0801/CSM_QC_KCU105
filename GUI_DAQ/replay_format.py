"""Select the DAT decoder format without reading or changing hardware registers."""
from pathlib import Path


def replay_modes(dat_path, fallback=(0, 0)):
    path = Path(dat_path)
    config = path.with_name(path.stem + "_configuration.txt")
    values = {}
    try:
        section = ""
        with config.open(encoding="utf-8", errors="replace") as source:
            for line in source:
                line = line.strip()
                if line.startswith("["):
                    section = line
                elif section == "[run_context]":
                    key, sep, value = line.partition(":")
                    if sep:
                        values[key.strip()] = value.strip()
        mode, noise = int(values["acquisition_mode"]), int(values["noise_test_mode"])
        # Older replay code overwrote capture metadata with online GUI settings.
        # Trust capture metadata only; inspect framing for old replay snapshots.
        if values.get("mode") == "capture" and (mode, noise) in ((0, 0), (1, 0), (1, 1), (1, 2)):
            return mode, noise, f"recorded configuration: {config.name}"
    except (OSError, KeyError, ValueError):
        pass

    # A copied DAT may have no sidecar. The two event formats encode header IDs
    # differently; compare complete header/trailer pairs, not individual tags.
    with path.open("rb") as source:
        data = source.read(1024 * 1024)
    votes = [0, 0]
    header = None
    for offset in range(0, len(data) - 4, 5):
        word = int.from_bytes(data[offset:offset+5], "big")
        tag = word >> 36
        if tag == 0xa:
            header = word
        elif tag == 0xc and header is not None:
            triggered = ((header >> 17) & 0xfff) == ((word >> 16) & 0xfff)
            triggerless = ((header >> 16) & 0xfffff) == ((word >> 16) & 0xfffff)
            if triggered != triggerless:
                votes[int(triggerless)] += 1
            header = None
    for mode in (0, 1):
        if votes[mode] >= 2 and votes[mode] > 3 * votes[1-mode]:
            return mode, 0, "DAT event header/trailer format"
    return int(fallback[0]), int(fallback[1]), "current mode selection (no conclusive recording metadata or framing)"
