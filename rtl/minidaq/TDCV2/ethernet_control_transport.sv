// Raw-Ethernet control/monitor parser and four independent CDC FIFOs.
//
// Hierarchy and clock crossings:
//
//   Parent: ethernet_control_top.transport
//   Children: four xpm_fifo_async instances
//
//   TEMAC RX, 125 MHz
//          |
//          +-- MDC1 parser -> control-request FIFO --+
//          +-- MDM1 parser -> monitor-request FIFO --+--> 40 MHz engine
//                                                       
//   TEMAC TX, 125 MHz                                  40 MHz engine
//          ^                                                 |
//          +-- control-result FIFO <-------------------------+
//          +-- monitor-result FIFO <-------------------------+
//
// The parser consumes every received frame so it can share a lossless RX fork
// with the MDJ1 programming parser. Only matching protocol frames are written
// into a request FIFO. This module does not execute commands or serialize the
// resulting Ethernet response frames.
//
// Requests with magic "MDC1"/EtherType 0x88B5 enter the control request
// FIFO.  Requests with magic "MDM1"/EtherType 0x88B6 enter the monitor
// request FIFO.  Results cross back through matching, physically separate
// FIFOs.  Unrelated Ethernet frames (including MDJ1 programming frames and
// 0x0068 hit traffic) are consumed without generating a reply.
//
// Request wire format, network byte order:
//   0..13  Ethernet header
//   14..17 "MDC1" or "MDM1"
//   18     version (2; readback pages contain no UART metadata bytes)
//   19     opcode
//   20     flags
//   21     target (uplink or CSM)
//   22     subtarget (SCA mask/index or readback selector)
//   23     payload byte count, 0..20
//   24..27 request ID
//   28..29 register address
//   30     SCA transaction ID
//   31     SCA channel
//   32     SCA command
//   33     SCA address
//   34..37 32-bit argument
//   38..39 reserved
//   40..59 optional payload and Ethernet padding

`timescale 1ns / 1ps

module ethernet_control_transport #(
    parameter logic [47:0] FPGA_MAC = 48'h020000C70501,
    parameter logic [15:0] CONTROL_ETHERTYPE = 16'h88B5,
    parameter logic [15:0] MONITOR_ETHERTYPE = 16'h88B6
) (
    input  wire         rx_clk,
    input  wire         rx_resetn,
    input  wire [7:0]   rx_tdata,
    input  wire         rx_tvalid,
    output wire         rx_tready,
    input  wire         rx_tlast,

    input  wire         control_clk,
    input  wire         control_reset,
    output wire [415:0] control_request,
    output wire         control_request_valid,
    input  wire         control_request_ready,
    output wire [415:0] monitor_request,
    output wire         monitor_request_valid,
    input  wire         monitor_request_ready,

    input  wire [511:0] control_result,
    input  wire         control_result_valid,
    output wire         control_result_ready,
    input  wire [511:0] monitor_result,
    input  wire         monitor_result_valid,
    output wire         monitor_result_ready,

    input  wire         tx_clk,
    input  wire         tx_reset,
    output wire [511:0] control_response,
    output wire         control_response_valid,
    input  wire         control_response_ready,
    output wire [511:0] monitor_response,
    output wire         monitor_response_valid,
    input  wire         monitor_response_ready,

    output wire         control_request_fifo_full,
    output wire         monitor_request_fifo_full,
    output wire         control_result_fifo_full,
    output wire         monitor_result_fifo_full
);

    localparam logic [31:0] CONTROL_MAGIC = 32'h4D444331; // "MDC1"
    localparam logic [31:0] MONITOR_MAGIC = 32'h4D444D31; // "MDM1"
    localparam logic [7:0] VERSION = 8'h02;

    reg [6:0] frame_index = 7'd0;
    reg [47:0] destination_mac = 48'b0;
    reg [47:0] source_mac = 48'b0;
    reg [15:0] frame_ethertype = 16'b0;
    reg [31:0] frame_magic = 32'b0;
    reg [7:0] frame_version = 8'b0;
    reg [7:0] frame_opcode = 8'b0;
    reg [7:0] frame_flags = 8'b0;
    reg [7:0] frame_target = 8'b0;
    reg [7:0] frame_subtarget = 8'b0;
    reg [7:0] frame_data_len = 8'b0;
    reg [31:0] frame_request_id = 32'b0;
    reg [15:0] frame_address = 16'b0;
    reg [7:0] frame_transid = 8'b0;
    reg [7:0] frame_channel = 8'b0;
    reg [7:0] frame_command = 8'b0;
    reg [7:0] frame_sca_address = 8'b0;
    reg [31:0] frame_argument = 32'b0;
    reg [159:0] frame_payload = 160'b0;

    reg control_request_wr_en = 1'b0;
    reg monitor_request_wr_en = 1'b0;
    wire control_request_wr_busy;
    wire monitor_request_wr_busy;

    // This observer never backpressures TEMAC.  If its small class-specific
    // FIFO is full, only that request is dropped; the host retransmits the
    // same request ID.  This also prevents monitoring from blocking a large
    // programming frame being consumed by the parallel MDJ1 parser.
    assign rx_tready = 1'b1;
    wire rx_fire = rx_tvalid;

    wire frame_is_control =
        (destination_mac == FPGA_MAC || destination_mac == 48'hFFFFFFFFFFFF)
        && frame_ethertype == CONTROL_ETHERTYPE
        && frame_magic == CONTROL_MAGIC
        && frame_version == VERSION
        && frame_data_len <= 8'd20;
    wire frame_is_monitor =
        (destination_mac == FPGA_MAC || destination_mac == 48'hFFFFFFFFFFFF)
        && frame_ethertype == MONITOR_ETHERTYPE
        && frame_magic == MONITOR_MAGIC
        && frame_version == VERSION
        && frame_data_len <= 8'd20;

    // The FIFO samples DIN on the same edge as WR_EN. Build the completed
    // descriptor directly from the frame registers so that the first request
    // after reset cannot capture a preceding descriptor value.
    wire [415:0] completed_request = {
        source_mac, frame_ethertype, frame_request_id,
        frame_opcode, frame_flags, frame_target, frame_subtarget,
        frame_data_len, frame_address, frame_transid,
        frame_channel, frame_command, frame_sca_address,
        frame_argument,
        (frame_index == 7'd59
            ? {frame_payload[151:0], rx_tdata}
            : frame_payload),
        40'b0
    };

    always @(posedge rx_clk) begin
        control_request_wr_en <= 1'b0;
        monitor_request_wr_en <= 1'b0;

        if (!rx_resetn) begin
            frame_index <= 7'd0;
            destination_mac <= 48'b0;
            source_mac <= 48'b0;
            frame_ethertype <= 16'b0;
            frame_magic <= 32'b0;
            frame_payload <= 160'b0;
        end else if (rx_fire) begin
            if (frame_index == 7'd0) begin
                destination_mac <= 48'b0;
                source_mac <= 48'b0;
                frame_ethertype <= 16'b0;
                frame_magic <= 32'b0;
                frame_version <= 8'b0;
                frame_opcode <= 8'b0;
                frame_flags <= 8'b0;
                frame_target <= 8'b0;
                frame_subtarget <= 8'b0;
                frame_data_len <= 8'b0;
                frame_request_id <= 32'b0;
                frame_address <= 16'b0;
                frame_transid <= 8'b0;
                frame_channel <= 8'b0;
                frame_command <= 8'b0;
                frame_sca_address <= 8'b0;
                frame_argument <= 32'b0;
                frame_payload <= 160'b0;
            end

            case (frame_index)
                0,1,2,3,4,5:
                    destination_mac <= {destination_mac[39:0], rx_tdata};
                6,7,8,9,10,11:
                    source_mac <= {source_mac[39:0], rx_tdata};
                12,13:
                    frame_ethertype <= {frame_ethertype[7:0], rx_tdata};
                14,15,16,17:
                    frame_magic <= {frame_magic[23:0], rx_tdata};
                18: frame_version <= rx_tdata;
                19: frame_opcode <= rx_tdata;
                20: frame_flags <= rx_tdata;
                21: frame_target <= rx_tdata;
                22: frame_subtarget <= rx_tdata;
                23: frame_data_len <= rx_tdata;
                24,25,26,27:
                    frame_request_id <= {frame_request_id[23:0], rx_tdata};
                28,29: frame_address <= {frame_address[7:0], rx_tdata};
                30: frame_transid <= rx_tdata;
                31: frame_channel <= rx_tdata;
                32: frame_command <= rx_tdata;
                33: frame_sca_address <= rx_tdata;
                34,35,36,37:
                    frame_argument <= {frame_argument[23:0], rx_tdata};
                40,41,42,43,44,45,46,47,48,49,
                50,51,52,53,54,55,56,57,58,59:
                    frame_payload <= {frame_payload[151:0], rx_tdata};
                default: begin end
            endcase

            if (rx_tlast) begin
                // All protocol fields precede the mandatory byte-59 padding,
                // so their registered values are complete at normal TLAST.
                if (frame_is_control && !control_request_fifo_full
                    && !control_request_wr_busy)
                    control_request_wr_en <= 1'b1;
                else if (frame_is_monitor && !monitor_request_fifo_full
                         && !monitor_request_wr_busy)
                    monitor_request_wr_en <= 1'b1;
                frame_index <= 7'd0;
            end else begin
                frame_index <= frame_index + 1'b1;
            end
        end
    end

    wire control_request_empty;
    wire monitor_request_empty;
    wire control_request_rd_busy;
    wire monitor_request_rd_busy;

    xpm_fifo_async #(
        .CDC_SYNC_STAGES(2), .DOUT_RESET_VALUE("0"),
        .ECC_MODE("no_ecc"), .FIFO_MEMORY_TYPE("distributed"),
        .FIFO_READ_LATENCY(0), .FIFO_WRITE_DEPTH(16),
        .FULL_RESET_VALUE(0), .PROG_EMPTY_THRESH(2),
        .PROG_FULL_THRESH(14), .RD_DATA_COUNT_WIDTH(1),
        .READ_DATA_WIDTH(416), .READ_MODE("fwft"),
        .RELATED_CLOCKS(0), .SIM_ASSERT_CHK(1),
        .USE_ADV_FEATURES("0000"), .WAKEUP_TIME(0),
        .WRITE_DATA_WIDTH(416), .WR_DATA_COUNT_WIDTH(1)
    ) control_request_fifo (
        .din(completed_request), .wr_en(control_request_wr_en),
        .wr_clk(rx_clk), .full(control_request_fifo_full),
        .wr_rst_busy(control_request_wr_busy), .dout(control_request),
        .empty(control_request_empty),
        .rd_en(control_request_valid && control_request_ready),
        .rd_clk(control_clk), .rd_rst_busy(control_request_rd_busy),
        .rst(~rx_resetn | control_reset), .sleep(1'b0),
        .injectdbiterr(1'b0), .injectsbiterr(1'b0),
        .almost_empty(), .almost_full(), .data_valid(), .dbiterr(),
        .overflow(), .prog_empty(), .prog_full(), .rd_data_count(),
        .sbiterr(), .underflow(), .wr_ack(), .wr_data_count()
    );
    assign control_request_valid = ~control_request_empty
                                 && ~control_request_rd_busy;

    xpm_fifo_async #(
        .CDC_SYNC_STAGES(2), .DOUT_RESET_VALUE("0"),
        .ECC_MODE("no_ecc"), .FIFO_MEMORY_TYPE("distributed"),
        .FIFO_READ_LATENCY(0), .FIFO_WRITE_DEPTH(16),
        .FULL_RESET_VALUE(0), .PROG_EMPTY_THRESH(2),
        .PROG_FULL_THRESH(14), .RD_DATA_COUNT_WIDTH(1),
        .READ_DATA_WIDTH(416), .READ_MODE("fwft"),
        .RELATED_CLOCKS(0), .SIM_ASSERT_CHK(1),
        .USE_ADV_FEATURES("0000"), .WAKEUP_TIME(0),
        .WRITE_DATA_WIDTH(416), .WR_DATA_COUNT_WIDTH(1)
    ) monitor_request_fifo (
        .din(completed_request), .wr_en(monitor_request_wr_en),
        .wr_clk(rx_clk), .full(monitor_request_fifo_full),
        .wr_rst_busy(monitor_request_wr_busy), .dout(monitor_request),
        .empty(monitor_request_empty),
        .rd_en(monitor_request_valid && monitor_request_ready),
        .rd_clk(control_clk), .rd_rst_busy(monitor_request_rd_busy),
        .rst(~rx_resetn | control_reset), .sleep(1'b0),
        .injectdbiterr(1'b0), .injectsbiterr(1'b0),
        .almost_empty(), .almost_full(), .data_valid(), .dbiterr(),
        .overflow(), .prog_empty(), .prog_full(), .rd_data_count(),
        .sbiterr(), .underflow(), .wr_ack(), .wr_data_count()
    );
    assign monitor_request_valid = ~monitor_request_empty
                                 && ~monitor_request_rd_busy;

    wire control_result_empty;
    wire monitor_result_empty;
    wire control_result_wr_busy;
    wire monitor_result_wr_busy;
    wire control_result_rd_busy;
    wire monitor_result_rd_busy;

    xpm_fifo_async #(
        .CDC_SYNC_STAGES(2), .DOUT_RESET_VALUE("0"),
        .ECC_MODE("no_ecc"), .FIFO_MEMORY_TYPE("distributed"),
        .FIFO_READ_LATENCY(0), .FIFO_WRITE_DEPTH(16),
        .FULL_RESET_VALUE(0), .PROG_EMPTY_THRESH(2),
        .PROG_FULL_THRESH(14), .RD_DATA_COUNT_WIDTH(1),
        .READ_DATA_WIDTH(512), .READ_MODE("fwft"),
        .RELATED_CLOCKS(0), .SIM_ASSERT_CHK(1),
        .USE_ADV_FEATURES("0000"), .WAKEUP_TIME(0),
        .WRITE_DATA_WIDTH(512), .WR_DATA_COUNT_WIDTH(1)
    ) control_result_fifo (
        .din(control_result),
        .wr_en(control_result_valid && control_result_ready),
        .wr_clk(control_clk), .full(control_result_fifo_full),
        .wr_rst_busy(control_result_wr_busy), .dout(control_response),
        .empty(control_result_empty),
        .rd_en(control_response_valid && control_response_ready),
        .rd_clk(tx_clk), .rd_rst_busy(control_result_rd_busy),
        .rst(control_reset | tx_reset), .sleep(1'b0),
        .injectdbiterr(1'b0), .injectsbiterr(1'b0),
        .almost_empty(), .almost_full(), .data_valid(), .dbiterr(),
        .overflow(), .prog_empty(), .prog_full(), .rd_data_count(),
        .sbiterr(), .underflow(), .wr_ack(), .wr_data_count()
    );
    assign control_result_ready = ~control_result_fifo_full
                                && ~control_result_wr_busy;
    assign control_response_valid = ~control_result_empty
                                  && ~control_result_rd_busy;

    xpm_fifo_async #(
        .CDC_SYNC_STAGES(2), .DOUT_RESET_VALUE("0"),
        .ECC_MODE("no_ecc"), .FIFO_MEMORY_TYPE("distributed"),
        .FIFO_READ_LATENCY(0), .FIFO_WRITE_DEPTH(16),
        .FULL_RESET_VALUE(0), .PROG_EMPTY_THRESH(2),
        .PROG_FULL_THRESH(14), .RD_DATA_COUNT_WIDTH(1),
        .READ_DATA_WIDTH(512), .READ_MODE("fwft"),
        .RELATED_CLOCKS(0), .SIM_ASSERT_CHK(1),
        .USE_ADV_FEATURES("0000"), .WAKEUP_TIME(0),
        .WRITE_DATA_WIDTH(512), .WR_DATA_COUNT_WIDTH(1)
    ) monitor_result_fifo (
        .din(monitor_result),
        .wr_en(monitor_result_valid && monitor_result_ready),
        .wr_clk(control_clk), .full(monitor_result_fifo_full),
        .wr_rst_busy(monitor_result_wr_busy), .dout(monitor_response),
        .empty(monitor_result_empty),
        .rd_en(monitor_response_valid && monitor_response_ready),
        .rd_clk(tx_clk), .rd_rst_busy(monitor_result_rd_busy),
        .rst(control_reset | tx_reset), .sleep(1'b0),
        .injectdbiterr(1'b0), .injectsbiterr(1'b0),
        .almost_empty(), .almost_full(), .data_valid(), .dbiterr(),
        .overflow(), .prog_empty(), .prog_full(), .rd_data_count(),
        .sbiterr(), .underflow(), .wr_ack(), .wr_data_count()
    );
    assign monitor_result_ready = ~monitor_result_fifo_full
                                && ~monitor_result_wr_busy;
    assign monitor_response_valid = ~monitor_result_empty
                                  && ~monitor_result_rd_busy;

endmodule
