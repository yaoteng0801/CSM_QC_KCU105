from PyQt5.QtCore import *
import subprocess
import time
import sys
import os
import pandas as pd
from TDC_config_low_level_function import *
import csv


def _is_missing_reply_error(error):
    """Return True when an lpGBT transaction had no usable reply."""
    text = str(error)
    return any(
        marker in text
        for marker in (
            "received 0 byte(s)",
            "No reply bytes were received",
            "MiniDAQ reply timeout",
            "MiniDAQ Ethernet reply timeout",
        )
    )


class Worker_lpGBT(QObject):
    finished = pyqtSignal()
    message_out = pyqtSignal(str)

    def __init__(self,eth):
        super(Worker_lpGBT, self).__init__()
        self.eth = eth


    def load_lpgbt_config(self,which_csm, is_master):
        load_success = False
        if is_master:
            filename = "lpgbt_master_reg.csv"
            lpgbt_addr = 117
        else:
            filename = "lpgbt_slave_reg.csv"
            lpgbt_addr = 115

        try:
            # Resolve next to this file so the GUI can be started from any directory.
            self.df = pd.read_csv(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), filename),
                delimiter=' ', header=None)
        except Exception as e:
            print("Error loading "+filename)
            print(e)
        else:
            print(filename+" loaded successfully.")
            register_values = [
                (int(addr, 16), int(data, 16))
                for addr, data in zip(
                    self.df[0].values.tolist(),
                    self.df[1].values.tolist(),
                )
                if int(addr, 16) <= LPGBT_V1_LAST_WRITABLE_REGISTER
            ]
            skipped_count = len(self.df.index) - len(register_values)
            if skipped_count:
                print(
                    "Skipping %s read-only lpGBT registers starting at 0x150."
                    % skipped_count
                )
            transaction_count = 0
            failed_transaction_count = 0
            no_reply_transaction_count = 0
            writable_register_count = len(register_values)
            while register_values:
                chunk = register_values[:15]
                del register_values[:len(chunk)]
                addr = chunk[0][0]
                expected_addresses = list(range(addr, addr + len(chunk)))
                if [entry[0] for entry in chunk] != expected_addresses:
                    print("Non-contiguous lpGBT register addresses in " + filename)
                    failed_transaction_count += 1
                    break
                values = [entry[1] for entry in chunk]
                transaction_count += 1
                verification = {}
                try:
                    result = lpgbt_config_write(
                        self.eth,
                        reg_addr=addr,
                        value_list=values,
                        which_csm=which_csm,
                        lpgbt_addr=lpgbt_addr,
                        verbose=False,
                        verification=verification,
                    )
                except Exception as e:
                    result = -1
                    verification.setdefault("errors", []).append(
                        "%s: %s" % (type(e).__name__, e)
                    )
                no_valid_reply = not isinstance(result, list)
                if no_valid_reply:
                    verification.setdefault("errors", []).append(
                        "No valid register-data reply was returned."
                    )
                errors = verification.get("errors", [])
                if errors:
                    missing_reply = no_valid_reply and any(
                        _is_missing_reply_error(error) for error in errors
                    )
                    if missing_reply:
                        no_reply_transaction_count += 1
                    else:
                        failed_transaction_count += 1
                    end_addr = addr + len(values) - 1
                    print(
                        "%s CSM%s lpGBT%s writable transaction "
                        "0x%03X-0x%03X, requested=%s"
                        % (
                            "UNVERIFIED (NO REPLY)" if missing_reply else "FAILED",
                            which_csm,
                            lpgbt_addr,
                            addr,
                            end_addr,
                            values,
                        )
                    )
                    for error in errors:
                        print("  - " + error)
                    if missing_reply:
                        print(
                            "  - NOTE: No reply can be expected during the initial "
                            "bootstrap while the uplink is not ready. The write was "
                            "sent, so this does not necessarily indicate a write "
                            "failure."
                        )

            if failed_transaction_count:
                print(
                    "lpGBT configuration verification FAILED: %s/%s writable "
                    "transactions failed and %s/%s had no reply."
                    % (
                        failed_transaction_count,
                        transaction_count,
                        no_reply_transaction_count,
                        transaction_count,
                    )
                )
            elif no_reply_transaction_count:
                print(
                    "lpGBT configuration completed with incomplete verification: "
                    "%s/%s writable transactions had no reply. During bootstrap, "
                    "these writes may still have succeeded."
                    % (no_reply_transaction_count, transaction_count)
                )
            else:
                print(
                    "lpGBT configuration verification succeeded: %s writable "
                    "registers in %s transactions."
                    % (writable_register_count, transaction_count)
                )
                load_success = True

        self.finished.emit()
        return load_success
