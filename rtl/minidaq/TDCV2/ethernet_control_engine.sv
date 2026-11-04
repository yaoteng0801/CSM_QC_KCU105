// Executes validated Ethernet control/monitor requests in the 40 MHz domain.
// One transaction is active at a time, which prevents lpGBT IC, SCA and FPGA
// register replies from being associated with the wrong host request.
//
// Hierarchy and interfaces:
//
//   Parent: ethernet_control_top.engine
//   Children: none; this module is one synchronous control FSM
//
//   ethernet_control_transport request FIFOs
//                         |
//                         v
//              ethernet_control_engine
//                |        |         |
//                v        v         v
//          MiniDAQ regs  lpGBT IC  generic SCA command
//                |        |         |
//                +--------+---------+
//                         |
//                         v
//   ethernet_control_transport result FIFOs -> response serializers
//
// All request execution, endpoint handshakes, timeout counters, duplicate
// detection, and result generation use the 40 MHz control clock.
//
// Opcodes:
//   0x10 FPGA_WRITE, 0x11 FPGA_READ, 0x12 FPGA_REGISTER_RESET
//   0x20 LPGBT_WRITE, 0x21 LPGBT_READ
//   0x30 SCA_COMMAND, 0x31 SCA_CONNECT, 0x32 SCA_RESET
//
// The last exact request/result pair is cached.  A host retry with the same
// complete descriptor receives the cached response without repeating a write,
// reset pulse, SCA command, or IC transaction.
// FPGA writes use a 20-byte, big-endian payload; the host right-justifies
// smaller register values inside it.  Unlike the former UART command frame,
// the address and read selector do not overwrite any payload byte.

`timescale 1ns / 1ps

module ethernet_control_engine #(
    parameter integer UPLINK_COUNT = 4,
    parameter integer DOWNLINK_COUNT = 2,
    parameter integer SCA_COUNT = 4,
    parameter integer REPLY_TIMEOUT_CYCLES = 4_000_000
) (
    input  wire clk,
    input  wire rst,
    input  wire programming_active,

    input  wire [415:0] control_request,
    input  wire control_request_valid,
    output wire control_request_ready,
    input  wire [415:0] monitor_request,
    input  wire monitor_request_valid,
    output wire monitor_request_ready,

    output reg [511:0] control_result,
    output reg control_result_valid,
    input  wire control_result_ready,
    output reg [511:0] monitor_result,
    output reg monitor_result_valid,
    input  wire monitor_result_ready,

    // The register address and read selector are independent protocol fields;
    // they are not overlaid onto the 160-bit register write value.
    output reg [7:0] fpga_register_address,
    output reg [7:0] fpga_readback_selector,
    output reg [159:0] fpga_register_write_data,
    output reg fpga_register_write,
    output reg fpga_register_read,
    output reg fpga_register_reset,
    input  wire [159:0] fpga_readback_data,
    input  wire fpga_readback_valid,

    output reg [7:0] ic_gbtx_address [DOWNLINK_COUNT-1:0],
    output reg [15:0] ic_register_address [DOWNLINK_COUNT-1:0],
    output reg [7:0] ic_read_count [DOWNLINK_COUNT-1:0],
    output reg [DOWNLINK_COUNT-1:0] ic_start_write,
    output reg [DOWNLINK_COUNT-1:0] ic_start_read,
    output reg [7:0] ic_write_data [DOWNLINK_COUNT-1:0],
    output reg [DOWNLINK_COUNT-1:0] ic_write_enable,
    output reg [DOWNLINK_COUNT-1:0] ic_rx_reset,
    input  wire [UPLINK_COUNT-1:0] ic_rx_fifo_empty,
    input  wire [7:0] ic_rx_fifo_data [UPLINK_COUNT-1:0],
    output reg [UPLINK_COUNT-1:0] ic_rx_fifo_read,

    output reg generic_sca_active,
    output reg [1:0] generic_sca_target_csm,
    output reg [SCA_COUNT-1:0] generic_sca_enable,
    output reg generic_sca_start_reset,
    output reg generic_sca_start_connect,
    output reg generic_sca_start_command,
    output reg [7:0] generic_sca_address,
    output reg [7:0] generic_sca_transid,
    output reg [7:0] generic_sca_channel,
    output reg [7:0] generic_sca_command,
    output reg [31:0] generic_sca_data,
    input  wire [SCA_COUNT-1:0] sca_rx_done [DOWNLINK_COUNT-1:0],
    input  wire [7:0] sca_rx_address [DOWNLINK_COUNT-1:0][SCA_COUNT-1:0],
    input  wire [7:0] sca_rx_transid [DOWNLINK_COUNT-1:0][SCA_COUNT-1:0],
    input  wire [7:0] sca_rx_channel [DOWNLINK_COUNT-1:0][SCA_COUNT-1:0],
    input  wire [7:0] sca_rx_length [DOWNLINK_COUNT-1:0][SCA_COUNT-1:0],
    input  wire [7:0] sca_rx_error [DOWNLINK_COUNT-1:0][SCA_COUNT-1:0],
    input  wire [31:0] sca_rx_data [DOWNLINK_COUNT-1:0][SCA_COUNT-1:0]
);

    localparam [7:0] FPGA_WRITE = 8'h10;
    localparam [7:0] FPGA_READ = 8'h11;
    localparam [7:0] FPGA_RESET = 8'h12;
    localparam [7:0] LPGBT_WRITE = 8'h20;
    localparam [7:0] LPGBT_READ = 8'h21;
    localparam [7:0] SCA_COMMAND = 8'h30;
    localparam [7:0] SCA_CONNECT = 8'h31;
    localparam [7:0] SCA_RESET = 8'h32;

    localparam [7:0] STATUS_OK = 8'h00;
    localparam [7:0] STATUS_INVALID = 8'h01;
    localparam [7:0] STATUS_BUSY = 8'h02;
    localparam [7:0] STATUS_TIMEOUT = 8'h03;
    localparam [7:0] STATUS_OVERFLOW = 8'h04;

    localparam [4:0] IDLE = 5'd0;
    localparam [4:0] FPGA_WRITE_PULSE = 5'd1;
    localparam [4:0] FPGA_READ_PULSE = 5'd2;
    localparam [4:0] FPGA_READ_WAIT = 5'd3;
    localparam [4:0] FPGA_RESET_PULSE = 5'd4;
    localparam [4:0] IC_RESET_PULSE = 5'd5;
    localparam [4:0] IC_RESET_WAIT = 5'd6;
    localparam [4:0] IC_LOAD = 5'd7;
    localparam [4:0] IC_START = 5'd8;
    localparam [4:0] IC_WAIT = 5'd9;
    // The legacy IC RX FIFO registers its empty flag using the pre-increment
    // read pointer.  After its last available byte is consumed, empty remains
    // deasserted for one extra clock.  Spend that clock here before consulting
    // empty again so the Ethernet reader cannot overrun the two-bit IC decoder.
    localparam [4:0] IC_READ_GAP = 5'd10;
    localparam [4:0] IC_CAPTURE = 5'd11;
    localparam [4:0] SCA_WAIT_PROGRAM = 5'd12;
    localparam [4:0] SCA_START = 5'd13;
    localparam [4:0] SCA_WAIT = 5'd14;
    localparam [4:0] RESULT_WAIT = 5'd15;

    reg [4:0] state = IDLE;
    reg active_monitor = 1'b0;
    reg [415:0] active_request = 416'b0;
    reg [47:0] host_mac = 48'b0;
    reg [15:0] ethertype = 16'b0;
    reg [31:0] request_id = 32'b0;
    reg [7:0] opcode = 8'b0;
    reg [7:0] flags = 8'b0;
    reg [7:0] target = 8'b0;
    reg [7:0] subtarget = 8'b0;
    reg [7:0] data_len = 8'b0;
    reg [15:0] address = 16'b0;
    reg [7:0] transid = 8'b0;
    reg [7:0] channel = 8'b0;
    reg [7:0] sca_command = 8'b0;
    reg [7:0] sca_address = 8'b0;
    reg [31:0] argument = 32'b0;
    reg [159:0] payload = 160'b0;

    reg cache_valid = 1'b0;
    reg [415:0] cached_request = 416'b0;
    reg [511:0] cached_result = 512'b0;
    reg cached_monitor = 1'b0;

    reg [7:0] byte_count = 8'b0;
    reg [7:0] expected_reply_bytes = 8'b0;
    reg [7:0] reply_length_low = 8'b0;
    reg [287:0] reply_data = 288'b0;
    reg [SCA_COUNT-1:0] sca_expected = {SCA_COUNT{1'b0}};
    reg [SCA_COUNT-1:0] sca_received = {SCA_COUNT{1'b0}};
    reg [31:0] timeout_count = 32'b0;

    wire choose_control = control_request_valid;
    wire choose_monitor = !control_request_valid && monitor_request_valid;
    wire [415:0] chosen_request = choose_control
        ? control_request : monitor_request;
    assign control_request_ready = state == IDLE && !control_result_valid
                                 && !monitor_result_valid;
    assign monitor_request_ready = state == IDLE && !control_request_valid
                                 && !control_result_valid
                                 && !monitor_result_valid;

    task automatic publish_result;
        input [7:0] result_status;
        input [7:0] result_detail;
        input [7:0] result_length;
        input [287:0] result_data;
        reg [511:0] assembled;
        begin
            assembled = {
                host_mac, ethertype, request_id, opcode, result_status,
                target, subtarget, result_length, address, result_detail,
                result_data, 64'b0
            };
            if (active_monitor) begin
                monitor_result <= assembled;
                monitor_result_valid <= 1'b1;
            end else begin
                control_result <= assembled;
                control_result_valid <= 1'b1;
            end
            cached_request <= active_request;
            cached_result <= assembled;
            cached_monitor <= active_monitor;
            cache_valid <= 1'b1;
            state <= RESULT_WAIT;
        end
    endtask

    integer d;
    integer s;
    integer temp_count;
    reg [287:0] temp_reply;
    reg [SCA_COUNT-1:0] temp_received;
    reg [7:0] first_sca_error;

    always @(posedge clk) begin
        fpga_register_write <= 1'b0;
        fpga_register_read <= 1'b0;
        fpga_register_reset <= 1'b0;
        ic_start_write <= {DOWNLINK_COUNT{1'b0}};
        ic_start_read <= {DOWNLINK_COUNT{1'b0}};
        ic_write_enable <= {DOWNLINK_COUNT{1'b0}};
        ic_rx_reset <= {DOWNLINK_COUNT{1'b0}};
        ic_rx_fifo_read <= {UPLINK_COUNT{1'b0}};
        generic_sca_start_reset <= 1'b0;
        generic_sca_start_connect <= 1'b0;
        generic_sca_start_command <= 1'b0;

        if (rst) begin
            state <= IDLE;
            control_result_valid <= 1'b0;
            monitor_result_valid <= 1'b0;
            generic_sca_active <= 1'b0;
            cache_valid <= 1'b0;
            fpga_register_address <= 8'b0;
            fpga_readback_selector <= 8'b0;
            fpga_register_write_data <= 160'b0;
            for (d = 0; d < DOWNLINK_COUNT; d = d + 1) begin
                ic_gbtx_address[d] <= 8'b0;
                ic_register_address[d] <= 16'b0;
                ic_read_count[d] <= 8'b0;
                ic_write_data[d] <= 8'b0;
            end
        end else begin
            case (state)
                IDLE: begin
                    generic_sca_active <= 1'b0;
                    timeout_count <= 32'b0;
                    if (choose_control || choose_monitor) begin
                        active_monitor <= choose_monitor;
                        active_request <= chosen_request;
                        host_mac <= chosen_request[415:368];
                        ethertype <= chosen_request[367:352];
                        request_id <= chosen_request[351:320];
                        opcode <= chosen_request[319:312];
                        flags <= chosen_request[311:304];
                        target <= chosen_request[303:296];
                        subtarget <= chosen_request[295:288];
                        data_len <= chosen_request[287:280];
                        address <= chosen_request[279:264];
                        transid <= chosen_request[263:256];
                        channel <= chosen_request[255:248];
                        sca_command <= chosen_request[247:240];
                        sca_address <= chosen_request[239:232];
                        argument <= chosen_request[231:200];
                        payload <= chosen_request[199:40];
                        fpga_register_address
                            <= chosen_request[271:264];
                        fpga_readback_selector
                            <= chosen_request[295:288];
                        fpga_register_write_data
                            <= chosen_request[199:40];

                        if (cache_valid && chosen_request == cached_request) begin
                            if (cached_monitor) begin
                                monitor_result <= cached_result;
                                monitor_result_valid <= 1'b1;
                            end else begin
                                control_result <= cached_result;
                                control_result_valid <= 1'b1;
                            end
                            state <= RESULT_WAIT;
                        end else begin
                            case (chosen_request[319:312])
                                FPGA_WRITE: state <= choose_monitor
                                    ? RESULT_WAIT : FPGA_WRITE_PULSE;
                                FPGA_READ: state <= choose_monitor
                                    ? FPGA_READ_PULSE : RESULT_WAIT;
                                FPGA_RESET: state <= choose_monitor
                                    ? RESULT_WAIT : FPGA_RESET_PULSE;
                                LPGBT_WRITE: state <= choose_monitor
                                    ? RESULT_WAIT : IC_RESET_PULSE;
                                LPGBT_READ: state <= choose_monitor
                                    ? IC_RESET_PULSE : RESULT_WAIT;
                                SCA_COMMAND, SCA_CONNECT, SCA_RESET:
                                    state <= SCA_WAIT_PROGRAM;
                                default: state <= RESULT_WAIT;
                            endcase
                        end
                    end
                end

                FPGA_WRITE_PULSE: begin
                    if (address[15:8] != 0 || data_len != 8'd20) begin
                        publish_result(STATUS_INVALID, 8'b0, 8'b0, 288'b0);
                    end else begin
                        fpga_register_address <= address[7:0];
                        fpga_register_write_data <= payload;
                        fpga_register_write <= 1'b1;
                        publish_result(STATUS_OK, 8'b0, 8'b0, 288'b0);
                    end
                end
                FPGA_READ_PULSE: begin
                    if (address[15:8] != 0 || data_len != 0) begin
                        publish_result(STATUS_INVALID, 8'b0, 8'b0, 288'b0);
                    end else begin
                        fpga_register_address <= address[7:0];
                        fpga_readback_selector <= subtarget;
                        fpga_register_read <= 1'b1;
                        timeout_count <= 32'b0;
                        state <= FPGA_READ_WAIT;
                    end
                end
                FPGA_READ_WAIT: begin
                    if (fpga_readback_valid) begin
                        publish_result(STATUS_OK, 8'b0, 8'd20,
                            {fpga_readback_data, 128'b0});
                    end else if (timeout_count >= REPLY_TIMEOUT_CYCLES-1) begin
                        publish_result(STATUS_TIMEOUT, 8'b0, 8'b0, 288'b0);
                    end else timeout_count <= timeout_count + 1'b1;
                end
                FPGA_RESET_PULSE: begin
                    fpga_register_reset <= 1'b1;
                    publish_result(STATUS_OK, 8'b0, 8'b0, 288'b0);
                end

                IC_RESET_PULSE: begin
                    if (target >= UPLINK_COUNT || data_len > 8'd15
                        || (opcode == LPGBT_WRITE && data_len == 0)
                        || (opcode == LPGBT_READ
                            && (argument[15:8] == 0
                                || argument[15:8] > 15))) begin
                        publish_result(STATUS_INVALID, 8'b0, 8'b0, 288'b0);
                    end else begin
                        ic_rx_reset[target[7:1]] <= 1'b1;
                        ic_gbtx_address[target[7:1]] <= argument[7:0];
                        ic_register_address[target[7:1]] <= address;
                        ic_read_count[target[7:1]] <= (opcode == LPGBT_READ)
                            ? argument[15:8] : data_len;
                        byte_count <= 8'b0;
                        expected_reply_bytes <= 8'b0;
                        reply_length_low <= 8'b0;
                        reply_data <= 288'b0;
                        timeout_count <= 32'b0;
                        state <= IC_RESET_WAIT;
                    end
                end
                IC_RESET_WAIT: begin
                    // Keep reset separate from TX FIFO writes/start strobes.
                    if (opcode == LPGBT_WRITE) begin
                        ic_write_data[target[7:1]] <= payload[159 -: 8];
                        // Present the first byte and WR_EN for a complete
                        // cycle before the IC TX FIFO samples them.
                        ic_write_enable[target[7:1]] <= 1'b1;
                        state <= IC_LOAD;
                    end else state <= IC_START;
                end
                IC_LOAD: begin
                    // The byte currently on ic_write_data was accepted at
                    // this edge. Keep WR_EN asserted only when another byte
                    // must be presented for the following edge.
                    if (byte_count + 1'b1 >= data_len) begin
                        byte_count <= 8'b0;
                        state <= IC_START;
                    end else begin
                        byte_count <= byte_count + 1'b1;
                        ic_write_enable[target[7:1]] <= 1'b1;
                        ic_write_data[target[7:1]]
                            <= payload[159 - (byte_count + 1'b1)*8 -: 8];
                    end
                end
                IC_START: begin
                    if (opcode == LPGBT_WRITE)
                        ic_start_write[target[7:1]] <= 1'b1;
                    else
                        ic_start_read[target[7:1]] <= 1'b1;
                    timeout_count <= 32'b0;
                    state <= IC_WAIT;
                end
                IC_WAIT: begin
                    if (!ic_rx_fifo_empty[target]) begin
                        ic_rx_fifo_read[target] <= 1'b1;
                        state <= IC_CAPTURE;
                    end else if (timeout_count >= REPLY_TIMEOUT_CYCLES-1) begin
                        publish_result(STATUS_TIMEOUT, 8'b0, byte_count,
                            reply_data);
                    end else timeout_count <= timeout_count + 1'b1;
                end
                IC_CAPTURE: begin
                    if (byte_count < 8'd36) begin
                        reply_data[287 - byte_count*8 -: 8]
                            <= ic_rx_fifo_data[target];
                        // The gbt-sc IC deserializer removes the 0x7E HDLC
                        // delimiters.  Its FIFO therefore starts with the
                        // lpGBT address byte, followed by status, the
                        // little-endian data count, register address, data,
                        // and parity.  There is no delimiter/prefix byte in
                        // this interface.
                        if (byte_count == 8'd2)
                            reply_length_low <= ic_rx_fifo_data[target];
                        if (byte_count == 8'd3) begin
                            if (ic_rx_fifo_data[target] != 0
                                || reply_length_low > 8'd15) begin
                                temp_reply = reply_data;
                                temp_reply[287 - byte_count*8 -: 8]
                                    = ic_rx_fifo_data[target];
                                publish_result(STATUS_OVERFLOW, 8'b0,
                                    byte_count + 1'b1, temp_reply);
                            end else begin
                                expected_reply_bytes <= 8'd7
                                    + reply_length_low;
                                state <= IC_READ_GAP;
                            end
                        end else begin
                            state <= IC_READ_GAP;
                        end
                        byte_count <= byte_count + 1'b1;
                        timeout_count <= 32'b0;
                        temp_reply = reply_data;
                        temp_reply[287 - byte_count*8 -: 8]
                            = ic_rx_fifo_data[target];
                        if (expected_reply_bytes != 0
                            && byte_count + 1'b1 >= expected_reply_bytes) begin
                            publish_result(STATUS_OK, 8'b0,
                                byte_count + 1'b1,
                                temp_reply);
                        end
                    end else begin
                        publish_result(STATUS_OVERFLOW, 8'b0, 8'd36,
                            reply_data);
                    end
                end
                IC_READ_GAP: begin
                    // Do not inspect ic_rx_fifo_empty in this cycle.  It still
                    // describes the FIFO occupancy from before the preceding
                    // read pointer increment.
                    state <= IC_WAIT;
                end

                SCA_WAIT_PROGRAM: begin
                    if (target >= DOWNLINK_COUNT
                        || subtarget[SCA_COUNT-1:0] == 0) begin
                        publish_result(STATUS_INVALID, 8'b0, 8'b0, 288'b0);
                    end else if (!programming_active) begin
                        generic_sca_active <= 1'b1;
                        generic_sca_target_csm <= target[1:0];
                        generic_sca_enable <= subtarget[SCA_COUNT-1:0];
                        generic_sca_address <= sca_address;
                        generic_sca_transid <= transid;
                        generic_sca_channel <= channel;
                        generic_sca_command <= sca_command;
                        generic_sca_data <= argument;
                        sca_expected <= subtarget[SCA_COUNT-1:0];
                        sca_received <= {SCA_COUNT{1'b0}};
                        reply_data <= 288'b0;
                        byte_count <= 8'b0;
                        timeout_count <= 32'b0;
                        state <= SCA_START;
                    end else if (timeout_count >= REPLY_TIMEOUT_CYCLES-1) begin
                        publish_result(STATUS_BUSY, 8'b0, 8'b0, 288'b0);
                    end else timeout_count <= timeout_count + 1'b1;
                end
                SCA_START: begin
                    if (opcode == SCA_RESET)
                        generic_sca_start_reset <= 1'b1;
                    else if (opcode == SCA_CONNECT)
                        generic_sca_start_connect <= 1'b1;
                    else
                        generic_sca_start_command <= 1'b1;
                    state <= SCA_WAIT;
                end
                SCA_WAIT: begin
                    temp_reply = reply_data;
                    temp_received = sca_received;
                    temp_count = byte_count;
                    first_sca_error = 8'b0;
                    for (s = 0; s < SCA_COUNT; s = s + 1) begin
                        if (sca_rx_done[target][s] && sca_expected[s]
                            && !temp_received[s] && temp_count <= 27) begin
                            temp_reply[287 - temp_count*8 -: 72] = {
                                sca_rx_address[target][s],
                                sca_rx_transid[target][s],
                                sca_rx_channel[target][s],
                                sca_rx_error[target][s],
                                sca_rx_length[target][s],
                                sca_rx_data[target][s]
                            };
                            if (first_sca_error == 0
                                && sca_rx_error[target][s] != 0)
                                first_sca_error = sca_rx_error[target][s];
                            temp_count = temp_count + 9;
                            temp_received[s] = 1'b1;
                        end
                    end
                    reply_data <= temp_reply;
                    byte_count <= temp_count[7:0];
                    sca_received <= temp_received;
                    if ((temp_received & sca_expected) == sca_expected) begin
                        generic_sca_active <= 1'b0;
                        publish_result(STATUS_OK, first_sca_error,
                            temp_count[7:0], temp_reply);
                    end else if (timeout_count >= REPLY_TIMEOUT_CYCLES-1) begin
                        generic_sca_active <= 1'b0;
                        publish_result(STATUS_TIMEOUT, 8'b0,
                            temp_count[7:0], temp_reply);
                    end else timeout_count <= timeout_count + 1'b1;
                end

                RESULT_WAIT: begin
                    // Wrong traffic-class/opcode combinations and unknown
                    // opcodes reach this state without a published result.
                    if (!control_result_valid && !monitor_result_valid
                        && !(cache_valid && active_request == cached_request))
                        publish_result(STATUS_INVALID, 8'b0, 8'b0, 288'b0);
                    else if ((control_result_valid && control_result_ready)
                          || (monitor_result_valid && monitor_result_ready)) begin
                        control_result_valid <= 1'b0;
                        monitor_result_valid <= 1'b0;
                        state <= IDLE;
                    end
                end
                default: state <= IDLE;
            endcase
        end
    end

endmodule
