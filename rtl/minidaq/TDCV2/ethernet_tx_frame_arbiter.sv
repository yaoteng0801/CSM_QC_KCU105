// Frame-level two-input AXI-Stream arbiter.
//
// Hierarchy and current subsystem use:
//
//   Parent: minidaq_ethernet_subsystem.control_class_arbiter
//   Children: none; this is a registered frame grant plus AXI routing
//
//   generic control response -- hit_* input -----+
//                                                   +--> combined control
//   programming ACK/NACK ----- control_* input --+       -> tx_qos
//
// The hit_* and control_* names are generic legacy port names. At this parent
// hierarchy level they carry two control-plane sources, not detector hit data.
// Input control_* has idle-boundary priority, so programming ACKs win over a
// simultaneously waiting generic control response. All ports use tx_clk.
//
// Programming/control responses have priority only while no frame owns the
// output.  Once the first byte of either input frame is accepted, grant is held
// through that input's successful TLAST transfer.  Therefore a control ACK can
// never be inserted into the middle of a hit-data frame, and a hit-data frame
// can never split an ACK.

`timescale 1ns / 1ps

module ethernet_tx_frame_arbiter (
    // All three AXI streams use the same TEMAC transmit clock.
    input  wire       clk,
    input  wire       rst,

    // Lower-priority input; generic-control replies in the current hierarchy.
    input  wire [7:0] hit_tdata,
    input  wire       hit_tvalid,
    output wire       hit_tready,
    input  wire       hit_tlast,

    // Higher-priority input; programming ACK/NACK in the current hierarchy.
    input  wire [7:0] control_tdata,
    input  wire       control_tvalid,
    output wire       control_tready,
    input  wire       control_tlast,

    // Combined control-class stream connected to the final TX QoS arbiter.
    output wire [7:0] tx_tdata,
    output wire       tx_tvalid,
    input  wire       tx_tready,
    output wire       tx_tlast
);

    localparam logic [1:0] GRANT_IDLE = 2'd0;
    localparam logic [1:0] GRANT_HIT  = 2'd1;
    localparam logic [1:0] GRANT_CTRL = 2'd2;
    reg [1:0] grant = GRANT_IDLE;

    // Route ready only to the selected producer. While idle, control has
    // priority; if it is not valid, hit data can start immediately. Continuous
    // assignments keep this AXI routing purely feed-forward when arbiters are
    // cascaded by the application-level Ethernet wrapper.
    wire select_control = (grant == GRANT_CTRL)
                        || ((grant == GRANT_IDLE) && control_tvalid);
    wire select_hit = (grant == GRANT_HIT)
                    || ((grant == GRANT_IDLE) && !control_tvalid);

    assign tx_tdata = select_control ? control_tdata
                    : (select_hit ? hit_tdata : 8'b0);
    assign tx_tvalid = select_control ? control_tvalid
                     : (select_hit ? hit_tvalid : 1'b0);
    assign tx_tlast = select_control ? control_tlast
                    : (select_hit ? hit_tlast : 1'b0);
    assign control_tready = select_control ? tx_tready : 1'b0;
    assign hit_tready = select_hit ? tx_tready : 1'b0;

    // Lock the selected producer after its first non-final byte transfers.
    // A complete one-byte frame needs no stored grant because its first
    // transfer is also its TLAST transfer.
    always @(posedge clk) begin
        if (rst) begin
            grant <= GRANT_IDLE;
        end else begin
            case (grant)
                GRANT_IDLE: begin
                    if (control_tvalid) begin
                        if (!(tx_tready && control_tlast))
                            grant <= GRANT_CTRL;
                    end else if (hit_tvalid) begin
                        if (!(tx_tready && hit_tlast))
                            grant <= GRANT_HIT;
                    end
                end
                GRANT_HIT: begin
                    if (hit_tvalid && tx_tready && hit_tlast)
                        grant <= GRANT_IDLE;
                end
                GRANT_CTRL: begin
                    if (control_tvalid && tx_tready && control_tlast)
                        grant <= GRANT_IDLE;
                end
                default: grant <= GRANT_IDLE;
            endcase
        end
    end

endmodule
