import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest
from unittest.mock import Mock, patch
from PyQt5 import QtWidgets

from external_trigger import DEFAULT_CONFIG, DEFAULT_EDITOR_CONFIG, SIGNATURE
from external_trigger_widget import ExternalTriggerWidget
from MiniDAQ_reg import MiniDAQ_reg
from pop_miniDAQ_setup import pop_miniDAQ_setup


class ExternalTriggerWidgetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def setUp(self):
        confirmation = patch.object(ExternalTriggerWidget, '_confirm_polarity_change', return_value=True)
        confirmation.start()
        self.addCleanup(confirmation.stop)

    def test_roundtrip_expression_polarity_and_disabled_terms(self):
        widget = ExternalTriggerWidget(DEFAULT_CONFIG, lambda: None, lambda: None)
        self.assertEqual(widget.config(), DEFAULT_CONFIG)
        for enable in widget.enables:
            enable.setChecked(True)
        widget.expression.setText("(A & ~B) | (C & D)")
        widget.hex_mode.setChecked(False)
        self.assertEqual(widget.config(), 0xF2221F)
        widget.polarities[3].setCurrentIndex(1)
        widget.enables[1].setChecked(False)
        self.assertEqual(widget.config(), 0xFAAA9D)
        widget.set_config(0x88880F)
        self.assertTrue(widget.hex_mode.isChecked())
        self.assertEqual(widget.config(), 0x88880F)
        widget.close()

    def test_invalid_expression_does_not_silently_apply(self):
        widget = ExternalTriggerWidget(DEFAULT_CONFIG, lambda: None, lambda: None)
        widget.hex_mode.setChecked(False)
        widget.expression.setText("A ^ B")
        with self.assertRaises(ValueError):
            widget.config()
        self.assertIn("Use only", widget.preview.text())
        widget.close()

    def test_popup_contains_only_board_controls_and_preserves_acquisition_drafts(self):
        from acquisition_settings import BOARD_SETTINGS
        registers = MiniDAQ_reg()
        registers.set_named_value("external_trigger_config", 0xEEEE0F)
        registers.set_named_value("window_cycles", 31)
        with patch("pop_miniDAQ_setup.fpga_readback", return_value="0"*160), \
             patch("pop_miniDAQ_setup.fpga_config") as send:
            dialog = pop_miniDAQ_setup(object(), registers)
            self.assertEqual(set(dialog.board_controls), BOARD_SETTINGS)
            self.assertFalse(dialog.findChildren(ExternalTriggerWidget))
            self.assertEqual(next(r[3] for r in registers.register_table if r[1] == "external_trigger_config"), 0xEEEE0F)
            self.assertEqual(next(r[3] for r in registers.register_table if r[1] == "window_cycles"), 31)
            send.assert_not_called()
            dialog.close()


class TriggerPolarityConfirmationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_cancel_reverts_each_channel_without_applying_or_saving(self):
        apply = Mock()
        saved = Mock()
        widget = ExternalTriggerWidget(DEFAULT_EDITOR_CONFIG, apply, lambda: None)
        widget.settings_changed.connect(saved)
        with patch('external_trigger_widget.QtWidgets.QMessageBox.warning',
                   return_value=QtWidgets.QMessageBox.Cancel) as warning:
            for polarity in widget.polarities:
                polarity.setCurrentIndex(0)
                self.assertEqual(polarity.currentIndex(), 1)
                self.assertEqual(widget.config(), DEFAULT_EDITOR_CONFIG)
        self.assertEqual(warning.call_count, 4)
        self.assertEqual(warning.call_args.args[2],
                         'Adjust the threshold and/or channel biasing on the board before changing this')
        self.assertEqual(warning.call_args.args[4], QtWidgets.QMessageBox.Cancel)
        apply.assert_not_called()
        saved.assert_not_called()
        widget.close()

    def test_confirm_applies_once_in_both_directions(self):
        apply = Mock()
        saved = Mock()
        widget = ExternalTriggerWidget(DEFAULT_EDITOR_CONFIG, apply, lambda: None)
        widget.settings_changed.connect(saved)
        with patch('external_trigger_widget.QtWidgets.QMessageBox.warning',
                   return_value=QtWidgets.QMessageBox.Ok) as warning:
            widget.polarities[0].setCurrentIndex(0)
            self.assertEqual(widget.config(), 0xAAAAE1)
            widget.polarities[0].setCurrentIndex(1)
            self.assertEqual(widget.config(), DEFAULT_EDITOR_CONFIG)
        self.assertEqual(warning.call_count, 2)
        self.assertEqual(apply.call_count, 2)
        self.assertEqual(saved.call_count, 2)
        widget.close()

    def test_restore_and_hardware_readback_skip_confirmation_and_track_previous_value(self):
        apply = Mock()
        widget = ExternalTriggerWidget(DEFAULT_EDITOR_CONFIG, apply, lambda: None)
        state = widget.settings_state()
        state['active_low'] = 0
        with patch('external_trigger_widget.QtWidgets.QMessageBox.warning') as warning:
            widget.restore_settings(state)
            widget.set_config(DEFAULT_CONFIG)
            warning.assert_not_called()
            apply.assert_not_called()
            warning.return_value = QtWidgets.QMessageBox.Cancel
            widget.polarities[1].setCurrentIndex(1)
            warning.assert_called_once()
            self.assertEqual(widget.polarities[1].currentIndex(), 0)
        self.assertEqual(widget.config(), DEFAULT_CONFIG)
        widget.close()



if __name__ == "__main__":
    unittest.main()
