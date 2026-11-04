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
// File   : rollover_add.v
// Create : 2021-03-08 01:55:01
// Revise : 2021-03-08 10:31:43
// Editor : sublime text3, tab size (4)
// Description: 
//
// -----------------------------------------------------------------------------
module rollover_add #(parameter WIDTH = 12)
(
	output reg [WIDTH-1:0] out,
	input [WIDTH-1:0] in,
	input [WIDTH-1:0] add,
	input [WIDTH-1:0] rollover	
);

always @(*) begin 
	if ((rollover-in)>=add) out = in+add;
	else                    out = in+add-rollover-1'b1;
end
endmodule
