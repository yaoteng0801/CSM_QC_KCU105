# MiniDAQ GUI

This directory contains the current `master` GUI for MiniDAQ configuration,
Ethernet acquisition, monitoring, geometry display, and `.dat` replay. The GUI
and all hardware-control paths are Ethernet-only. See the
[repository README](../README.md) for the firmware architecture, register 61
chamber map, FIFO configuration, and complete 40-bit data formats.

## Install and Run

```bash
cd GUI_DAQ
source ./install_native.sh
python GUI_DAQ_init.py
```

## Program a CSM FPGA over Ethernet

The [shared bitstream folder](../README.md#bitstream-downloads) is the location
for new FPGA builds. Download the CSM `.bit` file locally before selecting it
in the GUI; existing checked-in bit files remain available.

Select the board-facing interface on the **Ethernet Capture** tab. On the
**LpGBT Config** tab, select the `.bit` file and click **Program via Ethernet**
for CSM0 or CSM1. The current hardware route programs SCA0 on the selected CSM.
A preliminary IDCODE read is not required because the firmware performs its own
final DONE/INIT and JTAG capture-status check.

The GUI sends 1408-byte chunks using raw EtherType `0x88B5`. Progress advances
only after the FPGA returns both transport admission and SCA completion
acknowledgements. Every chunk has a CRC32, the complete bitstream has a CRC32,
and the FPGA reports the rolling CRC in each completion ACK. A lost frame or
ACK is retried at most three times with the same session/sequence identity;
cancel sends an ABORT frame and releases the firmware programmer.

The **Read IDCODE** button uses the same raw-Ethernet and SCA/JTAG path without
starting a programming session. Firmware returns `IDCODE_ACK` with the complete
32-bit value and the captured IR status, so the GUI reports IDCODE, DONE, and
INIT. The FPGA status indicator requires the expected `0x0362D093` IDCODE and,
when the bitstream supports status reporting, valid DONE/INIT. The request is
safe to repeat: a duplicate request replays the cached result instead of
rerunning the JTAG scan.

## Ethernet Traffic Classes

MiniDAQ uses three independent raw-Ethernet traffic classes:

- `0x0068`: detector hit frames. The FPGA TX scheduler gives this class
  priority whenever the hit FIFO contains at least 1024 40-bit words.
- `0x88B5`: programming and active control. FPGA register writes, lpGBT writes,
  SCA commands, JTAG programming, and their acknowledgements use this class.
- `0x88B6`: monitoring/readback. FPGA, lpGBT, and SCA read replies use a
  separate pair of request/result FIFOs. TX admission requires at most 256 hit
  words and is limited to one monitor frame per millisecond.

The generic `MDC1`/`MDM1` control protocol is version 2. FPGA readback remains
160 bits, but pages 1-4 and 6-8 are right-aligned at bit 0 and contain no
embedded page-address or UART-parity byte. Page 5 remains the complete 160-bit
BER record. The requested address is verified from the Ethernet response
metadata instead of from the readback payload.

Arbitration is locked until the selected frame's `TLAST`, so bytes from two
classes can never be interleaved. The acquisition capture filter accepts only
the exact `0x0068` hit class; control and monitoring replies are consumed by
the raw-Ethernet helper and never enter the hit decoder.

All GUI hardware access is now Ethernet-only. lpGBT requests carry their CSM
and master/slave target explicitly, so there is no persistent routing register
or legacy selection state in the FPGA.

The detector source MAC and capture filter are fixed by the current firmware:

```text
ether src 02:00:00:c7:05:01 and ether[12:2] = 0x0068
```

The low-level filter field is hidden in the normal workflow. The GUI removes
the obsolete `last/last_filter` setting from `capture_settings.ini` at startup
and always restores this filter, so an old saved filter cannot silently block
detector hits.

## Acquisition Profiles

Select the profile on the **Ethernet Capture** tab before live capture or DAT
replay:

| GUI profile | `acquisition_mode` | `noise_test_mode` | Data interpreted as |
|---|---:|---:|---|
| Triggered | 0 | 0 | Trigger-driven events |
| Triggerless | 1 | 0 | Per-chamber hit-driven events |
| Triggerless Noise Raw | 1 | 1 | Unframed raw hit words |
| Triggerless Noise Counter | 1 | 2 | One-second cumulative counter records |

For live capture, select the board-facing Ethernet interface, output directory,
run number, and profile, then click **Start DAQ**. The GUI applies and verifies
the selected mode before it starts hardware acquisition. It writes only the
detector words to the run `.dat` file while decoding the same stream for the
live plots.

**Remove isolated hits from .dat** is unchecked by default. In **Triggerless** event
mode, check it before starting to remove hits with no immediately adjacent
hit tube in the same chamber and multilayer. Neighbors include left/right and
the staggered tubes above/below, using physical centers from the loaded geometry
(including `.geo` files). All neighboring groups are retained; repeated hits in
one tube do not count as neighbors. The decision uses the complete event, before
software time cuts or track fitting.

After isolation removal, the writer reapplies the same enabled **Triggerless
Settings (MiniDAQ)** tube cuts for that chamber: minimum distinct tubes/event,
distinct tubes/every configured ML, distinct tubes/every configured layer, and
hit layers/every configured ML. All enabled cuts must pass. Duplicate hits and
channel aliases count as one tube; configured layers/MLs with no survivors count
as zero. As in firmware, an event must retain at least one mapped tube even when
all four cuts are disabled. Failing events, including their header, triggers and
trailer, are omitted from both DAT and live decoding. Event IDs are not renumbered.
The geometry and filter settings are snapshotted at capture start.

Filtering runs in the native capture writer, and the live decoder receives the
same filtered stream as the saved DAT. Event IDs, trigger words and word order
are preserved for passing events; their trailer hit counts are updated.
Unmapped hits are kept in passing events but do not contribute to tube cuts.
Damaged, aborted, packet-loss-affected or incomplete events
are saved unchanged. **Live Status → Capture and Throughput** shows isolated hits
removed, events filtered (examined), events rejected after isolation, and
damaged/incomplete events kept, without periodic
log messages. These totals reset at the start of each capture or replay.
The run's `_neighbors.txt` file records the geometry and tube cuts used for the
decision. The selection is saved between sessions and locked during capture;
triggered and noise profiles always save their original stream. DAT replay reads
the file as recorded. This option does not change FPGA firmware or Ethernet traffic.

**Display min hits** only controls which decoded events enter the Geometry
event-display buffer. It does not change the firmware `hit_threshold`, remove
events from spectra, or remove data from the `.dat` file. In triggerless mode,
an external trigger can also commit the current hardware event below the
configured `hit_threshold`, so a valid event can contain fewer hits than that
threshold.

## Triggerless Geometry Assignment

Current `master` supports at most two logical chambers, shown as Geometry 0 and
Geometry 1. A chamber is a firmware event-assembly group and does not have to
match the physical CSM number. Each chamber has its own triggerless event
builder, event sequence, trigger FIFO, and readout FIFO; both chambers share
the same RGMII output.

Each Geometry tab contains these subtabs in order:

1. **Geometry display**
2. **Settings**
3. **Event hit count**

TDC assignment is at the top of **Settings**, with the geometry fields arranged
in three columns below it. Geometry changes are applied automatically; there is
no separate Apply button. A TDC can be assigned to only one geometry.

When **Start DAQ** is pressed in triggerless mode, the GUI compares the enabled
Mezz Config TDCs with both Geometry assignments. If the sets differ, the
warning lists enabled-but-unassigned and assigned-but-disabled mezzanines and
offers **Start DAQ Anyway** or **Cancel**. Continuing excludes enabled but
unassigned TDCs from acquisition. The GUI then writes and verifies the
80-bit TDC chamber map in firmware register 61 before enabling the run; that
register can only be changed while the DAQ is stopped.

The **Event hit count** histogram displays hit-count bins 0 through 20 for its
geometry and automatically rescales the event-count axis. Events with more
than 20 hits are included in the total event count but accumulated silently
instead of being drawn as an overflow bin.

Triggerless event IDs contain a chamber bit and a chamber-local sequence:

```text
event_id20 = {chamber_id[0], chamber_sequence[18:0]}
```

The two chambers count independently. The GUI therefore does not report a
repeat or missing event merely because packets switch between chambers; an
event-ID mismatch means that a given event header and trailer disagree.

## Load a Chamber GEO File

In the appropriate **Geometry → Settings** tab, click **Load...** and select a
`.geo` table such as `EML1A05.geo`. Loading applies automatically. That example
imports 336 tubes: 6 layers (3 per multilayer), 56 columns, and 7 mezzanines per
multilayer with 8 columns per mezzanine.

The supported header is:

```text
MZ  MezzCh  locY  locZ  Layer  Tube_y  ML
```

`MZ` becomes the initial global TDC ID (0–39). `MezzCh` encodes
`100*(MZ+1)+channel`, with channel 0–23; a plain channel number is also accepted.
`Layer` is local to each multilayer; `Layer`, `Tube_y`, and `ML` start at 1.
The GUI uses `locZ` as horizontal x and `locY` as vertical y, in millimetres.
Every channel's wiring and tube centre comes directly from its row, including
differences between ML1 and ML2. Missing channels are left unmapped.

For an imported layout, dimensions and column counts are read-only. Change the
TDC IDs in the assignment grid to match the connected hardware; this preserves
each slot's channel wiring and tube positions. **Save...** writes a GUI `.txt`
configuration containing the full imported map, so it can be reloaded without
the original `.geo` file. Hit decoding, channel labels, NRT=2 multilayer
selection, and the triggerless firmware geometry table all use this map.

The GEO table contains no tube radius, drift limit, or tube length. Imports use
MDT defaults of 14.985 mm radius and 14.6 mm maximum drift distance and retain
the editor's tube length. These values remain editable under **Geometry**.

For regular layouts, **Total layers** and **Layers per ML** now stay in sync:
selecting 6 total layers with 2 multilayers selects 3 layers per ML. The
**Columns / mezz** choices follow the channel count and layers per ML, allowing
8 columns for a 24-channel, 3-layer mezzanine. Use the GEO import for the exact
EML wiring rather than relying on the regular-layout channel pattern.

## Process an Existing DAT File

An additional `offline_decode` program is not required. The GUI reuses its
normal decoder, spectra, Geometry displays, event navigation, and plot-saving
path for recorded files:

1. Select the `.dat` file in **Offline DAT Processing**.
2. Select the chamber's ROOT calibration or a legacy RT coefficient TXT file
   if track fitting is needed (see below).
3. Click **Process DAT**.

Replay reads the acquisition/noise modes from the original `_configuration.txt`
beside the DAT. Without usable capture metadata, it compares event headers and
trailers to distinguish triggered and triggerless framing. If neither identifies
the format (for example, a raw noise stream without metadata), the current mode
selection is used; choose the recording's profile in that case. The selected
decoder mode and its source are printed in the log. The DAT itself has no
self-describing format header.

Replay reports and plots go into a new `replays/<timestamp>/` folder beside the
DAT, preserving the original capture metadata, diagnostics, plots and duration.
Replay does not start hardware, change hardware mode, or modify the chamber map.
**Stop DAQ** also stops an active replay.

## RT Calibration and Multilayers

On **Geometry N → Settings → RT Calibration**, select the
chamber's `.root` file and leave **NRT** on **Auto**, or select **2 (ML1 / ML2)**.
Click **Apply RT** to load it for this geometry. Capture and replay preserve
the applied assignments. Stop an active capture or replay before changing RT.
The loaded filename, actual NRT, and time ranges appear below the controls.

Catalogue ROOT files contain ten Chebyshev coefficients in each of the vectors
`RTParam0` (ML1) and `RTParam1` (ML2). With NRT=2, the fitter, drift circles, and
fit residuals select the curve using the hit layer and the loaded geometry's
`MAX_TDC_LAYER`. Load the matching chamber geometry too: MDT and sMDT tube
radii, layer counts, and spacings differ. Each Geometry tab has an independent RT assignment.

For framed **Triggerless** capture and DAT replay, both TDC spectra use
`t_corr_ns - fitted T0`, with a separate fitted T0 for each chamber-event.
Only hits that pass the existing event-quality and fit-inlier selections enter
these spectra, so their totals can be smaller than the raw CH Hits totals.
The plot label is **Drift time (event T0)**, and its range follows the loaded
RT calibration. This requires a valid RT calibration and the C++ track fitter.
Triggered spectra continue to use `hit_ledge - trigger_ledge`.

These ROOT vectors do **not** include physical time limits. Leave **Catalogue
times** checked and keep the matching `<chamber>_ML1.txt` and
`<chamber>_ML2.txt` beside the ROOT file. The GUI reads their first and last times
to normalize time to [-1, 1]; coefficients always come from ROOT. For a standalone
ROOT file, uncheck that option to show the manual timing fields and enter the
calibrated Tmin/Tmax in ns for each multilayer. Missing tables or invalid ranges
are reported without replacing the previous calibration. Catalogue source tables
cannot be selected as coefficient TXT files.

Legacy one-coefficient-per-line TXT files use NRT=1 and default to 0–200 ns.
NRT=1 shares the first curve across both multilayers. File, NRT, and timing
choices are saved per geometry in `capture_settings.ini`. Run configuration
snapshots record each chamber’s RT file, coefficients and time ranges. ROOT reading uses
[Uproot](https://uproot.readthedocs.io/en/latest/basic.html), included in
`requirements.txt`; PyROOT is not required. Re-run `source ./install_native.sh`
after updating to install that dependency and rebuild the C++ fitter for NRT=2.

## Runtime Verification

When live capture starts successfully, the GUI output log reports:

```text
Native pcap initialized on <interface>
```

Open **Status / Diagnostics**, immediately beside **Ethernet Capture**, to view
**Live Status** (capture throughput and decoder counters) and **FPGA triggerless
diagnostics**. These displays continue updating during capture when another tab
is selected.

## Troubleshooting

### `native_decoder_cpp` cannot be imported

Make sure the extension was built with the same Python interpreter used to
launch MiniDAQ:

```bash
.venv/bin/python --version
cd native_decoder
../.venv/bin/python setup.py build_ext --inplace
cd ..
```

If Python was upgraded, remove stale files from `native_decoder/build/` and
old `native_decoder_cpp*.so` files, then rebuild.

Also rebuild after switching between branches that contain different decoder
interfaces. A stale extension can import successfully but still expose an old
constructor or data format.

### `trackfit_cpp` cannot be imported

Reinstall the fitter using the same virtual environment that runs MiniDAQ:

```bash
source .venv/bin/activate
python -m pip install --no-build-isolation -e ./cppfit
```

### `pybind11` or Python headers are missing

Activate the virtual environment and reinstall the Python dependencies:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Also install `python3-devel` on RHEL-family systems or `python3-dev` on
Debian-family systems.

### `pcap.h` is missing or the linker cannot find `-lpcap`

Install `libpcap-devel` on RHEL-family systems or `libpcap-dev` on
Debian-family systems, then rerun:

```bash
make -C native_capture
```

### Live capture reports `Operation not permitted`

Reapply the executable capabilities:

```bash
sudo setcap cap_net_raw,cap_net_admin=eip native_capture/minidaq_capture
sudo setcap cap_net_raw,cap_net_admin=eip native_capture/ethernet_frame_io
getcap native_capture/minidaq_capture
getcap native_capture/ethernet_frame_io
```

### The native capture helper is not built

The GUI expects the executables at exactly
`native_capture/minidaq_capture` and
`native_capture/ethernet_frame_io`. Build them from the `GUI_DAQ` directory:

```bash
make -C native_capture
```

### Packets arrive but the GUI reports no hits

Confirm that the incoming detector frames use source MAC
`02:00:00:c7:05:01` and bytes 12-13 equal `0x0068`. Control traffic with
EtherType `0x88B5` or `0x88B6` is intentionally not sent to the hit decoder.
Also verify that the selected GUI acquisition profile matches the programmed
firmware mode and rebuild `native_decoder_cpp` after changing branches.

### Triggerless chamber-map readback is zero or mismatched

Stop the DAQ and use a bitstream built from the current `master` firmware.
Older bitstreams do not implement the current register 61 mapping/readback.
If the mismatch persists with a current bitstream, inspect the Ethernet
control/readback path before bypassing the GUI check; acquisition is not
started after a failed map verification.

### Process DAT produces packets/words but no events

Select the acquisition profile used when the file was recorded. Triggered,
triggerless framed, noise-raw, and noise-counter streams require different
decoder interpretations.
