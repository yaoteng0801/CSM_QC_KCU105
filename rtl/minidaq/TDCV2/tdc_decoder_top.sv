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
// File   : tdc_decoder_top.sv
// Create : 2023-11-05 22:35:53
// Revise : 2026-07-27 10:54:43
// Editor : sublime text4, tab size (4)
// Description: 
//
// -----------------------------------------------------------------------------



module tdc_decoder_top
    #(parameter UPLINKCOUNT = 1,
      parameter TDC_COUNT_SINGLE = 10)
    (
    input           clk_40,
    input           clk_asyn,
    input           rst_in,
    input           acquisition_mode,
    input           run_enable,
    input           stream_hits_only,
    input           noise_counter_stream,
    input           noise_counter_clear,
    input   [229:0] userDataUpLink[UPLINKCOUNT-1:0],
    // input [27:0] elink_config_i[1:0],
    input           trigger_in,
    // output  [27:0]  error_detected_o,
    output  [1:0]   encode_ttc,
    // output [23:0] hit,
    // output mezz_TRST,
    output [UPLINKCOUNT*TDC_COUNT_SINGLE-1:0] locked_dline1_o,
    output [UPLINKCOUNT*TDC_COUNT_SINGLE-1:0] locked_dline0_o,

    input           bc_rst,
    input           event_rst,
    input           master_rst,

    input           en_int_trigger,
    input           enable_hit,
    input           hit_inv,
    input           hit_single,
    input   [11:0]  width_hit,
    input   [23:0]  hit_interval,

    input   [19:0]  correct_counter_th,
    input           enable_K28_1,
    input           enable_320M,
    input   [15:0]  trigger_deadtime,
    input   [11:0]  match_window,
    input   [11:0]  search_margin,
    input   [11:0]  bc_offset,
    input   [11:0]  reject_offset,
    input   [11:0]  rollover,
    input   [11:0]  coarse_count_offset,
    input           enable_relative_trigger_data,
    input           enable_matching,
    input           trigger_redge,
    input   [7:0]   trigger_latency,
    input   [15:0]  window_cycles,
    input   [9:0]   hit_threshold,
    input   [9:0]   hit_upper_threshold,
    input   [20:0]  fsm_watchdog_cycles,
    input   [39:0]  tdc_enable_mask,
    input   [39:0]  tdc_chamber1_mask,
    output  [21:0]  geometry_lookup_address,
    input   [95:0]  geometry_lookup_data,
    input           geometry_ready,
    input   [85:0]  tube_filter_settings,
    input   [31:0]  geometry_mls,
    input   [511:0] geometry_layers,
    output  [27:0] diagnostic_pulses,
    output  [11:0] diagnostic_fifo_lost_words,

    input   [19:0]  phase_sel_160M_20b[UPLINKCOUNT-1:0],

    output  [43:0]  total_received_40bit_dline1[UPLINKCOUNT-1:0][9:0],
    output  [43:0]  total_received_40bit_dline0[UPLINKCOUNT-1:0][9:0],
    output  [35:0]  total_error_bit_dline1[UPLINKCOUNT-1:0][9:0],
    output  [35:0]  total_error_bit_dline0[UPLINKCOUNT-1:0][9:0],
    output  [UPLINKCOUNT*TDC_COUNT_SINGLE*24*31-1:0] noise_hit_counts,




    //  ethernet interface
    input  tx_axis_clk,
    input  ethernet_programming_active,
    output [7:0] tx_axis_fifo_tdata,
    output tx_axis_fifo_tvalid,
    input  tx_axis_fifo_tready,
    output tx_axis_fifo_tlast,
    // Sum of both chamber readout FIFO occupancies.  This is
    // synchronous to tx_axis_clk and directly drives Ethernet TX QoS.
    output [15:0] hit_fifo_occupancy
);



// wire           bc_rst;
// wire           event_rst;
// wire           master_rst;

// wire           en_int_trigger;
// wire           enable_hit;
// wire           hit_inv;
// wire           hit_single;
// wire   [11:0]  width_hit;
// wire   [23:0]  hit_interval;

// wire   [19:0]  correct_counter_th;
// wire           enable_K28_1;
// wire           enable_320M;
// wire   [15:0]   trigger_deadtime;
// wire   [11:0]  match_window;
// wire   [11:0]  search_margin;
// wire   [11:0]  bc_offset;
// wire   [11:0]  reject_offset;
// wire   [11:0]  rollover;
// wire   [11:0]  coarse_count_offset;
// wire           enable_relative_trigger_data;
// wire           enable_matching;
// wire           trigger_redge;
// wire   [7:0]   trigger_latency;


localparam TDC_COUNT = TDC_COUNT_SINGLE*UPLINKCOUNT;
localparam TDC_DATA_WIDTH = 40;
localparam MODE_SWITCH_RESET_CYCLES = 8;

reg [11:0] trigger_coarse;


(* dont_touch = "true" *) wire [TDC_COUNT-1:0] locked_dline1;
(* dont_touch = "true" *) wire [TDC_COUNT-1:0] locked_dline0;
assign locked_dline1_o = locked_dline1;
assign locked_dline0_o = locked_dline0;

wire [TDC_COUNT-1:0] locked_dline;
assign locked_dline = locked_dline1&locked_dline0;

wire [TDC_COUNT-1:0] matching_busy;


wire [TDC_COUNT-1:0] tdc_fifo_read;
wire [TDC_COUNT-1:0] tdc_fifo_empty;
wire [TDC_COUNT*TDC_DATA_WIDTH-1:0] tdc_fifo_data;

wire tdc_fifo_empty_mux;
wire matching_busy_mux;
wire tdc_fifo_read_mux;
wire [TDC_DATA_WIDTH-1:0] tdc_fifo_data_mux;

wire [TDC_COUNT-1:0] triggerless_fifo_read;
wire [TDC_COUNT-1:0] triggerless_fifo_empty;
wire [TDC_COUNT*TDC_DATA_WIDTH-1:0] triggerless_fifo_data;
wire [TDC_COUNT-1:0] triggerless_fifoA_empty;
wire [TDC_COUNT-1:0] triggerless_fifoB_empty;
wire [TDC_COUNT-1:0] triggerless_fifo_empty_safe;
wire [TDC_COUNT-1:0] triggerless_overflowA;
wire [TDC_COUNT-1:0] triggerless_overflowB;
wire [TDC_COUNT-1:0] triggerless_overflow_word;
wire [TDC_COUNT*2*31-1:0] noise_error_counts;
wire [TDC_COUNT-1:0] chamber_tdc_mask [0:1];
wire [1:0] chamber_enable;
wire [TDC_COUNT-1:0] triggerless_fifo_read_group [0:1];
wire [1:0] triggerless_fifo_empty_mux;
wire [1:0] triggerless_fifo_read_mux;
wire [TDC_DATA_WIDTH-1:0] triggerless_fifo_data_mux [0:1];
wire [1:0] triggerless_fifoA_empty_global;
wire [1:0] triggerless_fifoB_empty_global;

wire [29:0] trigger_fifo_data;
wire trigger_fifo_empty;
wire [29:0] trigger_fifo_data_secondary;
wire trigger_fifo_empty_secondary;
wire [29:0] trigger_fifo_data_by_chamber [0:1];
wire [1:0] trigger_fifo_empty_by_chamber;
wire building_busy;
wire trigger_fifo_read;




wire [TDC_DATA_WIDTH-1:0] event_data;
wire event_data_ready;
wire [TDC_DATA_WIDTH-1:0] triggered_event_data;
wire triggered_event_data_ready;
wire [TDC_DATA_WIDTH-1:0] triggerless_event_data [0:1];
wire [1:0] triggerless_event_data_ready;
wire [TDC_DATA_WIDTH-1:0] noise_counter_data;
wire noise_counter_data_ready;
wire [TDC_DATA_WIDTH-1:0] readout_fifo_data [0:1];
wire [1:0] readout_fifo_empty;
wire [1:0] readout_fifo_full;
wire [1:0] readout_fifo_read;
wire [TDC_DATA_WIDTH-1:0] readout_write_data [0:1];
wire [1:0] readout_write_enable;
wire [14:0] readout_fifo_count [0:1];
wire [15:0] readout_fifo_count_sum;
wire [TDC_DATA_WIDTH-1:0] readout_data_arb;
wire readout_data_ready_arb;
wire readout_data_read_arb;
wire [1:0] readout_source_enable_40;
wire [1:0] readout_source_enable_tx;
wire readout_framed_mode_40;
wire readout_framed_mode_tx;
wire [2:0] readout_control_tx;
wire packet_done;
//vio for ethernet enable
wire packet_rst;
wire readout_arbiter_rst_tx;
wire packet_enable;




// wire global_rst;
wire fpga_bcr;
wire rst_40;


// wire ttc_bc_reset_vio;
// wire ttc_event_reset_vio;
// wire ttc_master_reset_vio;


// assign bc_rst = ttc_bc_reset_vio;
// assign event_rst = ttc_event_reset_vio;
// assign master_rst = ttc_master_reset_vio;

//vio for hit generator




wire [23:0] hit_mask;
wire [23:0] delay_mask;
wire [11:0] hit_delay;
wire [11:0] hit_trigger_ratio;
wire trigger_internal;



// reg srst_160;
wire rst_40_vio;
wire trigger_detect;
wire trigger_delayed;





wire trigger_fifo_read_triggermode;
wire trigger_fifo_read_triggerless;
wire trigger_fifo_read_triggered;
wire [1:0] trigger_fifo_read_byhit;
wire [TDC_COUNT-1:0] tdc_fifo_read_triggermode;
wire [TDC_COUNT-1:0] tdc_fifo_read_triggerless;
wire [TDC_DATA_WIDTH-1:0] event_data_triggermode;
wire [TDC_DATA_WIDTH-1:0] event_data_trigger_matching;
wire event_data_ready_triggermode;
wire event_data_ready_trigger_matching;
wire mode_switch_rst;
wire mode_switch_detect;
wire readout_fifo_rst;
wire [1:0] triggerless_wr_bank_sel;
wire [1:0] triggerless_rd_bank_sel;
wire [1:0] triggerless_drop_hits;
wire [1:0] triggerless_clr_hit_fifos;
wire [1:0] triggerless_clr_trig_fifo;
wire [TDC_COUNT-1:0] triggerless_run_enable_tdc;
wire [TDC_COUNT-1:0] triggerless_wr_bank_sel_tdc;
wire [TDC_COUNT-1:0] triggerless_rd_bank_sel_tdc;
wire [TDC_COUNT-1:0] triggerless_drop_hits_tdc;
wire [TDC_COUNT-1:0] triggerless_clr_hit_fifos_tdc;
wire stream_hits_only_eff;
wire noise_counter_reset;
wire trigger_interface_run_enable;
wire trigger_interface_clr_trig_fifo;
wire trigger_interface_clr_trig_fifo_secondary;
reg acquisition_mode_d_40;
reg run_enable_d_40;
reg [3:0] mode_switch_rst_count;

// Triggerless events are hit-driven, but external trigger words are still included.
assign trigger_detect = acquisition_mode ? trigger_in : (en_int_trigger?trigger_internal:trigger_in);
// Do not begin a new hit-data frame while Ethernet owns the link for JTAG
// programming.  data_packet checks enable only in IDLE, so a frame already in
// progress still finishes cleanly.
assign packet_enable = ~ethernet_programming_active;
assign trigger_fifo_read_triggered = enable_matching?trigger_fifo_read_triggerless:trigger_fifo_read_triggermode;
assign triggered_event_data = enable_matching?event_data_trigger_matching:event_data_triggermode;
assign triggered_event_data_ready = enable_matching?event_data_ready_trigger_matching:event_data_ready_triggermode;

assign chamber_tdc_mask[0] = tdc_enable_mask[TDC_COUNT-1:0] &
                             ~tdc_chamber1_mask[TDC_COUNT-1:0];
assign chamber_tdc_mask[1] = tdc_enable_mask[TDC_COUNT-1:0] &
                              tdc_chamber1_mask[TDC_COUNT-1:0];
assign chamber_enable = {|chamber_tdc_mask[1], |chamber_tdc_mask[0]};
assign trigger_fifo_data_by_chamber[0] = trigger_fifo_data;
assign trigger_fifo_data_by_chamber[1] = trigger_fifo_data_secondary;
assign trigger_fifo_empty_by_chamber =
    {trigger_fifo_empty_secondary, trigger_fifo_empty};

assign trigger_fifo_read = acquisition_mode ? trigger_fifo_read_byhit[0] : trigger_fifo_read_triggered;
assign tdc_fifo_read = enable_matching?tdc_fifo_read_triggerless:tdc_fifo_read_triggermode;
assign event_data = acquisition_mode ?
                    (noise_counter_stream ? noise_counter_data : triggerless_event_data[0]) :
                    triggered_event_data;
assign event_data_ready = acquisition_mode ?
                          (noise_counter_stream ? noise_counter_data_ready :
                           triggerless_event_data_ready[0]) :
                          triggered_event_data_ready;
assign triggerless_fifo_read = triggerless_fifo_read_group[0] |
                               triggerless_fifo_read_group[1];
assign triggerless_fifo_empty_safe = triggerless_fifo_empty | ~locked_dline;
assign stream_hits_only_eff = stream_hits_only & ~noise_counter_stream;
assign mode_switch_detect = acquisition_mode ^ acquisition_mode_d_40;
assign mode_switch_rst = mode_switch_detect | (mode_switch_rst_count != 0);
assign readout_fifo_rst = rst_40 | mode_switch_rst | (acquisition_mode & ~run_enable);
assign noise_counter_reset = noise_counter_clear | mode_switch_rst | (run_enable & ~run_enable_d_40);
assign trigger_interface_run_enable = acquisition_mode ? run_enable : 1'b1;
assign trigger_interface_clr_trig_fifo =
    mode_switch_rst | (acquisition_mode ? triggerless_clr_trig_fifo[0] : 1'b0);
assign trigger_interface_clr_trig_fifo_secondary =
    mode_switch_rst | (acquisition_mode ? triggerless_clr_trig_fifo[1] : 1'b0);
assign readout_source_enable_40 =
    (!acquisition_mode || noise_counter_stream) ? 2'b01 : chamber_enable;
assign readout_framed_mode_40 = ~(acquisition_mode & stream_hits_only_eff);
assign {readout_framed_mode_tx, readout_source_enable_tx} = readout_control_tx;
assign readout_write_data[0] = event_data;
assign readout_write_data[1] = triggerless_event_data[1];
assign readout_write_enable = {triggerless_event_data_ready[1], event_data_ready};
assign readout_fifo_count_sum = {1'b0, readout_fifo_count[0]} +
                                {1'b0, readout_fifo_count[1]};
assign hit_fifo_occupancy = readout_fifo_count_sum;
assign packet_done = tx_axis_fifo_tvalid & tx_axis_fifo_tready &
                     tx_axis_fifo_tlast;

genvar route_tdc;
generate
for (route_tdc = 0; route_tdc < TDC_COUNT; route_tdc = route_tdc + 1) begin : route_tdc_to_chamber
    wire chamber_select = chamber_tdc_mask[1][route_tdc];
    wire tdc_enabled = tdc_enable_mask[route_tdc];

    assign triggerless_run_enable_tdc[route_tdc] = run_enable & tdc_enabled;
    assign triggerless_wr_bank_sel_tdc[route_tdc] =
        chamber_select ? triggerless_wr_bank_sel[1] : triggerless_wr_bank_sel[0];
    assign triggerless_rd_bank_sel_tdc[route_tdc] =
        chamber_select ? triggerless_rd_bank_sel[1] : triggerless_rd_bank_sel[0];
    assign triggerless_drop_hits_tdc[route_tdc] =
        !tdc_enabled ? 1'b1 :
        (chamber_select ? triggerless_drop_hits[1] : triggerless_drop_hits[0]);
    assign triggerless_clr_hit_fifos_tdc[route_tdc] =
        !tdc_enabled ? 1'b1 :
        (chamber_select ? triggerless_clr_hit_fifos[1] :
                          triggerless_clr_hit_fifos[0]);
end
endgenerate




// (* dont_touch = "true" *) wire [43:0] total_received_40bit_dline1[UPLINKCOUNT-1:0][9:0];
// (* dont_touch = "true" *) wire [43:0] total_received_40bit_dline0[UPLINKCOUNT-1:0][9:0];
// (* dont_touch = "true" *) wire [35:0] total_error_bit_dline1[UPLINKCOUNT-1:0][9:0];
// (* dont_touch = "true" *) wire [35:0] total_error_bit_dline0[UPLINKCOUNT-1:0][9:0];
// (* dont_touch = "true" *) wire [19:0] phase_sel_160M_20b[UPLINKCOUNT-1:0];



// genvar n;
// for (n = 0; n < UPLINKCOUNT; n++) begin: uplink
//     vio_BER vio_BER_inst (
//       .clk(clk_40),                // input wire clk
//       .probe_in0 (total_received_40bit_dline1[n][0]),    // input wire [43 : 0] probe_in0
//       .probe_in1 (total_received_40bit_dline0[n][0]),    // input wire [43 : 0] probe_in1
//       .probe_in2 (total_error_bit_dline1[n][0]),      // input wire [35 : 0] probe_in2
//       .probe_in3 (total_error_bit_dline0[n][0]),      // input wire [35 : 0] probe_in3
//       .probe_in4 (total_received_40bit_dline1[n][1]),     // input wire [43 : 0] probe_in4
//       .probe_in5 (total_received_40bit_dline0[n][1]),     // input wire [43 : 0] probe_in5
//       .probe_in6 (total_error_bit_dline1[n][1]),          // input wire [35 : 0] probe_in6
//       .probe_in7 (total_error_bit_dline0[n][1]),          // input wire [35 : 0] probe_in7
//       .probe_in8 (total_received_40bit_dline1[n][2]),    // input wire [43 : 0] probe_in8
//       .probe_in9 (total_received_40bit_dline0[n][2]),    // input wire [43 : 0] probe_in9
//       .probe_in10(total_error_bit_dline1[n][2]),        // input wire [35 : 0] probe_in10
//       .probe_in11(total_error_bit_dline0[n][2]),        // input wire [35 : 0] probe_in11
//       .probe_in12(total_received_40bit_dline1[n][3]),   // input wire [43 : 0] probe_in12
//       .probe_in13(total_received_40bit_dline0[n][3]),   // input wire [43 : 0] probe_in13
//       .probe_in14(total_error_bit_dline1[n][3]),        // input wire [35 : 0] probe_in14
//       .probe_in15(total_error_bit_dline0[n][3]),        // input wire [35 : 0] probe_in15
//       .probe_in16(total_received_40bit_dline1[n][4]),   // input wire [43 : 0] probe_in16
//       .probe_in17(total_received_40bit_dline0[n][4]),   // input wire [43 : 0] probe_in17
//       .probe_in18(total_error_bit_dline1[n][4]),        // input wire [35 : 0] probe_in18
//       .probe_in19(total_error_bit_dline0[n][4]),        // input wire [35 : 0] probe_in19
//       .probe_in20(total_received_40bit_dline1[n][5]),   // input wire [43 : 0] probe_in20
//       .probe_in21(total_received_40bit_dline0[n][5]),   // input wire [43 : 0] probe_in21
//       .probe_in22(total_error_bit_dline1[n][5]),        // input wire [35 : 0] probe_in22
//       .probe_in23(total_error_bit_dline0[n][5]),        // input wire [35 : 0] probe_in23
//       .probe_in24(total_received_40bit_dline1[n][6]),   // input wire [43 : 0] probe_in24
//       .probe_in25(total_received_40bit_dline0[n][6]),   // input wire [43 : 0] probe_in25
//       .probe_in26(total_error_bit_dline1[n][6]),        // input wire [35 : 0] probe_in26
//       .probe_in27(total_error_bit_dline0[n][6]),        // input wire [35 : 0] probe_in27
//       .probe_in28(total_received_40bit_dline1[n][7]),   // input wire [43 : 0] probe_in28
//       .probe_in29(total_received_40bit_dline0[n][7]),   // input wire [43 : 0] probe_in29
//       .probe_in30(total_error_bit_dline1[n][7]),        // input wire [35 : 0] probe_in30
//       .probe_in31(total_error_bit_dline0[n][7]),        // input wire [35 : 0] probe_in31
//       .probe_in32(total_received_40bit_dline1[n][8]),   // input wire [43 : 0] probe_in32
//       .probe_in33(total_received_40bit_dline0[n][8]),   // input wire [43 : 0] probe_in33
//       .probe_in34(total_error_bit_dline1[n][8]),        // input wire [35 : 0] probe_in34
//       .probe_in35(total_error_bit_dline0[n][8]),        // input wire [35 : 0] probe_in35
//       .probe_in36(total_received_40bit_dline1[n][9]),   // input wire [43 : 0] probe_in36
//       .probe_in37(total_received_40bit_dline0[n][9]),   // input wire [43 : 0] probe_in37
//       .probe_in38(total_error_bit_dline1[n][9]),        // input wire [35 : 0] probe_in38
//       .probe_in39(total_error_bit_dline0[n][9]),        // input wire [35 : 0] probe_in39
//       .probe_out0(phase_sel_160M_20b[n])  // output wire [19 : 0] probe_out0
//     );
// end


xpm_cdc_sync_rst #(
 .DEST_SYNC_FF   (5),
 .INIT           (1),
 .INIT_SYNC_FF   (0),
 .SIM_ASSERT_CHK (1)
) r40_rst_sync (
 .src_rst  (rst_in),
 .dest_clk (clk_40),
 .dest_rst (rst_40)
);

xpm_cdc_sync_rst #(
 .DEST_SYNC_FF   (5),
 .INIT           (1),
 .INIT_SYNC_FF   (0),
 .SIM_ASSERT_CHK (1)
) pck_rst_sync (
 .src_rst  (rst_40),
 .dest_clk (tx_axis_clk),
 .dest_rst (packet_rst)
);

xpm_cdc_sync_rst #(
 .DEST_SYNC_FF   (5),
 .INIT           (1),
 .INIT_SYNC_FF   (0),
 .SIM_ASSERT_CHK (1)
) readout_arbiter_rst_sync (
 .src_rst  (readout_fifo_rst),
 .dest_clk (tx_axis_clk),
 .dest_rst (readout_arbiter_rst_tx)
);

xpm_cdc_array_single #(
 .DEST_SYNC_FF   (2),
 .INIT_SYNC_FF   (0),
 .SIM_ASSERT_CHK (1),
 .SRC_INPUT_REG  (1),
 .WIDTH          (3)
) readout_source_enable_cdc (
 .src_clk  (clk_40),
 .src_in   ({readout_framed_mode_40, readout_source_enable_40}),
 .dest_clk (tx_axis_clk),
 .dest_out (readout_control_tx)
);


always @(posedge clk_40 ) begin
    if (rst_40|fpga_bcr) begin
        // reset
        trigger_coarse <= coarse_count_offset;
    end else begin
        trigger_coarse <= trigger_coarse == rollover ? 'b0 : trigger_coarse + 1'b1;
    end 
end

always @(posedge clk_40) begin
    if (rst_40) begin
        acquisition_mode_d_40 <= acquisition_mode;
        run_enable_d_40       <= 1'b0;
        mode_switch_rst_count <= 4'd0;
    end else begin
        acquisition_mode_d_40 <= acquisition_mode;
        run_enable_d_40       <= run_enable;

        if (mode_switch_detect)
            mode_switch_rst_count <= MODE_SWITCH_RESET_CYCLES - 1;
        else if (mode_switch_rst_count != 0)
            mode_switch_rst_count <= mode_switch_rst_count - 1'b1;
    end
end


trigger_interface inst_trigger_interface
(
    .clk_40              (clk_40),
    // Keep the trigger timestamp aligned with TDC BCIDs across a mode switch.
    // mode_switch_rst clears the trigger FIFO through clr_trig_fifo instead.
    .rst_40              (rst_40),
    .mode_switch_rst     (mode_switch_rst),
    .run_enable          (trigger_interface_run_enable),
    .clr_trig_fifo       (trigger_interface_clr_trig_fifo),
    .secondary_enable    (acquisition_mode & chamber_enable[1]),
    .clr_trig_fifo_secondary(trigger_interface_clr_trig_fifo_secondary),
    .bc_reset            (fpga_bcr),
    .event_reset         (event_rst),
    .trigger_in          (trigger_detect),
    .trigger_ready_out   (trigger_delayed),
    .trigger_read        (trigger_fifo_read),
    .trigger_read_secondary(trigger_fifo_read_byhit[1]),
    .trigger_fifo_data   (trigger_fifo_data),
    .trigger_fifo_empty  (trigger_fifo_empty),
    .trigger_fifo_data_secondary(trigger_fifo_data_secondary),
    .trigger_fifo_empty_secondary(trigger_fifo_empty_secondary),
    // .trigger_coarse      (trigger_coarse),
    .trigger_redge       (trigger_redge),
    .rollover            (rollover),
    .coarse_count_offset (coarse_count_offset),
    .trigger_latency     (trigger_latency),
    .trigger_deadtime    (trigger_deadtime)
);

// assign trigger_fifo_data = 'b0;
// assign trigger_fifo_empty = 'b1;
// assign trigger_coarse = 'b0;



genvar i;
for (i = 0; i < UPLINKCOUNT; i++) begin:tdc_inst

tdcv2_decoder_wrapper #(
        .TDC_COUNT(TDC_COUNT_SINGLE),
        .IS_MASTER((i+1)%2),
        .CSM_ID(i/2),
        .TDC_DATA_WIDTH(TDC_DATA_WIDTH)
) tdcv2_decoder_wrapper (
    .clk_40                       (clk_40),
    .rst_40                       (rst_40),
    .pipeline_rst                 (mode_switch_rst),
    .userDataUpLink_i             (userDataUpLink[i]),
    .correct_counter_th           (correct_counter_th),
    .enable_K28_1                 (enable_K28_1),
    .enable_320M                  (enable_320M),
    .phase_sel_160M_20b           (phase_sel_160M_20b[i]),
    .locked_dline1                (locked_dline1[TDC_COUNT_SINGLE*(i+1)-1:TDC_COUNT_SINGLE*i]),
    .locked_dline0                (locked_dline0[TDC_COUNT_SINGLE*(i+1)-1:TDC_COUNT_SINGLE*i]),

    // .sys_clk_160                  (sys_clk_160),
    // .rst_160                      (rst_160),
    .tdc_fifo_read                (tdc_fifo_read[TDC_COUNT_SINGLE*(i+1)-1:TDC_COUNT_SINGLE*i]),
    .tdc_fifo_empty               (tdc_fifo_empty[TDC_COUNT_SINGLE*(i+1)-1:TDC_COUNT_SINGLE*i]),
    .tdc_fifo_data                (tdc_fifo_data[TDC_COUNT_SINGLE*TDC_DATA_WIDTH*(i+1)-1:TDC_COUNT_SINGLE*TDC_DATA_WIDTH*i]),
    .matching_busy                (matching_busy[TDC_COUNT_SINGLE*(i+1)-1:TDC_COUNT_SINGLE*i]),
    .acquisition_mode             (acquisition_mode),
    .triggerless_run_enable       (triggerless_run_enable_tdc[TDC_COUNT_SINGLE*(i+1)-1:TDC_COUNT_SINGLE*i]),
    .triggerless_clr_hit_fifos    (triggerless_clr_hit_fifos_tdc[TDC_COUNT_SINGLE*(i+1)-1:TDC_COUNT_SINGLE*i]),
    .triggerless_noise_counter_clear(noise_counter_reset),
    .triggerless_wr_bank_sel      (triggerless_wr_bank_sel_tdc[TDC_COUNT_SINGLE*(i+1)-1:TDC_COUNT_SINGLE*i]),
    .triggerless_rd_bank_sel      (triggerless_rd_bank_sel_tdc[TDC_COUNT_SINGLE*(i+1)-1:TDC_COUNT_SINGLE*i]),
    .triggerless_drop_hits        (triggerless_drop_hits_tdc[TDC_COUNT_SINGLE*(i+1)-1:TDC_COUNT_SINGLE*i]),
    .triggerless_fifo_read        (triggerless_fifo_read[TDC_COUNT_SINGLE*(i+1)-1:TDC_COUNT_SINGLE*i]),
    .triggerless_fifo_empty       (triggerless_fifo_empty[TDC_COUNT_SINGLE*(i+1)-1:TDC_COUNT_SINGLE*i]),
    .triggerless_fifo_data        (triggerless_fifo_data[TDC_COUNT_SINGLE*TDC_DATA_WIDTH*(i+1)-1:TDC_COUNT_SINGLE*TDC_DATA_WIDTH*i]),
    .triggerless_fifoA_empty      (triggerless_fifoA_empty[TDC_COUNT_SINGLE*(i+1)-1:TDC_COUNT_SINGLE*i]),
    .triggerless_fifoB_empty      (triggerless_fifoB_empty[TDC_COUNT_SINGLE*(i+1)-1:TDC_COUNT_SINGLE*i]),
    .triggerless_overflowA        (triggerless_overflowA[TDC_COUNT_SINGLE*(i+1)-1:TDC_COUNT_SINGLE*i]),
    .triggerless_overflowB        (triggerless_overflowB[TDC_COUNT_SINGLE*(i+1)-1:TDC_COUNT_SINGLE*i]),
    .triggerless_overflow_word    (triggerless_overflow_word[TDC_COUNT_SINGLE*(i+1)-1:TDC_COUNT_SINGLE*i]),
    .noise_hit_counts             (noise_hit_counts[TDC_COUNT_SINGLE*24*31*(i+1)-1:TDC_COUNT_SINGLE*24*31*i]),
    .noise_error_counts           (noise_error_counts[TDC_COUNT_SINGLE*2*31*(i+1)-1:TDC_COUNT_SINGLE*2*31*i]),
    .enable_matching              (enable_matching),
    .enable_matching_timeout      (1'b1),
    .trigger_fifo_data            (trigger_fifo_data[16:0]),
    .trigger_fifo_empty           (trigger_fifo_empty),
    .building_busy                (building_busy),
    .trigger_coarse               (trigger_coarse),
    .match_window                 (match_window),
    .search_margin                (search_margin),
    .bc_offset                    (bc_offset),
    .reject_offset                (reject_offset),
    .rollover                     (rollover),
    .enable_relative_trigger_data (enable_relative_trigger_data),

    .total_received_40bit_dline1 (total_received_40bit_dline1[i]),
    .total_received_40bit_dline0 (total_received_40bit_dline0[i]),
    .total_error_bit_dline1      (total_error_bit_dline1[i]),
    .total_error_bit_dline0      (total_error_bit_dline0[i])
);
end


tdc_fifo_data_mux #(
    .TDC_COUNT(TDC_COUNT),
    .TDC_DATA_WIDTH(TDC_DATA_WIDTH)
) inst_tdc_fifo_data_mux (
    .locked             (locked_dline),
    .tdc_fifo_empty     (tdc_fifo_empty),
    .tdc_fifo_data      (tdc_fifo_data),
    .matching_busy      (matching_busy),
    .tdc_fifo_read      (tdc_fifo_read_triggerless),

    .tdc_fifo_empty_mux (tdc_fifo_empty_mux),
    .tdc_fifo_data_mux  (tdc_fifo_data_mux),
    .matching_busy_mux  (matching_busy_mux),
    .tdc_fifo_read_mux  (tdc_fifo_read_mux)
);


event_builder inst_event_builder_trigger_matching
(
    .clk                (clk_40),
    .rst                (rst_40 | mode_switch_rst),
    .enable             (~acquisition_mode & enable_matching),
    .trigger_fifo_empty (trigger_fifo_empty),
    .trigger_fifo_data  (trigger_fifo_data),
    .trigger_fifo_read  (trigger_fifo_read_triggerless),
    .tdc_fifo_empty     (tdc_fifo_empty_mux),
    .tdc_fifo_data      (tdc_fifo_data_mux),
    .matching_busy      (matching_busy_mux),
    .tdc_fifo_read      (tdc_fifo_read_mux),
    .readout_fifo_full  (readout_fifo_full[0]),
    .event_data         (event_data_trigger_matching),
    .event_data_ready   (event_data_ready_trigger_matching),
    .building_busy      (building_busy)
);



event_builder_triggermode #(
        .TDC_COUNT(TDC_COUNT),
        .TDC_DATA_WIDTH(TDC_DATA_WIDTH)
) inst_event_builder_triggermode (
    .clk                  (clk_40),
    .rst                  (rst_40 | mode_switch_rst),
    .enable               (~acquisition_mode & ~enable_matching),

    .trigger_fifo_empty   (trigger_fifo_empty),
    .trigger_fifo_data    (trigger_fifo_data),
    .trigger_fifo_read    (trigger_fifo_read_triggermode),

    .locked_array         (locked_dline),
    .tdc_fifo_empty_array (tdc_fifo_empty),
    .tdc_fifo_data_array  (tdc_fifo_data),
    .tdc_fifo_read_array  (tdc_fifo_read_triggermode),
    
    .readout_fifo_full    (readout_fifo_full[0]),
    .event_data           (event_data_triggermode),
    .event_data_ready     (event_data_ready_triggermode)
);

// Each chamber owns an independent hit mux and event builder.  The same
// physical per-TDC FIFO can only be selected by one mux because the masks are
// disjoint; the two one-hot read vectors are ORed above.
genvar chamber_index;
generate
for (chamber_index = 0; chamber_index < 2; chamber_index = chamber_index + 1) begin : triggerless_chamber
    // Up to forty TDCs can lose a word on the same edge. Count all of them.
    reg [5:0] fifo_losses;
    integer loss_tdc;
    always @(*) begin
        fifo_losses = 0;
        for (loss_tdc=0; loss_tdc<TDC_COUNT; loss_tdc=loss_tdc+1)
            fifo_losses = fifo_losses + (triggerless_overflow_word[loss_tdc] &&
                                         chamber_tdc_mask[chamber_index][loss_tdc]);
    end
    assign diagnostic_fifo_lost_words[chamber_index*6 +: 6] =
        acquisition_mode && !stream_hits_only && !noise_counter_stream ? fifo_losses : 6'd0;
    wire [39:0] head_word = triggerless_fifo_data_mux[chamber_index];
    wire [7:0] global_tdc = {3'b0, head_word[36:32]} + head_word[39:37] * 8'd20;
    // Out-of-range physical TDC/channel addresses resolve to an invalid entry.
    assign geometry_lookup_address[chamber_index*11 +: 11] =
        head_word[39:37] < 2 && head_word[36:32] < 20 && head_word[31:27] < 24 ?
        {global_tdc[5:0], head_word[31:27]} : 11'h7ff;
    tdc_fifo_data_rr_mux #(
        .TDC_COUNT(TDC_COUNT),
        .TDC_DATA_WIDTH(TDC_DATA_WIDTH)
    ) inst_triggerless_fifo_rr_mux (
        .clk                 (clk_40),
        .rst                 (rst_40 | mode_switch_rst | ~acquisition_mode),
        .locked              (locked_dline & chamber_tdc_mask[chamber_index]),
        .tdc_fifo_empty      (triggerless_fifo_empty_safe),
        .tdc_fifo_data       (triggerless_fifo_data),
        .fifoA_empty         (triggerless_fifoA_empty),
        .fifoB_empty         (triggerless_fifoB_empty),
        .tdc_fifo_read_mux   (triggerless_fifo_read_mux[chamber_index]),
        .tdc_fifo_read       (triggerless_fifo_read_group[chamber_index]),
        .tdc_fifo_empty_mux  (triggerless_fifo_empty_mux[chamber_index]),
        .tdc_fifo_data_mux   (triggerless_fifo_data_mux[chamber_index]),
        .fifoA_empty_mux     (triggerless_fifoA_empty_global[chamber_index]),
        .fifoB_empty_mux     (triggerless_fifoB_empty_global[chamber_index])
    );

    event_builder_byhit #(
        .PREBUF_DEPTH(256),
        .TDC_COUNT(TDC_COUNT),
        .CHAMBER_ID(chamber_index),
        .ENABLE_ILA(chamber_index == 0)
    ) inst_event_builder_byhit (
        .clk                 (clk_40),
        .rst                 (rst_40 | mode_switch_rst),
        .enable              (acquisition_mode & chamber_enable[chamber_index]),
        .run_enable          (run_enable),
        .stream_hits_only    (stream_hits_only_eff),
        .stream_counts_only  (noise_counter_stream),
        .window_cycles       (window_cycles),
        .hit_threshold       (hit_threshold),
        .hit_upper_threshold (hit_upper_threshold),
        .fsm_watchdog_cycles (fsm_watchdog_cycles),
        .geometry_ready      (geometry_ready),
        .hit_geometry        (geometry_lookup_data[chamber_index*48 +: 48]),
        .filter_settings     (tube_filter_settings[chamber_index*43 +: 43]),
        .selected_mls        (geometry_mls[chamber_index*16 +: 16]),
        .selected_layers     (geometry_layers[chamber_index*256 +: 256]),
        .trigger_fifo_empty  (trigger_fifo_empty_by_chamber[chamber_index]),
        .trigger_fifo_data   (trigger_fifo_data_by_chamber[chamber_index]),
        .trigger_fifo_read   (trigger_fifo_read_byhit[chamber_index]),
        .fifoA_empty         (triggerless_fifoA_empty_global[chamber_index]),
        .fifoB_empty         (triggerless_fifoB_empty_global[chamber_index]),
        .overflowA           (triggerless_overflowA & chamber_tdc_mask[chamber_index]),
        .overflowB           (triggerless_overflowB & chamber_tdc_mask[chamber_index]),
        .tdc_fifo_empty      (triggerless_fifo_empty_mux[chamber_index]),
        .tdc_fifo_data       (triggerless_fifo_data_mux[chamber_index]),
        .tdc_fifo_read       (triggerless_fifo_read_mux[chamber_index]),
        .wr_bank_sel         (triggerless_wr_bank_sel[chamber_index]),
        .rd_bank_sel         (triggerless_rd_bank_sel[chamber_index]),
        .drop_hits           (triggerless_drop_hits[chamber_index]),
        .clr_hit_fifos       (triggerless_clr_hit_fifos[chamber_index]),
        .clr_trig_fifo       (triggerless_clr_trig_fifo[chamber_index]),
        .readout_fifo_full   (readout_fifo_full[chamber_index]),
        .event_data          (triggerless_event_data[chamber_index]),
        .event_data_ready    (triggerless_event_data_ready[chamber_index]),
        .diagnostic_pulses   (diagnostic_pulses[chamber_index*14 +: 14])
    );
end
endgenerate

noise_counter_streamer #(
    .TDC_COUNT(TDC_COUNT),
    .TDC_PER_CSM(20),
    .CHANNELS_PER_TDC(24),
    .COUNTER_WIDTH(31),
    .SAMPLE_PERIOD_CYCLES(40000000)
) inst_noise_counter_streamer (
    .clk                 (clk_40),
    .rst                 (rst_40 | mode_switch_rst),
    .enable              (acquisition_mode & run_enable & noise_counter_stream),
    .counter_reset       (noise_counter_reset),
    .locked_tdc          (locked_dline & tdc_enable_mask[TDC_COUNT-1:0]),
    .noise_hit_counts    (noise_hit_counts),
    .noise_error_counts  (noise_error_counts),
    .readout_fifo_full   (readout_fifo_full[0]),
    .counter_data        (noise_counter_data),
    .counter_data_ready  (noise_counter_data_ready)
);


genvar readout_chamber;
generate
for (readout_chamber = 0; readout_chamber < 2;
     readout_chamber = readout_chamber + 1) begin : chamber_readout_fifo
    readout_fifo readout_fifo_inst (
        // Independent write/read clocks; generated FIFO synchronizes reset
        // release in both domains.
        .rst(readout_fifo_rst),
        .wr_clk(clk_40),
        .rd_clk(tx_axis_clk),
        .din(readout_write_data[readout_chamber]),
        .wr_en(readout_write_enable[readout_chamber]),
        .rd_en(readout_fifo_read[readout_chamber]),
        .dout(readout_fifo_data[readout_chamber]),
        .full(readout_fifo_full[readout_chamber]),
        .empty(readout_fifo_empty[readout_chamber]),
        .rd_data_count(readout_fifo_count[readout_chamber]),
        .wr_rst_busy(),
        .rd_rst_busy()
    );
end
endgenerate


single_ttc_generator inst_single_ttc_generator
(
    .clk_40            (clk_40),
    .rst_40            (rst_40),
    .encode_ttc        (encode_ttc),
    .fpga_bcr          (fpga_bcr),
    .trigger           (trigger_delayed&(~acquisition_mode)&(~enable_matching)),
    .bc_reset          (bc_rst),
    .event_reset       (event_rst),
    .master_reset      (master_rst)
);

readout_chamber_arbiter inst_readout_chamber_arbiter (
    .clk             (tx_axis_clk),
    .rst             (readout_arbiter_rst_tx),
    .source_enable   (readout_source_enable_tx),
    .event_framed    (readout_framed_mode_tx),
    .fifo0_data      (readout_fifo_data[0]),
    .fifo0_empty     (readout_fifo_empty[0]),
    .fifo0_read      (readout_fifo_read[0]),
    .fifo1_data      (readout_fifo_data[1]),
    .fifo1_empty     (readout_fifo_empty[1]),
    .fifo1_read      (readout_fifo_read[1]),
    .output_data     (readout_data_arb),
    .output_ready    (readout_data_ready_arb),
    .output_read     (readout_data_read_arb),
    .packet_done     (packet_done)
);


data_packet data_packet_inst (
    .clk(tx_axis_clk),
    .rst(packet_rst),
    .enable(packet_enable),
    .TDC_fifo_data(readout_data_arb),
    .TDC_data_ready(readout_data_ready_arb),
    .TDC_data_rd(readout_data_read_arb),
    
    .data_to_eth(tx_axis_fifo_tdata),
    .packet_valid(tx_axis_fifo_tvalid),
    .tx_axis_fifo_tready(tx_axis_fifo_tready),
    .last(tx_axis_fifo_tlast)
);





trigger_generator inst_trigger_generator
(
    .clk          (clk_40),
    .rst          (rst_40),
    .enable       (en_int_trigger),
    .trigger_out  (trigger_internal),
    .width        (width_hit),
    .start        (enable_hit),
    .inv          (hit_inv),
    .interval     (hit_interval),
    .start_single (hit_single)
);



// vio_trigger vio_trigger_inst (
//     .clk(clk_asyn),                // input wire clk
//     .probe_out0(rst_40_vio),  // output wire [0 : 0] probe_out0
//     .probe_out1(trigger_deadtime),  // output wire [7 : 0] probe_out1
//     .probe_out2(match_window),  // output wire [11 : 0] probe_out2
//     .probe_out3(search_margin),  // output wire [11 : 0] probe_out3
//     .probe_out4(bc_offset),  // output wire [11 : 0] probe_out4
//     .probe_out5(reject_offset),  // output wire [11 : 0] probe_out5
//     .probe_out6(rollover),  // output wire [11 : 0] probe_out6
//     .probe_out7(coarse_count_offset), // output wire [11 : 0] probe_out7
//     .probe_out8(enable_relative_trigger_data),  // output wire [0 : 0] probe_out8
//     .probe_out9(enable_matching),  // output wire [0 : 0] probe_out9
//     .probe_out10(trigger_redge),  // output wire [0 : 0]
//     .probe_out11(trigger_latency) // output wire [7 : 0]
// );

// vio_hit_output vio_hit_output_inst (
//     .clk(clk_asyn),                // input wire clk
//     .probe_out0(enable_hit),  // output wire [0 : 0] probe_out0
//     .probe_out1(enable_internal_trigger),  // output wire [0 : 0] probe_out1
//     .probe_out2(hit_inv),  // output wire [0 : 0] probe_out2
//     .probe_out3(width_hit),  // output wire [11 : 0] probe_out3
//     .probe_out4(hit_interval),  // output wire [11 : 0] probe_out4
//     .probe_out5(hit_mask),  // output wire [23 : 0] probe_out5
//     .probe_out6(hit_single),  // output wire [0 : 0] probe_out6
//     .probe_out7(hit_delay),  // output wire [11 : 0] probe_out7
//     .probe_out8(delay_mask), // output wire [23 : 0] probe_out8
//     .probe_out9(hit_trigger_ratio) // output wire [11 : 0] probe_out9
// );



// vio_40M vio_40M_inst (
//     .clk(clk_asyn),                // input wire clk
//     .probe_in0({{(40-TDC_COUNT){1'b0}},locked_dline1}),    // input wire [9 : 0] probe_in0
//     .probe_in1({{(40-TDC_COUNT){1'b0}},locked_dline0}),    // input wire [9 : 0] probe_in1

//     .probe_out0(global_rst),  // output wire [0 : 0] probe_out0
//     .probe_out1(correct_counter_th),  // output wire [19 : 0] probe_out1
//     .probe_out2(enable_K28_1),  // output wire [0 : 0] probe_out2
//     .probe_out3(ttc_bc_reset_vio),  // output wire [0 : 0] probe_out3
//     .probe_out4(ttc_event_reset_vio),  // output wire [0 : 0] probe_out4
//     .probe_out5(ttc_master_reset_vio),  // output wire [0 : 0] probe_out5
//     .probe_out6(enable_320M),  // output wire [0 : 0] probe_out6
//     .probe_out7(mezz_TRST) // output wire [0 : 0] probe_out7
// );



endmodule
