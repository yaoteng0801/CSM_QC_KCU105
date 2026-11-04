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
// File   : trigger_matching.v
// Create : 2021-02-28 19:16:46
// Revise : 2021-03-08 10:37:56
// Editor : sublime text3, tab size (4)
// Description: 
// Note: The following criteria must be fullfilled:
// 		rollover>=match_window;
// 		rollover>=bc_offset;
// 		rollover>=reject_offset.
// -----------------------------------------------------------------------------

`timescale 1ns / 1ps
`define WARNING_CHANNEL 5'b11101
`define ERROR_CHANNEL 5'b11110


module trigger_matching (
	input clk_40,
    input rst_40,
	input [31:0] tdc_hit_data,
	input tdc_hit_data_valid,

	// input sys_clk_160,
	// input rst_160,	
	input ram_read,
	//trigger interface
	input enable_matching,
	input enable_matching_timeout,
	input building_busy,	
	input trigger_fifo_empty,
	input [16:0] trigger_fifo_data,
	output reg [31:0] matched_data,	
	output reg  match_valid,
	output matching_busy,
	//configuration

	input enable_relative_trigger_data,	
	input [11:0] rollover,
    input [11:0] trigger_coarse,
	
	input [11:0] match_window,
	input [11:0] search_margin,
	input [11:0] bc_offset,
	input [11:0] reject_offset		
	);

localparam  IDLE           = 5'b00001,
            TRIGGER_IN     = 5'b00010,
            MATCHING_START = 5'b00100,
            MATCHING       = 5'b01000,
            LAST           = 5'b10000;


reg matching_busy_reg;
reg [2:0] matching_busy_reg_delay;


//hit interface
wire sync_fifo_empty;
wire [31:0] tdc_hit_data_sync;

//trigger interface
reg  [16:0] trigger_reg;
wire [11:0] trigger_BCID;
wire [11:0] reject_counter;
wire [11:0] match_start;
wire [11:0] match_stop;
wire [11:0] search_start;
wire [11:0] search_stop;

//hit ram
reg  [9:0] waddr, raddr, saddr;
reg  [9:0] raddr_reg;
wire ram_empty;
wire ram_full;
wire [31:0] ram_data_out;
wire [11:0] ram_data_BCID;
wire [16:0] ram_data_leading;

reg  ram_empty_reg;
wire ram_read_ready;


//trigger matching
wire in_range_keep;
wire in_range_match;
wire in_range_search;
wire [16:0] data_relative_full;
// wire [16:0] data_relative_BCID;
reg  [4:0] state, next;

reg  match_valid_reg;
wire is_error_word;
wire is_warning_word;

assign trigger_BCID     = trigger_reg[16:5];
assign ram_empty        = (waddr == raddr) ? 1'b1 : 1'b0;
assign ram_full         = (raddr-1'b1 == waddr) ? 1'b1 : 1'b0;
assign ram_data_BCID    = ram_data_out[24:13]; //pair mode 
assign ram_data_leading = ram_data_out[24:8]; //pair mode 
assign matching_busy    = (|matching_busy_reg_delay)|matching_busy_reg; 
assign is_warning_word    = (ram_data_out[31:27]==`WARNING_CHANNEL) ? 1'b1:1'b0;
assign is_error_word    = (ram_data_out[31:27]==`ERROR_CHANNEL) ? 1'b1:1'b0;
//matching_busy is prolonged 3 clocks to compensate tdc fifo empty latency

reg [11:0] time_out_counter;
wire time_out;
assign  time_out = (&time_out_counter)&enable_matching_timeout;



always @(posedge clk_40  ) begin
    if (rst_40) begin
        // reset
        time_out_counter <= 'b0;
    end else if (state==IDLE) begin
        time_out_counter <= 'b0;
    end else if (enable_matching_timeout) begin
        time_out_counter <= time_out_counter + 1'b1;
    end
end

always @(posedge clk_40) begin
	if (rst_40) begin
		matching_busy_reg_delay <= 3'b0;          
	end else begin
		matching_busy_reg_delay <= {matching_busy_reg_delay[1:0],matching_busy_reg};
	end
end

rollover_sub #(.WIDTH(12)) rollover_sub_reject (
	.out(reject_counter), .in(trigger_coarse), .sub(reject_offset), .rollover(rollover));

rollover_sub #(.WIDTH(12)) rollover_sub_matchstart (
	.out(match_start), .in(trigger_BCID), .sub(bc_offset), .rollover(rollover));

rollover_add #(.WIDTH(12)) rollover_add_matchstop (
	.out(match_stop), .in(match_start), .add(match_window), .rollover(rollover));

rollover_add #(.WIDTH(12)) rollover_add_searchstop (
	.out(search_stop), .in(match_stop), .add(search_margin), .rollover(rollover));

rollover_sub #(.WIDTH(12)) rollover_sub_searchstart (
	.out(search_start), .in(match_start), .sub(search_margin), .rollover(rollover));

// xlx_ku_mgt_ip_reset_synchronizer rst_sync(
// 	.clk_in(sys_clk_160),
// 	.rst_in(rst_in),
// 	.rst_out(rst_160)
// );


// assign trigger_BCID = trigger_reg[16:5];

// sync_fifo_32b sync_fifo_32b_inst (
//   .wr_clk(clk_40),  // input wire wr_clk
//   .rd_clk(sys_clk_160),  // input wire rd_clk
//   .din(tdc_hit_data),        // input wire [31 : 0] din
//   .wr_en(tdc_hit_data_valid),    // input wire wr_en
//   .rd_en(~ram_full),    // input wire rd_en
//   .dout(tdc_hit_data_sync),      // output wire [31 : 0] dout
//   .full(),      // output wire full
//   .empty(sync_fifo_empty)    // output wire empty
// );


// 40M common clk fifo
sync_fifo_32b sync_fifo_32b_inst (
    .clk(clk_40),      // input wire clk
    .srst(rst_40),     // input wire srst
    .din(tdc_hit_data),      // input wire [31 : 0] din
    .wr_en(tdc_hit_data_valid),  // input wire wr_en
    .rd_en(~ram_full),  // input wire rd_en
    .dout(tdc_hit_data_sync),    // output wire [31 : 0] dout
    .full(),    // output wire full
    .empty(sync_fifo_empty)  // output wire empty
);


always @(posedge clk_40) begin
	if (rst_40) begin
		waddr <= 10'b0;          
	end else if ((~sync_fifo_empty)&(~ram_full)) begin
		waddr <= waddr + 10'b1;
	end
end


tdc_hit_ram tdc_hit_ram_inst (
  .clka(clk_40),            // input wire clka
  .wea((~sync_fifo_empty)&(~ram_full)),              // input wire [0 : 0] wea
  .addra(waddr),          // input wire [9 : 0] addra
  .dina(tdc_hit_data_sync),            // input wire [31 : 0] dina
  .clkb(clk_40),            // input wire clkb
  .rstb(rst_40),            // input wire rstb
  .addrb(raddr),          // input wire [9 : 0] addrb
  .doutb(ram_data_out),          // output wire [31 : 0] doutb
  .rsta_busy(),  // output wire rsta_busy
  .rstb_busy()  // output wire rstb_busy
);

in_range #(.WIDTH(12)) in_range_keep_inst (
	.flag(in_range_keep), .in(ram_data_BCID), .start(reject_counter), .stop(trigger_coarse));

in_range #(.WIDTH(12)) in_range_match_inst (
	.flag(in_range_match), .in(ram_data_BCID), .start(match_start), .stop(match_stop));

in_range #(.WIDTH(12)) in_range_search_inst (
	.flag(in_range_search), .in(ram_data_BCID), .start(search_start), .stop(search_stop));



rollover_sub #(.WIDTH(17)) rollover_sub_relative_data (
	.out(data_relative_full), .in(ram_data_leading), 
	.sub(trigger_reg), .rollover({rollover,5'b11111}));

// rollover_sub #(.WIDTH(17)) rollover_sub_relative_BCID (
// 	.out(data_relative_BCID), .in(ram_data_leading), 
// 	.sub({trigger_BCID,5'b00000}), .rollover({rollover,5'b11111}));


always @(posedge clk_40) begin
	if(rst_40)	state <= IDLE;
	else	state <= next;
end

always @(*) begin
	next = IDLE;
	if(enable_matching && !rst_40) begin
		case (state)
			IDLE: begin
				if ((~trigger_fifo_empty)&(~building_busy))
										next = TRIGGER_IN;
			end // IDLE
			TRIGGER_IN: begin
				if(ram_empty|time_out)	next = LAST;
				else begin
					if(in_range_match)	next = MATCHING_START;
					else				next = TRIGGER_IN;
				end
			end // TRIGGER_IN
			MATCHING_START:				next = MATCHING;
			MATCHING: begin
				if(ram_empty)			next = LAST;
				else begin
					if(in_range_search|is_error_word|is_warning_word) next = MATCHING;
					else				next = LAST;
				end
			end // MATCHING
			LAST:						next = IDLE;
			default:					next = IDLE;
		endcase // case(state)
	end // enable_matching && !rst_40
end


always @(posedge clk_40) begin
	if (rst_40) begin
		ram_empty_reg <= 1'b1;
		raddr_reg <= 10'b0;
	end else begin
		ram_empty_reg <= ram_empty;        //ram_empty_reg is aligned to ram_data_out, while ram_empty is aligned to address pointer
		raddr_reg <= raddr;
	end
end

assign ram_read_ready = (~((~ram_empty)&ram_empty_reg)) & (raddr==raddr_reg);
//ram read not ready at the clock when ~empty or at the clock when raddr changes
always @(posedge clk_40) begin    
	if(rst_40) begin
		trigger_reg       <= 17'b0;
		matching_busy_reg <=  1'b0;
		raddr             <= 10'b0;
		saddr             <= 10'b0;
		matched_data      <= 32'b0;
		match_valid       <=  1'b0;
		match_valid_reg   <=  1'b0;
	end //rst_40
	else if (enable_matching) begin
		case(state)
			IDLE: begin 				
				trigger_reg       <= trigger_fifo_data;
				matching_busy_reg <=  1'b0;
				if ((~ram_empty)&ram_read_ready&(~in_range_keep)) begin
					raddr         <= saddr +1'b1;   //requires 2 clocks per reject
					saddr         <= saddr +1'b1;   //deleting data older than reject_counter
				end				
			end // IDLE
			TRIGGER_IN:begin
				matching_busy_reg <=  1'b1;
				saddr             <= raddr;
				if((~ram_empty)&ram_read_ready&(~in_range_match))
					raddr         <= raddr +1'b1;   //requires 2 clocks per increment
			end // TRIGGER_IN
			MATCHING_START:begin
				raddr     <= raddr +1'b1;
			end // TRIGGER_IN
			MATCHING:begin 
				if (~ram_empty) raddr <= raddr +1'b1;  //address increases every clock
				if (in_range_match|is_error_word|is_warning_word) begin 					
					matched_data <=      //previous address ram content matched out
						{enable_relative_trigger_data&in_range_match}? 
						{ram_data_out[31:25],data_relative_full,ram_data_out[7:0]}:
						// (enable_relative_trigger_BCID?
						// {ram_data_out[31:25],data_relative_BCID,ram_data_out[7:0]}:
						ram_data_out;
					match_valid  <= 1'b1;					
				end else begin 
					matched_data <=  'b0;
					match_valid  <= 1'b0;
				end
			end // MATCHING
			LAST:begin			
				raddr        <= saddr;
				matched_data <=  'b0;
				match_valid  <= 1'b0;
			end //LAST
		endcase // state
	end // enable_matching
	else begin 
		match_valid         <= match_valid_reg;
		if(match_valid_reg)
			matched_data    <= ram_data_out;
		if ((~ram_empty) & ram_read) begin
			raddr           <= raddr + 10'b1;
			// matched_data <= ram_data_out;
			match_valid_reg <= 1'b1;
		end else begin
			match_valid_reg <= 1'b0;
		end
	end // ~enable_matching
end


//  ila_ram ila_ram_inst (
// 	.clk(clk_40), // input wire clk


// 	.probe0(tdc_hit_data_sync), // input wire [31:0]  probe0  
// 	.probe1(sync_fifo_empty), // input wire [0:0]  probe1 
// 	.probe2(matched_data), // input wire [31:0]  probe2 
// 	.probe3(match_valid), // input wire [0:0]  probe3 
// 	.probe4(ram_data_out), // input wire [31:0]  probe4 
// 	.probe5(waddr), // input wire [9:0]  probe5 
// 	.probe6(raddr), // input wire [9:0]  probe6 
// 	.probe7(saddr), // input wire [9:0]  probe7 
// 	.probe8(ram_empty), // input wire [0:0]  probe8 
// 	.probe9(ram_full), // input wire [0:0]  probe9 
// 	.probe10(ram_read), // input wire [0:0]  probe10 
// 	.probe11(state), // input wire [4:0]  probe11 
// 	.probe12(next), // input wire [4:0]  probe12 
// 	.probe13(in_range_keep), // input wire [0:0]  probe13 
// 	.probe14(in_range_match), // input wire [0:0]  probe14 
// 	.probe15(in_range_search), // input wire [0:0]  probe15
// 	.probe16(trigger_fifo_empty), // input wire [0:0]  probe16 
// 	.probe17(trigger_reg), // input wire [16:0]  probe17 
// 	.probe18(trigger_coarse) // input wire [11:0]  probe17 

// );

endmodule
