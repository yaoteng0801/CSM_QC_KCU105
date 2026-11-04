/* 
       _________   ________     ________       
      / U OF M  \ | LSA    \   / Physics\
      \__ATLAS__/ |   ___   | |   ______/
         |   |    |  |   \  | |  |
         |   |    |  |___/  | |  \______     
         |   |    |         | |         \
         \___/    |________/   \________/
*/  

// Author : Yuxiang Guo  gyuxiang@umich.edu
// File   : MiniDAQ_reg.sv
// Create : 2025-01-27 09:55:52
// Revise : 2026-07-31
// Editor : sublime text4, tab size (4)
// Description:
//   Addressed MiniDAQ register bank.  Address, read selector, and write data
//   are separate signals; no control field is packed into the write value.
//   Readback remains 160 bits because one BER sample is exactly 160 bits and
//   Ethernet request/response metadata carries the page address and Ethernet
//   FCS supplies integrity, so readback data contains neither an embedded
//   page-address byte nor the former UART parity byte.
//
// -----------------------------------------------------------------------------
// fpga config reg map
/*
reg_address     reg                     value_bit   desc
1               reserved                4           target selection is carried in Ethernet requests
2               uplink_reset            UPLINKCOUNT  bit[i] resets uplink i
3               downlink_reset          1
4               sc_reset                1           Reset ic tx, ic rx and sca
5               global_rst              1           FPGA_TDC reset/bcr, send TTC bcr and TTC event reset, 
reset FPGA trigger FIFO, reset FPGA event count, reset FPGA trigger_coarse (for trigger matching), reset event builder, reset FPGA readout FIFO, reset decoder dline lock, reset decoder channel FIFO and RAM.
6               bc_rst                  1           FPGA_TDC reset/bcr, send TTC bcr
7               event_rst               1           FPGA event reset, send TTC event reset
8               master_rst              1           send TTC master reset
9               TRST                    1           mezz JTAG TRST and rst_in (tied together)
10              en_int_trigger          1           switch between internal and external trigger, 1=internal
11              enable_hit              1           start internal periodical pulse
12              hit_inv                 1           inverse the internal trigger. 1 = negative pulse
13              hit_single              1           send a single pulse as internal trigger
14              hit_width               12          internal pulse width = hit_width*25 ns
15              hit_interval            24          rate = 40M/(1+hit_interval), default to 1KHz
16              correct_counter_th      20          comma code repeating time before data line lock
17              enable_K28_1            1           1=k28.1, 0=k28.5
18              enable_320M             1           1=320 Mbps, 0=160 Mbps
19              trigger_deadtime        16           trigger dead time, LSB=25 ns
20              match_window            12          MiniDAQ trigger match window, LSB=25 ns
21              search_margin           12          MiniDAQ trigger match search margin, LSB=25 ns
22              bc_offset               12          MiniDAQ trigger match bc_offset, LSB=25 ns
23              reject_offset           12          MiniDAQ trigger match reject_offset, LSB=25 ns
24              rollover                12          MiniDAQ trigger match rollover, LSB=25 ns
25              coarse_count_offset     12          MiniDAQ trigger match coarse_count_offset, LSB=25 ns
26              en_relative_trig_data   1           MiniDAQ sends out timing relative to trigger instead of raw when set to 1
27              enable_matching         1           1 = matching in MiniDAQ. 0 = sends all data out.
28              trigger_redge           1           1 = rising edge, 0 = falling edge
29              trigger_latency         8           Trigger matching starts trigger_latency*25 ns after a trigger is detected                           
30              phase_sel_160M_20b      80          Phase select for 160M mode 4*{TDC9_dline1,TDC9_dline0,..., TDC0_dline1, TDC0_dline0}
31              drpen                   4           drpen for uplink[3:0]  enable read (when drpwe=0)/write(when drpwe=01) for DRP
32              drpwe                   4           drpwe for uplink[3:0]  status 0: read 1: write
33              drpaddr                 36          drpaddr for uplink[3:0]
34              drpdi                   64          drpdi for uplink[3:0]
35              rxprbscntreset          4           rxprbscntreset for uplink[3:0]  Resets the PRBS error counter
36              rxprbssel               16          rxprbssel for uplink[3:0] 
                                                    4'b0000: Standard operation mode. (PRBS check is off) 
                                                    4'b0001: PRBS-7 
                                                    4'b0010: PRBS-9 
                                                    4'b0011: PRBS-15 
                                                    4'b0100: PRBS-23 
                                                    4'b0101: PRBS-31
37              window_cycles           16          LSB=25 ns, default to 20, hit arrive time window for event builder
38              hit_threshold           10          default 4
39              hit_upper_threshold     10          default 128
40              run_enable              1           hit fifo starts to receive input when run_enable=1
41              fsm_watchdog_cycles     21          LSB=25 ns, default 40000 (1 ms), clamp to 2000000 (50 ms)
42              noise_test_mode         2           bit0 = raw hit stream, bit1 = 1 Hz counter stream
43              noise_counter_clear     1           clear live noise counters pulse
44              acquisition_mode       1           0 = externally triggered, 1 = hit-driven events with external trigger data included
45              system_reset            1           one-clock pulse replacing the uplink VIO system reset
46              uplink_interleaver_bypass UPLINKCOUNT
47              uplink_fec_bypass       UPLINKCOUNT
48              uplink_scrambler_bypass UPLINKCOUNT
49              uplink_rx_polarity      UPLINKCOUNT
50              uplink_fec_clear        UPLINKCOUNT
51              uplink_phase_calib      3*UPLINKCOUNT
52              uplink_phase_force      UPLINKCOUNT
53              downlink_interleaver_bypass DOWNLINKCOUNT
54              downlink_fec_bypass     DOWNLINKCOUNT
55              downlink_scrambler_bypass DOWNLINKCOUNT
56              downlink_tx_pi_calib    7*DOWNLINKCOUNT
57              downlink_tx_calib_enable DOWNLINKCOUNT
58              downlink_tx_polarity    DOWNLINKCOUNT
59              downlink_phase_calib    10*DOWNLINKCOUNT
60              downlink_phase_force    DOWNLINKCOUNT
61              tdc_chamber_map         80          [39:0] enabled TDCs, [79:40] chamber-1 TDCs; writable only while stopped
62..67          tube geometry/filter registers     see firmware/triggerless_tube_filters.md
68..70          diagnostic snapshot/readback       see firmware/triggerless_diagnostics.md


*/

// -----------------------------------------------------------------------------
// readback page map
//
// page 1  control/reset and run-mode status
// page 2  internal-trigger and trigger-matching configuration
// page 3  decoded-line locks and uplink/downlink ready status
// page 4  event-builder thresholds and watchdog configuration
// page 5  BER counters; readback_selector_i selects one of 10 TDCs per uplink
// page 6  PRBS and DRP status
// page 7  per-uplink configuration and status
// page 8  per-downlink configuration and status
//
// Pages 1-4 and 6-8 are right-aligned at bit 0 and zero-padded above their
// payload. Page 5 occupies the complete 160-bit readback word.
// -----------------------------------------------------------------------------
  
module MiniDAQ_reg
    #(parameter UPLINKCOUNT = 1,
      parameter DOWNLINKCOUNT = 1)
    (
    input               clk,
    input               rst,
    input               register_reset_i,

    // Ethernet carries the address and selector as protocol fields, so they
    // no longer consume bytes inside the register value.  All 160 write-data
    // bits are available to the selected register.
    input [7:0]    register_address_i,
    input [7:0]    readback_selector_i,
    input [159:0]  register_write_data_i,
    input          register_write_i,
    input          register_read_i,

    input [UPLINKCOUNT*10-1:0] locked_dline0,
    input [UPLINKCOUNT*10-1:0] locked_dline1,

    input [UPLINKCOUNT-1:0] lpgbtfpga_uplinkrdy,
    input [DOWNLINKCOUNT-1:0] lpgbtfpga_downlinkrdy,
    input [UPLINKCOUNT-1:0] uplink_fec_corrected_latched_i,
    input [2:0] uplink_phase_i[UPLINKCOUNT-1:0],
    input [9:0] downlink_phase_i[DOWNLINKCOUNT-1:0],
    input [DOWNLINKCOUNT-1:0] downlink_tx_aligned_i,
    input [6:0] downlink_tx_pi_phase_i[DOWNLINKCOUNT-1:0],



    input  [43:0]  total_received_40bit_dline1[UPLINKCOUNT-1:0][9:0],
    input  [43:0]  total_received_40bit_dline0[UPLINKCOUNT-1:0][9:0],
    input  [35:0]  total_error_bit_dline1[UPLINKCOUNT-1:0][9:0],
    input  [35:0]  total_error_bit_dline0[UPLINKCOUNT-1:0][9:0],

    output reg          run_enable_o,
    output reg          stream_hits_only_o,
    output reg          noise_counter_stream_o,
    output reg          noise_counter_clear_o,
    output reg          acquisition_mode_o,


    output reg          readback_valid_o,
    output reg [159:0]  readback_data_o,

    output reg          sc_reset_o,
    output reg          global_rst_o,
    output reg          bc_rst_o,
    output reg          event_rst_o,
    output reg          master_rst_o,
    output reg          mezz_TRST_o,

    output reg  [UPLINKCOUNT-1:0] uplink_reset_o,
    output reg          downlink_reset_o,
    output reg          system_reset_pulse_o,

    output reg  [UPLINKCOUNT-1:0] uplink_interleaver_bypass_o,
    output reg  [UPLINKCOUNT-1:0] uplink_fec_bypass_o,
    output reg  [UPLINKCOUNT-1:0] uplink_scrambler_bypass_o,
    output reg  [UPLINKCOUNT-1:0] uplink_rx_polarity_o,
    output reg  [UPLINKCOUNT-1:0] uplink_fec_clear_o,
    output      [2:0]             uplink_phase_calib_o[UPLINKCOUNT-1:0],
    output reg  [UPLINKCOUNT-1:0] uplink_phase_force_o,

    output reg  [DOWNLINKCOUNT-1:0] downlink_interleaver_bypass_o,
    output reg  [DOWNLINKCOUNT-1:0] downlink_fec_bypass_o,
    output reg  [DOWNLINKCOUNT-1:0] downlink_scrambler_bypass_o,
    output      [6:0]               downlink_tx_pi_calib_o[DOWNLINKCOUNT-1:0],
    output reg  [DOWNLINKCOUNT-1:0] downlink_tx_calib_enable_o,
    output reg  [DOWNLINKCOUNT-1:0] downlink_tx_polarity_o,
    output      [9:0]               downlink_phase_calib_o[DOWNLINKCOUNT-1:0],
    output reg  [DOWNLINKCOUNT-1:0] downlink_phase_force_o,

    output reg          en_int_trigger_o,
    output reg          enable_hit_o,
    output reg          hit_inv_o,
    output reg          hit_single_o,
    output reg  [11:0]  hit_width_o,
    output reg  [23:0]  hit_interval_o,

    output reg  [19:0]  correct_counter_th_o,
    output reg          enable_K28_1_o,
    output reg          enable_320M_o,

    output reg  [15:0]  trigger_deadtime_o,
    output reg  [11:0]  match_window_o,
    output reg  [11:0]  search_margin_o,
    output reg  [11:0]  bc_offset_o,
    output reg  [11:0]  reject_offset_o,
    output reg  [11:0]  rollover_o,
    output reg  [11:0]  coarse_count_offset_o,
    output reg          en_relative_trig_data_o,
    output reg          enable_matching_o,
    output reg          trigger_redge_o,
    output reg  [7:0]   trigger_latency_o,
    output  [19:0]      phase_sel_160M_20b_o[UPLINKCOUNT-1:0],

    output reg  [UPLINKCOUNT-1:0]       drpen_o,
    output reg  [UPLINKCOUNT-1:0]       drpwe_o,
    output reg  [UPLINKCOUNT*9-1:0]     drpaddr_o,
    output reg  [UPLINKCOUNT*16-1:0]    drpdi_o,
    output reg  [UPLINKCOUNT-1:0]       rxprbscntreset_o,
    output reg  [UPLINKCOUNT*4-1:0]     rxprbssel_o,

    output reg  [15:0]  window_cycles_o,
    output reg  [9:0]   hit_threshold_o,
    output reg  [9:0]   hit_upper_threshold_o,
    output reg  [20:0]  fsm_watchdog_cycles_o,
    output reg  [39:0]  tdc_enable_mask_o,
    output reg  [39:0]  tdc_chamber1_mask_o,
    input       [21:0]  geometry_lookup_address_i,
    output      [95:0]  geometry_lookup_data_o,
    output              geometry_ready_o,
    output      [85:0]  tube_filter_settings_o,
    output      [31:0]  geometry_mls_o,
    output      [511:0] geometry_layers_o,
    input       [27:0] diagnostic_pulses_i,
    input       [11:0] diagnostic_fifo_lost_words_i,

    input [UPLINKCOUNT*16-1:0]    drpdo_i,
    input [UPLINKCOUNT-1:0]       rxprbserr_i,
    input [UPLINKCOUNT-1:0]       rxprbslocked_i

);
    
reg readback_pending;
reg [159:0] readback_reg;
reg [UPLINKCOUNT*20-1:0] phase_sel_160M_20b_reg;
reg [UPLINKCOUNT*3-1:0] uplink_phase_calib_reg;
wire [UPLINKCOUNT*3-1:0] uplink_phase_flat;
reg [DOWNLINKCOUNT*7-1:0] downlink_tx_pi_calib_reg;
reg [DOWNLINKCOUNT*10-1:0] downlink_phase_calib_reg;
wire [DOWNLINKCOUNT*10-1:0] downlink_phase_flat;
wire [DOWNLINKCOUNT*7-1:0] downlink_tx_pi_phase_flat;
wire [159:0] BER_info[UPLINKCOUNT*10-1:0];
wire [159:0] geometry_readback;
wire geometry_busy;
wire [159:0] diagnostic_readback;
triggerless_diagnostics diagnostics (
    .clk(clk), .rst(rst), .register_reset(register_reset_i), .run_enable(run_enable_o),
    .write_enable(register_write_i), .address(register_address_i),
    .selector(readback_selector_i), .write_data(register_write_data_i),
    .increments(diagnostic_pulses_i), .fifo_lost_words(diagnostic_fifo_lost_words_i),
    .read_data(diagnostic_readback)
);
triggerless_geometry_config tube_geometry_config (
    .clk(clk), .rst(rst | register_reset_i),
    .run_enable(run_enable_o), .write_enable(register_write_i),
    .address(register_address_i), .selector(readback_selector_i),
    .write_data(register_write_data_i),
    .tdc_enable(tdc_enable_mask_o), .tdc_chamber1(tdc_chamber1_mask_o),
    .lookup_address(geometry_lookup_address_i), .lookup_data(geometry_lookup_data_o),
    .ready(geometry_ready_o), .busy(geometry_busy),
    .filter_settings(tube_filter_settings_o),
    .selected_mls(geometry_mls_o), .selected_layers(geometry_layers_o),
    .read_data(geometry_readback)
);

genvar m;
for (m = 0; m < UPLINKCOUNT; m=m+1) begin
    assign phase_sel_160M_20b_o[m] = phase_sel_160M_20b_reg[m*20+19:m*20];
    assign uplink_phase_calib_o[m] = uplink_phase_calib_reg[m*3 +: 3];
    assign uplink_phase_flat[m*3 +: 3] = uplink_phase_i[m];
end

genvar n;
for (n = 0; n < DOWNLINKCOUNT; n=n+1) begin
    assign downlink_tx_pi_calib_o[n] = downlink_tx_pi_calib_reg[n*7 +: 7];
    assign downlink_phase_calib_o[n] = downlink_phase_calib_reg[n*10 +: 10];
    assign downlink_phase_flat[n*10 +: 10] = downlink_phase_i[n];
    assign downlink_tx_pi_phase_flat[n*7 +: 7] = downlink_tx_pi_phase_i[n];
end

genvar uplink, ch;
generate
  for (uplink = 0; uplink < UPLINKCOUNT; uplink = uplink + 1) begin : uplink_loop
    for (ch = 0; ch < 10; ch = ch + 1) begin : ch_loop
      assign BER_info[uplink*10 + ch] = {
        total_received_40bit_dline1[uplink][ch],  // 44 bits
        total_received_40bit_dline0[uplink][ch],  // 44 bits
        total_error_bit_dline1[uplink][ch],       // 36 bits
        total_error_bit_dline0[uplink][ch]        // 36 bits
      };
      // Total = 44 + 44 + 36 + 36 = 160 bits
    end
  end
endgenerate


localparam ZERO_PADDING_BITS = 128 - (UPLINKCOUNT * 20);
localparam UPLINK_PADDING = 8 - UPLINKCOUNT;
localparam DOWNLINK_PADDING = 8 - DOWNLINKCOUNT;
localparam CONTROL_READBACK_PADDING = 5 - UPLINKCOUNT;
localparam [20:0] FSM_WATCHDOG_DEFAULT_CYCLES = 21'd40000;
localparam [20:0] FSM_WATCHDOG_MAX_CYCLES     = 21'd2000000;
localparam [15:0] WINDOW_CYCLES_MIN           = 16'd1;
localparam [9:0]  HIT_THRESHOLD_MAX           = 10'd256;
localparam UPLINK_READBACK_PADDING             = 144 - (13 * UPLINKCOUNT);
localparam DOWNLINK_READBACK_PADDING           = 144 - (42 * DOWNLINKCOUNT);

// output control
always @(posedge clk  ) begin
    if (rst | register_reset_i) begin
        readback_pending <= 1'b0;
        readback_valid_o <= 1'b0;
        readback_data_o <= 'b0;
    end else begin
        readback_pending <= register_read_i;
        // Two cycles after register_read_i, readback_valid_o is aligned with
        // readback_data_o.  The Ethernet engine waits for this valid pulse.
        readback_valid_o <= readback_pending;
        readback_data_o <= readback_reg;
    end
end


always @(posedge clk  ) begin
    if (rst | register_reset_i) begin
        // default values
        uplink_reset_o   <= 'b0;
        downlink_reset_o <= 1'b0;
        system_reset_pulse_o  <= 1'b0;
        uplink_interleaver_bypass_o <= 'b0;
        uplink_fec_bypass_o         <= 'b0;
        uplink_scrambler_bypass_o   <= 'b0;
        uplink_rx_polarity_o        <= 'b0;
        uplink_fec_clear_o          <= 'b0;
        uplink_phase_calib_reg      <= 'b0;
        uplink_phase_force_o        <= 'b0;
        downlink_interleaver_bypass_o <= 'b0;
        downlink_fec_bypass_o         <= 'b0;
        downlink_scrambler_bypass_o   <= 'b0;
        downlink_tx_pi_calib_reg      <= 'b0;
        downlink_tx_calib_enable_o    <= 'b0;
        downlink_tx_polarity_o        <= 'b0;
        downlink_phase_calib_reg      <= 'b0;
        downlink_phase_force_o        <= 'b0;
        sc_reset_o            <= 1'b0;
        global_rst_o     <= 1'b0;
        bc_rst_o         <= 1'b0;
        event_rst_o      <= 1'b0;
        master_rst_o     <= 1'b0;
        mezz_TRST_o           <= 1'b1;

        en_int_trigger_o      <= 1'b0;
        enable_hit_o          <= 1'b0;
        hit_inv_o             <= 1'b1;
        hit_single_o          <= 1'b0;
        hit_width_o           <= 12'h4;
        hit_interval_o        <= 24'd40000;  //rate = 40M/(1+interval), default to 1KHz

        correct_counter_th_o    <=  20'd1000000;
        enable_K28_1_o          <=  1'b1;
        enable_320M_o           <=  1'b1;

        trigger_deadtime_o      <=  16'd10;
        match_window_o          <=  12'd60;
        search_margin_o         <=  12'd100;
        bc_offset_o             <=  12'd0;
        reject_offset_o         <=  12'd300;
        rollover_o              <=  12'd4095;
        coarse_count_offset_o   <=  12'd4070;
        en_relative_trig_data_o <=  1'b0;
        enable_matching_o       <=  1'b1;
        trigger_redge_o         <=  1'b0;
        trigger_latency_o       <=  8'd100;
        phase_sel_160M_20b_reg  <=  'b0;

        drpen_o                 <=  'b0;
        drpwe_o                 <=  'b0;
        drpaddr_o               <=  'b0;
        drpdi_o                 <=  'b0;
        rxprbscntreset_o        <=  'b0;
        rxprbssel_o             <=  'b0;

        window_cycles_o         <= 16'd20;
        hit_threshold_o         <= 10'd4;
        hit_upper_threshold_o   <= 10'd128;
        fsm_watchdog_cycles_o   <= FSM_WATCHDOG_DEFAULT_CYCLES;

        run_enable_o            <= 1'b0;
        stream_hits_only_o      <= 1'b0;
        noise_counter_stream_o  <= 1'b0;
        noise_counter_clear_o   <= 1'b0;
        acquisition_mode_o      <= 1'b0;
        tdc_enable_mask_o       <= 40'hffffffffff;
        tdc_chamber1_mask_o     <= 40'b0;

    end else begin
        noise_counter_clear_o <= 1'b0;
        system_reset_pulse_o  <= 1'b0;

        if (register_write_i) begin
            case (register_address_i)
                8'd1:begin end // reserved: Ethernet request selects its target
                8'd2:uplink_reset_o           <= register_write_data_i[UPLINKCOUNT-1:0];
                8'd3:downlink_reset_o         <= register_write_data_i[0];
                8'd4:sc_reset_o               <= register_write_data_i[0];
                8'd5:global_rst_o             <= register_write_data_i[0];
                8'd6:bc_rst_o                 <= register_write_data_i[0];
                8'd7:event_rst_o              <= register_write_data_i[0];
                8'd8:master_rst_o             <= register_write_data_i[0];
                8'd9:mezz_TRST_o              <= register_write_data_i[0];

                8'd10:en_int_trigger_o        <= register_write_data_i[0];
                8'd11:enable_hit_o            <= register_write_data_i[0];
                8'd12:hit_inv_o               <= register_write_data_i[0];
                8'd13:hit_single_o            <= register_write_data_i[0];
                8'd14:hit_width_o             <= register_write_data_i[11:0];
                8'd15:hit_interval_o          <= register_write_data_i[23:0];  //rate = 40M/(1+interval), default to 1KHz


                8'd16:correct_counter_th_o    <= register_write_data_i[19:0];
                8'd17:enable_K28_1_o          <= register_write_data_i[0];
                8'd18:enable_320M_o           <= register_write_data_i[0];

                8'd19:trigger_deadtime_o      <= register_write_data_i[15:0];
                8'd20:match_window_o          <= register_write_data_i[11:0];
                8'd21:search_margin_o         <= register_write_data_i[11:0];
                8'd22:bc_offset_o             <= register_write_data_i[11:0];
                8'd23:reject_offset_o         <= register_write_data_i[11:0];
                8'd24:rollover_o              <= register_write_data_i[11:0];
                8'd25:coarse_count_offset_o   <= register_write_data_i[11:0];
                8'd26:en_relative_trig_data_o <= register_write_data_i[0];
                8'd27:enable_matching_o       <= register_write_data_i[0];
                8'd28:trigger_redge_o         <= register_write_data_i[0];
                8'd29:trigger_latency_o       <= register_write_data_i[7:0];
                8'd30:phase_sel_160M_20b_reg  <= register_write_data_i[UPLINKCOUNT*20-1:0];

                8'd31:drpen_o                 <= register_write_data_i[UPLINKCOUNT-1:0];
                8'd32:drpwe_o                 <= register_write_data_i[UPLINKCOUNT-1:0];
                8'd33:drpaddr_o               <= register_write_data_i[UPLINKCOUNT*9-1:0];
                8'd34:drpdi_o                 <= register_write_data_i[UPLINKCOUNT*16-1:0];
                8'd35:rxprbscntreset_o        <= register_write_data_i[UPLINKCOUNT-1:0];
                8'd36:rxprbssel_o             <= register_write_data_i[UPLINKCOUNT*4-1:0];
                8'd37:window_cycles_o         <= (register_write_data_i[15:0] < WINDOW_CYCLES_MIN) ?
                                                 WINDOW_CYCLES_MIN : register_write_data_i[15:0];
                8'd38:if (!run_enable_o) hit_threshold_o <= (register_write_data_i[9:0] > HIT_THRESHOLD_MAX) ?
                                                 HIT_THRESHOLD_MAX : register_write_data_i[9:0];
                8'd39:if (!run_enable_o) hit_upper_threshold_o <= register_write_data_i[9:0];
                8'd40:run_enable_o <= register_write_data_i[0] &&
                    (!acquisition_mode_o || stream_hits_only_o || noise_counter_stream_o || geometry_ready_o);
                8'd41:fsm_watchdog_cycles_o   <= (register_write_data_i[20:0] > FSM_WATCHDOG_MAX_CYCLES) ?
                                                 FSM_WATCHDOG_MAX_CYCLES : register_write_data_i[20:0];
                8'd42:if (!run_enable_o) begin
                    stream_hits_only_o     <= register_write_data_i[0];
                    noise_counter_stream_o <= register_write_data_i[1];
                end
                8'd43:noise_counter_clear_o <= register_write_data_i[0];
                8'd44:if (!run_enable_o) acquisition_mode_o <= register_write_data_i[0];
                8'd45:system_reset_pulse_o         <= register_write_data_i[0];
                8'd46:uplink_interleaver_bypass_o <= register_write_data_i[UPLINKCOUNT-1:0];
                8'd47:uplink_fec_bypass_o         <= register_write_data_i[UPLINKCOUNT-1:0];
                8'd48:uplink_scrambler_bypass_o   <= register_write_data_i[UPLINKCOUNT-1:0];
                8'd49:uplink_rx_polarity_o        <= register_write_data_i[UPLINKCOUNT-1:0];
                8'd50:uplink_fec_clear_o          <= register_write_data_i[UPLINKCOUNT-1:0];
                8'd51:uplink_phase_calib_reg      <= register_write_data_i[UPLINKCOUNT*3-1:0];
                8'd52:uplink_phase_force_o        <= register_write_data_i[UPLINKCOUNT-1:0];
                8'd53:downlink_interleaver_bypass_o <= register_write_data_i[DOWNLINKCOUNT-1:0];
                8'd54:downlink_fec_bypass_o         <= register_write_data_i[DOWNLINKCOUNT-1:0];
                8'd55:downlink_scrambler_bypass_o   <= register_write_data_i[DOWNLINKCOUNT-1:0];
                8'd56:downlink_tx_pi_calib_reg      <= register_write_data_i[DOWNLINKCOUNT*7-1:0];
                8'd57:downlink_tx_calib_enable_o    <= register_write_data_i[DOWNLINKCOUNT-1:0];
                8'd58:downlink_tx_polarity_o        <= register_write_data_i[DOWNLINKCOUNT-1:0];
                8'd59:downlink_phase_calib_reg      <= register_write_data_i[DOWNLINKCOUNT*10-1:0];
                8'd60:downlink_phase_force_o        <= register_write_data_i[DOWNLINKCOUNT-1:0];
                8'd61:if (!run_enable_o) begin
                    tdc_enable_mask_o   <= register_write_data_i[39:0];
                    tdc_chamber1_mask_o <= register_write_data_i[79:40] &
                                           register_write_data_i[39:0];
                end

                default: begin end
            endcase
        end
    end
end

wire [UPLINKCOUNT*20-1:0] dline_status;
genvar j;
for (j = 0; j < UPLINKCOUNT; j=j+1) begin
    
    assign dline_status[j*20+10-1:j*20]    = locked_dline0[j*10+9:j*10];
    assign dline_status[j*20+20-1:j*20+10] = locked_dline1[j*10+9:j*10];
end

always @(posedge clk  ) begin
    if (rst | register_reset_i) begin
        readback_reg <= 160'b0;
    end else if (register_read_i) begin
        case (register_address_i)
            8'd1:readback_reg <= {16'b0,96'b0,
                trigger_deadtime_o, //2 bytes         
                3'b0,acquisition_mode_o,noise_counter_stream_o,stream_hits_only_o,run_enable_o,en_int_trigger_o,
                enable_hit_o,hit_inv_o,hit_single_o,enable_K28_1_o,
                enable_320M_o,en_relative_trig_data_o,enable_matching_o,trigger_redge_o,
                {CONTROL_READBACK_PADDING{1'b0}},4'b0,
                uplink_reset_o,downlink_reset_o,sc_reset_o,global_rst_o,
                bc_rst_o,event_rst_o,master_rst_o,mezz_TRST_o};
            8'd2:readback_reg <= {16'b0,
                hit_interval_o,  //3 bytes
                hit_width_o,correct_counter_th_o, //4 bytes
                8'b0, 
                match_window_o,search_margin_o,bc_offset_o,reject_offset_o,rollover_o,coarse_count_offset_o, //9 bytes
                trigger_latency_o};
            8'd3:
                readback_reg <= {16'b0, {ZERO_PADDING_BITS{1'b0}},
                dline_status,
                {UPLINK_PADDING{1'b0}},lpgbtfpga_uplinkrdy,
                {DOWNLINK_PADDING{1'b0}},lpgbtfpga_downlinkrdy};
            8'd4:
                readback_reg <= {16'b0,
                72'b0,
                window_cycles_o,          // 16
                6'b0, hit_threshold_o,    // 10 (pad to 16)
                6'b0, hit_upper_threshold_o, // 10 (pad to 16)
                3'b0, fsm_watchdog_cycles_o}; // 21 (pad to 24)

            8'd5:  begin //readback bit error content
                if (readback_selector_i < UPLINKCOUNT*10)
                    readback_reg <= BER_info[readback_selector_i];
                else
                    readback_reg <= 160'b0;
            end
            8'd6:
                readback_reg <= {16'b0,
                    {(128-16*UPLINKCOUNT){1'b0}},
                    {(8-UPLINKCOUNT){1'b0}}, rxprbserr_i,
                    {(8-UPLINKCOUNT){1'b0}}, rxprbslocked_i,
                    drpdo_i}; //2*UPLINKCOUNT bytes
            // UPLINKCOUNT=4 payload:
            // [51:40] phase status, [39:36] FEC-corrected latch,
            // [35:24] phase calibration, [23:20] phase force,
            // [19:16] FEC clear, [15:12] RX polarity,
            // [11:8] scrambler bypass, [7:4] FEC bypass,
            // [3:0] interleaver bypass.
            8'd7:
                readback_reg <= {16'b0,
                    {UPLINK_READBACK_PADDING{1'b0}},
                    uplink_phase_flat,
                    uplink_fec_corrected_latched_i,
                    uplink_phase_calib_reg,
                    uplink_phase_force_o,
                    uplink_fec_clear_o,
                    uplink_rx_polarity_o,
                    uplink_scrambler_bypass_o,
                    uplink_fec_bypass_o,
                    uplink_interleaver_bypass_o};
            // DOWNLINKCOUNT=2 payload:
            // [83:70] TX PI phase status, [69:68] TX aligned,
            // [67:48] phase status, [47:46] ready,
            // [45:44] phase force, [43:24] phase calibration,
            // [23:22] TX polarity, [21:20] TX calibration enable,
            // [19:6] TX PI calibration, [5:4] scrambler bypass,
            // [3:2] FEC bypass, [1:0] interleaver bypass.
            8'd8:
                readback_reg <= {16'b0,
                    {DOWNLINK_READBACK_PADDING{1'b0}},
                    downlink_tx_pi_phase_flat,
                    downlink_tx_aligned_i,
                    downlink_phase_flat,
                    lpgbtfpga_downlinkrdy,
                    downlink_phase_force_o,
                    downlink_phase_calib_reg,
                    downlink_tx_polarity_o,
                    downlink_tx_calib_enable_o,
                    downlink_tx_pi_calib_reg,
                    downlink_scrambler_bypass_o,
                    downlink_fec_bypass_o,
                    downlink_interleaver_bypass_o};
            8'd61:
                readback_reg <= {80'b0, tdc_chamber1_mask_o,
                                 tdc_enable_mask_o};
            8'd62, 8'd63, 8'd64, 8'd65, 8'd66, 8'd67:
                readback_reg <= geometry_readback;
            8'd68, 8'd69, 8'd70:
                readback_reg <= diagnostic_readback;

            default: readback_reg <= 160'b0;
        endcase
    end
end

endmodule
