// Local GBT-SCA JTAG programmer and IDCODE reader.
//
// Hierarchy and interfaces:
//
//   Parent: ethernet_sca_jtag_top.programmer
//   Children: none; this module is one 40 MHz autonomous FSM
//
//   ethernet_jtag_transport
//       descriptor + 128-bit payload
//                    |
//                    v
//       ethernet_jtag_programmer
//          |                    ^
//          | SCA command        | selected/matched SCA reply
//          v                    |
//   ethernet_sca_command_arbiter + ethernet_sca_reply_mux
//          |
//          v
//       physical sca_top -> lpGBT EC link -> GBT-SCA JTAG controller
//
//   programmer result -> ethernet_jtag_transport -> ACK descriptor
//
// This is a one-process, 40 MHz state machine.  The Ethernet transport first
// checks a programming frame and places its payload in a 128-bit asynchronous
// FIFO.  It then presents one descriptor to this module.  Only one descriptor
// is processed at a time.
//
// A normal 1408-byte Ethernet chunk contains 88 input words.  Each 128-bit
// word is executed by the SCA as:
//
//   W_CTRL when the transfer length changes
//   W_TMS3..W_TMS0 for only the TMS words that changed
//   W_TDO3, W_TDO2, W_TDO1, W_TDO0
//   GO
//   R_CTRL repeatedly until BUSY is zero
//
// The first chunk also enables the SCA JTAG channel, sets its frequency, sends
// JPROGRAM, waits 10 ms, and enters CFG_IN/Shift-DR.  The final chunk handles
// a possible partial word, sends JSTART, waits 2 ms, resets the TAP, and checks
// the FPGA DONE/INIT and captured-IR status.
//
// SCA commands use unique transaction IDs.  Replies are accepted only when
// both the transaction ID and channel match.  A missing write/status reply is
// retried up to MAX_REPLY_RETRIES times before the chunk fails.  GO is not
// repeated after an ambiguous timeout; R_CTRL is used to determine whether
// that GO completed.  A standalone IDCODE descriptor follows the same checked
// SCA command path but skips JPROGRAM/CFG_IN and returns the captured 32-bit
// IDCODE without opening a bit-file programming session.

`timescale 1ns / 1ps

module ethernet_jtag_programmer #(
    parameter integer CLOCK_FREQUENCY_HZ   = 40_000_000,
    parameter integer REPLY_TIMEOUT_CYCLES = 400_000,
    parameter integer MAX_REPLY_RETRIES    = 100
) (
    // 40 MHz MiniDAQ control domain.
    input  wire         clk,
    input  wire         rst,
    input  wire         abort,

    // One validated Ethernet chunk descriptor.
    input  wire [191:0] descriptor,
    input  wire         descriptor_valid,
    output wire         descriptor_ready,

    // Bit-file payload from the transport's 128-bit CDC FIFO.
    input  wire [127:0] chunk_data,
    input  wire         chunk_data_valid,
    output reg          chunk_data_ready = 1'b0,

    // Completion record returned to the Ethernet ACK generator.
    output reg  [159:0] result = 160'b0,
    output reg          result_valid = 1'b0,
    input  wire         result_ready,

    // The target remains stable while a chunk is being executed.  The top
    // level uses it to grant the programmer ownership of one CSM/SCA.
    output reg          programming_active = 1'b0,
    output reg  [1:0]   target_csm = 2'b0,
    output reg  [1:0]   target_sca = 2'b0,

    // Command request to the existing SCA protocol engine.
    output reg          sca_start_command = 1'b0,
    output reg  [7:0]   sca_tx_address = 8'b0,
    output reg  [7:0]   sca_tx_transid = 8'b0,
    output reg  [7:0]   sca_tx_channel = 8'b0,
    output reg  [7:0]   sca_tx_command = 8'b0,
    output reg  [31:0]  sca_tx_data = 32'b0,

    // Reply selected from the target CSM/SCA by ethernet_sca_reply_mux.
    input  wire         sca_reply_valid,
    input  wire [7:0]   sca_reply_transid,
    input  wire [7:0]   sca_reply_channel,
    input  wire [7:0]   sca_reply_error,
    input  wire [31:0]  sca_reply_data
);

    localparam logic [7:0] CR_CHANNEL       = 8'h00;
    localparam logic [7:0] CTRL_W_CRD       = 8'h06;
    localparam logic [31:0] ENJTAG_DATA     = 32'h08000000;

    localparam logic [7:0] JTAG_CHANNEL     = 8'h13;
    localparam logic [7:0] JTAG_W_CTRL      = 8'h80;
    localparam logic [7:0] JTAG_R_CTRL      = 8'h81;
    localparam logic [7:0] JTAG_W_FREQ      = 8'h90;
    localparam logic [7:0] JTAG_W_TDO0      = 8'h00;
    localparam logic [7:0] JTAG_W_TDO1      = 8'h10;
    localparam logic [7:0] JTAG_W_TDO2      = 8'h20;
    localparam logic [7:0] JTAG_W_TDO3      = 8'h30;
    localparam logic [7:0] JTAG_R_TDI0      = 8'h01;
    localparam logic [7:0] JTAG_R_TDI1      = 8'h11;
    localparam logic [7:0] JTAG_W_TMS0      = 8'h40;
    localparam logic [7:0] JTAG_W_TMS1      = 8'h50;
    localparam logic [7:0] JTAG_W_TMS2      = 8'h60;
    localparam logic [7:0] JTAG_W_TMS3      = 8'h70;
    localparam logic [7:0] JTAG_GO          = 8'hA2;

    localparam integer WAIT_10MS_CYCLES = CLOCK_FREQUENCY_HZ / 100;
    localparam integer WAIT_2MS_CYCLES  = CLOCK_FREQUENCY_HZ / 500;
    localparam logic [7:0] STATUS_REPLY_TIMEOUT = 8'h03;

    // State groups:
    //   0..15  - chunk/session sequencing, FPGA configuration, and IDCODE
    //   20..30 - execution of one staged JTAG block
    //   31     - common SCA reply/timeout handler
    localparam logic [7:0]
        ST_IDLE              = 8'd0,
        ST_INIT_ENABLE       = 8'd1,
        ST_INIT_FREQ         = 8'd2,
        ST_PREP_JPROGRAM     = 8'd3,
        ST_WAIT_10MS         = 8'd4,
        ST_PREP_CFG_ENTRY    = 8'd5,
        ST_FETCH_DATA        = 8'd6,
        ST_PREP_POST_JSTART  = 8'd7,
        ST_WAIT_2MS          = 8'd8,
        ST_PREP_TLR          = 8'd9,
        ST_PREP_VERIFY       = 8'd10,
        ST_READ_VERIFY_TDI1  = 8'd11,
        ST_VERIFY_CHECK      = 8'd12,
        ST_SUCCESS           = 8'd13,
        ST_RESULT            = 8'd14,
        ST_READ_VERIFY_TDI0  = 8'd15,

        ST_BLOCK_CTRL        = 8'd20,
        ST_BLOCK_TMS3        = 8'd21,
        ST_BLOCK_TMS2        = 8'd22,
        ST_BLOCK_TMS1        = 8'd23,
        ST_BLOCK_TMS0        = 8'd24,
        ST_BLOCK_TDO3        = 8'd25,
        ST_BLOCK_TDO2        = 8'd26,
        ST_BLOCK_TDO1        = 8'd27,
        ST_BLOCK_TDO0        = 8'd28,
        ST_BLOCK_GO          = 8'd29,
        ST_BLOCK_RCTRL       = 8'd30,
        ST_WAIT_REPLY        = 8'd31;

    // Common SCA transaction context.  Every command enters ST_WAIT_REPLY;
    // after_reply_state determines where a successful reply continues.
    // retry_state determines which command state is revisited after timeout.
    reg [7:0] state = ST_IDLE;
    reg [7:0] after_reply_state = ST_IDLE;
    reg [7:0] retry_state = ST_IDLE;
    reg [7:0] block_after_state = ST_IDLE;
    reg [7:0] expected_transid = 8'b0;
    reg [7:0] expected_channel = 8'b0;
    reg [7:0] expected_command = 8'b0;
    reg [7:0] next_transid = 8'h01;
    reg [31:0] reply_timeout_count = 32'b0;
    reg [15:0] reply_retry_count = 16'b0;

    // Fields retained from the active Ethernet chunk descriptor.
    reg [31:0] current_session = 32'b0;
    reg [31:0] current_sequence = 32'b0;
    reg [31:0] current_file_offset = 32'b0;
    reg [31:0] current_rolling_crc = 32'b0;
    reg [15:0] current_chunk_length = 16'b0;
    reg [7:0] words_remaining = 8'b0;
    reg current_last = 1'b0;
    reg [1:0] current_operation = 2'b0;

    localparam logic [1:0] OP_PROGRAM = 2'b00;
    localparam logic [1:0] OP_IDCODE  = 2'b01;

    // One staged SCA JTAG operation.  Full payload blocks contain 128 bits;
    // the last bit-file block can contain 1..128 valid bits.
    reg [127:0] block_tdo = 128'b0;
    reg [127:0] block_tms = 128'b0;
    reg [7:0] block_bit_count = 8'd128;

    // SCA TMS and CTRL registers retain their values.  These shadows avoid
    // rewriting them before every data word when their contents are unchanged.
    reg [127:0] tms_shadow = 128'b0;
    reg tms_shadow_valid = 1'b0;
    reg [7:0] ctrl_bit_count = 8'b0;
    reg ctrl_shadow_valid = 1'b0;

    // Delay and final status-capture registers.
    reg [31:0] wait_counter = 32'b0;
    reg [31:0] verification_tdi1 = 32'b0;
    reg [31:0] verification_tdi0 = 32'b0;

    // Descriptor layout produced by ethernet_jtag_transport:
    //
    //   [191:160] session ID
    //   [159:128] chunk sequence
    //   [127:96]  bit-file byte offset
    //   [95:64]   complete bit-file length
    //   [63:32]   rolling CRC32, or zero for an IDCODE request
    //   [31:16]   valid bytes in this chunk
    //   [15:8]    number of 128-bit FIFO words
    //   [7]       first chunk
    //   [6]       last chunk
    //   [5:4]     target CSM/downlink
    //   [3:2]     target SCA
    //   [1:0]     operation: 0=program chunk, 1=standalone IDCODE read
    wire [31:0] desc_session       = descriptor[191:160];
    wire [31:0] desc_sequence      = descriptor[159:128];
    wire [31:0] desc_file_offset   = descriptor[127:96];
    wire [31:0] desc_total_length  = descriptor[95:64];
    wire [31:0] desc_rolling_crc   = descriptor[63:32];
    wire [15:0] desc_chunk_length  = descriptor[31:16];
    wire [7:0]  desc_word_count    = descriptor[15:8];
    wire        desc_first         = descriptor[7];
    wire        desc_last          = descriptor[6];
    wire [1:0]  desc_target_csm    = descriptor[5:4];
    wire [1:0]  desc_target_sca    = descriptor[3:2];
    wire [1:0]  desc_operation     = descriptor[1:0];

    // A new descriptor is accepted only when the preceding result has left.
    assign descriptor_ready = (state == ST_IDLE) && !result_valid;

    // SCA transaction ID zero is avoided; valid IDs wrap from FE back to 01.
    function automatic [7:0] increment_transid(input [7:0] value);
        begin
            increment_transid = (value >= 8'hFE)
                              ? 8'h01 : value + 1'b1;
        end
    endfunction

    // The captured six-bit FPGA instruction-register pattern is returned in
    // the opposite bit order from the convenient status representation.
    function automatic [5:0] reverse_six(input [5:0] value);
        integer index;
        begin
            for (index = 0; index < 6; index = index + 1)
                reverse_six[index] = value[5-index];
        end
    endfunction

    function automatic [31:0] reverse_thirty_two(input [31:0] value);
        integer index;
        begin
            for (index = 0; index < 32; index = index + 1)
                reverse_thirty_two[index] = value[31-index];
        end
    endfunction

    wire [5:0] captured_ir =
        reverse_six(verification_tdi1[12:7]);
    wire captured_ir_valid = captured_ir[1:0] == 2'b01;
    wire captured_done = captured_ir[5];
    wire captured_init = captured_ir[4];
    // In the fixed 55-clock IDCODE sequence, the 32 captured DR bits occupy
    // TDI register bits [33:2].  JTAG shifts the IDCODE least-significant bit
    // first, so reverse the captured order before returning the device value.
    wire [31:0] captured_idcode = reverse_thirty_two(
        {verification_tdi1[1:0], verification_tdi0[31:2]}
    );

    // There are 16 bytes per FIFO word.  A zero byte remainder means that the
    // final word is full; otherwise the remainder is converted to bits.
    wire [7:0] final_block_bit_count =
        (current_chunk_length[3:0] == 4'b0)
        ? 8'd128 : {1'b0, current_chunk_length[3:0], 3'b000};

    // Build the SCA JTAG CTRL value using the encoding already used by the
    // legacy SCA JTAG convention. A 7-bit length of zero means 128 clocks.
    function automatic [31:0] control_word(input [7:0] bit_count);
        begin
            // MSB=1, RXEDGE=TXEDGE=0, IVNTCK=0.
            // Preserve the existing software encoding: 128 sets bit 7,
            // while the SCA interprets length[6:0]==0 as 128 clocks.
            control_word = 32'h00000800 + bit_count;
        end
    endfunction

    // Common command-launch procedure used by the FSM states below.  A
    // synthesizable task is only source-code reuse: Vivado inlines these
    // nonblocking assignments at every call site.  It does not create another
    // FSM, processor, task scheduler, or extra clock cycle.
    task automatic issue_sca_command;
        input [7:0] channel_value;
        input [7:0] command_value;
        input [31:0] data_value;
        input [7:0] successful_state;
        input [7:0] retry_from_state;
        begin
            sca_tx_address <= 8'h00;
            sca_tx_transid <= next_transid;
            sca_tx_channel <= channel_value;
            sca_tx_command <= command_value;
            sca_tx_data <= data_value;
            sca_start_command <= 1'b1;
            expected_transid <= next_transid;
            expected_channel <= channel_value;
            expected_command <= command_value;
            next_transid <= increment_transid(next_transid);
            after_reply_state <= successful_state;
            retry_state <= retry_from_state;
            reply_timeout_count <= 32'b0;
            state <= ST_WAIT_REPLY;
        end
    endtask

    // Produce a uniformly formatted failure record and release SCA ownership.
    // Result fields are:
    //   session, sequence, offset/status, result data (rolling CRC or IDCODE),
    //   failure flag, status code, failed command, SCA/status detail.
    // For a successful standalone IDCODE operation, offset/status[5:0]
    // contains the captured FPGA IR.  This exposes DONE/INIT without another
    // JTAG transaction; programming operations retain the byte-offset meaning.
    task automatic fail_programming;
        input [7:0] status_code;
        input [7:0] failed_command;
        input [7:0] sca_error;
        begin
            result <= {
                current_session,
                current_sequence,
                current_file_offset,
                (current_operation == OP_IDCODE)
                    ? captured_idcode : current_rolling_crc,
                8'h01,
                status_code,
                failed_command,
                sca_error
            };
            result_valid <= 1'b1;
            programming_active <= 1'b0;
            state <= ST_RESULT;
        end
    endtask

    // One-process FSM.  Pulsed outputs are cleared at every clock and asserted
    // only by the state that consumes or launches the corresponding transfer.
    always @(posedge clk) begin
        sca_start_command <= 1'b0;
        chunk_data_ready <= 1'b0;

        if (rst) begin
            state <= ST_IDLE;
            result_valid <= 1'b0;
            programming_active <= 1'b0;
            target_csm <= 2'b0;
            target_sca <= 2'b0;
            next_transid <= 8'h01;
            tms_shadow_valid <= 1'b0;
            ctrl_shadow_valid <= 1'b0;
            wait_counter <= 32'b0;
            reply_timeout_count <= 32'b0;
            reply_retry_count <= 16'b0;
            sca_start_command <= 1'b0;
            chunk_data_ready <= 1'b0;
        end else if (abort) begin
            state <= ST_IDLE;
            result_valid <= 1'b0;
            programming_active <= 1'b0;
            tms_shadow_valid <= 1'b0;
            ctrl_shadow_valid <= 1'b0;
            reply_retry_count <= 16'b0;
        end else begin
            case (state)
                ST_IDLE: begin
                    // Wait for one fully checked Ethernet chunk descriptor.
                    if (result_valid && result_ready)
                        result_valid <= 1'b0;

                    if (descriptor_valid && descriptor_ready) begin
                        current_session <= desc_session;
                        current_sequence <= desc_sequence;
                        current_file_offset <= desc_file_offset;
                        current_rolling_crc <= desc_rolling_crc;
                        current_chunk_length <= desc_chunk_length;
                        words_remaining <= desc_word_count;
                        current_last <= desc_last;
                        current_operation <= desc_operation;
                        target_csm <= desc_target_csm;
                        target_sca <= desc_target_sca;
                        programming_active <= 1'b1;
                        reply_retry_count <= 16'b0;
                        verification_tdi1 <= 32'b0;
                        verification_tdi0 <= 32'b0;

                        if (desc_operation == OP_IDCODE) begin
                            tms_shadow_valid <= 1'b0;
                            ctrl_shadow_valid <= 1'b0;
                            state <= ST_INIT_ENABLE;
                        end else if (desc_first) begin
                            tms_shadow_valid <= 1'b0;
                            ctrl_shadow_valid <= 1'b0;
                            state <= ST_INIT_ENABLE;
                        end else begin
                            state <= ST_FETCH_DATA;
                        end
                    end
                end

                ST_INIT_ENABLE: begin
                    // Enable the SCA JTAG channel through its control register.
                    issue_sca_command(
                        CR_CHANNEL, CTRL_W_CRD, ENJTAG_DATA,
                        ST_INIT_FREQ, ST_INIT_ENABLE
                    );
                end

                ST_INIT_FREQ: begin
                    // Select the existing SCA JTAG clock-divider setting.
                    issue_sca_command(
                        JTAG_CHANNEL, JTAG_W_FREQ, 32'h00000000,
                        (current_operation == OP_IDCODE)
                            ? ST_PREP_VERIFY : ST_PREP_JPROGRAM,
                        ST_INIT_FREQ
                    );
                end

                ST_PREP_JPROGRAM: begin
                    // TAP reset followed by JPROGRAM and its required
                    // reset-after instruction sequence.  Bits are
                    // right-aligned in the SCA register bank because a
                    // partial transfer uses TDO0 first.
                    block_tdo <=
                        128'h00000000000000000000000000000D00;
                    block_tms <=
                        128'h000000000000000000000000003EC07E;
                    block_bit_count <= 8'd22;
                    block_after_state <= ST_WAIT_10MS;
                    state <= ST_BLOCK_CTRL;
                end

                ST_WAIT_10MS: begin
                    if (wait_counter >= WAIT_10MS_CYCLES-1) begin
                        wait_counter <= 32'b0;
                        state <= ST_PREP_CFG_ENTRY;
                    end else begin
                        wait_counter <= wait_counter + 1'b1;
                    end
                end

                ST_PREP_CFG_ENTRY: begin
                    // Shift CFG_IN, return to RTI, then enter Shift-DR.
                    block_tdo <=
                        128'h00000000000000000000000000000500;
                    block_tms <=
                        128'h00000000000000000000000000006034;
                    block_bit_count <= 8'd15;
                    block_after_state <= ST_FETCH_DATA;
                    state <= ST_BLOCK_CTRL;
                end

                ST_FETCH_DATA: begin
                    // Stage the next FIFO word.  On the final partial word,
                    // right-align the valid data and leave Shift-DR on its last
                    // bit by driving the corresponding TMS bits high.
                    if (words_remaining == 8'd0) begin
                        if (current_last)
                            state <= ST_PREP_POST_JSTART;
                        else
                            state <= ST_SUCCESS;
                    end else if (chunk_data_valid) begin
                        chunk_data_ready <= 1'b1;
                        block_tdo <= chunk_data;
                        words_remaining <= words_remaining - 1'b1;

                        if (current_last && words_remaining == 8'd1) begin
                            block_bit_count <= final_block_bit_count;
                            block_tdo <= chunk_data
                                      >> (128-final_block_bit_count);
                            block_tms <= 128'b1;
                            block_after_state <= ST_PREP_POST_JSTART;
                        end else begin
                            block_bit_count <= 8'd128;
                            block_tms <= 128'b0;
                            block_after_state <= ST_FETCH_DATA;
                        end
                        state <= ST_BLOCK_CTRL;
                    end
                end

                ST_PREP_POST_JSTART: begin
                    // Starting in Exit1-DR: Update-DR, RTI, shift JSTART.
                    block_tdo <=
                        128'h00000000000000000000000000000030;
                    block_tms <=
                        128'h00000000000000000000000000002C06;
                    block_bit_count <= 8'd14;
                    block_after_state <= ST_WAIT_2MS;
                    state <= ST_BLOCK_CTRL;
                end

                ST_WAIT_2MS: begin
                    if (wait_counter >= WAIT_2MS_CYCLES-1) begin
                        wait_counter <= 32'b0;
                        state <= ST_PREP_TLR;
                    end else begin
                        wait_counter <= wait_counter + 1'b1;
                    end
                end

                ST_PREP_TLR: begin
                    block_tdo <= 128'b0;
                    block_tms <=
                        128'h000000000000000000000000FFFFFFFF;
                    block_bit_count <= 8'd32;
                    block_after_state <= ST_PREP_VERIFY;
                    state <= ST_BLOCK_CTRL;
                end

                ST_PREP_VERIFY: begin
                    // Complete IDCODE IR/DR verification sequence.  The six
                    // captured IR bits are later read from TDI1.
                    block_tdo <=
                        128'h00000000000000000000120000000000;
                    block_tms <=
                        128'h0000000000000000007D80D000000006;
                    block_bit_count <= 8'd55;
                    block_after_state <= ST_READ_VERIFY_TDI1;
                    state <= ST_BLOCK_CTRL;
                end

                ST_READ_VERIFY_TDI1: begin
                    issue_sca_command(
                        JTAG_CHANNEL, JTAG_R_TDI1, 32'b0,
                        ST_READ_VERIFY_TDI0, ST_READ_VERIFY_TDI1
                    );
                end

                ST_READ_VERIFY_TDI0: begin
                    issue_sca_command(
                        JTAG_CHANNEL, JTAG_R_TDI0, 32'b0,
                        ST_VERIFY_CHECK, ST_READ_VERIFY_TDI0
                    );
                end

                ST_VERIFY_CHECK: begin
                    if (!captured_ir_valid) begin
                        fail_programming(
                            8'h02, JTAG_R_TDI1,
                            {2'b0, captured_ir}
                        );
                    end else if (current_operation == OP_PROGRAM
                                 && (!captured_done || !captured_init)) begin
                        fail_programming(
                            8'h02, JTAG_R_TDI1,
                            {2'b0, captured_ir}
                        );
                    end else begin
                        state <= ST_SUCCESS;
                    end
                end

                ST_SUCCESS: begin
                    // Programming reports the first unconsumed byte offset.
                    // Standalone IDCODE instead reports the captured six-bit IR
                    // status in this otherwise-unused field.
                    result <= {
                        current_session,
                        current_sequence,
                        (current_operation == OP_IDCODE)
                            ? {26'b0, captured_ir}
                            : current_file_offset + current_chunk_length,
                        (current_operation == OP_IDCODE)
                            ? captured_idcode : current_rolling_crc,
                        8'h00,
                        8'h00,
                        8'h00,
                        8'h00
                    };
                    result_valid <= 1'b1;
                    if (current_last || current_operation == OP_IDCODE)
                        programming_active <= 1'b0;
                    state <= ST_RESULT;
                end

                ST_RESULT: begin
                    if (result_valid && result_ready) begin
                        result_valid <= 1'b0;
                        state <= ST_IDLE;
                    end
                end

                ST_BLOCK_CTRL: begin
                    // W_CTRL is required only when the valid JTAG length differs
                    // from the value already stored in the SCA.
                    if (!ctrl_shadow_valid
                        || ctrl_bit_count != block_bit_count) begin
                        issue_sca_command(
                            JTAG_CHANNEL, JTAG_W_CTRL,
                            control_word(block_bit_count),
                            ST_BLOCK_TMS3, ST_BLOCK_CTRL
                        );
                    end else begin
                        state <= ST_BLOCK_TMS3;
                    end
                end

                ST_BLOCK_TMS3: begin
                    // TMS registers are similarly skipped when their shadowed
                    // values already match this block.
                    if (!tms_shadow_valid
                        || tms_shadow[127:96] != block_tms[127:96]) begin
                        issue_sca_command(
                            JTAG_CHANNEL, JTAG_W_TMS3,
                            block_tms[127:96],
                            ST_BLOCK_TMS2, ST_BLOCK_TMS3
                        );
                    end else begin
                        state <= ST_BLOCK_TMS2;
                    end
                end

                ST_BLOCK_TMS2: begin
                    if (!tms_shadow_valid
                        || tms_shadow[95:64] != block_tms[95:64]) begin
                        issue_sca_command(
                            JTAG_CHANNEL, JTAG_W_TMS2,
                            block_tms[95:64],
                            ST_BLOCK_TMS1, ST_BLOCK_TMS2
                        );
                    end else begin
                        state <= ST_BLOCK_TMS1;
                    end
                end

                ST_BLOCK_TMS1: begin
                    if (!tms_shadow_valid
                        || tms_shadow[63:32] != block_tms[63:32]) begin
                        issue_sca_command(
                            JTAG_CHANNEL, JTAG_W_TMS1,
                            block_tms[63:32],
                            ST_BLOCK_TMS0, ST_BLOCK_TMS1
                        );
                    end else begin
                        state <= ST_BLOCK_TMS0;
                    end
                end

                ST_BLOCK_TMS0: begin
                    if (!tms_shadow_valid
                        || tms_shadow[31:0] != block_tms[31:0]) begin
                        issue_sca_command(
                            JTAG_CHANNEL, JTAG_W_TMS0,
                            block_tms[31:0],
                            ST_BLOCK_TDO3, ST_BLOCK_TMS0
                        );
                    end else begin
                        tms_shadow_valid <= 1'b1;
                        state <= ST_BLOCK_TDO3;
                    end
                end

                ST_BLOCK_TDO3: begin
                    // The SCA exposes four independent 32-bit TDO registers.
                    // All four are written from the most-significant word down
                    // to TDO0 before GO starts the complete JTAG operation.
                    issue_sca_command(
                        JTAG_CHANNEL, JTAG_W_TDO3, block_tdo[127:96],
                        ST_BLOCK_TDO2, ST_BLOCK_TDO3
                    );
                end

                ST_BLOCK_TDO2: begin
                    issue_sca_command(
                        JTAG_CHANNEL, JTAG_W_TDO2, block_tdo[95:64],
                        ST_BLOCK_TDO1, ST_BLOCK_TDO2
                    );
                end

                ST_BLOCK_TDO1: begin
                    issue_sca_command(
                        JTAG_CHANNEL, JTAG_W_TDO1, block_tdo[63:32],
                        ST_BLOCK_TDO0, ST_BLOCK_TDO1
                    );
                end

                ST_BLOCK_TDO0: begin
                    issue_sca_command(
                        JTAG_CHANNEL, JTAG_W_TDO0, block_tdo[31:0],
                        ST_BLOCK_GO, ST_BLOCK_TDO0
                    );
                end

                ST_BLOCK_GO: begin
                    // GO has side effects.  If its reply is lost, do not issue
                    // another GO; proceed to R_CTRL and observe BUSY instead.
                    issue_sca_command(
                        JTAG_CHANNEL, JTAG_GO, 32'b0,
                        ST_BLOCK_RCTRL, ST_BLOCK_GO
                    );
                end

                ST_BLOCK_RCTRL: begin
                    // Poll the SCA JTAG busy bit after each GO.
                    issue_sca_command(
                        JTAG_CHANNEL, JTAG_R_CTRL, 32'b0,
                        ST_BLOCK_RCTRL, ST_BLOCK_RCTRL
                    );
                end

                ST_WAIT_REPLY: begin
                    // Ignore unrelated replies.  The selected transaction must
                    // match both the saved transaction ID and SCA channel.
                    if (sca_reply_valid
                        && sca_reply_transid == expected_transid
                        && sca_reply_channel == expected_channel) begin
                        reply_timeout_count <= 32'b0;
                        reply_retry_count <= 16'b0;

                        if (sca_reply_error != 8'b0) begin
                            fail_programming(
                                8'h01, expected_command, sca_reply_error
                            );
                        end else if (expected_command == JTAG_W_CTRL) begin
                            ctrl_shadow_valid <= 1'b1;
                            ctrl_bit_count <= block_bit_count;
                            state <= after_reply_state;
                        end else if (expected_command == JTAG_W_TMS3) begin
                            tms_shadow[127:96] <= block_tms[127:96];
                            state <= after_reply_state;
                        end else if (expected_command == JTAG_W_TMS2) begin
                            tms_shadow[95:64] <= block_tms[95:64];
                            state <= after_reply_state;
                        end else if (expected_command == JTAG_W_TMS1) begin
                            tms_shadow[63:32] <= block_tms[63:32];
                            state <= after_reply_state;
                        end else if (expected_command == JTAG_W_TMS0) begin
                            tms_shadow[31:0] <= block_tms[31:0];
                            tms_shadow_valid <= 1'b1;
                            state <= after_reply_state;
                        end else if (expected_command == JTAG_R_CTRL) begin
                            if (sca_reply_data[8])
                                state <= ST_BLOCK_RCTRL;
                            else
                                state <= block_after_state;
                        end else if (expected_command == JTAG_R_TDI1) begin
                            verification_tdi1 <= sca_reply_data;
                            state <= after_reply_state;
                        end else if (expected_command == JTAG_R_TDI0) begin
                            verification_tdi0 <= sca_reply_data;
                            state <= after_reply_state;
                        end else begin
                            state <= after_reply_state;
                        end
                    end else if (reply_timeout_count
                                 >= REPLY_TIMEOUT_CYCLES-1) begin
                        reply_timeout_count <= 32'b0;
                        // Ordinary missing replies return to retry_state.  This
                        // repeats polling and register writes at most
                        // MAX_REPLY_RETRIES times.
                        // GO is never repeated after an ambiguous missing
                        // reply.  R_CTRL establishes whether it completed.
                        if (expected_command == JTAG_GO) begin
                            reply_retry_count <= 16'b0;
                            state <= ST_BLOCK_RCTRL;
                        end else if (reply_retry_count
                                     >= MAX_REPLY_RETRIES) begin
                            fail_programming(
                                STATUS_REPLY_TIMEOUT,
                                expected_command,
                                reply_retry_count[7:0]
                            );
                        end else begin
                            reply_retry_count <= reply_retry_count + 1'b1;
                            state <= retry_state;
                        end
                    end else begin
                        reply_timeout_count <= reply_timeout_count + 1'b1;
                    end
                end

                default: state <= ST_IDLE;
            endcase
        end
    end

endmodule
