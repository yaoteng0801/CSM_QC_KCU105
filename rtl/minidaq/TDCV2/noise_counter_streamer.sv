/*
       _________   ________     ________
      / U OF M  \ | LSA    \   / Physics\
      \__ATLAS__/ |   ___   | |   ______/
         |   |    |  |   \  | |  |
         |   |    |  |___/  | |  \______
         |   |    |         | |         \
         \___/    |________/   \________/
*/

// Streams one-second noise counter snapshots into the normal 40-bit readout path.
//
// Packet format, repeated once per locked TDC:
//   HEADER  = {4'hD, csm_id[0], tdc_id[4:0], seconds_elapsed[29:0]}
//   COUNTER = {4'h9, channel_id[4:0], total_count[30:0]}
//   ERROR   = {4'hF, error_kind[4:0], total_count[30:0]}
//   TRAILER = {4'hE, csm_id[0], tdc_id[4:0], total_count_this_tdc[29:0]}
// Error kind 0 is KERR/DErr; kind 1 is an invalid decoded channel ID.
//
// The counter value is the live cumulative 31-bit channel counter from
// tdcv2_decoder. The counter and this streamer's seconds timer share the same
// reset pulse, generated from DAQ start or noise_counter_clear. The trailer
// total is the low 30 bits of this TDC's channel-count sum.

module noise_counter_streamer #(
    parameter integer TDC_COUNT            = 40,
    parameter integer TDC_PER_CSM          = 20,
    parameter integer CHANNELS_PER_TDC     = 24,
    parameter integer COUNTER_WIDTH        = 31,
    parameter integer SAMPLE_PERIOD_CYCLES = 40000000
)(
    input  wire                                               clk,
    input  wire                                               rst,
    input  wire                                               enable,
    input  wire                                               counter_reset,
    input  wire [TDC_COUNT-1:0]                               locked_tdc,
    input  wire [TDC_COUNT*CHANNELS_PER_TDC*COUNTER_WIDTH-1:0] noise_hit_counts,
    input  wire [TDC_COUNT*2*COUNTER_WIDTH-1:0]                noise_error_counts,
    input  wire                                               readout_fifo_full,
    output reg  [39:0]                                        counter_data,
    output reg                                                counter_data_ready
);

localparam integer COUNTER_COUNT = TDC_COUNT * CHANNELS_PER_TDC;
localparam integer ERROR_KIND_COUNT = 2;
localparam integer TDC_AW        = (TDC_COUNT <= 2) ? 1 : $clog2(TDC_COUNT);
localparam integer CHANNEL_AW    = (CHANNELS_PER_TDC <= 2) ? 1 : $clog2(CHANNELS_PER_TDC);
localparam integer ERROR_KIND_AW = 1;
localparam integer TIMER_AW      = (SAMPLE_PERIOD_CYCLES <= 2) ? 1 : $clog2(SAMPLE_PERIOD_CYCLES);

localparam [TIMER_AW-1:0] SAMPLE_PERIOD_LAST = SAMPLE_PERIOD_CYCLES - 1;

localparam [3:0] TAG_HEADER  = 4'hD;
localparam [3:0] TAG_COUNTER = 4'h9;
localparam [3:0] TAG_ERROR   = 4'hF;
localparam [3:0] TAG_TRAILER = 4'hE;

localparam [2:0] S_WAIT     = 3'd0;
localparam [2:0] S_FIND_TDC = 3'd1;
localparam [2:0] S_HEADER   = 3'd2;
localparam [2:0] S_COUNTER  = 3'd3;
localparam [2:0] S_ERROR    = 3'd4;
localparam [2:0] S_TRAILER  = 3'd5;

reg [2:0] state;
reg [TIMER_AW-1:0] sample_timer;
reg [TDC_AW-1:0] tdc_idx;
reg [CHANNEL_AW-1:0] channel_idx;
reg [ERROR_KIND_AW-1:0] error_kind_idx;
reg [29:0] seconds_elapsed;
reg [29:0] packet_seconds;
reg [29:0] tdc_total_count;
reg enable_d;

reg [TDC_COUNT-1:0] locked_snapshot;
reg [TDC_COUNT*CHANNELS_PER_TDC*COUNTER_WIDTH-1:0] cur_snapshot;
reg [TDC_COUNT*ERROR_KIND_COUNT*COUNTER_WIDTH-1:0] cur_error_snapshot;

wire enable_rise = enable & ~enable_d;
wire sample_due  = (sample_timer == SAMPLE_PERIOD_LAST);

wire [TDC_AW+CHANNEL_AW-1:0] counter_linear_idx =
    (tdc_idx * CHANNELS_PER_TDC) + channel_idx;

wire [COUNTER_WIDTH-1:0] cur_counter_word =
    cur_snapshot[counter_linear_idx*COUNTER_WIDTH +: COUNTER_WIDTH];

wire [TDC_AW+ERROR_KIND_AW-1:0] error_linear_idx =
    (tdc_idx * ERROR_KIND_COUNT) + error_kind_idx;

wire [COUNTER_WIDTH-1:0] cur_error_word =
    cur_error_snapshot[error_linear_idx*COUNTER_WIDTH +: COUNTER_WIDTH];

wire [5:0] csm_linear = tdc_idx / TDC_PER_CSM;
wire       csm_id = csm_linear[0];
wire [4:0] tdc_id = tdc_idx % TDC_PER_CSM;
wire [4:0] channel_id = channel_idx;

wire output_accepted = counter_data_ready & ~readout_fifo_full;
wire last_tdc = (tdc_idx == TDC_COUNT - 1);
wire last_channel = (channel_idx == CHANNELS_PER_TDC - 1);
wire last_error_kind = (error_kind_idx == ERROR_KIND_COUNT - 1);

always @(*) begin
    counter_data_ready = 1'b0;
    counter_data       = 40'd0;

    if (enable && !readout_fifo_full) begin
        case (state)
            S_HEADER: begin
                counter_data_ready = 1'b1;
                counter_data       = {TAG_HEADER, csm_id, tdc_id, packet_seconds};
            end

            S_COUNTER: begin
                counter_data_ready = 1'b1;
                counter_data       = {TAG_COUNTER, channel_id, cur_counter_word[30:0]};
            end

            S_ERROR: begin
                counter_data_ready = 1'b1;
                counter_data       = {TAG_ERROR, 4'b0, error_kind_idx, cur_error_word[30:0]};
            end

            S_TRAILER: begin
                counter_data_ready = 1'b1;
                counter_data       = {TAG_TRAILER, csm_id, tdc_id, tdc_total_count};
            end

            default: begin
                counter_data_ready = 1'b0;
                counter_data       = 40'd0;
            end
        endcase
    end
end

always @(posedge clk) begin
    if (rst) begin
        state           <= S_WAIT;
        sample_timer    <= {TIMER_AW{1'b0}};
        tdc_idx         <= {TDC_AW{1'b0}};
        channel_idx     <= {CHANNEL_AW{1'b0}};
        error_kind_idx  <= {ERROR_KIND_AW{1'b0}};
        seconds_elapsed <= 30'd0;
        packet_seconds  <= 30'd0;
        tdc_total_count <= 30'd0;
        enable_d        <= 1'b0;
        locked_snapshot <= {TDC_COUNT{1'b0}};
        cur_snapshot    <= {COUNTER_COUNT*COUNTER_WIDTH{1'b0}};
        cur_error_snapshot <= {TDC_COUNT*ERROR_KIND_COUNT*COUNTER_WIDTH{1'b0}};
    end else begin
        enable_d <= enable;

        if (!enable) begin
            state           <= S_WAIT;
            sample_timer    <= {TIMER_AW{1'b0}};
            tdc_idx         <= {TDC_AW{1'b0}};
            channel_idx     <= {CHANNEL_AW{1'b0}};
            error_kind_idx  <= {ERROR_KIND_AW{1'b0}};
            seconds_elapsed <= 30'd0;
            packet_seconds  <= 30'd0;
            tdc_total_count <= 30'd0;
            locked_snapshot <= {TDC_COUNT{1'b0}};
        end else if (counter_reset || enable_rise) begin
            state           <= S_WAIT;
            sample_timer    <= {TIMER_AW{1'b0}};
            tdc_idx         <= {TDC_AW{1'b0}};
            channel_idx     <= {CHANNEL_AW{1'b0}};
            error_kind_idx  <= {ERROR_KIND_AW{1'b0}};
            seconds_elapsed <= 30'd0;
            packet_seconds  <= 30'd0;
            tdc_total_count <= 30'd0;
            locked_snapshot <= {TDC_COUNT{1'b0}};
            cur_snapshot    <= noise_hit_counts;
            cur_error_snapshot <= noise_error_counts;
        end else begin
            if (sample_due) begin
                sample_timer    <= {TIMER_AW{1'b0}};
                seconds_elapsed <= seconds_elapsed + 30'd1;
            end else begin
                sample_timer    <= sample_timer + 1'b1;
            end

            case (state)
                S_WAIT: begin
                    if (sample_due) begin
                        cur_snapshot    <= noise_hit_counts;
                        cur_error_snapshot <= noise_error_counts;
                        locked_snapshot <= locked_tdc;
                        tdc_idx         <= {TDC_AW{1'b0}};
                        channel_idx     <= {CHANNEL_AW{1'b0}};
                        error_kind_idx  <= {ERROR_KIND_AW{1'b0}};
                        packet_seconds  <= seconds_elapsed + 30'd1;
                        tdc_total_count <= 30'd0;
                        state           <= S_FIND_TDC;
                    end
                end

                S_FIND_TDC: begin
                    channel_idx     <= {CHANNEL_AW{1'b0}};
                    error_kind_idx  <= {ERROR_KIND_AW{1'b0}};
                    tdc_total_count <= 30'd0;
                    if (locked_snapshot[tdc_idx]) begin
                        state <= S_HEADER;
                    end else if (last_tdc) begin
                        state         <= S_WAIT;
                    end else begin
                        tdc_idx <= tdc_idx + 1'b1;
                    end
                end

                S_HEADER: begin
                    if (output_accepted) begin
                        channel_idx     <= {CHANNEL_AW{1'b0}};
                        error_kind_idx  <= {ERROR_KIND_AW{1'b0}};
                        tdc_total_count <= 30'd0;
                        state           <= S_COUNTER;
                    end
                end

                S_COUNTER: begin
                    if (output_accepted) begin
                        tdc_total_count <= tdc_total_count + cur_counter_word[29:0];
                        if (last_channel) begin
                            channel_idx <= {CHANNEL_AW{1'b0}};
                            error_kind_idx <= {ERROR_KIND_AW{1'b0}};
                            state       <= S_ERROR;
                        end else begin
                            channel_idx <= channel_idx + 1'b1;
                        end
                    end
                end

                S_ERROR: begin
                    if (output_accepted) begin
                        if (last_error_kind) begin
                            state <= S_TRAILER;
                        end else begin
                            error_kind_idx <= error_kind_idx + 1'b1;
                        end
                    end
                end

                S_TRAILER: begin
                    if (output_accepted) begin
                        if (last_tdc) begin
                            state         <= S_WAIT;
                        end else begin
                            tdc_idx <= tdc_idx + 1'b1;
                            state   <= S_FIND_TDC;
                        end
                    end
                end

                default: begin
                    state <= S_WAIT;
                end
            endcase
        end
    end
end

endmodule
