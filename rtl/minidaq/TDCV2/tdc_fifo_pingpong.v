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
// File   : tdc_fifo_pingpong.v
// Create : 2026-01-13 12:56:29
// Revise : 2026-01-29 17:42:43
// Editor : sublime text4, tab size (4)
// Description:
//
// -----------------------------------------------------------------------------
//   Mode-aware FIFO wrapper shared by external-trigger and triggerless acquisition.
//
//   External-trigger mode uses fifoA as a normal single FIFO.
//   Triggerless mode uses fifoA/fifoB as ping-pong banks:
//   - TDC writes into triggerless_wr_bank_sel
//   - Event builder reads from triggerless_rd_bank_sel
//
//   This supports concurrent operation in triggerless mode: while writing to one
//   bank, the event builder can read the other. Both banks are reset on every
//   acquisition-mode change so no FIFO contents survive the switch.
//
//   FIFO IP: common clock, Native, FWFT
//


module tdc_fifo_pingpong #(
    parameter DATA_WIDTH = 40
)(
    input                       clk_40,
    input                       rst_40,

    input                       acquisition_mode,          // 0=>external-trigger, 1=>triggerless
    input                       triggerless_run_enable,
    input                       triggerless_clr_hit_fifos,

    // External-trigger FIFO interface. Uses fifoA only.
    input   [DATA_WIDTH-1:0]    triggered_din,
    input                       triggered_wr_en,
    output                      triggered_full,
    input                       triggered_rd_en,
    output  [DATA_WIDTH-1:0]    triggered_dout,
    output                      triggered_empty,

    // Triggerless bank controls.
    input                       triggerless_wr_bank_sel,   // 0=>fifoA, 1=>fifoB
    input                       triggerless_rd_bank_sel,   // 0=>fifoA, 1=>fifoB

    output                      fifoA_empty,
    output                      fifoB_empty,

    // Triggerless write-side interface.
    input   [DATA_WIDTH-1:0]    triggerless_din,
    input                       triggerless_wr_en,
    output                      triggerless_full,          // full of the selected write bank

    // Triggerless read-side interface. Looks like one FIFO selected by rd bank.
    input                       triggerless_rd_en,
    output  [DATA_WIDTH-1:0]    triggerless_dout,
    output                      triggerless_empty,



    // Optional overflow flags (sticky)
    output reg                  overflowA,
    output reg                  overflowB,
    output                      overflow_word
);
    reg acquisition_mode_d;

    wire mode_switch_rst = acquisition_mode ^ acquisition_mode_d;
    wire triggerless_active = acquisition_mode & triggerless_run_enable;
    wire triggerless_clear  = triggerless_active & triggerless_clr_hit_fifos;

    wire fifoA_srst = rst_40 | mode_switch_rst |
                      (acquisition_mode & (~triggerless_run_enable | triggerless_clr_hit_fifos));
    wire fifoB_srst = rst_40 | mode_switch_rst |
                      ~acquisition_mode |
                      ~triggerless_run_enable |
                      triggerless_clr_hit_fifos;

    wire [DATA_WIDTH-1:0] fifoA_din = acquisition_mode ? triggerless_din : triggered_din;
    wire [DATA_WIDTH-1:0] fifoB_din = triggerless_din;

    // ----------------------------
    // Write enables
    // ----------------------------
    wire triggered_wr_en_A   = triggered_wr_en & ~acquisition_mode;
    wire triggerless_wr_en_A = triggerless_wr_en & triggerless_active &
                               ~triggerless_clear & ~triggerless_wr_bank_sel;
    wire triggerless_wr_en_B = triggerless_wr_en & triggerless_active &
                               ~triggerless_clear &  triggerless_wr_bank_sel;
    wire wr_en_A = acquisition_mode ? triggerless_wr_en_A : triggered_wr_en_A;
    wire wr_en_B = triggerless_wr_en_B;

    // ----------------------------
    // Read enables
    // ----------------------------
    wire triggered_rd_en_A   = triggered_rd_en & ~acquisition_mode;
    wire triggerless_rd_en_A = triggerless_rd_en & triggerless_active &
                               ~triggerless_clear & ~triggerless_rd_bank_sel;
    wire triggerless_rd_en_B = triggerless_rd_en & triggerless_active &
                               ~triggerless_clear &  triggerless_rd_bank_sel;
    wire rd_en_A = acquisition_mode ? triggerless_rd_en_A : triggered_rd_en_A;
    wire rd_en_B = triggerless_rd_en_B;

    // FIFO A signals
    wire [DATA_WIDTH-1:0] fifoA_dout;
    wire fifoA_full;
    wire fifoA_empty_int;
    wire fifoA_wr_rst_busy;
    wire fifoA_rd_rst_busy;
    wire fifoA_busy = fifoA_wr_rst_busy | fifoA_rd_rst_busy;

    // FIFO B signals
    wire [DATA_WIDTH-1:0] fifoB_dout;
    wire fifoB_full;
    wire fifoB_empty_int;
    wire fifoB_wr_rst_busy;
    wire fifoB_rd_rst_busy;
    wire fifoB_busy = fifoB_wr_rst_busy | fifoB_rd_rst_busy;

    // A pulse per lost write, not a rising edge of the sticky flags. Exclude
    // reset/busy cycles when no FIFO write is actually attempted.
    assign overflow_word =
        (triggerless_wr_en_A && !fifoA_srst && !fifoA_busy && fifoA_full) ||
        (triggerless_wr_en_B && !fifoB_srst && !fifoB_busy && fifoB_full);

    assign fifoA_empty = fifoA_empty_int | fifoA_busy;
    assign fifoB_empty = fifoB_empty_int | fifoB_busy;

    always @(posedge clk_40) begin
        if (rst_40 | mode_switch_rst)
            acquisition_mode_d <= acquisition_mode;
    end



    // ----------------------------
    // FIFO A
    // ----------------------------
    TDC_data_fifo_40b fifoA (
        .clk(clk_40),
        .srst(fifoA_srst),
        .din(fifoA_din),
        .wr_en(wr_en_A & ~fifoA_busy),
        .rd_en(rd_en_A & ~fifoA_busy),
        .dout(fifoA_dout),
        .full(fifoA_full),
        .empty(fifoA_empty_int),
        .wr_rst_busy(fifoA_wr_rst_busy),
        .rd_rst_busy(fifoA_rd_rst_busy)
    );

    // ----------------------------
    // FIFO B
    // ----------------------------
    TDC_data_fifo_40b fifoB (
        .clk(clk_40),
        .srst(fifoB_srst),
        .din(fifoB_din),
        .wr_en(wr_en_B & ~fifoB_busy),
        .rd_en(rd_en_B & ~fifoB_busy),
        .dout(fifoB_dout),
        .full(fifoB_full),
        .empty(fifoB_empty_int),
        .wr_rst_busy(fifoB_wr_rst_busy),
        .rd_rst_busy(fifoB_rd_rst_busy)
    );

    // ----------------------------
    // Present mode-specific FIFO interfaces
    // ----------------------------
    assign triggered_dout  = fifoA_dout;
    assign triggered_empty = fifoA_empty_int | fifoA_busy;
    assign triggered_full  = fifoA_full | fifoA_busy;

    assign triggerless_dout  = (triggerless_rd_bank_sel == 1'b0) ? fifoA_dout : fifoB_dout;
    assign triggerless_empty = (triggerless_rd_bank_sel == 1'b0) ?
                               (fifoA_empty_int | fifoA_busy) :
                               (fifoB_empty_int | fifoB_busy);

    // Report full of the selected write bank (useful for overflow monitoring)
    assign triggerless_full  = (triggerless_wr_bank_sel == 1'b0) ?
                               (fifoA_full | fifoA_busy) :
                               (fifoB_full | fifoB_busy);

    // ----------------------------
    // Triggerless overflow monitoring (sticky)
    // ----------------------------
    always @(posedge clk_40) begin
        if (rst_40 | mode_switch_rst | ~acquisition_mode |
            ~triggerless_run_enable | triggerless_clr_hit_fifos) begin
            overflowA <= 1'b0;
            overflowB <= 1'b0;
        end else begin
            if (triggerless_wr_en_A && fifoA_full) overflowA <= 1'b1;
            if (triggerless_wr_en_B && fifoB_full) overflowB <= 1'b1;
        end
    end

endmodule
