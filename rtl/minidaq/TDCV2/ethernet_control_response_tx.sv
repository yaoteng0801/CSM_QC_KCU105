// Serializes one generic control/monitor result descriptor into a raw Ethernet
// frame.  The TEMAC adds preamble, SFD and FCS.  The descriptor is held across
// TX backpressure and the grant remains valid through the accepted TLAST byte.
//
// Hierarchy and interfaces:
//
//   Parent: ethernet_control_top.control_tx or ethernet_control_top.monitor_tx
//   Children: none; this module is one descriptor latch and byte serializer
//
//   ethernet_control_transport result FIFO
//                         |
//                         v
//          ethernet_control_response_tx
//                         |
//                         +-- control instance -> control_class_arbiter
//                         +-- monitor instance -> tx_qos monitor input
//
// Both instances run entirely on the 125 MHz TEMAC TX clock. They serialize
// different EtherType/magic pairs but share the same descriptor format.

`timescale 1ns / 1ps

module ethernet_control_response_tx #(
    parameter logic [47:0] FPGA_MAC = 48'h020000C70501,
    parameter logic [15:0] ETHERTYPE = 16'h88B5,
    parameter logic [31:0] MAGIC = 32'h4D444331 // "MDC1"
) (
    input  wire         clk,
    input  wire         rst,
    input  wire [511:0] response_descriptor,
    input  wire         response_valid,
    output wire         response_ready,
    output reg  [7:0]   tx_tdata,
    output reg          tx_tvalid,
    input  wire         tx_tready,
    output reg          tx_tlast
);

    localparam logic [7:0] VERSION = 8'h02;
    reg active = 1'b0;
    reg [6:0] byte_index = 7'b0;
    reg [6:0] frame_bytes = 7'd60;
    reg [511:0] latched = 512'b0;

    // Result descriptor:
    // [511:464] destination MAC, [463:448] EtherType,
    // [447:416] request ID, [415:408] opcode, [407:400] status,
    // [399:392] target, [391:384] subtarget, [383:376] data length,
    // [375:360] address, [359:352] detail, [351:64] data (36 bytes).
    wire [47:0] destination_mac = latched[511:464];
    wire [31:0] request_id = latched[447:416];
    wire [7:0] opcode = latched[415:408];
    wire [7:0] status = latched[407:400];
    wire [7:0] target = latched[399:392];
    wire [7:0] subtarget = latched[391:384];
    wire [7:0] data_len = latched[383:376];
    wire [15:0] address = latched[375:360];
    wire [7:0] detail = latched[359:352];
    wire [287:0] data = latched[351:64];

    assign response_ready = ~active;

    integer data_bit;
    always @(*) begin
        tx_tdata = 8'b0;
        tx_tvalid = active;
        tx_tlast = active && (byte_index == frame_bytes - 1'b1);
        case (byte_index)
            0: tx_tdata = destination_mac[47:40];
            1: tx_tdata = destination_mac[39:32];
            2: tx_tdata = destination_mac[31:24];
            3: tx_tdata = destination_mac[23:16];
            4: tx_tdata = destination_mac[15:8];
            5: tx_tdata = destination_mac[7:0];
            6: tx_tdata = FPGA_MAC[47:40];
            7: tx_tdata = FPGA_MAC[39:32];
            8: tx_tdata = FPGA_MAC[31:24];
            9: tx_tdata = FPGA_MAC[23:16];
            10: tx_tdata = FPGA_MAC[15:8];
            11: tx_tdata = FPGA_MAC[7:0];
            12: tx_tdata = ETHERTYPE[15:8];
            13: tx_tdata = ETHERTYPE[7:0];
            14: tx_tdata = MAGIC[31:24];
            15: tx_tdata = MAGIC[23:16];
            16: tx_tdata = MAGIC[15:8];
            17: tx_tdata = MAGIC[7:0];
            18: tx_tdata = VERSION;
            19: tx_tdata = opcode | 8'h80;
            20: tx_tdata = status;
            21: tx_tdata = target;
            22: tx_tdata = subtarget;
            23: tx_tdata = data_len;
            24: tx_tdata = request_id[31:24];
            25: tx_tdata = request_id[23:16];
            26: tx_tdata = request_id[15:8];
            27: tx_tdata = request_id[7:0];
            28: tx_tdata = address[15:8];
            29: tx_tdata = address[7:0];
            30: tx_tdata = detail;
            31,32,33,34,35: tx_tdata = 8'b0;
            default: begin
                if (byte_index >= 7'd36 && byte_index < 7'd72) begin
                    data_bit = 287 - ((byte_index - 36) * 8);
                    tx_tdata = data[data_bit -: 8];
                end
            end
        endcase
    end

    always @(posedge clk) begin
        if (rst) begin
            active <= 1'b0;
            byte_index <= 7'b0;
            frame_bytes <= 7'd60;
            latched <= 512'b0;
        end else if (!active && response_valid) begin
            active <= 1'b1;
            byte_index <= 7'b0;
            latched <= response_descriptor;
            frame_bytes <= (response_descriptor[383:376] > 8'd24)
                ? (7'd36 + response_descriptor[383:376]) : 7'd60;
        end else if (active && tx_tvalid && tx_tready) begin
            if (tx_tlast) begin
                active <= 1'b0;
                byte_index <= 7'b0;
            end else begin
                byte_index <= byte_index + 1'b1;
            end
        end
    end

endmodule
