# MiniDAQ GUI on Windows

Copied from `phase2_MiniDAQ/GUI_DAQ` at commit `124dc6d` (2026-09-23), made to
run on Windows, then updated to upstream `1654ccb` (2026-11-03) by a three-way
merge (base `124dc6d`). On Linux every file behaves exactly as upstream: all Windows code
sits behind `sys.platform == "win32"` checks.

## Why the upstream GUI is Linux-only

Raw Ethernet (control, FPGA programming and detector data) goes through two
libpcap helpers in `native_capture/` (`ethernet_frame_io`, `minidaq_capture`)
that are built with `make` and granted `CAP_NET_RAW` with `setcap`. They use
POSIX APIs (`poll`, `fcntl`, signals). The Python side reads the interface MAC
with `fcntl.ioctl(SIOCGIFHWADDR)`, waits on pipes with `selectors`, and lists
interfaces with `pcapy-ng`. None of that exists on Windows.

## What replaces it

| Linux | Windows |
|---|---|
| `native_capture/ethernet_frame_io` (subprocess) | `win_pcap.PcapEthernetPort`, in-process through Npcap `wpcap.dll` |
| `fcntl.ioctl` MAC lookup | `win_pcap.interface_mac` (IP Helper API) |
| `native_capture/minidaq_capture` (subprocess) | `win_capture.run_live` inside `CaptureThread` |
| `native_capture/isolated_hits.h` | `isolated_hit_filter.py` (line-by-line port) |
| `pcapy.findalldevs()` | `win_pcap.list_devices()`; the combo box shows "Ethernet 3 - adapter (MAC)" |
| `install_native.sh` | `install_windows.ps1` + `requirements-windows.txt` |

Output is unchanged: same `.dat` words, same `MINIDAQ_STATS` / status lines.
`test_win_capture.py` runs the upstream native capture tests
(`test_isolated_hits.NativeIsolationTests`) against the Windows code.

Files changed from upstream: `ethernet_jtag_protocol.py`, `CaptureThread.py`,
`tab_capture.py`, `tab_lpgbt.py` (interface label), `tab_csm.py` and `tab_sca.py`
(matplotlib temp dir), `Worker_lpGBT.py` and `tab_elink.py` (CSV files found
next to the script, so the GUI can start from any directory), `GUI_DAQ_init.py`
(imports `win_runtime` first), `native_decoder/setup.py` and `cppfit/setup.py`
(MSVC options), `pop_prbs.py` and `pop_link_setup.py` (readback pages 6-8 decoded
for the link count `firmware_links.py` detects, any MiniDAQ build; not Windows
specific, worth sending upstream). New: `firmware_links.py`, `test_firmware_links.py`, `win_pcap.py`,
`win_capture.py`, `isolated_hit_filter.py`, `win_runtime.py`, `test_win_capture.py`, `cppfit/msvc_compat.h`,
`install_windows.ps1`, `requirements-windows.txt`, this file.

C++ extensions with MSVC: both build with Visual Studio 2022 Build Tools.
`trackfit_cpp.cpp` uses the POSIX `ssize_t`, supplied by the force-included
`cppfit/msvc_compat.h`. Both extensions are compiled with
`_DISABLE_CONSTEXPR_MUTEX_CONSTRUCTOR`: PyQt5-Qt5 5.15.2 loads an old
`msvcp140.dll`, and `std::mutex` built with MSVC 17.10+ otherwise crashes the
GUI on import (access violation in `import native_decoder_cpp`).
Third-party extensions have the same problem: `awkward_cpp` (used by `uproot`
for ROOT RT files) crashes when imported after PyQt5. `win_runtime.py`, imported
first by `GUI_DAQ_init.py`, loads the newer `msvcp140.dll` from System32 before
PyQt5 so every module shares it.

## Updating to a newer upstream

Upstream files are CRLF. Merge each file changed on both sides with line endings
normalised (`git merge-file` on LF copies of ours/base/theirs, then back to
CRLF); otherwise the whole file shows as one conflict. Rebuild `native_decoder`
when `native_decoder.cpp` changes (close the GUI first: Windows locks the
loaded `.pyd`).

Run the unit tests with `.\.venv\Scripts\python.exe -m win_runtime` (the same
runtime preload, then `unittest discover`). 2026-11-04, upstream `1654ccb` plus
the CSM QC page: all pass except `NativeIsolationTests` (g++). The GUI starts
with 11 tabs (CSM and SCA monitoring are one Monitoring tab upstream).

## CSM QC page

`tab_qc.py` is the page and `csm_qc.py` the sequence; neither exists upstream.
They also add small hooks to `tab_lpgbt.py` (result callbacks on the IDCODE and
programming starts), `Worker_Monitor.py` and `tab_monitor.py` (`scan_limit`) and
`MainWindow.py` (the tab and `show_adc_plots`). Keep these when merging upstream.
Results go to `<output>/<serial>/<operator>/YYYYMMDDHHMM/`: `qc_summary.txt`,
`qc_summary.json`, `qc_log.txt`, the monitoring CSV and plot, `plots/ADC_overall/`
and the capture's run folder. `PRBS_LINE_RATE_BPS` in `csm_qc.py` is 12.8e9 as the
QC procedure specifies; the transceivers themselves run at 10.24 Gb/s.

Tested on Windows 11, Python 3.11, Npcap 1.90 (2026-10-28): all upstream unit
tests pass except `test_isolated_hits.NativeIsolationTests`, which compiles the
Linux helper with g++; `test_win_capture.py` runs those cases against the Windows
code (15/15). The full GUI starts (11 tabs, native decoder and track fitting
active). 2026-10-29: Ethernet control to the KCU105 works (FPGA register
writes and link-status readback). Later the same day: master and slave lpGBT
configured (uplink ready = 11), CSM FPGA IDCODE read over the SCA.

Upstream `1654ccb` also adds firmware registers 71 (external-trigger logic) and
72 (SMA trigger gates). With firmware older than that, the GUI shows "Local
settings only" for the external-trigger editor and the FPGA ignores writes to
71/72; everything else works.

## Install and run

1. Install **Npcap** from https://npcap.com (administrator). Legacy WinPcap 4.1
   also works but is unmaintained. If you tick "Restrict Npcap driver's access
   to Administrators only", start the GUI as administrator.
2. In PowerShell:

   ```powershell
   cd GUI_DAQ
   powershell -ExecutionPolicy Bypass -File .\install_windows.ps1
   .\.venv\Scripts\python.exe GUI_DAQ_init.py
   ```

3. On the **Ethernet Capture** tab select the adapter cabled to the KCU105
   (for the 1000BASE-T link: a gigabit NIC, no IP configuration needed).

## Limits

* Detector-data capture runs in Python (numpy per packet). It is meant for
  bring-up and moderate rates; at full gigabit line rate expect kernel drops,
  which are reported as `[WARN] libpcap kernel drops`. The `.dat` file is still
  written in order.
* The C++ extensions (`native_decoder`, `cppfit`) need MSVC Build Tools (the
  installer builds them when found). Without them the GUI falls back to the
  Python decoder and track fitting is disabled.
* Without a saved choice the capture tab selects the first adapter with link
  (often the office NIC). Select the KCU105 adapter once; the GUI remembers it.
* `numpy==2.4.1` needs Python 3.11 or newer (the installer defaults to 3.11).
