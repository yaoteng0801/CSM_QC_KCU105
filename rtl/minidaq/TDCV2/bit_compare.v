/* 
       _________   ________     ________       
      / U OF M  \ | LSA    \   / Physics\
      \__ATLAS__/ |   ___   | |   ______/
         |   |    |  |   \  | |  |
         |   |    |  |___/  | |  \______     
         |   |    |         | |         \
         \___/    |________/   \________/
*/ 
//==================================================================================================
//  Filename      : bit_compare.v
//  Created On    : 2021-05-27 15:36:00
//  Last Modified : 2021-05-27 15:37:21
//  Revision      : 
//  Author        : Yuxiang Guo
//  Company       : University of Michigan
//  Email         : gyuxiang@umich.edu
//
//  Description   : 
//
//
//==================================================================================================


module bit_compare
#(parameter BIT_IN = 10,
            BIT_OUT = 4)
    (
    input [BIT_IN-1:0] a,
    input [BIT_IN-1:0] b,
    output reg [BIT_OUT-1:0] out
);
integer i;
wire [BIT_IN-1:0] x_or;
assign x_or = a ^ b;

always@(x_or)
begin
    out = 0;  //initialize count variable.
    for(i=0;i<BIT_IN;i=i+1)   //check for all the bits.
        if(x_or[i] == 1'b1)    //check if the bit is '1'
            out = out + 1;    //if its one, increment the count.
end

endmodule