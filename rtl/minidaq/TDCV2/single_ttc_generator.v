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
// File   : single_ttc_generator.v
// Create : 2021-03-16 10:14:49
// Revise : 2025-07-29 16:58:07
// Editor : sublime text4, tab size (4)
// Description: 
//
// -----------------------------------------------------------------------------

module single_ttc_generator
(
    input clk_40,
    input rst_40,
    output [1:0] encode_ttc,
    output fpga_bcr, //width synchoronized to one clk_40

    input trigger,
    input bc_reset,
    input event_reset,
    input master_reset
);

localparam IDLE                    = 6'b000001;
localparam WAIT_BC_RESET           = 6'b000010;
localparam PROCESSING_BC_RESET     = 6'b000100;
localparam PROCESSING_TRIGGER      = 6'b001000;
localparam PROCESSING_EVENT_RESET  = 6'b010000;
localparam PROCESSING_MASTER_RESET = 6'b100000;
reg [5:0] state;
reg [5:0] nextstate;

reg  bc_reset_r    ;
reg  trigger_r     ;
reg  event_reset_r ;
reg  master_reset_r;
reg [2:0] trigger_syn     ;
reg [2:0] bc_reset_syn    ;
reg [2:0] event_reset_syn ;
reg [2:0] master_reset_syn;

reg [5:0] legacy_ttc;
reg [1:0] ttc_busy_counter;

reg trigger_waiting;
reg master_reset_waiting;
reg event_reset_waiting;

reg trigger_read;
reg master_reset_read;
reg event_reset_read;

assign encode_ttc = legacy_ttc[5:4];
assign fpga_bcr = bc_reset_syn[2];

reg [1:0] bc_reset_by_rst_40_syn;
reg [1:0] event_reset_by_rst_40_syn;
wire bc_reset_by_rst_40;
wire event_reset_by_rst_40;

//bc_reset_by_rst_40 and event_reset_by_rst_40 must follow the rst_40 falling edge, otherwise state machine is in reset
assign bc_reset_by_rst_40 = bc_reset_by_rst_40_syn[1]&(~bc_reset_by_rst_40_syn[0]);  //falling edge found
assign event_reset_by_rst_40 = event_reset_by_rst_40_syn[1]&(~event_reset_by_rst_40_syn[0]); //falling edge found

always @(posedge clk_40) begin
    bc_reset_by_rst_40_syn <= {bc_reset_by_rst_40_syn[0], rst_40};
    event_reset_by_rst_40_syn <= {event_reset_by_rst_40_syn[0], rst_40};
end



always @(posedge clk_40) begin
    bc_reset_r       <= {bc_reset|bc_reset_by_rst_40};
    trigger_r        <= {trigger};    
    event_reset_r    <= {event_reset|event_reset_by_rst_40};
    master_reset_r   <= {master_reset};
    bc_reset_syn     <= {bc_reset_syn    [1:0],(~bc_reset_r    )&(bc_reset|bc_reset_by_rst_40)};
    trigger_syn      <= {trigger_syn     [1:0],(~trigger_r     )&trigger     };    
    event_reset_syn  <= {event_reset_syn [1:0],(~event_reset_r )&(event_reset|event_reset_by_rst_40)};
    master_reset_syn <= {master_reset_syn[1:0],(~master_reset_r)&master_reset};
end



always @(posedge clk_40) begin
    if(rst_40) begin
        trigger_waiting <= 1'b0;
        event_reset_waiting <= 1'b0;
        master_reset_waiting <= 1'b0;        
    end else if (trigger_syn[1]|event_reset_syn[1]|master_reset_syn[1]) begin
        if (trigger_syn[1]) trigger_waiting <= 1'b1;
        if (event_reset_syn[1]) event_reset_waiting <= 1'b1;
        if (master_reset_syn[1]) master_reset_waiting <= 1'b1;
    end else if (trigger_read|event_reset_read|master_reset_read) begin
        if (trigger_read) trigger_waiting <= 1'b0;
        if (event_reset_read) event_reset_waiting <= 1'b0;
        if (master_reset_read) master_reset_waiting <= 1'b0;
    end
end

always @(posedge clk_40  ) begin
    if (rst_40) begin
        // reset
        state <= IDLE;
    end else begin
        state <= nextstate;
    end
end

always @(*) begin
    case(state)
        IDLE: 
            nextstate = bc_reset_syn[2] ? PROCESSING_BC_RESET : 
                        (|bc_reset_syn[1:0]) ? WAIT_BC_RESET :
                        trigger_waiting ? PROCESSING_TRIGGER :
                        event_reset_waiting ? PROCESSING_EVENT_RESET :
                        master_reset_waiting ? PROCESSING_MASTER_RESET : IDLE;
        WAIT_BC_RESET:
            nextstate = bc_reset_syn[2]? PROCESSING_BC_RESET : WAIT_BC_RESET;
        PROCESSING_BC_RESET:
            nextstate = (|ttc_busy_counter)?PROCESSING_BC_RESET:IDLE;
        PROCESSING_TRIGGER:
            nextstate = (|ttc_busy_counter)?PROCESSING_TRIGGER:IDLE;
        PROCESSING_EVENT_RESET:
            nextstate = (|ttc_busy_counter)?PROCESSING_EVENT_RESET:IDLE;
        PROCESSING_MASTER_RESET:
            nextstate = (|ttc_busy_counter)?PROCESSING_MASTER_RESET:IDLE;
        default: nextstate = IDLE;
    endcase
end

always @(posedge clk_40) begin
    if(rst_40) 
        ttc_busy_counter <= 2'b0;
    if(state!=nextstate) begin
        ttc_busy_counter <= 2'b01;
    end else if(|ttc_busy_counter) begin 
        ttc_busy_counter <= ttc_busy_counter - 2'b1;
    end
end

always @(posedge clk_40) begin
    if (rst_40) begin
        // reset
        legacy_ttc <= 6'b000000;
    end else if (state==IDLE) begin
        if (nextstate == PROCESSING_BC_RESET)
            legacy_ttc <= 6'b111100;
        else if (nextstate == PROCESSING_TRIGGER)
            legacy_ttc <= 6'b110000;
        else if (nextstate == PROCESSING_EVENT_RESET)
            legacy_ttc <= 6'b111111;
        else if (nextstate == PROCESSING_MASTER_RESET)
            legacy_ttc <= 6'b110011;
        else legacy_ttc <= {legacy_ttc[3:0],2'b00};
    end else if(state==WAIT_BC_RESET) begin
        if (nextstate == PROCESSING_BC_RESET)
            legacy_ttc <= 6'b111100;
        else
            legacy_ttc <= 6'b000000;
    end else begin
        legacy_ttc <= {legacy_ttc[3:0],2'b00};
    end
end

always @(posedge clk_40) begin
    if (rst_40) begin
        // reset
        trigger_read      <= 1'b0;
        event_reset_read  <= 1'b0;
        master_reset_read <= 1'b0;
    end else if (state==IDLE) begin
        if (nextstate == PROCESSING_TRIGGER)
            trigger_read <= 1'b1;
        else if (nextstate == PROCESSING_EVENT_RESET)
            event_reset_read <= 1'b1;
        else if (nextstate == PROCESSING_MASTER_RESET)
            master_reset_read <= 1'b1;
    end else begin
        trigger_read      <= 1'b0;
        event_reset_read  <= 1'b0;
        master_reset_read <= 1'b0;
    end
end

ila_ttc_gen ila_ttc_gen_inst (
    .clk(clk_40), // input wire clk
    .probe0(state), // input wire [5:0]  probe0  
    .probe1(nextstate), // input wire [5:0]  probe1 
    .probe2(trigger_syn), // input wire [2:0]  probe2 
    .probe3(bc_reset_syn), // input wire [2:0]  probe3 
    .probe4(event_reset_syn), // input wire [2:0]  probe4 
    .probe5(master_reset_syn), // input wire [2:0]  probe5 
    .probe6(encode_ttc), // input wire [1:0]  probe6 
    .probe7(ttc_busy_counter), // input wire [0:0]  probe7 
    .probe8(fpga_bcr), // input wire [0:0]  probe8 
    .probe9(trigger), // input wire [0:0]  probe9 
    .probe10(bc_reset), // input wire [0:0]  probe10 
    .probe11(event_reset), // input wire [0:0]  probe11 
    .probe12(master_reset), // input wire [0:0]  probe12
    .probe13(rst_40) // input wire [0:0]  probe13

);


endmodule
