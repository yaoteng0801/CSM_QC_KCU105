from PyQt5 import QtCore, QtWidgets


class pop_run_plot_saving(QtWidgets.QDialog):
    def __init__(
        self,
        plot_labels,
        selected_live_labels=None,
        selected_save_labels=None,
        *,
        save_previous_callback=None,
        can_save_previous_callback=None,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Run Plot Display / Saving")
        self.resize(620, 500)

        self._save_previous_callback = save_previous_callback
        self._can_save_previous_callback = can_save_previous_callback
        self._items = {}
        selected_live = set(selected_live_labels or [])
        selected_save = set(selected_save_labels or [])

        layout = QtWidgets.QVBoxLayout(self)
        note = QtWidgets.QLabel(
            "Live display controls which plot tabs receive periodic GUI updates. "
            "Save at end controls which plots are exported after the run."
        )
        note.setWordWrap(True)
        layout.addWidget(note)

        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels(["Plot tab", "Live display", "Save at end"])
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)

        for group_name, labels in self._group_labels(plot_labels or []):
            group = QtWidgets.QTreeWidgetItem(self.tree, [group_name, "", ""])
            group.setFlags(group.flags() & ~QtCore.Qt.ItemIsSelectable)
            font = group.font(0)
            font.setBold(True)
            group.setFont(0, font)
            for label in labels:
                text = str(label)
                item = QtWidgets.QTreeWidgetItem(group, [text, "", ""])
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                item.setCheckState(
                    1,
                    QtCore.Qt.Checked if text in selected_live else QtCore.Qt.Unchecked,
                )
                item.setCheckState(
                    2,
                    QtCore.Qt.Checked if text in selected_save else QtCore.Qt.Unchecked,
                )
                self._items[text] = item
            group.setExpanded(True)
        layout.addWidget(self.tree, 1)

        select_row = QtWidgets.QHBoxLayout()
        for text, column, checked in (
            ("Live All", 1, True),
            ("Live None", 1, False),
            ("Save All", 2, True),
            ("Save None", 2, False),
        ):
            button = QtWidgets.QPushButton(text)
            button.clicked.connect(
                lambda _checked=False, col=column, state=checked: self._set_column_checked(col, state)
            )
            select_row.addWidget(button)
        select_row.addStretch(1)
        layout.addLayout(select_row)

        self.btn_save_previous = QtWidgets.QPushButton("Save previous run plots")
        self.btn_save_previous.clicked.connect(self._save_previous_run_plots)
        self.btn_save_previous.setEnabled(self._can_save_previous_run_plots())
        layout.addWidget(self.btn_save_previous)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def live_labels(self):
        return [
            label for label, item in self._items.items()
            if item.checkState(1) == QtCore.Qt.Checked
        ]

    def save_labels(self):
        return [
            label for label, item in self._items.items()
            if item.checkState(2) == QtCore.Qt.Checked
        ]

    def selected_labels(self):
        """Compatibility alias for end-of-run plot saving."""
        return self.save_labels()

    @staticmethod
    def _group_for_label(label):
        text = str(label or "")
        if text.startswith("Residual"):
            return "Residual tabs"
        if text.startswith("Geometry"):
            return "Geometry tabs"
        return "Spectra tabs"

    @classmethod
    def _group_labels(cls, labels):
        grouped = []
        by_name = {}
        for label in labels:
            group = cls._group_for_label(label)
            if group not in by_name:
                by_name[group] = []
                grouped.append((group, by_name[group]))
            by_name[group].append(str(label))
        return grouped

    def _set_column_checked(self, column, checked):
        state = QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked
        for item in self._items.values():
            item.setCheckState(int(column), state)

    def _can_save_previous_run_plots(self):
        if self._save_previous_callback is None:
            return False
        if self._can_save_previous_callback is None:
            return True
        try:
            return bool(self._can_save_previous_callback())
        except Exception:
            return False

    def _save_previous_run_plots(self):
        labels = self.save_labels()
        if not labels:
            QtWidgets.QMessageBox.warning(
                self,
                "Run Plot Saving",
                "Select at least one plot tab under Save at end before saving.",
            )
            return
        if not self._can_save_previous_run_plots():
            QtWidgets.QMessageBox.warning(
                self,
                "Run Plot Saving",
                "Previous run plots can be saved only after a run has stopped and before a new run starts.",
            )
            return
        try:
            ok = bool(self._save_previous_callback(labels))
        except Exception as error:
            QtWidgets.QMessageBox.warning(
                self,
                "Run Plot Saving",
                f"Failed to save previous run plots:\n{error}",
            )
            return
        if ok:
            QtWidgets.QMessageBox.information(self, "Run Plot Saving", "Previous run plots saved.")
        else:
            QtWidgets.QMessageBox.warning(self, "Run Plot Saving", "Previous run plots were not saved.")
