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
// File   : tdc_fifo_data_mux.v
// Create : 2021-03-14 17:36:43
// Revise : 2021-03-16 00:47:06
// Editor : sublime text3, tab size (4)
// Description: 
//
// -----------------------------------------------------------------------------

module tdc_fifo_data_mux
    #(parameter TDC_COUNT = 8,
           TDC_DATA_WIDTH = 40)
(
    input  [TDC_COUNT-1:0] locked,
    input  [TDC_COUNT-1:0] tdc_fifo_empty,
    input  [TDC_COUNT*TDC_DATA_WIDTH-1:0] tdc_fifo_data,
    input  [TDC_COUNT-1:0] matching_busy,
    output [TDC_COUNT-1:0] tdc_fifo_read,

    output tdc_fifo_empty_mux,
    output [TDC_DATA_WIDTH-1:0] tdc_fifo_data_mux,
    output matching_busy_mux,
    input  tdc_fifo_read_mux
);
wire [TDC_COUNT-1:0] readable;
assign matching_busy_mux = |(locked&matching_busy);
assign tdc_fifo_empty_mux = &((~locked)|tdc_fifo_empty);

generate
    genvar i;
    for(i=0;i<TDC_COUNT;i=i+1) begin
        assign readable[i] = tdc_fifo_read_mux&locked[i]&(~tdc_fifo_empty[i]);
    end
endgenerate

multi_hot_one_hot #(.WIDTH(TDC_COUNT)) 
multi_hot_one_hot_inst(
    .multi_hot_code(readable),
    .one_hot_code(tdc_fifo_read)
);
one_hot_select #(.DATA_WIDTH(TDC_DATA_WIDTH),.DATA_DEPTH(TDC_COUNT))
one_hot_select_inst(
    .one_hot_code(tdc_fifo_read),
    .data_in(tdc_fifo_data),
    .data_out(tdc_fifo_data_mux)
);

endmodule
