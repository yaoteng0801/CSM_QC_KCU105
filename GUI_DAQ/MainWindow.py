# MainWindow.py
from PyQt5 import QtCore, QtWidgets
from bounded_log_browser import BoundedLogBrowser
import inspect
import os
import re

from tab_capture import tab_capture
from tab_geometry import tab_geometry
from tab_lpgbt import tab_lpgbt
from tab_eom import tab_eom
from tab_elink import tab_elink
from tab_monitor import tab_monitor
from tab_mezz import tab_mezz
from tab_qc import tab_qc
from ethernet_control_protocol import EthernetControlClient
from triggerless_filters import build_geometry_image
from tube_filter_widget import GeometryUploadDialog
from types import SimpleNamespace

# NEW: import the concrete spectra tabs
from tab_spectra import (
    tab_adc_spectra,
    tab_tdc_spectra,
    tab_adc_channels,
    tab_tdc_channels,
    tab_adc_channel_hits,
    tab_fit_residual_spectra,
    tab_fit_residual_overall,
)


class Ui_MainWindow:
    def __init__(self):
        pass

    def _add_scrollable_tab(self, title):
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        # Keep this tab's content size out of the top-level QTabWidget's size
        # hint.  Oversized content is handled by this tab's own scrollbars.
        scroll_area.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustIgnored)
        scroll_area.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding,
        )
        scroll_area.setMinimumSize(0, 0)

        content = QtWidgets.QWidget()
        scroll_area.setWidget(content)
        self.tabWidget.addTab(scroll_area, title)
        self._tab_scroll_areas.append(scroll_area)
        return content

    @staticmethod
    def _finalize_scrollable_tab(content):
        layout = content.layout()
        if layout is not None:
            # Preserve the tab's usable minimum content size.  Its surrounding
            # scroll area, rather than the main window, absorbs any overflow.
            layout.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)

    def setupUi(self, MainWindow, backend=None, geo=None, rt=None):
        """
        geo is expected to be a list/tuple of Geometry objects: [geo0, geo1, ...]
        Each Geometry MUST have geo.chamber_id set (>=0).
        """
        MainWindow.setWindowTitle("GUI_DAQ")
        self.backend = backend
        self._last_completed_plot_dat_path = ""
        self._last_completed_plot_dir = ""

        if geo is None:
            geos = []
        elif isinstance(geo, (list, tuple)):
            geos = list(geo)
        else:
            # allow single Geometry
            geos = [geo]

        if not geos:
            raise ValueError("MainWindow.setupUi expects geo=[Geometry,...] (non-empty)")

        # validate chamber_id and build a stable ordering (by chamber_id)
        for g in geos:
            if g is None:
                raise ValueError("MainWindow.setupUi got geo list containing None")
            cid = int(getattr(g, "chamber_id", -1))
            if cid < 0:
                raise ValueError("Each Geometry must have geo.chamber_id >= 0")

        geos.sort(key=lambda g: int(getattr(g, "chamber_id", -1)))
        self.geos = geos  # keep reference
        self.rt = rt

        self.centralWidget = QtWidgets.QWidget()
        MainWindow.setCentralWidget(self.centralWidget)
        mainLayout = QtWidgets.QVBoxLayout(self.centralWidget)

        self.tabWidget = QtWidgets.QTabWidget()
        self.tabWidget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding,
        )
        self._tab_scroll_areas = []
        mainLayout.addWidget(self.tabWidget)

        # ---------------- Ethernet capture tab ----------------
        capture_tab = self._add_scrollable_tab("Ethernet Capture")
        status_tab = self._add_scrollable_tab("Diagnostics")
        self.tab_capture_inst = tab_capture(
            capture_tab,
            backend=self.backend,
            status_parent_widget=status_tab,
            initial_rt_file=str(getattr(self.rt, "txt_file", "") or ""),
            rt_apply_callback=getattr(MainWindow, "apply_rt_file", None),
        )
        self._finalize_scrollable_tab(capture_tab)
        self._finalize_scrollable_tab(status_tab)
        self.eth = EthernetControlClient(self.tab_capture_inst.current_device)

        # ---------------- MiniDAQ configuration tabs ----------------
        lpgbt_tab = self._add_scrollable_tab("LpGBT Config")
        self.tab_lpgbt_inst = tab_lpgbt(
            lpgbt_tab,
            self.eth,
            ethernet_device_callback=self.tab_capture_inst.current_device,
        )
        self.tab_capture_inst.combo_iface.currentTextChanged.connect(
            self.tab_lpgbt_inst.set_ethernet_device
        )
        self.tab_lpgbt_inst.set_ethernet_device(
            self.tab_capture_inst.current_device()
        )
        self._finalize_scrollable_tab(lpgbt_tab)
        self.tab_capture_inst.bind_minidaq_registers(self.tab_lpgbt_inst.miniDAQ_reg)
        self.tab_lpgbt_inst._manual_daq_start_callback = self._manual_daq_start
        if hasattr(self.tab_capture_inst, "set_daq_run_control"):
            self.tab_capture_inst.set_daq_run_control(
                preflight_callback=self._confirm_tdc_assignments,
                start_callback=self._start_daq_with_chamber_map,
                stop_callback=self.tab_lpgbt_inst.DAQ_stop,
                set_modes_callback=self.tab_lpgbt_inst.set_run_modes,
                set_mode_callback=self.tab_lpgbt_inst.set_acquisition_mode,
                mode_callback=self.tab_lpgbt_inst.inquire_acquisition_mode,
                cached_mode_callback=self.tab_lpgbt_inst.current_acquisition_mode,
                noise_test_mode_callback=self.tab_lpgbt_inst.current_noise_test_mode,
                set_triggerless_settings_callback=(
                    self.tab_lpgbt_inst.set_triggerless_event_settings
                ),
                triggerless_settings_callback=(
                    self.tab_lpgbt_inst.current_triggerless_event_settings
                ),
                diagnostic_snapshot_callback=self.tab_lpgbt_inst.read_diagnostic_snapshot,
                configure_external_trigger_callback=self.tab_lpgbt_inst.configure_external_trigger,
                read_external_trigger_callback=self.tab_lpgbt_inst.read_external_trigger_settings,
                set_sma_output_callback=self.tab_lpgbt_inst.set_sma_trigger_output,
                set_acquisition_register_callback=self.tab_lpgbt_inst.set_acquisition_register,
                read_acquisition_registers_callback=self.tab_lpgbt_inst.read_acquisition_registers,
            )

        mezz_tab = self._add_scrollable_tab("Mezz Config")
        self.mezz_tab_inst = tab_mezz(mezz_tab, self.eth)
        self._finalize_scrollable_tab(mezz_tab)

        elink_tab = self._add_scrollable_tab("eLink Phase")
        self.tab_elink_inst = tab_elink(elink_tab, self.eth)
        self._finalize_scrollable_tab(elink_tab)
        if hasattr(self.tab_elink_inst, "set_mezz_tab"):
            self.tab_elink_inst.set_mezz_tab(self.mezz_tab_inst)
        if hasattr(self.tab_capture_inst, "set_filename_prefix_control"):
            self.tab_capture_inst.set_filename_prefix_control(
                asd_main_thr_callback=getattr(self.mezz_tab_inst, "asd_main_thr_value", None),
            )
        if hasattr(self.tab_capture_inst, "set_noise_scan_control"):
            self.tab_capture_inst.set_noise_scan_control(
                selected_mezz_callback=getattr(self.mezz_tab_inst, "selected_mezz_indices", None),
                active_channels_callback=getattr(self.mezz_tab_inst, "selected_noise_scan_channels", None),
                disabled_channels_callback=getattr(self.mezz_tab_inst, "selected_disabled_channels", None),
                configure_threshold_callback=getattr(self.mezz_tab_inst, "configure_selected_asd_threshold", None),
                configure_hyst_callback=getattr(self.mezz_tab_inst, "configure_selected_asd_hyst", None),
                minidaq_setup_callback=getattr(self.tab_lpgbt_inst, "configure_noise_scan_minidaq", None),
            )

        # ---------------- Spectra tab (nested sub-tabs) ----------------
        spectra_tab = self._add_scrollable_tab("Spectra")

        spectra_layout = QtWidgets.QVBoxLayout(spectra_tab)
        self.spectraTabs = QtWidgets.QTabWidget()
        self.spectraTabs.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.MinimumExpanding,
        )
        spectra_layout.addWidget(self.spectraTabs)

        # ADC spectra (per TDC)
        adc_tab = QtWidgets.QWidget()
        self.spectraTabs.addTab(adc_tab, "ADC overall")
        self.tab_adc_spectra_inst = tab_adc_spectra(adc_tab, backend=self.backend, n_tdcs=40)

        # TDC spectra (event-T0 drift time in triggerless mode)
        tdc_tab = QtWidgets.QWidget()
        self.spectraTabs.addTab(tdc_tab, "TDC overall")
        self.tab_tdc_spectra_inst = tab_tdc_spectra(tdc_tab, backend=self.backend, n_tdcs=40)

        # ADC channel spectra (single TDC, channels paged 2x3)
        adc_ch_tab = QtWidgets.QWidget()
        self.spectraTabs.addTab(adc_ch_tab, "ADC (per CH)")
        self.tab_adc_channels_inst = tab_adc_channels(
            adc_ch_tab, backend=self.backend, n_tdcs=40, n_channels=24
        )

        # TDC channel spectra use the same mode-dependent timing reference.
        tdc_ch_tab = QtWidgets.QWidget()
        self.spectraTabs.addTab(tdc_ch_tab, "TDC (per CH)")
        self.tab_tdc_channels_inst = tab_tdc_channels(
            tdc_ch_tab, backend=self.backend, n_tdcs=40, n_channels=24
        )

        hits_tab = QtWidgets.QWidget()
        self.spectraTabs.addTab(hits_tab, "CH Hits")
        self.tab_ch_hits_inst = tab_adc_channel_hits(
            hits_tab,
            backend=self.backend,
            n_tdcs=40,
            active_channels_callback=getattr(
                self.mezz_tab_inst,
                "selected_noise_scan_channels",
                None,
            ),
        )

        self.tab_fit_residual_overall_inst = []
        self.tab_fit_residuals_inst = []
        for g in self.geos:
            cid = int(getattr(g, "chamber_id", -1))
            is_active = getattr(g, "isActiveTDC", None)
            active_tdcs = []
            if is_active is not None:
                try:
                    active_tdcs = [t for t, flag in enumerate(is_active) if int(flag) == 1]
                except Exception:
                    active_tdcs = []

            residual_overall_tab = QtWidgets.QWidget()
            self.spectraTabs.addTab(residual_overall_tab, f"Residual overall C{cid}")
            self.tab_fit_residual_overall_inst.append(
                tab_fit_residual_overall(
                    residual_overall_tab,
                    backend=self.backend,
                    chamber_id=cid,
                )
            )

            residual_tab = QtWidgets.QWidget()
            self.spectraTabs.addTab(residual_tab, f"Residual C{cid}")
            self.tab_fit_residuals_inst.append(
                tab_fit_residual_spectra(
                    residual_tab,
                    backend=self.backend,
                    n_tdcs=40,
                    chamber_id=cid,
                    default_tdcs=active_tdcs,
                )
            )
        self._finalize_scrollable_tab(spectra_tab)

        # ---------------- Geometry tabs: dynamic from geo list ----------------
        self.tab_geometries = []  # list of tab_geometry instances
        self.tab_capture_inst._geometry_rt_managed = True
        from rt_calibration_widget import RTCalibrationWidget

        geometry_pages = []
        for g in self.geos:
            cid = int(g.chamber_id)
            tabw = self._add_scrollable_tab(f"Geometry {cid}")
            geometry_pages.append(tabw)

            tab_inst = tab_geometry(
                tabw,
                g,
                default_filename="geometry.txt",
                backend=self.backend,
                chamber_id=cid,
                n_tdcs=40,
                rt=self.rt
            )
            self.backend.set_chamber_rt(cid, self.rt)
            def apply_chamber_rt(rt, tab=tab_inst, chamber_id=cid):
                self.backend.set_chamber_rt(chamber_id, rt)
                tab.set_rt(rt)
            tab_inst.rt_calibration = RTCalibrationWidget(
                cid, self.tab_capture_inst.settings, apply_chamber_rt, self.rt, tabw)
            tab_inst.settings_layout.insertWidget(0, tab_inst.rt_calibration)
            self.tab_geometries.append(tab_inst)
            self._finalize_scrollable_tab(tabw)

            # When capture restarts, clear event caches (so colors don't mismatch)
            if self.backend is not None and hasattr(self.backend, "capture_started"):
                self.backend.capture_started.connect(self.backend.clear_event_cache)

        if hasattr(self.mezz_tab_inst, "set_geometry_sync_callback"):
            self.mezz_tab_inst.set_geometry_sync_callback(self._sync_geometry_from_mezz)
        self._sync_spectra_tdcs_from_mezz()

        # One monitor schedule and CSV for mezzanine and CSM selections.
        monitor_tab = self._add_scrollable_tab("Monitoring")
        self.tab_monitor_inst = tab_monitor(monitor_tab, self.eth)
        self.tab_sca_inst = self.tab_monitor_inst.mezz
        self.tab_csm_inst = self.tab_monitor_inst.csm
        self._finalize_scrollable_tab(monitor_tab)

        qc_tab = self._add_scrollable_tab("CSM QC")
        self.tab_qc_inst = tab_qc(
            qc_tab,
            SimpleNamespace(
                eth=self.eth,
                lpgbt=self.tab_lpgbt_inst,
                mezz=self.mezz_tab_inst,
                monitor=self.tab_monitor_inst,
                capture=self.tab_capture_inst,
                adc=self.tab_adc_spectra_inst,
                backend=self.backend,
                tdc_mismatch=self._tdc_assignment_mismatch,
                show_adc_plots=self.show_adc_plots,
            ),
            settings=self.tab_capture_inst.settings,
        )
        self._finalize_scrollable_tab(qc_tab)

        # Keep the Eye Monitor at the far right as the final top-level tab.
        eom_tab = self._add_scrollable_tab("Eye Monitor")
        self.tab_eom_inst = tab_eom(eom_tab, self.eth)
        self._finalize_scrollable_tab(eom_tab)

        # Construction follows controller dependencies; display follows the
        # operator's workflow, retaining Diagnostics after the requested tabs.
        pages = [lpgbt_tab, mezz_tab, capture_tab, monitor_tab, spectra_tab, qc_tab,
                 *geometry_pages, elink_tab, eom_tab, status_tab]
        for position, page in enumerate(pages):
            scroll = next(area for area in self._tab_scroll_areas if area.widget() is page)
            self.tabWidget.tabBar().moveTab(self.tabWidget.indexOf(scroll), position)
        self.tabWidget.setCurrentIndex(0)

        if hasattr(self.tab_capture_inst, "set_run_plot_saving_control"):
            self.tab_capture_inst.set_run_plot_saving_control(
                plot_labels_callback=self.plot_export_labels,
                selection_callback=self.set_plot_selections,
                save_previous_callback=lambda labels: self.save_run_plots(
                    selected_labels=labels,
                    manual=True,
                ),
                can_save_previous_callback=self.can_save_previous_run_plots,
            )

        if self.backend is not None and hasattr(self.backend, "capture_started"):
            self.backend.capture_started.connect(self._clear_previous_run_plot_path)

        if self.backend is not None and hasattr(self.backend, "run_finished"):
            self.backend.run_finished.connect(self._remember_previous_run_plot_path)
            self.backend.run_finished.connect(self.save_run_plots)

        # ---------------- clear info button ----------------
        self.pushButton_clearinfo = QtWidgets.QPushButton()
        self.pushButton_clearinfo.setText("clear info")
        self.pushButton_clearinfo.clicked.connect(self.clear_info)
        mainLayout.addWidget(self.pushButton_clearinfo)

        label = QtWidgets.QLabel()
        label.setText("Output Log")
        label.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        mainLayout.addWidget(label)

        self.textBrowser = BoundedLogBrowser()
        self.textBrowser.setMinimumHeight(140)
        self.textBrowser.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.Preferred,
        )
        mainLayout.addWidget(self.textBrowser)

    def show_adc_plots(self):
        """Bring up Spectra > ADC overall; plots export correctly only once laid out."""
        spectra_page = self.spectraTabs.parentWidget()
        while spectra_page is not None:
            index = self.tabWidget.indexOf(spectra_page)
            if index >= 0:
                self.tabWidget.setCurrentIndex(index)
                break
            spectra_page = spectra_page.parentWidget()
        self.spectraTabs.setCurrentIndex(0)
        QtWidgets.QApplication.processEvents()

    def clear_info(self):
        self.textBrowser.clear()

    def _tdc_chamber_masks(self):
        """Return firmware masks from the GUI's authoritative geometries."""
        owners = {}
        for geo in list(getattr(self, "geos", []) or []):
            chamber_id = int(getattr(geo, "chamber_id", -1))
            if chamber_id not in (0, 1):
                raise ValueError(
                    f"Firmware supports only chamber IDs 0 and 1, got {chamber_id}"
                )
            active = getattr(geo, "isActiveTDC", None)
            if active is None:
                continue
            for tdc_id in range(min(40, len(active))):
                if int(active[tdc_id]) != 1:
                    continue
                if tdc_id in owners:
                    raise ValueError(
                        f"TDC {tdc_id} is assigned to chambers "
                        f"{owners[tdc_id]} and {chamber_id}"
                    )
                owners[tdc_id] = chamber_id

        enabled_mask = 0
        chamber1_mask = 0
        for tdc_id, chamber_id in owners.items():
            enabled_mask |= 1 << int(tdc_id)
            if int(chamber_id) == 1:
                chamber1_mask |= 1 << int(tdc_id)
        return enabled_mask, chamber1_mask

    def _tdc_assignment_mismatch(self):
        """Return enabled/unassigned and assigned/disabled TDC IDs."""
        enabled_mezz = {}
        selected_mezz = getattr(
            getattr(self, "mezz_tab_inst", None),
            "selected_mezz_indices",
            None,
        )
        if callable(selected_mezz):
            for which_csm, mezz in selected_mezz() or []:
                which_csm = int(which_csm)
                mezz = int(mezz)
                tdc_id = which_csm * 20 + mezz
                if 0 <= tdc_id < 40:
                    enabled_mezz[tdc_id] = (which_csm, mezz)

        geometry_mask, chamber1_mask = self._tdc_chamber_masks()
        geometry_tdcs = {
            tdc_id for tdc_id in range(40)
            if geometry_mask & (1 << tdc_id)
        }
        enabled_tdcs = set(enabled_mezz)
        return (
            sorted(enabled_tdcs - geometry_tdcs),
            sorted(geometry_tdcs - enabled_tdcs),
            enabled_mezz,
            chamber1_mask,
        )

    @staticmethod
    def _mezz_assignment_label(tdc_id, chamber_id=None):
        tdc_id = int(tdc_id)
        label = f"CSM{tdc_id // 20} Mezz{tdc_id % 20} (TDC {tdc_id})"
        if chamber_id is not None:
            label += f" - Geometry {int(chamber_id)}"
        return label

    def _confirm_tdc_assignments(self):
        """Warn before any run when selected mezz and Geometry sets differ."""
        acquisition_mode = int(self.tab_lpgbt_inst.current_acquisition_mode())

        unassigned, assigned_disabled, enabled_mezz, chamber1_mask = (
            self._tdc_assignment_mismatch()
        )
        if not unassigned and not assigned_disabled:
            return True

        lines = [
            "Enabled mezzanine TDCs do not match the TDCs assigned in Geometry 0/1.",
            "",
        ]
        if unassigned:
            lines.append("Enabled mezzanines not assigned to any Geometry:")
            lines.extend(
                f"  - {self._mezz_assignment_label(tdc_id)}"
                for tdc_id in unassigned
            )
            lines.extend((
                ("These TDCs will be excluded from triggerless acquisition."
                 if acquisition_mode == 1 else
                 "These TDCs have no Geometry assignment for event display."),
                "",
            ))
        if assigned_disabled:
            lines.append("TDCs assigned in Geometry but not enabled in Mezz Config:")
            lines.extend(
                "  - " + self._mezz_assignment_label(
                    tdc_id,
                    1 if chamber1_mask & (1 << tdc_id) else 0,
                )
                for tdc_id in assigned_disabled
            )
            lines.append("")
        lines.extend((
            "Assign every enabled mezzanine to Geometry 0 or Geometry 1, and remove",
            "disabled mezzanines from Geometry, before starting the DAQ.",
            "",
            "Do you want to start the DAQ anyway?",
        ))

        dialog = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Warning,
            "TDC assignment mismatch",
            "\n".join(lines),
            parent=getattr(self, "centralWidget", None),
        )
        start_button = dialog.addButton(
            "Start DAQ Anyway", QtWidgets.QMessageBox.AcceptRole
        )
        cancel_button = dialog.addButton(
            "Cancel", QtWidgets.QMessageBox.RejectRole
        )
        dialog.setDefaultButton(cancel_button)
        dialog.setEscapeButton(cancel_button)
        dialog.exec_()
        return dialog.clickedButton() is start_button

    def _start_daq_with_chamber_map(self):
        if int(self.tab_lpgbt_inst.current_acquisition_mode()) != 1:
            self.tab_lpgbt_inst.DAQ_start()
            return
        if self.tab_lpgbt_inst.current_noise_test_mode() == 0:
            image = build_geometry_image(self.geos)
            self.tab_lpgbt_inst.set_triggerless_event_settings(
                *self.tab_lpgbt_inst.current_triggerless_event_settings())
            GeometryUploadDialog(
                lambda progress: self.tab_lpgbt_inst.configure_triggerless_geometry(image, progress),
                getattr(self, "centralWidget", None),
            ).upload()
        else:
            # Raw/count noise streams bypass the tube filters and geometry LUT.
            self.tab_lpgbt_inst.configure_tdc_chamber_map(*self._tdc_chamber_masks())
        self.tab_lpgbt_inst.DAQ_start()

    def _manual_daq_start(self):
        if self._confirm_tdc_assignments():
            self._start_daq_with_chamber_map()

    def _sync_geometry_from_mezz(self, reason=""):
        if not hasattr(self, "mezz_tab_inst") or not hasattr(self.mezz_tab_inst, "geometry_sync_state"):
            return False
        monitor_changed = False
        if reason == "mezz scan completed":
            monitor_tab = getattr(self, "tab_sca_inst", None)
            select_scanned_mezz = getattr(monitor_tab, "select_scanned_mezz", None)
            if callable(select_scanned_mezz):
                select_scanned_mezz(self.mezz_tab_inst.selected_mezz_indices())
                monitor_changed = True

        spectra_changed = self._sync_spectra_tdcs_from_mezz()
        tabs = list(getattr(self, "tab_geometries", []) or [])
        if not tabs:
            return bool(monitor_changed or spectra_changed)

        # With multiple chambers, the Geometry tabs are the authoritative
        # TDC-to-chamber assignment.  Mezz programming/configuration describes
        # the physical TDCs and channel enables; it must not silently restore
        # the legacy CSM-number-to-chamber-number mapping and overwrite a
        # user's chamber assignment.  Keep automatic mezz-to-geometry mapping
        # only for the legacy single-geometry setup.
        if len(tabs) > 1:
            return bool(monitor_changed or spectra_changed)

        state = self.mezz_tab_inst.geometry_sync_state()
        changed = False

        entries = []
        for csm_entries in state.values():
            entries.extend(csm_entries)
        changed = tabs[0].sync_from_mezz_state(
            entries,
            csm_ids=sorted(state.keys()),
            reason=reason,
        ) or changed

        if changed and self.backend is not None and hasattr(self.backend, "set_geometries_from_list"):
            self.backend.set_geometries_from_list(self.geos)
        return bool(monitor_changed or changed or spectra_changed)

    def _spectra_tabs_filtered_by_mezz(self):
        return [
            getattr(self, "tab_adc_spectra_inst", None),
            getattr(self, "tab_tdc_spectra_inst", None),
            getattr(self, "tab_ch_hits_inst", None),
        ]

    def _sync_spectra_tdcs_from_mezz(self) -> bool:
        active_tdcs = self._active_mezz_tdc_ids_for_plot_save()
        changed = False
        for inst in self._spectra_tabs_filtered_by_mezz():
            setter = getattr(inst, "set_display_tdcs", None)
            if not callable(setter):
                continue
            try:
                changed = bool(setter(active_tdcs)) or changed
            except Exception as e:
                print(f"[WARN] Failed to update spectra TDC filter from mezz selection: {e}")
        return changed

    @staticmethod
    def _safe_folder_name(text: str, default: str = "tab") -> str:
        name = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(text or "").strip()).strip("._")
        return name or str(default)

    def _plot_export_targets(self):
        targets = [
            ("ADC overall", getattr(self, "tab_adc_spectra_inst", None)),
            ("TDC overall", getattr(self, "tab_tdc_spectra_inst", None)),
            ("ADC per CH", getattr(self, "tab_adc_channels_inst", None)),
            ("TDC per CH", getattr(self, "tab_tdc_channels_inst", None)),
            ("CH Hits", getattr(self, "tab_ch_hits_inst", None)),
        ]

        for inst in getattr(self, "tab_fit_residual_overall_inst", []) or []:
            cid = getattr(inst, "chamber_id", None)
            label = f"Residual overall C{cid}" if cid is not None else "Residual overall"
            targets.append((label, inst))

        for inst in getattr(self, "tab_fit_residuals_inst", []) or []:
            cid = getattr(inst, "chamber_id", None)
            label = f"Residual C{cid}" if cid is not None else "Residual"
            targets.append((label, inst))

        for inst in getattr(self, "tab_geometries", []) or []:
            cid = getattr(inst, "chamber_id", None)
            label = f"Geometry {cid}" if cid is not None else "Geometry"
            targets.append((label, inst))

        return [(label, inst) for label, inst in targets if inst is not None and hasattr(inst, "save_plots")]

    def plot_export_labels(self):
        return [label for label, _inst in self._plot_export_targets()]

    def set_plot_selections(self, live_labels, save_labels):
        live = set(str(label) for label in (live_labels or []) if str(label))
        save = set(str(label) for label in (save_labels or []) if str(label))
        for label, instance in self._plot_export_targets():
            setter = getattr(instance, "set_live_updates_enabled", None)
            if callable(setter):
                setter(str(label) in live)
        if self.backend is not None:
            setter = getattr(self.backend, "set_plot_selections", None)
            if callable(setter):
                setter(live, save)

    def _selected_run_plot_labels(self):
        capture_tab = getattr(self, "tab_capture_inst", None)
        labels = getattr(capture_tab, "run_plot_save_labels", None)
        if callable(labels):
            try:
                return set(str(label) for label in labels())
            except Exception:
                return set()
        return set()

    def can_save_previous_run_plots(self):
        if self.backend is None:
            return False
        if hasattr(self.backend, "is_running") and self.backend.is_running():
            return False
        return bool(self._last_completed_plot_dat_path)

    def _clear_previous_run_plot_path(self):
        self._last_completed_plot_dat_path = ""
        self._last_completed_plot_dir = ""

    def _remember_previous_run_plot_path(self):
        if self.backend is None or not hasattr(self.backend, "current_out_path"):
            return
        self._last_completed_plot_dat_path = str(self.backend.current_out_path() or "")
        self._last_completed_plot_dir = str(self.backend.current_artifact_dir() or "")

    def _active_mezz_tdc_ids_for_plot_save(self):
        mezz_tab = getattr(self, "mezz_tab_inst", None)
        selected_mezz = getattr(mezz_tab, "selected_mezz_indices", None)
        if not callable(selected_mezz):
            return None

        try:
            pairs = list(selected_mezz() or [])
        except Exception as e:
            print(f"[WARN] Failed to read active mezz list for plot saving: {e}")
            return None

        mezz_per_csm = int(getattr(mezz_tab, "mezz_per_CSM", 20) or 20)
        active = set()
        for which_csm, mezz in pairs:
            try:
                active.add(int(which_csm) * mezz_per_csm + int(mezz))
            except Exception:
                continue
        return sorted(active)

    @staticmethod
    def _target_accepts_active_tdcs(inst) -> bool:
        try:
            return "active_tdcs" in inspect.signature(inst.save_plots).parameters
        except Exception:
            return False

    def save_run_plots(self, selected_labels=None, manual=False):
        selected = set(str(label) for label in (
            selected_labels if selected_labels is not None else self._selected_run_plot_labels()
        ))
        if not selected:
            print("Plot saving skipped: no plot tabs are selected.")
            return False

        if self.backend is None or not hasattr(self.backend, "current_out_path"):
            return False

        if manual and hasattr(self.backend, "is_running") and self.backend.is_running():
            print("Plot saving skipped: a run is active.")
            return False

        dat_path = self._last_completed_plot_dat_path if manual else self.backend.current_out_path()
        if not dat_path:
            return False

        run_dir = (self._last_completed_plot_dir if manual else self.backend.current_artifact_dir())
        run_dir = run_dir or os.path.dirname(os.path.abspath(str(dat_path)))
        if not run_dir:
            return False

        plots_root = os.path.join(run_dir, "plots")
        active_tdcs = self._active_mezz_tdc_ids_for_plot_save()
        total = 0
        print(f"Saving plots to: {plots_root}")
        if active_tdcs is not None:
            print(f"Active mezz TDCs for plot saving: {active_tdcs}")
        for label, inst in self._plot_export_targets():
            if str(label) not in selected:
                continue
            tab_dir = os.path.join(plots_root, self._safe_folder_name(label))
            try:
                if active_tdcs is not None and self._target_accepts_active_tdcs(inst):
                    saved = list(inst.save_plots(tab_dir, active_tdcs=active_tdcs) or [])
                else:
                    saved = list(inst.save_plots(tab_dir) or [])
            except Exception as e:
                print(f"[WARN] Failed to save plots for tab '{label}': {repr(e)}")
                continue
            total += len(saved)
            if saved:
                print(f"Saved {len(saved)} plot(s) for tab '{label}' to {tab_dir}")
        print(f"Plot save complete: {total} image(s)")
        return total > 0
