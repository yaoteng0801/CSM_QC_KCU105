// Builds minimum-size raw Ethernet response frames for the programming
// protocol.
//
// Hierarchy and interfaces:
//
//   Parent: ethernet_sca_jtag_top.ack_tx
//   Children: none; this module is one descriptor latch and byte serializer
//
//   ethernet_jtag_transport response descriptor
//                         |
//                         v
//            ethernet_program_ack_tx
//                         |
//                         v
//   minidaq_ethernet_subsystem.control_class_arbiter -> final TX QoS -> TEMAC
//
// The module runs entirely on the 125 MHz TEMAC TX clock. It knows nothing
// about hit or monitoring traffic; the parent subsystem performs arbitration.
//
// One 256-bit response descriptor is accepted while the module is idle and is
// converted into a 60-byte AXI-Stream frame.  Sixty bytes is the minimum
// Ethernet frame size measured from destination MAC through payload, excluding
// the four-byte FCS.  The TEMAC adds the preamble, SFD and FCS.
//
// The descriptor is latched before transmission, so every field remains stable
// if the TEMAC applies backpressure.  byte_index advances only on a successful
// TVALID/TREADY transfer and TLAST marks byte 59.

`timescale 1ns / 1ps

module ethernet_program_ack_tx #(
    parameter logic [15:0] PROGRAM_ETHERTYPE = 16'h88B5,
    parameter logic [47:0] FPGA_MAC          = 48'h020000C70501
) (
    // TEMAC 125 MHz user-transmit clock domain.
    input  wire         clk,
    input  wire         rst,

    // Response-descriptor ready/valid handshake from ethernet_jtag_transport.
    input  wire [255:0] response_descriptor,
    input  wire         response_valid,
    output wire         response_ready,

    // Byte-wide AXI-Stream frame presented to the TX frame arbiter.
    output reg  [7:0]   tx_tdata = 8'b0,
    output reg          tx_tvalid = 1'b0,
    input  wire         tx_tready,
    output reg          tx_tlast = 1'b0
);

    localparam logic [31:0] PROTOCOL_MAGIC = 32'h4D444A31; // "MDJ1"
    localparam logic [7:0] PROTOCOL_VERSION = 8'h01;
    localparam integer FRAME_BYTES = 60; // 14-byte header + 46-byte payload

    // active owns one complete frame.  response_ready is low from the moment
    // its descriptor is captured until the final byte is accepted.
    reg active = 1'b0;
    reg [5:0] byte_index = 6'b0;
    reg [255:0] response_latched = 256'b0;

    // Descriptor layout:
    //   [255:208] destination/host MAC
    //   [207:176] programming session ID
    //   [175:144] sequence being acknowledged
    //   [143:112] next sequence expected by the FPGA
    //   [111:80]  committed bit-file byte offset, or captured FPGA IR[5:0]
    //             for a standalone IDCODE_ACK
    //   [79:48]   result data: rolling CRC32 or standalone FPGA IDCODE
    //   [47:40]   RX/SCA/IDCODE ACK or NACK message type
    //   [39:32]   status
    //   [31:24]   target CSM/downlink
    //   [23:16]   target SCA
    //   [15:8]    failed SCA command
    //   [7:0]     detailed error
    wire [47:0] destination_mac = response_latched[255:208];
    wire [31:0] session_id      = response_latched[207:176];
    wire [31:0] sequence_number = response_latched[175:144];
    wire [31:0] expected_seq    = response_latched[143:112];
    wire [31:0] completed_offset= response_latched[111:80];
    wire [31:0] rolling_crc     = response_latched[79:48];
    wire [7:0] message_type     = response_latched[47:40];
    wire [7:0] status           = response_latched[39:32];
    wire [7:0] target_csm       = response_latched[31:24];
    wire [7:0] target_sca       = response_latched[23:16];
    wire [7:0] failed_command   = response_latched[15:8];
    wire [7:0] error_code       = response_latched[7:0];

    assign response_ready = ~active;

    // Combinational byte serializer.  The first fourteen bytes are the raw
    // Ethernet header.  Protocol fields use network byte order (big endian).
    always @(*) begin
        tx_tdata = 8'b0;
        tx_tvalid = active;
        tx_tlast = active && (byte_index == FRAME_BYTES-1);

        case (byte_index)
            6'd0:  tx_tdata = destination_mac[47:40];
            6'd1:  tx_tdata = destination_mac[39:32];
            6'd2:  tx_tdata = destination_mac[31:24];
            6'd3:  tx_tdata = destination_mac[23:16];
            6'd4:  tx_tdata = destination_mac[15:8];
            6'd5:  tx_tdata = destination_mac[7:0];
            6'd6:  tx_tdata = FPGA_MAC[47:40];
            6'd7:  tx_tdata = FPGA_MAC[39:32];
            6'd8:  tx_tdata = FPGA_MAC[31:24];
            6'd9:  tx_tdata = FPGA_MAC[23:16];
            6'd10: tx_tdata = FPGA_MAC[15:8];
            6'd11: tx_tdata = FPGA_MAC[7:0];
            6'd12: tx_tdata = PROGRAM_ETHERTYPE[15:8];
            6'd13: tx_tdata = PROGRAM_ETHERTYPE[7:0];

            6'd14: tx_tdata = PROTOCOL_MAGIC[31:24];
            6'd15: tx_tdata = PROTOCOL_MAGIC[23:16];
            6'd16: tx_tdata = PROTOCOL_MAGIC[15:8];
            6'd17: tx_tdata = PROTOCOL_MAGIC[7:0];
            6'd18: tx_tdata = PROTOCOL_VERSION;
            6'd19: tx_tdata = message_type;
            6'd20: tx_tdata = status;
            6'd21: tx_tdata = target_csm;
            6'd22: tx_tdata = target_sca;
            6'd23: tx_tdata = failed_command;
            6'd24: tx_tdata = error_code;
            6'd25: tx_tdata = 8'b0;

            6'd26: tx_tdata = session_id[31:24];
            6'd27: tx_tdata = session_id[23:16];
            6'd28: tx_tdata = session_id[15:8];
            6'd29: tx_tdata = session_id[7:0];
            6'd30: tx_tdata = sequence_number[31:24];
            6'd31: tx_tdata = sequence_number[23:16];
            6'd32: tx_tdata = sequence_number[15:8];
            6'd33: tx_tdata = sequence_number[7:0];
            6'd34: tx_tdata = expected_seq[31:24];
            6'd35: tx_tdata = expected_seq[23:16];
            6'd36: tx_tdata = expected_seq[15:8];
            6'd37: tx_tdata = expected_seq[7:0];
            6'd38: tx_tdata = completed_offset[31:24];
            6'd39: tx_tdata = completed_offset[23:16];
            6'd40: tx_tdata = completed_offset[15:8];
            6'd41: tx_tdata = completed_offset[7:0];
            6'd42: tx_tdata = rolling_crc[31:24];
            6'd43: tx_tdata = rolling_crc[23:16];
            6'd44: tx_tdata = rolling_crc[15:8];
            6'd45: tx_tdata = rolling_crc[7:0];
            default: tx_tdata = 8'b0; // bytes 46..59 are Ethernet padding
        endcase
    end

    // Capture exactly one descriptor, then retain the frame and byte position
    // across any TX backpressure.  A one-byte final transfer returns directly
    // to the idle/ready state after its TLAST handshake.
    always @(posedge clk) begin
        if (rst) begin
            active <= 1'b0;
            byte_index <= 6'b0;
            response_latched <= 256'b0;
        end else begin
            if (!active && response_valid) begin
                response_latched <= response_descriptor;
                active <= 1'b1;
                byte_index <= 6'b0;
            end else if (active && tx_tvalid && tx_tready) begin
                if (tx_tlast) begin
                    active <= 1'b0;
                    byte_index <= 6'b0;
                end else begin
                    byte_index <= byte_index + 1'b1;
                end
            end
        end
    end

endmodule
