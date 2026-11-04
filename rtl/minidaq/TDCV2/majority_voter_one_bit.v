/* 
       _________   ________     ________       
      / U OF M  \ | LSA    \   / Physics\
      \__ATLAS__/ |   ___   | |   ______/
         |   |    |  |   \  | |  |
         |   |    |  |___/  | |  \______     
         |   |    |         | |         \
         \___/    |________/   \________/
*/  

// Author : Yu Liang
// File   : majority_voter_one_bit.sv
// Create : 2019-03-12 14:17:17
// Revise : 2019-03-12 14:17:17
// Editor : sublime text4, tab size (4)
// Description: 
//
// -----------------------------------------------------------------------------

module majority_voter_one_bit
(
	input  inA,
	input  inB,
	input  inC,
	output reg out,
	output reg err);
	always @(*) begin
		if (inA == inB) begin
			out = inA;
			err = (inB == inC) ? 1'b0 : 1'b1;
		end	else begin
			out = inC;
			err = 1'b1;
		end
	end
endmodule