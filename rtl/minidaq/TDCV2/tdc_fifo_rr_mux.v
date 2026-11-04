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
// File   : tdc_fifo_rr_mux.v
// Create : 2025-12-16 17:04:15
// Revise : 2026-01-21 18:08:38
// Editor : sublime text4, tab size (4)
// Description:
//
//   FWFT round-robin "peek + pop" mux for multiple per-TDC FIFOs.
//
//   - Immediately outputs the selected FIFO head word (FWFT peek).
//   - Pops at most 1 FIFO per cycle when tdc_fifo_read_mux == 1 and data exists.
//   - Registered: the memory of who was served last (rr_ptr)
//   - Combinational: who is served now and what data you see now
//   - Fair draining by rotating rr_ptr after each successful pop.
//   - Verilog-2001 compatible (no [base +: width]).
//
// -----------------------------------------------------------------------------
// Interface philosophy (similar to your old tdc_fifo_data_mux.v):
//   - tdc_fifo_data_mux is ALWAYS a peek of the selected FIFO (when not empty).
//   - tdc_fifo_read_mux is "consume one word now" from the selected FIFO.
//   - tdc_fifo_read is one-hot pop strobe to the per-TDC FIFOs.
//
// Notes:
//   - Downstream should only use tdc_fifo_data_mux when tdc_fifo_empty_mux == 0.
//   - With FWFT FIFOs, data is valid immediately when ~empty.
// -----------------------------------------------------------------------------

module tdc_fifo_data_rr_mux #(
    parameter TDC_COUNT      = 8,
    parameter TDC_DATA_WIDTH = 40
)(
    input                        clk,
    input                        rst,

    input  [TDC_COUNT-1:0]       locked,

    // Selected-bank (rd_bank_sel) FIFO view per lane (from pingpong wrapper)
    input  [TDC_COUNT-1:0]       tdc_fifo_empty,
    input  [TDC_COUNT*TDC_DATA_WIDTH-1:0] tdc_fifo_data,

    // NEW: real per-bank empties per lane (from pingpong wrapper)
    input  [TDC_COUNT-1:0]       fifoA_empty,
    input  [TDC_COUNT-1:0]       fifoB_empty,

    input                        tdc_fifo_read_mux,   // downstream consume request

    output reg [TDC_COUNT-1:0]   tdc_fifo_read,        // one-hot pop strobes

    // Selected-bank reduction (like your old mux):
    output                       tdc_fifo_empty_mux,   // "no selectable lane has data"
    output reg [TDC_DATA_WIDTH-1:0] tdc_fifo_data_mux,  // selected FWFT head word

    // NEW: global per-bank empties (locked-aware), for event_builder_byhit timers
    output                       fifoA_empty_mux,
    output                       fifoB_empty_mux
);

    // ---- local helper: ceil(log2(N)) ----
    function integer clog2;
        input integer value;
        integer v;
        begin
            v = value - 1;
            clog2 = 0;
            while (v > 0) begin
                clog2 = clog2 + 1;
                v = v >> 1;
            end
        end
    endfunction

    // NEW: guard against TDC_COUNT==1 so RR_W never becomes 0
    // (clog2(1)=0 would create zero-width rr_ptr which is illegal)
    localparam RR_W = (TDC_COUNT <= 2) ? 1 : clog2(TDC_COUNT);

    // -------------------------------------------------------------------------
    // Availability / summary signals
    // -------------------------------------------------------------------------
    wire [TDC_COUNT-1:0] avail;
    assign avail = locked & ~tdc_fifo_empty;

    // "no selectable lane has data in the selected read-bank view"
    assign tdc_fifo_empty_mux = ~(|avail);

    // NEW: locked-aware reduction of per-bank empties across lanes
    // If a lane is unlocked, treat it as empty (it doesn't participate in "any non-empty").
    //
    // These are GLOBAL bank-empty flags:
    // - fifoA_empty_mux == 1 means ALL locked lanes have fifoA_empty==1 (i.e. bank A empty globally)
    // - fifoA_empty_mux == 0 means SOME locked lane has fifoA_empty==0 (i.e. bank A has data somewhere)
    //
    // This form is equivalent to:
    //   fifoA_empty_mux = &((~locked) | fifoA_empty);
    // but is easier to read as "any_nonempty" then invert.
    wire fifoA_any_nonempty = |(locked & ~fifoA_empty);
    wire fifoB_any_nonempty = |(locked & ~fifoB_empty);

    assign fifoA_empty_mux = ~fifoA_any_nonempty;
    assign fifoB_empty_mux = ~fifoB_any_nonempty;

    // -------------------------------------------------------------------------
    // RR pointer + selection
    // -------------------------------------------------------------------------
    reg  [RR_W-1:0] rr_ptr;

    reg             sel_found; // == 1 when at least one avail[] is true
    reg  [RR_W-1:0] sel_idx;   // selected FIFO index

    integer k;
    integer idx;

    // Combinational RR search starting at rr_ptr
    always @(*) begin
        sel_found = 1'b0;
        sel_idx   = rr_ptr;

        for (k = 0; k < TDC_COUNT; k = k + 1) begin
            idx = rr_ptr + k;
            if (idx >= TDC_COUNT)
                idx = idx - TDC_COUNT;

            if (!sel_found && avail[idx]) begin
                sel_found = 1'b1;
                sel_idx   = idx[RR_W-1:0];
            end
        end
    end

    // -------------------------------------------------------------------------
    // Unpack packed bus -> per-lane word array (constant part-selects only)
    // -------------------------------------------------------------------------
    wire [TDC_DATA_WIDTH-1:0] tdc_word [0:TDC_COUNT-1];

    genvar g;
    generate
        for (g = 0; g < TDC_COUNT; g = g + 1) begin : GEN_TDC_WORD
            assign tdc_word[g] =
                tdc_fifo_data[(g*TDC_DATA_WIDTH) + TDC_DATA_WIDTH - 1 : (g*TDC_DATA_WIDTH)];
        end
    endgenerate


        // -------------------------------------------------------------------------
    // Immediate FWFT peek mux + conditional pop strobes
    // -------------------------------------------------------------------------
    always @(*) begin
        // defaults
        tdc_fifo_read     = {TDC_COUNT{1'b0}};
        tdc_fifo_data_mux = {TDC_DATA_WIDTH{1'b0}};

        // Always present selected head word when something is available
        if (sel_found) begin
            tdc_fifo_data_mux = tdc_word[sel_idx]; // mux via array indexing (synth OK)
        end

        // Pop only when downstream requests AND we actually have a selection
        if (tdc_fifo_read_mux && sel_found) begin
            tdc_fifo_read[sel_idx] = 1'b1; // variable bit-select is OK
        end
    end


    // -------------------------------------------------------------------------
    // Advance rr_ptr only after a successful pop
    // -------------------------------------------------------------------------
    always @(posedge clk) begin
        if (rst) begin
            rr_ptr <= {RR_W{1'b0}};
        end else if (tdc_fifo_read_mux && sel_found) begin
            if (sel_idx == (TDC_COUNT-1))
                rr_ptr <= {RR_W{1'b0}};
            else
                rr_ptr <= sel_idx + 1'b1;
        end
    end

endmodule
