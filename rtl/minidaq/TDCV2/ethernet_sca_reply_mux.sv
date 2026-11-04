// Selects the reply from the CSM/SCA currently owned by the Ethernet
// programmer. Invalid target indices produce no reply.
//
// Hierarchy and interfaces:
//
//   Parent: ethernet_sca_jtag_top.reply_mux
//   Children: none; this is a combinational array selector
//
//   sca_top[downlink][sca] reply arrays
//                    |
//                    v
//          ethernet_sca_reply_mux
//                    |
//                    v
//   ethernet_jtag_programmer reply matcher and timeout FSM
//
// The target indices come from the active programmer transaction. Selection
// occurs in the common 40 MHz SCA control domain and adds no CDC boundary.

`timescale 1ns / 1ps

module ethernet_sca_reply_mux #(
    parameter integer DOWNLINK_COUNT = 2,
    parameter integer SCA_COUNT      = 4
) (
    input  wire [1:0] target_csm,
    input  wire [1:0] target_sca,

    input  wire [SCA_COUNT-1:0]         sca_rx_done
        [DOWNLINK_COUNT-1:0],
    input  wire [7:0]                   sca_rx_transid
        [DOWNLINK_COUNT-1:0][SCA_COUNT-1:0],
    input  wire [7:0]                   sca_rx_channel
        [DOWNLINK_COUNT-1:0][SCA_COUNT-1:0],
    input  wire [7:0]                   sca_rx_error
        [DOWNLINK_COUNT-1:0][SCA_COUNT-1:0],
    input  wire [31:0]                  sca_rx_data
        [DOWNLINK_COUNT-1:0][SCA_COUNT-1:0],

    output reg          selected_valid,
    output reg  [7:0]   selected_transid,
    output reg  [7:0]   selected_channel,
    output reg  [7:0]   selected_error,
    output reg  [31:0]  selected_data
);

    always @(*) begin
        selected_valid   = 1'b0;
        selected_transid = 8'b0;
        selected_channel = 8'b0;
        selected_error   = 8'b0;
        selected_data    = 32'b0;

        if ((target_csm < DOWNLINK_COUNT) && (target_sca < SCA_COUNT)) begin
            selected_valid   = sca_rx_done[target_csm][target_sca];
            selected_transid = sca_rx_transid[target_csm][target_sca];
            selected_channel = sca_rx_channel[target_csm][target_sca];
            selected_error   = sca_rx_error[target_csm][target_sca];
            selected_data    = sca_rx_data[target_csm][target_sca];
        end
    end

endmodule
