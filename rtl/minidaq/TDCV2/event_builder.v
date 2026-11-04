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
// File   : event_builder.v
// Create : 2021-03-14 17:36:43
// Revise : 2024-09-20 03:01:01
// Editor : sublime text4, tab size (4)
// Description: 
//
// -----------------------------------------------------------------------------

module event_builder
(
    input clk,
    
    input rst,
    input enable,

    input trigger_fifo_empty,        
    input [29:0] trigger_fifo_data,
    output reg trigger_fifo_read,

    input tdc_fifo_empty,
    input [39:0] tdc_fifo_data,
    input matching_busy,    
    output reg tdc_fifo_read,
    
    input readout_fifo_full,
    output reg [39:0] event_data,
    output reg event_data_ready,
    output reg building_busy
);

reg [9:0] hit_count;
reg [5:0] state;
reg [5:0] nextstate;
reg [29:0] trigger_data_reg;
reg [5:0] eventID_MSBext;


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
        hit_count <='b0;
    end else if (nextstate[GET_TRIGGER_INFO_BIT]) begin
        hit_count <='b0;
    end else if(tdc_fifo_read) begin
        hit_count <= hit_count+'b1;
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
            nextstate = (~matching_busy)? SEND_HEAD :
                        tdc_fifo_empty ? WAIT_TDC_DATA : SEND_HEAD;
        SEND_HEAD:
            nextstate = readout_fifo_full ? SEND_HEAD : SEND_TDC_DATA;
        SEND_TDC_DATA:
            nextstate = readout_fifo_full ? SEND_TDC_DATA :
                         (~tdc_fifo_empty) ? SEND_TDC_DATA : 
                          matching_busy    ? SEND_TDC_DATA : SEND_TRAIL;
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
    if (readout_fifo_full) begin 
        event_data_ready = 1'b0;
        event_data = 'b0;
        tdc_fifo_read = 1'b0;
    end else begin
        if (state[SEND_HEAD_BIT]) begin
            event_data_ready = 1'b1;
            event_data       = {4'b1010,trigger_data_reg[29],eventID_MSBext,trigger_data_reg[28:0]};
            tdc_fifo_read    = 1'b0;
        end else if (state[SEND_TDC_DATA_BIT] ) begin
            event_data_ready = ~tdc_fifo_empty;
            event_data       = tdc_fifo_data;
            tdc_fifo_read    = ~tdc_fifo_empty;
        end else if (state[SEND_TRAIL_BIT] ) begin
            event_data_ready = 1'b1;
            event_data       = {4'b1100,8'b0,trigger_data_reg[28:17],6'b0,hit_count};
            tdc_fifo_read    = 1'b0;
        end else begin
            event_data_ready = 1'b0;
            event_data       = 'b0;
            tdc_fifo_read    = 1'b0;
        end
    end
end

ila_event_builder ila_event_builder_inst (
    .clk(clk), // input wire clk

    .probe0(trigger_fifo_empty), // input wire [0:0]  probe0  
    .probe1(trigger_fifo_data), // input wire [29:0]  probe1 
    .probe2(trigger_fifo_read), // input wire [0:0]  probe2 
    .probe3(tdc_fifo_empty), // input wire [0:0]  probe3 
    .probe4(tdc_fifo_data), // input wire [39:0]  probe4 
    .probe5(matching_busy), // input wire [0:0]  probe5 
    .probe6(tdc_fifo_read), // input wire [0:0]  probe6 
    .probe7(readout_fifo_full), // input wire [0:0]  probe7 
    .probe8(event_data), // input wire [39:0]  probe8 
    .probe9(event_data_ready), // input wire [0:0]  probe9 
    .probe10(building_busy), // input wire [0:0]  probe10 
    .probe11(hit_count), // input wire [9:0]  probe11 
    .probe12(state), // input wire [5:0]  probe12 
    .probe13(nextstate) // input wire [5:0]  probe13 
);

endmodule


