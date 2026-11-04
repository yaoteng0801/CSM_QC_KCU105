# tab_spectra.py
from __future__ import annotations

from PyQt5 import QtWidgets, QtCore
import os
import re
import numpy as np
import pyqtgraph as pg
from sparse_log_axis import SparseLogAxisItem

pg.setConfigOption("background", "w")  # white
pg.setConfigOption("foreground", "k")  # black axes, ticks, labels

ADC_LSB_NS = 0.78125 * 2
CH_HIT_TIME_WINDOW_S = 60.0 * 25.0e-9
CH_HIT_RATE_REF_HZ = 1000.0


def _weighted_mean_std(values, weights) -> tuple[float, float]:
    values = np.asarray(values, dtype=np.float64)
    weights = np.asarray(weights, dtype=np.float64)
    total = float(np.sum(weights))
    if total <= 0.0:
        return 0.0, 0.0

    mean = float(np.dot(values, weights) / total)
    variance = float(np.dot((values - mean) ** 2, weights) / total)
    return mean, float(np.sqrt(max(0.0, variance)))


def _enabled_total_mean(values, enabled_mask=None) -> tuple[float, float, int]:
    values = np.asarray(values, dtype=np.float64).reshape(-1)
    if enabled_mask is None:
        mask = np.ones(values.size, dtype=bool)
    else:
        supplied = np.asarray(enabled_mask, dtype=bool).reshape(-1)
        mask = np.zeros(values.size, dtype=bool)
        mask[:min(values.size, supplied.size)] = supplied[:values.size]

    enabled_count = int(np.count_nonzero(mask))
    if enabled_count <= 0:
        return 0.0, 0.0, 0

    enabled_values = np.nan_to_num(
        values[mask], nan=0.0, posinf=0.0, neginf=0.0
    )
    total = float(np.sum(enabled_values))
    return total, total / float(enabled_count), enabled_count


def _spectra_update_suppressed(backend) -> bool:
    if backend is None:
        return False
    checker = getattr(backend, "spectra_update_suppressed", None)
    if callable(checker):
        try:
            return bool(checker())
        except Exception:
            return False
    return bool(getattr(backend, "_spectra_update_suppressed", False))


def _widget_is_visible(widget) -> bool:
    try:
        return bool(widget.isVisible())
    except Exception:
        return True


def _safe_plot_filename(text: str, default: str = "plot") -> str:
    name = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(text or "").strip()).strip("._")
    return name or str(default)


def _export_plot_item_png(plot_item, path: str) -> bool:
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        from pyqtgraph.exporters import ImageExporter

        exporter = ImageExporter(plot_item)
        try:
            exporter.parameters()["width"] = 1200
        except Exception:
            pass
        exporter.export(path)
        return True
    except Exception as e:
        print(f"[WARN] Failed to save plot image: path={path} error={repr(e)}")
        return False


def _gauss_pdf(x: np.ndarray, mu: float, sigma: float) -> np.ndarray:
    s = max(float(sigma), 1e-9)
    z = (x - float(mu)) / s
    return np.exp(-0.5 * z * z) / (s * np.sqrt(2.0 * np.pi))


def _fit_double_gauss_hist(centers: np.ndarray, counts: np.ndarray, binw: float):
    y = np.asarray(counts, dtype=np.float64)
    x = np.asarray(centers, dtype=np.float64)
    if x.ndim != 1 or y.ndim != 1 or x.size != y.size:
        return None

    mask = y > 0.0
    if np.count_nonzero(mask) < 8:
        return None

    xv = x[mask]
    yv = y[mask]
    n_tot = float(np.sum(yv))
    if n_tot < 40.0:
        return None

    mean = float(np.dot(xv, yv) / n_tot)
    var = float(np.dot((xv - mean) ** 2, yv) / n_tot)
    std = float(np.sqrt(max(var, (0.7 * float(binw)) ** 2)))
    xrng = float(max(1e-6, xv.max() - xv.min()))
    sig_min = max(0.5 * float(binw), 1e-4)
    sig_max = max(sig_min * 2.0, 0.6 * xrng)

    # Shared-mean model: narrow and wide components use the same mu.
    mu = mean
    w1 = 0.7
    s1 = float(np.clip(0.8 * std, sig_min, sig_max))
    s2 = float(np.clip(1.6 * std, sig_min, sig_max))
    eps = 1e-12

    for _ in range(80):
        p1 = _gauss_pdf(xv, mu, s1)
        p2 = _gauss_pdf(xv, mu, s2)
        mix = w1 * p1 + (1.0 - w1) * p2 + eps
        r1 = (w1 * p1) / mix
        r2 = 1.0 - r1

        n1 = float(np.sum(yv * r1))
        n2 = float(np.sum(yv * r2))
        if n1 <= eps or n2 <= eps:
            return None

        w1_new = float(np.clip(n1 / n_tot, 0.01, 0.99))
        s1_new = float(np.sqrt(max(np.sum(yv * r1 * (xv - mu) ** 2) / n1, sig_min * sig_min)))
        s2_new = float(np.sqrt(max(np.sum(yv * r2 * (xv - mu) ** 2) / n2, sig_min * sig_min)))
        s1_new = float(np.clip(s1_new, sig_min, sig_max))
        s2_new = float(np.clip(s2_new, sig_min, sig_max))

        delta = max(
            abs(w1_new - w1),
            abs(s1_new - s1),
            abs(s2_new - s2),
        )

        w1, s1, s2 = w1_new, s1_new, s2_new
        if delta < 1e-5:
            break

    # Sort as narrow/wide by sigma (narrow = smaller sigma)
    if s1 > s2:
        s1, s2 = s2, s1
        w1 = 1.0 - w1
    w2 = 1.0 - w1

    # Requested combined sigma: linear weighted average of component sigmas.
    sigma_weighted = float(w1 * s1 + w2 * s2)
    pdf_all = w1 * _gauss_pdf(x, mu, s1) + w2 * _gauss_pdf(x, mu, s2)
    yfit = float(np.sum(y)) * float(binw) * pdf_all

    return {
        "yfit": yfit,
        "w1": float(w1),
        "w2": float(w2),
        "mu1": float(mu),
        "mu2": float(mu),
        "sigma1": float(s1),
        "sigma2": float(s2),
        "sigma_weighted": sigma_weighted,
    }


class TDCSelectDialog(QtWidgets.QDialog):
    """Popup dialog with checkboxes to select which TDCs to draw (multi-select)."""
    def __init__(self, parent=None, n_tdcs=40, checked=None):
        super().__init__(parent)
        self.setWindowTitle("Select TDCs")
        self.setModal(True)

        self._n_tdcs = int(n_tdcs)
        checked = set(checked or [])

        layout = QtWidgets.QVBoxLayout(self)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        inner = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(inner)
        scroll.setWidget(inner)

        self._cbs = []
        cols = 4
        for tdc in range(self._n_tdcs):
            cb = QtWidgets.QCheckBox(f"TDC {tdc:02d}")
            cb.setChecked(tdc in checked)
            self._cbs.append(cb)
            r = tdc // cols
            c = tdc % cols
            grid.addWidget(cb, r, c)

        btn_row = QtWidgets.QHBoxLayout()
        layout.addLayout(btn_row)

        btn_all = QtWidgets.QPushButton("All")
        btn_none = QtWidgets.QPushButton("None")
        btn_ok = QtWidgets.QPushButton("OK")
        btn_cancel = QtWidgets.QPushButton("Cancel")

        btn_row.addWidget(btn_all)
        btn_row.addWidget(btn_none)
        btn_row.addStretch(1)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)

        btn_all.clicked.connect(lambda: [cb.setChecked(True) for cb in self._cbs])
        btn_none.clicked.connect(lambda: [cb.setChecked(False) for cb in self._cbs])
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        self.resize(420, 520)

    def selected_tdcs(self):
        return [i for i, cb in enumerate(self._cbs) if cb.isChecked()]


class _HistPlot:
    """
    Fast step-hist plot; overlay stats positioned by view ratio (not data coords).
    """
    __slots__ = ("plot", "curve", "fit_curve", "stats_text", "_fx", "_fy")

    def __init__(self, plot: pg.PlotWidget, *, stats_pos=(0.0, 0.8), stats_anchor=(0, 1)):
        self.plot = plot
        self.plot.showGrid(x=True, y=True, alpha=0.2)
        self.plot.setMenuEnabled(False)
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.enableAutoRange(x=False, y=True)

        self.curve = self.plot.plot(
            [], [],
            stepMode=True,
            pen=pg.mkPen(color=(0, 0, 255), width=1.5)
        )
        self.fit_curve = self.plot.plot(
            [], [],
            pen=pg.mkPen(color=(220, 0, 0), width=1.4)
        )

        self._fx, self._fy = float(stats_pos[0]), float(stats_pos[1])
        self.stats_text = pg.TextItem("", anchor=stats_anchor, color=(0, 0, 0))

        vb = self.plot.getViewBox()
        vb.addItem(self.stats_text, ignoreBounds=True)
        vb.sigRangeChanged.connect(lambda *args: self._reposition_stats())

        self._reposition_stats()

    def clear(self, title=""):
        self.curve.setData([], [])
        self.fit_curve.setData([], [])
        self.plot.setTitle(title)
        self.stats_text.setText("")
        self._reposition_stats()

    def _reposition_stats(self):
        try:
            vb = self.plot.getViewBox()
            (x0, x1), (y0, y1) = vb.viewRange()
            x = x0 + self._fx * (x1 - x0)
            y = y0 + self._fy * (y1 - y0)
            self.stats_text.setPos(x, y)
        except Exception:
            return

    def update_counts(
        self,
        counts,
        *,
        title: str,
        xmin: float,
        xmax: float,
        xscale: float = 1.0,
        xlabel: str = "",
        xunits: str = "",
        show_stats: bool = True,
        fit_x=None,
        fit_y=None,
        extra_stats_lines=None,
    ):
        counts = np.asarray(counts)
        nb = int(counts.size)
        edges = np.linspace(xmin, xmax, nb + 1, dtype=np.float64) * float(xscale)

        self.curve.setData(edges, counts, stepMode=True)
        self.plot.setTitle(title)
        self.plot.setXRange(edges[0], edges[-1], padding=0.0)

        if xlabel:
            self.plot.setLabel("bottom", xlabel, units=xunits)

        if fit_y is not None:
            fy = np.asarray(fit_y, dtype=np.float64)
            if fit_x is None:
                fx = 0.5 * (edges[:-1] + edges[1:])
            else:
                fx = np.asarray(fit_x, dtype=np.float64)
            if fy.ndim == 1 and fx.ndim == 1 and fy.size == fx.size and fy.size > 0:
                self.fit_curve.setData(fx, fy)
            else:
                self.fit_curve.setData([], [])
        else:
            self.fit_curve.setData([], [])

        lines = []
        if show_stats:
            n = float(np.sum(counts))
            if n > 0:
                centers = 0.5 * (edges[:-1] + edges[1:])
                mean, std = _weighted_mean_std(centers, counts)
                lines.append(f"N={int(n)}")
                lines.append(f"mean={mean:.2f} {xunits}".strip())
                lines.append(f"std={std:.2f} {xunits}".strip())
            else:
                lines.append("N=0")
                lines.append("mean=0")
                lines.append("std=0")

        if extra_stats_lines:
            for line in extra_stats_lines:
                if line is None:
                    continue
                text = str(line).strip()
                if text:
                    lines.append(text)

        self.stats_text.setText("\n".join(lines))

        self._reposition_stats()


class _BarPlot24:
    """
    24-bin channel occupancy plot for one TDC.
    """
    __slots__ = ("plot", "bars", "rate_ref_line", "stats_text", "_fx", "_fy", "_log_y")

    def __init__(self, plot: pg.PlotWidget, *, stats_pos=(0.0, 0.8), stats_anchor=(0, 1)):
        self.plot = plot
        self.plot.setAxisItems({'left': SparseLogAxisItem(orientation='left')})
        self.plot.showGrid(x=True, y=True, alpha=0.2)
        self.plot.setMenuEnabled(False)
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.enableAutoRange(x=False, y=True)

        self._fx, self._fy = float(stats_pos[0]), float(stats_pos[1])
        self._log_y = False

        x = np.arange(24, dtype=np.float64)
        self.bars = pg.BarGraphItem(
            x=x,
            height=np.zeros(24, dtype=np.float64),
            width=0.9,
            brush=pg.mkBrush(0, 0, 255)
        )
        self.plot.addItem(self.bars)

        self.rate_ref_line = pg.InfiniteLine(
            pos=CH_HIT_RATE_REF_HZ,
            angle=0,
            pen=pg.mkPen(color=(210, 60, 0), width=1.2, style=QtCore.Qt.DashLine),
        )
        self.rate_ref_line.setVisible(False)
        self.plot.addItem(self.rate_ref_line)

        self.plot.setXRange(-0.5, 23.5, padding=0.0)
        self.plot.setLabel("bottom", "Channel", units="")
        self.plot.getAxis("bottom").setTicks([[(i, str(i)) for i in range(0, 24, 2)]])

        self.stats_text = pg.TextItem("", anchor=stats_anchor, color=(0, 0, 0))
        vb = self.plot.getViewBox()
        vb.addItem(self.stats_text, ignoreBounds=True)
        vb.sigRangeChanged.connect(lambda *args: self._reposition_stats())
        self._reposition_stats()

    def _reposition_stats(self):
        try:
            vb = self.plot.getViewBox()
            (x0, x1), (y0, y1) = vb.viewRange()
            x = x0 + self._fx * (x1 - x0)
            y = y0 + self._fy * (y1 - y0)
            self.stats_text.setPos(x, y)
        except Exception:
            return

    def clear(self, title=""):
        self.bars.setOpts(y0=0, height=np.zeros(24, dtype=np.float64))
        self.rate_ref_line.setVisible(False)
        self.plot.enableAutoRange(y=True)
        self.plot.setTitle(title)
        self.stats_text.setText("")
        self._reposition_stats()

    def set_log_y(self, enabled):
        self._log_y = bool(enabled)
        # Do not briefly interpret the old linear range as logarithmic powers.
        # The caller redraws the current data immediately after switching.
        self.bars.setOpts(y0=0, height=np.zeros(24, dtype=np.float64))
        self.rate_ref_line.setVisible(False)
        self.plot.setYRange(0, 1, padding=0)
        self.plot.setLogMode(x=False, y=self._log_y)
        self.plot.enableAutoRange(x=False, y=True)
        self.plot.setXRange(-0.5, 23.5, padding=0)

    def update_counts(
        self,
        counts24,
        *,
        title: str,
        ylabel: str = "Counts",
        yunits: str = "",
        total_label: str = "N",
        total_units: str = "",
        total_format: str = ".0f",
        extra_stats_lines=None,
        rate_ref_hz: float | None = None,
        show_rate_ref_below: bool = False,
        enabled_channel_mask=None,
        mean_label: str = "mean",
        mean_units: str = "",
        mean_format: str = ".3g",
        **_ignored,
    ):
        h = np.asarray(counts24, dtype=np.float64)
        if h.size != 24:
            h = np.resize(h, 24)

        self.plot.setTitle(title)
        self.plot.setLabel("left", ylabel, units=yunits)

        ymax = float(np.nanmax(h)) if h.size else 0.0
        show_ref = (
            rate_ref_hz is not None
            and bool(show_rate_ref_below)
            and np.isfinite(ymax)
            and ymax < float(rate_ref_hz)
        )
        self.rate_ref_line.setVisible(show_ref)
        baseline = 0.0
        if self._log_y:
            # BarGraphItem does not transform its geometry for PlotItem log
            # mode. Use log coordinates and a baseline below the smallest
            # positive value; zero/nonpositive values have no visible bar.
            positive = np.isfinite(h) & (h > 0)
            values = h[positive]
            if show_ref:
                values = np.append(values, float(rate_ref_hz))
            baseline = float(np.floor(np.log10(values.min())) - 1) if values.size else 0.0
            heights = np.zeros_like(h)
            heights[positive] = np.log10(h[positive]) - baseline
            self.bars.setOpts(y0=baseline, height=heights)
        else:
            self.bars.setOpts(y0=0, height=h)
        if show_ref:
            ref = float(rate_ref_hz)
            if self._log_y:
                self.rate_ref_line.setPos(float(np.log10(ref)))
                self.plot.setYRange(baseline, float(np.log10(ref)) + 0.05, padding=0.0)
            else:
                self.rate_ref_line.setPos(ref)
                self.plot.setYRange(0.0, max(ref * 1.05, ymax * 1.05, 1.0), padding=0.0)
        else:
            self.plot.enableAutoRange(y=True)

        total, mean, enabled_count = _enabled_total_mean(
            h, enabled_channel_mask
        )
        total_text = format(total, total_format)
        if total_units:
            total_text = f"{total_text} {total_units}"
        mean_text = format(mean, mean_format)
        if mean_units:
            mean_text = f"{mean_text} {mean_units}"
        lines = [
            f"{total_label}={total_text}",
            f"{mean_label}={mean_text}",
            f"enabled_ch={enabled_count}",
        ]

        if extra_stats_lines:
            for line in extra_stats_lines:
                if line is None:
                    continue
                text = str(line).strip()
                if text:
                    lines.append(text)

        self.stats_text.setText("\n".join(lines))

        self._reposition_stats()


# ======================================================================================
# Base Grid
# ======================================================================================

class _GridSpectraBase(QtCore.QObject):
    def __init__(
        self,
        parent_widget,
        backend,
        *,
        n_tdcs: int = 40,
        plots_rows: int = 2,
        plots_cols: int = 4,
        tab_name: str = "Spectra",
        x_label: str = "X",
        x_units: str = "",
        x_scale: float = 1.0,
        plot_wrapper_cls=_HistPlot,
    ):
        super().__init__(parent_widget)
        self.parent = parent_widget
        self.backend = backend
        self.n_tdcs = int(n_tdcs)

        self.plots_rows = int(plots_rows)
        self.plots_cols = int(plots_cols)
        self.plots_per_page = self.plots_rows * self.plots_cols

        self.tab_name = tab_name
        self.x_label = x_label
        self.x_units = x_units
        self.x_scale = float(x_scale)

        self.page = 0
        self._last_snap = None
        self._live_updates_enabled = True
        self._plot_wrapper_cls = plot_wrapper_cls
        self._plot_save_active_tdcs = None
        self._display_tdc_filter = None

        self._build_ui()
        self.parent.installEventFilter(self)

        if hasattr(self.backend, "analysis_1hz"):
            self.backend.analysis_1hz.connect(self.on_analysis_1hz)
        else:
            print(f"[WARN] backend has no 'analysis_1hz' signal; {self.tab_name} will not update.\n")

    def _build_controls(self, top_layout: QtWidgets.QHBoxLayout) -> None:
        raise NotImplementedError

    def eventFilter(self, watched, event):
        if (
            watched is self.parent
            and event.type() == QtCore.QEvent.Show
            and self._last_snap is not None
            and self._live_updates_enabled
            and not _spectra_update_suppressed(self.backend)
        ):
            QtCore.QTimer.singleShot(0, self._redraw)
        return super().eventFilter(watched, event)

    def set_live_updates_enabled(self, enabled: bool) -> None:
        self._live_updates_enabled = bool(enabled)

    def _max_pages(self) -> int:
        items = self._items_for_current_filter()
        n = len(items)
        return max(1, (n + self.plots_per_page - 1) // self.plots_per_page)

    def _all_items(self) -> list:
        raise NotImplementedError

    @staticmethod
    def _active_tdc_set(active_tdcs):
        if active_tdcs is None:
            return None
        out = set()
        for tdc in active_tdcs:
            try:
                out.add(int(tdc))
            except Exception:
                continue
        return out

    def set_display_tdcs(self, tdcs) -> bool:
        active = self._active_tdc_set(tdcs)
        if active is not None:
            active = {tdc for tdc in active if 0 <= int(tdc) < self.n_tdcs}
        if active == self._display_tdc_filter:
            return False

        self._display_tdc_filter = active
        self.page = 0
        self._clamp_page()
        self._redraw()
        return True

    def _items_for_current_filter(self) -> list:
        items = list(self._all_items())
        display = self._display_tdc_filter
        if display is not None:
            filtered = []
            for item in items:
                try:
                    if int(item) in display:
                        filtered.append(item)
                except Exception:
                    continue
            items = filtered

        active = self._plot_save_active_tdcs
        if active is None:
            return items
        filtered = []
        for item in items:
            try:
                if int(item) in active:
                    filtered.append(item)
            except Exception:
                continue
        return filtered

    def _items_per_page(self) -> list:
        items = self._items_for_current_filter()
        start = self.page * self.plots_per_page
        return items[start:start + self.plots_per_page]

    def _plot_for_item(self, snap, item):
        raise NotImplementedError

    def _prepare_plot_counts(self, snap, item, counts: np.ndarray, nbins: int):
        return counts, {}

    def _status_left_text(self) -> str:
        return ""

    def _x_limits(self, snap, counts: np.ndarray, nbins: int) -> tuple[float, float]:
        return 0.0, float(nbins)

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self.parent)

        top = QtWidgets.QHBoxLayout()
        layout.addLayout(top)

        self._build_controls(top)

        self.capture_status = QtWidgets.QLabel("No analysis snapshot yet.")
        self.capture_status.setWordWrap(False)
        self.capture_status.setMinimumWidth(0)
        self.capture_status.setSizePolicy(
            QtWidgets.QSizePolicy.Ignored,
            QtWidgets.QSizePolicy.Preferred,
        )
        top.addWidget(self.capture_status, 1)

        self.grid = pg.GraphicsLayoutWidget()
        layout.addWidget(self.grid, 1)

        self._plots = []
        for r in range(self.plots_rows):
            for c in range(self.plots_cols):
                pw = self.grid.addPlot(row=r, col=c)
                pw.setLabel("bottom", self.x_label, units=self.x_units)
                pw.setLabel("left", "Counts")
                self._plots.append(self._plot_wrapper_cls(pw, stats_pos=(0.0, 0.8), stats_anchor=(0, 1)))
        try:
            gl = self.grid.ci.layout
            for c in range(self.plots_cols):
                gl.setColumnStretchFactor(c, 1)
            for r in range(self.plots_rows):
                gl.setRowStretchFactor(r, 1)
        except Exception:
            pass

        nav = QtWidgets.QHBoxLayout()
        layout.addLayout(nav)

        self.lab_status = QtWidgets.QLabel("")
        nav.addWidget(self.lab_status, 1)

        self.lab_page = QtWidgets.QLabel("Page 1/1")
        self.lab_page.setMinimumWidth(110)
        self.lab_page.setAlignment(QtCore.Qt.AlignCenter)

        style = self.parent.style()
        self.btn_prev = QtWidgets.QPushButton()
        self.btn_prev.setIcon(style.standardIcon(QtWidgets.QStyle.SP_ArrowLeft))
        self.btn_next = QtWidgets.QPushButton()
        self.btn_next.setIcon(style.standardIcon(QtWidgets.QStyle.SP_ArrowRight))

        self.btn_prev.clicked.connect(self.prev_page)
        self.btn_next.clicked.connect(self.next_page)

        nav.addWidget(self.lab_page)
        nav.addWidget(self.btn_prev)
        nav.addWidget(self.btn_next)

    def _clamp_page(self):
        mp = self._max_pages()
        self.page = max(0, min(self.page, mp - 1))
        self.lab_page.setText(f"Page {self.page + 1}/{mp}")

    def prev_page(self):
        self.page -= 1
        self._clamp_page()
        self._redraw()

    def next_page(self):
        self.page += 1
        self._clamp_page()
        self._redraw()

    @QtCore.pyqtSlot(object)
    def on_analysis_1hz(self, snap):
        self._last_snap = snap
        if not self._live_updates_enabled:
            return
        if _spectra_update_suppressed(self.backend):
            self.capture_status.setText("Noise scan active: spectra held")
            return
        if not _widget_is_visible(self.parent):
            return

        self._clamp_page()

        # Works with BOTH snapshot formats:
        # - old: hit_cnt/trig_cnt/header_cnt/trailer_cnt
        # - new: hits_total/triggers/headers/trailers
        try:
            hits = getattr(snap, "hits_total", getattr(snap, "hit_cnt", 0))
            trg = getattr(snap, "triggers", getattr(snap, "trig_cnt", 0))
            hdr = getattr(snap, "headers", getattr(snap, "header_cnt", 0))
            trl = getattr(snap, "trailers", getattr(snap, "trailer_cnt", 0))

            ovf_arr = getattr(snap, "overflow_cnt", None)
            err_arr = getattr(snap, "decode_err_cnt", None)
            ovf = int(np.sum(ovf_arr)) if ovf_arr is not None else 0
            err = int(np.sum(err_arr)) if err_arr is not None else 0
            evt_valid = int(getattr(snap, "fit_evt_valid", 0))
            evt_total = int(getattr(snap, "fit_evt_total", 0))
            evt_ratio = float(getattr(snap, "fit_evt_valid_ratio", 0.0))
            if evt_total <= 0 and evt_valid > 0:
                evt_total = evt_valid
            if evt_total > 0 and not np.isfinite(evt_ratio):
                evt_ratio = float(evt_valid) / float(evt_total)

            self.capture_status.setText(
                f"5 s update | hits={int(hits)} | trig={int(trg)} | "
                f"hdr={int(hdr)} | trl={int(trl)} | ovf={ovf} | err={err} | "
                f"evt_valid={evt_valid}/{evt_total} ({evt_ratio * 100.0:.1f}%)"
            )
        except Exception:
            self.capture_status.setText("5 s update")

        self._redraw()

    def _redraw(self):
        snap = self._last_snap
        if snap is None:
            for hp in self._plots:
                hp.clear("")
            self.capture_status.setText("No analysis snapshot yet.")
            self.lab_status.setText("")
            self._clamp_page()
            return

        if getattr(self, "hist_attr", None) in ("tdc_hist", "tdc_ch_hist"):
            self.x_label = str(getattr(snap, "tdc_time_label", "hit_ledge - trigger_ledge"))
        self._clamp_page()
        items = self._items_per_page()

        self.lab_status.setText(self._status_left_text())

        for i, hp in enumerate(self._plots):
            if i >= len(items):
                hp.clear("")
                continue

            item = items[i]
            try:
                title, counts, nbins = self._plot_for_item(snap, item)
            except Exception as e:
                hp.clear(f"plot error: {type(e).__name__}")
                continue

            counts = np.asarray(counts)
            nbins = int(nbins) if nbins is not None else int(counts.size)

            if counts.size != nbins:
                if counts.size > nbins:
                    counts = counts[:nbins]
                else:
                    counts = np.pad(counts, (0, nbins - counts.size))

            xmin, xmax = self._x_limits(snap, counts, nbins)
            try:
                counts, extra_plot_kwargs = self._prepare_plot_counts(snap, item, counts, nbins)
                counts = np.asarray(counts)
            except Exception as e:
                hp.clear(f"plot error: {type(e).__name__}")
                continue

            hp.update_counts(
                counts,
                title=title,
                xmin=float(xmin),
                xmax=float(xmax),
                xscale=self.x_scale,
                xlabel=self.x_label,
                xunits=self.x_units,
                **extra_plot_kwargs,
            )

    def _export_item_name(self, item) -> str:
        try:
            return f"tdc_{int(item):02d}"
        except Exception:
            return _safe_plot_filename(str(item), "item")

    def _paged_status_text(self, *, empty: str = "tdcs=0") -> str:
        items = self._items_for_current_filter()
        n = len(items)
        if n == 0:
            return empty

        start = self.page * self.plots_per_page
        end = min(start + self.plots_per_page, n) - 1
        return f"tdcs={n} | showing {start} ~ {max(start, end)}"

    def save_plots(self, output_dir: str, active_tdcs=None) -> list[str]:
        if self._last_snap is None:
            return []
        os.makedirs(output_dir, exist_ok=True)
        saved: list[str] = []
        old_page = int(self.page)
        old_active_tdcs = self._plot_save_active_tdcs
        try:
            self._plot_save_active_tdcs = self._active_tdc_set(active_tdcs)
            for page in range(self._max_pages()):
                self.page = int(page)
                self._redraw()
                QtWidgets.QApplication.processEvents()
                items = self._items_per_page()
                for idx, item in enumerate(items):
                    if idx >= len(self._plots):
                        continue
                    name = f"{_safe_plot_filename(self.tab_name)}_{self._export_item_name(item)}.png"
                    path = os.path.join(output_dir, name)
                    if _export_plot_item_png(self._plots[idx].plot, path):
                        saved.append(path)
        finally:
            self._plot_save_active_tdcs = old_active_tdcs
            self.page = old_page
            self._redraw()
        return saved


# ======================================================================================
# Subclass 1: per-TDC spectra
# ======================================================================================

class tab_spectra_base(_GridSpectraBase):
    def __init__(
        self,
        parent_widget,
        backend,
        n_tdcs: int = 40,
        *,
        tab_name: str = "Spectra",
        hist_attr: str = "adc_hist",
        bins_attr: str = "adc_bins",
        x_label: str = "ADC time",
        x_units: str = "ns",
        x_scale: float = 1.0,
        title_prefix: str = "ADC",
        x_min_attr: str | None = None,
        x_max_attr: str | None = None,
        plots_rows: int = 2,
        plots_cols: int = 4,
    ):
        self.selected_tdcs = list(range(int(n_tdcs)))
        self.hist_attr = hist_attr
        self.bins_attr = bins_attr
        self.title_prefix = title_prefix
        self.x_min_attr = x_min_attr
        self.x_max_attr = x_max_attr

        super().__init__(
            parent_widget,
            backend,
            n_tdcs=n_tdcs,
            plots_rows=int(plots_rows),
            plots_cols=int(plots_cols),
            tab_name=tab_name,
            x_label=x_label,
            x_units=x_units,
            x_scale=x_scale,
        )

    def _build_controls(self, top_layout: QtWidgets.QHBoxLayout) -> None:
        self.btn_select = QtWidgets.QPushButton("Select TDCs")
        self.btn_select.setToolTip("Choose a subset; Mezz Config still limits which TDCs are visible.")
        self.btn_select.clicked.connect(self._open_select_dialog)
        top_layout.addWidget(self.btn_select)

    def _open_select_dialog(self):
        dlg = TDCSelectDialog(self.parent, n_tdcs=self.n_tdcs, checked=self.selected_tdcs)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            sel = dlg.selected_tdcs() or [0]
            self.selected_tdcs = sel
            self.page = 0
            self._clamp_page()
            self._redraw()

    def _all_items(self) -> list:
        return list(self.selected_tdcs)

    def _status_left_text(self) -> str:
        return self._paged_status_text()

    def _plot_for_item(self, snap, tdc):
        hists = getattr(snap, self.hist_attr, None)
        if hists is None:
            raise RuntimeError(f"missing {self.hist_attr}")

        nbins = getattr(snap, self.bins_attr, None)
        if nbins is None:
            nbins = len(hists[0]) if len(hists) else 0
        nbins = int(nbins)

        tdc = int(tdc)
        if not (0 <= tdc < len(hists)):
            return (f"TDC {tdc:02d} (out of range)", np.zeros(nbins, dtype=np.int64), nbins)

        counts = np.asarray(hists[tdc], dtype=np.int64)

        ovf_arr = getattr(snap, "overflow_cnt", None)
        err_arr = getattr(snap, "decode_err_cnt", None)
        ovf = ovf_arr[tdc] if ovf_arr is not None and tdc < len(ovf_arr) else 0
        err = err_arr[tdc] if err_arr is not None and tdc < len(err_arr) else 0

        title = f"TDC {tdc:02d} {self.title_prefix} (all ch) | ovf={int(ovf)} err={int(err)}"
        return (title, counts, nbins)

    def _x_limits(self, snap, counts: np.ndarray, nbins: int) -> tuple[float, float]:
        if self.x_min_attr and self.x_max_attr:
            try:
                return float(getattr(snap, self.x_min_attr)), float(getattr(snap, self.x_max_attr))
            except Exception:
                pass
        return super()._x_limits(snap, counts, nbins)


# ======================================================================================
# Subclass 2: per-channel spectra (requires snapshot to include adc_ch_hist/tdc_ch_hist)
# ======================================================================================

class tab_channel_spectra_base(_GridSpectraBase):
    def __init__(
        self,
        parent_widget,
        backend,
        n_tdcs: int = 40,
        n_channels: int = 24,
        *,
        tab_name: str = "Channel Spectra",
        hist_attr: str = "adc_ch_hist",
        bins_attr: str = "ch_adc_bins",
        x_label: str = "ADC time",
        x_units: str = "ns",
        x_scale: float = 1.0,
        title_prefix: str = "ADC",
        x_min_attr: str | None = None,
        x_max_attr: str | None = None,
    ):
        self.n_channels = int(n_channels)
        self.tdc = 0

        self.hist_attr = hist_attr
        self.bins_attr = bins_attr
        self.title_prefix = title_prefix
        self.x_min_attr = x_min_attr
        self.x_max_attr = x_max_attr

        super().__init__(
            parent_widget,
            backend,
            n_tdcs=n_tdcs,
            plots_rows=2,
            plots_cols=4,
            tab_name=tab_name,
            x_label=x_label,
            x_units=x_units,
            x_scale=x_scale,
        )

    def _build_controls(self, top_layout: QtWidgets.QHBoxLayout) -> None:
        top_layout.addWidget(QtWidgets.QLabel("TDC:"))
        self.spin_tdc = QtWidgets.QSpinBox()
        self.spin_tdc.setRange(0, self.n_tdcs - 1)
        self.spin_tdc.setValue(self.tdc)
        self.spin_tdc.valueChanged.connect(self._on_tdc_changed)
        top_layout.addWidget(self.spin_tdc)

    def _on_tdc_changed(self, v: int):
        self.tdc = int(v)
        self.page = 0
        self._clamp_page()
        self._redraw()

    def _max_pages(self) -> int:
        n = self.n_channels
        return max(1, (n + self.plots_per_page - 1) // self.plots_per_page)

    def _all_items(self) -> list:
        return list(range(self.n_channels))

    def _status_left_text(self) -> str:
        start = self.page * self.plots_per_page
        end = min(start + self.plots_per_page, self.n_channels) - 1
        return f"TDC {self.tdc:02d} | channels {start} ~ {max(start, end)}"

    def _plot_for_item(self, snap, ch):
        ch_hists = getattr(snap, self.hist_attr, None)
        if ch_hists is None:
            # With your current DecodeSnapshot, this will happen (no channel hist in Decode.py)
            raise RuntimeError(f"missing {self.hist_attr}")

        nbins = getattr(snap, self.bins_attr, None)
        if nbins is None:
            if 0 <= self.tdc < len(ch_hists) and len(ch_hists[self.tdc]) > 0:
                nbins = len(ch_hists[self.tdc][0])
            else:
                nbins = 0
        nbins = int(nbins)

        if not (0 <= self.tdc < len(ch_hists)):
            return (f"TDC {self.tdc:02d} (out of range)", np.zeros(nbins, dtype=np.int64), nbins)

        ch = int(ch)
        if not (0 <= ch < len(ch_hists[self.tdc])):
            return (f"TDC {self.tdc:02d} CH {ch:02d} (out of range)", np.zeros(nbins, dtype=np.int64), nbins)

        counts = np.asarray(ch_hists[self.tdc][ch], dtype=np.int64)
        title = f"TDC {self.tdc:02d} CH {ch:02d} {self.title_prefix}"
        return (title, counts, nbins)

    def _export_item_name(self, item) -> str:
        try:
            return f"tdc_{int(self.tdc):02d}_ch_{int(item):02d}"
        except Exception:
            return _safe_plot_filename(f"tdc_{self.tdc}_{item}", "channel")

    def save_plots(self, output_dir: str, active_tdcs=None) -> list[str]:
        if self._last_snap is None:
            return []
        os.makedirs(output_dir, exist_ok=True)
        saved: list[str] = []
        old_tdc = int(self.tdc)
        old_page = int(self.page)
        active = self._active_tdc_set(active_tdcs)
        tdcs = list(range(self.n_tdcs))
        if active is not None:
            tdcs = [tdc for tdc in tdcs if tdc in active]
        try:
            for tdc in tdcs:
                self.tdc = int(tdc)
                try:
                    self.spin_tdc.blockSignals(True)
                    self.spin_tdc.setValue(int(tdc))
                    self.spin_tdc.blockSignals(False)
                except Exception:
                    pass
                for page in range(self._max_pages()):
                    self.page = int(page)
                    self._redraw()
                    QtWidgets.QApplication.processEvents()
                    items = self._items_per_page()
                    for idx, item in enumerate(items):
                        if idx >= len(self._plots):
                            continue
                        name = f"{_safe_plot_filename(self.tab_name)}_{self._export_item_name(item)}.png"
                        path = os.path.join(output_dir, name)
                        if _export_plot_item_png(self._plots[idx].plot, path):
                            saved.append(path)
        finally:
            self.tdc = old_tdc
            self.page = old_page
            try:
                self.spin_tdc.blockSignals(True)
                self.spin_tdc.setValue(old_tdc)
                self.spin_tdc.blockSignals(False)
            except Exception:
                pass
            self._redraw()
        return saved

    def _x_limits(self, snap, counts: np.ndarray, nbins: int) -> tuple[float, float]:
        if self.x_min_attr and self.x_max_attr:
            try:
                return float(getattr(snap, self.x_min_attr)), float(getattr(snap, self.x_max_attr))
            except Exception:
                pass
        return super()._x_limits(snap, counts, nbins)


class tab_channel_hits_base(_GridSpectraBase):
    def __init__(
        self,
        parent_widget,
        backend,
        n_tdcs: int = 40,
        *,
        tab_name: str = "CH Hits",
        ch_hist_attr: str = "adc_ch_hist",
        title_prefix: str = "CH hits",
        active_channels_callback=None,
    ):
        self.selected_tdcs = list(range(int(n_tdcs)))
        self.ch_hist_attr = ch_hist_attr
        self.title_prefix = title_prefix
        self._active_channels_callback = active_channels_callback
        self._rate_mode = True

        super().__init__(
            parent_widget,
            backend,
            n_tdcs=n_tdcs,
            plots_rows=2,
            plots_cols=4,
            tab_name=tab_name,
            x_label="Channel",
            x_units="",
            x_scale=1.0,
            plot_wrapper_cls=_BarPlot24,
        )
        self._set_y_axis_labels()

    def _build_controls(self, top_layout: QtWidgets.QHBoxLayout) -> None:
        self.btn_select = QtWidgets.QPushButton("Select TDCs")
        self.btn_select.setToolTip("Choose a subset; Mezz Config still limits which TDCs are visible.")
        self.btn_select.clicked.connect(self._open_select_dialog)
        top_layout.addWidget(self.btn_select)

        self.chk_rate = QtWidgets.QCheckBox("Rate")
        self.chk_rate.setChecked(self._rate_mode)
        self.chk_rate.setToolTip(
            "Triggered: hits / event-window exposure. "
            "Triggerless: decoded hits / acquisition time, or direct firmware counter rate."
        )
        self.chk_rate.toggled.connect(self._on_rate_toggled)
        top_layout.addWidget(self.chk_rate)
        self.chk_log_y = QtWidgets.QCheckBox("Log Y scale")
        self.chk_log_y.setToolTip("Use a logarithmic Y axis for all CH Hits plots. Zero and negative values have no visible bar.")
        self.chk_log_y.toggled.connect(self._on_log_y_toggled)
        top_layout.addWidget(self.chk_log_y)

    def _on_log_y_toggled(self, checked):
        for hp in self._plots:
            hp.set_log_y(checked)
        self._redraw()

    def _on_rate_toggled(self, checked: bool):
        self._rate_mode = bool(checked)
        self._set_y_axis_labels()
        self._redraw()

    def _set_y_axis_labels(self):
        ylabel, yunits = ("Rate", "Hz") if self._rate_mode else ("Counts", "")
        for hp in getattr(self, "_plots", []):
            try:
                hp.plot.setLabel("left", ylabel, units=yunits)
            except Exception:
                pass

    def _open_select_dialog(self):
        dlg = TDCSelectDialog(self.parent, n_tdcs=self.n_tdcs, checked=self.selected_tdcs)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            sel = dlg.selected_tdcs() or [0]
            self.selected_tdcs = sel
            self.page = 0
            self._clamp_page()
            self._redraw()

    def _all_items(self) -> list:
        return list(self.selected_tdcs)

    def _status_left_text(self) -> str:
        text = self._paged_status_text()
        if self._rate_mode:
            snap = self._last_snap
            if self._is_triggerless(snap):
                if self._has_noise_counter_rate(snap):
                    text += " | triggerless rate=firmware counters"
                else:
                    duration_s = self._triggerless_rate_duration_s(snap)
                    source = str(getattr(snap, "hit_rate_duration_source", "elapsed acquisition"))
                    text += f" | triggerless rate=decoded hits / {duration_s:.3g} s ({source})"
            else:
                windows = self._event_windows(snap) if snap is not None else 0
                duration_s = float(windows) * CH_HIT_TIME_WINDOW_S
                text += f" | rate window={windows} x 1.50 us = {duration_s:.3g} s"
        return text

    @staticmethod
    def _is_triggerless(snap) -> bool:
        try:
            return int(getattr(snap, "acquisition_mode", 0)) == 1
        except Exception:
            return False

    @staticmethod
    def _has_noise_counter_rate(snap) -> bool:
        if snap is None or getattr(snap, "noise_counter_rate", None) is None:
            return False
        try:
            return int(getattr(snap, "noise_counters", 0) or 0) > 0
        except Exception:
            return False

    @staticmethod
    def _triggerless_rate_duration_s(snap) -> float:
        try:
            return max(0.0, float(getattr(snap, "hit_rate_duration_s", 0.0) or 0.0))
        except Exception:
            return 0.0

    def _event_windows(self, snap) -> int:
        if snap is None:
            return 0
        try:
            headers = int(getattr(snap, "headers", getattr(snap, "header_cnt", 0)) or 0)
        except Exception:
            headers = 0
        if headers > 0:
            return headers

        try:
            fifo_a = int(getattr(snap, "events_fifoA", 0) or 0)
            fifo_b = int(getattr(snap, "events_fifoB", 0) or 0)
        except Exception:
            fifo_a = 0
            fifo_b = 0
        fifo_windows = fifo_a + fifo_b
        if fifo_windows > 0:
            return fifo_windows

        try:
            return max(0, int(getattr(snap, "trailers", getattr(snap, "trailer_cnt", 0)) or 0))
        except Exception:
            return 0

    @staticmethod
    def _tdc_issue_stats(snap, tdc) -> list[str]:
        try:
            tdc = int(tdc)
        except Exception:
            return []

        lines = []
        for attr, label in (("overflow_cnt", "ovf"), ("decode_err_cnt", "err")):
            values = getattr(snap, attr, None)
            try:
                value = int(values[tdc]) if values is not None and 0 <= tdc < len(values) else 0
            except Exception:
                value = 0
            if value != 0:
                lines.append(f"{label}={value}")
        return lines

    def _enabled_channel_mask(self, tdc, channel_count: int) -> np.ndarray:
        channel_count = max(0, int(channel_count))
        callback = self._active_channels_callback
        if not callable(callback):
            return np.ones(channel_count, dtype=bool)

        try:
            active_by_tdc = callback()
        except Exception:
            return np.ones(channel_count, dtype=bool)
        if not isinstance(active_by_tdc, dict):
            return np.ones(channel_count, dtype=bool)

        try:
            tdc = int(tdc)
        except Exception:
            return np.ones(channel_count, dtype=bool)

        active_channels = active_by_tdc.get(tdc, active_by_tdc.get(str(tdc), []))
        mask = np.zeros(channel_count, dtype=bool)
        for channel in active_channels or []:
            try:
                channel = int(channel)
            except Exception:
                continue
            if 0 <= channel < channel_count:
                mask[channel] = True
        return mask

    def _prepare_plot_counts(self, snap, item, counts: np.ndarray, nbins: int):
        issue_stats = self._tdc_issue_stats(snap, item)
        enabled_mask = self._enabled_channel_mask(item, nbins)
        if not self._rate_mode:
            return counts, {
                "ylabel": "Counts",
                "yunits": "",
                "total_label": "N",
                "total_units": "",
                "total_format": ".0f",
                "enabled_channel_mask": enabled_mask,
                "mean_label": "mean_count",
                "mean_format": ".3g",
                "extra_stats_lines": issue_stats,
            }

        if self._is_triggerless(snap) and self._has_noise_counter_rate(snap):
            plot_counts = np.asarray(counts, dtype=np.float64)
        else:
            if self._is_triggerless(snap):
                duration_s = self._triggerless_rate_duration_s(snap)
            else:
                windows = self._event_windows(snap)
                duration_s = float(windows) * CH_HIT_TIME_WINDOW_S

            if duration_s > 0.0:
                plot_counts = np.asarray(counts, dtype=np.float64) / duration_s
            else:
                plot_counts = np.zeros_like(np.asarray(counts, dtype=np.float64))

        return plot_counts, {
            "ylabel": "Rate",
            "yunits": "Hz",
            "total_label": "sum_rate",
            "total_units": "Hz",
            "total_format": ".3g",
            "enabled_channel_mask": enabled_mask,
            "mean_label": "mean_rate",
            "mean_units": "Hz",
            "mean_format": ".3g",
            "rate_ref_hz": CH_HIT_RATE_REF_HZ,
            "show_rate_ref_below": True,
            "extra_stats_lines": issue_stats,
        }

    def _plot_for_item(self, snap, tdc):
        tdc = int(tdc)
        if self._rate_mode and self._is_triggerless(snap):
            if self._has_noise_counter_rate(snap):
                rate_arr = np.asarray(getattr(snap, "noise_counter_rate"))
                counts24 = rate_arr[tdc] if 0 <= tdc < len(rate_arr) else np.zeros(24, dtype=np.float64)
            else:
                raw_arr = np.asarray(getattr(snap, "raw_hit_ch_count", np.zeros((0, 24), dtype=np.int64)))
                counts24 = raw_arr[tdc] if 0 <= tdc < len(raw_arr) else np.zeros(24, dtype=np.int64)
        else:
            ch_hists = getattr(snap, self.ch_hist_attr, None)
            if ch_hists is None:
                raise RuntimeError(f"missing {self.ch_hist_attr}")
            if not (0 <= tdc < len(ch_hists)):
                return (f"TDC {tdc:02d} (out of range)", np.zeros(24, dtype=np.int64), 24)

            arr = np.asarray(ch_hists[tdc])
            if arr.ndim != 2:
                return (f"TDC {tdc:02d} bad dim", np.zeros(24, dtype=np.int64), 24)
            counts24 = arr.sum(axis=1)

        title = f"TDC {tdc:02d} rate" if self._rate_mode else f"TDC {tdc:02d} {self.title_prefix}"
        return (title, counts24, 24)


# ======================================================================================
# Concrete Tabs
# ======================================================================================

class tab_adc_spectra(tab_spectra_base):
    def __init__(self, parent_widget, backend, n_tdcs: int = 40):
        self._adc_fit_only = False
        super().__init__(
            parent_widget,
            backend,
            n_tdcs=n_tdcs,
            tab_name="ADC Spectra",
            hist_attr="adc_hist",
            bins_attr="adc_bins",          # optional; inferred if missing (DecodeSnapshot)
            x_label="ADC time",
            x_units="ns",
            x_scale=ADC_LSB_NS,
            title_prefix="ADC",
        )

    def _build_controls(self, top_layout: QtWidgets.QHBoxLayout) -> None:
        super()._build_controls(top_layout)
        self.chk_fit_only = QtWidgets.QCheckBox("Fit data only")
        self.chk_fit_only.setChecked(False)
        self.chk_fit_only.toggled.connect(self._on_toggle_fit_only)
        top_layout.addWidget(self.chk_fit_only)

    def _on_toggle_fit_only(self, checked: bool):
        self._adc_fit_only = bool(checked)
        self._redraw()

    def _plot_for_item(self, snap, tdc):
        if self._adc_fit_only:
            hists = getattr(snap, "fit_adc_hist", None)
            if hists is None:
                raise RuntimeError("missing fit_adc_hist")
            nbins = getattr(snap, "fit_adc_bins", None)
        else:
            hists = getattr(snap, "adc_hist", None)
            if hists is None:
                raise RuntimeError("missing adc_hist")
            nbins = getattr(snap, "adc_bins", None)

        if nbins is None:
            nbins = len(hists[0]) if len(hists) else 0
        nbins = int(nbins)

        tdc = int(tdc)
        if not (0 <= tdc < len(hists)):
            return (f"TDC {tdc:02d} (out of range)", np.zeros(nbins, dtype=np.int64), nbins)

        counts = np.asarray(hists[tdc], dtype=np.int64)

        ovf_arr = getattr(snap, "overflow_cnt", None)
        err_arr = getattr(snap, "decode_err_cnt", None)
        ovf = ovf_arr[tdc] if ovf_arr is not None and tdc < len(ovf_arr) else 0
        err = err_arr[tdc] if err_arr is not None and tdc < len(err_arr) else 0

        title = f"TDC {tdc:02d} ADC (all ch) | ovf={int(ovf)} err={int(err)}"
        return (title, counts, nbins)


class tab_tdc_spectra(tab_spectra_base):
    def __init__(self, parent_widget, backend, n_tdcs: int = 40):
        super().__init__(
            parent_widget,
            backend,
            n_tdcs=n_tdcs,
            tab_name="TDC Spectra",
            hist_attr="tdc_hist",
            bins_attr="tdc_bins",          # optional; inferred if missing (DecodeSnapshot)
            x_label="hit_ledge - trigger_ledge",
            x_units="ns",
            x_scale=1.0,
            title_prefix="TDC",
            x_min_attr="tdc_time_min_ns",
            x_max_attr="tdc_time_max_ns",
        )


class tab_adc_channels(tab_channel_spectra_base):
    def __init__(self, parent_widget, backend, n_tdcs: int = 40, n_channels: int = 24):
        self._adc_fit_only = False
        super().__init__(
            parent_widget,
            backend,
            n_tdcs=n_tdcs,
            n_channels=n_channels,
            tab_name="ADC Channels",
            hist_attr="adc_ch_hist",
            bins_attr="ch_adc_bins",
            x_label="ADC time",
            x_units="ns",
            x_scale=ADC_LSB_NS,
            title_prefix="ADC",
        )

    def _build_controls(self, top_layout: QtWidgets.QHBoxLayout) -> None:
        super()._build_controls(top_layout)
        self.chk_fit_only = QtWidgets.QCheckBox("Fit data only")
        self.chk_fit_only.setChecked(False)
        self.chk_fit_only.toggled.connect(self._on_toggle_fit_only)
        top_layout.addWidget(self.chk_fit_only)

    def _on_toggle_fit_only(self, checked: bool):
        self._adc_fit_only = bool(checked)
        self._redraw()

    def _plot_for_item(self, snap, ch):
        if self._adc_fit_only:
            ch_hists = getattr(snap, "fit_adc_ch_hist", None)
            if ch_hists is None:
                raise RuntimeError("missing fit_adc_ch_hist")
            nbins = getattr(snap, "fit_ch_adc_bins", None)
        else:
            ch_hists = getattr(snap, "adc_ch_hist", None)
            if ch_hists is None:
                raise RuntimeError("missing adc_ch_hist")
            nbins = getattr(snap, "ch_adc_bins", None)

        if nbins is None:
            if 0 <= self.tdc < len(ch_hists) and len(ch_hists[self.tdc]) > 0:
                nbins = len(ch_hists[self.tdc][0])
            else:
                nbins = 0
        nbins = int(nbins)

        if not (0 <= self.tdc < len(ch_hists)):
            return (f"TDC {self.tdc:02d} (out of range)", np.zeros(nbins, dtype=np.int64), nbins)

        ch = int(ch)
        if not (0 <= ch < len(ch_hists[self.tdc])):
            return (f"TDC {self.tdc:02d} CH {ch:02d} (out of range)", np.zeros(nbins, dtype=np.int64), nbins)

        counts = np.asarray(ch_hists[self.tdc][ch], dtype=np.int64)
        title = f"TDC {self.tdc:02d} CH {ch:02d} ADC"
        return (title, counts, nbins)


class tab_tdc_channels(tab_channel_spectra_base):
    def __init__(self, parent_widget, backend, n_tdcs: int = 40, n_channels: int = 24):
        super().__init__(
            parent_widget,
            backend,
            n_tdcs=n_tdcs,
            n_channels=n_channels,
            tab_name="TDC Channels",
            hist_attr="tdc_ch_hist",
            bins_attr="ch_tdc_bins",
            x_label="hit_ledge - trigger_ledge",
            x_units="ns",
            x_scale=1.0,
            title_prefix="TDC",
            x_min_attr="tdc_time_min_ns",
            x_max_attr="tdc_time_max_ns",
        )


class tab_adc_channel_hits(tab_channel_hits_base):
    def __init__(
        self,
        parent_widget,
        backend,
        n_tdcs: int = 40,
        active_channels_callback=None,
    ):
        super().__init__(
            parent_widget,
            backend,
            n_tdcs=n_tdcs,
            tab_name="ADC CH Hits",
            ch_hist_attr="adc_ch_hist",
            title_prefix="CH hits",
            active_channels_callback=active_channels_callback,
        )


class tab_fit_residual_spectra(tab_spectra_base):
    def __init__(
        self,
        parent_widget,
        backend,
        n_tdcs: int = 40,
        *,
        chamber_id: int | None = None,
        default_tdcs=None,
    ):
        self.chamber_id = None if chamber_id is None else int(chamber_id)
        self._fallback_tdcs = []
        super().__init__(
            parent_widget,
            backend,
            n_tdcs=n_tdcs,
            tab_name="Fit Residuals",
            hist_attr="fit_residual_hist",
            bins_attr="fit_residual_bins",
            x_label="Residual",
            x_units="mm",
            x_scale=1.0,
            title_prefix="Residual",
            x_min_attr="fit_residual_min_mm",
            x_max_attr="fit_residual_max_mm",
            plots_rows=2,
            plots_cols=3,
        )
        if default_tdcs is not None:
            self._fallback_tdcs = [int(t) for t in default_tdcs if 0 <= int(t) < int(n_tdcs)]
            self.page = 0
            self._clamp_page()

    def _build_controls(self, top_layout: QtWidgets.QHBoxLayout) -> None:
        # Chamber-specific residual tabs follow the chamber's current active TDCs.
        # A manual TDC selector here would go stale after geometry remaps.
        if self.chamber_id is None:
            super()._build_controls(top_layout)

    def _chamber_active_tdcs(self) -> list[int]:
        if self.chamber_id is None:
            return list(self.selected_tdcs)

        geo = None
        if self.backend is not None and hasattr(self.backend, "get_geometry"):
            try:
                geo = self.backend.get_geometry(self.chamber_id)
            except Exception:
                geo = None

        is_active = getattr(geo, "isActiveTDC", None)
        if is_active is not None:
            try:
                active = [t for t, flag in enumerate(is_active) if int(flag) == 1]
                if active:
                    return active
            except Exception:
                pass

        return list(self._fallback_tdcs)

    def _all_items(self) -> list:
        if self.chamber_id is None:
            return super()._all_items()
        return self._chamber_active_tdcs()

    def _status_left_text(self) -> str:
        if self.chamber_id is None:
            return super()._status_left_text()

        items = self._all_items()
        start = self.page * self.plots_per_page
        end = min(start + self.plots_per_page, len(items)) - 1
        if len(items) == 0:
            return f"chamber={self.chamber_id} | active_tdcs=0"
        return (
            f"chamber={self.chamber_id} | active_tdcs={len(items)} | "
            f"showing {start} ~ {max(start, end)}"
        )

    def _plot_for_item(self, snap, tdc):
        nbins = int(getattr(snap, "fit_residual_bins", 0))
        tdc = int(tdc)

        if self.chamber_id is None:
            hists = getattr(snap, "fit_residual_hist", None)
        else:
            by_ch = getattr(snap, "fit_residual_hist_by_chamber", None)
            hists = by_ch.get(self.chamber_id) if isinstance(by_ch, dict) else None

        if hists is None:
            title = (
                f"Chamber {self.chamber_id} TDC {tdc:02d} Residual"
                if self.chamber_id is not None
                else f"TDC {tdc:02d} Residual"
            )
            return (title, np.zeros(nbins, dtype=np.int64), nbins)

        if nbins <= 0:
            nbins = len(hists[0]) if len(hists) else 0
        nbins = int(nbins)

        if not (0 <= tdc < len(hists)):
            title = (
                f"Chamber {self.chamber_id} TDC {tdc:02d} (out of range)"
                if self.chamber_id is not None
                else f"TDC {tdc:02d} (out of range)"
            )
            return (title, np.zeros(nbins, dtype=np.int64), nbins)

        counts = np.asarray(hists[tdc], dtype=np.int64)
        prefix = f"Chamber {self.chamber_id} | " if self.chamber_id is not None else ""
        title = f"{prefix}TDC {tdc:02d} Residual"
        return (title, counts, nbins)

    def _redraw(self):
        snap = self._last_snap
        if snap is None:
            for hp in self._plots:
                hp.clear("")
            self.capture_status.setText("No analysis snapshot yet.")
            self.lab_status.setText("")
            self._clamp_page()
            return

        self._clamp_page()
        items = self._items_per_page()
        self.lab_status.setText(self._status_left_text())

        for i, hp in enumerate(self._plots):
            if i >= len(items):
                hp.clear("")
                continue

            tdc = items[i]
            try:
                title, counts, nbins = self._plot_for_item(snap, tdc)
            except Exception as e:
                hp.clear(f"plot error: {type(e).__name__}")
                continue

            counts = np.asarray(counts, dtype=np.float64)
            nbins = int(nbins) if nbins is not None else int(counts.size)
            if counts.size != nbins:
                if counts.size > nbins:
                    counts = counts[:nbins]
                else:
                    counts = np.pad(counts, (0, nbins - counts.size))

            xmin, xmax = self._x_limits(snap, counts, nbins)
            edges = np.linspace(float(xmin), float(xmax), nbins + 1, dtype=np.float64)
            centers = 0.5 * (edges[:-1] + edges[1:])
            binw = float((float(xmax) - float(xmin)) / max(1, nbins))

            fit = _fit_double_gauss_hist(centers, counts, binw)
            fit_y = None
            extra_lines = None
            if fit is not None:
                fit_y = fit["yfit"]
                extra_lines = [f"sigma_w={fit['sigma_weighted']:.3f} mm"]

            hp.update_counts(
                counts,
                title=title,
                xmin=float(xmin),
                xmax=float(xmax),
                xscale=self.x_scale,
                xlabel=self.x_label,
                xunits=self.x_units,
                fit_x=centers,
                fit_y=fit_y,
                extra_stats_lines=extra_lines,
            )


class tab_fit_residual_overall(QtCore.QObject):
    """
    Single residual histogram summed over all TDCs (all tubes), with
    double-Gaussian fit overlay and weighted sigma readout.
    """
    def __init__(self, parent_widget, backend, *, chamber_id: int | None = None):
        super().__init__(parent_widget)
        self.parent = parent_widget
        self.backend = backend
        self.chamber_id = None if chamber_id is None else int(chamber_id)
        self._last_snap = None
        self._live_updates_enabled = True
        self._build_ui()
        self.parent.installEventFilter(self)

        if hasattr(self.backend, "analysis_1hz"):
            self.backend.analysis_1hz.connect(self.on_analysis_1hz)
        else:
            print("[WARN] backend has no 'analysis_1hz' signal; Residual overall will not update.\n")

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self.parent)

        top = QtWidgets.QHBoxLayout()
        layout.addLayout(top)

        self.capture_status = QtWidgets.QLabel("No analysis snapshot yet.")
        self.fit_status = QtWidgets.QLabel("Double-Gauss: n/a")
        top.addWidget(self.capture_status, 1)
        top.addWidget(self.fit_status, 0)

        self.plot = pg.PlotWidget()
        self.plot.showGrid(x=True, y=True, alpha=0.2)
        self.plot.setMenuEnabled(False)
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.enableAutoRange(x=False, y=True)
        self.plot.setLabel("bottom", "Residual", units="mm")
        self.plot.setLabel("left", "Counts")
        if self.chamber_id is not None:
            self.plot.setTitle(f"Chamber {self.chamber_id} residual overall")
        layout.addWidget(self.plot, 1)

        self.hist_curve = self.plot.plot(
            [], [],
            stepMode=True,
            pen=pg.mkPen(color=(0, 0, 255), width=1.5),
        )
        self.fit_curve = self.plot.plot(
            [], [],
            pen=pg.mkPen(color=(220, 0, 0), width=2.0),
        )

        self.stats_text = pg.TextItem("", anchor=(0, 1), color=(0, 0, 0))
        vb = self.plot.getViewBox()
        vb.addItem(self.stats_text, ignoreBounds=True)
        vb.sigRangeChanged.connect(lambda *args: self._reposition_stats())
        self._reposition_stats()

    def eventFilter(self, watched, event):
        if (
            watched is self.parent
            and event.type() == QtCore.QEvent.Show
            and self._last_snap is not None
            and self._live_updates_enabled
            and not _spectra_update_suppressed(self.backend)
        ):
            QtCore.QTimer.singleShot(0, self._redraw)
        return super().eventFilter(watched, event)

    def set_live_updates_enabled(self, enabled: bool) -> None:
        self._live_updates_enabled = bool(enabled)

    def _reposition_stats(self):
        try:
            vb = self.plot.getViewBox()
            (x0, x1), (y0, y1) = vb.viewRange()
            self.stats_text.setPos(x0 + 0.01 * (x1 - x0), y0 + 0.85 * (y1 - y0))
        except Exception:
            return

    @staticmethod
    def _gauss_pdf(x: np.ndarray, mu: float, sigma: float) -> np.ndarray:
        s = max(float(sigma), 1e-9)
        z = (x - float(mu)) / s
        return np.exp(-0.5 * z * z) / (s * np.sqrt(2.0 * np.pi))

    @classmethod
    def _fit_double_gauss_hist(
        cls,
        centers: np.ndarray,
        counts: np.ndarray,
        binw: float,
    ):
        return _fit_double_gauss_hist(centers, counts, binw)

    @QtCore.pyqtSlot(object)
    def on_analysis_1hz(self, snap):
        self._last_snap = snap
        if not self._live_updates_enabled:
            return
        if _spectra_update_suppressed(self.backend):
            self.capture_status.setText("Noise scan active: spectra held")
            return
        if not _widget_is_visible(self.parent):
            return

        try:
            hits = getattr(snap, "hits_total", getattr(snap, "hit_cnt", 0))
            trg = getattr(snap, "triggers", getattr(snap, "trig_cnt", 0))
            evt_valid = int(getattr(snap, "fit_evt_valid", 0))
            evt_total = int(getattr(snap, "fit_evt_total", 0))
            evt_ratio = float(getattr(snap, "fit_evt_valid_ratio", 0.0))
            if evt_total <= 0 and evt_valid > 0:
                evt_total = evt_valid
            if evt_total > 0 and not np.isfinite(evt_ratio):
                evt_ratio = float(evt_valid) / float(evt_total)
            prefix = f"chamber={self.chamber_id} | " if self.chamber_id is not None else ""
            self.capture_status.setText(
                f"5 s update | {prefix}hits={int(hits)} | trig={int(trg)} | "
                f"evt_valid={evt_valid}/{evt_total} ({evt_ratio * 100.0:.1f}%)"
            )
        except Exception:
            self.capture_status.setText("5 s update")
        self._redraw()

    def _redraw(self):
        snap = self._last_snap
        if snap is None:
            self.hist_curve.setData([], [])
            self.fit_curve.setData([], [])
            self.stats_text.setText("")
            self.fit_status.setText("Double-Gauss: n/a")
            return

        if self.chamber_id is None:
            arr = getattr(snap, "fit_residual_hist", None)
        else:
            by_ch = getattr(snap, "fit_residual_hist_by_chamber", None)
            arr = by_ch.get(self.chamber_id) if isinstance(by_ch, dict) else None
        if arr is None:
            self.hist_curve.setData([], [])
            self.fit_curve.setData([], [])
            self.stats_text.setText("")
            if self.chamber_id is None:
                self.fit_status.setText("Double-Gauss: missing residual hist")
            else:
                self.fit_status.setText(f"Double-Gauss: no residual hist for chamber {self.chamber_id}")
            return

        h = np.asarray(arr, dtype=np.float64)
        if h.ndim == 2:
            counts = np.sum(h, axis=0)
        elif h.ndim == 1:
            counts = h
        else:
            self.fit_status.setText("Double-Gauss: bad residual hist shape")
            return

        nbins = int(getattr(snap, "fit_residual_bins", counts.size))
        if counts.size != nbins:
            if counts.size > nbins:
                counts = counts[:nbins]
            else:
                counts = np.pad(counts, (0, nbins - counts.size))

        xmin = float(getattr(snap, "fit_residual_min_mm", -5.0))
        xmax = float(getattr(snap, "fit_residual_max_mm", 5.0))
        edges = np.linspace(xmin, xmax, nbins + 1, dtype=np.float64)
        centers = 0.5 * (edges[:-1] + edges[1:])
        binw = float((xmax - xmin) / max(1, nbins))

        self.hist_curve.setData(edges, counts, stepMode=True)
        self.plot.setXRange(xmin, xmax, padding=0.0)

        n = float(np.sum(counts))
        if n > 0.0:
            mean, std = _weighted_mean_std(centers, counts)
            self.stats_text.setText(f"N={int(n)}\nmean={mean:.3f} mm\nstd={std:.3f} mm")
        else:
            self.stats_text.setText("N=0\nmean=0\nstd=0")
        self._reposition_stats()

        fit = _fit_double_gauss_hist(centers, counts, binw)
        if fit is None:
            self.fit_curve.setData([], [])
            self.fit_status.setText("Double-Gauss: fit not stable (need more stats)")
            return

        self.fit_curve.setData(centers, np.asarray(fit["yfit"], dtype=np.float64))
        self.fit_status.setText(
            "Double-Gauss: "
            f"sigma_w={fit['sigma_weighted']:.3f} mm | "
            f"narrow={fit['sigma1']:.3f} mm ({fit['w1'] * 100.0:.1f}%) | "
            f"wide={fit['sigma2']:.3f} mm ({fit['w2'] * 100.0:.1f}%)"
        )

    def save_plots(self, output_dir: str, active_tdcs=None) -> list[str]:
        if self._last_snap is None:
            return []
        os.makedirs(output_dir, exist_ok=True)
        self._redraw()
        QtWidgets.QApplication.processEvents()
        suffix = f"chamber_{int(self.chamber_id)}" if self.chamber_id is not None else "all_chambers"
        path = os.path.join(output_dir, f"fit_residual_overall_{suffix}.png")
        plot_item = getattr(self.plot, "plotItem", self.plot)
        return [path] if _export_plot_item_png(plot_item, path) else []
