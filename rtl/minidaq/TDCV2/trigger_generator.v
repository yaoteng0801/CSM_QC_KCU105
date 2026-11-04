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
// File   : trigger_generator.v
// Create : 2024-12-05 15:28:16
// Revise : 2024-12-05 15:59:46
// Editor : sublime text4, tab size (4)
// Description: 
//
// -----------------------------------------------------------------------------
//     
module trigger_generator(
    input clk,
    input rst,
    input enable,
    output trigger_out,

    input [11:0] width,
    input start,
    input inv,
    input [23:0] interval,

    input start_single
);


wire start_pulse;
reg  [23:0] interval_counter;

pulse_hit_generator pulse_hit_generator_inst (
    .clk(clk), 
    .rst(rst), 
    .width(width), 
    .start(start_pulse), 
    .inv(inv), 
    .hit(trigger_out)
);


always @(posedge clk) begin
    if (rst) begin
        interval_counter <= 24'b0;
    end else if (enable) begin
        interval_counter <= (interval_counter == interval) ? 24'b0 : interval_counter +24'b1;
    end
end

assign start_pulse = enable & ((start & ( interval_counter == interval ))|start_single);


endmodule

