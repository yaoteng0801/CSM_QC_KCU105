`timescale 1ns / 1ps
//-------------------------------------------------------
//! eth_init_fsm - Deterministic AXI4-Lite hardware init sequencer for daq_axi_ethernet
//! New for Stage 3 (KCU105 Ethernet migration). There is no MicroBlaze/CPU/AXI-Lite processor
//! anywhere in this design (matches the source MiniDAQ project, which also has none -- its
//! RGMII tri_mode_ethernet_mac used an XDC-only reset sequence plus Xilinx's own
//! tri_mode_ethernet_mac_0_axi_lite_sm.v example-design init state machine for exactly the
//! same reason: a non-CPU register bring-up sequencer). This is that sequencer's Stage 3
//! counterpart, hand-written for axi_ethernet's own AXI4-Lite management interface, since
//! axi_ethernet's example design's own init state machine is bundled as part of a Block-
//! Design-based example project, not a standalone RTL file this pure-RTL-flow repo can just
//! drop in.
//!
//! Sequence, once mmcm_locked_i (daq_axi_ethernet's MMCM, fed from the real 625MHz onboard-PHY
//! reference) and idelay_rdy_i are both asserted and rst_125_i (the IP's own internally-
//! sequenced AXI4-Stream/AXI4-Lite-domain reset release) has cleared:
//!   1. Write Speed Config (offset 0x410) = 32'h8000_0000 -- bits[31:30]=2'b10, forces 1000Mbps,
//!      matching this design's fixed SGMII/1000BASE-X link (no runtime renegotiation supported).
//!   2. Write RCW1         (offset 0x404) = 32'h9000_0000 -- Reset(bit31)+Receiver Enable(bit28).
//!   3. Write TC           (offset 0x408) = 32'h9000_0000 -- Reset(bit31)+Transmitter Enable(bit28).
//!   4. Write Flow Control (offset 0x40C) = 32'h0000_0000 -- pause-frame generation/reception
//!      disabled (this design implements no flow-control response logic).
//!   5. Assert done_o and hold (no further AXI4-Lite traffic needed for basic TX operation --
//!      this design has no Ethernet RX/command path to service, see rtl/daq/ethernet's own
//!      top-level integration comment for why).
//!
//! REGISTER MAP SOURCE (no longer a memory-only guess): all 4 offsets and exact write values
//! above are copied directly from the real MiniDAQ source project's own equivalent sequencer,
//! D:\phase2_KCU105\firmware\sources\tri_mode_ethernet_mac\tri_mode_ethernet_mac_0_axi_lite_sm.v
//! (RECEIVER_ADD=0x404/TRANSMITTER_ADD=0x408/CONFIG_FLOW_CTRL_ADD=0x40C/SPEED_CONFIG_ADD=0x410,
//! states RESET_MAC_RX/RESET_MAC_TX/CNFG_FLOW/UPDATE_SPEED) -- this repo's installed Vivado still
//! doesn't bundle xaxiethernet_hw.h to double-cross-check axi_ethernet's own copy of this same
//! register map, but it is no longer sourced from recollection alone. An earlier version of this
//! file guessed a 3rd, different offset/value combination (0x40C read as a speed register) before
//! this source file was consulted -- corrected.
//!
//! PHY MDIO bring-up (Stage 4 Step 2, appended after the 4 MAC writes above -- that sequence
//! itself is untouched, same states/addresses/values/order as before, so its own existing
//! verification in sim/daq/tb_eth_init_fsm.sv still covers it unchanged):
//!   6. Write MDIO Setup   (offset 0x500) = 32'h0000_0058 -- enables the MDIO controller and
//!      sets MDC = aclk/24, the exact divide value the source FSM's own STARTUP-state comment
//!      documents for "125MHz s_axi_aclk" -- a real match here, since daq_axi_ethernet's
//!      s_axi_lite_clk genuinely is its own 125MHz clk125_out (not the source's later, second
//!      MDIO Setup write of 0x68, which the source only reaches after its own MAC-reset
//!      sequence and is not otherwise explained by that file's own comments as clock-matched).
//!   7-8, 9-10, 11-12. Write MDIO Tx Data (0x508) then MDIO Control (0x504) for 3 back-to-back
//!      PHY register writes, each followed by a fixed settle wait (MDIO_SETTLE_CYCLES below)
//!      before the next: 1000BASE-T Control Reg (IEEE reg 0x9) = 32'h0000_0200 (advertise
//!      1000Mbps full-duplex only -- this design's link is always forced 1000Mbps, matching
//!      the Speed Config write already made to the MAC); Auto-Neg Ability Reg (IEEE reg 0x4) =
//!      32'h0000_0000 (advertise nothing at 10/100, since 1000-only is being forced); Control
//!      Reg (IEEE reg 0x0) = 32'h0000_9000 (bit15 PHY software reset, bit12 autonegotiation
//!      enable). Every MDIO Control write encodes {PHY_ADDR=8'h07, REG_ADDR, MDIO_OP=2'b01
//!      (write), 3'h1, 11'h0} -- the exact word format the source FSM's own mdio_access_sm
//!      builds (D:\phase2_KCU105\firmware\sources\tri_mode_ethernet_mac\
//!      tri_mode_ethernet_mac_0_axi_lite_sm.v, states IDLE/SET_DATA/INIT), reusing daq_axi_
//!      ethernet's real MDIO Setup/Control/Tx Data/Rx Data register offsets (0x500/0x504/
//!      0x508/0x50C -- confirmed identical to the source's own values by cross-checking
//!      ip/daq_axi_ethernet/header_files/daq_axi_ethernet_axi4_lite_registers.h, since the
//!      underlying MAC in both is the same tri_mode_ethernet_mac core).
//!
//!   PHY_ADDR=8'h07 is not a guess: AMD/Xilinx's own Adaptive Support answer for this exact
//!   board confirms the KCU105's onboard Marvell 88E1111 powers up strapped to MDIO address
//!   0b00111 (=7) in SGMII mode (adaptivesupport.amd.com, "How to connect Ethernet PHY MARVELL
//!   88E1111 via SGMII to KINTEX ULTRASCALE?") -- the same numeric value the source's own
//!   (SP605-specific, RGMII) PHY_ADDR happened to use, confirmed independently for KCU105/SGMII
//!   rather than carried over on the strength of that coincidence alone.
//!
//!   Deliberately NOT ported from the source FSM, all for the same reason -- this design only
//!   needs the PHY physically link-trained and sending/receiving SGMII correctly; the source's
//!   own host software this repo's firmware talks to already handles the DAQ readout protocol
//!   end to end (raw broadcast-style Ethernet-II frames, no ARP/IP/handshake -- see
//!   daq_ethernet_top.v's header), so nothing beyond physical link-up is a feature this design
//!   needs:
//!     - MDIO_RGMII/MDIO_DELAY (source's non-IEEE Mode Control/Status reg 0x14/0x1b writes):
//!       these configure an RGMII electrical-interface PHY strap; the KCU105 Marvell 88E1111
//!       is already strapped to SGMII mode by the board itself (same AMD source as above), so
//!       writing an RGMII-mode-specific register here would be wrong for this interface, not
//!       just unnecessary.
//!     - The MDIO_RD "is a PHY even present" liveness check: the KCU105's PHY is populated
//!       hardware, not an optional demo-board jumper, so this check has nothing to detect.
//!     - MDIO_LOOPBACK (source's phy_loopback branch): a bring-up/test mode, not part of normal
//!       operation.
//!
//!   MDIO_SETTLE_CYCLES=4096 (at clk125's 8ns period, 32.8us) is a fixed wait after each MDIO
//!   Control write, not a handshake poll: one full MDIO transaction (32-bit preamble + 32-bit
//!   frame) at the 2.5MHz MDC this FSM's own Setup write configures takes at most 64/2.5MHz =
//!   25.6us; 4096 cycles is a >25% margin above that.
//!
//! Autonegotiation-complete polling (Stage 4, added after Step 2's own initial simplification
//! -- see MDIO_SETTLE_CYCLES above for the timing derivation still used for each individual
//! transaction's settle time): after the 3 PHY register writes above, this FSM now polls the
//! PHY's own Status Register (IEEE reg 0x1) via a real AXI4-Lite read, matching the source's
//! own MDIO_STATS/MDIO_STATS_POLL_CHECK loop (checking bit5=Auto-Negotiation-Complete and
//! bit16=MDIO-transaction-ready, exactly as the source's own axi_rd_data[5]/axi_rd_data[16]
//! check does) instead of firing the writes once and declaring done. Each poll iteration:
//! write MDIO Control requesting a read of reg 0x1 (same {PHY_ADDR,reg,op,...} word format as
//! every other MDIO Control write here, with MDIO_OP=2'b10=read), settle, then issue a real
//! AXI4-Lite read of MDIO Rx Data (0x50C) and check the result. Bounded at
//! MDIO_POLL_MAX_ITERATIONS (200, ~6.6ms total at the settle time above) rather than polling
//! forever -- if autonegotiation genuinely never completes (e.g. no cable plugged in), done_o
//! still asserts once the bound is hit, since done_o has always meant "no further AXI4-Lite
//! register traffic queued", not "link is physically up" (that is what the RJ45 jack's own
//! link LED and vio_lpgbt_debug's eth probes show independently).
//!
//! The AXI4-Lite master sequencing (one outstanding write at a time, proper AWVALID/WVALID/
//! BVALID handshaking, plus the read channel added for the polling above) is independently
//! verified in sim/daq/tb_eth_init_fsm.sv against a minimal AXI4-Lite slave model.
//-------------------------------------------------------
module eth_init_fsm (
    input  wire        clk,          // = daq_axi_ethernet's clk125_out (s_axi_lite_clk)
    input  wire        aresetn,      // = ~rst_125_i, i.e. active-low, released once the IP's
                                      // own internal reset sequencing completes
    input  wire        mmcm_locked_i,
    input  wire        idelay_rdy_i,

    // AXI4-Lite master, write channel (the 11 MAC/MDIO-config writes)
    output reg  [17:0] m_axi_awaddr,
    output reg         m_axi_awvalid,
    input  wire        m_axi_awready,
    output reg  [31:0] m_axi_wdata,
    output reg  [3:0]  m_axi_wstrb,
    output reg         m_axi_wvalid,
    input  wire        m_axi_wready,
    input  wire [1:0]  m_axi_bresp,
    input  wire        m_axi_bvalid,
    output reg         m_axi_bready,

    // AXI4-Lite master, read channel (Stage 4 -- added solely for the autonegotiation-complete
    // poll below; nothing else in this FSM reads back)
    output reg  [17:0] m_axi_araddr,
    output reg         m_axi_arvalid,
    input  wire        m_axi_arready,
    input  wire [31:0] m_axi_rdata,
    input  wire [1:0]  m_axi_rresp,
    input  wire        m_axi_rvalid,
    output reg         m_axi_rready,

    output reg         done_o
);

    localparam ADDR_SPEED = 18'h410;
    localparam ADDR_RCW1  = 18'h404;
    localparam ADDR_TC    = 18'h408;
    localparam ADDR_FLOW  = 18'h40C;

    localparam DATA_SPEED_1000M = 32'h8000_0000; // bits[31:30] = 2'b10 -> force 1000Mbps
    localparam DATA_RCW1_RSTEN  = 32'h9000_0000; // Reset(bit31) + Receiver Enable(bit28)
    localparam DATA_TC_RSTEN    = 32'h9000_0000; // Reset(bit31) + Transmitter Enable(bit28)
    localparam DATA_FLOW_OFF    = 32'h0000_0000; // pause-frame gen/reception disabled

    // MDIO PHY bring-up (Stage 4 Step 2) -- see header for the full derivation. Steps 0-3
    // above are unchanged; steps 4-10 below are new, appended after them.
    localparam ADDR_MDIO_SETUP   = 18'h500;
    localparam ADDR_MDIO_CONTROL = 18'h504;
    localparam ADDR_MDIO_TXDATA  = 18'h508;

    localparam DATA_MDIO_ENABLE  = 32'h0000_0058; // enable MDIO, MDC = aclk/24 (125MHz aclk)
    localparam DATA_PHY_1000ADV  = 32'h0000_0200; // 1000BASE-T Control: advertise 1000-full only
    localparam DATA_PHY_1010ADV  = 32'h0000_0000; // Auto-Neg Ability: advertise nothing at 10/100
    localparam DATA_PHY_RESTART  = 32'h0000_9000; // Control: bit15 SW reset, bit12 AN enable

    localparam [7:0] PHY_ADDR              = 8'h07; // KCU105 onboard Marvell 88E1111, confirmed (see header)
    localparam [7:0] PHY_REG_1000BASET_CTL = 8'h09;
    localparam [7:0] PHY_REG_ABILITY       = 8'h04;
    localparam [7:0] PHY_REG_CONTROL       = 8'h00;
    localparam [7:0] PHY_REG_STATUS        = 8'h01;
    localparam [1:0] MDIO_OP_WR            = 2'b01;
    localparam [1:0] MDIO_OP_RD            = 2'b10;

    // {PHY_ADDR, reg_addr, op, 3'h1, 11'h0} -- exact word format the source FSM's own
    // mdio_access_sm builds for MDIO Control (see header). Same format for a read (op=2'b10)
    // as for a write -- only the op field differs.
    localparam DATA_MDIO_CTRL_1000BASET   = {PHY_ADDR, PHY_REG_1000BASET_CTL, MDIO_OP_WR, 3'h1, 11'h0};
    localparam DATA_MDIO_CTRL_ABILITY     = {PHY_ADDR, PHY_REG_ABILITY,       MDIO_OP_WR, 3'h1, 11'h0};
    localparam DATA_MDIO_CTRL_CONTROL     = {PHY_ADDR, PHY_REG_CONTROL,       MDIO_OP_WR, 3'h1, 11'h0};
    localparam DATA_MDIO_CTRL_READ_STATUS = {PHY_ADDR, PHY_REG_STATUS,       MDIO_OP_RD, 3'h1, 11'h0};

    localparam ADDR_MDIO_RXDATA = 18'h50C;

    localparam MDIO_SETTLE_CYCLES = 13'd4096; // ~32.8us at clk125 -- see header derivation
    localparam MDIO_POLL_MAX_ITERATIONS = 9'd200; // ~6.6ms total -- see header derivation

    // Flat step list, one (address, data) pair per AXI4-Lite write, in issue order. Steps 0-3
    // are exactly the pre-Step-2 sequence, same addresses/values/order. Steps 4-10 are the
    // MDIO bring-up (Stage 4 Step 2): 4 is a single register-enable write; 5/7/9 each write
    // MDIO Tx Data for one PHY register, immediately followed by 6/8/10 writing MDIO Control to
    // launch that transaction (a fixed settle wait follows each of 6/8/10 -- see NEEDS_SETTLE
    // below). Step 11 (Stage 4, autoneg polling) writes MDIO Control requesting a read of the
    // PHY's Status Register -- issued once per poll iteration, see the S_POLL_* states below.
    localparam [3:0] STEP_LAST = 4'd11;

    reg [3:0]  state_step;
    reg [17:0] step_addr;
    reg [31:0] step_data;
    reg        step_needs_settle;

    always @(*) begin
        case (state_step)
            4'd0:  begin step_addr = ADDR_SPEED;        step_data = DATA_SPEED_1000M;        step_needs_settle = 1'b0; end
            4'd1:  begin step_addr = ADDR_RCW1;         step_data = DATA_RCW1_RSTEN;          step_needs_settle = 1'b0; end
            4'd2:  begin step_addr = ADDR_TC;           step_data = DATA_TC_RSTEN;            step_needs_settle = 1'b0; end
            4'd3:  begin step_addr = ADDR_FLOW;         step_data = DATA_FLOW_OFF;            step_needs_settle = 1'b0; end
            4'd4:  begin step_addr = ADDR_MDIO_SETUP;   step_data = DATA_MDIO_ENABLE;         step_needs_settle = 1'b0; end
            4'd5:  begin step_addr = ADDR_MDIO_TXDATA;  step_data = DATA_PHY_1000ADV;         step_needs_settle = 1'b0; end
            4'd6:  begin step_addr = ADDR_MDIO_CONTROL; step_data = DATA_MDIO_CTRL_1000BASET; step_needs_settle = 1'b1; end
            4'd7:  begin step_addr = ADDR_MDIO_TXDATA;  step_data = DATA_PHY_1010ADV;         step_needs_settle = 1'b0; end
            4'd8:  begin step_addr = ADDR_MDIO_CONTROL; step_data = DATA_MDIO_CTRL_ABILITY;   step_needs_settle = 1'b1; end
            4'd9:  begin step_addr = ADDR_MDIO_TXDATA;  step_data = DATA_PHY_RESTART;         step_needs_settle = 1'b0; end
            4'd10: begin step_addr = ADDR_MDIO_CONTROL; step_data = DATA_MDIO_CTRL_CONTROL;   step_needs_settle = 1'b1; end
            default /*11*/: begin step_addr = ADDR_MDIO_CONTROL; step_data = DATA_MDIO_CTRL_READ_STATUS; step_needs_settle = 1'b1; end
        endcase
    end

    localparam S_WAIT_READY     = 4'd0,
               S_ISSUE_WRITE    = 4'd1,
               S_WAIT_AW        = 4'd2,
               S_WAIT_B         = 4'd3,
               S_SETTLE         = 4'd4,
               S_NEXT           = 4'd5,
               S_POLL_READ_ADDR = 4'd6,
               S_POLL_READ_DATA = 4'd7,
               S_DONE           = 4'd8;

    reg  [3:0]  state;
    reg  [12:0] settle_count;
    reg  [8:0]  poll_count;

    always @(posedge clk) begin
        if (!aresetn) begin
            state         <= S_WAIT_READY;
            state_step    <= 4'd0;
            settle_count  <= 13'd0;
            poll_count    <= 9'd0;
            m_axi_awaddr  <= 18'd0;
            m_axi_awvalid <= 1'b0;
            m_axi_wdata   <= 32'd0;
            m_axi_wstrb   <= 4'b0000;
            m_axi_wvalid  <= 1'b0;
            m_axi_bready  <= 1'b0;
            m_axi_araddr  <= 18'd0;
            m_axi_arvalid <= 1'b0;
            m_axi_rready  <= 1'b0;
            done_o        <= 1'b0;
        end else begin
            case (state)
                S_WAIT_READY: begin
                    if (mmcm_locked_i && idelay_rdy_i) begin
                        state <= S_ISSUE_WRITE;
                    end
                end

                S_ISSUE_WRITE: begin
                    m_axi_awaddr  <= step_addr;
                    m_axi_wdata   <= step_data;
                    m_axi_wstrb   <= 4'b1111;
                    m_axi_awvalid <= 1'b1;
                    m_axi_wvalid  <= 1'b1;
                    state         <= S_WAIT_AW;
                end

                // AWVALID and WVALID are asserted together above and each held until its own
                // *ready arrives independently (a slave may accept AW and W in either order,
                // or the same cycle) -- track them separately rather than assuming lockstep.
                S_WAIT_AW: begin
                    if (m_axi_awready) m_axi_awvalid <= 1'b0;
                    if (m_axi_wready)  m_axi_wvalid  <= 1'b0;
                    if ((m_axi_awready || !m_axi_awvalid) && (m_axi_wready || !m_axi_wvalid)) begin
                        state <= S_WAIT_B;
                        m_axi_bready <= 1'b1;
                    end
                end

                S_WAIT_B: begin
                    if (m_axi_bvalid) begin
                        m_axi_bready <= 1'b0;
                        // m_axi_bresp is not checked beyond acceptance: on a real SLVERR/DECERR
                        // there is no register-map fallback to retry with, and this FSM's own
                        // AXI4-Lite protocol sequencing (the part independently verified here)
                        // is unaffected either way.
                        if (step_needs_settle) begin
                            settle_count <= 13'd0;
                            state        <= S_SETTLE;
                        end else begin
                            state <= S_NEXT;
                        end
                    end
                end

                // Only entered after an MDIO Control write actually launches a PHY MDIO
                // transaction (step_needs_settle) -- see header for the timing derivation.
                S_SETTLE: begin
                    if (settle_count == MDIO_SETTLE_CYCLES) begin
                        state <= S_NEXT;
                    end else begin
                        settle_count <= settle_count + 13'd1;
                    end
                end

                S_NEXT: begin
                    if (state_step == STEP_LAST) begin
                        // Step 11's write just launched an MDIO read of the PHY's Status
                        // Register -- go collect the result over the real AXI4-Lite read
                        // channel instead of the old "declare done" shortcut.
                        state <= S_POLL_READ_ADDR;
                    end else begin
                        state_step <= state_step + 4'd1;
                        state      <= S_ISSUE_WRITE;
                    end
                end

                S_POLL_READ_ADDR: begin
                    m_axi_araddr  <= ADDR_MDIO_RXDATA;
                    m_axi_arvalid <= 1'b1;
                    if (m_axi_arvalid && m_axi_arready) begin
                        m_axi_arvalid <= 1'b0;
                        m_axi_rready  <= 1'b1;
                        state         <= S_POLL_READ_DATA;
                    end
                end

                S_POLL_READ_DATA: begin
                    if (m_axi_rvalid) begin
                        m_axi_rready <= 1'b0;
                        // m_axi_rresp not checked, same reasoning as m_axi_bresp above.
                        // Bit16 = MDIO transaction ready/done, bit5 = Auto-Negotiation Complete
                        // -- matches the source's own axi_rd_data[16]/axi_rd_data[5] check
                        // (MDIO_STATS_POLL_CHECK) exactly.
                        if ((m_axi_rdata[16] && m_axi_rdata[5]) ||
                            poll_count == MDIO_POLL_MAX_ITERATIONS) begin
                            state <= S_DONE;
                        end else begin
                            // Not ready yet -- re-issue step 11's write (re-reads Status) after
                            // another settle wait.
                            poll_count   <= poll_count + 9'd1;
                            settle_count <= 13'd0;
                            state        <= S_ISSUE_WRITE;
                        end
                    end
                end

                S_DONE: begin
                    done_o <= 1'b1;
                end

                default: state <= S_WAIT_READY;
            endcase
        end
    end

endmodule
