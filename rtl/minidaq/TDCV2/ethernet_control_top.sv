// Complete generic Ethernet control/monitor subsystem.
//
// Hierarchy:
//
//   Parent: minidaq_ethernet_subsystem.control
//
//   ethernet_control_top
//   |
//   +-- transport: ethernet_control_transport
//   |     +-- control-request FIFO   125 MHz RX -> 40 MHz control
//   |     +-- monitor-request FIFO   125 MHz RX -> 40 MHz control
//   |     +-- control-result FIFO    40 MHz control -> 125 MHz TX
//   |     +-- monitor-result FIFO    40 MHz control -> 125 MHz TX
//   |
//   +-- engine: ethernet_control_engine
//   |     Executes one MiniDAQ-register, lpGBT-IC, or generic-SCA request
//   |     at a time in the 40 MHz control domain.
//   |
//   +-- control_tx: ethernet_control_response_tx
//   |     Serializes active control replies using EtherType 0x88B5 / MDC1.
//   |
//   +-- monitor_tx: ethernet_control_response_tx
//         Serializes monitoring replies using EtherType 0x88B6 / MDM1.
//
// External data flow:
//
//   shared TEMAC RX fork -> transport -> engine -> physical endpoints
//   control response --------------------------------> control-class arbiter
//   monitor response --------------------------------> final TX QoS arbiter
//
// Programming (MDJ1) remains a separate 0x88B5 protocol and SCA owner.  This
// module waits for that owner before issuing a generic SCA transaction.

`timescale 1ns / 1ps

module ethernet_control_top #(
    parameter integer UPLINK_COUNT = 4,
    parameter integer DOWNLINK_COUNT = 2,
    parameter integer SCA_COUNT = 4,
    parameter logic [47:0] FPGA_MAC = 48'h020000C70501
) (
    input wire rx_clk,
    input wire rx_resetn,
    input wire [7:0] rx_tdata,
    input wire rx_tvalid,
    output wire rx_tready,
    input wire rx_tlast,
    input wire tx_clk,
    output wire [7:0] control_tdata,
    output wire control_tvalid,
    input wire control_tready,
    output wire control_tlast,
    output wire [7:0] monitor_tdata,
    output wire monitor_tvalid,
    input wire monitor_tready,
    output wire monitor_tlast,
    input wire control_clk,
    input wire control_reset,
    input wire programming_active,

    output wire [7:0] fpga_register_address,
    output wire [7:0] fpga_readback_selector,
    output wire [159:0] fpga_register_write_data,
    output wire fpga_register_write,
    output wire fpga_register_read,
    output wire fpga_register_reset,
    input wire [159:0] fpga_readback_data,
    input wire fpga_readback_valid,

    output wire [7:0] ic_gbtx_address [DOWNLINK_COUNT-1:0],
    output wire [15:0] ic_register_address [DOWNLINK_COUNT-1:0],
    output wire [7:0] ic_read_count [DOWNLINK_COUNT-1:0],
    output wire [DOWNLINK_COUNT-1:0] ic_start_write,
    output wire [DOWNLINK_COUNT-1:0] ic_start_read,
    output wire [7:0] ic_write_data [DOWNLINK_COUNT-1:0],
    output wire [DOWNLINK_COUNT-1:0] ic_write_enable,
    output wire [DOWNLINK_COUNT-1:0] ic_rx_reset,
    input wire [UPLINK_COUNT-1:0] ic_rx_fifo_empty,
    input wire [7:0] ic_rx_fifo_data [UPLINK_COUNT-1:0],
    output wire [UPLINK_COUNT-1:0] ic_rx_fifo_read,

    output wire generic_sca_active,
    output wire [1:0] generic_sca_target_csm,
    output wire [SCA_COUNT-1:0] generic_sca_enable,
    output wire generic_sca_start_reset,
    output wire generic_sca_start_connect,
    output wire generic_sca_start_command,
    output wire [7:0] generic_sca_address,
    output wire [7:0] generic_sca_transid,
    output wire [7:0] generic_sca_channel,
    output wire [7:0] generic_sca_command,
    output wire [31:0] generic_sca_data,
    input wire [SCA_COUNT-1:0] sca_rx_done [DOWNLINK_COUNT-1:0],
    input wire [7:0] sca_rx_address [DOWNLINK_COUNT-1:0][SCA_COUNT-1:0],
    input wire [7:0] sca_rx_transid [DOWNLINK_COUNT-1:0][SCA_COUNT-1:0],
    input wire [7:0] sca_rx_channel [DOWNLINK_COUNT-1:0][SCA_COUNT-1:0],
    input wire [7:0] sca_rx_length [DOWNLINK_COUNT-1:0][SCA_COUNT-1:0],
    input wire [7:0] sca_rx_error [DOWNLINK_COUNT-1:0][SCA_COUNT-1:0],
    input wire [31:0] sca_rx_data [DOWNLINK_COUNT-1:0][SCA_COUNT-1:0]
);

    wire [415:0] control_request;
    wire control_request_valid;
    wire control_request_ready;
    wire [415:0] monitor_request;
    wire monitor_request_valid;
    wire monitor_request_ready;
    wire [511:0] control_result;
    wire control_result_valid;
    wire control_result_ready;
    wire [511:0] monitor_result;
    wire monitor_result_valid;
    wire monitor_result_ready;
    wire [511:0] control_response;
    wire control_response_valid;
    wire control_response_ready;
    wire [511:0] monitor_response;
    wire monitor_response_valid;
    wire monitor_response_ready;

    ethernet_control_transport #(
        .FPGA_MAC(FPGA_MAC)
    ) transport (
        .rx_clk(rx_clk), .rx_resetn(rx_resetn), .rx_tdata(rx_tdata),
        .rx_tvalid(rx_tvalid), .rx_tready(rx_tready), .rx_tlast(rx_tlast),
        .control_clk(control_clk), .control_reset(control_reset),
        .control_request(control_request),
        .control_request_valid(control_request_valid),
        .control_request_ready(control_request_ready),
        .monitor_request(monitor_request),
        .monitor_request_valid(monitor_request_valid),
        .monitor_request_ready(monitor_request_ready),
        .control_result(control_result),
        .control_result_valid(control_result_valid),
        .control_result_ready(control_result_ready),
        .monitor_result(monitor_result),
        .monitor_result_valid(monitor_result_valid),
        .monitor_result_ready(monitor_result_ready),
        .tx_clk(tx_clk), .tx_reset(~rx_resetn),
        .control_response(control_response),
        .control_response_valid(control_response_valid),
        .control_response_ready(control_response_ready),
        .monitor_response(monitor_response),
        .monitor_response_valid(monitor_response_valid),
        .monitor_response_ready(monitor_response_ready),
        .control_request_fifo_full(), .monitor_request_fifo_full(),
        .control_result_fifo_full(), .monitor_result_fifo_full()
    );

    ethernet_control_engine #(
        .UPLINK_COUNT(UPLINK_COUNT), .DOWNLINK_COUNT(DOWNLINK_COUNT),
        .SCA_COUNT(SCA_COUNT)
    ) engine (
        .clk(control_clk), .rst(control_reset),
        .programming_active(programming_active),
        .control_request(control_request),
        .control_request_valid(control_request_valid),
        .control_request_ready(control_request_ready),
        .monitor_request(monitor_request),
        .monitor_request_valid(monitor_request_valid),
        .monitor_request_ready(monitor_request_ready),
        .control_result(control_result),
        .control_result_valid(control_result_valid),
        .control_result_ready(control_result_ready),
        .monitor_result(monitor_result),
        .monitor_result_valid(monitor_result_valid),
        .monitor_result_ready(monitor_result_ready),
        .fpga_register_address(fpga_register_address),
        .fpga_readback_selector(fpga_readback_selector),
        .fpga_register_write_data(fpga_register_write_data),
        .fpga_register_write(fpga_register_write),
        .fpga_register_read(fpga_register_read),
        .fpga_register_reset(fpga_register_reset),
        .fpga_readback_data(fpga_readback_data),
        .fpga_readback_valid(fpga_readback_valid),
        .ic_gbtx_address(ic_gbtx_address),
        .ic_register_address(ic_register_address),
        .ic_read_count(ic_read_count),
        .ic_start_write(ic_start_write), .ic_start_read(ic_start_read),
        .ic_write_data(ic_write_data), .ic_write_enable(ic_write_enable),
        .ic_rx_reset(ic_rx_reset), .ic_rx_fifo_empty(ic_rx_fifo_empty),
        .ic_rx_fifo_data(ic_rx_fifo_data),
        .ic_rx_fifo_read(ic_rx_fifo_read),
        .generic_sca_active(generic_sca_active),
        .generic_sca_target_csm(generic_sca_target_csm),
        .generic_sca_enable(generic_sca_enable),
        .generic_sca_start_reset(generic_sca_start_reset),
        .generic_sca_start_connect(generic_sca_start_connect),
        .generic_sca_start_command(generic_sca_start_command),
        .generic_sca_address(generic_sca_address),
        .generic_sca_transid(generic_sca_transid),
        .generic_sca_channel(generic_sca_channel),
        .generic_sca_command(generic_sca_command),
        .generic_sca_data(generic_sca_data),
        .sca_rx_done(sca_rx_done), .sca_rx_address(sca_rx_address),
        .sca_rx_transid(sca_rx_transid), .sca_rx_channel(sca_rx_channel),
        .sca_rx_length(sca_rx_length), .sca_rx_error(sca_rx_error),
        .sca_rx_data(sca_rx_data)
    );

    ethernet_control_response_tx #(
        .FPGA_MAC(FPGA_MAC), .ETHERTYPE(16'h88B5),
        .MAGIC(32'h4D444331)
    ) control_tx (
        .clk(tx_clk), .rst(~rx_resetn),
        .response_descriptor(control_response),
        .response_valid(control_response_valid),
        .response_ready(control_response_ready),
        .tx_tdata(control_tdata), .tx_tvalid(control_tvalid),
        .tx_tready(control_tready), .tx_tlast(control_tlast)
    );

    ethernet_control_response_tx #(
        .FPGA_MAC(FPGA_MAC), .ETHERTYPE(16'h88B6),
        .MAGIC(32'h4D444D31)
    ) monitor_tx (
        .clk(tx_clk), .rst(~rx_resetn),
        .response_descriptor(monitor_response),
        .response_valid(monitor_response_valid),
        .response_ready(monitor_response_ready),
        .tx_tdata(monitor_tdata), .tx_tvalid(monitor_tvalid),
        .tx_tready(monitor_tready), .tx_tlast(monitor_tlast)
    );

endmodule
