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
// File   : channel_align_32b.v
// Create : 2021-01-02 22:53:00
// Revise : 2024-03-21 17:22:23
// Editor : sublime text4, tab size (4)
// Description: 
//
`define TRIGGERLESS_ERROR_packet		8'b11011100 
`define OVERFLOW_WORD_FILL              8'b1110_1000
`define DECODE_ERROR_WORD_FILL          32'b1111_0111_0100_0001_0001_0001_0001_0001 

module channel_align_32b (
	input clk,
	input rst,
	input enable,
	input [63:0] data_64b_decode, 
	input [7:0] i_Kout,
    input [7:0] i_DErr,
    input [7:0] i_KErr,
	input data_ready,
	output chnl_data_valid,
	output [31:0] chnl_data_32b
	);

reg [63:0] data_64b_decode_pre;
reg [7:0] o_Kout_pre;
reg data_decode_error;
wire [7:0] K_pre_overflow;
generate
	genvar i;
	for (i=0;i<8;i=i+1) begin
		assign K_pre_overflow[i] = ((data_64b_decode_pre[i*8+7:i*8]==`TRIGGERLESS_ERROR_packet)&
											(o_Kout_pre[i]==1'b1))?1'b1:1'b0;
	end
endgenerate

always @(posedge clk) begin
	if(rst) begin
		data_64b_decode_pre <= 'b0;
		o_Kout_pre <= 8'hff;
        data_decode_error <= 'b0;
	end else if(data_ready&enable) begin
		data_64b_decode_pre <= data_64b_decode;
		o_Kout_pre <= i_Kout;
        data_decode_error <= |(i_DErr|i_KErr);
	end
end



reg [3:0] data_ready_r;
/*  data_ready is 1 for every 5 clocks, i.g. ...01000010000100...
when data_ready is 0, data_64b_decode remains unchange (decoder enable=0).
data_ready[0] is aligned with data_64b_decode, data_ready_r[1] is aligned with data_64b_decode_pre
time                    0   1   2   3   4   5   6
data_ready              0   1   0   0   0   0   1 
data_ready_r[0]         0   0   1   0   0   0   0   1 
data_ready_r[1]         0   0   0   1   0   0   0   0  
data_ready_r[2]         0   0   0   0   1   0   0   0 
data_ready_r[3]         0   0   0   0   0   1   0   0   
data_64b_decode         d0  d0  d1  d1  d1  d1  d1  d2
data_64b_decode_pre     X   X   d0  d0  d0  d0  d0  d1

*/
always @(posedge clk) begin
	if (rst) begin
		data_ready_r <= 'b0;
	end else if (enable) begin
		data_ready_r <= {data_ready_r[1:0], data_ready};
	end
end

/*
It is always true that:
i_DErr & i_KErr = 0
i_KErr & Kout = 0
*/

reg [1:0] data_start;
reg [31:0] chnl_data_1, chnl_data_2;
reg chnl_data_1_valid, chnl_data_2_valid;
always @(posedge clk) begin
	if(rst) begin
		chnl_data_1 <= 'b0;
		chnl_data_1_valid <= 1'b0;
		chnl_data_2 <= 'b0;
		chnl_data_2_valid <= 1'b0;
	end else if(enable)begin
		if(data_ready_r[0]) begin
			chnl_data_2_valid <= 'b0;
			chnl_data_2 <= 'b0;
			if(data_start == 2'b0) begin
				if(o_Kout_pre[7:4] == 4'b0) begin
					data_start <= 2'b0;
					chnl_data_1 <= data_64b_decode_pre[63:32];
					chnl_data_1_valid <= 1'b1;
				end else if(o_Kout_pre[7:4] == 4'b1000) begin
					data_start <= 2'b01;
					chnl_data_1 <= data_64b_decode_pre[55:24];
					chnl_data_1_valid <= 1'b1;
				end else if(o_Kout_pre[7:4] == 4'b1100) begin
					data_start <= 2'b10;
					chnl_data_1 <= data_64b_decode_pre[47:16];
					chnl_data_1_valid <= 1'b1;
				end else if(o_Kout_pre[7:4] == 4'b1110) begin
					data_start <= 2'b11;
					chnl_data_1 <= data_64b_decode_pre[39:8];
					chnl_data_1_valid <= 1'b1;
				end else begin
					data_start <= 2'b0;
					chnl_data_1 <= 'b0;
					chnl_data_1_valid <= 1'b0;				
				end				
			end else if(data_start == 2'b01) begin
				if(o_Kout_pre[6:4] == 3'b000) begin
					data_start <= 2'b01;
					chnl_data_1 <= data_64b_decode_pre[55:24];
					chnl_data_1_valid <= 1'b1;
				end else if(o_Kout_pre[6:4] == 3'b100) begin
					data_start <= 2'b10;
					chnl_data_1 <= data_64b_decode_pre[47:16];
					chnl_data_1_valid <= 1'b1;
				end else if(o_Kout_pre[6:4] == 3'b110) begin
					data_start <= 2'b11;
					chnl_data_1 <= data_64b_decode_pre[39:8];
					chnl_data_1_valid <= 1'b1;
				end else begin
					data_start <= 2'b0;
					chnl_data_1 <= 'b0;
					chnl_data_1_valid <= 1'b0;	
				end
			end else if(data_start == 2'b10) begin
				if(o_Kout_pre[5:4] == 2'b00) begin
					data_start <= 2'b10;
					chnl_data_1 <= data_64b_decode_pre[47:16];
					chnl_data_1_valid <= 1'b1;
				end else if(o_Kout_pre[5:4] == 2'b10) begin
					data_start <= 2'b11;
					chnl_data_1 <= data_64b_decode_pre[39:8];
					chnl_data_1_valid <= 1'b1;
				end else begin
					data_start <= 2'b0;
					chnl_data_1 <= 'b0;
					chnl_data_1_valid <= 1'b0;
				end
			end else if(data_start == 2'b11) begin
				if(o_Kout_pre[4] == 1'b0) begin
					data_start <= 2'b11;
					chnl_data_1 <= data_64b_decode_pre[39:8];
					chnl_data_1_valid <= 1'b1;
				end else begin
					data_start <= 2'b0;
					chnl_data_1 <= 'b0;
					chnl_data_1_valid <= 1'b0;
				end
			end
		end else if(data_ready_r[1]) begin
			chnl_data_1_valid <= 'b0;
			chnl_data_1 <= 'b0;
			if(data_start == 2'b0) begin
				if(o_Kout_pre[3:0] == 4'b0) begin
					data_start <= 2'b0;
					chnl_data_2 <= data_64b_decode_pre[31:0];
					chnl_data_2_valid <= 1'b1;
				end else if(o_Kout_pre[3:0] == 4'b1000) begin
					data_start <= 2'b01;
					chnl_data_2 <= {data_64b_decode_pre[23:0],data_64b_decode[63:56]};
					chnl_data_2_valid <= 1'b1;
				end else if(o_Kout_pre[3:0] == 4'b1100) begin
					data_start <= 2'b10;
					chnl_data_2 <= {data_64b_decode_pre[15:0],data_64b_decode[63:48]};
					chnl_data_2_valid <= 1'b1;
				end else if(o_Kout_pre[3:0] == 4'b1110) begin
					data_start <= 2'b11;
					chnl_data_2 <= {data_64b_decode_pre[7:0],data_64b_decode[63:40]};
					chnl_data_2_valid <= 1'b1;
				end else begin
					data_start <= 2'b0;
					chnl_data_2 <= 'b0;
					chnl_data_2_valid <= 1'b0;				
				end				
			end else if(data_start == 2'b01) begin
				if(o_Kout_pre[2:0] == 3'b000) begin
					data_start <= 2'b01;
					chnl_data_2 <= {data_64b_decode_pre[23:0],data_64b_decode[63:56]};
					chnl_data_2_valid <= 1'b1;
				end else if(o_Kout_pre[2:0] == 3'b100) begin
					data_start <= 2'b10;
					chnl_data_2 <={data_64b_decode_pre[15:0],data_64b_decode[63:48]};
					chnl_data_2_valid <= 1'b1;
				end else if(o_Kout_pre[2:0] == 3'b110) begin
					data_start <= 2'b11;
					chnl_data_2 <= {data_64b_decode_pre[7:0],data_64b_decode[63:40]};
					chnl_data_2_valid <= 1'b1;
				end else begin
					data_start <= 2'b0;
					chnl_data_2 <= 'b0;
					chnl_data_2_valid <= 1'b0;	
				end
			end else if(data_start == 2'b10) begin
				if(o_Kout_pre[1:0] == 2'b00) begin
					data_start <= 2'b10;
					chnl_data_2 <= {data_64b_decode_pre[15:0],data_64b_decode[63:48]};
					chnl_data_2_valid <= 1'b1;
				end else if(o_Kout_pre[1:0] == 2'b10) begin
					data_start <= 2'b11;
					chnl_data_2 <= {data_64b_decode_pre[7:0],data_64b_decode[63:40]};
					chnl_data_2_valid <= 1'b1;
				end else begin
					data_start <= 2'b0;
					chnl_data_2 <= 'b0;
					chnl_data_2_valid <= 1'b0;
				end
			end else if(data_start == 2'b11) begin
				if(o_Kout_pre[0] == 1'b0) begin
					data_start <= 2'b11;
					chnl_data_2 <= {data_64b_decode_pre[7:0],data_64b_decode[63:40]};
					chnl_data_2_valid <= 1'b1;
				end else begin
					data_start <= 2'b0;
					chnl_data_2 <= 'b0;
					chnl_data_2_valid <= 1'b0;
				end
			end
		end else if (data_ready_r[2])begin
			chnl_data_2 <= 'b0;
			chnl_data_2_valid <= 1'b0;
			if(|K_pre_overflow)begin
				chnl_data_1 <= {`OVERFLOW_WORD_FILL,K_pre_overflow,16'b0};
				chnl_data_1_valid <= 1'b1;
				if(K_pre_overflow[7]==1'b1)
					chnl_data_1[15:8] <= {3'b111,data_64b_decode_pre[55:51]};
				if(K_pre_overflow[6]==1'b1)
					chnl_data_1[15:8] <= {3'b111,data_64b_decode_pre[47:43]};
				if(K_pre_overflow[5]==1'b1)
					chnl_data_1[15:8] <= {3'b111,data_64b_decode_pre[39:35]};
				if(K_pre_overflow[4]==1'b1)
					chnl_data_1[15:8] <= {3'b111,data_64b_decode_pre[31:27]};
				if(K_pre_overflow[3]==1'b1)
					chnl_data_1[7:0] <= {3'b111,data_64b_decode_pre[23:19]};
				if(K_pre_overflow[2]==1'b1)
					chnl_data_1[7:0] <= {3'b111,data_64b_decode_pre[15:11]};
				if(K_pre_overflow[1]==1'b1)
					chnl_data_1[7:0] <= {3'b111,data_64b_decode_pre[7:3]};
				if(K_pre_overflow[0]==1'b1)
					chnl_data_1[7:0] <= {3'b111,data_64b_decode[63:59]};				
			end else begin
				chnl_data_1 <= 'b0;
				chnl_data_1_valid <= 1'b0;
			end
		end else if(data_ready_r[3])begin  //adding a decode error flag word
            chnl_data_1 <= 'b0;
            chnl_data_1_valid <= 1'b0;
            if(data_decode_error)begin
                chnl_data_2 <= `DECODE_ERROR_WORD_FILL;
                chnl_data_2_valid <= 1'b1;                
            end
        end else begin
			chnl_data_1 <= 'b0;
			chnl_data_1_valid <= 1'b0;
			chnl_data_2 <= 'b0;
			chnl_data_2_valid <= 1'b0;
		end
	end
end

assign chnl_data_valid = chnl_data_1_valid|chnl_data_2_valid;
assign chnl_data_32b = chnl_data_1_valid?chnl_data_1:(chnl_data_2_valid?chnl_data_2:32'b0);

// wire [4:0] chnum1, chnum2;
// wire [1:0] mode1, mode2;
// wire [16:0] leading1, leading2;
// wire [7:0] width1, width2;
// assign chnum1 	= chnl_data_1[31:27];
// assign mode1	= chnl_data_1[26:25];
// assign leading1 = chnl_data_1[24:8];   
// assign width1	= chnl_data_1[7:0];
// assign chnum2 	= chnl_data_2[31:27];
// assign mode2	= chnl_data_2[26:25];
// assign leading2 = chnl_data_2[24:8];   
// assign width2	= chnl_data_2[7:0];



// ila_tdcv2_decoder ila_tdcv2_decoder_inst (
// 	.clk(clk), // input wire clk


// 	.probe0(data_ready), // input wire [0:0]  probe0  
// 	.probe1(data_64b_decode), // input wire [63:0]  probe1 
// 	.probe2(i_Kout), // input wire [7:0]  probe2 
// 	.probe3(data_64b_decode_pre), // input wire [63:0]  probe3 
// 	.probe4(o_Kout_pre), // input wire [7:0]  probe4 
// 	.probe5(data_ready_r), // input wire [1:0]  probe5 
// 	.probe6(data_start), // input wire [1:0]  probe6 
// 	.probe7(chnl_data_1_valid), // input wire [0:0]  probe7 
// 	.probe8(chnl_data_1), // input wire [31:0]  probe8 
// 	.probe9(chnum1), // input wire [4:0]  probe9 
// 	.probe10(mode1), // input wire [1:0]  probe10 
// 	.probe11(width1), // input wire [7:0]  probe11 
// 	.probe12(leading1), // input wire [16:0]  probe12 
// 	.probe13(chnl_data_2_valid), // input wire [0:0]  probe13 
// 	.probe14(chnl_data_2), // input wire [31:0]  probe14 
// 	.probe15(chnum2), // input wire [4:0]  probe15 
// 	.probe16(mode2), // input wire [1:0]  probe16 
// 	.probe17(width2), // input wire [7:0]  probe17 
// 	.probe18(leading2) // input wire [16:0]  probe18
// );


endmodule
