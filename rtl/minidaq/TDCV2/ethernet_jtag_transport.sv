// Ethernet transport for streamed GBT-SCA JTAG programming and IDCODE reads.
//
// Hierarchy and clock crossings:
//
//   Parent: ethernet_sca_jtag_top.transport
//   Children:
//     - xpm_fifo_async data_fifo        128-bit payload, RX -> control
//     - xpm_fifo_async descriptor_fifo  chunk metadata, RX -> control
//     - xpm_fifo_async result_fifo      completion data, control -> RX/TX
//     - XPM reset/pulse synchronizers   reset and abort control
//
//   shared TEMAC RX fork, 125 MHz
//                    |
//                    v
//       ethernet_jtag_transport parser/CRC/session logic
//          |                                      ^
//          | data + descriptor CDC                | result CDC
//          v                                      |
//       ethernet_jtag_programmer, 40 MHz ----------+
//          |
//          +-- immediate RX_ACK descriptor --------+
//          +-- completed SCA/IDCODE result --------+--> program ACK serializer
//
// This module owns protocol validation, CRC/session state, duplicate replay,
// and all programming CDC storage. It does not issue SCA commands itself.
//
// Module data-flow summary:
//
//   1. The TEMAC presents FCS-checked Ethernet bytes at 125 MHz.
//   2. This module parses the raw-Ethernet/programming header and validates the
//      destination, target, session, sequence, offset and chunk length.
//   3. Payload bytes update the chunk and rolling CRC32 calculations while
//      groups of sixteen bytes are packed into 128-bit data-FIFO words.
//   4. At TLAST, a bad frame is NACKed and its speculative FIFO data is
//      flushed.  A good frame writes one descriptor and produces RX_ACK.
//   5. Data words and their descriptor cross asynchronously from the 125 MHz
//      RX domain into the 40 MHz SCA-control domain.
//   6. ethernet_jtag_programmer consumes exactly the descriptor's word count
//      and returns one 160-bit success/failure result.
//   7. The result crosses back to 125 MHz.  Success commits the next sequence
//      and byte offset; failure ends the session and flushes remaining data.
//   8. This module emits an SCA/IDCODE ACK or NACK response descriptor, which
//      ethernet_program_ack_tx serializes into a TEMAC TX frame.
//
// Only one chunk may be outstanding.  ABORT can interrupt it, a duplicate
// in-flight chunk replays RX_ACK/BUSY, and a duplicate completed chunk replays
// the cached SCA result without executing its JTAG data again.
//
// RX wire format (all multi-byte header fields are big endian):
//   Ethernet header:
//     0..5   destination MAC
//     6..11  source MAC
//     12..13 EtherType (default 0x88B5)
//   32-byte programming header:
//     14..17 magic ("MDJ1")
//     18     protocol version
//     19     message type (1=data, 2=abort, 3=IDCODE read)
//     20     flags: bit 0 FIRST, bit 1 LAST
//     21     target CSM/downlink
//     22     target SCA index
//     23     reserved
//     24..25 valid chunk byte count
//     26..29 session ID
//     30..33 sequence number
//     34..37 bit-file byte offset
//     38..41 complete bit-file byte count
//     42..45 expected complete-file CRC32
//   46..    bit-file data
//   then    chunk CRC32 over valid bit-file bytes
//
// IDCODE_READ uses the same header with flags, length, offsets, total length,
// and file CRC set to zero.  The frame is padded to the 60-byte Ethernet
// minimum; no application payload or application CRC is present.
//
// A normal data frame contains 1408 bytes, exactly 88 128-bit words.  The
// final frame may be shorter.  The TEMAC has already checked Ethernet FCS.
//
// The payload is placed into the data FIFO while its frame is arriving, but it
// cannot be consumed because the descriptor is committed only after TLAST and
// all checks pass.  A rejected frame resets both RX-to-control FIFOs, discarding
// its uncommitted data.
//
// RX_ACK means that a chunk passed transport checks and was committed to the
// FIFOs.  SCA_ACK means the programmer finished consuming it.

`timescale 1ns / 1ps

module ethernet_jtag_transport #(
    parameter logic [15:0] PROGRAM_ETHERTYPE = 16'h88B5,
    parameter logic [47:0] FPGA_MAC          = 48'h020000C70501,
    parameter integer MAX_CHUNK_BYTES        = 1408,
    parameter integer DATA_FIFO_DEPTH        = 128
) (
    // Byte-wide TEMAC RX AXI stream, normally 125 MHz.  TEMAC has already
    // removed and checked the physical Ethernet FCS.
    input  wire         rx_clk,
    input  wire         rx_resetn,
    input  wire [7:0]   rx_tdata,
    input  wire         rx_tvalid,
    output wire         rx_tready,
    input  wire         rx_tlast,

    // MiniDAQ/SCA command domain, normally 40 MHz.
    input  wire         control_clk,
    input  wire         control_reset,

    // Validated bit-file words crossing from rx_clk to control_clk.
    output wire [127:0] chunk_data,
    output wire         chunk_data_valid,
    input  wire         chunk_data_ready,

    // Atomic metadata for the data FIFO chunk.  This appears only after the
    // complete input frame and its CRCs have passed.
    output wire [191:0] chunk_descriptor,
    output wire         chunk_descriptor_valid,
    input  wire         chunk_descriptor_ready,

    // Synchronized one-cycle abort request in the control clock domain.
    output wire         abort_control,

    // Programmer result crossing back from control_clk to rx_clk.
    input  wire [159:0] programmer_result,
    input  wire         programmer_result_valid,
    output wire         programmer_result_ready,

    // ACK/NACK metadata consumed by ethernet_program_ack_tx in the 125 MHz
    // Ethernet user-clock domain.
    output reg  [255:0] response_descriptor = 256'b0,
    output reg          response_valid = 1'b0,
    input  wire         response_ready,

    // Session state is also used by the top level to stop starting new hit
    // frames while bit-file programming owns the Ethernet/SCA path.
    output reg          programming_session_active = 1'b0,
    output wire         data_fifo_full,
    output wire         data_fifo_overflow,
    output wire         descriptor_fifo_full,
    output wire         result_fifo_full
);

    localparam logic [31:0] PROTOCOL_MAGIC = 32'h4D444A31; // "MDJ1"
    localparam logic [7:0]  PROTOCOL_VERSION = 8'h01;

    localparam logic [7:0] MSG_DATA       = 8'h01;
    localparam logic [7:0] MSG_ABORT      = 8'h02;
    localparam logic [7:0] MSG_IDCODE_READ= 8'h03;
    localparam logic [7:0] MSG_RX_ACK     = 8'h81;
    localparam logic [7:0] MSG_SCA_ACK    = 8'h82;
    localparam logic [7:0] MSG_IDCODE_ACK = 8'h83;
    localparam logic [7:0] MSG_RX_NACK    = 8'hE1;
    localparam logic [7:0] MSG_SCA_NACK   = 8'hE2;
    localparam logic [7:0] MSG_IDCODE_NACK= 8'hE3;

    localparam logic [7:0] ERR_NONE        = 8'h00;
    localparam logic [7:0] ERR_HEADER      = 8'h01;
    localparam logic [7:0] ERR_SEQUENCE    = 8'h02;
    localparam logic [7:0] ERR_BUSY        = 8'h03;
    localparam logic [7:0] ERR_CHUNK_CRC   = 8'h04;
    localparam logic [7:0] ERR_FILE_CRC    = 8'h05;
    localparam logic [7:0] ERR_FIFO        = 8'h06;
    localparam logic [7:0] ERR_ABORTED     = 8'h07;

    localparam logic [2:0] FRAME_REJECT       = 3'd0;
    localparam logic [2:0] FRAME_NEW          = 3'd1;
    localparam logic [2:0] FRAME_DUP_INFLIGHT = 3'd2;
    localparam logic [2:0] FRAME_DUP_DONE     = 3'd3;
    localparam logic [2:0] FRAME_ABORT        = 3'd4;
    localparam logic [2:0] FRAME_IDCODE       = 3'd5;
    localparam logic [2:0] FRAME_IGNORE       = 3'd6;

    // Reflected CRC32 used by Ethernet-style/zlib CRC code:
    // polynomial 0xEDB88320, initial state 0xFFFFFFFF and final complement.
    // Only bit-file payload bytes are included; protocol headers are excluded.
    function automatic [31:0] crc32_next_byte(
        input [31:0] crc_in,
        input [7:0]  data_in
    );
        integer bit_index;
        reg [31:0] crc_work;
        begin
            crc_work = crc_in ^ {24'b0, data_in};
            for (bit_index = 0; bit_index < 8; bit_index = bit_index + 1)
                crc_work = crc_work[0]
                         ? ((crc_work >> 1) ^ 32'hEDB88320)
                         :  (crc_work >> 1);
            crc32_next_byte = crc_work;
        end
    endfunction

    // Ceiling(byte_count / 16), used to tell the programmer how many FIFO
    // words belong to the current descriptor.
    function automatic [7:0] chunk_word_count(input [15:0] byte_count);
        begin
            chunk_word_count = (byte_count + 16'd15) >> 4;
        end
    endfunction

    // Synchronize the 40 MHz control reset into the RX clock domain.  The
    // assertion remains asynchronous, while release is synchronized.
    wire control_reset_rx;
    xpm_cdc_async_rst #(
        .DEST_SYNC_FF    (4),
        .INIT_SYNC_FF    (0),
        .RST_ACTIVE_HIGH (1)
    ) control_reset_to_rx (
        .src_arst  (control_reset),
        .dest_clk  (rx_clk),
        .dest_arst (control_reset_rx)
    );

    // The result FIFO's write side is in the control domain.  Stretch either
    // reset source through an async-assert/sync-release reset synchronizer so
    // XPM sees reset asserted for at least four control-clock cycles.
    wire result_fifo_reset;
    xpm_cdc_async_rst #(
        .DEST_SYNC_FF    (4),
        .INIT_SYNC_FF    (0),
        .RST_ACTIVE_HIGH (1)
    ) result_reset_to_control (
        .src_arst  (control_reset | ~rx_resetn),
        .dest_clk  (control_clk),
        .dest_arst (result_fifo_reset)
    );

    reg [4:0] fifo_flush_count = 5'd0;
    reg finalize_pending = 1'b0;
    reg finalize_crc_good = 1'b0;
    reg [2:0] finalize_mode = FRAME_REJECT;
    reg [7:0] finalize_error = ERR_HEADER;

    // The data and descriptor FIFOs contain only one uncommitted/in-flight
    // chunk.  Holding their reset for sixteen RX clocks safely discards a bad,
    // aborted or partially consumed chunk in both clock domains.
    wire fifo_flush = |fifo_flush_count;
    wire fifo_reset = ~rx_resetn | control_reset_rx | fifo_flush;

    // FIFO 1: programming payload, rx_clk -> control_clk.
    //
    // Width conversion is performed explicitly in the RX domain before this
    // FIFO; the XPM write and read widths are both 128 bits:
    //
    //   TEMAC 8 bits @ 125 MHz
    //       -> collect 16 accepted bytes in payload_shift
    //       -> one 128-bit FIFO write @ 125 MHz
    //       -> xpm_fifo_async
    //       -> chunk_data[127:0] @ 40 MHz
    //
    // For payload bytes B0..B15, the packed word is:
    //
    //   [127:120] B0, [119:112] B1, ... [15:8] B14, [7:0] B15
    //
    // This is the only FIFO that contains bit-file bytes.  With the default
    // depth it stores 128 words = 2048 bytes.  A normal 1408-byte chunk
    // occupies 88 words, leaving 40 words (640 bytes) of margin.
    //
    // Payload is written while the Ethernet frame is arriving, before its
    // trailing application CRC is known.  It remains uncommitted because the
    // programmer will not read this FIFO until FIFO 2 supplies a descriptor.
    // Any frame rejection asserts fifo_reset and discards the speculative data.
    //
    // At full Ethernet rate the packer writes 125 MHz / 16 = 7.8125 million
    // words/s, preserving the 125 MB/s byte rate.  The 40 MHz read port can
    // present one 128-bit word per clock, or 640 MB/s.  Actual consumption is
    // much slower because every word requires several SCA commands.  Block RAM
    // avoids placing this 16-Kbit payload store in the congested CLB fabric.
    //
    // XPM stores data in dual-port memory and crosses Gray-coded read/write
    // pointers between clocks to derive full and empty.  It does not pass the
    // 128 data bits through independent bit synchronizers.
    reg  [127:0] data_fifo_din = 128'b0;
    reg          data_fifo_wr_en = 1'b0;
    wire         data_fifo_empty;
    wire         data_fifo_wr_rst_busy;
    wire         data_fifo_rd_rst_busy;

    xpm_fifo_async #(
        .CDC_SYNC_STAGES     (2),
        .DOUT_RESET_VALUE    ("0"),
        .ECC_MODE            ("no_ecc"),
        .FIFO_MEMORY_TYPE    ("block"),
        .FIFO_READ_LATENCY   (0),
        .FIFO_WRITE_DEPTH    (DATA_FIFO_DEPTH),
        .FULL_RESET_VALUE    (0),
        .PROG_EMPTY_THRESH   (4),
        .PROG_FULL_THRESH    (DATA_FIFO_DEPTH - 4),
        .RD_DATA_COUNT_WIDTH (1),
        .READ_DATA_WIDTH     (128),
        .READ_MODE           ("fwft"),
        .RELATED_CLOCKS      (0),
        .SIM_ASSERT_CHK      (1),
        .USE_ADV_FEATURES    ("0000"),
        .WAKEUP_TIME         (0),
        .WRITE_DATA_WIDTH    (128),
        .WR_DATA_COUNT_WIDTH (1)
    ) programming_data_fifo (
        .almost_empty  (),
        .almost_full   (),
        .data_valid    (),
        .dbiterr       (),
        .din           (data_fifo_din),
        .dout          (chunk_data),
        .empty         (data_fifo_empty),
        .full          (data_fifo_full),
        .injectdbiterr (1'b0),
        .injectsbiterr (1'b0),
        .overflow      (data_fifo_overflow),
        .prog_empty    (),
        .prog_full     (),
        .rd_clk        (control_clk),
        .rd_data_count (),
        .rd_en         (chunk_data_valid & chunk_data_ready),
        .rd_rst_busy   (data_fifo_rd_rst_busy),
        .rst           (fifo_reset),
        .sbiterr       (),
        .sleep         (1'b0),
        .underflow     (),
        .wr_ack        (),
        .wr_clk        (rx_clk),
        .wr_data_count (),
        .wr_en         (data_fifo_wr_en),
        .wr_rst_busy   (data_fifo_wr_rst_busy)
    );

    // First-word fall-through makes chunk_data show the oldest word whenever
    // the FIFO is nonempty.  It is removed only on the control-domain
    // chunk_data_valid && chunk_data_ready handshake.
    assign chunk_data_valid = ~data_fifo_empty & ~data_fifo_rd_rst_busy;

    // FIFO 2: validated chunk descriptor, rx_clk -> control_clk.
    //
    // One 192-bit descriptor atomically describes and commits all data words
    // belonging to one Ethernet chunk:
    //
    //   [191:160] session ID
    //   [159:128] chunk sequence
    //   [127:96]  bit-file byte offset
    //   [95:64]   complete bit-file length
    //   [63:32]   rolling CRC32 after this chunk
    //   [31:16]   valid bytes in this chunk
    //   [15:8]    number of 128-bit data-FIFO words
    //   [7]       FIRST
    //   [6]       LAST
    //   [5:4]     target CSM/downlink
    //   [3:2]     target SCA
    //   [1:0]     operation: 0=program chunk, 1=standalone IDCODE read
    //
    // The descriptor is written only after the complete frame passes header,
    // sequence, length, FIFO and CRC checks.  The programmer reads a descriptor
    // first, then consumes exactly its [15:8] data words from FIFO 1.  Therefore
    // speculative payload can never be executed before it is committed.
    //
    // Stop-and-wait permits only one active chunk; depth 16 provides CDC and
    // handshake elasticity rather than permission to queue 16 host chunks.
    // The FIFO is shallow and 192 bits wide, so distributed RAM uses resources
    // more efficiently than several mostly-empty parallel block RAMs.
    reg  [191:0] descriptor_fifo_din = 192'b0;
    reg          descriptor_fifo_wr_en = 1'b0;
    wire         descriptor_fifo_empty;
    wire         descriptor_fifo_wr_rst_busy;
    wire         descriptor_fifo_rd_rst_busy;

    xpm_fifo_async #(
        .CDC_SYNC_STAGES     (2),
        .DOUT_RESET_VALUE    ("0"),
        .ECC_MODE            ("no_ecc"),
        .FIFO_MEMORY_TYPE    ("distributed"),
        .FIFO_READ_LATENCY   (0),
        .FIFO_WRITE_DEPTH    (16),
        .FULL_RESET_VALUE    (0),
        .PROG_EMPTY_THRESH   (2),
        .PROG_FULL_THRESH    (14),
        .RD_DATA_COUNT_WIDTH (1),
        .READ_DATA_WIDTH     (192),
        .READ_MODE           ("fwft"),
        .RELATED_CLOCKS      (0),
        .SIM_ASSERT_CHK      (1),
        .USE_ADV_FEATURES    ("0000"),
        .WAKEUP_TIME         (0),
        .WRITE_DATA_WIDTH    (192),
        .WR_DATA_COUNT_WIDTH (1)
    ) programming_descriptor_fifo (
        .almost_empty  (),
        .almost_full   (),
        .data_valid    (),
        .dbiterr       (),
        .din           (descriptor_fifo_din),
        .dout          (chunk_descriptor),
        .empty         (descriptor_fifo_empty),
        .full          (descriptor_fifo_full),
        .injectdbiterr (1'b0),
        .injectsbiterr (1'b0),
        .overflow      (),
        .prog_empty    (),
        .prog_full     (),
        .rd_clk        (control_clk),
        .rd_data_count (),
        .rd_en         (chunk_descriptor_valid & chunk_descriptor_ready),
        .rd_rst_busy   (descriptor_fifo_rd_rst_busy),
        .rst           (fifo_reset),
        .sbiterr       (),
        .sleep         (1'b0),
        .underflow     (),
        .wr_ack        (),
        .wr_clk        (rx_clk),
        .wr_data_count (),
        .wr_en         (descriptor_fifo_wr_en),
        .wr_rst_busy   (descriptor_fifo_wr_rst_busy)
    );

    assign chunk_descriptor_valid =
        ~descriptor_fifo_empty & ~descriptor_fifo_rd_rst_busy;

    // FIFO 3: programmer completion result, control_clk -> rx_clk.
    //
    // This FIFO runs in the opposite direction from FIFOs 1 and 2.  After the
    // SCA finishes or fails a chunk, the 40 MHz programmer writes:
    //
    //   [159:128] session ID
    //   [127:96]  chunk sequence
    //   [95:64]   completed byte offset
    //   [63:32]   result data: rolling CRC32 or captured FPGA IDCODE
    //   [31:24]   zero on success, nonzero on failure
    //   [23:16]   failure class
    //   [15:8]    failed SCA command
    //   [7:0]     SCA error, status detail or retry count
    //
    // The programmer holds result_valid until this FIFO accepts the complete
    // record, keeping all fields coherent across the CDC.  The RX/session side
    // converts a successful result into SCA_ACK and advances sequence/offset.
    // A failed result becomes SCA_NACK, leaves sequence/offset uncommitted and
    // flushes FIFOs 1 and 2.
    //
    // Like the descriptor FIFO, this FIFO is only 16 entries deep and very
    // wide, so distributed RAM is preferable to several underused BRAMs.
    wire [159:0] result_fifo_dout;
    wire         result_fifo_empty;
    wire         result_fifo_wr_rst_busy;
    wire         result_fifo_rd_rst_busy;
    wire         result_fifo_pop;

    xpm_fifo_async #(
        .CDC_SYNC_STAGES     (2),
        .DOUT_RESET_VALUE    ("0"),
        .ECC_MODE            ("no_ecc"),
        .FIFO_MEMORY_TYPE    ("distributed"),
        .FIFO_READ_LATENCY   (0),
        .FIFO_WRITE_DEPTH    (16),
        .FULL_RESET_VALUE    (0),
        .PROG_EMPTY_THRESH   (2),
        .PROG_FULL_THRESH    (14),
        .RD_DATA_COUNT_WIDTH (1),
        .READ_DATA_WIDTH     (160),
        .READ_MODE           ("fwft"),
        .RELATED_CLOCKS      (0),
        .SIM_ASSERT_CHK      (1),
        .USE_ADV_FEATURES    ("0000"),
        .WAKEUP_TIME         (0),
        .WRITE_DATA_WIDTH    (160),
        .WR_DATA_COUNT_WIDTH (1)
    ) programming_result_fifo (
        .almost_empty  (),
        .almost_full   (),
        .data_valid    (),
        .dbiterr       (),
        .din           (programmer_result),
        .dout          (result_fifo_dout),
        .empty         (result_fifo_empty),
        .full          (result_fifo_full),
        .injectdbiterr (1'b0),
        .injectsbiterr (1'b0),
        .overflow      (),
        .prog_empty    (),
        .prog_full     (),
        .rd_clk        (rx_clk),
        .rd_data_count (),
        .rd_en         (result_fifo_pop),
        .rd_rst_busy   (result_fifo_rd_rst_busy),
        .rst           (result_fifo_reset),
        .sbiterr       (),
        .sleep         (1'b0),
        .underflow     (),
        .wr_ack        (),
        .wr_clk        (control_clk),
        .wr_data_count (),
        .wr_en         (programmer_result_valid
                       & programmer_result_ready),
        .wr_rst_busy   (result_fifo_wr_rst_busy)
    );

    assign programmer_result_ready =
        ~result_fifo_full & ~result_fifo_wr_rst_busy;

    // Do not consume a programmer result while the single response slot is
    // occupied or while an RX frame is waiting to be finalized.
    assign result_fifo_pop =
        ~result_fifo_empty & ~result_fifo_rd_rst_busy
        & ~response_valid & ~finalize_pending;

    // ABORT is the only command allowed to interrupt a committed chunk.
    reg abort_rx_pulse = 1'b0;
    xpm_cdc_pulse #(
        .DEST_SYNC_FF   (4),
        .INIT_SYNC_FF   (0),
        .REG_OUTPUT     (1),
        .RST_USED       (1),
        .SIM_ASSERT_CHK (1)
    ) abort_to_control (
        .src_clk   (rx_clk),
        .src_pulse (abort_rx_pulse),
        .src_rst   (~rx_resetn),
        .dest_clk  (control_clk),
        .dest_pulse(abort_control),
        .dest_rst  (control_reset)
    );

    // Fields assembled from the currently arriving Ethernet frame.
    reg [15:0] frame_index = 16'd0;
    reg [47:0] frame_destination_mac = 48'b0;
    reg [47:0] frame_source_mac = 48'b0;
    reg [15:0] frame_ethertype = 16'b0;
    reg [31:0] frame_magic = 32'b0;
    reg [7:0]  frame_version = 8'b0;
    reg [7:0]  frame_message = 8'b0;
    reg [7:0]  frame_flags = 8'b0;
    reg [7:0]  frame_target_csm = 8'b0;
    reg [7:0]  frame_target_sca = 8'b0;
    reg [15:0] frame_chunk_length = 16'b0;
    reg [31:0] frame_session = 32'b0;
    reg [31:0] frame_sequence = 32'b0;
    reg [31:0] frame_file_offset = 32'b0;
    reg [31:0] frame_total_length = 32'b0;
    reg [31:0] frame_expected_file_crc = 32'b0;

    // Per-frame parser state.  FRAME_NEW is the only mode that writes payload
    // bytes into the data FIFO.  Other modes still consume through TLAST so a
    // complete ACK/NACK can be generated without losing frame alignment.
    reg [2:0] frame_mode = FRAME_REJECT;
    reg [7:0] frame_reject_error = ERR_HEADER;
    reg [15:0] payload_byte_index = 16'b0;
    reg [127:0] payload_shift = 128'b0;
    reg [31:0] chunk_crc_state = 32'hFFFFFFFF;
    reg [31:0] rolling_candidate_state = 32'hFFFFFFFF;
    reg [31:0] received_chunk_crc = 32'b0;
    reg frame_crc_seen = 1'b0;
    reg frame_crc_good = 1'b0;
    reg frame_fifo_error = 1'b0;

    // Committed programming-session identity and expected next-chunk position.
    // Continuation chunks must match every one of these invariants.
    reg [31:0] active_session = 32'b0;
    reg [47:0] active_source_mac = 48'b0;
    reg [7:0] active_target_csm = 8'b0;
    reg [7:0] active_target_sca = 8'b0;
    reg [31:0] expected_sequence = 32'b0;
    reg [31:0] expected_file_offset = 32'b0;
    reg [31:0] active_total_length = 32'b0;
    reg [31:0] active_expected_file_crc = 32'b0;
    reg [31:0] rolling_file_crc_state = 32'hFFFFFFFF;

    // Identity of the one chunk currently owned by the 40 MHz programmer.
    reg chunk_inflight = 1'b0;
    reg inflight_last = 1'b0;
    reg [31:0] inflight_sequence = 32'b0;
    reg [31:0] inflight_rolling_crc = 32'b0;
    reg [7:0] inflight_message = MSG_DATA;

    // Cached completed result.  If an ACK is lost, retransmitting the same
    // session/sequence returns this result without shifting JTAG data again.
    reg last_result_valid = 1'b0;
    reg [31:0] last_result_session = 32'b0;
    reg [31:0] last_result_sequence = 32'b0;
    reg [31:0] last_result_offset = 32'b0;
    reg [31:0] last_result_crc = 32'b0;
    reg [7:0]  last_result_message = MSG_SCA_ACK;
    reg [7:0]  last_result_status = 8'b0;
    reg [7:0]  last_result_command = 8'b0;
    reg [7:0]  last_result_error = 8'b0;
    reg [7:0]  last_result_request_message = MSG_DATA;

    // Checks common to DATA, ABORT, and IDCODE headers.  The hardware exposes
    // two CSM/downlink targets with four SCAs on each.
    wire header_common_valid =
        ((frame_destination_mac == FPGA_MAC)
         || (frame_destination_mac == 48'hFFFFFFFFFFFF))
        && (frame_ethertype == PROGRAM_ETHERTYPE)
        && (frame_magic == PROTOCOL_MAGIC)
        && (frame_version == PROTOCOL_VERSION)
        && (frame_target_csm < 8'd2)
        && (frame_target_sca < 8'd4);

    // Every non-final frame must contain exactly MAX_CHUNK_BYTES.  Only LAST
    // may contain a shorter, nonzero payload.
    wire header_chunk_shape_valid =
        frame_flags[1]
        ? ((frame_chunk_length != 16'd0)
           && (frame_chunk_length <= MAX_CHUNK_BYTES))
        :  (frame_chunk_length == MAX_CHUNK_BYTES);

    // FIRST starts/restarts a file and must begin at sequence and byte offset
    // zero.  The full-file size must at least contain this first chunk.
    wire header_new_first =
        header_common_valid
        && (frame_message == MSG_DATA)
        && frame_flags[0]
        && !chunk_inflight
        && (frame_sequence == 32'd0)
        && (frame_file_offset == 32'd0)
        && header_chunk_shape_valid
        && (frame_total_length >= frame_chunk_length);

    // A continuation is accepted only at the exact committed sequence/offset
    // and for the same session, target, file size and expected file CRC.
    wire header_new_continuation =
        header_common_valid
        && (frame_message == MSG_DATA)
        && !frame_flags[0]
        && programming_session_active
        && !chunk_inflight
        && (frame_session == active_session)
        && (frame_target_csm == active_target_csm)
        && (frame_target_sca == active_target_sca)
        && (frame_total_length == active_total_length)
        && (frame_expected_file_crc == active_expected_file_crc)
        && (frame_sequence == expected_sequence)
        && (frame_file_offset == expected_file_offset)
        && header_chunk_shape_valid;

    // A standalone IDCODE request is allowed only outside a programming
    // session.  It has no application payload; Ethernet FCS protects the
    // padded control frame, while the SCA reply matching protects execution.
    wire header_new_idcode =
        header_common_valid
        && (frame_message == MSG_IDCODE_READ)
        && (frame_flags == 8'b0)
        && (frame_chunk_length == 16'b0)
        && (frame_file_offset == 32'b0)
        && (frame_total_length == 32'b0)
        && (frame_expected_file_crc == 32'b0)
        && !programming_session_active
        && !chunk_inflight;

    // A duplicate of the executing chunk receives RX_ACK/BUSY.  A duplicate
    // of the most recently completed chunk receives its cached SCA result.
    wire header_duplicate_inflight =
        header_common_valid
        && (frame_message == inflight_message)
        && chunk_inflight
        && (frame_session == active_session)
        && (frame_sequence == inflight_sequence)
        && (frame_target_csm == active_target_csm)
        && (frame_target_sca == active_target_sca);

    wire header_duplicate_done =
        header_common_valid
        && (frame_message == last_result_request_message)
        && last_result_valid
        && !chunk_inflight
        && (frame_session == last_result_session)
        && (frame_sequence == last_result_sequence)
        && (frame_target_csm == active_target_csm)
        && (frame_target_sca == active_target_sca);

    // Backpressure is asserted only for FIFO reset/flush or when internal
    // single-entry finalization/response storage is occupied.  Once ready is
    // asserted, each accepted byte is identified by rx_fire.
    wire parser_blocked =
        data_fifo_wr_rst_busy | descriptor_fifo_wr_rst_busy
        | fifo_flush | finalize_pending
        | (response_valid & ~response_ready);

    assign rx_tready = ~parser_blocked;

    // Parser state and payload packing advance only for accepted AXI bytes.
    // If either side deasserts its handshake, the current byte position and
    // partially assembled 128-bit word remain unchanged.
    wire rx_fire = rx_tvalid & rx_tready;

    // Byte ranges are derived from the length captured in header bytes 24..25.
    // Bytes 46 through 46+length-1 are payload; the following four bytes are
    // the application chunk CRC32 in network byte order.
    wire payload_cycle =
        (frame_message == MSG_DATA)
        && (frame_index >= 16'd46)
        && (frame_index < (16'd46 + frame_chunk_length));
    wire crc_cycle =
        (frame_message == MSG_DATA)
        && (frame_index >= (16'd46 + frame_chunk_length))
        && (frame_index < (16'd50 + frame_chunk_length));

    // Response descriptor passed atomically to ethernet_program_ack_tx:
    // [255:208] destination MAC, [207:176] session, [175:144] sequence,
    // [143:112] expected sequence, [111:80] completed byte offset or,
    // for IDCODE_ACK, captured FPGA IR status in bits [5:0],
    // [79:48] result data (rolling CRC or IDCODE), [47:40] message,
    // [39:32] status,
    // [31:24] CSM, [23:16] SCA, [15:8] failed command, [7:0] error.
    //
    // This synthesizable task only centralizes repeated nonblocking
    // assignments; it creates no separate state machine or clock cycle.
    task automatic set_response;
        input [47:0] destination;
        input [31:0] session;
        input [31:0] sequence_value;
        input [31:0] expected;
        input [31:0] offset;
        input [31:0] result_data;
        input [7:0] message;
        input [7:0] status;
        input [7:0] target_csm;
        input [7:0] target_sca;
        input [7:0] failed_command;
        input [7:0] error;
        begin
            response_descriptor <= {
                destination, session, sequence_value, expected, offset,
                result_data,
                message, status, target_csm, target_sca,
                failed_command, error
            };
            response_valid <= 1'b1;
        end
    endtask

    // Temporary values used inside the sequential parser.  Blocking assignment
    // is intentional here: comparisons at the final byte must include the byte
    // currently present on rx_tdata, not only the previous registered value.
    integer padding_shift;
    reg [31:0] crc_received_now;
    reg [31:0] crc_expected_now;
    reg [127:0] assembled_word;
    reg [7:0] current_result_status;
    reg [7:0] current_result_error;
    reg [7:0] current_result_command;
    reg [7:0] current_result_sca_error;

    // RX-domain parser and session controller.  FIFO write enables and the
    // abort pulse are one-clock strobes, so they are cleared before processing
    // this cycle's result, finalization or accepted RX byte.
    always @(posedge rx_clk) begin
        data_fifo_wr_en <= 1'b0;
        descriptor_fifo_wr_en <= 1'b0;
        abort_rx_pulse <= 1'b0;

        if (response_valid && response_ready)
            response_valid <= 1'b0;

        if (fifo_flush_count != 5'd0)
            fifo_flush_count <= fifo_flush_count - 1'b1;

        if (!rx_resetn || control_reset_rx) begin
            frame_index <= 16'd0;
            frame_mode <= FRAME_REJECT;
            payload_byte_index <= 16'd0;
            payload_shift <= 128'b0;
            chunk_crc_state <= 32'hFFFFFFFF;
            rolling_candidate_state <= 32'hFFFFFFFF;
            frame_crc_seen <= 1'b0;
            frame_crc_good <= 1'b0;
            frame_fifo_error <= 1'b0;
            finalize_pending <= 1'b0;
            programming_session_active <= 1'b0;
            active_session <= 32'b0;
            expected_sequence <= 32'b0;
            expected_file_offset <= 32'b0;
            rolling_file_crc_state <= 32'hFFFFFFFF;
            chunk_inflight <= 1'b0;
            inflight_message <= MSG_DATA;
            last_result_valid <= 1'b0;
            last_result_request_message <= MSG_DATA;
            response_valid <= 1'b0;
            fifo_flush_count <= 5'd0;
        end else begin
            // A completed programmer result has priority when there is no
            // pending frame-finalization response.  result[31:24] is zero for
            // success and nonzero for failure; result[23:16] carries the
            // detailed SCA_NACK failure class.
            if (result_fifo_pop) begin
                current_result_status  = result_fifo_dout[31:24];
                current_result_error   = result_fifo_dout[23:16];
                current_result_command = result_fifo_dout[15:8];
                current_result_sca_error = result_fifo_dout[7:0];

                chunk_inflight <= 1'b0;
                last_result_valid <= 1'b1;
                last_result_session <= result_fifo_dout[159:128];
                last_result_sequence <= result_fifo_dout[127:96];
                last_result_offset <= result_fifo_dout[95:64];
                last_result_crc <= result_fifo_dout[63:32];
                // Cache exactly the status value carried in the original
                // SCA response so a retransmitted completed chunk receives
                // the same response fields.
                last_result_status <= current_result_error;
                last_result_command <= current_result_command;
                last_result_error <= current_result_sca_error;
                last_result_request_message <= inflight_message;

                if (current_result_status == 8'h00) begin
                    if (inflight_message == MSG_IDCODE_READ) begin
                        // IDCODE is a standalone transaction.  The result-data
                        // field contains the captured device ID and no file
                        // session is opened.  The offset field is otherwise
                        // unused here, so it carries captured IR[5:0] to expose
                        // DONE/INIT. Advancing the response sequence also makes
                        // a duplicate replay byte-for-byte stable.
                        last_result_message <= MSG_IDCODE_ACK;
                        expected_sequence
                            <= result_fifo_dout[127:96] + 1'b1;
                        expected_file_offset <= 32'b0;
                        set_response(
                            active_source_mac,
                            result_fifo_dout[159:128],
                            result_fifo_dout[127:96],
                            result_fifo_dout[127:96] + 1'b1,
                            result_fifo_dout[95:64],
                            result_fifo_dout[63:32],
                            MSG_IDCODE_ACK,
                            current_result_error,
                            active_target_csm,
                            active_target_sca,
                            current_result_command,
                            current_result_sca_error
                        );
                    end else begin
                        // Commit this chunk only after the SCA finished it. The
                        // next sequence and byte offset now become acceptable.
                        last_result_message <= MSG_SCA_ACK;
                        expected_sequence
                            <= result_fifo_dout[127:96] + 1'b1;
                        expected_file_offset <= result_fifo_dout[95:64];
                        if (inflight_last)
                            programming_session_active <= 1'b0;
                        set_response(
                            active_source_mac,
                            result_fifo_dout[159:128],
                            result_fifo_dout[127:96],
                            result_fifo_dout[127:96] + 1'b1,
                            result_fifo_dout[95:64],
                            result_fifo_dout[63:32],
                            MSG_SCA_ACK,
                            current_result_error,
                            active_target_csm,
                            active_target_sca,
                            current_result_command,
                            current_result_sca_error
                        );
                    end
                end else begin
                    // A programming failure terminates its file session.  An
                    // IDCODE failure has no payload/session state to flush.
                    last_result_message <=
                        (inflight_message == MSG_IDCODE_READ)
                            ? MSG_IDCODE_NACK : MSG_SCA_NACK;
                    if (inflight_message != MSG_IDCODE_READ) begin
                        programming_session_active <= 1'b0;
                        fifo_flush_count <= 5'd16;
                    end
                    set_response(
                        active_source_mac,
                        result_fifo_dout[159:128],
                        result_fifo_dout[127:96],
                        expected_sequence,
                        expected_file_offset,
                        result_fifo_dout[63:32],
                        (inflight_message == MSG_IDCODE_READ)
                            ? MSG_IDCODE_NACK : MSG_SCA_NACK,
                        current_result_error,
                        active_target_csm,
                        active_target_sca,
                        current_result_command,
                        current_result_sca_error
                    );
                end
            end

            // TLAST records the outcome, and finalization runs on a following
            // clock so nonblocking updates from the last received byte (CRC,
            // parser mode and FIFO-error state) are visible here.
            if (finalize_pending && !response_valid) begin
                finalize_pending <= 1'b0;

                if (finalize_mode == FRAME_IGNORE) begin
                    // 0x88B5 is shared with MDC1 control.  A non-MDJ1 frame
                    // belongs to another parser and must not receive an MDJ1
                    // programming NACK.
                end else if (finalize_mode == FRAME_ABORT) begin
                    // Stop the control-domain FSM and flush all payload and
                    // descriptor state.  The response confirms the abort was
                    // accepted, not that a data chunk completed.
                    abort_rx_pulse <= 1'b1;
                    programming_session_active <= 1'b0;
                    chunk_inflight <= 1'b0;
                    fifo_flush_count <= 5'd16;
                    set_response(
                        frame_source_mac, frame_session, frame_sequence,
                        expected_sequence, expected_file_offset,
                        ~rolling_file_crc_state, MSG_RX_ACK, ERR_ABORTED,
                        frame_target_csm, frame_target_sca, 8'b0, ERR_NONE
                    );
                end else if (finalize_mode == FRAME_DUP_INFLIGHT) begin
                    // The original chunk is already buffered/executing.
                    // Re-advertise RX acceptance without enqueueing it again.
                    set_response(
                        active_source_mac, active_session, inflight_sequence,
                        expected_sequence, expected_file_offset,
                        inflight_rolling_crc, MSG_RX_ACK, ERR_BUSY,
                        active_target_csm, active_target_sca, 8'b0, ERR_NONE
                    );
                end else if (finalize_mode == FRAME_DUP_DONE) begin
                    // Re-send the exact cached programming/IDCODE result in
                    // case the host missed the original response.
                    set_response(
                        active_source_mac, last_result_session,
                        last_result_sequence, expected_sequence,
                        last_result_offset, last_result_crc,
                        last_result_message, last_result_status,
                        active_target_csm, active_target_sca,
                        last_result_command, last_result_error
                    );
                end else if (finalize_mode == FRAME_IDCODE) begin
                    if (descriptor_fifo_full) begin
                        set_response(
                            frame_source_mac, frame_session, frame_sequence,
                            frame_sequence, 32'b0, 32'b0, MSG_RX_NACK,
                            ERR_FIFO, frame_target_csm, frame_target_sca,
                            8'b0, ERR_FIFO
                        );
                    end else begin
                        // Commit a metadata-only operation.  OP_IDCODE in the
                        // low descriptor bits tells the 40 MHz FSM not to read
                        // the bit-file data FIFO or enter configuration mode.
                        descriptor_fifo_din <= {
                            frame_session,
                            frame_sequence,
                            32'b0,
                            32'b0,
                            32'b0,
                            16'b0,
                            8'b0,
                            1'b0,
                            1'b0,
                            frame_target_csm[1:0],
                            frame_target_sca[1:0],
                            2'b01
                        };
                        descriptor_fifo_wr_en <= 1'b1;
                        chunk_inflight <= 1'b1;
                        inflight_last <= 1'b0;
                        inflight_sequence <= frame_sequence;
                        inflight_rolling_crc <= 32'b0;
                        inflight_message <= MSG_IDCODE_READ;
                        active_session <= frame_session;
                        active_source_mac <= frame_source_mac;
                        active_target_csm <= frame_target_csm;
                        active_target_sca <= frame_target_sca;
                        expected_sequence <= frame_sequence;
                        expected_file_offset <= 32'b0;
                        last_result_valid <= 1'b0;

                        set_response(
                            frame_source_mac, frame_session, frame_sequence,
                            frame_sequence, 32'b0, 32'b0,
                            MSG_RX_ACK, ERR_NONE,
                            frame_target_csm, frame_target_sca,
                            8'b0, ERR_NONE
                        );
                    end
                end else if (finalize_mode != FRAME_NEW) begin
                    // Header, session, sequence or busy rejection.  No payload
                    // from this frame was committed.
                    set_response(
                        frame_source_mac, frame_session, frame_sequence,
                        expected_sequence, expected_file_offset,
                        ~rolling_file_crc_state, MSG_RX_NACK,
                        finalize_error, frame_target_csm, frame_target_sca,
                        8'b0, finalize_error
                    );
                end else if (!finalize_crc_good || frame_fifo_error
                             || descriptor_fifo_full) begin
                    // Payload may already have entered the speculative data
                    // FIFO, so rejection also flushes both RX-to-control FIFOs.
                    fifo_flush_count <= 5'd16;
                    set_response(
                        frame_source_mac, frame_session, frame_sequence,
                        expected_sequence, expected_file_offset,
                        ~rolling_file_crc_state, MSG_RX_NACK,
                        (frame_fifo_error || descriptor_fifo_full)
                            ? ERR_FIFO : ERR_CHUNK_CRC,
                        frame_target_csm, frame_target_sca, 8'b0,
                        (frame_fifo_error || descriptor_fifo_full)
                            ? ERR_FIFO : ERR_CHUNK_CRC
                    );
                end else if (frame_flags[1]
                    && ((frame_file_offset + frame_chunk_length
                         != frame_total_length)
                        || (~rolling_candidate_state
                            != frame_expected_file_crc))) begin
                    // LAST commits only when both total byte count and rolling
                    // CRC32 agree with the values announced in every header.
                    fifo_flush_count <= 5'd16;
                    programming_session_active <= 1'b0;
                    set_response(
                        frame_source_mac, frame_session, frame_sequence,
                        expected_sequence, expected_file_offset,
                        ~rolling_candidate_state, MSG_RX_NACK,
                        ERR_FILE_CRC, frame_target_csm, frame_target_sca,
                        8'b0, ERR_FILE_CRC
                    );
                end else begin
                    // Commit metadata after all transport checks.  The
                    // descriptor appears in the 40 MHz domain after payload
                    // words that are already safely stored in the data FIFO.
                    descriptor_fifo_din <= {
                        frame_session,
                        frame_sequence,
                        frame_file_offset,
                        frame_total_length,
                        ~rolling_candidate_state,
                        frame_chunk_length,
                        chunk_word_count(frame_chunk_length),
                        frame_flags[0],
                        frame_flags[1],
                        frame_target_csm[1:0],
                        frame_target_sca[1:0],
                        2'b00
                    };
                    descriptor_fifo_wr_en <= 1'b1;
                    chunk_inflight <= 1'b1;
                    inflight_last <= frame_flags[1];
                    inflight_sequence <= frame_sequence;
                    inflight_rolling_crc <= ~rolling_candidate_state;
                    inflight_message <= MSG_DATA;
                    rolling_file_crc_state <= rolling_candidate_state;

                    if (frame_flags[0]) begin
                        // FIRST establishes the identity and invariants that
                        // every following chunk must reproduce.
                        programming_session_active <= 1'b1;
                        active_session <= frame_session;
                        active_source_mac <= frame_source_mac;
                        active_target_csm <= frame_target_csm;
                        active_target_sca <= frame_target_sca;
                        active_total_length <= frame_total_length;
                        active_expected_file_crc
                            <= frame_expected_file_crc;
                        expected_sequence <= frame_sequence;
                        expected_file_offset <= frame_file_offset;
                        last_result_valid <= 1'b0;
                    end

                    // RX_ACK is deliberately earlier than SCA_ACK.  It tells
                    // the host the frame is safely buffered and being handled.
                    set_response(
                        frame_source_mac, frame_session, frame_sequence,
                        frame_sequence, frame_file_offset,
                        ~rolling_candidate_state, MSG_RX_ACK, ERR_NONE,
                        frame_target_csm, frame_target_sca, 8'b0, ERR_NONE
                    );
                end
            end

            if (rx_fire) begin
                if (frame_index == 16'd0) begin
                    // Start of a new AXI frame.  Clear only per-frame state;
                    // committed session and duplicate history remain intact.
                    frame_destination_mac <= 48'b0;
                    frame_source_mac <= 48'b0;
                    frame_ethertype <= 16'b0;
                    frame_magic <= 32'b0;
                    frame_mode <= FRAME_REJECT;
                    frame_reject_error <= ERR_HEADER;
                    payload_byte_index <= 16'b0;
                    payload_shift <= 128'b0;
                    chunk_crc_state <= 32'hFFFFFFFF;
                    rolling_candidate_state <= 32'hFFFFFFFF;
                    received_chunk_crc <= 32'b0;
                    frame_crc_seen <= 1'b0;
                    frame_crc_good <= 1'b0;
                    frame_fifo_error <= 1'b0;
                end

                // Capture the fixed Ethernet/protocol header in network byte
                // order.  Byte 23 is reserved and is intentionally ignored.
                case (frame_index)
                    16'd0, 16'd1, 16'd2, 16'd3, 16'd4, 16'd5:
                        frame_destination_mac
                            <= {frame_destination_mac[39:0], rx_tdata};
                    16'd6, 16'd7, 16'd8, 16'd9, 16'd10, 16'd11:
                        frame_source_mac
                            <= {frame_source_mac[39:0], rx_tdata};
                    16'd12, 16'd13:
                        frame_ethertype
                            <= {frame_ethertype[7:0], rx_tdata};
                    16'd14, 16'd15, 16'd16, 16'd17:
                        frame_magic <= {frame_magic[23:0], rx_tdata};
                    16'd18: frame_version <= rx_tdata;
                    16'd19: frame_message <= rx_tdata;
                    16'd20: frame_flags <= rx_tdata;
                    16'd21: frame_target_csm <= rx_tdata;
                    16'd22: frame_target_sca <= rx_tdata;
                    16'd24, 16'd25:
                        frame_chunk_length
                            <= {frame_chunk_length[7:0], rx_tdata};
                    16'd26, 16'd27, 16'd28, 16'd29:
                        frame_session <= {frame_session[23:0], rx_tdata};
                    16'd30, 16'd31, 16'd32, 16'd33:
                        frame_sequence <= {frame_sequence[23:0], rx_tdata};
                    16'd34, 16'd35, 16'd36, 16'd37:
                        frame_file_offset
                            <= {frame_file_offset[23:0], rx_tdata};
                    16'd38, 16'd39, 16'd40, 16'd41:
                        frame_total_length
                            <= {frame_total_length[23:0], rx_tdata};
                    16'd42, 16'd43, 16'd44, 16'd45:
                        frame_expected_file_crc
                            <= {frame_expected_file_crc[23:0], rx_tdata};
                    default: begin end
                endcase

                // At byte 46 all header registers contain complete values.
                // Byte 46 is also the first data byte, so an accepted FRAME_NEW
                // initializes both CRC calculations and the 128-bit packer
                // with that same byte.  Placing it in bits [7:0] initially lets
                // the following fifteen shifts move it into bits [127:120].
                if (frame_index == 16'd46) begin
                    if (frame_ethertype != PROGRAM_ETHERTYPE
                        || frame_magic != PROTOCOL_MAGIC) begin
                        frame_mode <= FRAME_IGNORE;
                    end else if (frame_message == MSG_ABORT
                        && header_common_valid
                        && frame_session == active_session) begin
                        frame_mode <= FRAME_ABORT;
                    end else if (header_duplicate_inflight) begin
                        frame_mode <= FRAME_DUP_INFLIGHT;
                        frame_reject_error <= ERR_BUSY;
                    end else if (header_duplicate_done) begin
                        frame_mode <= FRAME_DUP_DONE;
                    end else if (header_new_idcode) begin
                        frame_mode <= FRAME_IDCODE;
                    end else if (header_new_first
                        || header_new_continuation) begin
                        frame_mode <= FRAME_NEW;
                        chunk_crc_state
                            <= crc32_next_byte(32'hFFFFFFFF, rx_tdata);
                        rolling_candidate_state <= crc32_next_byte(
                            header_new_first
                                ? 32'hFFFFFFFF : rolling_file_crc_state,
                            rx_tdata
                        );
                        payload_shift <= {120'b0, rx_tdata};
                        payload_byte_index <= 16'd1;
                        if (frame_chunk_length == 16'd1) begin
                            // A one-byte LAST frame completes a padded FIFO
                            // word immediately on its first payload byte.
                            if (!data_fifo_full) begin
                                data_fifo_din <= {rx_tdata, 120'b0};
                                data_fifo_wr_en <= 1'b1;
                            end else begin
                                frame_fifo_error <= 1'b1;
                            end
                        end
                    end else begin
                        // Consume the remainder through TLAST, but do not write
                        // rejected payload bytes into the programming FIFO.
                        frame_mode <= FRAME_REJECT;
                        frame_reject_error <=
                            (chunk_inflight || programming_session_active)
                            ? ERR_BUSY : ERR_SEQUENCE;
                    end
                end else if (payload_cycle && frame_mode == FRAME_NEW) begin
                    // Shift bytes into network order.  Every sixteenth byte
                    // completes one 128-bit FIFO word:
                    //
                    //   assembled_word = previous 15 bytes followed by rx_tdata
                    //
                    // payload_byte_index counts bytes already accepted before
                    // this clock, so a low nibble of F identifies byte 16.
                    chunk_crc_state
                        <= crc32_next_byte(chunk_crc_state, rx_tdata);
                    rolling_candidate_state <= crc32_next_byte(
                        rolling_candidate_state, rx_tdata
                    );
                    assembled_word = {payload_shift[119:0], rx_tdata};
                    payload_shift <= assembled_word;
                    payload_byte_index <= payload_byte_index + 1'b1;

                    if (payload_byte_index[3:0] == 4'hF) begin
                        if (!data_fifo_full) begin
                            data_fifo_din <= assembled_word;
                            data_fifo_wr_en <= 1'b1;
                        end else begin
                            frame_fifo_error <= 1'b1;
                        end
                    end else if (payload_byte_index + 1'b1
                                 == frame_chunk_length) begin
                        // Pad a partial LAST word on the right.  The programmer
                        // later right-aligns its valid bits before the SCA
                        // partial-length JTAG operation.  For three bytes:
                        //
                        //   FIFO [127:120]=B0, [119:112]=B1,
                        //        [111:104]=B2, [103:0]=zero.
                        padding_shift =
                            (16 - ((payload_byte_index + 1'b1) & 15)) * 8;
                        if (!data_fifo_full) begin
                            data_fifo_din <= assembled_word << padding_shift;
                            data_fifo_wr_en <= 1'b1;
                        end else begin
                            frame_fifo_error <= 1'b1;
                        end
                    end
                end

                if (crc_cycle) begin
                    // Receive the four-byte application CRC in network order.
                    // On its final byte, blocking temporaries include rx_tdata
                    // in the comparison performed during this same clock.
                    received_chunk_crc
                        <= {received_chunk_crc[23:0], rx_tdata};
                    if (frame_index == 16'd49 + frame_chunk_length) begin
                        crc_received_now
                            = {received_chunk_crc[23:0], rx_tdata};
                        crc_expected_now = ~chunk_crc_state;
                        frame_crc_seen <= 1'b1;
                        frame_crc_good
                            <= (crc_received_now == crc_expected_now);
                    end
                end

                if (rx_tlast) begin
                    // Defer the response decision for one clock.  This also
                    // verifies that the frame ended at the expected CRC byte;
                    // early or late TLAST cannot accidentally pass.
                    finalize_pending <= 1'b1;
                    finalize_mode <= frame_mode;
                    finalize_error <= frame_reject_error;
                    if (frame_index == 16'd49 + frame_chunk_length) begin
                        finalize_crc_good <=
                            ({received_chunk_crc[23:0], rx_tdata}
                             == ~chunk_crc_state);
                    end else begin
                        finalize_crc_good <= frame_crc_seen
                                          & frame_crc_good;
                    end
                    frame_index <= 16'd0;
                end else begin
                    frame_index <= frame_index + 1'b1;
                end
            end
        end
    end

endmodule
