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
// File   : tdcv2_decoder_wrapper.sv
// Create : 2021-03-10 14:45:53
// Revise : 2026-07-29 14:32:15
// Editor : sublime text4, tab size (4)
// Description: 
//
// -----------------------------------------------------------------------------

module tdcv2_decoder_wrapper
#(parameter TDC_COUNT = 10,
            IS_MASTER = 1,
            CSM_ID    = 0,
       TDC_DATA_WIDTH = 40)
    (
    //clk_40 aligned
    input                   clk_40,
    input                   rst_40,
    input                   pipeline_rst,
    input   [229:0]         userDataUpLink_i,
    input   [19:0]          correct_counter_th,
    input                   enable_K28_1,
    input                   enable_320M,
    input   [19:0]          phase_sel_160M_20b,
    output  [TDC_COUNT-1:0] locked_dline1,
    output  [TDC_COUNT-1:0] locked_dline0, 

    //sys_clk_160 aligned
    // input  sys_clk_160,
    // input  rst_160,
    input   [TDC_COUNT-1:0] tdc_fifo_read,    
    output  [TDC_COUNT-1:0] tdc_fifo_empty,
    output  [TDC_COUNT*TDC_DATA_WIDTH-1:0]  tdc_fifo_data,
    output  [TDC_COUNT-1:0] matching_busy,

    // Triggerless event-driven FIFO interface
    input                   acquisition_mode,
    input   [TDC_COUNT-1:0] triggerless_run_enable,
    input   [TDC_COUNT-1:0] triggerless_clr_hit_fifos,
    input                   triggerless_noise_counter_clear,
    input   [TDC_COUNT-1:0] triggerless_wr_bank_sel,
    input   [TDC_COUNT-1:0] triggerless_rd_bank_sel,
    input   [TDC_COUNT-1:0] triggerless_drop_hits,
    input   [TDC_COUNT-1:0] triggerless_fifo_read,
    output  [TDC_COUNT-1:0] triggerless_fifo_empty,
    output  [TDC_COUNT*TDC_DATA_WIDTH-1:0] triggerless_fifo_data,
    output  [TDC_COUNT-1:0] triggerless_fifoA_empty,
    output  [TDC_COUNT-1:0] triggerless_fifoB_empty,
    output  [TDC_COUNT-1:0] triggerless_overflowA,
    output  [TDC_COUNT-1:0] triggerless_overflowB,
    output  [TDC_COUNT-1:0] triggerless_overflow_word,
    output  [TDC_COUNT*24*31-1:0] noise_hit_counts,
    output  [TDC_COUNT*2*31-1:0] noise_error_counts,

    //trigger interface
    input                   enable_matching,
    input                   enable_matching_timeout,
    input   [16:0]          trigger_fifo_data,
    input                   trigger_fifo_empty,
    input                   building_busy,    

    input   [11:0]          trigger_coarse,
    input   [11:0]          match_window,
    input   [11:0]          search_margin,
    input   [11:0]          bc_offset,
    input   [11:0]          reject_offset,
    input   [11:0]          rollover,
    input                   enable_relative_trigger_data,

    //BER monitor
    output [43:0] total_received_40bit_dline1[9:0],
    output [43:0] total_received_40bit_dline0[9:0],
    output [35:0] total_error_bit_dline1[9:0],
    output [35:0] total_error_bit_dline0[9:0]
);


wire [7:0] elink_320m [27:0]; //Maximum of 28 links @ 320Mbps
wire [7:0] tdc_dline_1[9:0];
wire [7:0] tdc_dline_0[9:0];
wire [4:0] tdc_id[TDC_COUNT-1:0];  
// wire [7:0] TTC_ENC;
wire [1:0] phase_sel_160M[9:0];

generate
    genvar i;
    for (i = 0; i < 28; i = i + 1) begin
        assign elink_320m[i] = userDataUpLink_i[i*8+7:i*8]; 
    end   
endgenerate

generate
    genvar k;
    for (k = 0; k < TDC_COUNT; k = k + 1) begin
        assign tdc_id[k] = IS_MASTER? k : k+5'd10; 
        assign phase_sel_160M[k] = phase_sel_160M_20b[2*k+1:2*k];
    end   
endgenerate


// TDC**_CH*_IN corresponds to lpGBT_CSM board schematic net name;
// tdc_dline_1 mapped to TDC**_CH1_IN, tdc_dline_0 mapped to TDC**_CH2_IN.

// TDC data connections from LpGBT_CSM_preprod_010324_sch.pdf:
//   IS_MASTER = 1: sheet 5, Master LpGBT0, TDC0 through TDC9
//   IS_MASTER = 0: sheet 6, Slave  LpGBT1, TDC10 through TDC19
//
// P/N suffixes are omitted below; every EDIN entry represents a differential
// input pair.  At 320 Mbps, EDINxy maps to elink_320m[4*x+y].
// tdc_dline_1 is the schematic TDC#CH1 signal and tdc_dline_0 is TDC#CH2.
//
// Local     Master LpGBT0 (IS_MASTER=1)       Slave LpGBT1 (IS_MASTER=0)
// slot k    dline_1 / dline_0                 dline_1 / dline_0
// -------   --------------------------------  ---------------------------------
//   0       TDC0: EDIN63[27] / EDIN62[26]    TDC10: EDIN63[27] / EDIN62[26]
//   1       TDC1: EDIN51[21] / EDIN50[20]    TDC11: EDIN41[17] / EDIN40[16]
//   2       TDC2: EDIN61[25] / EDIN60[24]    TDC12: EDIN61[25] / EDIN60[24]
//   3       TDC3: EDIN43[19] / EDIN42[18]    TDC13: EDIN33[15] / EDIN32[14]
//   4       TDC4: EDIN53[23] / EDIN52[22]    TDC14: EDIN43[19] / EDIN42[18]
//   5       TDC5: EDIN10[ 4] / EDIN11[ 5]    TDC15: EDIN10[ 4] / EDIN11[ 5]
//   6       TDC6: EDIN00[ 0] / EDIN01[ 1]    TDC16: EDIN00[ 0] / EDIN01[ 1]
//   7       TDC7: EDIN12[ 6] / EDIN13[ 7]    TDC17: EDIN12[ 6] / EDIN13[ 7]
//   8       TDC8: EDIN02[ 2] / EDIN03[ 3]    TDC18: EDIN02[ 2] / EDIN03[ 3]
//   9       TDC9: EDIN20[ 8] / EDIN21[ 9]    TDC19: EDIN20[ 8] / EDIN21[ 9]
assign tdc_dline_1[0] = elink_320m[27];
assign tdc_dline_0[0] = elink_320m[26];
assign tdc_dline_1[1] = IS_MASTER ? elink_320m[21] : elink_320m[17];
assign tdc_dline_0[1] = IS_MASTER ? elink_320m[20] : elink_320m[16];
assign tdc_dline_1[2] = elink_320m[25];
assign tdc_dline_0[2] = elink_320m[24];
assign tdc_dline_1[3] = IS_MASTER ? elink_320m[19] : elink_320m[15];
assign tdc_dline_0[3] = IS_MASTER ? elink_320m[18] : elink_320m[14];
assign tdc_dline_1[4] = IS_MASTER ? elink_320m[23] : elink_320m[19];
assign tdc_dline_0[4] = IS_MASTER ? elink_320m[22] : elink_320m[18];
assign tdc_dline_1[5] = elink_320m[4 ];
assign tdc_dline_0[5] = elink_320m[5 ];
assign tdc_dline_1[6] = elink_320m[0 ];
assign tdc_dline_0[6] = elink_320m[1 ];
assign tdc_dline_1[7] = elink_320m[6 ];
assign tdc_dline_0[7] = elink_320m[7 ];
assign tdc_dline_1[8] = elink_320m[2 ];
assign tdc_dline_0[8] = elink_320m[3 ];
assign tdc_dline_1[9] = elink_320m[8 ];
assign tdc_dline_0[9] = elink_320m[9 ];


generate
    genvar j;
    for (j = 0; j < TDC_COUNT; j = j + 1) begin: tdcv2_decoder
        tdcv2_decoder inst_tdcv2_decoder
        (
            .clk_40                       (clk_40),
            .rst_40                       (rst_40),
            .pipeline_rst                 (pipeline_rst),
            .tdc_dline_1                  (tdc_dline_1[j]),
            .tdc_dline_0                  (tdc_dline_0[j]),
            .tdc_id                       (tdc_id[j]),
            .csm_id                       (CSM_ID[2:0]),

            .tdc_fifo_read                (tdc_fifo_read[j]),
            .tdc_fifo_empty               (tdc_fifo_empty[j]),
            .tdc_fifo_data                (tdc_fifo_data[(j+1)*TDC_DATA_WIDTH-1:j*TDC_DATA_WIDTH]),

            .acquisition_mode             (acquisition_mode),
            .triggerless_run_enable       (triggerless_run_enable[j]),
            .triggerless_clr_hit_fifos    (triggerless_clr_hit_fifos[j]),
            .triggerless_noise_counter_clear(triggerless_noise_counter_clear),
            .triggerless_wr_bank_sel      (triggerless_wr_bank_sel[j]),
            .triggerless_rd_bank_sel      (triggerless_rd_bank_sel[j]),
            .triggerless_drop_hits        (triggerless_drop_hits[j]),
            .triggerless_fifo_read        (triggerless_fifo_read[j]),
            .triggerless_fifo_empty       (triggerless_fifo_empty[j]),
            .triggerless_fifo_data        (triggerless_fifo_data[(j+1)*TDC_DATA_WIDTH-1:j*TDC_DATA_WIDTH]),
            .triggerless_fifoA_empty      (triggerless_fifoA_empty[j]),
            .triggerless_fifoB_empty      (triggerless_fifoB_empty[j]),
            .triggerless_overflowA        (triggerless_overflowA[j]),
            .triggerless_overflowB        (triggerless_overflowB[j]),
            .triggerless_overflow_word    (triggerless_overflow_word[j]),
            .noise_hit_counts             (noise_hit_counts[(j+1)*24*31-1:j*24*31]),
            .noise_error_counts           (noise_error_counts[(j+1)*2*31-1:j*2*31]),

            .enable_K28_1                 (enable_K28_1),
            .enable_320M                  (enable_320M),
            .phase_sel_160M               (phase_sel_160M[j]),
            .correct_counter_th           (correct_counter_th),
            .locked_dline1                (locked_dline1[j]),
            .locked_dline0                (locked_dline0[j]),

            // .sys_clk_160                  (sys_clk_160),
            // .rst_160                      (rst_160),
            .matching_busy                (matching_busy[j]),
            .enable_matching              (enable_matching),
            .enable_matching_timeout      (enable_matching_timeout),
            .trigger_fifo_data            (trigger_fifo_data),
            .trigger_fifo_empty           (trigger_fifo_empty),
            .building_busy                (building_busy),
            .trigger_coarse               (trigger_coarse),
            .match_window                 (match_window),
            .search_margin                (search_margin),
            .bc_offset                    (bc_offset),
            .reject_offset                (reject_offset),
            .rollover                     (rollover),
            .enable_relative_trigger_data (enable_relative_trigger_data),

            .total_received_40bit_dline1 (total_received_40bit_dline1[j]),
            .total_received_40bit_dline0 (total_received_40bit_dline0[j]),
            .total_error_bit_dline1      (total_error_bit_dline1[j]),
            .total_error_bit_dline0      (total_error_bit_dline0[j])
        );
    end   
endgenerate

genvar k1;
for(k1=TDC_COUNT;k1<10;k1=k1+1) begin
    assign total_received_40bit_dline1[k1] = 'b0;
    assign total_received_40bit_dline0[k1] = 'b0;
    assign total_error_bit_dline1[k1]      = 'b0;
    assign total_error_bit_dline0[k1]      = 'b0;
end


endmodule
