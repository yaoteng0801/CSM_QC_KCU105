/* 
       _________   ________     ________       
      / U OF M  \ | LSA    \   / Physics\
      \__ATLAS__/ |   ___   | |   ______/
         |   |    |  |   \  | |  |
         |   |    |  |___/  | |  \______     
         |   |    |         | |         \
         \___/    |________/   \________/
*/  
//  File Name  : pulse_hit_generator.v
//  Author     : Yu Liang
//  Revision   : 
//               First created on 2018-04-24 09:03:36
//  Note       : 
//     
module pulse_hit_generator(
input clk,
input rst,
input [11:0] width,
input start,
input inv,
output hit
);
reg [1:0] start_syn_r = 2'b0;
always @(posedge clk  ) begin
	if (rst) begin
		// reset
		start_syn_r <= 1'b0;
	end	else begin
		start_syn_r <= {start_syn_r[0],start};
	end
end
wire start_syn;
assign start_syn = (~start_syn_r[1])&start_syn_r[0];

reg [11:0] width_counter = 12'b0;
always @(posedge clk  ) begin
	if (rst) begin
		// reset
		width_counter <= 12'b0;
	end	else if (start_syn) begin
		width_counter <= width;
	end else if(|width_counter) begin
		width_counter <= width_counter - 12'b1;
	end 
end

wire hit_inner;
assign  hit_inner = |width_counter;
assign  hit = inv ? ~hit_inner:hit_inner;
endmodule


