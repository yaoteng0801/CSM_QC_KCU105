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
// File   : event_builder_byhit.v
// Create : 2026-01-13 14:49:53
// Revise : 2026-04-06 16:51:01
// Editor : sublime text4, tab size (4)
// Description:
//
// -----------------------------------------------------------------------------
// Triggerless ping-pong event builder with per-chamber ANDed tube-filter commit
//
// - Start an event when either bank becomes non-empty.
// - Each bank has its own fixed timer (window_cycles) that starts when that bank
//   transitions from empty -> non-empty.
// - wr_bank_sel selects the ACTIVE write bank; when the CURRENT write bank's timer
//   ends, wr_bank_sel toggles to the other bank (so new hits go to the alternate bank).
// - rd_bank_sel is fixed to the older bank for the current event. We drain ONLY this
//   bank until it becomes empty (event data are defined by arrival window, not TDC time).
// - No-mixing rule: if BOTH bank timers have ended but the older bank is not fully drained,
//   then drop_hits is asserted. Upstream must gate writes (discard new hits) so time windows
//   never mix across events.
//
// Filter commit (distinct mapped tubes, not raw hit words):
// - Buffer hit words into PREBUF and do NOT output until all enabled cuts pass.
// - On acceptance, commit the event and begin output immediately:
//       SEND_HEAD -> FLUSH_BUF -> STREAM_LIVE -> SEND_TRAIL
// - If the older-bank window ends and the older bank drains before commit: discard the
//   entire event (no output).
//
// - A trigger never bypasses the tube filters. Unaccepted candidates that reach
//   the buffer/raw burst limit are drained and discarded without an event header.
//
// Trigger FIFO behavior:
// - Event-first policy:
//   - If hit data are pending (either bank non-empty), start/continue the event first.
//   - Only when NO hits are pending (both banks empty) will the module send triggers alone.
// - If trigger FIFO is non-empty while IDLE and no hits pending:
//       send trigger words alone as event_data (one 40-bit word per trigger).
// - Triggers in accepted events are emitted as normal payload, interleaved with
//   hit words. Triggers belonging to a discarded candidate are cleared.
// - No strict ordering between trigger words and hit words: use a simple alternation scheme
//   (toggle preference when both are available).
//
// Assumptions / integration notes:
// - fifoA_empty / fifoB_empty are REAL per-bank empty indicators (not muxed).
// - tdc_fifo_empty / tdc_fifo_data correspond to the rd_bank_sel-selected bank upstream.
// - drop_hits must be used upstream to gate writes to the ping-pong FIFO wrapper:
//       wr_en_eff = wr_en & ~drop_hits
// - Event closes (SEND_TRAIL) only after:
//       older-bank window ended AND older bank drained AND trigger FIFO is empty,
//   so triggers arriving during assembly are included in the event before the trailer.
//
// NEW output format (2026-01-20):
// - Event ID: {chamber_id[0], chamber_sequence[18:0]} at [35:16] in BOTH
//   header and trailer.  Each chamber sequence advances independently.
// - Event-control top-nibble tags are explicit and unique:
//     HEADER = 4'b1010
//     ABORT  = 4'b1011
//     TRAILER= 4'b1100
//     TRIGGER= 4'b1110
// - Header word:  {HEADER,  event_id[19:0], rd_bank_sel, 15'b0}
// - Trailer word: {TRAILER, event_id[19:0], trig_count[5:0], hit_count[9:0]}
// - trig_count counts trigger words emitted during FLUSH_BUF/STREAM_LIVE (i.e. included in event).
//   (TRIG_ONLY mode sends trigger words without header/trailer; those are not counted here.)
// -----------------------------------------------------------------------------
//
// RUN ENABLE EXTENSION (2026-01-29):
// - Added run_enable input.
// - When run_enable=0:
//     - FSM is forced to IDLE (no event assembly).
//     - drop_hits is forced high (so upstream can gate writes).
//     - timers are held reset/disarmed (no window accounting during config).
//     - clear requests asserted (clr_hit_fifos/clr_trig_fifo) for upstream FIFO wrappers.
// -----------------------------------------------------------------------------
//
// BURST ABORT EXTENSION (2026-01-29):
// - Added hit_upper_threshold.
// - Abort condition is ONLY checked in STREAM_LIVE:
//     - If hit_count reaches hit_upper_threshold while in STREAM_LIVE,
//       ABORT the event by:
//         1) Emitting special burst-abort marker word:
//              {ABORT, burst_subtype[3:0], burst_magic[21:0], hit_upper_threshold[9:0]}
//         2) Emitting normal trailer word
//         3) Pulsing clr_hit_fifos/clr_trig_fifo (clear all FIFOs upstream)
//         4) Returning to IDLE
// - The raw-word upper limit is independent of tube thresholds; zero selects
//   the trailer's representable maximum (1023) to prevent count wraparound.
// - Abort path uses dedicated states (does NOT reuse SEND_HEAD).
// -----------------------------------------------------------------------------
//
// FSM WATCHDOG EXTENSION (2026-03-25):
// - Added configurable fsm_watchdog_cycles input.
// - If the FSM stays non-IDLE too long without observable progress, force it into
//   a watchdog-abort path that emits:
//     {ABORT, watchdog_subtype[3:0], watchdog_magic[10:0], watchdog_cnt_at_abort[20:0]}
//   optionally emits a trailer for already-committed events, then clears the FIFOs
//   and returns to IDLE.
// - This is intended as a last-resort hardware unlock path; data may be lost.
// -----------------------------------------------------------------------------
//
// RAW HIT STREAM EXTENSION (2026-05-14):
// - Added stream_hits_only input for noise tests.
// - When enable && run_enable && stream_hits_only:
//     - Event FSM is held IDLE.
//     - wr_bank_sel/rd_bank_sel are held at bank A and drop_hits is deasserted.
//     - Trigger FIFO is held clear.
//     - Each selected TDC FIFO word is forwarded directly as event_data.
//   No event header, trailer, trigger word, threshold cut, or window cut is applied.
// - When stream_counts_only is set, this block only protects the hit/trigger FIFOs
//   while a separate counter streamer writes rate packets to the readout FIFO.
// -----------------------------------------------------------------------------


`define ILA_EVENT_BUILDER

module event_builder_byhit
#(
    parameter integer PREBUF_DEPTH = 128,
    parameter integer TDC_COUNT = 10,
    // The MSB of the 20-bit triggerless event ID identifies the chamber;
    // the remaining 19 bits are an independent per-chamber sequence number.
    parameter integer CHAMBER_ID = 0,
    parameter integer ENABLE_ILA = 1
)
(
    input  wire        clk,
    input  wire        rst,
    input  wire        enable,
    input  wire        run_enable,   // NEW: DAQ RUN gate (prevents config/junk assembly)
    input  wire        stream_hits_only, // RAW hit stream mode for noise tests
    input  wire        stream_counts_only, // Counter packet mode for noise tests

    // Config
    input  wire [15:0] window_cycles,
    input  wire [9:0]  hit_threshold,
    input  wire [9:0]  hit_upper_threshold,  // NEW: burst abort threshold
    input  wire [20:0] fsm_watchdog_cycles,  // NEW: global FSM watchdog in clk cycles
    input  wire        geometry_ready,
    input  wire [47:0] hit_geometry,
    input  wire [42:0] filter_settings,
    input  wire [15:0] selected_mls,
    input  wire [255:0] selected_layers,

    // Trigger FIFO interface (30-bit payload)
    input  wire        trigger_fifo_empty,
    input  wire [29:0] trigger_fifo_data,
    output reg         trigger_fifo_read,

    // Real per-bank empty indicators
    input  wire        fifoA_empty,
    input  wire        fifoB_empty,

    input  wire [TDC_COUNT-1:0] overflowA,
    input  wire [TDC_COUNT-1:0] overflowB,

    // Selected (muxed) hit FIFO interface for rd_bank_sel bank
    input  wire        tdc_fifo_empty,
    input  wire [39:0] tdc_fifo_data,
    output reg         tdc_fifo_read,

    // Ping-pong control
    output reg         wr_bank_sel,   // 0=A, 1=B
    output reg         rd_bank_sel,   // 0=A, 1=B
    output reg         drop_hits,

    // FIFO clear requests (wire these in your FIFO wrapper)
    output reg         clr_hit_fifos,
    output reg         clr_trig_fifo,

    // Readout FIFO
    input  wire        readout_fifo_full,
    output reg  [39:0] event_data,
    output reg         event_data_ready,
    // One-cycle diagnostic increments; see triggerless_diagnostics.sv.
    output wire [13:0] diagnostic_pulses
    // output reg         building_busy
);

wire active = enable & run_enable;
wire count_stream_active = active & stream_counts_only;
wire stream_active = active & stream_hits_only & ~stream_counts_only;
wire event_active  = active & ~stream_hits_only & ~stream_counts_only;

// =========================================================================
// Prebuffer (store hit words before commit so we can discard if never committed)
// =========================================================================
localparam integer PREBUF_AW = (PREBUF_DEPTH <= 2) ? 1 : $clog2(PREBUF_DEPTH);
localparam integer FSM_WDOG_AW = 21;
localparam [9:0]  HIT_THRESHOLD_MAX = (PREBUF_DEPTH > 1023) ? 10'd1023 : PREBUF_DEPTH;

reg [39:0] prebuf_mem [0:PREBUF_DEPTH-1];
reg [PREBUF_AW-1:0] prebuf_wptr, prebuf_rptr;
reg [PREBUF_AW:0]   prebuf_count;

wire prebuf_full  = (prebuf_count == PREBUF_DEPTH);
wire prebuf_empty = (prebuf_count == 0);

// =========================================================================
// Event bookkeeping (preserve your header/trailer packing)
// =========================================================================
reg  [9:0]  hit_count;
reg         committed;

// committed-event ID (20 bits) and per-event trigger counter (6 bits)
// - committed_evt_ctr increments ONLY when an event is committed (CAPTURE_PRE->SEND_HEAD).
// - cur_event_id is latched at commit so header/trailer show the SAME ID.
// - trigger_count counts trigger words emitted during FLUSH_BUF/STREAM_LIVE.
reg  [19:0] committed_evt_ctr;
reg  [19:0] cur_event_id;
reg  [5:0]  trigger_count;

// Prefer toggle for simple alternation between trigger words and hit words
reg prefer_trig;
reg abort_is_watchdog;
reg [FSM_WDOG_AW-1:0] abort_watchdog_count;
reg [10:0] abort_watchdog_state;

// Top-nibble tags for event-builder control words.
localparam [3:0] WORD_TAG_HEADER  = 4'hA;
localparam [3:0] WORD_TAG_ABORT   = 4'hB;
localparam [3:0] WORD_TAG_TRAILER = 4'hC;
localparam [3:0] WORD_TAG_TRIGGER = 4'hE;

localparam [3:0]  ABORT_SUBTYPE_BURST    = 4'hA;
localparam [3:0]  ABORT_SUBTYPE_WATCHDOG = 4'hD;
localparam [21:0] BURST_ABORT_MAGIC      = 22'h2AAAAA;

// Trigger word packing (single 40-bit "data" word)
wire [39:0] trig_word  = {WORD_TAG_TRIGGER, 6'b0, trigger_fifo_data};
wire [18:0] next_event_sequence = committed_evt_ctr[18:0] + 19'd1;

// Special abort marker words (40-bit)
wire [35:0] burst_abort_payload    = {ABORT_SUBTYPE_BURST, BURST_ABORT_MAGIC, hit_upper_threshold};
wire [35:0] watchdog_abort_payload = {ABORT_SUBTYPE_WATCHDOG, abort_watchdog_state, abort_watchdog_count};
wire [39:0] burst_abort_word       = {WORD_TAG_ABORT, burst_abort_payload};
wire [39:0] watchdog_abort_word    = {WORD_TAG_ABORT, watchdog_abort_payload};
wire [39:0] abort_word          = abort_is_watchdog ? watchdog_abort_word : burst_abort_word;

// Verilog: declare these at module scope (cannot declare wire inside always @(*))
wire flush_hit_av  = ~prebuf_empty;
wire flush_trig_av = ~trigger_fifo_empty;
wire flush_both_av = flush_hit_av & flush_trig_av;

wire live_hit_av   = ~tdc_fifo_empty;
wire live_trig_av  = ~trigger_fifo_empty;
wire live_both_av  = live_hit_av & live_trig_av;

// Clamp unsafe runtime configuration locally so the FSM behaves sensibly even if
// software writes an out-of-range value.
wire [15:0] window_cycles_eff = (window_cycles == 16'd0) ? 16'd1 : window_cycles;
wire [9:0]  hit_threshold_eff = (hit_threshold > HIT_THRESHOLD_MAX) ? HIT_THRESHOLD_MAX : hit_threshold;

// =========================================================================
// Ping-pong timers (per bank)
// =========================================================================
reg  [15:0] timer_cnt_A, timer_cnt_B;
reg         timer_run_A, timer_run_B;
reg         timer_done_A, timer_done_B;

reg         older_bank;   // 0=A, 1=B
reg         older_timer_done_latched;
reg  [1:0]  abort_rearm_count;

// drop guard bookkeeping
// - drop_latch: once must_drop fires, keep dropping until event start defines older_bank.
reg         drop_latch;

// Edge detect empty->nonempty for timer start
reg fifoA_empty_d, fifoB_empty_d;
wire fifoA_became_nonempty = fifoA_empty_d & ~fifoA_empty;
wire fifoB_became_nonempty = fifoB_empty_d & ~fifoB_empty;

// Derived conditions
wire any_nonempty      = (~fifoA_empty) | (~fifoB_empty);
wire older_not_drained = (older_bank == 1'b0) ? (~fifoA_empty) : (~fifoB_empty);
wire both_timers_done  = timer_done_A & timer_done_B;
wire must_drop         = both_timers_done & older_not_drained;

wire wr_timer_done     = (wr_bank_sel == 1'b0) ? timer_done_A : timer_done_B;

// Event ends when older bank drained AND older timer done
wire event_done_older =
    (!older_not_drained) &&
    older_timer_done_latched;

// Commit conditions:
wire threshold_reached;
wire trigger_available = ~trigger_fifo_empty;
reg discarding;
wire commit_condition = threshold_reached && !discarding;

// =========================================================================
// FSM (1-hot with bit indices)
// =========================================================================
reg [10:0] state;
reg [10:0] nextstate;
reg [10:0] watchdog_prev_state;
reg [FSM_WDOG_AW-1:0] fsm_watchdog_cnt;

localparam IDLE         = 11'b000_0000_0001;
localparam TRIG_ONLY    = 11'b000_0000_0010; // send trigger(s) alone while idle (no hits pending)
localparam START_EVENT  = 11'b000_0000_0100;
localparam CAPTURE_PRE  = 11'b000_0000_1000; // buffer hits until committed
localparam SEND_HEAD    = 11'b000_0001_0000;
localparam FLUSH_BUF    = 11'b000_0010_0000;
localparam STREAM_LIVE  = 11'b000_0100_0000; // interleave trigger + live hits
localparam SEND_TRAIL   = 11'b000_1000_0000;

// NEW abort dedicated states (do NOT reuse SEND_HEAD)
localparam ABORT_MARK   = 11'b001_0000_0000; // emit abort marker word
localparam ABORT_TRAIL  = 11'b010_0000_0000; // emit normal trailer
localparam ABORT_CLEAN  = 11'b100_0000_0000; // pulse clears + reset internal bookkeeping

localparam IDLE_BIT        = 0;
localparam TRIG_ONLY_BIT   = 1;
localparam START_EVENT_BIT = 2;
localparam CAPTURE_PRE_BIT = 3;
localparam SEND_HEAD_BIT   = 4;
localparam FLUSH_BUF_BIT   = 5;
localparam STREAM_LIVE_BIT = 6;
localparam SEND_TRAIL_BIT  = 7;
localparam ABORT_MARK_BIT  = 8;
localparam ABORT_TRAIL_BIT = 9;
localparam ABORT_CLEAN_BIT = 10;

// true "event start" pulse (IDLE -> START_EVENT).
wire start_pulse = state[IDLE_BIT] && nextstate[START_EVENT_BIT] && event_active;

// true "event finished" pulse back to IDLE.
// Used to release the drop guard after an overloaded event fully closes/discards.
wire finish_to_idle = !state[IDLE_BIT] && nextstate[IDLE_BIT] && event_active;

// commit pulse (CAPTURE_PRE -> SEND_HEAD)
// This fires exactly once per committed event, even if SEND_HEAD stalls on readout_fifo_full.
wire commit_pulse = state[CAPTURE_PRE_BIT] && nextstate[SEND_HEAD_BIT] && event_active;

wire [9:0] raw_limit = hit_upper_threshold == 0 ? 10'd1023 : hit_upper_threshold;
wire abort_enabled = 1'b1;

// Abort only checked in STREAM_LIVE, based on the *next* hit count if we pop a HIT this cycle
wire [10:0] hit_count_next11 = {1'b0, hit_count} + (tdc_fifo_read ? 11'd1 : 11'd0);

wire abort_now = abort_enabled &&
                 state[STREAM_LIVE_BIT] &&
                 (hit_count_next11 >= {1'b0, raw_limit});

wire reject_full_candidate = state[CAPTURE_PRE_BIT] && !commit_condition &&
                             (prebuf_full || hit_count >= raw_limit);
wire reject_finished_candidate = state[CAPTURE_PRE_BIT] && event_done_older &&
                                 !commit_condition;
wire abort_clean_pulse = event_active && state[ABORT_CLEAN_BIT];
wire [9:0] distinct_tube_count;
wire [3:0] failed_filters;
tube_event_filter #(.CHAMBER_ID(CHAMBER_ID)) tube_filter (
    .clk(clk),
    .clear(rst || !event_active || state[IDLE_BIT] || state[START_EVENT_BIT] || abort_clean_pulse),
    .hit_accept(state[CAPTURE_PRE_BIT] && tdc_fifo_read && !discarding),
    .geometry_ready(geometry_ready),
    .geometry(hit_geometry),
    .settings(filter_settings),
    .selected_mls(selected_mls),
    .selected_layers(selected_layers),
    .pass(threshold_reached),
    .tube_count(distinct_tube_count),
    .new_tube(),
    .failed_filters(failed_filters)
);

always @(posedge clk) begin
    if (rst || !event_active || state[IDLE_BIT] || state[START_EVENT_BIT] || abort_clean_pulse)
        discarding <= 1'b0;
    else if (reject_full_candidate)
        discarding <= 1'b1;
end

// Handy one-cycle pulse when ABORT_CLEAN runs (used to reset internal stuff)
wire aborting_fsm = state[ABORT_MARK_BIT] | state[ABORT_TRAIL_BIT] | state[ABORT_CLEAN_BIT];

wire watchdog_enabled = (fsm_watchdog_cycles != 21'd0);
wire fsm_activity_pulse = start_pulse | commit_pulse | finish_to_idle |
                          event_data_ready | tdc_fifo_read | trigger_fifo_read;
wire [20:0] watchdog_limit = watchdog_enabled ? (fsm_watchdog_cycles - 21'd1) : 21'd0;
wire watchdog_timeout = watchdog_enabled &&
                        event_active &&
                        !state[IDLE_BIT] &&
                        !aborting_fsm &&
                        (fsm_watchdog_cnt == watchdog_limit);

// Diagnostics do not drive the acquisition FSM. Resolve each candidate once,
// including a pre-commit stop/reset and an abort while draining a rejected bank.
// TRIG_ONLY can also transition to START_EVENT (without the legacy start_pulse).
reg diagnostic_pending;
wire diagnostic_start = event_active && !rst && nextstate[START_EVENT_BIT] &&
                        (state[IDLE_BIT] || state[TRIG_ONLY_BIT]);
wire diagnostic_interrupted = diagnostic_pending && (rst || !event_active);
wire diagnostic_filter_reject = diagnostic_pending && event_active && !rst &&
    !watchdog_timeout && (reject_full_candidate || reject_finished_candidate);
wire diagnostic_reject = diagnostic_interrupted || diagnostic_filter_reject ||
    (diagnostic_pending && event_active && !rst && watchdog_timeout);
wire diagnostic_accept = diagnostic_pending && commit_pulse && !rst;
always @(posedge clk) begin
    if (rst || !event_active || diagnostic_reject || diagnostic_accept)
        diagnostic_pending <= 1'b0;
    else if (diagnostic_start)
        diagnostic_pending <= 1'b1;
end
assign diagnostic_pulses[0] = diagnostic_accept || diagnostic_reject;
assign diagnostic_pulses[1] = diagnostic_accept;
assign diagnostic_pulses[2] = diagnostic_reject;
assign diagnostic_pulses[6:3] = failed_filters & {4{diagnostic_filter_reject}};
assign diagnostic_pulses[7] = diagnostic_filter_reject && prebuf_full;
assign diagnostic_pulses[8] = diagnostic_filter_reject && hit_count >= raw_limit;
// FIFO losses are accumulated from the per-TDC write attempts upstream.
assign diagnostic_pulses[9] = 1'b0;
assign diagnostic_pulses[10] = watchdog_timeout && !rst;
// Count actual popped unmapped words, including post-commit and discard drains.
assign diagnostic_pulses[11] = event_active && !rst && tdc_fifo_read &&
    !(geometry_ready && hit_geometry[0] &&
      hit_geometry[1] == (CHAMBER_ID != 0) && hit_geometry[32:23] < 960);
assign diagnostic_pulses[12] = diagnostic_interrupted;
assign diagnostic_pulses[13] = event_active && !rst && abort_now && !watchdog_timeout;

// State register
always @(posedge clk) begin
    if (rst) begin
        state <= IDLE;
    end else begin
        state <= event_active ? nextstate : IDLE;
    end
end

always @(posedge clk) begin
    if (rst) begin
        watchdog_prev_state <= IDLE;
        fsm_watchdog_cnt    <= {FSM_WDOG_AW{1'b0}};
    end else if (!event_active || abort_clean_pulse) begin
        watchdog_prev_state <= IDLE;
        fsm_watchdog_cnt    <= {FSM_WDOG_AW{1'b0}};
    end else begin
        watchdog_prev_state <= state;

        if (state[IDLE_BIT] || (state != watchdog_prev_state) || fsm_activity_pulse) begin
            fsm_watchdog_cnt <= {FSM_WDOG_AW{1'b0}};
        end else if (watchdog_enabled && !watchdog_timeout) begin
            fsm_watchdog_cnt <= fsm_watchdog_cnt + {{(FSM_WDOG_AW-1){1'b0}}, 1'b1};
        end
    end
end

always @(posedge clk) begin
    if (rst) begin
        abort_rearm_count <= 2'd0;
    end else if (!event_active) begin
        abort_rearm_count <= 2'd0;
    end else if (abort_clean_pulse) begin
        abort_rearm_count <= 2'd2;
    end else if (abort_rearm_count != 2'd0) begin
        abort_rearm_count <= abort_rearm_count - 2'd1;
    end
end

wire abort_rearm_pending = (abort_rearm_count != 2'd0);

// =========================================================================
// Next-state logic
// =========================================================================
always @(*) begin
    if (!event_active) begin
        nextstate = IDLE;
    end else if (watchdog_timeout) begin
        nextstate = ABORT_MARK;
    end else begin
        case (state)
            IDLE: begin
                // Hold IDLE while upstream clear pulses are active so we do not
                // start a phantom event from stale FIFO-empty flags during cleanup.
                if (clr_hit_fifos || clr_trig_fifo || abort_rearm_pending)
                    nextstate = IDLE;
                // EVENT FIRST if any hits pending in ping-pong banks
                else if (any_nonempty)
                    nextstate = START_EVENT;
                // Only send trigger-alone if NO hits pending
                else if (~trigger_fifo_empty)
                    nextstate = TRIG_ONLY;
                else
                    nextstate = IDLE;
            end

            TRIG_ONLY: begin
                // If hits appear, immediately start event first
                if (any_nonempty)
                    nextstate = START_EVENT;
                else if (~trigger_fifo_empty)
                    nextstate = TRIG_ONLY;
                else
                    nextstate = IDLE;
            end

            START_EVENT:
                nextstate = CAPTURE_PRE;

            CAPTURE_PRE: begin
                // Check acceptance first: the final FIFO hit may have made the
                // tube counters pass on the same edge that emptied the bank.
                if (commit_condition)
                    nextstate = SEND_HEAD;     // commit and start sending
                else if (event_done_older)
                    nextstate = IDLE;          // discard
                else
                    nextstate = CAPTURE_PRE;
            end

            SEND_HEAD:
                nextstate = readout_fifo_full ? SEND_HEAD : FLUSH_BUF;

            FLUSH_BUF:
                nextstate = readout_fifo_full ? FLUSH_BUF :
                            ((prebuf_empty && trigger_fifo_empty) ?
                                (event_done_older ? SEND_TRAIL : STREAM_LIVE) :
                                FLUSH_BUF);

            STREAM_LIVE: begin
                // BURST ABORT is ONLY checked here
                if (abort_now)
                    nextstate = ABORT_MARK;
                else if (event_done_older && tdc_fifo_empty && trigger_fifo_empty)
                    nextstate = SEND_TRAIL;
                else
                    nextstate = STREAM_LIVE;
            end

            SEND_TRAIL:
                nextstate = readout_fifo_full ? SEND_TRAIL : IDLE;

            // Abort states:
            ABORT_MARK:
                nextstate = readout_fifo_full ? ABORT_MARK :
                            (committed ? ABORT_TRAIL : ABORT_CLEAN);

            ABORT_TRAIL:
                nextstate = readout_fifo_full ? ABORT_TRAIL : ABORT_CLEAN;

            ABORT_CLEAN:
                nextstate = IDLE;

            default:
                nextstate = IDLE;
        endcase
    end
end

// =========================================================================
// Abort cause bookkeeping
// =========================================================================
always @(posedge clk) begin
    if (rst) begin
        abort_is_watchdog <= 1'b0;
        abort_watchdog_count <= {FSM_WDOG_AW{1'b0}};
        abort_watchdog_state <= IDLE;
    end else if (!event_active || abort_clean_pulse || state[IDLE_BIT]) begin
        abort_is_watchdog <= 1'b0;
        abort_watchdog_count <= {FSM_WDOG_AW{1'b0}};
        abort_watchdog_state <= IDLE;
    end else if (watchdog_timeout) begin
        abort_is_watchdog <= 1'b1;
        abort_watchdog_count <= fsm_watchdog_cnt;
        abort_watchdog_state <= state;
    end else if (abort_now) begin
        abort_is_watchdog <= 1'b0;
        abort_watchdog_count <= {FSM_WDOG_AW{1'b0}};
        abort_watchdog_state <= IDLE;
    end
end

// =========================================================================
// FIFO clear requests (wire to wrappers)
// =========================================================================
// - Hold clear asserted while not running (config time)
// - Pulse clear during ABORT_CLEAN
always @(posedge clk) begin
    if (rst) begin
        clr_hit_fifos <= 1'b1;
        clr_trig_fifo <= 1'b1;
    end else begin
        // Default deassert
        clr_hit_fifos <= 1'b0;
        clr_trig_fifo <= 1'b0;

        // Hold clear asserted while not running (config time)
        if (!run_enable) begin
            clr_hit_fifos <= 1'b1;
            clr_trig_fifo <= 1'b1;
        end
        // Raw hit stream mode ignores triggers; keep the trigger FIFO empty.
        else if (stream_active) begin
            clr_trig_fifo <= 1'b1;
        end
        // Counter stream mode does not consume hit/trigger FIFOs.
        else if (count_stream_active) begin
            clr_hit_fifos <= 1'b1;
            clr_trig_fifo <= 1'b1;
        end
        // Pulse clear after the abort marker and any required trailer have been emitted
        else if (abort_clean_pulse) begin
            clr_hit_fifos <= 1'b1;
            clr_trig_fifo <= 1'b1;
        end
        else if (discarding || reject_finished_candidate) begin
            // Drain only the selected hit bank; do not clear the next candidate
            // in the other bank or any FIFO belonging to the other chamber.
            clr_trig_fifo <= 1'b1;
        end
    end
end

// =========================================================================
// Empty edge capture
// =========================================================================
always @(posedge clk) begin
    if (rst) begin
        fifoA_empty_d <= 1'b1;
        fifoB_empty_d <= 1'b1;
    end else begin
        fifoA_empty_d <= fifoA_empty;
        fifoB_empty_d <= fifoB_empty;
    end
end

// =========================================================================
// Bank timers
// =========================================================================
// IMPORTANT: abort_clean_pulse hard-disarms timers so we don't inherit stale done/run state
always @(posedge clk) begin
    if (rst) begin
        timer_cnt_A  <= 16'd0;
        timer_run_A  <= 1'b0;
        timer_done_A <= 1'b0;
    end else if (!event_active || abort_clean_pulse) begin
        // While not running OR after abort, hold timers disarmed
        timer_cnt_A  <= 16'd0;
        timer_run_A  <= 1'b0;
        timer_done_A <= 1'b0;
    end else begin
        // re-arm condition: once done, wait until bank truly drained, then clear done
        if (timer_done_A && fifoA_empty) begin
            timer_done_A <= 1'b0;
            timer_cnt_A  <= 16'd0;
            timer_run_A  <= 1'b0;
        end
        // start timer on first hit of a new window
        else if (!timer_run_A && !timer_done_A && fifoA_became_nonempty) begin
            timer_run_A <= 1'b1;
            timer_cnt_A <= 16'd0;
        end
        // run to completion regardless of fifoA_empty glitches
        else if (timer_run_A) begin
            if (timer_cnt_A == window_cycles_eff - 1'b1) begin
                timer_run_A  <= 1'b0;
                timer_done_A <= 1'b1;
            end else begin
                timer_cnt_A <= timer_cnt_A + 16'd1;
            end
        end
    end
end

always @(posedge clk) begin
    if (rst) begin
        timer_cnt_B  <= 16'd0;
        timer_run_B  <= 1'b0;
        timer_done_B <= 1'b0;
    end else if (!event_active || abort_clean_pulse) begin
        // While not running OR after abort, hold timers disarmed
        timer_cnt_B  <= 16'd0;
        timer_run_B  <= 1'b0;
        timer_done_B <= 1'b0;
    end else begin
        // re-arm condition: once done, wait until bank truly drained, then clear done
        if (timer_done_B && fifoB_empty) begin
            timer_done_B <= 1'b0;
            timer_cnt_B  <= 16'd0;
            timer_run_B  <= 1'b0;
        end
        // start timer on first hit of a new window
        else if (!timer_run_B && !timer_done_B && fifoB_became_nonempty) begin
            timer_run_B <= 1'b1;
            timer_cnt_B <= 16'd0;
        end
        // run to completion regardless of fifoB_empty glitches
        else if (timer_run_B) begin
            if (timer_cnt_B == window_cycles_eff - 1'b1) begin
                timer_run_B  <= 1'b0;
                timer_done_B <= 1'b1;
            end else begin
                timer_cnt_B <= timer_cnt_B + 16'd1;
            end
        end
    end
end

// =========================================================================
// older_bank, rd_bank_sel, wr_bank_sel
// =========================================================================
//
// Policy:
// - older_bank is latched ONLY at event start (IDLE -> START_EVENT).
// - rd_bank_sel is latched to older_bank at event start and stays fixed for the event.
//
// Rationale:
// - wr_bank_sel may have already toggled due to timer_done_* while the older bank
//   still contains unread hits. Reading wr_bank_sel would then read the *new* bank.
// - With the ping-pong wrapper, both banks can be non-empty; "prefer A if non-empty"
//   is NOT a valid definition of "older".
//
// (guard requested):
// - When must_drop asserts, we LATCH dropping (drop_latch) and do NOT release it
//   until either:
//     1) older_bank has been defined at start_pulse, or
//     2) the current event has fully finished and returned to IDLE.
//   This prevents writes from resuming before we have a stable drain target.

wire older_bank_det =
    (~fifoA_empty &&  fifoB_empty) ? 1'b0 :  // A only
    ( fifoA_empty && ~fifoB_empty) ? 1'b1 :  // B only
                                    older_bank; // both non-empty: keep previous

always @(posedge clk) begin
    if (rst) begin
        older_bank  <= 1'b0;
        rd_bank_sel <= 1'b0;
    end else if (!event_active || abort_clean_pulse) begin
        // When not running OR after abort, keep bank selects at default
        older_bank  <= 1'b0;
        rd_bank_sel <= 1'b0;
    end else if (start_pulse) begin
        older_bank  <= older_bank_det;
        rd_bank_sel <= older_bank_det;  // <-- critical: do NOT use older_bank here
    end
end

// wr_bank_sel (write-bank switching on timer-done)
always @(posedge clk) begin
    if (rst) begin
        wr_bank_sel <= 1'b0; // A
    end else if (!event_active || abort_clean_pulse) begin
        wr_bank_sel <= 1'b0; // A
    end else begin
        // Freeze switching while dropping is active (must_drop or latched)
        if (!(must_drop | drop_latch)) begin
            // If currently writing A and A's window is done -> switch to B
            if ((wr_bank_sel == 1'b0) && timer_done_A) begin
                wr_bank_sel <= 1'b1;
            end
            // If currently writing B and B's window is done -> switch to A
            else if ((wr_bank_sel == 1'b1) && timer_done_B) begin
                wr_bank_sel <= 1'b0;
            end
        end
    end
end

// Latch the older-bank timer completion for the duration of the current event so
// the close condition is not lost if the raw timer_done pulse clears while the
// FSM is between FLUSH_BUF and STREAM_LIVE.
always @(posedge clk) begin
    if (rst) begin
        older_timer_done_latched <= 1'b0;
    end else if (!event_active || abort_clean_pulse) begin
        older_timer_done_latched <= 1'b0;
    end else if (start_pulse) begin
        older_timer_done_latched <= 1'b0;
    end else if ((older_bank == 1'b0 && timer_done_A) ||
                 (older_bank == 1'b1 && timer_done_B)) begin
        older_timer_done_latched <= 1'b1;
    end
end


// =========================================================================
// drop_hits (with guard latch)
// =========================================================================
wire release_drop_guard = drop_latch && (start_pulse || finish_to_idle);

always @(posedge clk) begin
    if (rst) begin
        drop_latch <= 1'b0;
        drop_hits  <= 1'b0;
    end else if (!active) begin
        // While not running: force upstream to gate writes (avoid config/junk fill)
        drop_latch <= 1'b0;
        drop_hits  <= 1'b1;
    end else if (stream_active) begin
        // Raw stream mode must not deliberately drop hits.
        drop_latch <= 1'b0;
        drop_hits  <= 1'b0;
    end else if (count_stream_active) begin
        // Counter stream mode counts before the FIFO, then discards hit words.
        drop_latch <= 1'b0;
        drop_hits  <= 1'b1;
    end else if (abort_clean_pulse) begin
        // After abort, release drop bookkeeping (FIFOs are being cleared anyway)
        drop_latch <= 1'b0;
        drop_hits  <= 1'b1;
    end else begin
        // Latch drop as soon as must_drop happens
        if (must_drop)
            drop_latch <= 1'b1;

        // Release the guard once a new event has a stable older_bank, or once the
        // overloaded event has fully closed/discarded back to IDLE.
        if (release_drop_guard)
            drop_latch <= 1'b0;

        // Effective drop to upstream
        drop_hits <= must_drop | (drop_latch & ~release_drop_guard) | aborting_fsm;
    end
end

// =========================================================================
// committed-event counter and per-event trigger counter
// =========================================================================
// committed_evt_ctr increments ONLY when an event is committed (commit_pulse).
// cur_event_id is latched so header/trailer show the SAME ID.
// trigger_count resets at start_pulse and counts trigger words emitted as part of the event.
always @(posedge clk) begin
    if (rst) begin
        committed_evt_ctr <= 20'd0;
        cur_event_id      <= 20'd0;
    end else begin
        if (commit_pulse) begin
            committed_evt_ctr <= {1'b0, next_event_sequence};
            cur_event_id      <= {(CHAMBER_ID != 0), next_event_sequence};
        end
    end
end

always @(posedge clk) begin
    if (rst) begin
        trigger_count <= 6'd0;
    end else begin
        if (!event_active || start_pulse || abort_clean_pulse) begin
            trigger_count <= 6'd0;
        end else begin
            // Count triggers that are actually emitted during the committed event
            // (TRIG_ONLY has no trailer; we don't include those here)
            if (trigger_fifo_read && (state[FLUSH_BUF_BIT] || state[STREAM_LIVE_BIT])) begin
                trigger_count <= trigger_count + 6'd1;
            end
        end
    end
end

// =========================================================================
// Hit counter + commit latch + prefer_trig toggle init
// =========================================================================
reg flushbuf_pop_pulse;
reg prefer_trig_toggle_pulse;

always @(posedge clk) begin
    if (rst) begin
        hit_count   <= 10'd0;
        committed   <= 1'b0;
        prefer_trig <= 1'b0;
    end else begin
        if (start_pulse || abort_clean_pulse) begin
            hit_count   <= 10'd0;
            committed   <= 1'b0;
            prefer_trig <= 1'b0;
        end else if (state[IDLE_BIT]) begin
            hit_count   <= 10'd0;
            committed   <= 1'b0;
            prefer_trig <= 1'b0;
        end else if (!event_active) begin
            hit_count   <= 10'd0;
            committed   <= 1'b0;
            prefer_trig <= 1'b0;
        end else begin
            if (tdc_fifo_read && !discarding) begin
                hit_count <= hit_count + 10'd1;
            end

            if (commit_pulse)
                committed <= 1'b1;

            if (prefer_trig_toggle_pulse)
                prefer_trig <= ~prefer_trig;
        end
    end
end

// =========================================================================
// Prebuffer pointers + RAM write/read
// =========================================================================
always @(posedge clk) begin
    if (rst) begin
        prebuf_wptr  <= {PREBUF_AW{1'b0}};
        prebuf_rptr  <= {PREBUF_AW{1'b0}};
        prebuf_count <= {(PREBUF_AW+1){1'b0}};
    end else begin
        if (start_pulse || abort_clean_pulse) begin
            prebuf_wptr  <= {PREBUF_AW{1'b0}};
            prebuf_rptr  <= {PREBUF_AW{1'b0}};
            prebuf_count <= {(PREBUF_AW+1){1'b0}};
        end

        // Buffer writes during CAPTURE_PRE
        if (state[CAPTURE_PRE_BIT] && tdc_fifo_read && !discarding) begin
            if (!prebuf_full) begin
                prebuf_mem[prebuf_wptr] <= tdc_fifo_data;
                prebuf_wptr  <= prebuf_wptr + 1'b1;
                prebuf_count <= prebuf_count + 1'b1;
            end
        end

        // Buffer read advance (pulse made in comb output logic)
        if (flushbuf_pop_pulse) begin
            prebuf_rptr  <= prebuf_rptr + 1'b1;
            prebuf_count <= prebuf_count - 1'b1;
        end

        // Discard case
        if (reject_finished_candidate) begin
            prebuf_wptr  <= {PREBUF_AW{1'b0}};
            prebuf_rptr  <= {PREBUF_AW{1'b0}};
            prebuf_count <= {(PREBUF_AW+1){1'b0}};
        end

        // When not running, clear local prebuffer immediately
        // (prevents config-time residuals from being flushed when run starts)
        if (!run_enable || stream_active || count_stream_active) begin
            prebuf_wptr  <= {PREBUF_AW{1'b0}};
            prebuf_rptr  <= {PREBUF_AW{1'b0}};
            prebuf_count <= {(PREBUF_AW+1){1'b0}};
        end
    end
end

// =========================================================================
// Combinational output logic (event-first policy already handled in FSM)
// =========================================================================
always @(*) begin
    event_data_ready  = 1'b0;
    event_data        = 40'd0;
    tdc_fifo_read     = 1'b0;
    trigger_fifo_read = 1'b0;

    flushbuf_pop_pulse       = 1'b0;
    prefer_trig_toggle_pulse = 1'b0;

    if (stream_active) begin
        if (!readout_fifo_full && !tdc_fifo_empty) begin
            event_data_ready = 1'b1;
            event_data       = tdc_fifo_data;
            tdc_fifo_read    = 1'b1;
        end
    end

    else if (event_active) begin
        // CAPTURE_PRE only drains into the local prebuffer, so it must keep making
        // progress even when the downstream readout FIFO is backpressured.
        if (state[CAPTURE_PRE_BIT]) begin
            if (!tdc_fifo_empty && (discarding || (!prebuf_full && hit_count < raw_limit))) begin
                tdc_fifo_read = 1'b1;
            end
        end

        else if (!readout_fifo_full) begin
            // TRIG_ONLY: send triggers alone
            if (state[TRIG_ONLY_BIT]) begin
                if (~trigger_fifo_empty) begin
                    event_data_ready  = 1'b1;
                    event_data        = trig_word;
                    trigger_fifo_read = 1'b1;
                end
            end

            // SEND_HEAD
            else if (state[SEND_HEAD_BIT]) begin
                event_data_ready = 1'b1;
                // Header word: [39:36]=WORD_TAG_HEADER, [35:16]=cur_event_id[19:0],
                // [15]=rd_bank_sel, [14:0]=0.
                event_data       = {WORD_TAG_HEADER, cur_event_id, rd_bank_sel, 15'b0};
            end

            // FLUSH_BUF: interleave trigger and buffered hits
            else if (state[FLUSH_BUF_BIT]) begin
                if (flush_both_av) begin
                    if (prefer_trig) begin
                        event_data_ready  = 1'b1;
                        event_data        = trig_word;
                        trigger_fifo_read = 1'b1;
                    end else begin
                        event_data_ready   = 1'b1;
                        event_data         = prebuf_mem[prebuf_rptr];
                        flushbuf_pop_pulse = 1'b1;
                    end
                    prefer_trig_toggle_pulse = 1'b1;
                end else if (flush_trig_av) begin
                    event_data_ready  = 1'b1;
                    event_data        = trig_word;
                    trigger_fifo_read = 1'b1;
                end else if (flush_hit_av) begin
                    event_data_ready   = 1'b1;
                    event_data         = prebuf_mem[prebuf_rptr];
                    flushbuf_pop_pulse = 1'b1;
                end
            end

            // STREAM_LIVE: interleave trigger and live hits
            else if (state[STREAM_LIVE_BIT] && hit_count < raw_limit) begin
                if (live_both_av) begin
                    if (prefer_trig) begin
                        event_data_ready  = 1'b1;
                        event_data        = trig_word;
                        trigger_fifo_read = 1'b1;
                    end else begin
                        event_data_ready = 1'b1;
                        event_data       = tdc_fifo_data;
                        tdc_fifo_read    = 1'b1;
                    end
                    prefer_trig_toggle_pulse = 1'b1;
                end else if (live_trig_av) begin
                    event_data_ready  = 1'b1;
                    event_data        = trig_word;
                    trigger_fifo_read = 1'b1;
                end else if (live_hit_av) begin
                    event_data_ready = 1'b1;
                    event_data       = tdc_fifo_data;
                    tdc_fifo_read    = 1'b1;
                end
            end

            // ABORT_MARK: emit burst-abort or watchdog-abort marker word
            else if (state[ABORT_MARK_BIT]) begin
                event_data_ready = 1'b1;
                event_data       = abort_word;
            end

            // ABORT_TRAIL: emit normal trailer word for committed aborted events
            else if (state[ABORT_TRAIL_BIT]) begin
                event_data_ready = 1'b1;
                // Trailer word: {WORD_TAG_TRAILER, event_id[19:0], trig_count[5:0], hit_count[9:0]}
                event_data       = {WORD_TAG_TRAILER, cur_event_id, trigger_count, hit_count};
            end

            // SEND_TRAIL
            else if (state[SEND_TRAIL_BIT]) begin
                event_data_ready = 1'b1;
                // Trailer word: [39:36]=WORD_TAG_TRAILER, [35:16]=cur_event_id[19:0],
                // [15:10]=trigger_count[5:0], [9:0]=hit_count[9:0].
                event_data       = {WORD_TAG_TRAILER, cur_event_id, trigger_count, hit_count};
            end
        end
    end
end

// ============================================================================
// ILA probes for event_builder_byhit (NO BUNDLES, MAX VISIBILITY)
// - Place this INSIDE event_builder_byhit (near end of module, before endmodule)
// - Generate ila_event_builder IP with matching probe count + widths.
// - Guarded by `ILA_EVENT_BUILDER so you can compile out in production.
// ============================================================================

`ifdef ILA_EVENT_BUILDER

generate
if (ENABLE_ILA != 0) begin : gen_event_builder_ila
ila_event_builder_byhit ila_event_builder_inst (
    .clk (clk),  // 1

    // ------------------------------------------------------------------------
    // FSM / transitions
    // ------------------------------------------------------------------------
    .probe0  (state),                // [10:0]
    .probe1  (nextstate),            // [10:0]
    .probe2  (start_pulse),          // 1
    .probe3  (commit_pulse),         // 1

    // ------------------------------------------------------------------------
    // Config / enables
    // ------------------------------------------------------------------------
    .probe4  (enable),               // 1
    .probe5  (window_cycles),        // [15:0]
    .probe6  (hit_threshold),        // [9:0]

    // ------------------------------------------------------------------------
    // Bank empties + edge detect
    // ------------------------------------------------------------------------
    .probe7  (fifoA_empty),          // 1
    .probe8  (fifoB_empty),          // 1
    .probe9  (fifoA_empty_d),        // 1
    .probe10 (fifoB_empty_d),        // 1
    .probe11 (fifoA_became_nonempty),// 1
    .probe12 (fifoB_became_nonempty),// 1

    // ------------------------------------------------------------------------
    // Derived bank/event conditions
    // ------------------------------------------------------------------------
    .probe13 (any_nonempty),         // 1
    .probe14 (older_bank),           // 1
    .probe15 (older_not_drained),    // 1
    .probe16 (both_timers_done),     // 1
    .probe17 (must_drop),            // 1
    .probe18 (wr_timer_done),        // 1
    .probe19 (event_done_older),     // 1

    // ------------------------------------------------------------------------
    // Timers
    // ------------------------------------------------------------------------
    .probe20 (timer_cnt_A),          // [15:0]
    .probe21 (timer_run_A),          // 1
    .probe22 (timer_done_A),         // 1
    .probe23 (timer_cnt_B),          // [15:0]
    .probe24 (timer_run_B),          // 1
    .probe25 (timer_done_B),         // 1

    // ------------------------------------------------------------------------
    // Ping-pong controls / drop guard
    // ------------------------------------------------------------------------
    .probe26 (wr_bank_sel),          // 1
    .probe27 (rd_bank_sel),          // 1
    .probe28 (drop_hits),            // 1
    .probe29 (drop_latch),           // 1

    // ------------------------------------------------------------------------
    // Commit logic + hit/trigger availability
    // ------------------------------------------------------------------------
    .probe30 (threshold_reached),    // 1
    .probe31 (trigger_available),    // 1
    .probe32 (commit_condition),     // 1
    .probe33 (committed),            // 1

    // ------------------------------------------------------------------------
    // Hit FIFO (selected rd_bank)
    // ------------------------------------------------------------------------
    .probe34 (tdc_fifo_empty),       // 1
    .probe35 (tdc_fifo_read),        // 1
    .probe36 (tdc_fifo_data),        // [39:0]

    // ------------------------------------------------------------------------
    // Trigger FIFO
    // ------------------------------------------------------------------------
    .probe37 (trigger_fifo_empty),   // 1
    .probe38 (trigger_fifo_read),    // 1
    .probe39 (trigger_fifo_data),    // [29:0]
    .probe40 (trig_word),            // [39:0]

    // ------------------------------------------------------------------------
    // Prebuffer bookkeeping
    // ------------------------------------------------------------------------
    .probe41 (prebuf_wptr),          // [PREBUF_AW-1:0]
    .probe42 (prebuf_rptr),          // [PREBUF_AW-1:0]
    .probe43 (prebuf_count),         // [PREBUF_AW:0]
    .probe44 (prebuf_full),          // 1
    .probe45 (prebuf_empty),         // 1

    // ------------------------------------------------------------------------
    // Flush/live availability (arbiter inputs)
    // ------------------------------------------------------------------------
    .probe46 (flush_hit_av),         // 1
    .probe47 (flush_trig_av),        // 1
    .probe48 (flush_both_av),        // 1
    .probe49 (live_hit_av),          // 1
    .probe50 (live_trig_av),         // 1
    .probe51 (live_both_av),         // 1

    // ------------------------------------------------------------------------
    // Interleave control / pulses
    // ------------------------------------------------------------------------
    .probe52 (prefer_trig),              // 1
    .probe53 (prefer_trig_toggle_pulse), // 1
    .probe54 (flushbuf_pop_pulse),       // 1

    // ------------------------------------------------------------------------
    // Counters / IDs
    // ------------------------------------------------------------------------
    .probe55 (hit_count),            // [9:0]
    .probe56 (trigger_count),        // [5:0]
    .probe57 (committed_evt_ctr),    // [19:0]
    .probe58 (cur_event_id),         // [19:0]

    // ------------------------------------------------------------------------
    // Output / backpressure
    // ------------------------------------------------------------------------
    .probe59 (readout_fifo_full),    // 1
    .probe60 (event_data_ready),     // 1
    .probe61 (event_data),           // [39:0]

    .probe62 (overflowA), // [39:0]
    .probe63 (overflowB),  // [39:0]
    .probe64 (abort_now) //1
);
end
endgenerate

`endif

endmodule
