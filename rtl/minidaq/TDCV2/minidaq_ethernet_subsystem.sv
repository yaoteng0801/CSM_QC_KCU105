// MiniDAQ application-level Ethernet subsystem.
//
// The vendor TEMAC and the physical sca_top instances remain outside this
// wrapper so their generated constraints and board-level hierarchy do not
// change. This module owns the complete client-side Ethernet control plane:
//
//   xcku035_10g24_top
//   |
//   +-- ethernet_mac                         vendor TEMAC, outside this module
//   |     |
//   |     +-- RX AXI stream -----------------------------+
//   |     +-- TX AXI stream <-------------------------+   |
//   |                                                 |   |
//   +-- minidaq_ethernet_subsystem                    |   |
//   |     |                                           |   |
//   |     +-- lossless RX fork <----------------------+---+
//   |     |     Every accepted byte is delivered to both parsers. The TEMAC
//   |     |     is ready only when both parser branches can accept the byte.
//   |     |
//   |     +-- programming: ethernet_sca_jtag_top
//   |     |     +-- ethernet_jtag_transport
//   |     |     |     MDJ1 0x88B5 parser and RX/control-domain CDC FIFOs
//   |     |     +-- ethernet_jtag_programmer
//   |     |     |     Autonomous SCA JTAG command and busy/reply sequencing
//   |     |     +-- ethernet_sca_reply_mux
//   |     |     |     Selects the requested CSM/SCA reply
//   |     |     +-- ethernet_program_ack_tx
//   |     |           Serializes RX_ACK, SCA_ACK, NACK, and IDCODE replies
//   |     |
//   |     +-- control: ethernet_control_top
//   |     |     +-- ethernet_control_transport
//   |     |     |     MDC1 0x88B5 and MDM1 0x88B6 parser/CDC FIFOs
//   |     |     +-- ethernet_control_engine
//   |     |     |     MiniDAQ register, lpGBT IC, and generic SCA operations
//   |     |     +-- ethernet_control_response_tx x2
//   |     |           Separate control and monitoring response serializers
//   |     |
//   |     +-- sca_arbiter: ethernet_sca_command_arbiter
//   |     |     Programming owns its selected downlink over a simultaneous
//   |     |     generic SCA request; unowned physical SCA inputs are zero.
//   |     |
//   |     +-- control_class_arbiter: ethernet_tx_frame_arbiter
//   |     |     Programming ACK > generic control reply at frame boundaries.
//   |     |
//   |     +-- tx_qos: ethernet_tx_qos_arbiter
//   |           Hit data, combined control, and monitoring share TEMAC TX.
//   |           Grants remain locked through TLAST; urgent hit occupancy wins,
//   |           and monitoring is admitted only below its occupancy/rate limits.
//   |
//   +-- sca_top[DOWNLINK_COUNT] <---- arbitrated commands and shared replies
//
// Clock domains:
//
//   rx_clk / tx_clk : synchronous 125 MHz TEMAC client clock in this design
//   control_clk     : independent 40 MHz MiniDAQ, lpGBT IC, and SCA clock
//
// The programming and generic-control child wrappers contain their protocol
// CDC FIFOs. SCA arbitration occurs entirely in the 40 MHz control domain;
// TX response arbitration occurs entirely in the 125 MHz TEMAC domain.

`timescale 1ns / 1ps

module minidaq_ethernet_subsystem #(
    parameter integer UPLINK_COUNT = 4,
    parameter integer DOWNLINK_COUNT = 2,
    parameter integer SCA_COUNT = 4,
    parameter logic [47:0] FPGA_MAC = 48'h020000C70501,
    parameter logic [15:0] PROGRAM_ETHERTYPE = 16'h88B5,
    parameter integer MAX_CHUNK_BYTES = 1408,
    parameter integer DATA_FIFO_DEPTH = 128,
    parameter integer CONTROL_FREQUENCY_HZ = 40_000_000,
    parameter integer REPLY_TIMEOUT_CYCLES = 400_000,
    parameter integer MAX_REPLY_RETRIES = 100,
    parameter integer HIT_COUNT_WIDTH = 16,
    parameter integer HIT_HIGH_WATER = 1024,
    parameter integer HIT_LOW_WATER = 256,
    parameter integer MONITOR_MIN_GAP_CYCLES = 125000
) (
    // TEMAC client RX AXI stream.
    input  wire rx_clk,
    input  wire rx_resetn,
    input  wire [7:0] rx_tdata,
    input  wire rx_tvalid,
    output wire rx_tready,
    input  wire rx_tlast,

    // TEMAC client TX AXI stream.
    input  wire tx_clk,
    output wire [7:0] tx_tdata,
    output wire tx_tvalid,
    input  wire tx_tready,
    output wire tx_tlast,

    // MiniDAQ control/SCA clock domain.
    input  wire control_clk,
    input  wire control_reset,

    // Detector hit-frame source.
    input  wire [HIT_COUNT_WIDTH-1:0] hit_fifo_occupancy,
    input  wire [7:0] hit_tdata,
    input  wire hit_tvalid,
    output wire hit_tready,
    input  wire hit_tlast,

    // MiniDAQ register-bank endpoint.
    output wire [7:0] fpga_register_address,
    output wire [7:0] fpga_readback_selector,
    output wire [159:0] fpga_register_write_data,
    output wire fpga_register_write,
    output wire fpga_register_read,
    output wire fpga_register_reset,
    input  wire [159:0] fpga_readback_data,
    input  wire fpga_readback_valid,

    // lpGBT IC endpoints.
    output wire [7:0] ic_gbtx_address [DOWNLINK_COUNT-1:0],
    output wire [15:0] ic_register_address [DOWNLINK_COUNT-1:0],
    output wire [7:0] ic_read_count [DOWNLINK_COUNT-1:0],
    output wire [DOWNLINK_COUNT-1:0] ic_start_write,
    output wire [DOWNLINK_COUNT-1:0] ic_start_read,
    output wire [7:0] ic_write_data [DOWNLINK_COUNT-1:0],
    output wire [DOWNLINK_COUNT-1:0] ic_write_enable,
    output wire [DOWNLINK_COUNT-1:0] ic_rx_reset,
    input  wire [UPLINK_COUNT-1:0] ic_rx_fifo_empty,
    input  wire [7:0] ic_rx_fifo_data [UPLINK_COUNT-1:0],
    output wire [UPLINK_COUNT-1:0] ic_rx_fifo_read,

    // Already-arbitrated commands to every physical sca_top instance.
    output wire [SCA_COUNT-1:0] sca_enable [DOWNLINK_COUNT-1:0],
    output wire [DOWNLINK_COUNT-1:0] sca_start_reset,
    output wire [DOWNLINK_COUNT-1:0] sca_start_connect,
    output wire [DOWNLINK_COUNT-1:0] sca_start_command,
    output wire [7:0] sca_tx_address [DOWNLINK_COUNT-1:0],
    output wire [7:0] sca_tx_transid [DOWNLINK_COUNT-1:0],
    output wire [7:0] sca_tx_channel [DOWNLINK_COUNT-1:0],
    output wire [7:0] sca_tx_command [DOWNLINK_COUNT-1:0],
    output wire [31:0] sca_tx_data [DOWNLINK_COUNT-1:0],

    // Reply arrays from the physical sca_top instances.
    input  wire [SCA_COUNT-1:0] sca_rx_done [DOWNLINK_COUNT-1:0],
    input  wire [7:0] sca_rx_address
        [DOWNLINK_COUNT-1:0][SCA_COUNT-1:0],
    input  wire [7:0] sca_rx_transid
        [DOWNLINK_COUNT-1:0][SCA_COUNT-1:0],
    input  wire [7:0] sca_rx_channel
        [DOWNLINK_COUNT-1:0][SCA_COUNT-1:0],
    input  wire [7:0] sca_rx_length
        [DOWNLINK_COUNT-1:0][SCA_COUNT-1:0],
    input  wire [7:0] sca_rx_error
        [DOWNLINK_COUNT-1:0][SCA_COUNT-1:0],
    input  wire [31:0] sca_rx_data
        [DOWNLINK_COUNT-1:0][SCA_COUNT-1:0],

    // Programming state and FIFO diagnostics.
    output wire programming_active,
    output wire programming_session_active,
    output wire program_data_fifo_full,
    output wire program_data_fifo_overflow,
    output wire program_descriptor_fifo_full,
    output wire program_result_fifo_full
);

    // One accepted TEMAC byte must be observed by both parsers. The generic
    // parser is nonblocking; the programming parser may apply backpressure.
    wire program_rx_ready;
    wire control_rx_ready;
    wire program_rx_valid = rx_tvalid && control_rx_ready;
    wire control_rx_valid = rx_tvalid && program_rx_ready;
    assign rx_tready = program_rx_ready && control_rx_ready;

    // Programming/IDCODE command and response signals.
    wire [1:0] program_target_csm;
    wire [1:0] program_target_sca;
    wire program_sca_start;
    wire [7:0] program_sca_address;
    wire [7:0] program_sca_transid;
    wire [7:0] program_sca_channel;
    wire [7:0] program_sca_command;
    wire [31:0] program_sca_data;
    wire [7:0] program_tx_tdata;
    wire program_tx_tvalid;
    wire program_tx_tready;
    wire program_tx_tlast;

    ethernet_sca_jtag_top #(
        .DOWNLINK_COUNT(DOWNLINK_COUNT), .SCA_COUNT(SCA_COUNT),
        .PROGRAM_ETHERTYPE(PROGRAM_ETHERTYPE), .FPGA_MAC(FPGA_MAC),
        .MAX_CHUNK_BYTES(MAX_CHUNK_BYTES),
        .DATA_FIFO_DEPTH(DATA_FIFO_DEPTH),
        .CONTROL_FREQUENCY_HZ(CONTROL_FREQUENCY_HZ),
        .REPLY_TIMEOUT_CYCLES(REPLY_TIMEOUT_CYCLES),
        .MAX_REPLY_RETRIES(MAX_REPLY_RETRIES)
    ) programming (
        .rx_clk(rx_clk), .rx_resetn(rx_resetn), .rx_tdata(rx_tdata),
        .rx_tvalid(program_rx_valid), .rx_tready(program_rx_ready),
        .rx_tlast(rx_tlast),
        .tx_clk(tx_clk), .tx_tdata(program_tx_tdata),
        .tx_tvalid(program_tx_tvalid), .tx_tready(program_tx_tready),
        .tx_tlast(program_tx_tlast),
        .control_clk(control_clk), .control_reset(control_reset),
        .programming_active(programming_active),
        .target_csm(program_target_csm), .target_sca(program_target_sca),
        .sca_start_command(program_sca_start),
        .sca_tx_address(program_sca_address),
        .sca_tx_transid(program_sca_transid),
        .sca_tx_channel(program_sca_channel),
        .sca_tx_command(program_sca_command),
        .sca_tx_data(program_sca_data),
        .sca_rx_done(sca_rx_done), .sca_rx_transid(sca_rx_transid),
        .sca_rx_channel(sca_rx_channel), .sca_rx_error(sca_rx_error),
        .sca_rx_data(sca_rx_data),
        .programming_session_active(programming_session_active),
        .data_fifo_full(program_data_fifo_full),
        .data_fifo_overflow(program_data_fifo_overflow),
        .descriptor_fifo_full(program_descriptor_fifo_full),
        .result_fifo_full(program_result_fifo_full)
    );

    // Generic register, lpGBT IC, and SCA control/monitor signals.
    wire generic_sca_active;
    wire [1:0] generic_sca_target_csm;
    wire [SCA_COUNT-1:0] generic_sca_enable;
    wire generic_sca_start_reset;
    wire generic_sca_start_connect;
    wire generic_sca_start_command;
    wire [7:0] generic_sca_address;
    wire [7:0] generic_sca_transid;
    wire [7:0] generic_sca_channel;
    wire [7:0] generic_sca_command;
    wire [31:0] generic_sca_data;
    wire [7:0] control_tx_tdata;
    wire control_tx_tvalid;
    wire control_tx_tready;
    wire control_tx_tlast;
    wire [7:0] monitor_tx_tdata;
    wire monitor_tx_tvalid;
    wire monitor_tx_tready;
    wire monitor_tx_tlast;

    ethernet_control_top #(
        .UPLINK_COUNT(UPLINK_COUNT), .DOWNLINK_COUNT(DOWNLINK_COUNT),
        .SCA_COUNT(SCA_COUNT), .FPGA_MAC(FPGA_MAC)
    ) control (
        .rx_clk(rx_clk), .rx_resetn(rx_resetn), .rx_tdata(rx_tdata),
        .rx_tvalid(control_rx_valid), .rx_tready(control_rx_ready),
        .rx_tlast(rx_tlast),
        .tx_clk(tx_clk),
        .control_tdata(control_tx_tdata),
        .control_tvalid(control_tx_tvalid),
        .control_tready(control_tx_tready),
        .control_tlast(control_tx_tlast),
        .monitor_tdata(monitor_tx_tdata),
        .monitor_tvalid(monitor_tx_tvalid),
        .monitor_tready(monitor_tx_tready),
        .monitor_tlast(monitor_tx_tlast),
        .control_clk(control_clk), .control_reset(control_reset),
        .programming_active(programming_active),
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

    ethernet_sca_command_arbiter #(
        .DOWNLINK_COUNT(DOWNLINK_COUNT), .SCA_COUNT(SCA_COUNT)
    ) sca_arbiter (
        .programming_active(programming_active),
        .programming_target_csm(program_target_csm),
        .programming_target_sca(program_target_sca),
        .programming_start_command(program_sca_start),
        .programming_address(program_sca_address),
        .programming_transid(program_sca_transid),
        .programming_channel(program_sca_channel),
        .programming_command(program_sca_command),
        .programming_data(program_sca_data),
        .generic_active(generic_sca_active),
        .generic_target_csm(generic_sca_target_csm),
        .generic_enable(generic_sca_enable),
        .generic_start_reset(generic_sca_start_reset),
        .generic_start_connect(generic_sca_start_connect),
        .generic_start_command(generic_sca_start_command),
        .generic_address(generic_sca_address),
        .generic_transid(generic_sca_transid),
        .generic_channel(generic_sca_channel),
        .generic_command(generic_sca_command),
        .generic_data(generic_sca_data),
        .sca_enable(sca_enable), .sca_start_reset(sca_start_reset),
        .sca_start_connect(sca_start_connect),
        .sca_start_command(sca_start_command),
        .sca_address(sca_tx_address), .sca_transid(sca_tx_transid),
        .sca_channel(sca_tx_channel), .sca_command(sca_tx_command),
        .sca_data(sca_tx_data)
    );

    // Programming ACKs have priority over ordinary active-control replies at
    // frame boundaries. Monitoring remains a distinct QoS class.
    wire [7:0] combined_control_tdata;
    wire combined_control_tvalid;
    wire combined_control_tready;
    wire combined_control_tlast;
    ethernet_tx_frame_arbiter control_class_arbiter (
        .clk(tx_clk), .rst(~rx_resetn),
        .hit_tdata(control_tx_tdata), .hit_tvalid(control_tx_tvalid),
        .hit_tready(control_tx_tready), .hit_tlast(control_tx_tlast),
        .control_tdata(program_tx_tdata),
        .control_tvalid(program_tx_tvalid),
        .control_tready(program_tx_tready),
        .control_tlast(program_tx_tlast),
        .tx_tdata(combined_control_tdata),
        .tx_tvalid(combined_control_tvalid),
        .tx_tready(combined_control_tready),
        .tx_tlast(combined_control_tlast)
    );

    ethernet_tx_qos_arbiter #(
        .HIT_COUNT_WIDTH(HIT_COUNT_WIDTH),
        .HIT_HIGH_WATER(HIT_HIGH_WATER),
        .HIT_LOW_WATER(HIT_LOW_WATER),
        .MONITOR_MIN_GAP_CYCLES(MONITOR_MIN_GAP_CYCLES)
    ) tx_qos (
        .clk(tx_clk), .rst(~rx_resetn),
        .hit_fifo_occupancy(hit_fifo_occupancy),
        .hit_tdata(hit_tdata), .hit_tvalid(hit_tvalid),
        .hit_tready(hit_tready), .hit_tlast(hit_tlast),
        .control_tdata(combined_control_tdata),
        .control_tvalid(combined_control_tvalid),
        .control_tready(combined_control_tready),
        .control_tlast(combined_control_tlast),
        .monitor_tdata(monitor_tx_tdata),
        .monitor_tvalid(monitor_tx_tvalid),
        .monitor_tready(monitor_tx_tready),
        .monitor_tlast(monitor_tx_tlast),
        .tx_tdata(tx_tdata), .tx_tvalid(tx_tvalid),
        .tx_tready(tx_tready), .tx_tlast(tx_tlast)
    );

endmodule
