"""Ask the loaded MiniDAQ firmware how many lpGBT links it was built with.

MiniDAQ_reg.sv packs readback pages 6, 7 and 8 from bit 0 with fields sized by
UPLINKCOUNT and DOWNLINKCOUNT, so the GUI must decode them with the build's counts
(upstream board: 4 and 2, KCU105 port: 2 and 1). Pages 1 and 3 are padded and do not
depend on them. No register reports the counts, but ethernet_control_engine.sv answers
"invalid request" to an lpGBT access with target >= UPLINK_COUNT before touching the link.
"""

from ethernet_control_protocol import EthernetControlError, LPGBT_READ
from TDC_config_low_level_function import ethernet_exclusive_session

MAX_UPLINKS = 4
_STATUS_INVALID = 0x01
_STATUS_BUSY = 0x02


def detect_uplink_count(eth):
    """Highest uplink the firmware accepts, plus one. Raises if it cannot tell."""
    with ethernet_exclusive_session(eth):
        for target in range(MAX_UPLINKS - 1, 0, -1):
            # Odd targets are slave lpGBTs (115), even are masters (117). A target
            # that exists gets a harmless one-byte read; no reply still proves it exists.
            lpgbt_addr = 115 if target % 2 else 117
            try:
                eth.request(LPGBT_READ, monitor=True, target=target, address=0,
                            argument=(1 << 8) | lpgbt_addr)
            except EthernetControlError as error:
                if error.status == _STATUS_INVALID:
                    continue
                if error.status is None or error.status == _STATUS_BUSY:
                    raise
            return target + 1
    return 1


def downlink_count(uplinks):
    """Each downlink serves a CSM with a master and a slave uplink."""
    return (uplinks + 1) // 2
