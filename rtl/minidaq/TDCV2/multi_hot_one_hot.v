/* 
       _________   ________     ________       
      / U OF M  \ | LSA    \   / Physics\
      \__ATLAS__/ |   ___   | |   ______/
         |   |    |  |   \  | |  |
         |   |    |  |___/  | |  \______     
         |   |    |         | |         \
         \___/    |________/   \________/
*/  
//  File Name  : multi_hot_one_hot.v
//  Author     : Yu Liang
//  Revision   : 
//               First created on June 30st, 2017
//  Note       : example: input: 0111001011
//                        output:0100000000
// 
module multi_hot_one_hot #(
	parameter WIDTH=8
	)
(
    input [WIDTH-1:0] multi_hot_code,
    output [WIDTH-1:0] one_hot_code
    );

wire [WIDTH-1:0] multi_hot_code_inv;
assign  multi_hot_code_inv = ~multi_hot_code;
assign one_hot_code[WIDTH-1] = multi_hot_code[WIDTH-1];
generate
	genvar i;
	for (i = 1; i < WIDTH; i = i + 1)
	begin:multi_hot_one_hot_trans
		assign one_hot_code[WIDTH-1-i] = (&multi_hot_code_inv[WIDTH-1:WIDTH-i])&multi_hot_code[WIDTH-1-i];
	end
endgenerate
endmodule