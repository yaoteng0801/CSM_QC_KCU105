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
// File   : tdcv2_decoder.v
// Create : 2021-02-01 23:51:00
// Revise : 2021-10-23 20:07:51

// Editor : sublime text4, tab size (3)
// Description: 
//
// -----------------------------------------------------------------------------

module tdcv2_decoder (
    input           clk_40,
    input           rst_40,
    input           pipeline_rst,
    input   [7:0]   tdc_dline_1, 
    input   [7:0]   tdc_dline_0,
    input   [4:0]   tdc_id,
    input   [2:0]   csm_id,
    //TDC readout FIFO
    input           tdc_fifo_read,
    output          tdc_fifo_empty,
    output  [39:0]  tdc_fifo_data,

    // Triggerless event-builder interface to the shared mode-aware FIFO
    input           acquisition_mode,
    input           triggerless_run_enable,
    input           triggerless_clr_hit_fifos,
    input           triggerless_noise_counter_clear,
    input           triggerless_wr_bank_sel,
    input           triggerless_rd_bank_sel,
    input           triggerless_drop_hits,
    input           triggerless_fifo_read,
    output          triggerless_fifo_empty,
    output  [39:0]  triggerless_fifo_data,
    output          triggerless_fifoA_empty,
    output          triggerless_fifoB_empty,
    output          triggerless_overflowA,
    output          triggerless_overflowB,
    output          triggerless_overflow_word,
    output  [24*31-1:0] noise_hit_counts,
    output  [2*31-1:0] noise_error_counts,

    //dline info
    input           enable_K28_1,
    input           enable_320M,
    input   [1:0]   phase_sel_160M,
    // input  tdc_trigger_mode,
    input   [19:0]  correct_counter_th,
    output          locked_dline1,
    output          locked_dline0,


    //trigger info
    output          matching_busy,
    input           enable_matching,
    input           enable_matching_timeout,
    input   [16:0]  trigger_fifo_data,
    input           trigger_fifo_empty,
    input           building_busy,
    input   [11:0]  trigger_coarse,
    input   [11:0]  match_window,
    input   [11:0]  search_margin,
    input   [11:0]  bc_offset,
    input   [11:0]  reject_offset,
    input   [11:0]  rollover,
    input           enable_relative_trigger_data,

    //BER monitor
    output  [43:0]  total_received_40bit_dline1,
    output  [43:0]  total_received_40bit_dline0,
    output  [35:0]  total_error_bit_dline1,
    output  [35:0]  total_error_bit_dline0
);

// raw data align and 10b/8b decoding


//assign tdc_fifo_empty = 'b1;
//assign tdc_fifo_data = 'b0;
//assign matching_busy = 'b0;



wire chnl_data_valid;
wire [31:0] chnl_data_32b;
wire [4:0] chnl_id;



// TDC trigger matching
wire [31:0] matched_data;
wire match_valid;

// Shared mode-aware TDC readout FIFO
wire tdc_fifo_full;
wire triggered_path_rst = rst_40 | pipeline_rst | acquisition_mode;
wire triggerless_path_rst = rst_40 | pipeline_rst | ~acquisition_mode;
wire triggerless_active = acquisition_mode & triggerless_run_enable;
wire triggerless_fifoA_empty_int;
wire triggerless_fifoB_empty_int;
wire noise_decode_error_word = (chnl_data_32b == 32'hF7411111);
wire noise_control_word =
    (chnl_data_32b[31:24] == 8'hF8) |
    (chnl_data_32b[31:24] == 8'hF0) |
    (chnl_data_32b[31:24] == 8'hE8) |
    (chnl_data_32b[31:24] == 8'hF7);
wire noise_invalid_channel_word =
    chnl_data_valid & (chnl_id >= 5'd24) & ~noise_control_word;
assign chnl_id = chnl_data_32b[31:27];
assign triggerless_fifoA_empty = triggerless_fifoA_empty_int;
assign triggerless_fifoB_empty = triggerless_fifoB_empty_int;



phase_select inst_phase_select
(
    .clk                (clk_40),
    .rst                (rst_40),
    .tdc_dline_1        (tdc_dline_1),
    .tdc_dline_0        (tdc_dline_0),


    .enable_matching            (enable_matching | acquisition_mode),
    .chnl_data_valid            (chnl_data_valid),
    .chnl_data_32b              (chnl_data_32b),

    .enable_K28_1       (enable_K28_1),
    .enable_320M        (enable_320M),
    .phase_sel_160M     (phase_sel_160M),
    .correct_counter_th (correct_counter_th),
    .locked_dline1      (locked_dline1),
    .locked_dline0      (locked_dline0),

    .total_received_40bit_dline1 (total_received_40bit_dline1),
    .total_received_40bit_dline0 (total_received_40bit_dline0),
    .total_error_bit_dline1      (total_error_bit_dline1),
    .total_error_bit_dline0      (total_error_bit_dline0)
);









trigger_matching trigger_matching_inst
(
    .clk_40                       (clk_40),
    .rst_40                       (triggered_path_rst),
    .tdc_hit_data                 (chnl_data_32b),
    .tdc_hit_data_valid           (chnl_data_valid & ~acquisition_mode),

    // .sys_clk_160                  (sys_clk_160),
    // .rst_160                      (rst_160),
    .ram_read                     (~tdc_fifo_full),
    .enable_matching              (enable_matching),
    .enable_matching_timeout      (enable_matching_timeout),
    .building_busy                (building_busy),
    .trigger_fifo_empty           (trigger_fifo_empty),
    .trigger_fifo_data            (trigger_fifo_data),

    .matched_data                 (matched_data),
    .match_valid                  (match_valid),
    .matching_busy                (matching_busy),

    .enable_relative_trigger_data (enable_relative_trigger_data),
    .rollover                     (rollover),
    .trigger_coarse               (trigger_coarse),
    .match_window                 (match_window),
    .search_margin                (search_margin),
    .bc_offset                    (bc_offset),
    .reject_offset                (reject_offset)
);


tdc_fifo_pingpong #(
    .DATA_WIDTH(40)
) shared_mode_fifo_inst (
    .clk_40                       (clk_40),
    .rst_40                       (rst_40 | pipeline_rst),
    .acquisition_mode             (acquisition_mode),
    .triggerless_run_enable       (triggerless_run_enable),
    .triggerless_clr_hit_fifos    (triggerless_clr_hit_fifos),

    .triggered_din                ({csm_id,tdc_id,matched_data}),
    .triggered_wr_en              (match_valid),
    .triggered_full               (tdc_fifo_full),
    .triggered_rd_en              (tdc_fifo_read),
    .triggered_dout               (tdc_fifo_data),
    .triggered_empty              (tdc_fifo_empty),

    .triggerless_wr_bank_sel      (triggerless_wr_bank_sel),
    .triggerless_rd_bank_sel      (triggerless_rd_bank_sel),
    .fifoA_empty                  (triggerless_fifoA_empty_int),
    .fifoB_empty                  (triggerless_fifoB_empty_int),
    .triggerless_din              ({csm_id,tdc_id,chnl_data_32b}),
    .triggerless_wr_en            (chnl_data_valid & ~triggerless_drop_hits),
    .triggerless_full             (),
    .triggerless_rd_en            (triggerless_fifo_read),
    .triggerless_dout             (triggerless_fifo_data),
    .triggerless_empty            (triggerless_fifo_empty),
    .overflowA                    (triggerless_overflowA),
    .overflowB                    (triggerless_overflowB),
    .overflow_word                (triggerless_overflow_word)
);

genvar noise_ch;
generate
    for (noise_ch = 0; noise_ch < 24; noise_ch = noise_ch + 1) begin : GEN_NOISE_COUNTER_PACK
        reg [30:0] noise_hit_count;
        assign noise_hit_counts[noise_ch*31 +: 31] = noise_hit_count;

        always @(posedge clk_40) begin
            if (triggerless_path_rst || triggerless_noise_counter_clear)
                noise_hit_count <= 31'd0;
            else if (triggerless_active && chnl_data_valid && (chnl_id == noise_ch))
                noise_hit_count <= noise_hit_count + 31'd1;
        end
    end
endgenerate

reg [30:0] noise_decode_error_count;
reg [30:0] noise_invalid_channel_count;
assign noise_error_counts[0*31 +: 31] = noise_decode_error_count;
assign noise_error_counts[1*31 +: 31] = noise_invalid_channel_count;

always @(posedge clk_40) begin
    if (triggerless_path_rst || triggerless_noise_counter_clear) begin
        noise_decode_error_count <= 31'd0;
        noise_invalid_channel_count <= 31'd0;
    end else if (triggerless_active && chnl_data_valid) begin
        if (noise_decode_error_word)
            noise_decode_error_count <= noise_decode_error_count + 31'd1;
        if (noise_invalid_channel_word)
            noise_invalid_channel_count <= noise_invalid_channel_count + 31'd1;
    end
end

endmodule
