"""One scheduled acquisition and CSV row for selected mezzanine and CSM readings."""

import datetime as dt
import threading
import time
from PyQt5 import QtCore

from monitor_readers import MezzMonitorReader, CSMMonitorReader
from monitor_csv import MonitorCSV
from monitor_display_buffer import MonitorDisplayBuffer
from TDC_config_low_level_function import sca_reply_retry_reporting


class Worker_Monitor(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    message_out = QtCore.pyqtSignal(str)

    def __init__(self, controller):
        super().__init__()
        self.interval_seconds = controller.get_monitor_interval_seconds()
        self.scan_limit = int(getattr(controller, 'scan_limit', 0) or 0)  # 0 runs until Stop.
        self.stop_requested = threading.Event()
        self.display_values = MonitorDisplayBuffer()
        self.mezz_indices = tuple(i for i, bit in enumerate(controller.mezz.mezz_enable)
                                  if bit == '1') if controller.checkBox_monitor_mezz.isChecked() else ()
        self.csm_indices = tuple(i for i, box in enumerate(controller.csm.checkbox_list)
                                 if box.isChecked()) if controller.checkBox_monitor_csm.isChecked() else ()
        self.mezz_reader = MezzMonitorReader(controller.mezz) if self.mezz_indices else None
        self.csm_reader = CSMMonitorReader(controller.csm) if self.csm_indices else None
        self.metrics = tuple(controller.csm._monitor_metrics())
        self.mezz_per_csm = controller.mezz.mezz_per_CSM
        self.initialized = set()
        self.csv_fieldnames = ['timestamp', 'scan']
        for reader in (self.mezz_reader, self.csm_reader):
            if reader is None:
                continue
            reader.setParent(self)
            reader.message_out.connect(self.message_out.emit, QtCore.Qt.DirectConnection)
            self.csv_fieldnames.extend(name for name in reader.csv_fieldnames
                                       if name not in ('scan', 'timestamp'))
        if self.mezz_reader is not None:
            self.mezz_reader.display_update.connect(self._mezz_value, QtCore.Qt.DirectConnection)
        self.monitor_csv = MonitorCSV(controller.get_csv_filename(), self.csv_fieldnames,
                                      'Combined', self.message_out.emit, unique=True)

    def _mezz_value(self, index, label_index, text, abnormal):
        self.display_values.put(('mezz', index, label_index), (text, abnormal))

    def _missing_mezz(self, index):
        for label_index in range(3):
            self._mezz_value(index, label_index, 'NA', True)

    def _missing_csm(self, csm):
        for key, name, unit, column in self.metrics:
            if key[0] == csm:
                self.csm_reader.display_values.put(key, 'NA')

    def _scan(self, scan_index):
        row = dict.fromkeys(self.csv_fieldnames, 'NA')
        row.update(scan=scan_index, timestamp=dt.datetime.now().astimezone().isoformat(timespec='milliseconds'))
        for reader in (self.mezz_reader, self.csm_reader):
            if reader is not None:
                reader.current_scan_row = row
        # Both readers use the same SCA enable operation. Initialize each CSM
        # once, then serialize all target reads in this worker.
        selected_csms = set(self.csm_indices) | {i // self.mezz_per_csm for i in self.mezz_indices}
        ready = set()
        for csm in sorted(selected_csms):
            try:
                if csm not in self.initialized:
                    (self.mezz_reader or self.csm_reader).initialize_csm(csm)
                    self.initialized.add(csm)
                ready.add(csm)
            except Exception as exc:
                self.message_out.emit(f'Monitoring CSM{csm} ADC initialization failed: {exc}')
        for index in self.mezz_indices:
            csm = index // self.mezz_per_csm
            if csm not in ready:
                self._missing_mezz(index)
                continue
            try:
                self.mezz_reader.scan_mezz(index)
            except Exception as exc:
                self.message_out.emit(f'Monitoring Mezz{index} failed: {exc}')
                self._missing_mezz(index)
                self.initialized.discard(csm)
        for csm in self.csm_indices:
            # Start with NA so a partial failure cannot leave stale GUI values.
            self._missing_csm(csm)
            if csm not in ready:
                continue
            try:
                self.csm_reader.scan_csm(scan_index - 1, csm)
            except Exception as exc:
                self.message_out.emit(f'Monitoring CSM{csm} failed: {exc}')
                self.initialized.discard(csm)
        self.monitor_csv.write_row(row)
        self.display_values.put('csv_path', str(self.monitor_csv.path))
        for reader in (self.mezz_reader, self.csm_reader):
            if reader is not None:
                reader.current_scan_row = None
        self.display_values.put('status', f'Completed scan {scan_index} · {row["timestamp"]}')

    def stop(self):
        self.stop_requested.set()

    def run(self):
        try:
            next_scan_at = time.monotonic()
            scan = 0
            with sca_reply_retry_reporting(self.message_out.emit):
                while not self.stop_requested.is_set():
                    if self.stop_requested.wait(max(0.0, next_scan_at - time.monotonic())):
                        break
                    started = time.monotonic()
                    scan += 1
                    self._scan(scan)
                    if self.scan_limit and scan >= self.scan_limit:
                        break
                    next_scan_at = started + self.interval_seconds
        except Exception as exc:
            self.message_out.emit(f'Monitoring failed: {exc}')
        finally:
            for reader in (self.mezz_reader, self.csm_reader):
                if reader is not None:
                    reader.current_scan_row = None
            self.monitor_csv.close()
            self.finished.emit()
