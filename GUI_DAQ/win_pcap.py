"""Windows packet I/O for MiniDAQ through Npcap (or legacy WinPcap) ``wpcap.dll``.

On Linux the GUI delegates raw Ethernet to two small libpcap helpers in
``native_capture/`` that are granted CAP_NET_RAW with setcap.  Those helpers are
written against POSIX (poll, fcntl, signals) and are not built on Windows.  This
module provides the same services in-process through ctypes:

* adapter enumeration with friendly names and MAC addresses,
* ``PcapEthernetPort``: the raw-Ethernet control/programming port used by
  ``ethernet_jtag_protocol.NativeEthernetPort`` (same open/close/send_frame/
  receive_frame/source_mac interface),
* thin wrappers used by ``win_capture.py`` for detector-data capture.

Requires Npcap (https://npcap.com).  Npcap installed in "WinPcap API-compatible
mode" or the legacy WinPcap 4.1 driver also work: only the classic libpcap API
plus the Windows ``pcap_setbuff``/``pcap_setmintocopy`` extensions are used.
"""

from __future__ import annotations

import ctypes
import os
import queue
import sys
import threading
from typing import Dict, List, Optional

IS_WINDOWS = sys.platform == "win32"

PCAP_ERRBUF_SIZE = 256
FPGA_MAC_TEXT = "02:00:00:c7:05:01"
# Same filter as native_capture/ethernet_frame_io.cpp.
CONTROL_REPLY_FILTER = (
    "(ether proto 0x88b5 or ether proto 0x88b6) and "
    f"ether src {FPGA_MAC_TEXT}"
)
NETMASK_UNKNOWN = 0xFFFFFFFF


class PcapError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# libpcap structures (Windows layout: struct timeval uses 32-bit longs)
# ---------------------------------------------------------------------------

class TimeVal(ctypes.Structure):
    _fields_ = [("tv_sec", ctypes.c_long), ("tv_usec", ctypes.c_long)]


class PcapPkthdr(ctypes.Structure):
    _fields_ = [("ts", TimeVal), ("caplen", ctypes.c_uint32), ("len", ctypes.c_uint32)]


class BpfProgram(ctypes.Structure):
    _fields_ = [("bf_len", ctypes.c_uint), ("bf_insns", ctypes.c_void_p)]


class PcapStat(ctypes.Structure):
    # ps_capt/ps_sent/ps_netdrop exist with remote capture enabled; the spare
    # fields keep the buffer large enough for either layout.
    _fields_ = [
        ("ps_recv", ctypes.c_uint),
        ("ps_drop", ctypes.c_uint),
        ("ps_ifdrop", ctypes.c_uint),
        ("_spare", ctypes.c_uint * 4),
    ]


class PcapIf(ctypes.Structure):
    pass


PcapIf._fields_ = [
    ("next", ctypes.POINTER(PcapIf)),
    ("name", ctypes.c_char_p),
    ("description", ctypes.c_char_p),
    ("addresses", ctypes.c_void_p),
    ("flags", ctypes.c_uint),
]

PCAP_HANDLER = ctypes.CFUNCTYPE(
    None, ctypes.c_void_p, ctypes.POINTER(PcapPkthdr), ctypes.POINTER(ctypes.c_ubyte)
)

_lib = None
_lib_path = ""


def _load_library():
    """Load wpcap.dll once.  Npcap's native directory is preferred."""
    global _lib, _lib_path
    if _lib is not None:
        return _lib
    if not IS_WINDOWS:
        raise PcapError("win_pcap is only used on Windows")

    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    npcap_dir = os.path.join(system_root, "System32", "Npcap")
    candidates = []
    if os.path.isfile(os.path.join(npcap_dir, "wpcap.dll")):
        candidates.append((npcap_dir, os.path.join(npcap_dir, "wpcap.dll")))
    candidates.append((None, "wpcap.dll"))  # WinPcap or Npcap compatible mode

    errors = []
    for directory, path in candidates:
        try:
            if directory:
                # Packet.dll lives beside Npcap's wpcap.dll.
                os.add_dll_directory(directory)
            lib = ctypes.CDLL(path)
        except OSError as error:
            errors.append(f"{path}: {error}")
            continue
        _declare(lib)
        _lib, _lib_path = lib, path
        return lib

    raise PcapError(
        "Npcap is not installed (wpcap.dll not found). Install Npcap from "
        "https://npcap.com and run the GUI again. Details: " + "; ".join(errors)
    )


def _declare(lib) -> None:
    p = ctypes.c_void_p
    sigs = {
        "pcap_findalldevs": ([ctypes.POINTER(ctypes.POINTER(PcapIf)), ctypes.c_char_p], ctypes.c_int),
        "pcap_freealldevs": ([ctypes.POINTER(PcapIf)], None),
        "pcap_open_live": ([ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_char_p], p),
        "pcap_open_dead": ([ctypes.c_int, ctypes.c_int], p),
        "pcap_close": ([p], None),
        "pcap_compile": ([p, ctypes.POINTER(BpfProgram), ctypes.c_char_p, ctypes.c_int, ctypes.c_uint32], ctypes.c_int),
        "pcap_setfilter": ([p, ctypes.POINTER(BpfProgram)], ctypes.c_int),
        "pcap_freecode": ([ctypes.POINTER(BpfProgram)], None),
        "pcap_next_ex": ([p, ctypes.POINTER(ctypes.POINTER(PcapPkthdr)), ctypes.POINTER(ctypes.POINTER(ctypes.c_ubyte))], ctypes.c_int),
        "pcap_dispatch": ([p, ctypes.c_int, PCAP_HANDLER, ctypes.c_void_p], ctypes.c_int),
        "pcap_sendpacket": ([p, ctypes.c_char_p, ctypes.c_int], ctypes.c_int),
        "pcap_stats": ([p, ctypes.POINTER(PcapStat)], ctypes.c_int),
        "pcap_geterr": ([p], ctypes.c_char_p),
        "pcap_breakloop": ([p], None),
        "pcap_lib_version": ([], ctypes.c_char_p),
        # Windows extensions present in both WinPcap and Npcap.
        "pcap_setbuff": ([p, ctypes.c_int], ctypes.c_int),
        "pcap_setmintocopy": ([p, ctypes.c_int], ctypes.c_int),
    }
    for name, (argtypes, restype) in sigs.items():
        function = getattr(lib, name, None)
        if function is None:
            continue
        function.argtypes = argtypes
        function.restype = restype


def library_version() -> str:
    lib = _load_library()
    version = lib.pcap_lib_version()
    return (version or b"").decode(errors="replace") + f" [{_lib_path}]"


def _err(lib, handle) -> str:
    text = lib.pcap_geterr(handle)
    return text.decode(errors="replace") if text else "unknown pcap error"


# ---------------------------------------------------------------------------
# Adapter enumeration and MAC addresses (IP Helper API)
# ---------------------------------------------------------------------------

class _IpAdapterAddresses(ctypes.Structure):
    # Leading fields of IP_ADAPTER_ADDRESSES (iptypes.h); only these are read.
    _fields_ = [
        ("Length", ctypes.c_ulong),
        ("IfIndex", ctypes.c_ulong),
        ("Next", ctypes.c_void_p),
        ("AdapterName", ctypes.c_char_p),
        ("FirstUnicastAddress", ctypes.c_void_p),
        ("FirstAnycastAddress", ctypes.c_void_p),
        ("FirstMulticastAddress", ctypes.c_void_p),
        ("FirstDnsServerAddress", ctypes.c_void_p),
        ("DnsSuffix", ctypes.c_wchar_p),
        ("Description", ctypes.c_wchar_p),
        ("FriendlyName", ctypes.c_wchar_p),
        ("PhysicalAddress", ctypes.c_ubyte * 8),
        ("PhysicalAddressLength", ctypes.c_ulong),
        ("Flags", ctypes.c_ulong),
        ("Mtu", ctypes.c_ulong),
        ("IfType", ctypes.c_ulong),
        ("OperStatus", ctypes.c_int),
    ]


def _windows_adapters() -> Dict[str, dict]:
    """Return {"{GUID}": {friendly, description, mac, up}} for all adapters."""
    iphlpapi = ctypes.WinDLL("iphlpapi")
    get = iphlpapi.GetAdaptersAddresses
    get.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p,
                    ctypes.POINTER(ctypes.c_ulong)]
    get.restype = ctypes.c_ulong
    flags = 0x0002 | 0x0004 | 0x0008 | 0x0100  # skip anycast/multicast/DNS, include all
    size = ctypes.c_ulong(32 * 1024)
    for _ in range(4):
        buffer = ctypes.create_string_buffer(size.value)
        result = get(0, flags, None, buffer, ctypes.byref(size))
        if result == 0:
            break
        if result != 111:  # ERROR_BUFFER_OVERFLOW
            raise PcapError(f"GetAdaptersAddresses failed with error {result}")
    else:
        raise PcapError("GetAdaptersAddresses: buffer size did not converge")

    adapters: Dict[str, dict] = {}
    address = ctypes.addressof(buffer)
    while address:
        entry = _IpAdapterAddresses.from_address(address)
        guid = (entry.AdapterName or b"").decode(errors="replace").upper()
        mac = bytes(entry.PhysicalAddress[: min(entry.PhysicalAddressLength, 8)])
        adapters[guid] = {
            "friendly": entry.FriendlyName or "",
            "description": entry.Description or "",
            "mac": mac if len(mac) == 6 else b"",
            "up": entry.OperStatus == 1,
        }
        address = entry.Next or 0
    return adapters


def _guid_of(device: str) -> str:
    start, end = device.find("{"), device.rfind("}")
    return device[start:end + 1].upper() if 0 <= start < end else ""


def list_devices() -> List[dict]:
    """Capture devices with friendly name, description, MAC and link state.

    ``name`` is the libpcap device string (``\\Device\\NPF_{GUID}``) that must be
    passed to every other function.
    """
    lib = _load_library()
    errbuf = ctypes.create_string_buffer(PCAP_ERRBUF_SIZE)
    head = ctypes.POINTER(PcapIf)()
    if lib.pcap_findalldevs(ctypes.byref(head), errbuf) != 0:
        raise PcapError("pcap_findalldevs failed: " + errbuf.value.decode(errors="replace"))
    try:
        adapters = _windows_adapters()
    except Exception:
        adapters = {}

    devices = []
    node = head
    try:
        while node:
            item = node.contents
            name = (item.name or b"").decode(errors="replace")
            info = adapters.get(_guid_of(name), {})
            description = info.get("description") or (item.description or b"").decode(errors="replace")
            devices.append({
                "name": name,
                "friendly": info.get("friendly", ""),
                "description": description,
                "mac": info.get("mac", b""),
                "up": bool(info.get("up", False)),
                "loopback": "loopback" in (name + description).lower(),
            })
            node = item.next
    finally:
        lib.pcap_freealldevs(head)
    return devices


def format_mac(mac: bytes) -> str:
    return ":".join(f"{b:02x}" for b in mac) if mac else "no MAC"


def device_label(device: dict) -> str:
    """Human-readable combo-box label."""
    head = device["friendly"] or device["description"] or device["name"]
    tail = device["description"] if device["friendly"] else ""
    state = "" if device["up"] else ", link down"
    text = f"{head} - {tail}" if tail and tail != head else head
    return f"{text} ({format_mac(device['mac'])}{state})"


def resolve_device(device: str) -> str:
    """Accept an NPF name, a friendly name ("Ethernet 3") or a MAC address."""
    device = str(device or "").strip()
    if device.upper().startswith("\\DEVICE\\"):
        return device
    wanted = device.lower().replace("-", ":")
    for entry in list_devices():
        if device == device_label(entry) or wanted in (entry["friendly"].lower(), format_mac(entry["mac"])):
            return entry["name"]
    raise PcapError(f"Unknown network interface {device!r}")


def describe_device(device: str) -> str:
    """Combo-box label for a device name; the name itself if it is unknown."""
    for entry in list_devices():
        if entry["name"] == device:
            return device_label(entry)
    return device


def interface_mac(device: str) -> bytes:
    """MAC address of a capture device (NPF name or friendly name)."""
    name = resolve_device(device)
    adapters = _windows_adapters()
    mac = adapters.get(_guid_of(name), {}).get("mac", b"")
    if len(mac) != 6 or mac == b"\x00" * 6:
        raise PcapError(f"Interface {device!r} does not have a usable Ethernet MAC address")
    return mac


# ---------------------------------------------------------------------------
# Handles
# ---------------------------------------------------------------------------

def open_live(device: str, *, snaplen: int = 65536, promisc: bool = True,
              timeout_ms: int = 100, kernel_buffer_bytes: int = 0,
              immediate: bool = False):
    """Open a live capture handle; returns (lib, handle)."""
    lib = _load_library()
    name = resolve_device(device)
    errbuf = ctypes.create_string_buffer(PCAP_ERRBUF_SIZE)
    handle = lib.pcap_open_live(name.encode(), int(snaplen), int(bool(promisc)),
                                int(timeout_ms), errbuf)
    if not handle:
        raise PcapError(
            f"pcap_open_live failed on {name}: {errbuf.value.decode(errors='replace')}. "
            "Check that Npcap is installed and, if it was installed with "
            "'Restrict Npcap driver's access to Administrators only', run the GUI as administrator."
        )
    if kernel_buffer_bytes and getattr(lib, "pcap_setbuff", None) is not None:
        lib.pcap_setbuff(handle, int(kernel_buffer_bytes))
    if immediate and getattr(lib, "pcap_setmintocopy", None) is not None:
        lib.pcap_setmintocopy(handle, 0)  # deliver every packet without batching
    return lib, handle


def set_filter(lib, handle, expression: str) -> None:
    if not expression:
        return
    program = BpfProgram()
    if lib.pcap_compile(handle, ctypes.byref(program), expression.encode(), 1, NETMASK_UNKNOWN) < 0:
        raise PcapError(f"pcap_compile failed for {expression!r}: {_err(lib, handle)}")
    try:
        if lib.pcap_setfilter(handle, ctypes.byref(program)) < 0:
            raise PcapError(f"pcap_setfilter failed: {_err(lib, handle)}")
    finally:
        lib.pcap_freecode(ctypes.byref(program))


def check_filter(expression: str) -> None:
    """Compile a filter against an offline Ethernet handle (self-test)."""
    lib = _load_library()
    handle = lib.pcap_open_dead(1, 65535)  # DLT_EN10MB
    if not handle:
        raise PcapError("pcap_open_dead failed")
    try:
        program = BpfProgram()
        if lib.pcap_compile(handle, ctypes.byref(program), expression.encode(), 1, NETMASK_UNKNOWN) < 0:
            raise PcapError(f"pcap_compile failed for {expression!r}: {_err(lib, handle)}")
        lib.pcap_freecode(ctypes.byref(program))
    finally:
        lib.pcap_close(handle)


def stats(lib, handle):
    value = PcapStat()
    if lib.pcap_stats(handle, ctypes.byref(value)) != 0:
        return 0, 0, 0
    return int(value.ps_recv), int(value.ps_drop), int(value.ps_ifdrop)


# ---------------------------------------------------------------------------
# Raw-Ethernet control/programming port
# ---------------------------------------------------------------------------

class PcapEthernetPort:
    """In-process replacement for the Linux ``ethernet_frame_io`` helper.

    One handle receives the FPGA's 0x88B5/0x88B6 replies on a background
    thread; a second handle transmits, so sending never waits behind a
    blocked read.  Frames are passed whole, without the helper's length prefix.
    """

    MAX_FRAME_BYTES = 65535
    RX_TIMEOUT_MS = 20
    error_class = PcapError

    def __init__(self, device: str):
        self.device = str(device or "").strip()
        try:
            self._pcap_name = resolve_device(self.device)
            self.source_mac = interface_mac(self._pcap_name)
        except PcapError as error:
            raise self.error_class(str(error)) from error
        self._lib = None
        self._rx = None
        self._tx = None
        self._frames: "queue.Queue[bytes]" = queue.Queue()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._rx_error = ""

    def open(self) -> None:
        if self._thread is not None:
            return
        try:
            lib, rx = open_live(self._pcap_name, snaplen=self.MAX_FRAME_BYTES,
                                timeout_ms=self.RX_TIMEOUT_MS, immediate=True)
            try:
                set_filter(lib, rx, CONTROL_REPLY_FILTER)
                _, tx = open_live(self._pcap_name, snaplen=64, timeout_ms=1)
            except Exception:
                lib.pcap_close(rx)
                raise
        except PcapError as error:
            raise self.error_class(f"Ethernet port did not initialize: {error}") from error
        self._lib, self._rx, self._tx = lib, rx, tx
        self._stop.clear()
        self._thread = threading.Thread(target=self._receive_loop, name="minidaq-eth-rx", daemon=True)
        self._thread.start()

    def _receive_loop(self) -> None:
        lib, handle = self._lib, self._rx
        header = ctypes.POINTER(PcapPkthdr)()
        data = ctypes.POINTER(ctypes.c_ubyte)()
        while not self._stop.is_set():
            result = lib.pcap_next_ex(handle, ctypes.byref(header), ctypes.byref(data))
            if result == 1:
                length = header.contents.caplen
                if 14 <= length <= self.MAX_FRAME_BYTES:
                    self._frames.put(ctypes.string_at(data, length))
            elif result < 0:
                if not self._stop.is_set():
                    self._rx_error = f"pcap_next_ex failed: {_err(lib, handle)}"
                return

    def close(self) -> None:
        thread, self._thread = self._thread, None
        self._stop.set()
        if thread is not None:
            thread.join(timeout=2.0)
        for attribute in ("_rx", "_tx"):
            handle = getattr(self, attribute)
            if handle is not None and self._lib is not None:
                self._lib.pcap_close(handle)
            setattr(self, attribute, None)

    def __enter__(self) -> "PcapEthernetPort":
        self.open()
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback) -> None:
        self.close()

    def send_frame(self, frame: bytes) -> None:
        if not 14 <= len(frame) <= self.MAX_FRAME_BYTES:
            raise ValueError(f"invalid raw Ethernet frame length {len(frame)}")
        if self._tx is None:
            raise self.error_class("Ethernet port is not open")
        if self._lib.pcap_sendpacket(self._tx, bytes(frame), len(frame)) != 0:
            raise self.error_class(f"Ethernet frame injection failed: {_err(self._lib, self._tx)}")

    def receive_frame(self, timeout: float) -> Optional[bytes]:
        if self._thread is None:
            raise self.error_class("Ethernet port is not open")
        try:
            return self._frames.get(timeout=max(0.0, timeout))
        except queue.Empty:
            if self._rx_error:
                raise self.error_class("Ethernet receive failed: " + self._rx_error)
            return None


def self_test() -> int:
    """Print the library, devices and compile the production filters."""
    print("pcap library:", library_version())
    check_filter(CONTROL_REPLY_FILTER)
    check_filter(f"ether src {FPGA_MAC_TEXT} and ether[12:2] = 0x0068")
    print("filters: OK")
    for device in list_devices():
        print(("  * " if device["up"] else "    ") + device_label(device) + "  " + device["name"])
    return 0


if __name__ == "__main__":
    sys.exit(self_test())
