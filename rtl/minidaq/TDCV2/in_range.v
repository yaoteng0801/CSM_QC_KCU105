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
// File   : in_range.v
// Create : 2021-03-08 11:28:56
// Revise : 2021-03-10 00:55:39
// Editor : sublime text3, tab size (4)
// Description: 
//
// -----------------------------------------------------------------------------
module in_range #(parameter WIDTH = 12)
(
    output reg flag,
    input [WIDTH-1:0] in,
    input [WIDTH-1:0] start,
    input [WIDTH-1:0] stop	
);

always @(*) begin 
    if ((in>=start)&(in<=stop))         flag = 1'b1;
    else if ((in>=start)&(start>stop))  flag = 1'b1;
    else if ((in<=stop)&(stop<start))   flag = 1'b1;
    else                                flag = 1'b0;                                       
end
endmodule
