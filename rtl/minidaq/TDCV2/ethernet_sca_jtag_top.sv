// Ethernet-to-SCA JTAG programming and IDCODE-read subsystem.
//
// Hierarchy:
//
//   Parent: minidaq_ethernet_subsystem.programming
//
//   ethernet_sca_jtag_top
//   |
//   +-- transport: ethernet_jtag_transport
//   |     Parses MDJ1 frames, verifies CRC/session state, and owns the three
//   |     asynchronous data/descriptor/result FIFOs.
//   |
//   +-- programmer: ethernet_jtag_programmer
//   |     Executes the autonomous 40 MHz GBT-SCA JTAG sequence.
//   |
//   +-- reply_mux: ethernet_sca_reply_mux
//   |     Selects the reply for the programmer's current CSM/SCA target.
//   |
//   +-- ack_tx: ethernet_program_ack_tx
//         Serializes programming and IDCODE ACK/NACK descriptors at 125 MHz.
//
// This wrapper keeps the protocol parser, CDC FIFOs, autonomous programmer,
// SCA reply selection, and ACK serializer behind one top-level interface:
//
// Programming/IDCODE request path:
//
//   TEMAC RX -> transport -> data/descriptor FIFOs -> programmer
//                                                        |
//                                                        v
//                                                   SCA command
//
// SCA reply path:
//
//   all SCA replies -> reply mux -> selected reply -> programmer
//
// Completion/response path:
//
//   programmer -> result FIFO -> transport -> ACK serializer -> ACK AXI stream
//
// Final arbitration against generic control, monitoring, and hit data belongs
// to minidaq_ethernet_subsystem.  This wrapper therefore exposes only its own
// programming/IDCODE ACK stream.
//
// rx_clk and tx_clk are separate ports to match the TEMAC example-design
// interface, but the response descriptor crosses directly between them.  They
// must therefore be the same synchronous 125 MHz user clock, as they are in
// the current MiniDAQ TEMAC design.  control_clk is the independent 40 MHz SCA
// domain and is crossed only through XPM CDC primitives inside the transport.

`timescale 1ns / 1ps

module ethernet_sca_jtag_top #(
    parameter integer DOWNLINK_COUNT       = 2,
    parameter integer SCA_COUNT            = 4,
    parameter logic [15:0] PROGRAM_ETHERTYPE = 16'h88B5,
    parameter logic [47:0] FPGA_MAC          = 48'h020000C70501,
    parameter integer MAX_CHUNK_BYTES        = 1408,
    parameter integer DATA_FIFO_DEPTH        = 128,
    parameter integer CONTROL_FREQUENCY_HZ   = 40_000_000,
    parameter integer REPLY_TIMEOUT_CYCLES   = 400_000,
    parameter integer MAX_REPLY_RETRIES      = 100
) (
    // TEMAC receive stream.
    input  wire         rx_clk,
    input  wire         rx_resetn,
    input  wire [7:0]   rx_tdata,
    input  wire         rx_tvalid,
    output wire         rx_tready,
    input  wire         rx_tlast,

    // TEMAC transmit clock and programming ACK output stream.
    input  wire         tx_clk,
    output wire [7:0]   tx_tdata,
    output wire         tx_tvalid,
    input  wire         tx_tready,
    output wire         tx_tlast,

    // MiniDAQ/SCA control domain.
    input  wire         control_clk,
    input  wire         control_reset,

    // JTAG command interface. The parent Ethernet subsystem arbitrates these
    // signals against generic Ethernet commands before driving the SCA cores.
    output wire         programming_active,
    output wire [1:0]   target_csm,
    output wire [1:0]   target_sca,
    output wire         sca_start_command,
    output wire [7:0]   sca_tx_address,
    output wire [7:0]   sca_tx_transid,
    output wire [7:0]   sca_tx_channel,
    output wire [7:0]   sca_tx_command,
    output wire [31:0]  sca_tx_data,

    // Replies from every physical SCA.  The internal reply mux forwards only
    // target_csm/target_sca to the active programmer transaction.
    input  wire [SCA_COUNT-1:0] sca_rx_done
        [DOWNLINK_COUNT-1:0],
    input  wire [7:0] sca_rx_transid
        [DOWNLINK_COUNT-1:0][SCA_COUNT-1:0],
    input  wire [7:0] sca_rx_channel
        [DOWNLINK_COUNT-1:0][SCA_COUNT-1:0],
    input  wire [7:0] sca_rx_error
        [DOWNLINK_COUNT-1:0][SCA_COUNT-1:0],
    input  wire [31:0] sca_rx_data
        [DOWNLINK_COUNT-1:0][SCA_COUNT-1:0],

    // Session and FIFO diagnostics.
    output wire         programming_session_active,
    output wire         data_fifo_full,
    output wire         data_fifo_overflow,
    output wire         descriptor_fifo_full,
    output wire         result_fifo_full
);

    // Transport <-> programmer CDC interfaces.
    wire [127:0] chunk_data;
    wire         chunk_data_valid;
    wire         chunk_data_ready;
    wire [191:0] chunk_descriptor;
    wire         chunk_descriptor_valid;
    wire         chunk_descriptor_ready;
    wire         abort_control;
    wire [159:0] programmer_result;
    wire         programmer_result_valid;
    wire         programmer_result_ready;

    // Transport -> Ethernet ACK serializer.
    wire [255:0] response_descriptor;
    wire         response_valid;
    wire         response_ready;

    // Selected SCA reply -> programmer.
    wire         selected_reply_valid;
    wire [7:0]   selected_reply_transid;
    wire [7:0]   selected_reply_channel;
    wire [7:0]   selected_reply_error;
    wire [31:0]  selected_reply_data;

    ethernet_jtag_transport #(
        .PROGRAM_ETHERTYPE (PROGRAM_ETHERTYPE),
        .FPGA_MAC          (FPGA_MAC),
        .MAX_CHUNK_BYTES   (MAX_CHUNK_BYTES),
        .DATA_FIFO_DEPTH   (DATA_FIFO_DEPTH)
    ) ethernet_jtag_transport_inst (
        .rx_clk                     (rx_clk),
        .rx_resetn                  (rx_resetn),
        .rx_tdata                   (rx_tdata),
        .rx_tvalid                  (rx_tvalid),
        .rx_tready                  (rx_tready),
        .rx_tlast                   (rx_tlast),
        .control_clk                (control_clk),
        .control_reset              (control_reset),
        .chunk_data                 (chunk_data),
        .chunk_data_valid           (chunk_data_valid),
        .chunk_data_ready           (chunk_data_ready),
        .chunk_descriptor           (chunk_descriptor),
        .chunk_descriptor_valid     (chunk_descriptor_valid),
        .chunk_descriptor_ready     (chunk_descriptor_ready),
        .abort_control              (abort_control),
        .programmer_result          (programmer_result),
        .programmer_result_valid    (programmer_result_valid),
        .programmer_result_ready    (programmer_result_ready),
        .response_descriptor        (response_descriptor),
        .response_valid             (response_valid),
        .response_ready             (response_ready),
        .programming_session_active (programming_session_active),
        .data_fifo_full             (data_fifo_full),
        .data_fifo_overflow         (data_fifo_overflow),
        .descriptor_fifo_full       (descriptor_fifo_full),
        .result_fifo_full           (result_fifo_full)
    );

    ethernet_jtag_programmer #(
        .CLOCK_FREQUENCY_HZ   (CONTROL_FREQUENCY_HZ),
        .REPLY_TIMEOUT_CYCLES (REPLY_TIMEOUT_CYCLES),
        .MAX_REPLY_RETRIES    (MAX_REPLY_RETRIES)
    ) ethernet_jtag_programmer_inst (
        .clk                (control_clk),
        .rst                (control_reset),
        .abort              (abort_control),
        .descriptor         (chunk_descriptor),
        .descriptor_valid   (chunk_descriptor_valid),
        .descriptor_ready   (chunk_descriptor_ready),
        .chunk_data         (chunk_data),
        .chunk_data_valid   (chunk_data_valid),
        .chunk_data_ready   (chunk_data_ready),
        .result             (programmer_result),
        .result_valid       (programmer_result_valid),
        .result_ready       (programmer_result_ready),
        .programming_active (programming_active),
        .target_csm         (target_csm),
        .target_sca         (target_sca),
        .sca_start_command  (sca_start_command),
        .sca_tx_address     (sca_tx_address),
        .sca_tx_transid     (sca_tx_transid),
        .sca_tx_channel     (sca_tx_channel),
        .sca_tx_command     (sca_tx_command),
        .sca_tx_data        (sca_tx_data),
        .sca_reply_valid    (selected_reply_valid),
        .sca_reply_transid  (selected_reply_transid),
        .sca_reply_channel  (selected_reply_channel),
        .sca_reply_error    (selected_reply_error),
        .sca_reply_data     (selected_reply_data)
    );

    ethernet_sca_reply_mux #(
        .DOWNLINK_COUNT (DOWNLINK_COUNT),
        .SCA_COUNT      (SCA_COUNT)
    ) ethernet_sca_reply_mux_inst (
        .target_csm       (target_csm),
        .target_sca       (target_sca),
        .sca_rx_done      (sca_rx_done),
        .sca_rx_transid   (sca_rx_transid),
        .sca_rx_channel   (sca_rx_channel),
        .sca_rx_error     (sca_rx_error),
        .sca_rx_data      (sca_rx_data),
        .selected_valid   (selected_reply_valid),
        .selected_transid (selected_reply_transid),
        .selected_channel (selected_reply_channel),
        .selected_error   (selected_reply_error),
        .selected_data    (selected_reply_data)
    );

    ethernet_program_ack_tx #(
        .PROGRAM_ETHERTYPE (PROGRAM_ETHERTYPE),
        .FPGA_MAC          (FPGA_MAC)
    ) ethernet_program_ack_tx_inst (
        .clk                 (tx_clk),
        .rst                 (~rx_resetn),
        .response_descriptor (response_descriptor),
        .response_valid      (response_valid),
        .response_ready      (response_ready),
        .tx_tdata       (tx_tdata),
        .tx_tvalid      (tx_tvalid),
        .tx_tready      (tx_tready),
        .tx_tlast       (tx_tlast)
    );

endmodule
