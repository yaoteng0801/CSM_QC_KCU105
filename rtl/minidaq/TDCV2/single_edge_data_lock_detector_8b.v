`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: Yuxiang Guo
// 
// Create Date: 1/03/2021 00:29:00 AM
// Design Name: 
// Module Name: single_edge_data_lock_detector_8b
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
module single_edge_data_lock_detector_8b (
	input clk,
	input tick,
	input rst,
	input enable_320M,
	input phase_sel_160M,
	input [7:0] dline,
	input [9:0] correct_value,
	input [19:0] correct_counter_th,
	output reg locked,
	output reg [3:0] start_point,
	output reg [39:0] data_40b,
    output reg [43:0] total_received_40bit,
    output reg [35:0] total_error_bit
	);

always @(posedge clk) begin
	if(rst) data_40b <= 40'b0;
	else data_40b <= enable_320M 	? {data_40b[31:0], dline} : 
					 phase_sel_160M ? {data_40b[35:0], dline[6],dline[4],dline[2],dline[0]} : 
                                   {data_40b[35:0], dline[7],dline[5],dline[3],dline[1]} ;
end

reg [39:0] value_compare;
always @(*) begin
	case (start_point)
		4'h0:  value_compare = {correct_value,     correct_value,correct_value,correct_value     };
		4'h1:  value_compare = {correct_value[8:0],correct_value,correct_value,correct_value,correct_value[9]};
		4'h2:  value_compare = {correct_value[7:0],correct_value,correct_value,correct_value,correct_value[9:8]};
		4'h3:  value_compare = {correct_value[6:0],correct_value,correct_value,correct_value,correct_value[9:7]};
		4'h4:  value_compare = {correct_value[5:0],correct_value,correct_value,correct_value,correct_value[9:6]};
		4'h5:  value_compare = {correct_value[4:0],correct_value,correct_value,correct_value,correct_value[9:5]};
		4'h6:  value_compare = {correct_value[3:0],correct_value,correct_value,correct_value,correct_value[9:4]};
		4'h7:  value_compare = {correct_value[2:0],correct_value,correct_value,correct_value,correct_value[9:3]};
		4'h8:  value_compare = {correct_value[1:0],correct_value,correct_value,correct_value,correct_value[9:2]};
		4'h9:  value_compare = {correct_value[0],  correct_value,correct_value,correct_value,correct_value[9:1]};	
		default : value_compare = {correct_value,  correct_value,correct_value,correct_value     };
	endcase
end


reg [19:0] correct_counter='b0;

always @(posedge clk  ) begin
	if (rst) begin 
		start_point <=4'b0; 
	end	else if ((!locked)&tick&(data_40b!=value_compare)) begin		
		start_point <=start_point < 9 ? (start_point + 4'b1) : 4'b0;
	end
end

always @(posedge clk  ) begin
	if (rst) begin
		correct_counter <='b0;
	end else if(!locked) begin
		if (tick&(data_40b==value_compare)) begin
			correct_counter <= correct_counter + 1'b1;
		end else if (tick&(data_40b!=value_compare)) begin
			correct_counter <= 'b0;
		end
	end else begin
		correct_counter <= 'b0;
	end
end

always @(posedge clk  ) begin
	if (rst) begin
		locked <= 1'b0;
	end else if (correct_counter > correct_counter_th) begin
		locked <= 1'b1;
	end
end

wire [5:0] error_bit;

bit_compare #(.BIT_IN(40), .BIT_OUT(6)) bit_compare_inst 
    (.a(data_40b), .b(value_compare), .out(error_bit));

always @(posedge clk  ) begin
    if (rst) begin
        total_received_40bit <= 1'b0;
        total_error_bit      <= 1'b0;
    end else if (locked & tick) begin
        total_received_40bit <= total_received_40bit + 1'b1;
        total_error_bit      <= total_error_bit + error_bit;
    end
end

// ila_edge_lock ila_edge_lock_inst (
// 	.clk(clk), // input wire clk

// 	.probe0(tick), // input wire [0:0]  probe0  
// 	.probe1(dline), // input wire [7:0]  probe1 
// 	.probe2(correct_counter), // input wire [19:0]  probe2 
// 	.probe3(start_point), // input wire [3:0]  probe3 
// 	.probe4(data_40b), // input wire [39:0]  probe4 
// 	.probe5(value_compare), // input wire [39:0]  probe5 
// 	.probe6(error_bit), // input wire [5:0]  probe6 
// 	.probe7(total_error_bit), // input wire [35:0]  probe7 
// 	.probe8(locked) // input wire [0:0]  probe8
// );


endmodule
