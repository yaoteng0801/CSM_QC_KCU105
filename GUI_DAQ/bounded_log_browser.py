"""Keep only recent GUI log lines; the log files retain the full output."""

from PyQt5 import QtWidgets


class BoundedLogBrowser(QtWidgets.QTextBrowser):
    def __init__(self, parent=None, max_lines=5000):
        super().__init__(parent)
        self.setUndoRedoEnabled(False)
        self.document().setMaximumBlockCount(max_lines)
