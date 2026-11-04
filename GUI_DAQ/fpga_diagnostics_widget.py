"""Read-only diagnostic display and one-shot background polling worker."""
from PyQt5 import QtCore, QtWidgets
from fpga_diagnostics import COUNTERS, CLOCK_HZ


class SnapshotWorker(QtCore.QThread):
    def __init__(self, callback, parent=None):
        super().__init__(parent)
        self.callback = callback
        self.snapshot = None
        self.error = None

    def run(self):
        try:
            self.snapshot = self.callback(cancelled=self.isInterruptionRequested)
        except Exception as exc:
            self.error = str(exc)


class DiagnosticWidget(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super().__init__("FPGA triggerless diagnostics — per chamber", parent)
        layout = QtWidgets.QVBoxLayout(self)
        self.status = QtWidgets.QLabel("Not sampled (framed triggerless capture only)")
        self.status.setWordWrap(True)
        self.status.setMinimumHeight(2*self.fontMetrics().height())
        layout.addWidget(self.status)
        self.table = QtWidgets.QTableWidget(len(COUNTERS), 5)
        self.table.setHorizontalHeaderLabels(["Counter", "Ch 0 total", "Ch 0 /s", "Ch 1 total", "Ch 1 /s"])
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        for col in range(1, 5):
            self.table.horizontalHeader().setSectionResizeMode(col, QtWidgets.QHeaderView.ResizeToContents)
        # The host tab has an outer scroll area: keep all diagnostic rows
        # visible rather than burying loss counters in a second vertical scroll.
        row_height = max(24, self.fontMetrics().height()+6)
        self.table.verticalHeader().setDefaultSectionSize(row_height)
        self.table.setFixedHeight(len(COUNTERS)*row_height +
                                  self.table.horizontalHeader().sizeHint().height() +
                                  2*self.table.frameWidth()+2)
        for row, (_, label) in enumerate(COUNTERS):
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(label))
            for col in range(1, 5):
                item = QtWidgets.QTableWidgetItem("—")
                item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                self.table.setItem(row, col, item)
        layout.addWidget(self.table)
        self.note = QtWidgets.QLabel(
            "Requested every 1 s; totals are relative to the run-start snapshot.\n"
            "Processed = accepted + rejected; filter/limit reasons can overlap.\n"
            "Accepted means committed, not necessarily delivered intact."
        )
        layout.addWidget(self.note)

    def reset(self, message):
        self.status.setText(message)
        for row in range(len(COUNTERS)):
            for col in range(1, 5):
                self.table.item(row, col).setText("—")

    def show_snapshot(self, snapshot, baseline, previous=None, final=False):
        totals = snapshot.delta(baseline)
        elapsed = (snapshot.cycles - previous.cycles) / CLOCK_HZ if previous else 0
        changes = snapshot.delta(previous) if previous else None
        for chamber in range(2):
            for row in range(len(COUNTERS)):
                self.table.item(row, 1+chamber*2).setText(f"{totals[chamber][row]:,}")
                self.table.item(row, 2+chamber*2).setText(
                    f"{changes[chamber][row]/elapsed:,.1f}" if changes and elapsed > 0 and not final else "—")
        self.status.setText(
            f"{'Final (stopped)' if final else 'Live'} snapshot #{snapshot.sequence} | "
            f"{snapshot.sampled_at}"
        )
