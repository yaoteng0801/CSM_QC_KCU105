# geometry_dialog.py
from __future__ import annotations

import os
from typing import List, Tuple, Optional

from PyQt5 import QtCore, QtWidgets

from geometry import Geometry


TDC_CHOICES = 40
DEFAULT_TDC_NCOL = 6


class GeometryConfigDialog(QtWidgets.QDialog):
    """
    Edit geometry settings and assign TDCs to ML slots.

    The assignment UI is one grid:
      ML count x TDCs per ML dropdowns.
    Each TDC can be selected only once in the grid.
    """

    settings_applied = QtCore.pyqtSignal()
    settings_changed = QtCore.pyqtSignal()

    def __init__(
        self,
        parent=None,
        geo: Optional[Geometry] = None,
        n_mls: Optional[int] = None,
        slots_per_ml: int = 10,
        ml0_slots: Optional[List[Tuple[int, int]]] = None,
        ml1_slots: Optional[List[Tuple[int, int]]] = None,
        default_path: str = "geometry.txt",
        embedded: bool = False,
    ):
        super().__init__(parent)
        self._embedded = bool(embedded)
        if self._embedded:
            self.setWindowFlags(QtCore.Qt.Widget)
            self.setModal(False)
        else:
            self.setWindowTitle("Geometry + TDC Assignment")
            self.setModal(True)

        self._geo_in = geo if geo is not None else Geometry()
        self._n_mls = max(1, int(n_mls if n_mls is not None else getattr(self._geo_in, "n_mls", 2)))
        self._slots_per_ml = max(1, int(slots_per_ml))
        self._default_path = str(default_path)

        self._ml_slots = self._initial_ml_slots(self._geo_in, ml0_slots, ml1_slots)
        self._rows = []
        self._slot_count_spins = []
        self._suppress_combo_updates = False
        self._suppress_auto_apply = True
        self._loading_geometry = False
        self._explicit_layout = {}
        self._explicit_slots = []

        self._build_ui()
        self._load_into_widgets(self._geo_in, self._slots_per_ml, self._ml_slots)
        self._suppress_auto_apply = False
        if self._embedded:
            self.lab_io.setText("Changes apply automatically")

        if not self._embedded:
            self.resize(820, 720)

    # ---------------- UI ----------------

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        if self._embedded:
            layout.setContentsMargins(4, 4, 4, 4)
            layout.setSpacing(4)

        io = QtWidgets.QHBoxLayout()
        layout.addLayout(io)

        self.btn_load = QtWidgets.QPushButton("Load...")
        self.btn_save = QtWidgets.QPushButton("Save...")
        io.addWidget(self.btn_load)
        io.addWidget(self.btn_save)

        self.lab_io = QtWidgets.QLabel("")
        self.lab_io.setWordWrap(True)
        io.addWidget(self.lab_io, 1)
        self.lab_layout = QtWidgets.QLabel("")
        self.lab_layout.setWordWrap(True)
        layout.addWidget(self.lab_layout)

        self.btn_load.clicked.connect(self._on_load)
        self.btn_save.clicked.connect(self._on_save)

        if self._embedded:
            self.settings_scroll = QtWidgets.QScrollArea()
            self.settings_scroll.setWidgetResizable(True)
            self.settings_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
            # The assignment grid's natural width grows with the number of TDC
            # slots.  Do not let that size hint make the Geometry tab (and the
            # main window) open unnecessarily wide; the editor can still grow
            # with the window and provides a horizontal scrollbar when needed.
            self.settings_scroll.setSizeAdjustPolicy(
                QtWidgets.QAbstractScrollArea.AdjustIgnored
            )
            self.settings_scroll.setSizePolicy(
                QtWidgets.QSizePolicy.Ignored,
                QtWidgets.QSizePolicy.Expanding,
            )
            self.settings_scroll.setMinimumSize(0, 0)
            self.settings_page = QtWidgets.QWidget()
            self.settings_scroll.setWidget(self.settings_page)
            settings_layout = QtWidgets.QVBoxLayout(self.settings_page)
            settings_layout.setContentsMargins(4, 4, 4, 4)
            settings_layout.setSpacing(4)
            # Embedded Geometry-tab order: assignment first, numbers below.
            self._build_assignment_group(settings_layout)
            self.btn_cancel = None
            self.lab_warn = QtWidgets.QLabel("")
            self.btn_ok = None
            self._build_geometry_group(settings_layout)
            settings_layout.addStretch(1)
            layout.addWidget(self.settings_scroll, 1)
        else:
            self.tabs = QtWidgets.QTabWidget()
            layout.addWidget(self.tabs, 1)

            self.geometry_scroll = QtWidgets.QScrollArea()
            self.geometry_scroll.setWidgetResizable(True)
            self.geometry_page = QtWidgets.QWidget()
            self.geometry_scroll.setWidget(self.geometry_page)
            geometry_layout = QtWidgets.QVBoxLayout(self.geometry_page)
            self._build_geometry_group(geometry_layout)
            geometry_layout.addStretch(1)
            self.tabs.addTab(self.geometry_scroll, "Geometry data")

            self.assignment_scroll = QtWidgets.QScrollArea()
            self.assignment_scroll.setWidgetResizable(True)
            self.assignment_page = QtWidgets.QWidget()
            self.assignment_scroll.setWidget(self.assignment_page)
            assignment_layout = QtWidgets.QVBoxLayout(self.assignment_page)
            self._build_assignment_group(assignment_layout)
            assignment_layout.addStretch(1)
            self.tabs.addTab(self.assignment_scroll, "TDC assignment")

        if not self._embedded:
            bottom = QtWidgets.QHBoxLayout()
            layout.addLayout(bottom)
            self.lab_warn = QtWidgets.QLabel("")
            bottom.addWidget(self.lab_warn, 1)

            self.btn_cancel = QtWidgets.QPushButton("Cancel")
            bottom.addWidget(self.btn_cancel)
            self.btn_ok = QtWidgets.QPushButton("OK")
            bottom.addWidget(self.btn_ok)

        if self.btn_cancel is not None:
            self.btn_cancel.clicked.connect(self.reject)
        if self.btn_ok is not None:
            self.btn_ok.clicked.connect(self._on_ok)

        self.sb_n_mls.valueChanged.connect(self._on_assignment_shape_changed)
        self.sb_slots_per_ml.valueChanged.connect(self._on_assignment_shape_changed)
        self.sb_MAX_TDC_LAYER.valueChanged.connect(self._on_layers_per_ml_changed)
        self.sb_MAX_TDC_CHANNEL.valueChanged.connect(self._on_layers_per_ml_changed)
        self.sb_MAX_TUBE_LAYER.valueChanged.connect(self._on_total_layers_changed)
        self._connect_automatic_apply_signals()

    def _connect_automatic_apply_signals(self):
        widgets = (
            self.cb_chamber,
            self.sb_n_mls,
            self.sb_slots_per_ml,
            self.sb_flip,
            self.sb_tdcColByTubeNo,
            self.sb_MAX_TDC,
            self.sb_MAX_TDC_CHANNEL,
            self.sb_MAX_TUBE_LAYER,
            self.sb_MAX_TUBE_COLUMN,
            self.sb_MAX_TDC_LAYER,
            self.ds_ML_distance,
            self.ds_tube_length,
            self.ds_layer_distance,
            self.ds_column_distance,
            self.ds_radius,
            self.ds_min_drift,
            self.ds_max_drift,
        )
        for widget in widgets:
            if isinstance(widget, QtWidgets.QComboBox):
                widget.currentIndexChanged.connect(self._notify_settings_changed)
            else:
                widget.valueChanged.connect(self._notify_settings_changed)

    def _notify_settings_changed(self, *_):
        if self._embedded and not self._suppress_auto_apply:
            self.settings_changed.emit()

    def _build_geometry_group(self, parent_layout: QtWidgets.QVBoxLayout):
        group = QtWidgets.QGroupBox("Geometry")
        group.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Preferred,
        )
        parent_layout.addWidget(group)
        columns = QtWidgets.QHBoxLayout(group)
        columns.setContentsMargins(6, 4, 6, 6)
        columns.setSpacing(18)
        forms = []
        for _ in range(3):
            form = QtWidgets.QFormLayout()
            form.setVerticalSpacing(2)
            form.setFormAlignment(QtCore.Qt.AlignTop)
            columns.addLayout(form, 1)
            forms.append(form)
        form = forms[0]

        self.cb_chamber = QtWidgets.QComboBox()
        self.cb_chamber.addItems(["A", "C"])
        form.addRow("chamberType", self.cb_chamber)

        self.sb_n_mls = QtWidgets.QSpinBox()
        self.sb_n_mls.setRange(1, 16)
        form.addRow("ML count", self.sb_n_mls)

        self.sb_slots_per_ml = QtWidgets.QSpinBox()
        self.sb_slots_per_ml.setRange(1, TDC_CHOICES)
        form.addRow("TDCs per ML", self.sb_slots_per_ml)

        self.sb_flip = QtWidgets.QSpinBox()
        self.sb_flip.setRange(0, 1)
        form.addRow("flipTDCs", self.sb_flip)

        self.sb_tdcColByTubeNo = QtWidgets.QSpinBox()
        self.sb_tdcColByTubeNo.setRange(0, 1)
        form.addRow("tdcColByTubeNo", self.sb_tdcColByTubeNo)

        self.sb_MAX_TDC = QtWidgets.QSpinBox()
        self.sb_MAX_TDC.setRange(TDC_CHOICES, 512)
        self.sb_MAX_TDC_CHANNEL = QtWidgets.QSpinBox()
        self.sb_MAX_TDC_CHANNEL.setRange(1, 64)
        self.sb_MAX_TUBE_LAYER = QtWidgets.QSpinBox()
        self.sb_MAX_TUBE_LAYER.setRange(1, 256)
        self.sb_MAX_TUBE_COLUMN = QtWidgets.QSpinBox()
        self.sb_MAX_TUBE_COLUMN.setRange(1, 512)
        self.sb_MAX_TDC_LAYER = QtWidgets.QSpinBox()
        self.sb_MAX_TDC_LAYER.setRange(1, 16)

        form.addRow("MAX_TDC", self.sb_MAX_TDC)
        form = forms[1]
        form.addRow("MAX_TDC_CHANNEL", self.sb_MAX_TDC_CHANNEL)
        form.addRow("Total layers", self.sb_MAX_TUBE_LAYER)
        form.addRow("MAX_TUBE_COLUMN", self.sb_MAX_TUBE_COLUMN)
        form.addRow("Layers per ML", self.sb_MAX_TDC_LAYER)

        def _dspin(minv=-1e9, maxv=1e9, step=0.1, decimals=6):
            ds = QtWidgets.QDoubleSpinBox()
            ds.setRange(minv, maxv)
            ds.setDecimals(decimals)
            ds.setSingleStep(step)
            return ds

        self.ds_ML_distance = _dspin(step=0.1, decimals=6)
        self.ds_tube_length = _dspin(step=0.001, decimals=6)
        self.ds_layer_distance = _dspin(step=0.001, decimals=9)
        self.ds_column_distance = _dspin(step=0.001, decimals=6)
        self.ds_radius = _dspin(step=0.1, decimals=6)
        self.ds_min_drift = _dspin(step=0.01, decimals=6)
        self.ds_max_drift = _dspin(step=0.01, decimals=6)

        form.addRow("ML_distance", self.ds_ML_distance)
        form.addRow("tube_length", self.ds_tube_length)
        form = forms[2]
        form.addRow("layer_distance", self.ds_layer_distance)
        form.addRow("column_distance", self.ds_column_distance)
        form.addRow("radius", self.ds_radius)
        form.addRow("min_drift_dist", self.ds_min_drift)
        form.addRow("max_drift_dist", self.ds_max_drift)

    def _build_assignment_group(self, parent_layout: QtWidgets.QVBoxLayout):
        group = QtWidgets.QGroupBox("TDC Assignment")
        group.setSizePolicy(
            QtWidgets.QSizePolicy.Maximum,
            QtWidgets.QSizePolicy.Preferred,
        )
        parent_layout.addWidget(group, 0, QtCore.Qt.AlignLeft)
        layout = QtWidgets.QHBoxLayout(group)
        layout.setContentsMargins(6, 4, 6, 6)
        layout.setSpacing(8)
        self.btn_clear = QtWidgets.QPushButton("Clear")
        self.btn_clear.clicked.connect(self._clear_assignments)
        layout.addWidget(self.btn_clear, 0, QtCore.Qt.AlignTop)

        self.assignment_grid = QtWidgets.QGridLayout()
        self.assignment_grid.setVerticalSpacing(2)
        layout.addLayout(self.assignment_grid)

    # ---------------- assignment grid ----------------

    def _initial_ml_slots(
        self,
        geo: Geometry,
        ml0_slots: Optional[List[Tuple[int, int]]],
        ml1_slots: Optional[List[Tuple[int, int]]],
    ) -> List[List[Tuple[int, int]]]:
        if hasattr(geo, "assignment_by_ml"):
            slots = [list(v) for v in geo.assignment_by_ml()]
        else:
            slots = [list(getattr(geo, "ml0", [])), list(getattr(geo, "ml1", []))]

        if ml0_slots is not None:
            while len(slots) < 1:
                slots.append([])
            slots[0] = list(ml0_slots)
        if ml1_slots is not None:
            while len(slots) < 2:
                slots.append([])
            slots[1] = list(ml1_slots)

        while len(slots) < self._n_mls:
            slots.append([])
        return slots[: self._n_mls]

    def _clear_grid(self):
        while self.assignment_grid.count():
            item = self.assignment_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _rebuild_assignment_rows(self, init_slots: Optional[List[List[Tuple[int, int]]]] = None):
        self._clear_grid()
        self._rows.clear()
        self._slot_count_spins.clear()

        self.assignment_grid.addWidget(QtWidgets.QLabel("ML"), 0, 0)

        n_mls = int(self.sb_n_mls.value())
        slots_per_ml = int(self.sb_slots_per_ml.value())
        init_slots = init_slots or []
        slot_counts = self._slot_counts_from_slots(init_slots, slots_per_ml)

        for slot_idx in range(slots_per_ml):
            label = QtWidgets.QLabel(f"Slot {slot_idx}")
            label.setAlignment(QtCore.Qt.AlignCenter)
            self.assignment_grid.addWidget(label, 0, slot_idx + 1)

        self._suppress_combo_updates = True
        try:
            for row_idx, ml_id in enumerate(reversed(range(n_mls)), start=1):
                ml_vals = init_slots[ml_id] if ml_id < len(init_slots) else []
                lab_ml = QtWidgets.QLabel(f"ML{ml_id}")
                self.assignment_grid.addWidget(lab_ml, row_idx, 0)
                for slot_idx in range(slots_per_ml):
                    tdc_id = -1
                    if slot_idx < len(ml_vals):
                        try:
                            tdc_id = int(ml_vals[slot_idx][0])
                        except Exception:
                            tdc_id = -1

                    cb = self._create_tdc_combo()
                    cb.setCurrentIndex(0 if not (0 <= tdc_id < TDC_CHOICES) else tdc_id + 1)
                    cb.currentIndexChanged.connect(lambda _idx, combo=cb: self._on_tdc_combo_changed(combo))

                    self.assignment_grid.addWidget(cb, row_idx, slot_idx + 1)

                    self._rows.append({"ml": ml_id, "slot": slot_idx, "combo": cb})
        finally:
            self._suppress_combo_updates = False

        count_row = int(n_mls) + 1
        self.assignment_grid.addWidget(QtWidgets.QLabel("Columns / mezz"), count_row, 0)
        for slot_idx in range(slots_per_ml):
            combo = self._create_count_combo(slot_counts[slot_idx])
            combo.setEnabled(not self._explicit_layout)
            combo.currentIndexChanged.connect(self._sync_min_geometry_dims)
            combo.currentIndexChanged.connect(self._notify_settings_changed)
            self.assignment_grid.addWidget(combo, count_row, slot_idx + 1)
            self._slot_count_spins.append(combo)

        self._drop_duplicate_selections()
        self._update_tdc_choice_locks()
        self._notify_settings_changed()
        self._sync_min_geometry_dims()

    @staticmethod
    def _slot_counts_from_slots(
        ml_slots: List[List[Tuple[int, int]]],
        slots_per_ml: int,
    ) -> List[int]:
        counts = [DEFAULT_TDC_NCOL for _ in range(int(slots_per_ml))]
        for slot_idx in range(int(slots_per_ml)):
            found = False
            for slots in ml_slots or []:
                if slot_idx >= len(slots):
                    continue
                try:
                    value = max(0, int(slots[slot_idx][1]))
                except Exception:
                    continue
                counts[slot_idx] = min(24, value)
                found = True
                if value > 0:
                    break
            if not found:
                counts[slot_idx] = DEFAULT_TDC_NCOL
        return counts

    @staticmethod
    def _create_tdc_combo() -> QtWidgets.QComboBox:
        cb = QtWidgets.QComboBox()
        cb.addItem("--", -1)
        for tdc in range(TDC_CHOICES):
            cb.addItem(str(tdc), tdc)
        cb.setFixedWidth(55)
        return cb

    def _create_count_combo(self, value: int) -> QtWidgets.QComboBox:
        combo = QtWidgets.QComboBox()
        max_cols = 24 if self._explicit_layout else max(
            1, self.sb_MAX_TDC_CHANNEL.value() // max(1, self.sb_MAX_TDC_LAYER.value()))
        for ncol in range(max_cols + 1):
            combo.addItem(str(ncol), ncol)
        combo.setCurrentIndex(max(0, min(max_cols, int(value))))
        combo.setFixedWidth(55)
        return combo

    @staticmethod
    def _set_combo_item_enabled(combo: QtWidgets.QComboBox, index: int, enabled: bool):
        item = combo.model().item(index)
        if item is not None:
            item.setEnabled(bool(enabled))

    def _on_tdc_combo_changed(self, changed_combo: QtWidgets.QComboBox):
        if self._suppress_combo_updates:
            return

        new_tdc = int(changed_combo.currentData())
        if new_tdc >= 0:
            self._suppress_combo_updates = True
            try:
                for row in self._rows:
                    combo = row["combo"]
                    if combo is changed_combo:
                        continue
                    if int(combo.currentData()) == new_tdc:
                        combo.setCurrentIndex(0)
            finally:
                self._suppress_combo_updates = False

        self._update_tdc_choice_locks()
        self._notify_settings_changed()

    def _drop_duplicate_selections(self):
        seen = set()
        self._suppress_combo_updates = True
        try:
            for row in self._rows:
                combo = row["combo"]
                tdc = int(combo.currentData())
                if tdc < 0:
                    continue
                if tdc in seen:
                    combo.setCurrentIndex(0)
                else:
                    seen.add(tdc)
        finally:
            self._suppress_combo_updates = False

    def _update_tdc_choice_locks(self):
        selected = {
            int(row["combo"].currentData())
            for row in self._rows
            if int(row["combo"].currentData()) >= 0
        }
        for row in self._rows:
            combo = row["combo"]
            own = int(combo.currentData())
            for tdc in range(TDC_CHOICES):
                self._set_combo_item_enabled(combo, tdc + 1, (tdc == own) or (tdc not in selected))

    def _clear_assignments(self):
        self._suppress_combo_updates = True
        try:
            for row in self._rows:
                row["combo"].setCurrentIndex(0)
        finally:
            self._suppress_combo_updates = False
        self._update_tdc_choice_locks()
        self._notify_settings_changed()

    def _on_assignment_shape_changed(self, _):
        current = self._read_slots_by_ml() if self._rows else self._ml_slots
        self.sb_MAX_TUBE_LAYER.blockSignals(True)
        self.sb_MAX_TUBE_LAYER.setValue(self.sb_n_mls.value() * self.sb_MAX_TDC_LAYER.value())
        self.sb_MAX_TUBE_LAYER.blockSignals(False)
        self._sync_min_geometry_dims()
        self._rebuild_assignment_rows(current)

    def _on_layers_per_ml_changed(self, *_):
        if self._loading_geometry:
            return
        self.sb_MAX_TUBE_LAYER.blockSignals(True)
        self.sb_MAX_TUBE_LAYER.setValue(self.sb_n_mls.value() * self.sb_MAX_TDC_LAYER.value())
        self.sb_MAX_TUBE_LAYER.blockSignals(False)
        if self._rows:
            self._rebuild_assignment_rows(self._read_slots_by_ml())
        self._sync_min_geometry_dims()

    def _on_total_layers_changed(self, value):
        if self._loading_geometry:
            return
        n_mls = max(1, self.sb_n_mls.value())
        layers = max(1, (int(value) + n_mls - 1) // n_mls)
        self.sb_MAX_TDC_LAYER.setValue(layers)
        self.sb_MAX_TUBE_LAYER.blockSignals(True)
        self.sb_MAX_TUBE_LAYER.setValue(n_mls * self.sb_MAX_TDC_LAYER.value())
        self.sb_MAX_TUBE_LAYER.blockSignals(False)

    def _sync_min_geometry_dims(self, *_):
        if not hasattr(self, "sb_n_mls"):
            return
        min_layers = int(self.sb_n_mls.value()) * int(self.sb_MAX_TDC_LAYER.value())
        min_columns = sum(self._read_slot_counts())
        self.sb_MAX_TUBE_LAYER.setMinimum(max(1, int(self.sb_n_mls.value())))
        self.sb_MAX_TUBE_LAYER.setSingleStep(max(1, int(self.sb_n_mls.value())))
        self.sb_MAX_TUBE_COLUMN.setMinimum(max(1, min_columns))
        if self.sb_MAX_TUBE_LAYER.value() < min_layers:
            self.sb_MAX_TUBE_LAYER.setValue(min_layers)
        if self.sb_MAX_TUBE_COLUMN.value() < min_columns:
            self.sb_MAX_TUBE_COLUMN.setValue(min_columns)

    # ---------------- value plumbing ----------------

    def _load_into_widgets(self, geo: Geometry, slots_per_ml: int, ml_slots: List[List[Tuple[int, int]]]):
        self._loading_geometry = True
        self._explicit_layout = dict(geo.tube_map)
        self._explicit_slots = [list(slots) for slots in ml_slots]
        self._geometry_source = geo.geo_file
        self.cb_chamber.setCurrentText(str(geo.chamberType))
        self.sb_flip.setValue(int(geo.flipTDCs))
        self.sb_tdcColByTubeNo.setValue(int(geo.tdcColByTubeNo))

        self.sb_MAX_TDC.setValue(max(TDC_CHOICES, int(geo.MAX_TDC)))
        self.sb_MAX_TDC_CHANNEL.setValue(int(geo.MAX_TDC_CHANNEL))
        self.sb_MAX_TDC_LAYER.setValue(int(geo.MAX_TDC_LAYER))

        self.sb_n_mls.blockSignals(True)
        self.sb_slots_per_ml.blockSignals(True)
        self.sb_n_mls.setValue(max(1, int(getattr(geo, "n_mls", len(ml_slots) or 2))))
        self.sb_slots_per_ml.setValue(max(1, int(slots_per_ml)))
        self.sb_n_mls.blockSignals(False)
        self.sb_slots_per_ml.blockSignals(False)

        self._sync_min_geometry_dims()
        self.sb_MAX_TUBE_LAYER.setValue(max(self.sb_MAX_TUBE_LAYER.minimum(), int(geo.MAX_TUBE_LAYER)))
        self.sb_MAX_TUBE_COLUMN.setValue(max(self.sb_MAX_TUBE_COLUMN.minimum(), int(geo.MAX_TUBE_COLUMN)))

        self.ds_ML_distance.setValue(float(geo.ML_distance))
        self.ds_tube_length.setValue(float(geo.tube_length))
        self.ds_layer_distance.setValue(float(geo.layer_distance))
        self.ds_column_distance.setValue(float(geo.column_distance))
        self.ds_radius.setValue(float(geo.radius))
        self.ds_min_drift.setValue(float(geo.min_drift_dist))
        self.ds_max_drift.setValue(float(geo.max_drift_dist))

        self._ml_slots = [list(slots) for slots in ml_slots]
        self._rebuild_assignment_rows(self._ml_slots)
        # Old slot controls may have imposed a larger minimum while loading.
        self.sb_MAX_TUBE_COLUMN.setValue(max(self.sb_MAX_TUBE_COLUMN.minimum(), geo.MAX_TUBE_COLUMN))
        self._loading_geometry = False
        explicit = bool(self._explicit_layout)
        for widget in (self.sb_n_mls, self.sb_slots_per_ml, self.sb_MAX_TUBE_LAYER,
                       self.sb_MAX_TDC_LAYER, self.sb_MAX_TUBE_COLUMN, self.sb_MAX_TDC_CHANNEL,
                       self.ds_ML_distance, self.ds_layer_distance, self.ds_column_distance,
                       self.sb_flip, self.sb_tdcColByTubeNo):
            widget.setEnabled(not explicit)
        if explicit:
            self.lab_layout.setText(
                f"File layout: {len(self._explicit_layout)} tubes, {geo.MAX_TUBE_LAYER} layers "
                f"({geo.MAX_TDC_LAYER} per ML), {geo.MAX_TUBE_COLUMN} columns. "
                "Editable: TDC IDs, radius, drift limits, tube length."
            )
            self.lab_layout.setToolTip("Tube positions and channel wiring come from the geometry file.")
        else:
            self.lab_layout.setText("Regular layout: set total layers or layers per ML, and columns per mezzanine.")
            self.lab_layout.setToolTip("")

    def _read_geo_from_widgets(self) -> Geometry:
        n_mls = int(self.sb_n_mls.value())
        slots_per_ml = int(self.sb_slots_per_ml.value())
        max_tdc_layer = int(self.sb_MAX_TDC_LAYER.value())
        max_tube_layer = max(int(self.sb_MAX_TUBE_LAYER.value()), n_mls * max_tdc_layer)
        max_tube_column = max(int(self.sb_MAX_TUBE_COLUMN.value()), sum(self._read_slot_counts()))

        geo = Geometry(
            chamberType=str(self.cb_chamber.currentText()),
            flipTDCs=int(self.sb_flip.value()),
            tdcColByTubeNo=int(self.sb_tdcColByTubeNo.value()),
            MAX_TDC=max(TDC_CHOICES, int(self.sb_MAX_TDC.value())),
            MAX_TDC_CHANNEL=int(self.sb_MAX_TDC_CHANNEL.value()),
            MAX_TUBE_LAYER=max_tube_layer,
            MAX_TUBE_COLUMN=max_tube_column,
            MAX_TDC_LAYER=max_tdc_layer,
            ML_distance=float(self.ds_ML_distance.value()),
            tube_length=float(self.ds_tube_length.value()),
            layer_distance=float(self.ds_layer_distance.value()),
            column_distance=float(self.ds_column_distance.value()),
            radius=float(self.ds_radius.value()),
            min_drift_dist=float(self.ds_min_drift.value()),
            max_drift_dist=float(self.ds_max_drift.value()),
            n_mls=n_mls,
            slots_per_ml=slots_per_ml,
        )
        geo.tube_map = dict(self._explicit_layout)
        geo.geo_file = getattr(self, "_geometry_source", None)
        return geo

    def _read_slot_counts(self) -> List[int]:
        slots_per_ml = int(self.sb_slots_per_ml.value())
        counts = [
            int(combo.currentData())
            for combo in self._slot_count_spins[:slots_per_ml]
        ]
        while len(counts) < slots_per_ml:
            counts.append(DEFAULT_TDC_NCOL)
        return counts

    def _read_slots_by_ml(self) -> List[List[Tuple[int, int]]]:
        n_mls = int(self.sb_n_mls.value())
        slots_per_ml = int(self.sb_slots_per_ml.value())
        slot_counts = self._read_slot_counts()
        out = [
            [(-1, slot_counts[slot_idx]) for slot_idx in range(slots_per_ml)]
            for _ in range(n_mls)
        ]

        for row in self._rows:
            ml_id = int(row["ml"])
            slot_idx = int(row["slot"])
            if not (0 <= ml_id < n_mls and 0 <= slot_idx < slots_per_ml):
                continue
            ncol = slot_counts[slot_idx]
            if self._explicit_layout:
                ncol = self._explicit_slots[ml_id][slot_idx][1]
            out[ml_id][slot_idx] = (int(row["combo"].currentData()), ncol)

        return out

    # ---------------- button actions ----------------

    def _on_save(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save geometry", self._default_path, "Text files (*.txt);;All files (*)"
        )
        if not path:
            return
        try:
            geo = self._read_geo_from_widgets()
            geo.set_assignment(
                int(self.sb_slots_per_ml.value()),
                ml_slots=self._read_slots_by_ml(),
                n_mls=int(self.sb_n_mls.value()),
                apply_map=True,
            )
            geo.save(path)
            self.lab_io.setText(f"Saved: {path}")
        except Exception as e:
            self.lab_io.setText(f"Save failed: {type(e).__name__}: {e}")

    def _on_load(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Load geometry", "", "Geometry files (*.geo *.txt);;GEO tube tables (*.geo);;Text files (*.txt);;All files (*)"
        )
        if not path:
            return

        try:
            geo = Geometry.load(path, apply_map=True)
            if geo.tube_map:
                # The transverse GEO table contains no tube length.
                geo.tube_length = self.ds_tube_length.value()
            slots = int(geo.slots_per_ml)
            ml_slots = geo.assignment_by_ml() if hasattr(geo, "assignment_by_ml") else [list(geo.ml0), list(geo.ml1)]
            self._suppress_auto_apply = True
            try:
                self._load_into_widgets(geo, slots, ml_slots)
            finally:
                self._suppress_auto_apply = False
            self.lab_io.setText(
                f"Loaded: {os.path.basename(path)} | "
                f"MLs={getattr(geo, 'n_mls', len(ml_slots))} TDCs/ML={slots}"
            )
            self._notify_settings_changed()
        except Exception as e:
            self.lab_io.setText(f"Load failed: {type(e).__name__}: {e}")

    def _on_ok(self):
        geo = self.result_geometry()
        ml_slots = geo.assignment_by_ml()
        ids = [
            int(tdc)
            for slots in ml_slots
            for tdc, ncol in slots
            if int(tdc) >= 0 and int(ncol) > 0
        ]
        if len(ids) != len(set(ids)):
            self.lab_warn.setText("Duplicate TDC selection")
            return
        self.lab_warn.setText("")
        if self._embedded:
            self.settings_applied.emit()
        else:
            self.accept()

    # ---------------- public getters ----------------

    def result_geometry(self) -> Geometry:
        geo = self._read_geo_from_widgets()
        geo.set_assignment(
            int(self.sb_slots_per_ml.value()),
            ml_slots=self._read_slots_by_ml(),
            n_mls=int(self.sb_n_mls.value()),
            apply_map=True,
        )
        return geo

    def load_geometry(self, geo: Geometry) -> None:
        """Replace editor contents from a shared Geometry without opening a dialog."""
        self._geo_in = geo
        self._n_mls = max(1, int(getattr(geo, "n_mls", 2) or 2))
        self._slots_per_ml = max(1, int(getattr(geo, "slots_per_ml", 10) or 10))
        ml_slots = (
            geo.assignment_by_ml()
            if hasattr(geo, "assignment_by_ml")
            else [list(getattr(geo, "ml0", [])), list(getattr(geo, "ml1", []))]
        )
        self._suppress_auto_apply = True
        try:
            self._load_into_widgets(geo, self._slots_per_ml, ml_slots)
        finally:
            self._suppress_auto_apply = False

    def result_n_mls(self) -> int:
        return int(self.sb_n_mls.value())

    def result_slots_per_ml(self) -> int:
        return int(self.sb_slots_per_ml.value())

    def result_ml_slots(self) -> List[List[Tuple[int, int]]]:
        return self._read_slots_by_ml()

    def result_ml0_slots(self) -> List[Tuple[int, int]]:
        slots = self._read_slots_by_ml()
        return list(slots[0]) if slots else []

    def result_ml1_slots(self) -> List[Tuple[int, int]]:
        slots = self._read_slots_by_ml()
        return list(slots[1]) if len(slots) > 1 else []
