from PyQt5 import QtCore
from triggerless_filters import TubeFilterSettings


class MiniDAQ_reg(QtCore.QObject):
    register_changed = QtCore.pyqtSignal(str, object)
    MIN_WINDOW_CYCLES = 1
    MAX_HIT_THRESHOLD = 256
    MAX_NOISE_TEST_MODE = 2

    def __init__(self):
        super().__init__()
        self.register_table = [
            [2, 'uplink_rst', 1, 0],
            [3, 'down_rst', 1, 0],
            [4, 'sca_reset', 1, 0],
            [5, 'global_rst', 1, 0],
            [6, 'bc_rst', 1, 0],
            [7, 'event_rst', 1, 0],
            [8, 'master_rst', 1, 0],
            [9, 'TRST', 1, 1],
            [10, 'en_int_trigger', 1, 0],
            [11, 'enable_hit', 1, 0],
            [12, 'hit_inv', 1, 1],
            [13, 'hit_single', 1, 0],
            [14, 'hit_width', 12, 4],
            [15, 'hit_interval', 24, 40000],
            [16, 'correct_counter_th', 20, 1000000],
            [17, 'enable_K28_1', 1, 1],
            [18, 'enable_320M', 1, 1],
            [19, 'trigger_deadtime', 16, 10],
            [20, 'match_window', 12, 60],
            [21, 'search_margin', 12, 100],
            [22, 'bc_offset', 12, 0],
            [23, 'reject_offset', 12, 300],
            [24, 'rollover', 12, 4095],
            [25, 'coarse_count_offset', 12, 4070],
            [26, 'en_relative_trig_data', 1, 0],
            [27, 'enable_matching', 1, 1],
            [28, 'trigger_redge', 1, 0],
            [29, 'trigger_latency', 8, 100],
            [30, 'phase_sel_160M_20b_reg', 80, 0],
            [37, 'window_cycles', 16, 20],
            [38, 'hit_threshold', 10, 4],
            [39, 'hit_upper_threshold', 10, 128],
            [40, 'run_enable', 1, 0],
            [41, 'fsm_watchdog_cycles', 21, 40000],
            [42, 'noise_test_mode', 2, 0],
            [43, 'noise_counter_clear', 1, 0],
            [44, 'acquisition_mode', 1, 0],
            [61, 'tdc_chamber_map', 80, (1 << 40) - 1],
            [66, 'tube_filters_chamber0', 43, TubeFilterSettings().pack()],
            [67, 'tube_filters_chamber1', 43, TubeFilterSettings().pack()],
            [71, 'external_trigger_config', 24, 0xAAAA11],
            [72, 'sma_trigger_enable', 4, 15],
        ]

    def value_limits(self, name, bit_width):
        min_value = 0
        max_value = (1 << bit_width) - 1

        if name == 'window_cycles':
            min_value = self.MIN_WINDOW_CYCLES
        elif name == 'hit_threshold':
            max_value = min(max_value, self.MAX_HIT_THRESHOLD)
        elif name == 'noise_test_mode':
            max_value = min(max_value, self.MAX_NOISE_TEST_MODE)

        return min_value, max_value

    def sanitize_value(self, name, value, bit_width):
        if name.startswith('tube_filters_chamber'):
            return TubeFilterSettings.unpack(value).pack()
        try:
            value = int(value)
        except Exception:
            value = 0

        min_value, max_value = self.value_limits(name, bit_width)
        if value < min_value:
            value = min_value
        if value > max_value:
            value = max_value
        return value

    def set_register_value(self, pos, value):
        _, name, bit_width, _ = self.register_table[pos]
        value = self.sanitize_value(name, value, bit_width)
        old = self.register_table[pos][3]
        self.register_table[pos][3] = value
        if old != value:
            self.register_changed.emit(name, value)
        return value

    def set_named_value(self, name, value):
        pos = next(i for i, reg in enumerate(self.register_table) if reg[1] == name)
        return self.set_register_value(pos, value)

    def tube_filter_settings(self):
        return tuple(TubeFilterSettings.unpack(next(reg[3] for reg in self.register_table
                     if reg[1] == f'tube_filters_chamber{c}')) for c in range(2))

    def set_tube_filter_settings(self, settings):
        if len(settings) != 2:
            raise ValueError('Two chamber filter settings are required')
        packed = [cfg.pack() for cfg in settings]
        for c, value in enumerate(packed):
            self.set_named_value(f'tube_filters_chamber{c}', value)

    def reset(self):
        """ Reset all registers to their default values """
        default_table = [
            [2, 'uplink_rst', 1, 0],
            [3, 'down_rst', 1, 0],
            [4, 'sca_reset', 1, 0],
            [5, 'global_rst', 1, 0],
            [6, 'bc_rst', 1, 0],
            [7, 'event_rst', 1, 0],
            [8, 'master_rst', 1, 0],
            [9, 'TRST', 1, 1],
            [10, 'en_int_trigger', 1, 0],
            [11, 'enable_hit', 1, 0],
            [12, 'hit_inv', 1, 1],
            [13, 'hit_single', 1, 0],
            [14, 'hit_width', 12, 4],
            [15, 'hit_interval', 24, 40000],
            [16, 'correct_counter_th', 20, 1000000],
            [17, 'enable_K28_1', 1, 1],
            [18, 'enable_320M', 1, 1],
            [19, 'trigger_deadtime', 16, 10],
            [20, 'match_window', 12, 60],
            [21, 'search_margin', 12, 100],
            [22, 'bc_offset', 12, 0],
            [23, 'reject_offset', 12, 300],
            [24, 'rollover', 12, 4095],
            [25, 'coarse_count_offset', 12, 4070],
            [26, 'en_relative_trig_data', 1, 0],
            [27, 'enable_matching', 1, 1],
            [28, 'trigger_redge', 1, 0],
            [29, 'trigger_latency', 8, 100],
            [30, 'phase_sel_160M_20b_reg', 80, 0],
            [37, 'window_cycles', 16, 20],
            [38, 'hit_threshold', 10, 4],
            [39, 'hit_upper_threshold', 10, 128],
            [40, 'run_enable', 1, 0],
            [41, 'fsm_watchdog_cycles', 21, 40000],
            [42, 'noise_test_mode', 2, 0],
            [43, 'noise_counter_clear', 1, 0],
            [44, 'acquisition_mode', 1, 0],
            [61, 'tdc_chamber_map', 80, (1 << 40) - 1],
            [66, 'tube_filters_chamber0', 43, TubeFilterSettings().pack()],
            [67, 'tube_filters_chamber1', 43, TubeFilterSettings().pack()],
            [71, 'external_trigger_config', 24, 0xAAAA11],
            [72, 'sma_trigger_enable', 4, 15],
        ]
        
        # Reset all registers
        for i in range(len(self.register_table)):
            self.set_register_value(i, default_table[i][3])
