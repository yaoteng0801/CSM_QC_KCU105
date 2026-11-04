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
// File   : rollover_sub.v
// Create : 2021-03-08 10:14:36
// Revise : 2021-03-10 01:34:45
// Editor : sublime text3, tab size (4)
// Description: 
//
// -----------------------------------------------------------------------------
module rollover_sub #(parameter WIDTH = 12)
(
    output reg [WIDTH-1:0] out,
    input [WIDTH-1:0] in,
    input [WIDTH-1:0] sub,
    input [WIDTH-1:0] rollover
);

always @(*) begin
    if (in>=sub) out = in-sub;
    else         out = in-sub+rollover+1'b1;
end
endmodule
