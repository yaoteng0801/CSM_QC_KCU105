"""Continuous, single-attempt JTAG tests for the selected mezzanines."""

import random
import threading
from copy import deepcopy

from PyQt5 import QtCore, QtWidgets

from SCA_share import SCA_share
from TDCreg import TDCreg
from crc8_D81 import crc_cal
from TDC_config_low_level_function import SCA_clk_div, ethernet_exclusive_session


TDC_CHAINS = (
    ("setup_0", SCA_share.TDC_SETUP0),
    ("setup_1", SCA_share.TDC_SETUP1),
    ("setup_2", SCA_share.TDC_SETUP2),
)


def random_registers(rng, template=None):
    # Keep the configured controls fixed while varying every setup/ASD bit.
    tdc = deepcopy(template) if template is not None else TDCreg()
    for name, _ in TDC_CHAINS:
        width = sum(len("".join(field)) for field in getattr(tdc, name))
        setattr(tdc, name, [[format(rng.getrandbits(width), f"0{width}b")]])
    for asd in tdc.ASD_list:
        width = sum(len("".join(field)) for field in asd.setup)
        asd.setup = [[format(rng.getrandbits(width), f"0{width}b")]]
    return tdc


class JTAGDebugWorker(QtCore.QThread):
    result = QtCore.pyqtSignal(int, int, str, bool, str)

    def __init__(self, controller, selected, divider, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.selected = tuple(selected)
        self.divider = divider
        self.stop_requested = threading.Event()
        self.rng = random.Random()
        self.templates = {
            (csm, mezz): deepcopy(controller.CSM_list[csm].TDC_list[mezz])
            for csm, mezz in self.selected
        }
        self.controls_initialized = set()
        self.target_index = 0
        self.next_kind = "TDC"
        self.pending_tdc = None

    def stop(self):
        self.stop_requested.set()

    def _test(self, tdc, which_csm, mezz, kind):
        controller = self.controller
        # Keep selection, writes and readback together even while background
        # monitoring uses the same Ethernet connection.
        with ethernet_exclusive_session(controller.eth):
            SCA_clk_div(eth=controller.eth, transID=controller.get_transID(),
                        sca_enable=0b0010, which_csm=which_csm, data=self.divider, verbose=False)
            controller.SCA_GPIO_init(which_csm=which_csm, verbose=False)
            controller.Mezz_enable(mezz, which_csm=which_csm, verbose=False)

            def config(ir):
                return controller.config_single(ir, tdc, which_csm=which_csm,
                                                raise_errors=True, verbose=False)

            target = (which_csm, mezz)
            if target not in self.controls_initialized:
                # CRC covers the controls too. Establish known, fixed values
                # once per run; only the three setup chains vary in the loop.
                config(SCA_share.TDC_CONTROL0)
                config(SCA_share.TDC_CONTROL1)
                self.controls_initialized.add(target)

            if kind == "TDC":
                for _, ir in TDC_CHAINS:
                    config(ir)
                readback = config(SCA_share.TDC_STATUS0)
                if not isinstance(readback, str) or len(readback) != 33 or set(readback) - {"0", "1"}:
                    return False, "Missing or malformed TDC status readback"
                actual = format(int(readback[::-1][1:33], 2), "08X")
                expected = crc_cal(tdc)
                return actual == expected, f"CRC expected {expected}, read {actual}"

            expected = controller._asd_dr_value(tdc)
            config(SCA_share.ASD_WRITE)
            readback = config(SCA_share.ASD_READ)
            valid = isinstance(readback, str) and readback[::-1] == expected
            if valid:
                return True, "ASD readback matches"
            actual = (format(int(readback[::-1], 2), "042X")
                      if isinstance(readback, str) and readback and not set(readback) - {"0", "1"}
                      else repr(readback))
            return False, (f"ASD expected {int(expected, 2):042X}, read {actual}, "
                           f"read length {len(readback) if isinstance(readback, str) else 0}/165")

    def run(self):
        while not self.stop_requested.is_set():
            which_csm, mezz = self.selected[self.target_index]
            if self.pending_tdc is None:
                self.pending_tdc = random_registers(self.rng, self.templates[(which_csm, mezz)])
            kind = self.next_kind
            try:
                valid, detail = self._test(self.pending_tdc, which_csm, mezz, kind)
            except Exception as exc:
                valid, detail = False, str(exc)
            if not valid:
                print(f"[JTAG Debug] CSM{which_csm}, Mezz{mezz}, {kind} error: {detail}")
            if kind == "TDC":
                self.next_kind = "ASD"
            else:
                self.next_kind = "TDC"
                self.pending_tdc = None
                self.target_index = (self.target_index + 1) % len(self.selected)
            # Preserve the next test and random pattern across Stop/Continue.
            self.result.emit(which_csm, mezz, kind, valid, detail)


class JTAGDebugDialog(QtWidgets.QDialog):
    def __init__(self, controller, selected, parent=None):
        super().__init__(parent)
        self.setWindowTitle("JTAG Debug Test")
        self.setModal(True)
        self.controller = controller
        self.selected = tuple(selected)
        self.worker = None
        self.paused_worker = None
        self.pending_action = None
        self.counts = {}
        layout = QtWidgets.QVBoxLayout(self)
        description = QtWidgets.QLabel(
            "Continuously test the selected mezzanines with random values.\n"
            "One TDC test randomizes SETUP0, SETUP1 and SETUP2 and compares the CRC.\n"
            "One ASD test writes all 3 ASDs, then reads and compares every bit.\n"
            "CONTROL0 and CONTROL1 use the configured values, programmed once at the start.\n"
            "Each failed test adds one error; no retries. Start begins a new run.\n"
            "Stop pauses; Continue resumes. Reset stops and clears the counters.\n"
            "Random values remain in hardware after stopping. Reprogram your configuration before taking data."
        )
        description.setWordWrap(True)
        self.description = description
        layout.addWidget(description)
        self.table = QtWidgets.QTableWidget(len(selected), 5)
        self.table.setHorizontalHeaderLabels(["Mezz", "TDC tests", "TDC errors", "ASD tests", "ASD errors"])
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        for row, (csm, mezz) in enumerate(selected):
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(
                f"{csm * controller.mezz_per_CSM + mezz} (CSM{csm}, local {mezz})"))
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        layout.addWidget(self.table)
        self.totals = QtWidgets.QLabel()
        layout.addWidget(self.totals)
        self.status = QtWidgets.QLabel("Ready")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.last_error = QtWidgets.QLabel()
        self.last_error.setWordWrap(True)
        layout.addWidget(self.last_error)
        buttons = QtWidgets.QHBoxLayout()
        self.start_button = QtWidgets.QPushButton("Start")
        self.stop_button = QtWidgets.QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.continue_button = QtWidgets.QPushButton("Continue")
        self.continue_button.setEnabled(False)
        self.reset_button = QtWidgets.QPushButton("Reset")
        self.close_button = QtWidgets.QPushButton("Close")
        for button in (self.start_button, self.stop_button, self.continue_button,
                       self.reset_button, self.close_button):
            buttons.addWidget(button)
        layout.addLayout(buttons)
        self.start_button.clicked.connect(self.start)
        self.stop_button.clicked.connect(self.stop)
        self.continue_button.clicked.connect(self.continue_test)
        self.reset_button.clicked.connect(self.reset)
        self.close_button.clicked.connect(self.reject)
        self._reset_counts()
        self.resize(700, 440)

    def _reset_counts(self):
        self.counts = {target: [0, 0, 0, 0] for target in self.selected}
        self._update_counts()

    def _update_counts(self):
        totals = [0, 0, 0, 0]
        for row, target in enumerate(self.selected):
            for col, value in enumerate(self.counts[target], 1):
                self.table.setItem(row, col, QtWidgets.QTableWidgetItem(str(value)))
                totals[col - 1] += value
        self.totals.setText(f"Total TDC: {totals[0]} tests, {totals[1]} errors    |    "
                            f"Total ASD: {totals[2]} tests, {totals[3]} errors")

    def start(self):
        if self.worker is not None:
            return
        self._discard_paused_worker()
        self._reset_counts()
        self.last_error.clear()
        try:
            self.worker = self._make_worker()
        except Exception as exc:
            self.status.setText("Could not start")
            self.last_error.setText(str(exc))
            self.continue_button.setEnabled(False)
            print(f"[{self.windowTitle()}] Could not start: {exc}")
            return
        self.worker.result.connect(self._result)
        self.worker.finished.connect(self._finished)
        self.start_button.setEnabled(False)
        self.continue_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status.setText("Running")
        self.worker.start()

    def _make_worker(self):
        return JTAGDebugWorker(self.controller, self.selected,
                               self.controller.jtag_rate_spinbox.value(), self)

    def continue_test(self):
        if self.worker is not None or self.paused_worker is None:
            return
        self.worker = self.paused_worker
        self.paused_worker = None
        self.worker.stop_requested.clear()
        self.start_button.setEnabled(False)
        self.continue_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status.setText("Running")
        self.worker.start()

    def _discard_paused_worker(self):
        if self.paused_worker is not None:
            self.paused_worker.deleteLater()
            self.paused_worker = None

    def reset(self):
        if self.worker is not None:
            self.pending_action = "reset"
            self.reset_button.setEnabled(False)
            self.stop()
            return
        self._discard_paused_worker()
        self._reset_counts()
        self.last_error.clear()
        self.continue_button.setEnabled(False)
        self.status.setText("Ready")

    def _result(self, csm, mezz, kind, valid, detail):
        offset = 0 if kind == "TDC" else 2
        self.counts[(csm, mezz)][offset] += 1
        self.counts[(csm, mezz)][offset + 1] += int(not valid)
        self._update_counts()
        if not valid:
            self.last_error.setText(f"Last error: CSM{csm}, local Mezz{mezz}, {kind}: {detail}")

    def stop(self):
        if self.worker is not None:
            self.worker.stop()
            self.stop_button.setEnabled(False)
            self.status.setText("Stopping after the current test…")

    def _finished(self):
        self.paused_worker = self.worker
        self.worker = None
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.continue_button.setEnabled(True)
        self.reset_button.setEnabled(True)
        self.status.setText("Stopped")
        action = self.pending_action
        self.pending_action = None
        if action == "reset":
            self.reset()
        elif action == "close":
            self.reject()

    def reject(self):
        if self.worker is not None:
            self.pending_action = "close"
            self.stop()
            return
        self._discard_paused_worker()
        super().reject()

    def closeEvent(self, event):
        if self.worker is not None:
            self.reject()
            event.ignore()
        else:
            super().closeEvent(event)
