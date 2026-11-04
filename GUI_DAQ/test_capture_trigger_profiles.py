import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from MiniDAQ_reg import MiniDAQ_reg
from tab_capture import (
    RUN_PROFILE_TRIGGERED_EXTERNAL,
    RUN_PROFILE_TRIGGERED_INTERNAL,
    RUN_PROFILE_TRIGGERLESS,
    RUN_PROFILE_TRIGGERLESS_NOISE_COUNTER,
    RUN_PROFILE_TRIGGERLESS_NOISE_RAW,
    RUN_PROFILE_SETTINGS,
    tab_capture,
)
from tab_lpgbt import tab_lpgbt
from triggerless_filters import TubeFilterSettings


class CaptureTriggerProfileTest(unittest.TestCase):
    @staticmethod
    def _controller():
        controller = object.__new__(tab_lpgbt)
        controller.miniDAQ_reg = MiniDAQ_reg()
        writes = []

        def set_register(name, value):
            for pos, (_index, reg_name, bit_width, _old) in enumerate(
                controller.miniDAQ_reg.register_table
            ):
                if reg_name != name:
                    continue
                value = controller.miniDAQ_reg.sanitize_value(
                    reg_name, value, bit_width
                )
                controller.miniDAQ_reg.set_register_value(pos, value)
                writes.append((name, value))
                return value
            raise KeyError(name)

        controller._set_minidaq_register = set_register
        return controller, writes

    def test_capture_profile_register_values(self):
        self.assertEqual(
            RUN_PROFILE_SETTINGS[RUN_PROFILE_TRIGGERED_EXTERNAL],
            (0, 0, 0, 0),
        )
        self.assertEqual(
            RUN_PROFILE_SETTINGS[RUN_PROFILE_TRIGGERED_INTERNAL],
            (0, 0, 1, 1),
        )
        self.assertEqual(
            RUN_PROFILE_SETTINGS[RUN_PROFILE_TRIGGERLESS],
            (1, 0, None, None),
        )
        self.assertEqual(
            RUN_PROFILE_SETTINGS[RUN_PROFILE_TRIGGERLESS_NOISE_RAW],
            (1, 1, None, None),
        )
        self.assertEqual(
            RUN_PROFILE_SETTINGS[RUN_PROFILE_TRIGGERLESS_NOISE_COUNTER],
            (1, 2, None, None),
        )

    def test_triggered_profiles_remain_distinct(self):
        self.assertEqual(
            tab_capture._run_mode_profile(0, 0, 0, 0),
            RUN_PROFILE_TRIGGERED_EXTERNAL,
        )
        self.assertEqual(
            tab_capture._run_mode_profile(0, 0, 1, 1),
            RUN_PROFILE_TRIGGERED_INTERNAL,
        )

    def test_capture_forwards_trigger_controls_to_hardware_callback(self):
        callback = Mock(return_value=(0, 0))
        capture = SimpleNamespace(
            _daq_set_modes_callback=callback,
            _daq_set_mode_callback=None,
        )

        result = tab_capture._set_minidaq_run_modes(
            capture,
            0,
            0,
            en_int_trigger=1,
            enable_hit=1,
        )

        self.assertEqual(result, (0, 0))
        callback.assert_called_once_with(
            0,
            0,
            en_int_trigger=1,
            enable_hit=1,
        )

    def test_external_profile_disables_periodic_internal_trigger(self):
        controller, writes = self._controller()
        controller.set_run_modes(
            0,
            0,
            en_int_trigger=0,
            enable_hit=0,
        )

        self.assertEqual(controller.current_acquisition_mode(), 0)
        self.assertEqual(controller.current_noise_test_mode(), 0)
        self.assertEqual(controller.current_en_int_trigger(), 0)
        self.assertEqual(controller.current_enable_hit(), 0)
        self.assertEqual(writes[:2], [("enable_hit", 0), ("en_int_trigger", 0)])

    def test_internal_profile_enables_periodic_internal_trigger(self):
        controller, writes = self._controller()
        controller.set_run_modes(
            0,
            0,
            en_int_trigger=1,
            enable_hit=1,
        )

        self.assertEqual(controller.current_acquisition_mode(), 0)
        self.assertEqual(controller.current_noise_test_mode(), 0)
        self.assertEqual(controller.current_en_int_trigger(), 1)
        self.assertEqual(controller.current_enable_hit(), 1)
        self.assertEqual(writes[:2], [("en_int_trigger", 1), ("enable_hit", 1)])

    def test_triggerless_profile_preserves_trigger_controls(self):
        controller, writes = self._controller()
        controller.set_run_modes(
            0,
            0,
            en_int_trigger=1,
            enable_hit=1,
        )
        writes.clear()

        controller.set_run_modes(1, 2)

        self.assertEqual(controller.current_acquisition_mode(), 1)
        self.assertEqual(controller.current_noise_test_mode(), 2)
        self.assertEqual(controller.current_en_int_trigger(), 1)
        self.assertEqual(controller.current_enable_hit(), 1)
        self.assertEqual(
            writes,
            [("acquisition_mode", 1), ("noise_test_mode", 2)],
        )

    def test_triggerless_event_settings_program_minidaq_registers(self):
        controller, writes = self._controller()

        filters = (TubeFilterSettings(min_tubes=256), TubeFilterSettings(enabled=15, min_layers_per_ml=3))
        controller._require_tube_firmware = Mock()
        controller._read_fpga_value = lambda addr: {
            1: 0, 4: 1 << 56, 66: filters[0].pack(), 67: filters[1].pack()
        }[addr]
        values = controller.set_triggerless_event_settings(0, filters)

        self.assertEqual(values, (1, filters))
        self.assertEqual(controller.current_triggerless_event_settings(), values)
        self.assertEqual(
            writes,
            [("window_cycles", 1), ("tube_filters_chamber0", filters[0].pack()),
             ("tube_filters_chamber1", filters[1].pack())],
        )

    def test_triggerless_event_settings_require_stopped_daq(self):
        controller, writes = self._controller()
        for pos, (_index, name, _width, _value) in enumerate(
            controller.miniDAQ_reg.register_table
        ):
            if name == "run_enable":
                controller.miniDAQ_reg.set_register_value(pos, 1)
                break

        with self.assertRaisesRegex(RuntimeError, "Stop the DAQ"):
            controller.set_triggerless_event_settings(20, (TubeFilterSettings(),)*2)

        self.assertEqual(writes, [])

    def test_capture_forwards_triggerless_event_settings(self):
        filters = (TubeFilterSettings(min_tubes=6), TubeFilterSettings(min_tubes=8))
        callback = Mock(return_value=(32, filters))
        capture = SimpleNamespace(
            _daq_set_triggerless_settings_callback=callback,
        )

        values = tab_capture._set_minidaq_triggerless_settings(
            capture,
            32,
            filters,
        )

        self.assertEqual(values, (32, filters))
        callback.assert_called_once_with(32, filters)


if __name__ == "__main__":
    unittest.main()
