"""Keep one latest reading per monitor value while the GUI is busy."""

import threading


class MonitorDisplayBuffer:
    def __init__(self):
        self._lock = threading.Lock()
        self._values = {}

    def put(self, key, text):
        with self._lock:
            self._values[key] = text

    def take(self):
        with self._lock:
            values = self._values
            self._values = {}
        return values
