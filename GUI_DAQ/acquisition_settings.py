"""Acquisition register ownership and packed FPGA readback locations."""
BOARD_SETTINGS = frozenset(("uplink_rst", "down_rst", "sca_reset", "global_rst",
    "bc_rst", "event_rst", "master_rst", "TRST", "correct_counter_th",
    "enable_K28_1", "enable_320M", "phase_sel_160M_20b_reg"))
TIMING = ("trigger_deadtime", "trigger_latency", "rollover", "coarse_count_offset")
MATCHING = ("enable_matching", "match_window", "search_margin", "bc_offset",
            "reject_offset", "en_relative_trig_data")
GENERATOR = ("enable_hit", "hit_inv", "hit_width", "hit_interval", "hit_single")
# Profiles match the Capture mode selector. Shared names are the same registers.
MODE_FIELDS = {
    0: TIMING + MATCHING + ("tdc_chamber_map",),
    4: GENERATOR + TIMING + MATCHING + ("tdc_chamber_map",),
    1: ("hit_upper_threshold", "fsm_watchdog_cycles") + TIMING + ("tdc_chamber_map",),
    2: ("tdc_chamber_map",),
    3: ("tdc_chamber_map", "noise_counter_clear"),
}
PULSE_FIELDS = frozenset(("hit_single", "noise_counter_clear"))
READBACK = {
    "enable_matching": (1, 17, 1), "en_relative_trig_data": (1, 18, 1),
    "hit_inv": (1, 22, 1), "enable_hit": (1, 23, 1),
    "trigger_deadtime": (1, 32, 16),
    "trigger_latency": (2, 0, 8), "coarse_count_offset": (2, 8, 12),
    "rollover": (2, 20, 12), "reject_offset": (2, 32, 12),
    "bc_offset": (2, 44, 12), "search_margin": (2, 56, 12),
    "match_window": (2, 68, 12), "hit_width": (2, 108, 12),
    "hit_interval": (2, 120, 24), "fsm_watchdog_cycles": (4, 0, 21),
    "window_cycles": (4, 56, 16),
    "tube_filters_chamber0": (66, 0, 43), "tube_filters_chamber1": (67, 0, 43),
    "hit_upper_threshold": (4, 24, 10), "tdc_chamber_map": (61, 0, 80),
}
