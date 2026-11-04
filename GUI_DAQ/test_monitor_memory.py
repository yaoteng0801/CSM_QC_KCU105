import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import csv
import gc
import tempfile
import tracemalloc
import unittest
from pathlib import Path

from PyQt5 import QtGui, QtWidgets
from bounded_log_browser import BoundedLogBrowser
from monitor_csv import MonitorCSV


class MonitorMemoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_csv_rows_are_flushed_during_run_without_accumulating_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'monitor.csv'
            columns = ['scan'] + [f'value{i}' for i in range(120)]
            writer = MonitorCSV(str(path), columns, 'SCA', lambda message: None)
            tracemalloc.start()
            try:
                for scan in range(1000):
                    writer.write_row(dict.fromkeys(columns, scan))
                gc.collect()
                before, _ = tracemalloc.get_traced_memory()
                for scan in range(1000, 10000):
                    writer.write_row(dict.fromkeys(columns, scan))
                gc.collect()
                after, _ = tracemalloc.get_traced_memory()
                self.assertLess(after - before, 256 * 1024)
                # The complete data is already readable before close/finish.
                with path.open(newline='') as source:
                    rows = csv.DictReader(source)
                    self.assertEqual(sum(1 for _ in rows), 10000)
            finally:
                writer.close()
                tracemalloc.stop()

    def test_csv_failure_is_reported_once_without_buffering_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'directory.csv'
            path.mkdir()
            messages = []
            writer = MonitorCSV(str(path), ['scan'], 'CSM', messages.append)
            for scan in range(1000):
                writer.write_row({'scan': scan})
            writer.close()
            self.assertEqual(len(messages), 1)
            self.assertIn('CSV save failed', messages[0])
            self.assertIsNone(writer._file)

    def test_visible_log_keeps_recent_lines_only(self):
        browser = BoundedLogBrowser(max_lines=500)
        for batch in range(100):
            browser.moveCursor(QtGui.QTextCursor.End)
            browser.insertPlainText(''.join(f'monitor line {batch * 200 + i}\n' for i in range(200)))
        self.assertLessEqual(browser.document().blockCount(), 500)
        text = browser.toPlainText()
        self.assertIn('monitor line 19999', text)
        self.assertNotIn('monitor line 0\n', text)
        self.assertFalse(browser.isUndoRedoEnabled())
        browser.close()


if __name__ == '__main__':
    unittest.main()
