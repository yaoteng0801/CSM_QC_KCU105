"""Low-level MiniDAQ operations over the raw-Ethernet control protocol."""

from contextlib import contextmanager
from functools import wraps
import math
import threading

from JTAGTAPController import JTAGTAPController
from SCA_share import SCA_share
from sca_transaction_ids import validate_sca_transaction_id, next_sca_transaction_id
from lpgbt_register_map_v1 import LpgbtRegisterMapV1
from ethernet_control_protocol import (
    FPGA_READ,
    FPGA_RESET,
    FPGA_WRITE,
    LPGBT_READ,
    LPGBT_WRITE,
    SCA_COMMAND,
    SCA_CONNECT,
    SCA_RESET,
)


LPGBT_V1_LAST_WRITABLE_REGISTER = 0x14F
SCA_REPLY_LENGTH = 9
_fallback_locks_guard = threading.Lock()
_fallback_locks = {}
_sca_retry_context = threading.local()


class SCAReplyMismatchError(RuntimeError):
    """Ethernet responded, but no SCA record matched the command ID/channel."""


@contextmanager
def sca_reply_retry_reporting(callback):
    """Route recovery messages to the current worker's GUI signal."""
    previous = getattr(_sca_retry_context, "callback", None)
    _sca_retry_context.callback = callback
    try:
        yield
    finally:
        _sca_retry_context.callback = previous


def _report_sca_retry(message, callback=None):
    callback = callback or getattr(_sca_retry_context, "callback", None)
    if callback is not None:
        callback(message)
    else:
        print(message)


def get_ethernet_lock(eth):
    lock = getattr(eth, "_lock", None)
    if lock is not None:
        return lock
    with _fallback_locks_guard:
        return _fallback_locks.setdefault(id(eth), threading.RLock())


@contextmanager
def ethernet_exclusive_session(eth):
    """Keep a multi-command IC/SCA/JTAG operation transactionally ordered."""
    with get_ethernet_lock(eth):
        yield


def ethernet_locked(function):
    first_argument = function.__code__.co_varnames[0]

    @wraps(function)
    def locked(*args, **kwargs):
        if args:
            eth = args[0]
        elif first_argument in kwargs:
            eth = kwargs[first_argument]
        else:
            raise TypeError(
                f"{function.__name__}() is missing required argument "
                f"'{first_argument}'"
            )
        with ethernet_exclusive_session(eth):
            return function(*args, **kwargs)

    return locked


def ethernet_locked_method(function):
    @wraps(function)
    def locked(self, *args, **kwargs):
        with ethernet_exclusive_session(self.eth):
            return function(self, *args, **kwargs)
    return locked


def str_to_hex(data, interval=""):
    return "".join(f"{byte:02x}{interval}" for byte in bytes(data)).rstrip(interval)


def str_to_bin(data, interval=""):
    return "".join(f"{byte:08b}{interval}" for byte in bytes(data)).rstrip(interval)


def bin_to_hex_8bit(value):
    if len(value) != 8:
        print("Error the length of string is not 8")
        return ""
    return f"{int(value, 2):02x}"


def bin_to_hex(value):
    if len(value) % 8:
        print("Error the length of string is not 8N")
        return ""
    return bytes(int(value[i:i + 8], 2) for i in range(0, len(value), 8))


def chk_len(value, length):
    if int(value) < 0 or int(value) >= (1 << length):
        print(f"variable length incorrect! {value}")
        return 1
    return 0


def value_to_list(value):
    value = int(value)
    length = max(1, (value.bit_length() + 7) // 8)
    return list(value.to_bytes(length, "big"))


def _report_lpgbt_verification_error(verification, message):
    if verification is None:
        print(message)
    else:
        verification.setdefault("errors", []).append(message)


def _lpgbt_v1_range_is_writable(reg_addr, length):
    return length > 0 and 0 <= reg_addr <= reg_addr + length - 1 <= LPGBT_V1_LAST_WRITABLE_REGISTER


def _selected_uplink(eth, which_csm=None, lpgbt_addr=117):
    if which_csm is None:
        raise ValueError("which_csm is required for Ethernet lpGBT access")
    # Board convention: master address 117 uses even uplinks; slave address
    # 115 uses odd uplinks.  Unknown addresses retain the selected master path.
    slave = 1 if int(lpgbt_addr) == 115 else 0
    return 2 * int(which_csm) + slave


def _decode_lpgbt_reply(raw, verbose=True, tx_parity=None, verification=None):
    raw = bytes(raw)
    # The gbt-sc IC deserializer removes both 0x7E HDLC delimiters.  Ethernet
    # carries the resulting FIFO bytes directly:
    #   address, status, count[7:0], count[15:8], register[7:0],
    #   register[15:8], data..., parity.
    if len(raw) < 7:
        _report_lpgbt_verification_error(verification, "Incomplete lpGBT IC reply")
        return -1
    count = raw[2] | (raw[3] << 8)
    if len(raw) != 7 + count:
        _report_lpgbt_verification_error(
            verification,
            f"Reply length mismatch: received {len(raw)}, expected {7 + count}.",
        )
        return -1
    lpgbt_address = raw[0] // 2
    status = raw[1]
    reg_addr = raw[4] | (raw[5] << 8)
    data = list(raw[6:6 + count])
    parity_received = raw[-1]
    parity_calculated = 0
    # Parity covers the address through the final data byte.
    for byte in raw[:-1]:
        parity_calculated ^= byte
    if verification is not None:
        verification.update(
            reply_lpgbt_addr=lpgbt_address,
            reply_command=status,
            reply_data_count=count,
            reply_reg_addr=reg_addr,
            reply_data=data,
            rx_parity=parity_received,
            rx_parity_cal=parity_calculated,
        )
    if status != 1:
        _report_lpgbt_verification_error(
            verification, f"Downlink parity rejected: status=0x{status:02X}."
        )
    if parity_calculated != parity_received:
        _report_lpgbt_verification_error(
            verification,
            f"Uplink parity mismatch: received 0x{parity_received:02X}, "
            f"calculated 0x{parity_calculated:02X}.",
        )
    if tx_parity is not None and status == 1 and _lpgbt_v1_range_is_writable(reg_addr, count):
        expected = int(tx_parity) ^ 1
        if parity_received != expected:
            _report_lpgbt_verification_error(
                verification,
                f"Write/read parity mismatch: expected 0x{expected:02X}, "
                f"received 0x{parity_received:02X}.",
            )
    if verbose:
        print(
            f"Lpgbt{lpgbt_address} reply {count} regs from reg{reg_addr}, "
            f"value={data}, rx_parity={parity_received:08b}, "
            f"rx_parity_cal={parity_calculated:08b}"
        )
    return data


def lpgbt_read_back_print(readback_hex, verbose=True, tx_parity=None, verification=None):
    return _decode_lpgbt_reply(
        bytes.fromhex(readback_hex), verbose, tx_parity, verification
    )


@ethernet_locked
def fpga_config(eth, fpga_reg_addr, value_list):
    values = bytes(int(value) & 0xFF for value in value_list)
    if len(values) > 20:
        raise ValueError("FPGA register value exceeds the 160-bit payload")
    payload = values.rjust(20, b"\x00")
    eth.request(FPGA_WRITE, address=int(fpga_reg_addr), payload=payload)
    return 0


@ethernet_locked
def fpga_readback(eth, fpga_reg_addr, selector=0):
    expected_address = int(fpga_reg_addr) & 0xFFFF
    if not 0 <= int(selector) <= 255:
        raise ValueError("FPGA readback selector must be 0..255")
    options = {"subtarget": int(selector)} if selector else {}
    response = eth.request(FPGA_READ, monitor=True, address=expected_address, **options)
    if response.address != expected_address:
        print(
            "FPGA readback address mismatch: "
            f"received {response.address}, expected {expected_address}"
        )
        return 0
    if response.subtarget != int(selector):
        raise RuntimeError("FPGA readback selector mismatch")
    if len(response.data) != 20:
        print(f"FPGA readback incomplete: received {len(response.data)}/20 bytes")
        return 0
    return str_to_bin(response.data)


@ethernet_locked
def fpga_readback_BER(eth, tdc):
    selector = int(tdc) & 0xFF
    response = eth.request(
        FPGA_READ, monitor=True, address=5, subtarget=selector
    )
    if response.address != 5 or response.subtarget != selector:
        return 0
    return str_to_bin(response.data) if len(response.data) == 20 else 0


@ethernet_locked
def fpga_reg_reset(eth):
    eth.request(FPGA_RESET)
    return 0


@ethernet_locked
def lpgbt_write_multi(
    eth, lpgbt_addr, reg_addr, value_list, verbose=True,
    response_timeout_s=None, tx_parity=None, verification=None, which_csm=None,
):
    values = bytes(int(value) & 0xFF for value in value_list)
    if not 1 <= len(values) <= 15:
        raise ValueError("lpGBT write length must be 1..15 bytes")
    target = _selected_uplink(eth, which_csm, lpgbt_addr)
    response = eth.request(
        LPGBT_WRITE,
        target=target,
        address=int(reg_addr),
        argument=int(lpgbt_addr),
        payload=values,
        timeout_s=response_timeout_s,
    )
    return _decode_lpgbt_reply(
        response.data, verbose=verbose, tx_parity=tx_parity,
        verification=verification,
    )


@ethernet_locked
def lpgbt_write(
    eth, lpgbt_addr, reg_addr, reg_data, verbose=True,
    response_timeout_s=None, tx_parity=None, verification=None, which_csm=None,
):
    return lpgbt_write_multi(
        eth, lpgbt_addr, reg_addr, [reg_data], verbose,
        response_timeout_s, tx_parity, verification, which_csm,
    )


@ethernet_locked
def lpgbt_read(
    eth, lpgbt_addr, reg_addr, nb_to_be_read, verbose=True,
    verification=None, which_csm=None, response_timeout_s=None,
):
    count = int(nb_to_be_read)
    if not 1 <= count <= 15:
        raise ValueError("lpGBT read length must be 1..15 bytes")
    target = _selected_uplink(eth, which_csm, lpgbt_addr)
    response = eth.request(
        LPGBT_READ,
        monitor=True,
        target=target,
        address=int(reg_addr),
        argument=(count << 8) | int(lpgbt_addr),
        timeout_s=response_timeout_s,
    )
    return _decode_lpgbt_reply(
        response.data, verbose=verbose, verification=verification
    )


@ethernet_locked
def lpgbt_config_read(
    eth, lpgbt_addr, reg_addr, nb_read, verbose=True,
    response_timeout_s=None, which_csm=None,
):
    return lpgbt_read(
        eth, lpgbt_addr, reg_addr, nb_read, verbose=verbose,
        response_timeout_s=response_timeout_s, which_csm=which_csm,
    )


@ethernet_locked
def lpgbt_config_write(
    eth, reg_addr, value_list=None, which_csm=0, lpgbt_addr=117,
    verbose=True, response_timeout_s=None, verification=None,
):
    values = list(value_list or [])
    parity = (int(lpgbt_addr) % 0x80 * 2) ^ (int(reg_addr) >> 8) ^ (int(reg_addr) & 0xFF) ^ len(values)
    for value in values:
        parity ^= int(value)
    if verbose:
        print(
            f"Writing to CSM{which_csm}, lpGBT{lpgbt_addr}, reg{reg_addr}, "
            f"value={values}, tx_parity={parity:08b}"
        )
    data = lpgbt_write_multi(
        eth, lpgbt_addr, reg_addr, values, verbose=verbose,
        response_timeout_s=response_timeout_s, tx_parity=parity,
        verification=verification, which_csm=which_csm,
    )
    if isinstance(data, list) and _lpgbt_v1_range_is_writable(reg_addr, len(values)) and data != values:
        _report_lpgbt_verification_error(
            verification, f"Writable-register mismatch: wrote {values}, read {data}"
        )
    return data


@ethernet_locked
def lpgbt_read_parity(eth, lpgbt_addr=117, which_csm=None):
    return lpgbt_read(
        eth, lpgbt_addr, 0x1E7, 1, which_csm=which_csm
    )


def _decode_sca_replies(raw):
    raw = bytes(raw)
    if len(raw) % SCA_REPLY_LENGTH:
        raise ValueError(f"SCA response has invalid length {len(raw)}")
    replies = []
    for offset in range(0, len(raw), SCA_REPLY_LENGTH):
        frame = raw[offset:offset + SCA_REPLY_LENGTH]
        replies.append(
            dict(
                raw=frame,
                address=frame[0],
                trans_id=frame[1],
                channel=frame[2],
                error=frame[3],
                length=frame[4],
                data=int.from_bytes(frame[5:9], "big"),
            )
        )
    return replies


def _sca_is_monitor(channel, command):
    return bool(int(command) & 1) or (
        int(channel) == SCA_share.ADC_CHANNEL and int(command) == SCA_share.ADC_GO
    )


@ethernet_locked
def SCA_config(
    eth, sca_enable, which_csm, sca_address, transID, channel, datalen,
    command, data, read_required=0, wait=0, report_stale=True,
    reply_attempts=3, on_retry=None,
):
    """Recover mismatched replies only for ADC monitoring commands."""
    transID = validate_sca_transaction_id(transID)
    if reply_attempts < 1:
        raise ValueError("reply_attempts must be positive")
    repeatable = (
        channel == SCA_share.ADC_CHANNEL
        and command in (SCA_share.ADC_W_MUX, SCA_share.ADC_R_MUX, SCA_share.ADC_GO)
    )
    attempts = reply_attempts if repeatable else 1
    for attempt in range(1, attempts + 1):
        try:
            return _SCA_config_once(
                eth, sca_enable, which_csm, sca_address, transID, channel, datalen,
                command, data, read_required, wait, report_stale,
            )
        except SCAReplyMismatchError as exc:
            if attempts == 1:
                raise
            if attempt == attempts:
                raise SCAReplyMismatchError(f"SCA command failed after {attempts} attempts: {exc}") from exc
            new_id = next_sca_transaction_id(transID)
            _report_sca_retry(
                f"SCA reply mismatch, attempt {attempt}/{attempts}: {exc}; "
                f"retrying with transaction={new_id:#04x}", on_retry)
            transID = new_id


def _SCA_config_once(
    eth, sca_enable, which_csm, sca_address, transID, channel, datalen,
    command, data, read_required=0, wait=0, report_stale=True,
):
    del datalen, wait, report_stale
    transID = validate_sca_transaction_id(transID)
    response = eth.request(
        SCA_COMMAND,
        monitor=bool(read_required) or _sca_is_monitor(channel, command),
        target=int(which_csm),
        subtarget=int(sca_enable) & 0xF,
        trans_id=int(transID),
        channel=int(channel),
        command=int(command),
        sca_address=int(sca_address),
        argument=int(data),
    )
    replies = _decode_sca_replies(response.data)
    matching = [
        reply for reply in replies
        if reply["trans_id"] == int(transID) and reply["channel"] == int(channel)
    ]
    context = (f"CSM{which_csm}, SCA mask={int(sca_enable):#x}, "
               f"transaction={transID:#04x}, channel={int(channel):#04x}, "
               f"command={int(command):#04x}")
    if not matching:
        if (channel == SCA_share.CR_CHANNEL and command == SCA_share.CTRL_W_CRD
                and data == SCA_share.ENADC_DATA):
            # Older FPGA firmware can forward a link acknowledgement here.
            # No enable readback is needed; the following mux/conversion
            # commands still require correctly matched, error-free replies.
            return None
        received = "; ".join(
            f"transaction={reply['trans_id']:#04x}, channel={reply['channel']:#04x}, "
            f"error={reply['error']:#04x}" for reply in replies
        ) or "empty SCA payload"
        raise SCAReplyMismatchError(
            f"SCA reply mismatch: no matching Ethernet reply ({context}); received: {received}"
        )
    # Check all broadcast replies as well as reads and writes. A rejected write
    # must not be reported as a successful configuration by its caller.
    for reply in matching:
        if reply["error"]:
            raise RuntimeError(f"SCA command failed: error={reply['error']:#04x} ({context})")
    reply = matching[0]
    return [reply["channel"], reply["error"], reply["data"]]


def SCA_enable_adc(eth, get_transID, sca_enable, which_csm):
    """Send ADC enable once; an unmatched enable acknowledgement is ignored."""
    return SCA_config(
        eth, sca_enable=sca_enable, which_csm=which_csm, sca_address=0,
        transID=get_transID(), channel=SCA_share.CR_CHANNEL, datalen=4,
        command=SCA_share.CTRL_W_CRD, data=SCA_share.ENADC_DATA,
    )


def SCA_reply_print(readback):
    raw = bytes.fromhex(readback) if isinstance(readback, str) else bytes(readback)
    replies = _decode_sca_replies(raw)
    for reply in replies:
        print(
            f"Channel: 0x{reply['channel']:02X}, error: 0x{reply['error']:02X}, "
            f"length: {reply['length']}, data: 0x{reply['data']:08X}"
        )
    return 0


@ethernet_locked
def SCA_connect(eth, sca_enable, which_csm, sca_address, verbose=0):
    response = eth.request(
        SCA_CONNECT, target=int(which_csm), subtarget=int(sca_enable) & 0xF,
        sca_address=int(sca_address),
    )
    if verbose:
        print(str_to_hex(response.data))
    return 0


@ethernet_locked
def SCA_start_reset(eth, sca_enable, which_csm, sca_address, verbose=0):
    response = eth.request(
        SCA_RESET, target=int(which_csm), subtarget=int(sca_enable) & 0xF,
        sca_address=int(sca_address),
    )
    if verbose:
        print(str_to_hex(response.data))
    return 0


@ethernet_locked
def SCA_tx_rx_reset(eth, sca_enable, which_csm, sca_address, verbose=0):
    return SCA_start_reset(eth, sca_enable, which_csm, sca_address, verbose)


@ethernet_locked
def SCA_JTAGset(eth, transID, sca_enable, which_csm, data_len):
    channel, error, _ = SCA_config(
        eth, sca_enable, which_csm, 0, transID, SCA_share.CR_CHANNEL, 4,
        SCA_share.CTRL_W_CRD, SCA_share.ENJTAG_DATA,
    )
    if channel < 0 or error:
        raise RuntimeError(f"failed to enable JTAG: channel={channel}, error={error}")
    data = int(data_len) + (1 << 11)  # standard edges, MSB first, TCK idle low
    channel, error, _ = SCA_config(
        eth, sca_enable, which_csm, 0, transID, SCA_share.JTAG_CHANNEL, 4,
        SCA_share.JTAG_W_CTRL, data,
    )
    if channel < 0 or error:
        raise RuntimeError(f"JTAG_W_CTRL failed: channel={channel}, error={error}")


@ethernet_locked
def SCA_clk_div(eth, transID, sca_enable, which_csm, data, verbose=True):
    SCA_config(
        eth, sca_enable, which_csm, 0, transID, SCA_share.CR_CHANNEL, 4,
        SCA_share.CTRL_W_CRD, SCA_share.ENJTAG_DATA,
    )
    SCA_config(
        eth, sca_enable, which_csm, 0, transID, SCA_share.JTAG_CHANNEL, 4,
        SCA_share.JTAG_W_FREQ, data,
    )
    channel, error, value = SCA_config(
        eth, sca_enable, which_csm, 0, transID, SCA_share.JTAG_CHANNEL, 2,
        SCA_share.JTAG_R_FREQ, 0,
    )
    if channel < 0 or error:
        raise RuntimeError(f"JTAG divider read failed: channel={channel}, error={error}")
    if verbose:
        print(f"JTAG div configured to {value} for CSM{which_csm}, SCA{int(math.log2(sca_enable))}")


def _write_jtag_words(eth, transID, sca_enable, which_csm, bits, commands):
    if len(bits) > 128:
        raise ValueError("JTAG transaction exceeds 128 bits")
    for word in range((len(bits) + 31) // 32):
        low = word * 32
        chunk = bits[max(0, len(bits) - low - 32):len(bits) - low]
        SCA_config(
            eth, sca_enable, which_csm, 0, transID, SCA_share.JTAG_CHANNEL,
            4, commands[word], int(chunk or "0", 2),
        )


@ethernet_locked
def write_TMS(eth, transID, sca_enable, which_csm, data):
    _write_jtag_words(
        eth, transID, sca_enable, which_csm, data,
        [SCA_share.JTAG_W_TMS0, SCA_share.JTAG_W_TMS1,
         SCA_share.JTAG_W_TMS2, SCA_share.JTAG_W_TMS3],
    )


@ethernet_locked
def write_TDO(eth, transID, sca_enable, which_csm, data):
    _write_jtag_words(
        eth, transID, sca_enable, which_csm, data,
        [SCA_share.JTAG_W_TDO0, SCA_share.JTAG_W_TDO1,
         SCA_share.JTAG_W_TDO2, SCA_share.JTAG_W_TDO3],
    )


@ethernet_locked
def read_TDI(eth, transID, sca_enable, which_csm, length):
    if length > 128:
        raise ValueError("JTAG transaction exceeds 128 bits")
    commands = [
        SCA_share.JTAG_R_TDI0, SCA_share.JTAG_R_TDI1,
        SCA_share.JTAG_R_TDI2, SCA_share.JTAG_R_TDI3,
    ]
    words = []
    for word in range((length + 31) // 32):
        channel, error, value = SCA_config(
            eth, sca_enable, which_csm, 0, transID, SCA_share.JTAG_CHANNEL,
            2, commands[word], 0,
        )
        if channel < 0 or error:
            raise RuntimeError(f"JTAG TDI read failed: channel={channel}, error={error}")
        words.append(f"{value:032b}")
    result = "".join(reversed(words))
    return result[-length:]


@ethernet_locked
def SCA_JTAG_go(
    eth, transID, sca_enable, which_csm, ir_value, dr_value, isASD=False,
    capture_ir_readback=False, verbose=True,
):
    full_tdo, full_tms, ir_mask, dr_mask = JTAGTAPController().full_sequence(
        ir_value, dr_value, isASD
    )
    readback = ""
    while full_tms:
        length = min(len(full_tms), 128)
        write_TMS(eth, transID, sca_enable, which_csm, full_tms[:length])
        write_TDO(eth, transID, sca_enable, which_csm, full_tdo[:length])
        SCA_JTAGset(eth, transID, sca_enable, which_csm, length)
        SCA_config(
            eth, sca_enable, which_csm, 0, transID, SCA_share.JTAG_CHANNEL,
            2, SCA_share.JTAG_GO, 0,
        )
        readback += read_TDI(eth, transID, sca_enable, which_csm, length)
        full_tms = full_tms[length:]
        full_tdo = full_tdo[length:]
    ir_readback = "".join(readback[i] for i, bit in enumerate(ir_mask) if bit == "1")
    dr_readback = "".join(readback[i] for i, bit in enumerate(dr_mask) if bit == "1")
    if dr_readback and verbose:
        print("Valid TDI in DR seq: " + format(int(dr_readback[::-1], 2), "x"))
    return (ir_readback, dr_readback) if capture_ir_readback else dr_readback


def reset_TDO(self, which_csm):
    for command in (
        SCA_share.JTAG_W_TDO3, SCA_share.JTAG_W_TDO2,
        SCA_share.JTAG_W_TDO1, SCA_share.JTAG_W_TDO0,
    ):
        SCA_config(
            self.eth, 0b0010, which_csm, 0, self.get_transID(),
            SCA_share.JTAG_CHANNEL, 4, command, 0,
        )


def read_TMS(self, which_csm):
    for command in (
        SCA_share.JTAG_R_TMS0, SCA_share.JTAG_R_TMS1,
        SCA_share.JTAG_R_TMS2, SCA_share.JTAG_R_TMS3,
    ):
        SCA_config(
            self.eth, 0b0010, which_csm, 0, self.get_transID(),
            SCA_share.JTAG_CHANNEL, 2, command, 0,
        )
