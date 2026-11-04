`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: Yuxiang Guo
// 
// Create Date: 1/03/2021 03:49:00 AM
// Design Name: 
// Module Name: single_edge_data_shift_40b
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
module single_edge_data_shift_40b (
	input clk,
	input tick,
	input rst,
	input locked,
	input [3:0] shift,
	input [39:0] data_40b,
	output reg [39:0] data_40b_shifted
	);

reg [39:0] data_40b_r, data_40b_r2;
always @(posedge clk) begin
	if(rst) begin
		data_40b_r  <= 'b0;
		data_40b_r2 <= 'b0;
	end else if(locked&tick) begin		
		data_40b_r  <= data_40b;
		data_40b_r2 <= data_40b_r;
	end
end

always @(*) begin
	case (shift)
		4'h0:  data_40b_shifted = data_40b_r;
		4'h1:  data_40b_shifted = {data_40b_r2[0],   data_40b_r[39:1]};
		4'h2:  data_40b_shifted = {data_40b_r2[1:0], data_40b_r[39:2]};
		4'h3:  data_40b_shifted = {data_40b_r2[2:0], data_40b_r[39:3]};
		4'h4:  data_40b_shifted = {data_40b_r2[3:0], data_40b_r[39:4]};
		4'h5:  data_40b_shifted = {data_40b_r2[4:0], data_40b_r[39:5]};
		4'h6:  data_40b_shifted = {data_40b_r2[5:0], data_40b_r[39:6]};
		4'h7:  data_40b_shifted = {data_40b_r2[6:0], data_40b_r[39:7]};
		4'h8:  data_40b_shifted = {data_40b_r2[7:0], data_40b_r[39:8]};
		4'h9:  data_40b_shifted = {data_40b_r2[8:0], data_40b_r[39:9]};
		4'hA:  data_40b_shifted = {data_40b_r2[9:0], data_40b_r[39:10]};
		4'hB:  data_40b_shifted = {data_40b_r2[10:0],data_40b_r[39:11]};
		4'hC:  data_40b_shifted = {data_40b_r2[11:0],data_40b_r[39:12]};
		4'hD:  data_40b_shifted = {data_40b_r2[12:0],data_40b_r[39:13]};
		4'hE:  data_40b_shifted = {data_40b_r2[13:0],data_40b_r[39:14]};
		default : data_40b_shifted = data_40b_r;
	endcase
end
endmodule
