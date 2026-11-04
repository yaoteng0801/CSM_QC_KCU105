//------------------------------------------------------------------------------
// File       : tri_mode_ethernet_mac_0_example_design.v   (KCU105 SGMII variant)
//
// KCU105 replacement for the upstream MiniDAQ Ethernet MAC wrapper of the same name
// (ref_upstream/tri_mode_ethernet_mac/tri_mode_ethernet_mac_0_example_design.v, which wraps an
// RGMII TEMAC for the MiniDAQ board's PHY).  The USER-SIDE interface is identical -- 8-bit
// AXI4-Stream RX and TX FIFO ports clocked by the 125 MHz MAC clock, bad frames dropped by the RX
// FIFO, rx_axis_fifo_overflow flag -- so minidaq_ethernet_subsystem and everything behind it is
// untouched.  Only the PHY side differs:
//
//   upstream (MiniDAQ board)             this file (KCU105)
//   ---------------------------------    -----------------------------------------------------
//   TEMAC, Physical_Interface = RGMII    TEMAC, Physical_Interface = Internal (SGMII), GMII to
//   320 MHz oscillator -> rgmii_clk MMCM   gig_ethernet_pcs_pma (LVDS SGMII, shared logic in core)
//   gtx_clk = rgmii_clk MMCM output      gtx_clk = clk125_out of the PCS/PMA core, which derives
//                                          it from the PHY's 625 MHz reference (SGMIICLK_P/N)
//   tri_mode_ethernet_mac_0_axi_lite_sm  eth_init_fsm (MAC speed/enable + Marvell 88E1111 MDIO
//     (RGMII PHY delay setup)              bring-up for SGMII; register map identical, same core)
//   phy_resetn from a 64-cycle counter   phy_resetn held low 15 ms after configuration, timed by a
//                                          free-running clock (free_clk): the PHY itself generates
//                                          the 625 MHz SGMII clock, so the PHY-derived clk125 cannot
//                                          time its own reset (that deadlocked the first build)
//
// The TEMAC <-> PCS/PMA hookup (clk_enable <- sgmii_clk_en, gtx_clk <- clk125_out, speedis100 /
// speedis10100 -> speed_is_100 / speed_is_10_100, MDIO chained through the PCS/PMA core,
// phyaddr = 1, configuration_vector = 5'b10000 = auto-negotiation enabled) is the structure the
// Stage-3 AXI Ethernet subsystem generated internally (ip/daq_axi_ethernet/.../bd_4f5a.v).
//
// Verified on a KCU105 board.
//------------------------------------------------------------------------------

`timescale 1 ps/1 ps

module tri_mode_ethernet_mac_0_example_design
   (
      // asynchronous reset, active high (upstream: power_on_reset_40)
      input         glbl_rst,
      // free-running clock that does not depend on the PHY (KCU105 top: mgt_freedrpclk, 100 MHz)
      input         free_clk,

      output        gtx_clk_bufg_out,     // 125 MHz MAC / user clock
      output        phy_resetn,

      // SGMII interface to the onboard Marvell 88E1111
      //-----------------------------------------------
      input         sgmii_refclk625_p,    // 625 MHz reference from the PHY
      input         sgmii_refclk625_n,
      output        sgmii_txp,
      output        sgmii_txn,
      input         sgmii_rxp,
      input         sgmii_rxn,

      // MDIO Interface
      //---------------
      inout         mdio,
      output        mdc,

      // USER side RX AXI-S interface
      output        rx_axis_fifo_aclk,
      output        rx_axis_fifo_aresetn,
      output [7:0]  rx_axis_fifo_tdata,
      output        rx_axis_fifo_tvalid,
      input         rx_axis_fifo_tready,
      output        rx_axis_fifo_tlast,
      output        rx_axis_fifo_overflow,

      // USER side TX AXI-S interface
      input  [7:0]  tx_axis_fifo_tdata,
      input         tx_axis_fifo_tvalid,
      output        tx_axis_fifo_tready,
      input         tx_axis_fifo_tlast
    );

   //---------------------------------------------------------------------------
   // PCS/PMA <-> TEMAC glue signals
   //---------------------------------------------------------------------------
   wire         gtx_clk_bufg;             // = clk125_out
   wire         rst_125;                  // PCS/PMA's internally sequenced 125 MHz-domain reset
   wire         mmcm_locked;
   wire         idelay_rdy;
   wire         sgmii_clk_en;
   wire         speed_is_100;
   wire         speed_is_10_100;

   wire [7:0]   gmii_txd;
   wire         gmii_tx_en;
   wire         gmii_tx_er;
   wire [7:0]   gmii_rxd;
   wire         gmii_rx_dv;
   wire         gmii_rx_er;

   wire         mac_mdc;
   wire         mac_mdio_o;
   wire         mac_mdio_t;
   wire         pcs_mdio_o;

   wire         ext_mdc;
   wire         ext_mdio_i;
   wire         ext_mdio_o;
   wire         ext_mdio_t;

   assign gtx_clk_bufg_out = gtx_clk_bufg;
   assign mdc              = ext_mdc;

   //---------------------------------------------------------------------------
   // Resets
   //---------------------------------------------------------------------------
   wire         pcs_ready_sync;
   wire         glbl_rst_int;
   wire         glbl_rst_intn;
   wire         s_axi_reset_int;
   reg          s_axi_pre_resetn = 1'b0;
   reg          s_axi_resetn     = 1'b0;
   wire         gtx_clk_reset_int;
   reg          gtx_pre_resetn   = 1'b0;
   reg          gtx_resetn       = 1'b0;
   reg          phy_resetn_int   = 1'b0;

   wire         rx_reset;
   wire         tx_reset;

   tri_mode_ethernet_mac_0_sync_block pcs_ready_sync_i (
      .clk              (gtx_clk_bufg),
      .data_in          (mmcm_locked & idelay_rdy),
      .data_out         (pcs_ready_sync)
   );

   // core reset: asynchronous assert, synchronous release, held while the PCS/PMA clocking is not
   // ready (reset_sync's enable is the flops' clock-enable)
   tri_mode_ethernet_mac_0_reset_sync glbl_reset_gen (
      .clk              (gtx_clk_bufg),
      .enable           (pcs_ready_sync),
      .reset_in         (glbl_rst | rst_125),
      .reset_out        (glbl_rst_int)
   );
   assign glbl_rst_intn = !glbl_rst_int;

   // PHY reset: low for 1,500,000 free_clk cycles (15 ms at 100 MHz; the 88E1111 needs >= 10 ms)
   // after configuration, then released for good.  It MUST NOT be clocked by gtx_clk_bufg: on the
   // KCU105 the 625 MHz SGMIICLK that the PCS/PMA turns into gtx_clk_bufg is generated by the PHY
   // itself (88E1111 SOUT_P/N, schematic sheet 38), and a PHY held in reset produces no clock -- the
   // first port deadlocked there (no copper link, "network media is disconnected" on the host).
   // Nor does it wait for glbl_rst (power_on_reset_40 needs the 320 MHz MGT reference), so the
   // copper link comes up even before the lpGBT clocks run; the MAC side stays in reset as upstream.
   reg  [20:0]  phy_reset_count  = 21'd0;
   always @(posedge free_clk)
   begin
      if (phy_reset_count != 21'd1500000) begin
         phy_reset_count <= phy_reset_count + 1'b1;
         phy_resetn_int  <= 1'b0;
      end
      else begin
         phy_resetn_int  <= 1'b1;
      end
   end
   assign phy_resetn = phy_resetn_int;

   wire         phy_resetn_gtx;
   tri_mode_ethernet_mac_0_sync_block phy_resetn_sync_i (
      .clk              (gtx_clk_bufg),
      .data_in          (phy_resetn_int),
      .data_out         (phy_resetn_gtx)
   );

   // AXI-Lite domain (init FSM + TEMAC management) is held until the PHY is out of reset
   tri_mode_ethernet_mac_0_reset_sync axi_lite_reset_gen (
      .clk              (gtx_clk_bufg),
      .enable           (phy_resetn_gtx),
      .reset_in         (glbl_rst | rst_125),
      .reset_out        (s_axi_reset_int)
   );
   always @(posedge gtx_clk_bufg)
   begin
      if (s_axi_reset_int) begin
         s_axi_pre_resetn <= 1'b0;
         s_axi_resetn     <= 1'b0;
      end
      else begin
         s_axi_pre_resetn <= 1'b1;
         s_axi_resetn     <= s_axi_pre_resetn;
      end
   end

   // user-side FIFO resets (also follow the MAC's own tx/rx resets)
   tri_mode_ethernet_mac_0_reset_sync gtx_reset_gen (
      .clk              (gtx_clk_bufg),
      .enable           (pcs_ready_sync),
      .reset_in         (glbl_rst | rst_125 | rx_reset | tx_reset),
      .reset_out        (gtx_clk_reset_int)
   );
   always @(posedge gtx_clk_bufg)
   begin
      if (gtx_clk_reset_int) begin
         gtx_pre_resetn <= 1'b0;
         gtx_resetn     <= 1'b0;
      end
      else begin
         gtx_pre_resetn <= 1'b1;
         gtx_resetn     <= gtx_pre_resetn;
      end
   end

   assign rx_axis_fifo_aclk    = gtx_clk_bufg;
   assign rx_axis_fifo_aresetn = gtx_resetn;
   wire   tx_fifo_clock        = gtx_clk_bufg;
   wire   tx_fifo_resetn       = gtx_resetn;

   //---------------------------------------------------------------------------
   // SGMII PCS/PMA (LVDS, shared logic in core)
   //---------------------------------------------------------------------------
   gig_ethernet_pcs_pma_0 pcs_pma (
      .txp                  (sgmii_txp),
      .txn                  (sgmii_txn),
      .rxp                  (sgmii_rxp),
      .rxn                  (sgmii_rxn),
      .refclk625_p          (sgmii_refclk625_p),
      .refclk625_n          (sgmii_refclk625_n),
      .mmcm_locked_out      (mmcm_locked),
      .idelay_rdy_out       (idelay_rdy),
      .sgmii_clk_r          (),
      .sgmii_clk_f          (),
      .sgmii_clk_en         (sgmii_clk_en),
      .clk125_out           (gtx_clk_bufg),
      .clk625_out           (),
      .clk312_out           (),
      .rst_125_out          (rst_125),
      .gmii_txd             (gmii_txd),
      .gmii_tx_en           (gmii_tx_en),
      .gmii_tx_er           (gmii_tx_er),
      .gmii_rxd             (gmii_rxd),
      .gmii_rx_dv           (gmii_rx_dv),
      .gmii_rx_er           (gmii_rx_er),
      .gmii_isolate         (),
      .mdc                  (mac_mdc),
      .mdio_i               (mac_mdio_o),
      .mdio_o               (pcs_mdio_o),
      .mdio_t               (),
      .mdio_t_in            (mac_mdio_t),
      .ext_mdc              (ext_mdc),
      .ext_mdio_i           (ext_mdio_i),
      .ext_mdio_o           (ext_mdio_o),
      .ext_mdio_t           (ext_mdio_t),
      .phyaddr              (5'd1),
      .configuration_vector (5'b10000),    // bit 4: auto-negotiation enable
      .configuration_valid  (1'b1),
      .an_interrupt         (),
      .an_adv_config_vector (16'd0),
      .an_adv_config_val    (1'b0),
      .an_restart_config    (1'b0),
      .speed_is_10_100      (speed_is_10_100),
      .speed_is_100         (speed_is_100),
      .status_vector        (),
      .reset                (glbl_rst),
      .signal_detect        (1'b1)         // no optical module on the PHY side
   );

   // MDIO pad
   IOBUF mdio_iobuf (
      .I  (ext_mdio_o),
      .O  (ext_mdio_i),
      .T  (ext_mdio_t),
      .IO (mdio)
   );

   //---------------------------------------------------------------------------
   // AXI-Lite initialisation of the TEMAC (speed, enables) and the PHY (MDIO)
   //---------------------------------------------------------------------------
   wire [11:0]  s_axi_awaddr;
   wire         s_axi_awvalid;
   wire         s_axi_awready;
   wire [31:0]  s_axi_wdata;
   wire         s_axi_wvalid;
   wire         s_axi_wready;
   wire [1:0]   s_axi_bresp;
   wire         s_axi_bvalid;
   wire         s_axi_bready;
   wire [11:0]  s_axi_araddr;
   wire         s_axi_arvalid;
   wire         s_axi_arready;
   wire [31:0]  s_axi_rdata;
   wire [1:0]   s_axi_rresp;
   wire         s_axi_rvalid;
   wire         s_axi_rready;

   wire [17:0]  init_awaddr;
   wire [17:0]  init_araddr;
   assign s_axi_awaddr = init_awaddr[11:0];
   assign s_axi_araddr = init_araddr[11:0];

   eth_init_fsm axi_lite_controller (
      .clk             (gtx_clk_bufg),
      .aresetn         (s_axi_resetn),
      .mmcm_locked_i   (mmcm_locked),
      .idelay_rdy_i    (idelay_rdy),
      .m_axi_awaddr    (init_awaddr),
      .m_axi_awvalid   (s_axi_awvalid),
      .m_axi_awready   (s_axi_awready),
      .m_axi_wdata     (s_axi_wdata),
      .m_axi_wstrb     (),
      .m_axi_wvalid    (s_axi_wvalid),
      .m_axi_wready    (s_axi_wready),
      .m_axi_bresp     (s_axi_bresp),
      .m_axi_bvalid    (s_axi_bvalid),
      .m_axi_bready    (s_axi_bready),
      .m_axi_araddr    (init_araddr),
      .m_axi_arvalid   (s_axi_arvalid),
      .m_axi_arready   (s_axi_arready),
      .m_axi_rdata     (s_axi_rdata),
      .m_axi_rresp     (s_axi_rresp),
      .m_axi_rvalid    (s_axi_rvalid),
      .m_axi_rready    (s_axi_rready),
      .done_o          ()
   );

   //---------------------------------------------------------------------------
   // TEMAC + user-side AXI-S FIFOs (the "fifo block", as in the upstream example design)
   //---------------------------------------------------------------------------
   wire         rx_mac_aclk;
   wire         tx_mac_aclk;
   wire         rx_mac_reset;
   wire         tx_mac_reset;
   wire         rx_mac_resetn;
   wire         tx_mac_resetn;
   wire [7:0]   rx_axis_mac_tdata;
   wire         rx_axis_mac_tvalid;
   wire         rx_axis_mac_tlast;
   wire         rx_axis_mac_tuser;
   wire [7:0]   tx_axis_mac_tdata;
   wire         tx_axis_mac_tvalid;
   wire         tx_axis_mac_tready;
   wire         tx_axis_mac_tlast;
   wire         tx_axis_mac_tuser;
   wire [27:0]  rx_statistics_vector;
   wire         rx_statistics_valid;
   wire [31:0]  tx_statistics_vector;
   wire         tx_statistics_valid;

   tri_mode_ethernet_mac_0 tri_mode_ethernet_mac_i (
      .gtx_clk              (gtx_clk_bufg),
      .glbl_rstn            (glbl_rst_intn),
      .rx_axi_rstn          (1'b1),
      .tx_axi_rstn          (1'b1),
      .rx_statistics_vector (rx_statistics_vector),
      .rx_statistics_valid  (rx_statistics_valid),
      .rx_mac_aclk          (rx_mac_aclk),
      .rx_reset             (rx_reset),
      .rx_axis_mac_tdata    (rx_axis_mac_tdata),
      .rx_axis_mac_tvalid   (rx_axis_mac_tvalid),
      .rx_axis_mac_tlast    (rx_axis_mac_tlast),
      .rx_axis_mac_tuser    (rx_axis_mac_tuser),
      .tx_ifg_delay         (8'd0),
      .tx_statistics_vector (tx_statistics_vector),
      .tx_statistics_valid  (tx_statistics_valid),
      .tx_mac_aclk          (tx_mac_aclk),
      .tx_reset             (tx_reset),
      .tx_axis_mac_tdata    (tx_axis_mac_tdata),
      .tx_axis_mac_tvalid   (tx_axis_mac_tvalid),
      .tx_axis_mac_tlast    (tx_axis_mac_tlast),
      .tx_axis_mac_tuser    (tx_axis_mac_tuser),
      .tx_axis_mac_tready   (tx_axis_mac_tready),
      .pause_req            (1'b0),
      .pause_val            (16'd0),
      .clk_enable           (sgmii_clk_en),
      .speedis100           (speed_is_100),
      .speedis10100         (speed_is_10_100),
      .gmii_txd             (gmii_txd),
      .gmii_tx_en           (gmii_tx_en),
      .gmii_tx_er           (gmii_tx_er),
      .gmii_rxd             (gmii_rxd),
      .gmii_rx_dv           (gmii_rx_dv),
      .gmii_rx_er           (gmii_rx_er),
      .mdio_i               (pcs_mdio_o),
      .mdio_t               (mac_mdio_t),
      .mdio_o               (mac_mdio_o),
      .mdc                  (mac_mdc),
      .s_axi_aclk           (gtx_clk_bufg),
      .s_axi_resetn         (s_axi_resetn),
      .s_axi_awaddr         (s_axi_awaddr),
      .s_axi_awvalid        (s_axi_awvalid),
      .s_axi_awready        (s_axi_awready),
      .s_axi_wdata          (s_axi_wdata),
      .s_axi_wvalid         (s_axi_wvalid),
      .s_axi_wready         (s_axi_wready),
      .s_axi_bresp          (s_axi_bresp),
      .s_axi_bvalid         (s_axi_bvalid),
      .s_axi_bready         (s_axi_bready),
      .s_axi_araddr         (s_axi_araddr),
      .s_axi_arvalid        (s_axi_arvalid),
      .s_axi_arready        (s_axi_arready),
      .s_axi_rdata          (s_axi_rdata),
      .s_axi_rresp          (s_axi_rresp),
      .s_axi_rvalid         (s_axi_rvalid),
      .s_axi_rready         (s_axi_rready),
      .mac_irq              ()
   );

   tri_mode_ethernet_mac_0_reset_sync rx_mac_reset_gen (
      .clk                  (rx_mac_aclk),
      .enable               (1'b1),
      .reset_in             (rx_reset),
      .reset_out            (rx_mac_reset)
   );

   tri_mode_ethernet_mac_0_reset_sync tx_mac_reset_gen (
      .clk                  (tx_mac_aclk),
      .enable               (1'b1),
      .reset_in             (tx_reset),
      .reset_out            (tx_mac_reset)
   );

   assign tx_mac_resetn = !tx_mac_reset;
   assign rx_mac_resetn = !rx_mac_reset;

   tri_mode_ethernet_mac_0_ten_100_1g_eth_fifo #
   (
      .FULL_DUPLEX_ONLY     (1)
   )
   user_side_FIFO
   (
      // TX clock domain
      .tx_fifo_aclk           (tx_fifo_clock),
      .tx_fifo_resetn         (tx_fifo_resetn),
      .tx_axis_fifo_tdata     (tx_axis_fifo_tdata),
      .tx_axis_fifo_tvalid    (tx_axis_fifo_tvalid),
      .tx_axis_fifo_tlast     (tx_axis_fifo_tlast),
      .tx_axis_fifo_tready    (tx_axis_fifo_tready),

      .tx_mac_aclk            (tx_mac_aclk),
      .tx_mac_resetn          (tx_mac_resetn),
      .tx_axis_mac_tdata      (tx_axis_mac_tdata),
      .tx_axis_mac_tvalid     (tx_axis_mac_tvalid),
      .tx_axis_mac_tlast      (tx_axis_mac_tlast),
      .tx_axis_mac_tready     (tx_axis_mac_tready),
      .tx_axis_mac_tuser      (tx_axis_mac_tuser),

      .tx_fifo_overflow       (),
      .tx_fifo_status         (),
      .tx_collision           (1'b0),
      .tx_retransmit          (1'b0),

      // RX clock domain
      .rx_fifo_aclk           (rx_axis_fifo_aclk),
      .rx_fifo_resetn         (rx_axis_fifo_aresetn),
      .rx_axis_fifo_tdata     (rx_axis_fifo_tdata),
      .rx_axis_fifo_tvalid    (rx_axis_fifo_tvalid),
      .rx_axis_fifo_tlast     (rx_axis_fifo_tlast),
      .rx_axis_fifo_tready    (rx_axis_fifo_tready),

      .rx_mac_aclk            (rx_mac_aclk),
      .rx_mac_resetn          (rx_mac_resetn),
      .rx_axis_mac_tdata      (rx_axis_mac_tdata),
      .rx_axis_mac_tvalid     (rx_axis_mac_tvalid),
      .rx_axis_mac_tlast      (rx_axis_mac_tlast),
      .rx_axis_mac_tuser      (rx_axis_mac_tuser),

      .rx_fifo_status         (),
      .rx_fifo_overflow       (rx_axis_fifo_overflow)
   );

endmodule
