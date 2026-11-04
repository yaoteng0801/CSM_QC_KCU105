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
// File   : event_builder_triggermode.v
// Create : 2021-08-27 19:48:30
// Revise : 2024-09-20 03:01:15
// Editor : sublime text4, tab size (4)
// Description: 
//
// -----------------------------------------------------------------------------
`define HEADER_FILL 8'b1111_1000 
`define TRAILER_FILL 8'b1111_0000 

module event_builder_triggermode
    #(parameter TDC_COUNT = 10,
           TDC_DATA_WIDTH = 40)
(
    input clk,
    input rst,
    input enable,    

    // trigger fifo interface
    input trigger_fifo_empty,        
    input [29:0] trigger_fifo_data,
    output reg trigger_fifo_read,

    // tdc fifo interface
    input  [TDC_COUNT-1:0] locked_array,
    input  [TDC_COUNT-1:0] tdc_fifo_empty_array,
    input  [TDC_COUNT*TDC_DATA_WIDTH-1:0] tdc_fifo_data_array,
    output [TDC_COUNT-1:0] tdc_fifo_read_array,

    // readout fifo interface
    input readout_fifo_full,
    output reg [39:0] event_data,
    output reg event_data_ready
);

localparam IDLE                 = 6'b000001;
localparam GET_TRIGGER_INFO     = 6'b000010;
localparam WAIT_TDC_DATA        = 6'b000100;
localparam SEND_HEAD            = 6'b001000;
localparam SEND_TDC_DATA        = 6'b010000;
localparam SEND_TRAIL           = 6'b100000;

localparam IDLE_BIT             = 0;
localparam GET_TRIGGER_INFO_BIT = 1;
localparam WAIT_TDC_DATA_BIT    = 2;
localparam SEND_HEAD_BIT        = 3;
localparam SEND_TDC_DATA_BIT    = 4;
localparam SEND_TRAIL_BIT       = 5;

wire [TDC_COUNT-1:0] tdc_mux_one_hot;
wire [TDC_DATA_WIDTH-1:0] tdc_fifo_data_single;
reg tdc_fifo_read_single;
wire is_header, is_trailer;
reg building_busy;

reg [5:0] state;
reg [5:0] nextstate;
reg [29:0] trigger_data_reg;
reg [5:0] eventID_MSBext;

reg [9:0] hit_count;
reg [3:0] header_count;
reg [3:0] trailer_count;
wire header_count_error;
wire trailer_count_error;
reg [TDC_COUNT-1:0] tdc_trailer_found;  //1 indicates a trailer of a TDC is found for the current event
reg [TDC_COUNT-1:0] tdc_header_found;   //1 indicates a header of a TDC is found for the current event
reg [TDC_COUNT-1:0] tdc_readable;   //1 indicates the fifo data of a TDC 
                                    //is not readout completely for the current event


assign tdc_fifo_read_array = {TDC_COUNT{tdc_fifo_read_single}} & tdc_mux_one_hot;
assign is_header  = (tdc_fifo_data_single[31:24] == `HEADER_FILL) ? 1'b1 : 1'b0;
assign is_trailer = (tdc_fifo_data_single[31:24] == `TRAILER_FILL) ? 1'b1 : 1'b0;
assign header_count_error  = (tdc_header_found ==locked_array)?1'b0:1'b1;
assign trailer_count_error = (tdc_trailer_found==locked_array)?1'b0:1'b1;


multi_hot_one_hot #(.WIDTH(TDC_COUNT)) 
multi_hot_one_hot_inst(
    .multi_hot_code(tdc_readable&(~tdc_fifo_empty_array)),
    .one_hot_code(tdc_mux_one_hot)
);

one_hot_select #(.DATA_WIDTH(TDC_DATA_WIDTH),.DATA_DEPTH(TDC_COUNT))
one_hot_select_inst(
    .one_hot_code(tdc_mux_one_hot),
    .data_in(tdc_fifo_data_array),
    .data_out(tdc_fifo_data_single)
);

always @(posedge clk  ) begin
    if (rst) begin
        // reset
        state <= IDLE;
    end else begin
        state <= enable ? nextstate : IDLE;
    end
end

always @(posedge clk  ) begin
    if (rst) begin
        // reset
        tdc_header_found  <= 'b0;
        tdc_trailer_found <= 'b0;
        tdc_readable      <= 'b0;
    end else if (nextstate[GET_TRIGGER_INFO_BIT]) begin
        tdc_header_found  <= 'b0;
        tdc_trailer_found <= 'b0;
        tdc_readable      <= locked_array;
    end else if (state[SEND_TDC_DATA_BIT]) begin
        if(is_header) begin
            tdc_header_found  <= tdc_header_found |tdc_mux_one_hot;
        end else if(is_trailer) begin
            tdc_trailer_found <= tdc_trailer_found|tdc_mux_one_hot;
            tdc_readable      <= tdc_readable^tdc_mux_one_hot;
        end
    end
end

always @(posedge clk  ) begin
    if (rst) begin
        // reset
        header_count  <='b0;
        trailer_count <='b0;
        hit_count     <='b0;
    end else if (nextstate[GET_TRIGGER_INFO_BIT]) begin
        header_count  <='b0;
        trailer_count <='b0;
        hit_count     <='b0;
    end else if(tdc_fifo_read_single) begin
        if(is_header) begin
            header_count  <= header_count + 1'b1;
        end else if (is_trailer) begin
            trailer_count <= trailer_count + 1'b1;
        end else begin
            hit_count     <= hit_count+1'b1;
        end
    end
end

always @(posedge clk  ) begin
    if (rst) begin
        // reset
        eventID_MSBext <='b0;
    end else if (state[SEND_HEAD_BIT]&nextstate[SEND_TDC_DATA_BIT]) begin
        if (trigger_data_reg[28:17]==12'hFFF) eventID_MSBext<=eventID_MSBext+1'b1;
    end
end

always @(*) begin
    case(state)
        IDLE: 
            nextstate = enable&(~trigger_fifo_empty) ? GET_TRIGGER_INFO : IDLE;
        GET_TRIGGER_INFO:
            nextstate = WAIT_TDC_DATA;
        WAIT_TDC_DATA:
            nextstate = (|tdc_mux_one_hot)? SEND_HEAD  : WAIT_TDC_DATA;
        SEND_HEAD:
            nextstate = readout_fifo_full ? SEND_HEAD : SEND_TDC_DATA;
        SEND_TDC_DATA:
            nextstate = readout_fifo_full ? SEND_TDC_DATA :
                         (|tdc_readable)  ? SEND_TDC_DATA : SEND_TRAIL;
        SEND_TRAIL:
            nextstate = readout_fifo_full ? SEND_TRAIL:IDLE;
        default: nextstate = IDLE;
    endcase
end

always @(posedge clk  ) begin
    if (rst) begin
        // reset
        trigger_fifo_read <= 1'b0;
    end else if (nextstate[GET_TRIGGER_INFO_BIT]) begin
        trigger_fifo_read <= 1'b1;
    end else begin
        trigger_fifo_read <= 1'b0;
    end
end

always @(posedge clk  ) begin
    if (rst) begin
        // reset
        building_busy <= 1'b0;
    end else if (nextstate[GET_TRIGGER_INFO_BIT]) begin
        building_busy <= 1'b1;
    end else if (nextstate[SEND_TRAIL_BIT]) begin
        building_busy <= 1'b0;
    end
end

always @(posedge clk  ) begin
    if (rst) begin
        // reset
        trigger_data_reg <= 'b0;
    end else if (nextstate[GET_TRIGGER_INFO_BIT]) begin
        trigger_data_reg <= trigger_fifo_data;
    end else if (nextstate[IDLE_BIT]) begin
        trigger_data_reg <= 'b0;
    end
end


//combination output 
always @(*) begin
    if (readout_fifo_full|rst) begin 
        event_data_ready     = 1'b0;
        event_data           = 'b0;
        tdc_fifo_read_single = 1'b0;
    end else begin
        if (state[SEND_HEAD_BIT]) begin
            event_data_ready     = 1'b1;
            event_data           = {4'b1010,trigger_data_reg[29],eventID_MSBext,trigger_data_reg[28:0]};
            tdc_fifo_read_single = 1'b0;
        end else if (state[SEND_TDC_DATA_BIT] ) begin
            event_data_ready     = ~(&tdc_fifo_empty_array);
            event_data           = tdc_fifo_data_single;
            tdc_fifo_read_single = ~(&tdc_fifo_empty_array);
        end else if (state[SEND_TRAIL_BIT] ) begin
            event_data_ready     = 1'b1;
            event_data           = {4'b1100,header_count,trailer_count,trigger_data_reg[28:17],
                                    header_count_error, trailer_count_error, 4'b0,hit_count};
            tdc_fifo_read_single = 1'b0;
        end else begin
            event_data_ready     = 1'b0;
            event_data           = 'b0;
            tdc_fifo_read_single = 1'b0;
        end
    end
end


(* dont_touch = "true" *) wire [9:0] tdc_fifo_empty_array_ila;
(* dont_touch = "true" *) wire [9:0] tdc_fifo_read_array_ila;
(* dont_touch = "true" *) wire [9:0] tdc_readable_ila;
(* dont_touch = "true" *) wire [9:0] tdc_mux_one_hot_ila;
(* dont_touch = "true" *) wire [9:0] tdc_header_found_ila;
(* dont_touch = "true" *) wire [9:0] tdc_trailer_found_ila;




genvar i;
generate
    for(i=0;i<10;i=i+1) begin
        assign tdc_fifo_empty_array_ila[i]  = i<TDC_COUNT ? tdc_fifo_empty_array[i]   : 'b1;
        assign tdc_fifo_read_array_ila[i]   = i<TDC_COUNT ? tdc_fifo_read_array[i]    : 'b0;
        assign tdc_readable_ila[i]          = i<TDC_COUNT ? tdc_readable[i]           : 'b0;
        assign tdc_mux_one_hot_ila[i]       = i<TDC_COUNT ? tdc_mux_one_hot[i]        : 'b0;
        assign tdc_header_found_ila[i]      = i<TDC_COUNT ? tdc_header_found[i]       : 'b0;
        assign tdc_trailer_found_ila[i]     = i<TDC_COUNT ? tdc_trailer_found[i]      : 'b0;

    end
endgenerate


ila_event_builder_triggermode ila_event_builder_triggermode_inst (
    .clk(clk), // input wire clk

    .probe0(trigger_fifo_empty), // input wire [0:0]  probe0  
    .probe1(trigger_fifo_data), // input wire [29:0]  probe1 
    .probe2(trigger_fifo_read), // input wire [0:0]  probe2 
    .probe3(tdc_fifo_empty_array_ila), // input wire [9:0]  probe3 
    .probe4(tdc_fifo_read_array_ila), // input wire [9:0]  probe4 
    .probe5(tdc_readable_ila), // input wire [9:0]  probe5 
    .probe6(tdc_header_found_ila), // input wire [9:0]  probe6 
    .probe7(tdc_trailer_found_ila), // input wire [9:0]  probe7 
    .probe8(tdc_mux_one_hot_ila), // input wire [9:0]  probe8
    .probe9(is_header), // input wire [0:0]  probe9 
    .probe10(is_trailer), // input wire [0:0]  probe10 
    .probe11(header_count_error), // input wire [0:0]  probe11 
    .probe12(trailer_count_error), // input wire [0:0]  probe12 
    .probe13(tdc_fifo_data_single), // input wire [39:0]  probe13 
    .probe14(readout_fifo_full), // input wire [0:0]  probe14 
    .probe15(event_data), // input wire [39:0]  probe15 
    .probe16(event_data_ready), // input wire [0:0]  probe16 
    .probe17(building_busy), // input wire [0:0]  probe17 
    .probe18(hit_count), // input wire [9:0]  probe18 
    .probe19(state), // input wire [5:0]  probe19 
    .probe20(nextstate) // input wire [5:0]  probe20
);

endmodule


