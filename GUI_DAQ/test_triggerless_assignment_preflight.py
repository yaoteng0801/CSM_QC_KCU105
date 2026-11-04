import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from MainWindow import Ui_MainWindow


def geometry(chamber_id, *tdc_ids):
    active = [0] * 40
    for tdc_id in tdc_ids:
        active[int(tdc_id)] = 1
    return SimpleNamespace(chamber_id=chamber_id, isActiveTDC=active)


class AssignmentPreflightTest(unittest.TestCase):
    def test_reports_both_mismatch_directions(self):
        ui = Ui_MainWindow()
        ui.geos = [geometry(0, 0), geometry(1, 1, 2)]
        ui.mezz_tab_inst = SimpleNamespace(
            selected_mezz_indices=lambda: [(0, 0), (0, 1), (0, 4)]
        )

        unassigned, assigned_disabled, enabled_mezz, chamber1_mask = (
            ui._tdc_assignment_mismatch()
        )

        self.assertEqual(unassigned, [4])
        self.assertEqual(assigned_disabled, [2])
        self.assertEqual(enabled_mezz[4], (0, 4))
        self.assertEqual(chamber1_mask, (1 << 1) | (1 << 2))

    def test_cancel_is_default_and_blocks_start(self):
        for mode in (0, 1):
            with self.subTest(acquisition_mode=mode):
                ui = Ui_MainWindow()
                ui.centralWidget = None
                ui.tab_lpgbt_inst = SimpleNamespace(current_acquisition_mode=lambda mode=mode: mode)
                ui._tdc_assignment_mismatch = lambda: (
                    [4], [], {4: (0, 4)}, 0
                )

                start_button = object()
                cancel_button = object()
                with patch("MainWindow.QtWidgets.QMessageBox") as message_box:
                    dialog = message_box.return_value
                    dialog.addButton.side_effect = [start_button, cancel_button]
                    dialog.clickedButton.return_value = cancel_button

                    self.assertFalse(ui._confirm_tdc_assignments())
                    dialog.setDefaultButton.assert_called_once_with(cancel_button)
                    dialog.setEscapeButton.assert_called_once_with(cancel_button)
                    self.assertIn("CSM0 Mezz4 (TDC 4)", message_box.call_args.args[2])
                    self.assertIn("Assign every enabled mezzanine", message_box.call_args.args[2])

    def test_start_anyway_allows_start(self):
        for mode in (0, 1):
            with self.subTest(acquisition_mode=mode):
                ui = Ui_MainWindow()
                ui.centralWidget = None
                ui.tab_lpgbt_inst = SimpleNamespace(current_acquisition_mode=lambda mode=mode: mode)
                ui._tdc_assignment_mismatch = lambda: (
                    [4], [], {4: (0, 4)}, 0
                )

                start_button = object()
                cancel_button = object()
                with patch("MainWindow.QtWidgets.QMessageBox") as message_box:
                    dialog = message_box.return_value
                    dialog.addButton.side_effect = [start_button, cancel_button]
                    dialog.clickedButton.return_value = start_button
                    self.assertTrue(ui._confirm_tdc_assignments())

    def test_matching_sets_skip_dialog(self):
        for mode in (0, 1):
            with self.subTest(acquisition_mode=mode):
                ui = Ui_MainWindow()
                ui.tab_lpgbt_inst = SimpleNamespace(current_acquisition_mode=lambda mode=mode: mode)
                ui._tdc_assignment_mismatch = lambda: ([], [], {}, 0)
                with patch("MainWindow.QtWidgets.QMessageBox") as message_box:
                    self.assertTrue(ui._confirm_tdc_assignments())
                    message_box.assert_not_called()

    def test_triggered_manual_start_can_be_cancelled_or_confirmed(self):
        ui = Ui_MainWindow()
        ui.centralWidget = None
        ui.tab_lpgbt_inst = SimpleNamespace(current_acquisition_mode=lambda: 0)
        ui.geos = [geometry(0, 0), geometry(1, 2)]
        ui.mezz_tab_inst = SimpleNamespace(selected_mezz_indices=lambda: [(0, 0), (0, 4)])
        ui._start_daq_with_chamber_map = Mock()
        for proceed in (False, True):
            with self.subTest(proceed=proceed), patch("MainWindow.QtWidgets.QMessageBox") as message_box:
                start, cancel = object(), object()
                dialog = message_box.return_value
                dialog.addButton.side_effect = [start, cancel]
                dialog.clickedButton.return_value = start if proceed else cancel
                ui._manual_daq_start()
                text = message_box.call_args.args[2]
                self.assertIn("CSM0 Mezz4 (TDC 4)", text)
                self.assertIn("CSM0 Mezz2 (TDC 2) - Geometry 1", text)
                self.assertNotIn("excluded from triggerless", text)
                if proceed:
                    ui._start_daq_with_chamber_map.assert_called_once_with()
                else:
                    ui._start_daq_with_chamber_map.assert_not_called()



if __name__ == "__main__":
    unittest.main()
