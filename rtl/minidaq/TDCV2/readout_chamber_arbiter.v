// Merge two independent FWFT chamber readout FIFOs onto one Ethernet packetizer.
// A header locks the grant through its matching trailer, including across frame
// boundaries.  After a trailer, the current fixed-size Ethernet payload is
// padded before another chamber may be selected.

module readout_chamber_arbiter (
    input  wire        clk,
    input  wire        rst,
    input  wire [1:0]  source_enable,
    input  wire        event_framed,

    input  wire [39:0] fifo0_data,
    input  wire        fifo0_empty,
    output wire        fifo0_read,
    input  wire [39:0] fifo1_data,
    input  wire        fifo1_empty,
    output wire        fifo1_read,

    output wire [39:0] output_data,
    output wire        output_ready,
    input  wire        output_read,
    input  wire        packet_done
);

localparam [3:0] WORD_TAG_HEADER  = 4'hA;
localparam [3:0] WORD_TAG_TRAILER = 4'hC;

reg grant_valid;
reg grant_sel;
reg stream_in_event;
reg block_after_trailer;
reg rr_prefer;

reg select_valid;
reg select_group;
wire fifo0_available = source_enable[0] && !fifo0_empty;
wire fifo1_available = source_enable[1] && !fifo1_empty;

always @(*) begin
    select_valid = 1'b0;
    select_group = 1'b0;
    if (grant_valid) begin
        select_valid = source_enable[grant_sel];
        select_group = grant_sel;
    end else if (fifo0_available && fifo1_available) begin
        select_valid = 1'b1;
        select_group = rr_prefer;
    end else if (fifo0_available) begin
        select_valid = 1'b1;
        select_group = 1'b0;
    end else if (fifo1_available) begin
        select_valid = 1'b1;
        select_group = 1'b1;
    end
end

wire selected_empty = select_group ? fifo1_empty : fifo0_empty;
wire selected_accept = output_read && output_ready;
wire accepted_header = event_framed && selected_accept &&
                       (output_data[39:36] == WORD_TAG_HEADER);
wire accepted_trailer = event_framed && selected_accept &&
                        (output_data[39:36] == WORD_TAG_TRAILER);

assign output_data = select_group ? fifo1_data : fifo0_data;
assign output_ready = select_valid && !selected_empty && !block_after_trailer;
assign fifo0_read = selected_accept && !select_group;
assign fifo1_read = selected_accept &&  select_group;

always @(posedge clk) begin
    if (rst) begin
        grant_valid         <= 1'b0;
        grant_sel           <= 1'b0;
        stream_in_event     <= 1'b0;
        block_after_trailer <= 1'b0;
        rr_prefer           <= 1'b0;
    end else begin
        if (grant_valid && !source_enable[grant_sel]) begin
            grant_valid         <= 1'b0;
            stream_in_event     <= 1'b0;
            block_after_trailer <= 1'b0;
        end

        if (!grant_valid && selected_accept) begin
            grant_valid <= 1'b1;
            grant_sel   <= select_group;
        end
        if (accepted_header)
            stream_in_event <= 1'b1;
        if (accepted_trailer) begin
            stream_in_event     <= 1'b0;
            block_after_trailer <= 1'b1;
        end

        if (packet_done) begin
            block_after_trailer <= 1'b0;
            if (!event_framed || block_after_trailer || !stream_in_event ||
                accepted_trailer) begin
                grant_valid     <= 1'b0;
                stream_in_event <= 1'b0;
                rr_prefer       <= ~select_group;
            end
        end
    end
end

endmodule
