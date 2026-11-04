// Selects the Ethernet owner of each physical SCA downlink.
//
// Hierarchy and interfaces:
//
//   Parent: minidaq_ethernet_subsystem.sca_arbiter
//   Children: none; one combinational selection block is generated per link
//
//   ethernet_jtag_programmer command ----+
//                                        +--> this arbiter --> sca_top[link]
//   ethernet_control_engine command -----+
//
// Both sources and every physical sca_top command port are in the common
// 40 MHz control/SCA domain. Replies bypass this command arbiter and return to
// both protocol wrappers, which select and validate the reply they expect.
//
// Bit-file programming/IDCODE traffic has priority. Generic Ethernet SCA
// traffic may own only its selected downlink when no programming transaction
// owns that downlink. Unowned outputs are driven to zero so no stale command
// field can reach an enabled SCA accidentally.

`timescale 1ns / 1ps

module ethernet_sca_command_arbiter #(
    parameter integer DOWNLINK_COUNT = 2,
    parameter integer SCA_COUNT = 4
) (
    input  wire programming_active,
    input  wire [1:0] programming_target_csm,
    input  wire [1:0] programming_target_sca,
    input  wire programming_start_command,
    input  wire [7:0] programming_address,
    input  wire [7:0] programming_transid,
    input  wire [7:0] programming_channel,
    input  wire [7:0] programming_command,
    input  wire [31:0] programming_data,

    input  wire generic_active,
    input  wire [1:0] generic_target_csm,
    input  wire [SCA_COUNT-1:0] generic_enable,
    input  wire generic_start_reset,
    input  wire generic_start_connect,
    input  wire generic_start_command,
    input  wire [7:0] generic_address,
    input  wire [7:0] generic_transid,
    input  wire [7:0] generic_channel,
    input  wire [7:0] generic_command,
    input  wire [31:0] generic_data,

    output wire [SCA_COUNT-1:0] sca_enable [DOWNLINK_COUNT-1:0],
    output wire [DOWNLINK_COUNT-1:0] sca_start_reset,
    output wire [DOWNLINK_COUNT-1:0] sca_start_connect,
    output wire [DOWNLINK_COUNT-1:0] sca_start_command,
    output wire [7:0] sca_address [DOWNLINK_COUNT-1:0],
    output wire [7:0] sca_transid [DOWNLINK_COUNT-1:0],
    output wire [7:0] sca_channel [DOWNLINK_COUNT-1:0],
    output wire [7:0] sca_command [DOWNLINK_COUNT-1:0],
    output wire [31:0] sca_data [DOWNLINK_COUNT-1:0]
);

    genvar downlink;
    generate
        for (downlink = 0; downlink < DOWNLINK_COUNT;
             downlink = downlink + 1) begin : per_downlink
            wire programming_owns = programming_active
                && programming_target_csm == downlink;
            wire generic_owns = generic_active
                && generic_target_csm == downlink
                && !programming_owns;

            assign sca_enable[downlink] = programming_owns
                ? ({{(SCA_COUNT-1){1'b0}}, 1'b1}
                   << programming_target_sca)
                : (generic_owns ? generic_enable : {SCA_COUNT{1'b0}});
            assign sca_start_reset[downlink] = generic_owns
                && generic_start_reset;
            assign sca_start_connect[downlink] = generic_owns
                && generic_start_connect;
            assign sca_start_command[downlink] = programming_owns
                ? programming_start_command
                : (generic_owns && generic_start_command);

            assign sca_address[downlink] = programming_owns
                ? programming_address
                : (generic_owns ? generic_address : 8'b0);
            assign sca_transid[downlink] = programming_owns
                ? programming_transid
                : (generic_owns ? generic_transid : 8'b0);
            assign sca_channel[downlink] = programming_owns
                ? programming_channel
                : (generic_owns ? generic_channel : 8'b0);
            assign sca_command[downlink] = programming_owns
                ? programming_command
                : (generic_owns ? generic_command : 8'b0);
            assign sca_data[downlink] = programming_owns
                ? programming_data
                : (generic_owns ? generic_data : 32'b0);
        end
    endgenerate

endmodule
