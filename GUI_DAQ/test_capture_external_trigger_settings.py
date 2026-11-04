import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import tempfile
import unittest
from unittest.mock import Mock, patch
from PyQt5 import QtWidgets

from external_trigger import DEFAULT_CONFIG, DEFAULT_EDITOR_CONFIG, SIGNATURE
from external_trigger_widget import ExternalTriggerWidget
from MiniDAQ_reg import MiniDAQ_reg
from tab_capture import tab_capture, RUN_PROFILE_TRIGGERED_EXTERNAL, RUN_PROFILE_TRIGGERLESS
from tab_lpgbt import tab_lpgbt


class CaptureExternalTriggerSettingsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def setUp(self):
        confirmation = patch.object(ExternalTriggerWidget, '_confirm_polarity_change', return_value=True)
        confirmation.start()
        self.addCleanup(confirmation.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.settings_patch = patch("tab_capture.SETTINGS_FILE", os.path.join(self.temp.name, "settings.ini"))
        self.settings_patch.start()
        self.addCleanup(self.settings_patch.stop)
        self.devices_patch = patch("tab_capture.pcapy.findalldevs", return_value=[])
        self.devices_patch.start()
        self.addCleanup(self.devices_patch.stop)
        self.parent = QtWidgets.QWidget()
        self.capture = tab_capture(self.parent)
        self.addCleanup(self.parent.close)
        self.controller = object.__new__(tab_lpgbt)
        self.controller.eth = object()
        self.registers = self.controller.miniDAQ_reg = MiniDAQ_reg()
        self.state = {"config": DEFAULT_CONFIG, "mask": 15, "running": False, "deadtime": 10}

        def read(address, selector=0):
            if address == 1:
                return (int(self.state["running"]) << 25) | (self.state["deadtime"] << 32)
            if address == 71:
                return (SIGNATURE << 32) | self.state["config"]
            if address == 72:
                return self.state["mask"]
            raise AssertionError(address)

        def write(_eth, address, data):
            value = int.from_bytes(bytes(data), "big")
            if address == 71:
                self.state["config"] = value
            elif address == 72:
                self.state["mask"] = value & 15
            elif address == 19:
                self.state["deadtime"] = value
            else:
                raise AssertionError(address)

        self.controller._read_fpga_value = read
        self.write_patch = patch("tab_lpgbt.fpga_config", side_effect=write)
        self.send = self.write_patch.start()
        self.addCleanup(self.write_patch.stop)
        self.capture.bind_minidaq_registers(self.registers)
        self.capture.set_daq_run_control(
            set_modes_callback=lambda mode, noise, **_kw: (mode, noise),
            configure_external_trigger_callback=self.controller.configure_external_trigger,
            read_external_trigger_callback=self.controller.read_external_trigger_settings,
            set_sma_output_callback=self.controller.set_sma_trigger_output)

    def test_mode_replaces_panel_and_preserves_staged_values(self):
        capture = self.capture
        self.assertEqual(capture.selected_run_profile(), RUN_PROFILE_TRIGGERED_EXTERNAL)
        self.assertIs(capture.mode_settings_stack.currentWidget(), capture.trigger_settings_group)
        capture.external_triggers.hex_mode.setChecked(False)
        capture.external_triggers.expression.setText("~A")
        self.assertEqual(self.state["config"], 0x5555F1)
        self.send.reset_mock()
        capture.spin_triggerless_window_cycles.setValue(41)
        capture.combo_acquisition_mode.setCurrentIndex(
            capture.combo_acquisition_mode.findData(RUN_PROFILE_TRIGGERLESS))
        self.assertIs(capture.mode_settings_stack.currentWidget(), capture.triggerless_settings_group)
        capture.combo_acquisition_mode.setCurrentIndex(
            capture.combo_acquisition_mode.findData(RUN_PROFILE_TRIGGERED_EXTERNAL))
        self.assertIs(capture.mode_settings_stack.currentWidget(), capture.trigger_settings_group)
        self.assertEqual(capture.external_triggers.expression.text(), "~A")
        self.assertEqual(capture.spin_triggerless_window_cycles.value(), 41)
        self.send.assert_not_called()

    def test_missing_ini_trigger_settings_default_to_only_a_and_all_active_low(self):
        self.assertFalse(self.capture.settings.contains('trigger/external_editor'))
        for editor in self.capture.external_editors:
            self.assertEqual(editor.config(), DEFAULT_EDITOR_CONFIG)
            self.assertEqual([box.isChecked() for box in editor.enables], [True, False, False, False])
            self.assertEqual([polarity.currentIndex() for polarity in editor.polarities], [1, 1, 1, 1])
        self.send.assert_not_called()

    def test_existing_ini_polarities_are_preserved(self):
        import json
        state = {'enabled': 3, 'active_low': 1, 'expression': 'A&B',
                 'hex_mode': False, 'lut': '0x8888'}
        self.capture.settings.setValue('trigger/external_editor', json.dumps(state))
        self.capture.settings.sync()
        reopened = self.reopen_capture()
        for editor in reopened.external_editors:
            self.assertEqual(editor.settings_state(), state)
        self.send.assert_not_called()

    def test_apply_read_and_shared_register_updates(self):
        capture = self.capture
        capture.external_triggers.hex_mode.setChecked(False)
        capture.external_triggers.expression.setText("~A")
        capture.spin_trigger_deadtime.setValue(65535)
        with patch("tab_capture.QtWidgets.QMessageBox.warning") as warning:
            capture._apply_external_triggers()
            warning.assert_not_called()
        self.assertEqual(self.state["config"], 0x5555F1)
        self.assertEqual(self.state["deadtime"], 65535)
        self.assertFalse(capture.external_triggers.hex_mode.isChecked())
        self.assertEqual(capture.external_triggers.expression.text(), "~A")
        # A shared-register update propagates to every Capture view.
        self.registers.set_named_value("external_trigger_config", 0xEEEE0F)
        self.assertEqual(capture.external_triggers.config(), 0xEEEE0F)
        self.state.update(config=DEFAULT_CONFIG, mask=5, deadtime=32768)
        capture._read_external_triggers()
        self.assertEqual(capture.external_triggers.config(), DEFAULT_CONFIG)
        self.assertEqual(capture.spin_trigger_deadtime.value(), 32768)
        self.assertEqual([w.isChecked() for w in capture.sma_output_checks],
                         [True, False, True, False])

    def test_run_locks_logic_but_sma_gates_remain_independent(self):
        capture = self.capture
        self.state["running"] = True
        self.registers.set_named_value("run_enable", 1)
        self.assertFalse(capture.external_triggers.isEnabled())
        self.assertFalse(capture.spin_trigger_deadtime.isEnabled())
        self.assertTrue(all(w.isEnabled() for w in capture.sma_output_checks))
        capture.sma_output_checks[2].setChecked(False)
        self.assertEqual(self.state["mask"], 0b1011)
        self.assertEqual(self.state["config"], DEFAULT_CONFIG)
        with patch("tab_capture.QtWidgets.QMessageBox.warning") as warning:
            capture._apply_external_triggers()
            warning.assert_called_once()
        self.state["running"] = False
        self.registers.set_named_value("run_enable", 0)
        self.assertTrue(capture.external_triggers.isEnabled())

    def test_rejected_mode_switch_restores_previous_panel(self):
        capture = self.capture
        capture._daq_set_modes_callback = Mock(side_effect=RuntimeError("mode rejected"))
        capture.combo_acquisition_mode.setCurrentIndex(
            capture.combo_acquisition_mode.findData(RUN_PROFILE_TRIGGERLESS))
        self.assertEqual(capture.selected_run_profile(), RUN_PROFILE_TRIGGERED_EXTERNAL)
        self.assertIs(capture.mode_settings_stack.currentWidget(), capture.trigger_settings_group)

    def test_hardware_stop_unlocks_after_run_flag_is_cleared(self):
        capture = self.capture

        def set_running(running):
            self.state["running"] = running
            self.registers.set_named_value("run_enable", int(running))

        capture._daq_start_callback = lambda: set_running(True)
        capture._daq_stop_callback = lambda: set_running(False)
        self.assertTrue(capture._start_daq_hardware())
        self.assertFalse(capture.external_triggers.isEnabled())
        self.assertFalse(capture.spin_trigger_deadtime.isEnabled())
        self.assertTrue(capture._stop_daq_hardware())
        self.assertTrue(capture.external_triggers.isEnabled())

    def connect_acquisition_registers(self):
        from acquisition_settings import READBACK
        values = {r[1]: r[3] for r in self.registers.register_table}
        addresses = {r[0]: r[1] for r in self.registers.register_table}
        def read(page, selector=0):
            value = int(self.state["running"]) << 25 if page == 1 else 0
            for name, (regpage, shift, width) in READBACK.items():
                if regpage == page:
                    value |= (values[name] & ((1 << width)-1)) << shift
            return value
        def write(_eth, address, data):
            values[addresses[address]] = int.from_bytes(bytes(data), "big")
        self.controller._read_fpga_value = read
        self.send.side_effect = write
        self.capture._set_acquisition_register_callback = self.controller.set_acquisition_register
        self.capture._read_acquisition_registers_callback = self.controller.read_acquisition_registers
        self.capture._update_mode_settings()
        return values

    def test_all_modes_have_applicable_shared_controls(self):
        from acquisition_settings import MODE_FIELDS
        capture = self.capture
        self.assertEqual(set(capture.mode_pages), {0, 1, 2, 3, 4})
        for profile, fields in MODE_FIELDS.items():
            capture.combo_acquisition_mode.setCurrentIndex(capture.combo_acquisition_mode.findData(profile))
            self.assertIs(capture.mode_settings_stack.currentWidget(), capture.mode_pages[profile])
            expected = set(fields) - ({"trigger_deadtime"} if profile == 0 else set())
            self.assertEqual(set(capture.register_editors[profile].controls), expected)
        self.assertFalse(any(page.isAncestorOf(capture.sma_outputs_group)
                             for page in capture.mode_pages.values()))
        self.registers.set_named_value("sma_trigger_enable", 5)
        self.assertEqual([c.isChecked() for c in capture.sma_output_checks],
                         [True, False, True, False])

    def test_scalar_commit_verifies_and_updates_every_view(self):
        values = self.connect_acquisition_registers()
        capture = self.capture
        external = capture.register_editors[0].controls["match_window"]
        internal = capture.register_editors[4].controls["match_window"]
        external.setValue(87)
        external.editingFinished.emit()
        self.assertEqual(values["match_window"], 87)
        self.assertEqual(internal.value(), 87)
        # A rejected write restores the last verified value in every view.
        self.send.side_effect = RuntimeError("offline")
        internal.setValue(99)
        with patch("tab_capture.QtWidgets.QMessageBox.warning") as warning:
            internal.editingFinished.emit()
            warning.assert_called_once()
        self.assertEqual(internal.value(), 87)
        self.assertEqual(external.value(), 87)

    def test_read_refreshes_shared_values_and_single_action_is_a_pulse(self):
        values = self.connect_acquisition_registers()
        values["match_window"] = 123
        self.capture._read_acquisition_registers(("match_window",))
        for profile in (0, 4):
            self.assertEqual(self.capture.register_editors[profile].controls["match_window"].value(), 123)
        self.state["running"] = True
        self.registers.set_named_value("run_enable", 1)
        self.send.reset_mock()
        self.capture.register_editors[4].controls["hit_single"].click()
        self.assertEqual([(call.args[1], int.from_bytes(bytes(call.args[2]), "big"))
                          for call in self.send.call_args_list], [(13, 1), (13, 0)])
        for editor in self.capture.register_editors.values():
            if "trigger_deadtime" in editor.controls:
                self.assertFalse(editor.controls["trigger_deadtime"].isEnabled())
        self.assertTrue(all(check.isEnabled() for check in self.capture.sma_output_checks))

    def test_hardware_running_rejects_stale_cached_scalar_write(self):
        self.connect_acquisition_registers()
        self.state["running"] = True
        self.send.reset_mock()
        with self.assertRaisesRegex(RuntimeError, "Stop the DAQ"):
            self.controller.set_acquisition_register("trigger_deadtime", 65535)
        self.send.assert_not_called()


    def test_failed_read_snapshot_preserves_all_cached_values(self):
        self.connect_acquisition_registers()
        self.controller._read_fpga_value = Mock(side_effect=[0, RuntimeError("offline")])
        before = {r[1]: r[3] for r in self.registers.register_table}
        with self.assertRaisesRegex(RuntimeError, "offline"):
            self.controller.read_acquisition_registers(("trigger_deadtime", "match_window"))
        self.assertEqual({r[1]: r[3] for r in self.registers.register_table}, before)

    def test_mismatched_write_is_not_reported_as_applied(self):
        self.connect_acquisition_registers()
        self.send.side_effect = None  # Write accepted by transport, ignored by mock hardware.
        with self.assertRaisesRegex(RuntimeError, "readback mismatch"):
            self.controller.set_acquisition_register("match_window", 99)
        self.assertEqual(self.capture.register_editors[4].controls["match_window"].value(), 60)


    def test_trigger_changes_apply_without_button_and_invalid_text_is_not_sent(self):
        editor = self.capture.external_triggers
        self.assertFalse(editor.hex_mode.isChecked())
        self.assertTrue(editor.expression.isEnabled())
        self.assertFalse(any(b.text() == "Apply and verify" for b in editor.findChildren(QtWidgets.QPushButton)))
        editor.polarities[0].setCurrentIndex(0)
        self.assertEqual(self.state["config"], 0xAAAAE1)
        editor.enables[1].setChecked(True)
        self.assertEqual(self.state["config"] & 15, 3)
        self.send.reset_mock()
        editor.expression.setText("A & (")
        self.send.assert_not_called()
        editor.expression.setText("A & B")
        self.assertEqual(self.state["config"], 0x8888E3)
        editor.hex_mode.setChecked(True)
        editor.lut.setText("0xEEEE")
        self.assertEqual(self.state["config"], 0xEEEEE3)
        self.assertTrue(editor.expression.isEnabled())
        editor.expression.setText("A | ~B")
        self.assertFalse(editor.hex_mode.isChecked())
        self.assertEqual(self.state["config"], 0xBBBBE3)

    def test_config_readback_refresh_does_not_write_back(self):
        self.state.update(config=0xEEEE0F, deadtime=44)
        self.send.reset_mock()
        self.capture._read_external_triggers()
        self.send.assert_not_called()
        for editor in self.capture.external_editors:
            self.assertEqual(editor.config(), 0xEEEE0F)
            self.assertTrue(editor.expression.isEnabled())
        self.assertEqual(self.capture.spin_trigger_deadtime.value(), 44)


    def test_unsupported_firmware_keeps_local_edits_and_warns_once(self):
        capture = self.capture
        editor = capture.external_triggers
        read = self.controller._read_fpga_value
        self.controller._read_fpga_value = lambda page, selector=0: 0 if page == 71 else read(page, selector)
        with patch("tab_capture.QtWidgets.QMessageBox.warning") as warning:
            editor.enables[1].setChecked(True)
            editor.polarities[0].setCurrentIndex(0)
            editor.expression.setText("A & B")
            warning.assert_called_once()
        self.assertEqual(editor.expression.text(), "A & B")
        self.assertEqual(editor.lut.text(), "0x8888")
        self.assertTrue(editor.expression.isEnabled())
        self.assertEqual(editor.config(), 0x8888E3)
        self.assertIn("Local settings only", editor.hardware_status.text())
        self.assertEqual(capture.external_editors[1].config(), editor.config())
        self.assertEqual(self.state["config"], DEFAULT_CONFIG)
        self.assertEqual(next(r[3] for r in self.registers.register_table
                              if r[1] == "external_trigger_config"), DEFAULT_CONFIG)
        self.send.assert_not_called()
        # With supported firmware, the next change applies the whole draft.
        self.controller._read_fpga_value = read
        editor.expression.setText("A | B")
        self.assertEqual(self.state["config"], 0xEEEEE3)
        self.assertTrue(all(not w.hardware_status.text() for w in capture.external_editors))


    def reopen_capture(self):
        parent = QtWidgets.QWidget()
        self.addCleanup(parent.close)
        reopened = tab_capture(parent)
        reopened.bind_minidaq_registers(MiniDAQ_reg())
        return reopened

    def test_trigger_settings_survive_reopening_without_startup_writes(self):
        editor = self.capture.external_triggers
        editor.enables[1].setChecked(True)
        editor.polarities[1].setCurrentIndex(1)
        editor.expression.setText("(A & ~B)")
        self.capture.spin_trigger_deadtime.setValue(42)
        self.capture.sma_output_checks[2].setChecked(False)
        self.registers.set_named_value("hit_width", 12)
        self.registers.set_named_value("match_window", 89)
        expected = editor.settings_state()
        self.send.reset_mock()
        reopened = self.reopen_capture()
        self.send.assert_not_called()
        for other in reopened.external_editors:
            self.assertEqual(other.settings_state(), expected)
            self.assertIn("Restored local settings", other.hardware_status.text())
        self.assertEqual(reopened.spin_trigger_deadtime.value(), 42)
        self.assertFalse(reopened.sma_output_checks[2].isChecked())
        self.assertEqual(reopened.register_editors[4].controls["hit_width"].value(), 12)
        self.assertEqual(reopened.register_editors[0].controls["match_window"].value(), 89)

    def test_local_and_incomplete_expression_drafts_survive_reopening(self):
        editor = self.capture.external_triggers
        read = self.controller._read_fpga_value
        self.controller._read_fpga_value = lambda page, selector=0: 0 if page == 71 else read(page, selector)
        with patch("tab_capture.QtWidgets.QMessageBox.warning"):
            editor.expression.setText("~A")
        reopened = self.reopen_capture()
        self.assertEqual(reopened.external_triggers.expression.text(), "~A")
        self.assertEqual(reopened.external_triggers.lut.text(), "0x5555")
        self.assertEqual(self.state["config"], DEFAULT_CONFIG)
        editor.expression.setText("A & (")
        reopened = self.reopen_capture()
        self.assertEqual(reopened.external_triggers.expression.text(), "A & (")
        self.assertFalse(reopened.external_triggers.hex_mode.isChecked())

    def test_hex_editor_mode_and_readback_are_remembered(self):
        editor = self.capture.external_triggers
        editor.hex_mode.setChecked(True)
        editor.lut.setText("0xEEEE")
        reopened = self.reopen_capture()
        self.assertTrue(reopened.external_triggers.hex_mode.isChecked())
        self.assertEqual(reopened.external_triggers.lut.text(), "0xEEEE")
        self.state.update(config=0x88880F, deadtime=71, mask=3)
        self.capture._read_external_triggers()
        self.send.reset_mock()
        reopened = self.reopen_capture()
        self.send.assert_not_called()
        self.assertEqual(reopened.external_triggers.config(), 0x88880F)
        self.assertEqual(reopened.spin_trigger_deadtime.value(), 71)
        self.assertEqual([w.isChecked() for w in reopened.sma_output_checks], [True, True, False, False])



if __name__ == "__main__":
    unittest.main()
