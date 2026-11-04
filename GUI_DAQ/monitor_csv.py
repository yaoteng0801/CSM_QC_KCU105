"""Write monitor scans incrementally without retaining the run in memory."""

import csv
from pathlib import Path


class MonitorCSV:
    def __init__(self, filename, fieldnames, name, message, *, unique=False):
        path = Path((filename or f'{name.lower()}_monitor.csv').strip()).expanduser()
        if not path.suffix:
            path = path.with_suffix('.csv')
        if not path.is_absolute():
            base = Path(__file__).resolve().parent
            path = base / path if path.parts[0] == 'output' else base / 'output' / path
        self.path = path
        self.unique = unique
        self.fieldnames = tuple(fieldnames)
        self.name = name
        self.message = message
        self._file = None
        self._writer = None
        self._failed = False
        self._closed = False

    def write_row(self, row):
        if self._failed or self._closed:
            return
        try:
            if self._file is None:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                original = self.path
                suffix = 0
                while True:
                    try:
                        self._file = self.path.open('x' if self.unique else 'w', newline='')
                        break
                    except FileExistsError:
                        if not self.unique:
                            raise
                        suffix += 1
                        self.path = original.with_name(f'{original.stem}_{suffix}{original.suffix}')
                self._writer = csv.DictWriter(self._file, fieldnames=self.fieldnames, extrasaction='ignore')
                self._writer.writeheader()
            self._writer.writerow(row)
            self._file.flush()
        except Exception as exc:
            self._failed = True
            self.message(f'WARNING: {self.name} monitor CSV save failed: {exc}')
            self._close_file()

    def _close_file(self):
        try:
            if self._file is not None:
                self._file.close()
        except Exception as exc:
            if not self._failed:
                self._failed = True
                self.message(f'WARNING: {self.name} monitor CSV close failed: {exc}')
        finally:
            self._file = None
            self._writer = None

    def close(self):
        if self._closed:
            return
        had_file = self._file is not None
        self._close_file()
        self._closed = True
        try:
            if had_file and not self._failed:
                self.message(f'{self.name} monitor CSV saved: {self.path}')
        finally:
            # Workers pass a bound Qt signal; release it when the run ends.
            self.message = None
