# KCU105 MiniDAQ

Firmware and control software for running a CSM (lpGBT-based chamber service module) from a Xilinx
KCU105 evaluation board: 2 uplinks, 1 downlink, Ethernet control and readout. The GUI also runs an
automated CSM QC sequence.

| Folder | Contents |
| --- | --- |
| `bitstreams/` | Ready-to-load FPGA files |
| `GUI_DAQ/` | Control, capture and QC software (Python, PyQt5) |
| `rtl/`, `constr/`, `tcl/` | Firmware source, constraints and build scripts |

## Hardware

- KCU105 board (`xcku040-ffva1156-2-e`), with JTAG over USB
- 320 MHz reference clock on the SMA pair J33/J32. Without it nothing works, Ethernet included
- Master lpGBT on SFP0, slave lpGBT on SFP1
- Gigabit Ethernet from the board's RJ45 to the PC

## Quick start with the prebuilt bitstreams

### 1. Load the KCU105

Needs Vivado or Vivado Lab with `vivado` on the path. From the repo root:

```bash
vivado -mode batch -nojournal -nolog -source tcl/program_kcu105.tcl
```

### 2. Install and start the software

On Windows, install [Npcap](https://npcap.com) and Python 3.11, then in PowerShell:

```powershell
cd GUI_DAQ
powershell -ExecutionPolicy Bypass -File .\install_windows.ps1
.\.venv\Scripts\python.exe GUI_DAQ_init.py
```

Compiled decoder and fitter modules for 64-bit Windows and Python 3.11 are included. More detail is
in [GUI_DAQ/README_WINDOWS.md](GUI_DAQ/README_WINDOWS.md), and Linux setup is in
[GUI_DAQ/README.md](GUI_DAQ/README.md).

### 3. Bring up the CSM

Select the network adapter on the **Ethernet Capture** page, then use **LpGBT Config** by hand or run
everything from the **CSM QC** page. Both already point at the CSM bitstream below.

## Bitstream downloads

| File | Loads into |
| --- | --- |
| `bitstreams/kcu105_minidaq.bit` | KCU105 (`.ltx` is its debug-probe file) |
| `bitstreams/lpgbtcsm_fpga_top.bit` | CSM FPGA, over Ethernet from the GUI |

## Rebuild the firmware

Needs Vivado 2024.1 and a licence for the Tri-Mode Ethernet MAC (`tri_mode_eth_mac`). Clone to a short
path such as `D:\kcu105-minidaq`, because Vivado's generated paths can exceed the 260-character limit
on Windows. From the repo root:

```bash
mkdir build
vivado -mode batch -nojournal -log build/vivado_build.log -source tcl/build_full.tcl
```

This generates all IP, synthesises, implements and writes `build/kcu105_minidaq.bit`. Expect about
45 minutes. The build stops before writing a bitstream if timing is not met. AMD's Ethernet support
files are not in this repo; the build takes them from Vivado.

## Rebuild the software

Running `install_windows.ps1` again rebuilds the C++ modules if the MSVC Build Tools are installed.
Without them the GUI uses the included modules. To run the tests:

```powershell
.\.venv\Scripts\python.exe -m win_runtime
```

`NativeIsolationTests` needs `g++` and fails without it.

## Known limit

The firmware is based on upstream commit `124dc6d` and the software on `1654ccb`. The firmware lacks
the external-trigger registers 71 and 72, so the GUI shows "Local settings only" for that editor.

## Licence

No licence is granted. You may view this code, but all rights are reserved and it may not be reused
without permission. It includes work by other authors, whose rights remain theirs: the MiniDAQ
firmware and GUI (`phase2_MiniDAQ`, Yuxiang Guo) and the CERN lpGBT-FPGA and GBT-SC cores. AMD/Xilinx
tools and IP are subject to AMD's own licences.
