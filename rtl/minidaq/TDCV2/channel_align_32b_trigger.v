`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: Xiong Xiao
// 
// Create Date: 8/23/2021
// Design Name: 
// Module Name: channel_align_32b_trigger
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////

`define HEADER_FILL 8'b1111_1000 
`define TRAILER_FILL 8'b1111_0000 

module channel_align_32b_trigger (
	input clk,
    input rst,
    input enable,
	input [63:0] data_64b_decode, 
	input [7:0] o_Kout,
	input data_ready,
	output chnl_data_valid,
	output [31:0] chnl_data_32b
	);

//  Note: sample K_code and data for 3 times. 
//  Use the middile one to process data
//  Use the earliest to judge header
//  Use the last one to extend data and recognize trailer

reg [7:0] K_r_pre;
reg [7:0] K_r;
reg [7:0] K_r_after;

reg [63:0] data_r_pre;
reg [63:0] data_r;
reg [63:0] data_r_after;

reg [2:0] data_ready_r;
reg data_ready_delay;

always @(posedge clk) begin
    if (rst) begin 
        data_ready_delay <= 1'b0;
    end else begin 
        data_ready_delay <= data_ready;
    end
end

// sampling input for 3 times
always @(posedge clk) begin
    if (rst) begin 
        K_r_pre      <= 'hff; // Start with control code instead of data.
        K_r          <= 'hff;
        K_r_after    <= 'hff;
        data_r_pre   <= 64'b0;
        data_r       <= 64'b0;
        data_r_after <= 64'b0;
        data_ready_r <= 3'b0;
    end else begin 
        if (data_ready&enable) begin
            {K_r_pre,K_r,K_r_after}          <= {K_r,K_r_after,o_Kout};
            {data_r_pre,data_r,data_r_after} <= {data_r,data_r_after,data_64b_decode};
            //{K_r_after,K_r,K_r_pre}          <= {K_r,K_r_pre,o_Kout};
            //{data_r_after,data_r,data_r_pre} <= {data_r,data_r_pre,data_64b_decode};
            data_ready_r                     <= {data_ready_r[1:0],data_ready};
        end
    end
end



reg [31:0] data;
reg data_valid;
reg [2:0] data_pos;
reg proc_data; // indicate that header was found and it is processing data
reg proc_second_packet; // indicate there is a following packet
reg reading_data; // flag to indicate next packet is either data or trailer
reg is_second_packet; // flag to indicate is processing the second packet

wire find_header_front;
wire [23:0] header_data_front;
wire [2:0] data_pos_from_front;
wire proc_data_from_front;

wire find_header_behind;
wire [23:0] header_data_behind;
wire [2:0] data_pos_from_behind;
wire proc_data_from_behind;

wire find_data;
wire [31:0] data_packet;
wire [2:0] data_pos_next;
wire proc_data_from_data;
wire is_trailer;

// There is a chance two headers are inside one 64 bit data frame.
wire read_the_second_packet;
assign read_the_second_packet = find_header_behind & ( (find_header_front & (data_pos_from_front != data_pos_from_behind) ) | !find_header_front );


always @(posedge clk) begin
    if (rst) begin 
        data               <= 32'b0;
        data_valid         <= 1'b0;
        data_pos           <= 3'b0;
        proc_data          <= 1'b0;
        proc_second_packet <= 1'b0;
        reading_data       <= 1'b0;
        is_second_packet   <= 1'b0;
    end else if(enable) begin 
        data               <= 32'b0;
        data_valid         <= 1'b0;
        proc_data          <= 1'b0;
        proc_second_packet <= 1'b0;
        // 1.&data_ready_r confirms that it has 3 valide data
        // 2.data_ready_delay is used as a tick signal to trigger the checking
        // process.
        // 3.proc_data means is processing data packet
        // 4.proc_second_packet indicates there is a second packet needed to
        // be processed
        if ( &data_ready_r & ( data_ready_delay | proc_data | proc_second_packet )) begin
            if (!(&K_r)) begin // Has some data 
                if (!reading_data) begin // looking for header
                    if (!proc_second_packet & find_header_front) begin // looking for the header from front
                        data             <= {`HEADER_FILL,header_data_front};
                        data_valid       <= 1'b1;
                        data_pos         <= data_pos_from_front;
                        proc_data        <= proc_data_from_front;
                        reading_data     <= 1'b1;
                        is_second_packet <= 1'b0;
                    end else begin // looking for header from behind
                        if (find_header_behind) begin
                            data             <= {`HEADER_FILL,header_data_behind};
                            data_valid       <= 1'b1;
                            data_pos         <= data_pos_from_behind;
                            proc_data        <= proc_data_from_behind;
                            reading_data     <= 1'b1;
                            is_second_packet <= 1'b1;
                        end
                    end
                end else begin // looking for data
                    if (find_data) begin
                        data       <= data_packet;
                        data_valid <= 1'b1;
                        data_pos   <= data_pos_next;
                        proc_data  <= proc_data_from_data;
                        if (is_trailer) begin
                            reading_data <= 1'b0;
                        end

                        // need to judege if there is a second packet
                        if (data_ready_delay & is_trailer & read_the_second_packet ) begin
                            proc_second_packet <= 1'b1;
                            is_second_packet <= 1'b1;
                        end else if (is_trailer & read_the_second_packet & !is_second_packet) begin 
                            proc_second_packet <= 1'b1;
                            is_second_packet <= 1'b1;
                        end else if (data_ready_delay) begin // refresh the is_second_packet flag
                            is_second_packet <= 1'b0;
                        end
                    end 
                end
            end
        end 
    end
end


assign chnl_data_valid = data_valid;
assign chnl_data_32b   = data;


Looking_for_header_front Looking_for_header_front_inst (
    .K_r_pre              (K_r_pre),
    .K_r                  (K_r),
    .K_r_after            (K_r_after),
    .data_r               (data_r),
    .data_r_after         (data_r_after),
    .find_header_front    (find_header_front),
    .header_data_front    (header_data_front),
    .data_pos_from_front  (data_pos_from_front),
    .proc_data_from_front (proc_data_from_front)
);

Looking_for_header_behind Looking_for_header_behind_inst (
    .K_r                   (K_r),
    .K_r_after             (K_r_after),
    .data_r                (data_r),
    .data_r_after          (data_r_after),
    .find_header_behind    (find_header_behind),
    .header_data_behind    (header_data_behind),
    .data_pos_from_behind  (data_pos_from_behind),
    .proc_data_from_behind (proc_data_from_behind)
);

Looking_for_data Looking_for_data_inst (
    .K_r                 (K_r),
    .K_r_after           (K_r_after),
    .data_r              (data_r),
    .data_r_after        (data_r_after),
    .data_pos            (data_pos),
    .find_data           (find_data),
    .data_packet         (data_packet),
    .data_pos_next       (data_pos_next),
    .is_trailer          (is_trailer),
    .proc_data_from_data (proc_data_from_data)
);


// ila_channel_align_trigger ila_channel_align_trigger_inst (
//     .clk(clk), // input wire clk


//     .probe0(enable), // input wire [0:0]  probe0  
//     .probe1(data_64b_decode), // input wire [63:0]  probe1 
//     .probe2(o_Kout), // input wire [7:0]  probe2 
//     .probe3(data_ready), // input wire [0:0]  probe3 
//     .probe4(chnl_data_valid), // input wire [0:0]  probe4 
//     .probe5(chnl_data_32b), // input wire [31:0]  probe5 
//     .probe6(K_r_pre), // input wire [7:0]  probe6 
//     .probe7(K_r), // input wire [7:0]  probe7 
//     .probe8(K_r_after), // input wire [7:0]  probe8 
//     .probe9(data_r_pre), // input wire [63:0]  probe9 
//     .probe10(data_r), // input wire [63:0]  probe10 
//     .probe11(data_r_after), // input wire [63:0]  probe11 
//     .probe12(data_ready_r), // input wire [2:0]  probe12 
//     .probe13(data_ready_delay), // input wire [0:0]  probe13 
//     .probe14(data), // input wire [31:0]  probe14 
//     .probe15(data_valid), // input wire [0:0]  probe15 
//     .probe16(data_pos), // input wire [2:0]  probe16 
//     .probe17(find_header_front), // input wire [0:0]  probe17 
//     .probe18(header_data_front), // input wire [23:0]  probe18 
//     .probe19(data_pos_from_front), // input wire [2:0]  probe19 
//     .probe20(proc_data_from_front), // input wire [0:0]  probe20 
//     .probe21(find_header_behind), // input wire [0:0]  probe21 
//     .probe22(header_data_behind), // input wire [23:0]  probe22 
//     .probe23(data_pos_from_behind), // input wire [2:0]  probe23 
//     .probe24(proc_data_from_behind), // input wire [0:0]  probe24 
//     .probe25(find_data), // input wire [0:0]  probe25 
//     .probe26(data_packet), // input wire [31:0]  probe26 
//     .probe27(data_pos_next), // input wire [2:0]  probe27 
//     .probe28(proc_data_from_data), // input wire [0:0]  probe28 
//     .probe29(is_trailer) // input wire [0:0]  probe29
// );


endmodule

// This module will be used to look for header from behind. 
// Give the priority from front 
module Looking_for_header_front (
    input [7:0] K_r_pre,
    input [7:0] K_r,
    input [7:0] K_r_after,
    input [63:0] data_r,
    input [63:0] data_r_after,
    output reg find_header_front,
    output reg [23:0] header_data_front,
    output reg [2:0] data_pos_from_front,
    output reg proc_data_from_front
);


wire [13:0] K_judge;
assign K_judge = {K_r_pre[0],K_r,K_r_after[7:3]};


// Note: for a valid packet, The K code has at least 6 zeros.


always @(*) begin 
    casex (K_judge)
        14'b1_0000_00??_????_? : begin
        //14'b1_0000_0011_1111_1 : begin
            find_header_front    = 1'b1;
            header_data_front    = data_r[8*8-1:5*8];
            data_pos_from_front  = 3'd3;
            proc_data_from_front = 1'b1;
        end
        14'b1_1000_000?_????_? : begin
            find_header_front    = 1'b1;
            header_data_front    = data_r[7*8-1:4*8];
            data_pos_from_front  = 3'd4;
            proc_data_from_front = 1'b1;
        end
        14'b1_1100_0000_????_? : begin
            find_header_front    = 1'b1;
            header_data_front    = data_r[6*8-1:3*8];
            data_pos_from_front  = 3'd5;
            proc_data_from_front = 1'b1;
        end
        14'b1_1110_0000_0???_? : begin
            find_header_front    = 1'b1;
            header_data_front    = data_r[5*8-1:2*8];
            data_pos_from_front  = 3'd6;
            proc_data_from_front = 1'b1;
        end
        14'b1_1111_0000_00??_? : begin
            find_header_front    = 1'b1;
            header_data_front    = data_r[4*8-1:1*8];
            data_pos_from_front  = 3'd7;
            proc_data_from_front = 1'b1;
        end
        14'b1_1111_1000_000?_? : begin
            find_header_front    = 1'b1;
            header_data_front    = data_r[3*8-1:0*8];
            data_pos_from_front  = 3'd0;
            proc_data_from_front = 1'b0;
        end
        14'b1_1111_1100_0000_? : begin
            find_header_front    = 1'b1;
            header_data_front    = {data_r[2*8-1:0*8],data_r_after[8*8-1:7*8]};
            data_pos_from_front  = 3'd1;
            proc_data_from_front = 1'b0;
        end
        14'b1_1111_1110_0000_0 : begin
            find_header_front    = 1'b1;
            header_data_front    = {data_r[1*8-1:0*8],data_r_after[8*8-1:6*8]};
            data_pos_from_front  = 3'd2;
            proc_data_from_front = 1'b0;
        end
        default : begin
            find_header_front    = 1'b0;
            header_data_front    = 24'b0;
            data_pos_from_front  = 3'd0;
            proc_data_from_front = 1'b0;
        end
    endcase

end

//always @(*) begin 
    //find_header_front    = 1'b0;
    //header_data_front    = 64'b0;
    //data_pos_from_front  = 3'd0;
    //proc_data_from_front = 1'b0;
    ////if (K_judge == 14'b1_0000_00??_????_?) begin
    ////if (K_judge == 14'b1_0000_0011_1111_1) begin
    //if (K_judge == 14'b1_0000_00??_????_?) begin
        //find_header_front    = 1'b1;
        //header_data_front    = data_r[8*8-1:5*8];
        //data_pos_from_front  = 3'd3;
        //proc_data_from_front = 1'b1;
    //end else if (K_judge == 14'b1_1000_000?_????_?) begin
        //find_header_front    = 1'b1;
        //header_data_front    = data_r[7*8-1:4*8];
        //data_pos_from_front  = 3'd4;
        //proc_data_from_front = 1'b1;
    //end else if (K_judge == 14'b1_1100_0000_????_?) begin
        //find_header_front    = 1'b1;
        //header_data_front    = data_r[6*8-1:3*8];
        //data_pos_from_front  = 3'd5;
        //proc_data_from_front = 1'b1;
    //end else if (K_judge == 14'b1_1110_0000_0???_?) begin
        //find_header_front    = 1'b1;
        //header_data_front    = data_r[5*8-1:2*8];
        //data_pos_from_front  = 3'd6;
        //proc_data_from_front = 1'b1;
    //end else if (K_judge == 14'b1_1111_0000_00??_?) begin
        //find_header_front    = 1'b1;
        //header_data_front    = data_r[4*8-1:1*8];
        //data_pos_from_front  = 3'd7;
        //proc_data_from_front = 1'b1;
    //end else if (K_judge == 14'b1_1111_1000_000?_?) begin
        //find_header_front    = 1'b1;
        //header_data_front    = data_r[3*8-1:0*8];
        //data_pos_from_front  = 3'd0;
        //proc_data_from_front = 1'b0;
    //end else if (K_judge == 14'b1_1111_1100_0000_?) begin
        //find_header_front    = 1'b1;
        //header_data_front    = {data_r[2*8-1:0*8],data_r_after[8*8-1:7*8]};
        //data_pos_from_front  = 3'd1;
        //proc_data_from_front = 1'b0;
    //end else if (K_judge == 14'b1_1111_1110_0000_0) begin
        //find_header_front    = 1'b1;
        //header_data_front    = {data_r[1*8-1:0*8],data_r_after[8*8-1:6*8]};
        //data_pos_from_front  = 3'd2;
        //proc_data_from_front = 1'b0;
    //end
//end


endmodule

// This module will be used to look for header from behind. 
// Give the priority from behind
// It is possible those two modules find the same position.
module Looking_for_header_behind (
    input [7:0] K_r,
    input [7:0] K_r_after,
    input [63:0] data_r,
    input [63:0] data_r_after,
    output reg find_header_behind,
    output reg [23:0] header_data_behind,
    output reg [2:0] data_pos_from_behind,
    output reg proc_data_from_behind
);

wire [12:0] K_judge;
assign K_judge = {K_r,K_r_after[7:3]};

always @(*) begin 
    find_header_behind    = 1'b0;
    header_data_behind    = 64'b0;
    data_pos_from_behind  = 3'd0;
    proc_data_from_behind = 1'b0;
    if (K_judge[6:0] == 7'b1000000) begin
        find_header_behind    = 1'b1;
        header_data_behind    = {data_r[1*8-1:0*8],data_r_after[8*8-1:6*8]};
        data_pos_from_behind  = 3'd2;
        proc_data_from_behind = 1'b0;
    end else if (K_judge[7:1] == 7'b1000000) begin
        find_header_behind    = 1'b1;
        header_data_behind    = {data_r[2*8-1:0*8],data_r_after[8*8-1:7*8]};
        data_pos_from_behind  = 3'd1;
        proc_data_from_behind = 1'b0;
    end else if (K_judge[8:2] == 7'b1000000) begin
        find_header_behind    = 1'b1;
        header_data_behind    = data_r[3*8-1:0*8];
        data_pos_from_behind  = 3'd0;
        proc_data_from_behind = 1'b0;
    end else if (K_judge[9:3] == 7'b1000000) begin
        find_header_behind    = 1'b1;
        header_data_behind    = data_r[4*8-1:1*8];
        data_pos_from_behind  = 3'd7;
        proc_data_from_behind = 1'b1;
    end else if (K_judge[10:4] == 7'b1000000) begin
        find_header_behind    = 1'b1;
        header_data_behind    = data_r[5*8-1:2*8];
        data_pos_from_behind  = 3'd6;
        proc_data_from_behind = 1'b1;
    end else if (K_judge[11:5] == 7'b1000000) begin
        find_header_behind    = 1'b1;
        header_data_behind    = data_r[6*8-1:3*8];
        data_pos_from_behind  = 3'd5;
        proc_data_from_behind = 1'b1;
    end else if (K_judge[12:6] == 7'b1000000) begin
        find_header_behind    = 1'b1;
        header_data_behind    = data_r[7*8-1:4*8];
        data_pos_from_behind  = 3'd4;
        proc_data_from_behind = 1'b1;
    end
end
endmodule


module Looking_for_data (
    input [7:0] K_r,
    input [7:0] K_r_after,
    input [63:0] data_r,
    input [63:0] data_r_after,
    input [2:0] data_pos,
    output reg find_data,
    output reg [31:0] data_packet,
    output [2:0] data_pos_next,
    output reg is_trailer,
    output reg proc_data_from_data
);


assign data_pos_next = data_pos + 3'd4;

always @(*) begin 
    find_data           = 1'b0;
    data_packet         = 32'b0;
    proc_data_from_data = 1'b0;
    is_trailer          = 1'b0;
    case (data_pos)
        3'h0: begin
            if (K_r[7:4] == 4'b0000) begin 
                find_data           = 1'b1;
                data_packet         = data_r[8*8-1:4*8];
                proc_data_from_data = 1'b1;
            end else if (K_r[7:4] == 4'b0001) begin
                find_data           = 1'b1;
                data_packet         = {`TRAILER_FILL,data_r[8*8-1:5*8]};
                proc_data_from_data = 1'b0;
                is_trailer          = 1'b1;
            end
        end
        3'h1: begin
            if (K_r[6:3] == 4'b0000) begin 
                find_data           = 1'b1;
                data_packet         = data_r[7*8-1:3*8];
                proc_data_from_data = 1'b1;
            end else if (K_r[6:3] == 4'b0001) begin
                find_data           = 1'b1;
                data_packet         = {`TRAILER_FILL,data_r[7*8-1:4*8]};
                proc_data_from_data = 1'b0;
                is_trailer          = 1'b1;
            end
        end
        3'h2: begin
            if (K_r[5:2] == 4'b0000) begin 
                find_data           = 1'b1;
                data_packet         = data_r[6*8-1:2*8];
                proc_data_from_data = 1'b1;
            end else if (K_r[5:2] == 4'b0001) begin
                find_data           = 1'b1;
                data_packet         = {`TRAILER_FILL,data_r[6*8-1:3*8]};
                proc_data_from_data = 1'b0;
                is_trailer          = 1'b1;
            end
        end
        3'h3: begin
            if (K_r[4:1] == 4'b0000) begin 
                find_data           = 1'b1;
                data_packet         = data_r[5*8-1:1*8];
                proc_data_from_data = 1'b1;
            end else if (K_r[4:1] == 4'b0001) begin
                find_data           = 1'b1;
                data_packet         = {`TRAILER_FILL,data_r[5*8-1:2*8]};
                proc_data_from_data = 1'b0;
                is_trailer          = 1'b1;
            end
        end
        3'h4: begin
            if (K_r[3:0] == 4'b0000) begin 
                find_data           = 1'b1;
                data_packet         = data_r[4*8-1:0*8];
                proc_data_from_data = 1'b0;
            end else if (K_r[3:0] == 4'b0001) begin
                find_data           = 1'b1;
                data_packet         = {`TRAILER_FILL,data_r[4*8-1:1*8]};
                proc_data_from_data = 1'b0;
                is_trailer          = 1'b1;
            end
        end
        3'h5: begin
            if ({K_r[2:0],K_r_after[7:7]} == 4'b0000) begin 
                find_data           = 1'b1;
                data_packet         = {data_r[3*8-1:0*8],data_r_after[8*8-1:7*8]};
                proc_data_from_data = 1'b0;
            end else if ({K_r[2:0],K_r_after[7:7]} == 4'b0001) begin
                find_data           = 1'b1;
                data_packet         = {`TRAILER_FILL,data_r[3*8-1:0*8]};
                proc_data_from_data = 1'b0;
                is_trailer          = 1'b1;
            end
        end
        3'h6: begin
            if ({K_r[1:0],K_r_after[7:6]} == 4'b0000) begin 
                find_data           = 1'b1;
                data_packet         = {data_r[2*8-1:0*8],data_r_after[8*8-1:6*8]};
                proc_data_from_data = 1'b0;
            end else if ({K_r[1:0],K_r_after[7:6]} == 4'b0001) begin
                find_data           = 1'b1;
                data_packet         = {`TRAILER_FILL,data_r[2*8-1:0*8],data_r_after[8*8-1:7*8]};
                proc_data_from_data = 1'b0;
                is_trailer          = 1'b1;
            end
        end
        3'h7: begin
            if ({K_r[0:0],K_r_after[7:5]} == 4'b0000) begin 
                find_data           = 1'b1;
                data_packet         = {data_r[1*8-1:0*8],data_r_after[8*8-1:5*8]};
                proc_data_from_data = 1'b0;
            end else if ({K_r[0:0],K_r_after[7:5]} == 4'b0001) begin
                find_data           = 1'b1;
                data_packet         = {`TRAILER_FILL,data_r[1*8-1:0*8],data_r_after[8*8-1:6*8]};
                proc_data_from_data = 1'b0;
                is_trailer          = 1'b1;
            end
        end
        default: begin
            find_data           = 1'b0;
            data_packet         = 32'b0;
            proc_data_from_data = 1'b0;
            is_trailer          = 1'b0;
        end
    endcase 
end





endmodule
