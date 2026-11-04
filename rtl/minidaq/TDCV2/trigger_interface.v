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
// File   : trigger_interface.v
// Create : 2021-03-10 01:47:27
// Revise : 2026-06-08
// Editor : sublime text4, tab size (4)
// Description: 
//
// -----------------------------------------------------------------------------
module trigger_interface
(
    input clk_40,
    input rst_40,
    input mode_switch_rst,
    input run_enable,
    input clr_trig_fifo,
    input secondary_enable,
    input clr_trig_fifo_secondary,
    input bc_reset,
    input event_reset,
    input trigger_in,    
    input trigger_read,
    input trigger_read_secondary,

    output trigger_ready_out,
    
    output [29:0] trigger_fifo_data,
    output trigger_fifo_empty,
    output [29:0] trigger_fifo_data_secondary,
    output trigger_fifo_empty_secondary,
    //configuration
    input trigger_redge,
    input [11:0] rollover,
    input [11:0] coarse_count_offset,
    input [7:0] trigger_latency,
    input [15:0] trigger_deadtime

);

wire trigger_ready_delayed;
wire trigger_write;
wire [29:0] trigger_data_in;
wire [29:0] trigger_data_in_secondary;
wire [16:0] trigger_time;
wire [16:0] trigger_time_delayed;
wire trigger_fifo_full_tmp;
wire trigger_fifo_full;
wire trigger_fifo_full_secondary;
wire trigger_fifo_empty_tmp;
reg [11:0] event_count;
reg [13:0] trigger_coarse_reg;
wire trigger_ready;
reg [1:0] tick_reg;
wire delayed_write;
wire [28:0] delayed_trigger_data;
reg trigger_fifo_overflow;
reg trigger_fifo_overflow_secondary;
wire t0_clk;
wire t0_clk_rst;
wire run_enable_t0;
wire clr_trig_fifo_t0;
wire secondary_enable_t0;
wire clr_trig_fifo_secondary_t0;
wire [15:0] trigger_deadtime_t0;
wire [19:0] trigger_ctrl_t0;

reg [15:0] trigger_ready_block;  // driven by 160 MHz clock
wire trigger_allow;
wire gated_trigger_ready_delayed;
assign trigger_data_in = {trigger_fifo_overflow, event_count, trigger_time_delayed};
assign trigger_data_in_secondary =
    {trigger_fifo_overflow_secondary, event_count, trigger_time_delayed};

xpm_cdc_array_single #(
 .DEST_SYNC_FF   (2),
 .INIT_SYNC_FF   (0),
 .SIM_ASSERT_CHK (1),
 .SRC_INPUT_REG  (1),
 .WIDTH          (20)
) trigger_ctrl_cdc (
 .src_clk  (clk_40),
 .src_in   ({trigger_deadtime, clr_trig_fifo_secondary,
             secondary_enable, clr_trig_fifo, run_enable}),
 .dest_clk (t0_clk),
 .dest_out (trigger_ctrl_t0)
);

assign {trigger_deadtime_t0, clr_trig_fifo_secondary_t0,
        secondary_enable_t0, clr_trig_fifo_t0, run_enable_t0} = trigger_ctrl_t0;

assign trigger_allow = ~|trigger_ready_block;
assign gated_trigger_ready_delayed =
    trigger_ready_delayed & trigger_allow & run_enable_t0 &
    (~clr_trig_fifo_t0 |
     (secondary_enable_t0 & ~clr_trig_fifo_secondary_t0));

xpm_cdc_sync_rst #(
 .DEST_SYNC_FF   (5),
 .INIT           (1),
 .INIT_SYNC_FF   (0),
 .SIM_ASSERT_CHK (1)
) t0_clk_rst_sync (
 .src_rst  (rst_40 | event_reset | mode_switch_rst),
 .dest_clk (t0_clk),
 .dest_rst (t0_clk_rst)
);

always @(posedge t0_clk) begin
    if(t0_clk_rst) begin
        event_count <= 'b0;
        trigger_fifo_overflow <= 1'b0;
        trigger_fifo_overflow_secondary <= 1'b0;
    end else if(gated_trigger_ready_delayed) begin
        event_count <= event_count + 1'b1;  //
        trigger_fifo_overflow <= trigger_fifo_full;
        trigger_fifo_overflow_secondary <=
            secondary_enable_t0 && trigger_fifo_full_secondary;
    end
end


reg [1:0] tick_count;
always @(posedge t0_clk) begin
    if (t0_clk_rst)
        tick_count <= 2'b00;
    else
        tick_count <= tick_count + 1'b1;
end


always @(posedge t0_clk) begin
    if(t0_clk_rst) begin
        trigger_ready_block <= 'b0;
    end else if (gated_trigger_ready_delayed) begin
        trigger_ready_block <= trigger_deadtime_t0;
    end else if (~trigger_allow) begin
        if (&tick_count) begin
            trigger_ready_block <= trigger_ready_block - 1'b1;
        end
    end
end

t0_timestamp t0_timestamp_inst(
    .clk_40              (clk_40),
    // The timestamp must remain aligned with TDC BCIDs across acquisition modes.
    .reset_in            (rst_40|bc_reset),

    .trigger_ext         (trigger_in),
    .t0_timestamp        (trigger_time),
    .t0_ready            (trigger_ready),
    .clk0                (t0_clk),  //160 MHz clock
    
    .is_rising_edge      (trigger_redge),    
    .coarse_count_offset (coarse_count_offset),
    .rollover            (rollover)  
);



shift_ram_trigger shift_ram_trigger_inst (
  .A({trigger_latency,2'b00}),        // input wire [9 : 0] A
  .D({trigger_time,trigger_ready}),        // input wire [17 : 0] D
  .CLK(t0_clk),    // input wire CLK
  .SCLR(t0_clk_rst),  // input wire SCLR, only reset output register
  .Q({trigger_time_delayed,trigger_ready_delayed})        // output wire [17 : 0] Q
);

xpm_cdc_pulse #(
 .DEST_SYNC_FF   (2),
 .INIT_SYNC_FF   (0),
 .REG_OUTPUT     (1),
 .RST_USED       (1),
 .SIM_ASSERT_CHK (1)
) trigger_ready_cdc (
 .src_clk    (t0_clk),
 .src_pulse  (gated_trigger_ready_delayed),
 .src_rst    (t0_clk_rst),
 .dest_clk   (clk_40),
 .dest_rst   (rst_40 | event_reset | mode_switch_rst),
 .dest_pulse (trigger_ready_out)
);


// trigger_FIFO trigger_FIFO_delayed_inst (
//   .clk(clk_40),                  // input wire clk
//   .srst(rst_40),                // input wire srst
//   .din(trigger_data_in),                  // input wire [28 : 0] din
//   .wr_en(trigger_ready_delayed),              // input wire wr_en
//   .rd_en(trigger_read),              // input wire rd_en
//   .dout(trigger_fifo_data),                // output wire [28 : 0] dout
//   .full(trigger_fifo_full),                // output wire full
//   .empty(trigger_fifo_empty),              // output wire empty
//   .wr_rst_busy(),  // output wire wr_rst_busy
//   .rd_rst_busy()  // output wire rd_rst_busy
// );



//sync FPGA tdc data from 160 MHz to 40 MHz
trigger_FIFO trigger_FIFO_delayed_inst (
  .srst        (t0_clk_rst | ~run_enable_t0 | clr_trig_fifo_t0),  // synchronous to wr_clk
  .wr_clk      (t0_clk),            // input wire wr_clk
  .rd_clk      (clk_40),            // input wire rd_clk
  .din         (trigger_data_in),                  // input wire [29 : 0] din
  .wr_en       (gated_trigger_ready_delayed & ~clr_trig_fifo_t0), // input wire wr_en
  .rd_en       (trigger_read & run_enable & ~clr_trig_fifo),  // input wire rd_en
  .dout        (trigger_fifo_data),                // output wire [29 : 0] dout
  .full        (trigger_fifo_full),                // output wire full
  .empty       (trigger_fifo_empty),              // output wire empty
  .wr_rst_busy (),  // output wire wr_rst_busy
  .rd_rst_busy ()  // output wire rd_rst_busy
);

// Triggerless chamber 1 receives the same accepted triggers and maintains an
// independent read pointer.  This prevents one chamber's event builder from
// consuming triggers that the other chamber still needs.
trigger_FIFO trigger_FIFO_secondary_inst (
  .srst        (t0_clk_rst | ~run_enable_t0 | ~secondary_enable_t0 |
                clr_trig_fifo_secondary_t0),
  .wr_clk      (t0_clk),
  .rd_clk      (clk_40),
  .din         (trigger_data_in_secondary),
  .wr_en       (gated_trigger_ready_delayed & secondary_enable_t0 &
                ~clr_trig_fifo_secondary_t0),
  .rd_en       (trigger_read_secondary & run_enable & secondary_enable &
                ~clr_trig_fifo_secondary),
  .dout        (trigger_fifo_data_secondary),
  .full        (trigger_fifo_full_secondary),
  .empty       (trigger_fifo_empty_secondary),
  .wr_rst_busy (),
  .rd_rst_busy ()
);


ila_trigger_interface ila_trigger_interface_inst (
    .clk(clk_40), // input wire clk


    .probe0(rst_40), // input wire [0:0]  probe0  
    .probe1(trigger_fifo_full), // input wire [0:0]  probe1 
    .probe2(trigger_read), // input wire [0:0]  probe2 
    .probe3(trigger_fifo_data), // input wire [29:0]  probe3 
    .probe4(trigger_fifo_empty), // input wire [0:0]  probe4 
    .probe5(trigger_allow),  // input wire [0:0]  probe5 
    .probe6(trigger_ready_block), // input wire [15:0]  probe6 
    .probe7(trigger_in) // input wire [0:0]  probe7 
);



endmodule
