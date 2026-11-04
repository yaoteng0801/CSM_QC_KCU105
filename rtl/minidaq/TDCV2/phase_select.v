`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: Yuxiang Guo
// 
// Create Date: 1/03/2021 00:29:00 AM
// Design Name: 
// Module Name: phase_select
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////
module phase_select (
	input			clk,
	input			rst,
	input	[7:0]	tdc_dline_1, 
	input	[7:0]	tdc_dline_0,

	output			chnl_data_valid,
	output	[31:0]	chnl_data_32b,

	//config and info
	input			enable_K28_1,
	input			enable_320M,
	input	[1:0]	phase_sel_160M,
	input			enable_matching,
	input	[19:0]	correct_counter_th,
	output			locked_dline1,
	output			locked_dline0,	

    output	[43:0]	total_received_40bit_dline1,
    output	[43:0]	total_received_40bit_dline0,
    output	[35:0]	total_error_bit_dline1,
    output	[35:0]	total_error_bit_dline0
	);

localparam K28_5 = 20'b00111_11010_11000_00101;
localparam dline0_value_K28_5 = 10'b01100_10011;
localparam dline1_value_K28_5 = 10'b01111_10000;

//localparam correct_counter_th = 20'd1000_0000;

localparam K28_1 = 20'b00111_11001_11000_00110;
localparam dline0_value_K28_1 = 10'b01101_10010;
localparam dline1_value_K28_1 = 10'b01110_10001;


wire [9:0] dline1_value, dline0_value;
reg [3:0] counter;
wire tick;

wire data_ready;
wire [63:0] data_64b_decode;
wire [7:0] Kout;


wire[3:0] start_point_dline1, start_point_dline0;
wire[39:0] data_40b_dline1, data_40b_dline0;
(* dont_touch = "true" *) wire[39:0] data_40b_shifted_dline1;
(* dont_touch = "true" *) wire[39:0] data_40b_shifted_dline0;
wire [3:0] shift_dline1;
wire [3:0] shift_dline0;

(* dont_touch = "true" *) wire [79:0] data_80b_align;
wire [7:0] DErr,KErr,DpErr;

wire chnl_data_valid_triggerless;
wire [31:0] chnl_data_32b_triggerless;
wire chnl_data_valid_trigger;
wire [31:0] chnl_data_32b_trigger;


assign dline1_value = enable_K28_1? dline1_value_K28_1:dline1_value_K28_5;
assign dline0_value = enable_K28_1? dline0_value_K28_1:dline0_value_K28_5;
assign tick = ~|counter;
assign data_ready = tick&locked_dline1&locked_dline0;


assign shift_dline0 = (start_point_dline1>start_point_dline0)?((start_point_dline1-start_point_dline0>4)?
				(start_point_dline0+4'd10):start_point_dline0):start_point_dline0;
assign shift_dline1 = (start_point_dline0>start_point_dline1)?((start_point_dline0-start_point_dline1>4)?
				(start_point_dline1+4'd10):start_point_dline1):start_point_dline1;


//enable_matching is used in TDC triggerless mode
assign chnl_data_valid = (~enable_matching)?chnl_data_valid_trigger:chnl_data_valid_triggerless;
assign chnl_data_32b   = (~enable_matching)?chnl_data_32b_trigger:chnl_data_32b_triggerless;



always @(posedge clk) begin
	if(rst) begin
		counter <= enable_320M ? 4'd4 : 4'd9;
	end else if(~|counter) begin 
		counter <= enable_320M ? 4'd4 : 4'd9;
	end else begin
		counter <= counter - 1'b1;
	end
end

single_edge_data_lock_detector_8b single_edge_data_lock_detector_8b_dline1
	(
		.clk                (clk),
		.tick               (tick),
		.rst                (rst),
		.enable_320M        (enable_320M),
		.phase_sel_160M     (phase_sel_160M[1]),
		.dline              (tdc_dline_1),
		.correct_value      (dline1_value),
		.correct_counter_th (correct_counter_th),
		.locked             (locked_dline1),
		.start_point        (start_point_dline1),
		.data_40b			(data_40b_dline1),
        .total_received_40bit (total_received_40bit_dline1),
        .total_error_bit      (total_error_bit_dline1)

	);


single_edge_data_lock_detector_8b single_edge_data_lock_detector_8b_dline0
	(
		.clk                (clk),
		.tick               (tick),
		.rst                (rst),
		.dline              (tdc_dline_0),
		.enable_320M        (enable_320M),
		.phase_sel_160M     (phase_sel_160M[0]),
		.correct_value      (dline0_value),
		.correct_counter_th (correct_counter_th),
		.locked             (locked_dline0),
		.start_point        (start_point_dline0),
		.data_40b			(data_40b_dline0),
        .total_received_40bit (total_received_40bit_dline0),
        .total_error_bit      (total_error_bit_dline0)
	);

single_edge_data_shift_40b inst_single_edge_data_shift_40b_dline1
	(
		.clk              (clk),
		.tick             (tick),
		.rst			  (rst),
		.locked           (locked_dline1),
		.shift            (shift_dline1),
		.data_40b         (data_40b_dline1),
		.data_40b_shifted (data_40b_shifted_dline1)
	);

single_edge_data_shift_40b inst_single_edge_data_shift_40b_dline0
	(
		.clk              (clk),
		.tick             (tick),
		.rst			  (rst),
		.locked           (locked_dline0),
		.shift            (shift_dline0),
		.data_40b         (data_40b_dline0),
		.data_40b_shifted (data_40b_shifted_dline0)
	);

generate
	genvar j;
	for (j = 0; j < 40; j = j + 1) begin
		assign data_80b_align[2*j+1] = data_40b_shifted_dline1[j];
		assign data_80b_align[2*j]   = data_40b_shifted_dline0[j];		
	end	
endgenerate


generate
	genvar i;
	for(i = 0; i < 8; i=i+1)


	begin:decoder_10b8b
		mDec8b10bMem_tb 
		inst_mDec8b10bMem_tb (
			.o8_Dout          (data_64b_decode[i*8+7:i*8]),
			.o_Kout           (Kout[i]),
			.o_DErr           (DErr[i]),
			.o_KErr           (KErr[i]),
			.o_DpErr          (DpErr[i]),
			.i_ForceDisparity (1'b0),
			.i_Disparity      (1'b0),
			.i10_Din          (data_80b_align[i*10+9:i*10]),
			.o_Rd             (),
			.i_Clk            (clk),
			.i_ARst_L         (!rst),
			.soft_reset_i     (),
			.i_enable         (data_ready)
		);
	end	
endgenerate


channel_align_32b channel_align_32b_inst
(
	.clk             (clk),
	.rst             (rst),
	.enable          (enable_matching),
	.data_64b_decode (data_64b_decode),
	.i_Kout          (Kout),
	.i_DErr          (DErr),
	.i_KErr          (KErr),
	.data_ready      (data_ready),
	.chnl_data_valid (chnl_data_valid_triggerless),
	.chnl_data_32b   (chnl_data_32b_triggerless)
);

channel_align_32b_trigger channel_align_32b_trigger_inst
(
	.clk             (clk),
    .rst             (rst),
    .enable          (~enable_matching), //no MiniDAQ matching when TDC is in trigger mode
	.data_64b_decode (data_64b_decode),
	.o_Kout          (Kout),
	.data_ready      (data_ready),
	.chnl_data_valid (chnl_data_valid_trigger),
	.chnl_data_32b   (chnl_data_32b_trigger)
);


// ila_phase_align inst_ila_phase_align (

// 	.clk(clk), // input wire clk


// 	.probe0(tdc_dline_1), // input wire [7:0]  probe0  
// 	.probe1(tdc_dline_0), // input wire [7:0]  probe1 

// 	.probe2(data_40b_dline1), // input wire [39:0]  probe2 
// 	.probe3(data_40b_dline0), // input wire [39:0]  probe3 
// 	.probe4(data_40b_shifted_dline1), // input wire [39:0]  probe4 
// 	.probe5(data_40b_shifted_dline0), // input wire [39:0]  probe5 
// 	.probe6(data_80b_align), // input wire [79:0]  probe6 
// 	.probe7(data_64b_decode), // input wire [63:0]  probe7 
// 	.probe8(Kout), // input wire [7:0]  probe8 
// 	.probe9(shift_dline1), // input wire [3:0]  probe9 
// 	.probe10(shift_dline0), // input wire [3:0]  probe10 
// 	.probe11(chnl_data_valid), // input wire [0:0]  probe11 
// 	.probe12(chnl_data_32b) // input wire [31:0]  probe12
// );
wire    [4:0]   chnl_ID;
wire    [1:0]   mode;
wire    [16:0]  leading;
wire    [7:0]   width;
assign chnl_ID = chnl_data_32b[31:27];
assign mode    = chnl_data_32b[26:25];
assign leading = chnl_data_32b[24:8];
assign width   = chnl_data_32b[7:0];
// ila_data_monitor ila_data_monitor_inst (
//     .clk(clk), // input wire clk

//     .probe0(chnl_data_valid), // input wire [0:0]  probe0  
//     .probe1(chnl_ID), // input wire [4:0]  probe1 
//     .probe2(mode), // input wire [1:0]  probe2 
//     .probe3(leading), // input wire [16:0]  probe3 
//     .probe4(width), // input wire [7:0]  probe4 
//     .probe5(Kout), // input wire [7:0]  probe5 
//     .probe6(tdc_dline_1), // input wire [7:0]  probe6 
//     .probe7(tdc_dline_0), // input wire [7:0]  probe7
//     .probe8(DErr), // input wire [7:0]  probe8 
//     .probe9(KErr), // input wire [7:0]  probe9 
//     .probe10(DpErr) // input wire [7:0]  probe10
// );

endmodule