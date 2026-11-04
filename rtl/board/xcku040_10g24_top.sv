/* 
       _________   ________     ________       
      / U OF M  \ | LSA    \   / Physics\
      \__ATLAS__/ |   ___   | |   ______/
         |   |    |  |   \  | |  |
         |   |    |  |___/  | |  \______     
         |   |    |         | |         \
         \___/    |________/   \________/
*/  

// Author : Yuxiang Guo  gyuxiang@umich.edu
// File   : xcku035_10g24_top.sv  (upstream, gitlab.cern.ch/yuxiangg/phase2_MiniDAQ @ 124dc6d)
// Create : 2023-10-12 23:04:23
// Revise : 2025-10-10 12:21:28
// Editor : sublime text4, tab size (3)
// Description:
//
// -----------------------------------------------------------------------------
// KCU105 PORT of the MiniDAQ top level (xcku040-ffva1156-2-e), with UPLINKCOUNT = 2 and
// DOWNLINKCOUNT = 1.  Pristine upstream copy: ref_upstream/lpgbt-fpga-xcku035/hdl/.
// Everything below is the upstream design unchanged EXCEPT the board layer, marked "KCU105:":
//   - module renamed xcku040_10g24_top; defaults 2 uplinks / 1 downlink
//   - USER_CLOCK is the board's 125 MHz (not 200 MHz) -- sys_clk still makes the 100 MHz
//     mgt_freedrpclk, so all free-running-clock timing is identical to the upstream design
//   - the 2 uplink/1 downlink MGT lanes are the KCU105's two SFP+ cages: channel 0 = master lpGBT
//     (uplink 0 + the downlink) on SFP0 = GTH X0Y10, channel 1 = slave lpGBT (uplink 1) on SFP1 =
//     GTH X0Y9 (site swap in constr/kcu105_gth_sites.xdc); SFP_TX_DISABLE / SFP_RX_LOS are 2 bits
//     wide, index = GT wizard channel = logical uplink
//   - Ethernet is SGMII (onboard Marvell 88E1111, 625 MHz PHY clock) instead of RGMII; the
//     user-side AXI-S interface of ethernet_mac and everything behind it is unchanged
//   - TRIGGER1_P/N removed: upstream only feeds it to an IBUFDS whose output (trigger_out) has no
//     load anywhere in the design; the KCU105 has no spare differential input for it
//   - mezz_TRST drives a user LED (there is no mezzanine on the KCU105)
//   - SFP_TX_DISABLE is driven high: the KCU105 inverts it through a MOSFET (high = laser on)
// -----------------------------------------------------------------------------


module xcku040_10g24_top #(
    parameter UPLINKCOUNT = 2,
    parameter DOWNLINKCOUNT = 1)
    (
    // --===============--
    //   -- Clocks scheme --
    //   --===============--       
    //   -- MGT(GTX) reference clock:
    //   ----------------------------
      
    //   -- Comment: * The MGT reference clock MUST be provided by an external clock generator.
    //   --
    //   --          * The MGT reference clock frequency must be 320MHz.
    input           SMA_MGT_REFCLK_P,
    input           SMA_MGT_REFCLK_N,
        
      // -- Fabric clock: 125MHz on the KCU105 (200MHz on the MiniDAQ board)
    input           USER_CLOCK_P,
    input           USER_CLOCK_N,

    // KCU105: USER_SMA_CLOCK_P/N (differential SMA input)
    input           TRIGGER0_P,
    input           TRIGGER0_N,

    // KCU105: TRIGGER1_P/N removed (unused in the upstream design, see header)

    // --hit to mezz
    // output  [23:0]  hit,
    output          mezz_TRST,

    // -- MGT(GTX) --  index = GT wizard channel (ascending site) = logical uplink
    output  [UPLINKCOUNT-1:0]   SFP_TX_P,
    output  [UPLINKCOUNT-1:0]   SFP_TX_N,
    input   [UPLINKCOUNT-1:0]   SFP_RX_P,
    input   [UPLINKCOUNT-1:0]   SFP_RX_N,

    // -- SFP control (KCU105: 2 cages)
    output  [UPLINKCOUNT-1:0]   SFP_TX_DISABLE,
    input   [UPLINKCOUNT-1:0]   SFP_RX_LOS,

    // --====================--
    // -- Signals forwarding --
    // --====================--

    // -- SMA output:
    // --------------
    output          USER_SMA_GPIO_P,
    output          USER_SMA_GPIO_N,


    // -- SGMII Interface to the onboard Marvell 88E1111 PHY (KCU105)
    // ---------------------------------------------------------------
    input           SGMIICLK_P,      // 625 MHz reference clock supplied by the PHY
    input           SGMIICLK_N,
    output          SGMII_TX_P,
    output          SGMII_TX_N,
    input           SGMII_RX_P,
    input           SGMII_RX_N,
    output          phy_resetn,

    // -- MDIO Interface
    //     -----------------
    inout           mdio,
    output          mdc

    // All runtime configuration, readback, lpGBT IC and SCA traffic uses the
    // Ethernet interface above; no secondary control transport is used.
);


localparam SCA_PER_DOWNLINK = 4;
// The CERN SCA TX core always serializes all four command-data bytes.
localparam [7:0] SCA_COMMAND_DATA_BYTES = 8'd4;

localparam FEC5           =1;
localparam FEC12          =2;
localparam DATARATE_5G12  =1;
localparam DATARATE_10G24 =2;
localparam PCS            =0;
localparam PMA            =1;

//unused pins
// assign USER_SMA_GPIO_P =1'b0;
// assign USER_SMA_GPIO_N =1'b0;
// KCU105 SFP+ transmit control: the FPGA pins SFP0/1_TX_DISABLE (AL8 / D28) drive the gate of an
// NDS331N N-MOSFET (Q12 / Q13, schematic 0381556 rev 02, sheets 27/28) that pulls the module's
// TX_DISABLE input (4.7k pull-up to 3.3 V) low.  The polarity is therefore INVERTED w.r.t. the
// module pin: FPGA output 1 = transmitter ON, 0 = transmitter OFF.  Upstream (MiniDAQ board, direct
// connection) drives 0 = enabled; keeping that value here leaves both lasers off and the lpGBT
// never sees a downlink.  So the port keeps its upstream name but is driven high.
assign SFP_TX_DISABLE = {UPLINKCOUNT{1'b1}};


// -- Clocks:
wire mgtRefClk_from_smaMgtRefClkbuf;   //external 320MHz reference clock for MGT

wire mgt_freedrpclk;   //async clock for MGT reset and all vios

wire [DOWNLINKCOUNT-1:0] lpgbtfpga_mgttxclk;   // 320MHz clocks recovered from MGT tx
wire [UPLINKCOUNT-1:0] lpgbtfpga_mgtrxclk;   // 320MHz clocks recovered from MGT rx

// FPGA configuration initializes this shift register to all ones.  Once the
// TX-derived 40 MHz user clock starts, zeros shift through it and release the
// MiniDAQ register bank synchronously after four clock cycles.
(* SHREG_EXTRACT = "NO" *)
reg [3:0] power_on_reset_shift = 4'hF;
wire power_on_reset_40 = power_on_reset_shift[3];


// -- User CDC for lpGBT-FPGA      
wire lpgbtfpga_clk40;      //40MHz divided from 320MHz clock recovered from MGT tx

wire acquisition_mode;
wire run_enable;
wire stream_hits_only;
wire noise_counter_stream;
wire noise_counter_clear;
wire [39:0] tdc_enable_mask;
wire [39:0] tdc_chamber1_mask;

wire [2:0] uplinkPhase[UPLINKCOUNT-1:0];
wire [2:0] uplinkPhase_sync40[UPLINKCOUNT-1:0];
wire [2:0] uplinkPhaseCalib[UPLINKCOUNT-1:0];
wire [2:0] uplinkPhaseCalib_rxclk[UPLINKCOUNT-1:0];
wire [UPLINKCOUNT-1:0] uplinkPhaseForce;
wire [UPLINKCOUNT-1:0] uplinkPhaseForce_rxclk;
               
                                                                 
wire [9:0] downlinkPhase[DOWNLINKCOUNT-1:0];
wire [9:0] downlinkPhase_sync40[DOWNLINKCOUNT-1:0];
wire [9:0] downlinkPhaseCalib[DOWNLINKCOUNT-1:0];
wire [9:0] downlinkPhaseCalib_freedrp[DOWNLINKCOUNT-1:0];

wire [DOWNLINKCOUNT-1:0] downlinkPhaseForce;
wire [DOWNLINKCOUNT-1:0] downlinkPhaseForce_freedrp;

// -- LpGBT-FPGA
wire [DOWNLINKCOUNT-1:0] lpgbtfpga_downlinkrdy;
wire [DOWNLINKCOUNT-1:0] lpgbtfpga_downlinkrdy_raw;
                             

wire [UPLINKCOUNT-1:0] lpgbtfpga_uplinkrdy;
wire [UPLINKCOUNT-1:0] lpgbtfpga_uplinkrdy_raw;
wire [UPLINKCOUNT-1:0] active_sfp_rx_los;

// The GT Wizard channels are ordered from the lowest site upward.  On the MiniDAQ PCB, logical
// uplinks 0..3 use physical SFP cages 7, 5, 3 and 1 (its 8-bit LOS bus).  KCU105: the LOS/TX_DISABLE
// ports are already indexed by GT channel -- constr/kcu105_physical.xdc ties bit i to the cage whose
// GTH site is channel i -- so no remapping is needed here.
genvar los_i;
for (los_i = 0; los_i < UPLINKCOUNT; los_i = los_i + 1) begin : sfp_los_map
    assign active_sfp_rx_los[los_i] = SFP_RX_LOS[los_i];
end

// SFP RX_LOS is asynchronous and active high.  The module pulls this signal
// high when light is lost; the board pull-up also makes it high when no SFP is
// installed.  Synchronize both sides of the ready qualification into the 40
// MHz user domain so downstream logic never sees an unqualified frame lock.
(* ASYNC_REG = "TRUE", SHREG_EXTRACT = "NO" *)
reg [UPLINKCOUNT-1:0] sfp_rx_los_meta = {UPLINKCOUNT{1'b1}};
(* ASYNC_REG = "TRUE", SHREG_EXTRACT = "NO" *)
reg [UPLINKCOUNT-1:0] sfp_rx_los_sync = {UPLINKCOUNT{1'b1}};
(* ASYNC_REG = "TRUE", SHREG_EXTRACT = "NO" *)
reg [UPLINKCOUNT-1:0] lpgbtfpga_uplinkrdy_meta = {UPLINKCOUNT{1'b0}};
(* ASYNC_REG = "TRUE", SHREG_EXTRACT = "NO" *)
reg [UPLINKCOUNT-1:0] lpgbtfpga_uplinkrdy_sync = {UPLINKCOUNT{1'b0}};

always @(posedge lpgbtfpga_clk40) begin
    sfp_rx_los_meta          <= active_sfp_rx_los;
    sfp_rx_los_sync          <= sfp_rx_los_meta;
    lpgbtfpga_uplinkrdy_meta <= lpgbtfpga_uplinkrdy_raw;
    lpgbtfpga_uplinkrdy_sync <= lpgbtfpga_uplinkrdy_meta;
end

assign lpgbtfpga_uplinkrdy = lpgbtfpga_uplinkrdy_sync & ~sfp_rx_los_sync;

wire [31:0] lpgbtfpga_downlinkUserData[DOWNLINKCOUNT-1:0];


wire [1:0] lpgbtfpga_downlinkIcData[DOWNLINKCOUNT-1:0];

wire [229:0] lpgbtfpga_uplinkUserData[UPLINKCOUNT-1:0];
wire [1:0] lpgbtfpga_uplinkIcData[UPLINKCOUNT-1:0];


wire [DOWNLINKCOUNT-1:0] lpgbtfpga_mgt_txpolarity;
wire [DOWNLINKCOUNT-1:0] lpgbtfpga_mgt_txpolarity_freedrp;

wire [UPLINKCOUNT-1:0] lpgbtfpga_mgt_rxpolarity;
wire [UPLINKCOUNT-1:0] lpgbtfpga_mgt_rxpolarity_rxclk;


wire [DOWNLINKCOUNT-1:0] lpgbtfpga_mgt_txaligned;
wire [DOWNLINKCOUNT-1:0] lpgbtfpga_mgt_txaligned_sync40;
wire [6:0]lpgbtfpga_mgt_txpiphase[DOWNLINKCOUNT-1:0];
wire [6:0]lpgbtfpga_mgt_txpiphase_sync40[DOWNLINKCOUNT-1:0];
wire [6:0]lpgbtfpga_mgt_txpicalib[DOWNLINKCOUNT-1:0];
wire [6:0]lpgbtfpga_mgt_txpicalib_freedrp[DOWNLINKCOUNT-1:0];
wire [DOWNLINKCOUNT-1:0] lpgbtfpga_mgt_txcaliben;
wire [DOWNLINKCOUNT-1:0] lpgbtfpga_mgt_txcaliben_freedrp;
                
wire [DOWNLINKCOUNT-1:0] downLinkBypassInterleaver;
wire [DOWNLINKCOUNT-1:0] downLinkBypassFECEncoder;
wire [DOWNLINKCOUNT-1:0] downLinkBypassScrambler;
wire [DOWNLINKCOUNT-1:0] downLinkBypassInterleaver_txclk;
wire [DOWNLINKCOUNT-1:0] downLinkBypassFECEncoder_txclk;
wire [DOWNLINKCOUNT-1:0] downLinkBypassScrambler_txclk;

wire [UPLINKCOUNT-1:0] upLinkScramblerBypass;
wire [UPLINKCOUNT-1:0] upLinkFecBypass;
wire [UPLINKCOUNT-1:0] upLinkInterleaverBypass;
wire [UPLINKCOUNT-1:0] upLinkScramblerBypass_rxclk;
wire [UPLINKCOUNT-1:0] upLinkFecBypass_rxclk;
wire [UPLINKCOUNT-1:0] upLinkInterleaverBypass_rxclk;

wire [UPLINKCOUNT-1:0] upLinkFECCorrectedClear;
wire [UPLINKCOUNT-1:0] upLinkFECCorrectedLatched;
wire [UPLINKCOUNT-1:0] upLinkFECCorrectedClear_rxclk;
wire [UPLINKCOUNT-1:0] upLinkFECCorrectedLatched_sync40;

wire system_reset_pulse;
// ------------------------------------------------------------------------------------------------
// ------------------------------------------------------------------------------------------------

// --SCA control.  The programming engine has priority over generic Ethernet
// SCA transactions only for its selected downlink.
wire    sc_reset_control;
wire    [SCA_PER_DOWNLINK-1:0]  sca_enable_array_mux[DOWNLINKCOUNT-1:0];
wire    [DOWNLINKCOUNT-1:0]     sca_start_reset_mux;
wire    [DOWNLINKCOUNT-1:0]     sca_start_connect_mux;
wire    [DOWNLINKCOUNT-1:0]     sca_start_command_mux;
wire    [7:0]                   sca_tx_address_mux[DOWNLINKCOUNT-1:0];
wire    [7:0]                   sca_tx_transID_mux[DOWNLINKCOUNT-1:0];
wire    [7:0]                   sca_tx_channel_mux[DOWNLINKCOUNT-1:0];
wire    [7:0]                   sca_tx_command_mux[DOWNLINKCOUNT-1:0];
wire    [31:0]                  sca_tx_data_mux[DOWNLINKCOUNT-1:0];

//SCA rx
wire    [SCA_PER_DOWNLINK-1:0]  sca_rx_done[DOWNLINKCOUNT-1:0];  //  Reply received flag (pulse)
wire    [7:0]                   sca_rx_addr[DOWNLINKCOUNT-1:0][SCA_PER_DOWNLINK-1:0];  //  --! Reply: address field (According to the SCA manual)
wire    [7:0]                   sca_rx_trid[DOWNLINKCOUNT-1:0][SCA_PER_DOWNLINK-1:0];  //  --! Reply: transaction ID field (According to the SCA manual)
wire    [7:0]                   sca_rx_ch[DOWNLINKCOUNT-1:0][SCA_PER_DOWNLINK-1:0];  //    --! Reply: channel field (According to the SCA manual)
wire    [7:0]                   sca_rx_len[DOWNLINKCOUNT-1:0][SCA_PER_DOWNLINK-1:0];  //   --! Reply: len field (According to the SCA manual)
wire    [7:0]                   sca_rx_err[DOWNLINKCOUNT-1:0][SCA_PER_DOWNLINK-1:0];  //   --! Reply: error field (According to the SCA manual)
wire    [31:0]                  sca_rx_data[DOWNLINKCOUNT-1:0][SCA_PER_DOWNLINK-1:0];  // --!Reply: data field (According to the SCA manual)

// -- EC line
wire [1:0]sca_line_tx[DOWNLINKCOUNT-1:0][SCA_PER_DOWNLINK-1:0];       // --! (TX) Array of bits to be mapped to the TX GBT-Frame
wire [1:0]sca_line_rx[DOWNLINKCOUNT-1:0][SCA_PER_DOWNLINK-1:0];       // --! (RX) Array of bits to be mapped to the RX GBT-Frame



// -- IC
wire [UPLINKCOUNT-1:0] ic_rx_fifo_empty;
wire [7:0] data_from_gbtic[UPLINKCOUNT-1:0];

// -- Trigger
wire [1:0] ttc_ctrl;
wire trigger_SMA;

wire    [7:0]                   ic_GBTx_address_control[DOWNLINKCOUNT-1:0];
wire    [15:0]                  ic_Register_addr_control[DOWNLINKCOUNT-1:0];
wire    [7:0]                   ic_nb_to_be_read_control[DOWNLINKCOUNT-1:0];
wire    [DOWNLINKCOUNT-1:0]     ic_wr_start_control;
wire    [DOWNLINKCOUNT-1:0]     ic_rd_start_control;
wire    [7:0]                   ic_wfifo_data_control[DOWNLINKCOUNT-1:0];
wire    [DOWNLINKCOUNT-1:0]     ic_fifo_wr_control;
wire    [DOWNLINKCOUNT-1:0]     ic_rx_reset_control;
wire    [UPLINKCOUNT-1:0]       ic_rx_fifo_read_control;



wire  [UPLINKCOUNT-1:0] uplink_reset_control;
wire           downlink_reset_control;
wire           downlink_reset_freedrp;
wire  [UPLINKCOUNT-1:0] uplink_reset_freedrp;

wire           global_rst_control;
wire           bc_rst_control;
wire           event_rst_control;
wire           master_rst_control;

wire           en_int_trigger;
wire           enable_hit;
wire           hit_inv;
wire           hit_single;
wire  [11:0]   hit_width;
wire  [23:0]   hit_interval;

wire  [19:0]   correct_counter_th;
wire           enable_K28_1;
wire           enable_320M;
wire  [15:0]    trigger_deadtime;
wire  [11:0]   match_window;
wire  [11:0]   search_margin;
wire  [11:0]   bc_offset;
wire  [11:0]   reject_offset;
wire  [11:0]   rollover;
wire  [11:0]   coarse_count_offset;
wire           en_relative_trig_data;
wire           enable_matching;
wire           trigger_redge;
wire  [7:0]    trigger_latency;

wire [43:0] total_received_40bit_dline1[UPLINKCOUNT-1:0][9:0];
wire [43:0] total_received_40bit_dline0[UPLINKCOUNT-1:0][9:0];
wire [35:0] total_error_bit_dline1[UPLINKCOUNT-1:0][9:0];
wire [35:0] total_error_bit_dline0[UPLINKCOUNT-1:0][9:0];
wire [19:0] phase_sel_160M_20b[UPLINKCOUNT-1:0];
wire  [15:0]  window_cycles;
wire  [9:0]   hit_threshold;
wire  [9:0]   hit_upper_threshold;
wire  [20:0]  fsm_watchdog_cycles;
wire [21:0] geometry_lookup_address;
wire [95:0] geometry_lookup_data;
wire geometry_ready;
wire [85:0] tube_filter_settings;
wire [31:0] geometry_mls;
wire [511:0] geometry_layers;
wire [27:0] diagnostic_pulses;
wire [11:0] diagnostic_fifo_lost_words;




//Ethernet
wire tx_axis_clk;
wire [7:0] hit_tx_axis_tdata;
wire hit_tx_axis_tvalid;
wire hit_tx_axis_tready;
wire hit_tx_axis_tlast;
wire [7:0] tx_axis_fifo_tdata;
wire tx_axis_fifo_tvalid;
wire tx_axis_fifo_tready;
wire tx_axis_fifo_tlast;
wire ethernet_rx_axis_clk;
wire ethernet_rx_axis_resetn;
wire [7:0] ethernet_rx_axis_tdata;
wire ethernet_rx_axis_tvalid;
wire ethernet_rx_axis_tready;
wire ethernet_rx_axis_tlast;
(* mark_debug = "true" *) wire ethernet_rx_mac_fifo_overflow;

wire ethernet_program_session_active_125;
wire ethernet_program_data_fifo_full;
wire ethernet_program_data_fifo_overflow;
wire ethernet_program_descriptor_fifo_full;
wire ethernet_program_result_fifo_full;
wire [15:0] hit_fifo_occupancy;

wire fpga_readback_valid;
wire [159:0] fpga_readback_data;
wire [UPLINKCOUNT*10-1:0] locked_dline1;
wire [UPLINKCOUNT*10-1:0] locked_dline0;


//drp interface
wire  [UPLINKCOUNT-1:0]    drpen_control;
wire  [UPLINKCOUNT-1:0]    drpwe_control;
wire  [UPLINKCOUNT*9-1:0]  drpaddr_control;
wire  [UPLINKCOUNT*16-1:0] drpdi_control;
wire  [UPLINKCOUNT-1:0]    rxprbscntreset_control;
wire  [UPLINKCOUNT*4-1:0]  rxprbssel_control;

wire  [UPLINKCOUNT*16-1:0] drpdo_ip;
wire  [UPLINKCOUNT-1:0]    rxprbserr_ip;
wire  [UPLINKCOUNT-1:0]    rxprbslocked_ip;




// -- Clocks



sys_clk sys_clk_inst
(
    // Clock out ports
    .mgt_freedrpclk (mgt_freedrpclk),     // free running clock required by GTX drp

    // Status and control signals
    .locked         (),       // output locked
    // Clock in ports
    .clk_in1_p      (USER_CLOCK_P),    // input clk_in1_p
    .clk_in1_n      (USER_CLOCK_N)    // input clk_in1_n
);


    
// -- MGT(GTX) reference clock:
// ----------------------------   
// -- Comment: * The MGT reference clock MUST be provided by an external clock generator.
// --          * The MGT reference clock frequency must be 320MHz for the latency-optimized GBT Bank. 

// IBUFDS_GTE3: Gigabit Transceiver Buffer
//              UltraScale
IBUFDS_GTE3 #(
   .REFCLK_EN_TX_PATH(1'b0),   // Refer to Transceiver User Guide.
   .REFCLK_HROW_CK_SEL(2'b00), // Refer to Transceiver User Guide.
   .REFCLK_ICNTL_RX(2'b00)     // Refer to Transceiver User Guide.
)
smaMgtRefClkIbufdsGtxe2 (
   .O(mgtRefClk_from_smaMgtRefClkbuf),         // 1-bit output: Refer to Transceiver User Guide.
   .ODIV2(), // 1-bit output: Refer to Transceiver User Guide.
   .CEB(1'b0),     // 1-bit input: Refer to Transceiver User Guide.
   .I(SMA_MGT_REFCLK_P),         // 1-bit input: Refer to Transceiver User Guide.
   .IB(SMA_MGT_REFCLK_N)        // 1-bit input: Refer to Transceiver User Guide.
);


            
  // -- In this example design, the 40MHz clock used for the user logic is derived from a division of the Tx user clock of the MGT
  // -- It should be noted, that in realistic cases, this clock typically comes from an external PLL (sync. to the MGT Tx reference clock)
  
BUFGCE_DIV #(
   .BUFGCE_DIVIDE(8),              // 1-8
   // Programmable Inversion Attributes: Specifies built-in programmable inversion on specific pins
   .IS_CE_INVERTED(1'b0),          // Optional inversion for CE
   .IS_CLR_INVERTED(1'b0),         // Optional inversion for CLR
   .IS_I_INVERTED(1'b0),           // Optional inversion for I
   .SIM_DEVICE("ULTRASCALE"))  // ULTRASCALE, ULTRASCALE_PLUS
BUFGCE_DIV_inst (
   .O(lpgbtfpga_clk40),     // 1-bit output: Buffer
   .CE(1'b1),   // 1-bit input: Buffer enable
   .CLR(1'b0), // 1-bit input: Asynchronous clear
   .I(lpgbtfpga_mgttxclk[0])      // 1-bit input: Buffer 320M clk_mgtRxClk_o
);

always @(posedge lpgbtfpga_clk40) begin
    power_on_reset_shift <= {power_on_reset_shift[2:0], 1'b0};
end


OBUFDS #(
   .IOSTANDARD("DEFAULT"), // Specify the output I/O standard
   .SLEW("SLOW")           // Specify the output slew rate
) OBUFDS_inst (
   .O(USER_SMA_GPIO_P),     // Diff_p output (connect directly to top-level port)
   .OB(USER_SMA_GPIO_N),   // Diff_n output (connect directly to top-level port)
   .I(lpgbtfpga_clk40)      // Buffer input
);

IBUFDS
IBUFDS_inst (
   .O(trigger_SMA),   // 1-bit output: Buffer output
   .I(TRIGGER0_P),   // 1-bit input: Diff_p buffer input (connect directly to top-level port)
   .IB(TRIGGER0_N)  // 1-bit input: Diff_n buffer input (connect directly to top-level port)
);

// KCU105: upstream's IBUFDS_trigger_out (TRIGGER1_P/N -> trigger_out) removed; trigger_out had
// no load anywhere in the design.

// OBUF #(
//    .DRIVE(12),   // Specify the output drive strength
//    .IOSTANDARD("LVCMOS18"), // Specify the output I/O standard
//    .SLEW("FAST") // Specify the output slew rate
// ) OBUF_inst (
//    .O(USER_SMA_GPIO_P),     // Buffer output (connect directly to top-level port)
//    .I(trigger_out)      // Buffer input
// );


genvar j;
for (j = 0; j < UPLINKCOUNT; j++) begin : uplink
    

    ic_rx #(
        .g_FIFO_DEPTH(453)
        )
    ic_rx_inst(
        .rx_clk_i   (lpgbtfpga_clk40),
        .rx_clk_en  (1'b1),
        .reset_i    (sc_reset_control|ic_rx_reset_control[j/2]),
        .rx_empty_o (ic_rx_fifo_empty[j]),         //--! Rx FIFO is empty (no reply from ic)
        .rd_clk_i   (lpgbtfpga_clk40),
        .rd_i       (ic_rx_fifo_read_control[j]), // Ethernet engine read
        .data_o     (data_from_gbtic[j]),  //     --! Data from the FIFO
        .rx_data_i  (lpgbtfpga_uplinkIcData[j])     //            --! (RX) Array of bits to be mapped to the RX GBT-Frame (bits 83/84)
    );

    // Ethernet registers are written in the 40 MHz domain. Synchronize static
    // uplink controls before they enter the corresponding recovered RX clock.
    xpm_cdc_array_single #(
        .DEST_SYNC_FF   (2),
        .INIT_SYNC_FF   (0),
        .SIM_ASSERT_CHK (1),
        .SRC_INPUT_REG  (1),
        .WIDTH          (9)
    ) uplink_control_sync (
        .src_clk  (lpgbtfpga_clk40),
        .src_in   ({uplinkPhaseForce[j],
                    uplinkPhaseCalib[j],
                    upLinkFECCorrectedClear[j],
                    lpgbtfpga_mgt_rxpolarity[j],
                    upLinkScramblerBypass[j],
                    upLinkFecBypass[j],
                    upLinkInterleaverBypass[j]}),
        .dest_clk (lpgbtfpga_mgtrxclk[j]),
        .dest_out ({uplinkPhaseForce_rxclk[j],
                    uplinkPhaseCalib_rxclk[j],
                    upLinkFECCorrectedClear_rxclk[j],
                    lpgbtfpga_mgt_rxpolarity_rxclk[j],
                    upLinkScramblerBypass_rxclk[j],
                    upLinkFecBypass_rxclk[j],
                    upLinkInterleaverBypass_rxclk[j]})
    );

    // Synchronize the two status fields formerly monitored by the VIO into the
    // Ethernet/readback clock domain.
    xpm_cdc_array_single #(
        .DEST_SYNC_FF   (2),
        .INIT_SYNC_FF   (0),
        .SIM_ASSERT_CHK (1),
        .SRC_INPUT_REG  (0),
        .WIDTH          (4)
    ) uplink_status_sync (
        .src_clk  (lpgbtfpga_mgtrxclk[j]),
        .src_in   ({uplinkPhase[j], upLinkFECCorrectedLatched[j]}),
        .dest_clk (lpgbtfpga_clk40),
        .dest_out ({uplinkPhase_sync40[j], upLinkFECCorrectedLatched_sync40[j]})
    );
end

genvar i;
for (i = 0; i < DOWNLINKCOUNT; i++) begin : downlink

    sca_mapping #(
        .SCA_PER_DOWNLINK(SCA_PER_DOWNLINK)
    ) inst_sca_mapping (
        .sca_line_tx      (sca_line_tx[i]),
        .ttc_ctrl         (ttc_ctrl),
        .uplinkUserData   (lpgbtfpga_uplinkUserData[2*i]),
        .sca_line_rx      (sca_line_rx[i]),
        .downlinkUserData (lpgbtfpga_downlinkUserData[i])
    );

    // The three encoder controls are consumed in this downlink's TX clock
    // domain.
    xpm_cdc_array_single #(
        .DEST_SYNC_FF   (2),
        .INIT_SYNC_FF   (0),
        .SIM_ASSERT_CHK (1),
        .SRC_INPUT_REG  (1),
        .WIDTH          (3)
    ) downlink_datapath_control_sync (
        .src_clk  (lpgbtfpga_clk40),
        .src_in   ({downLinkBypassScrambler[i],
                    downLinkBypassFECEncoder[i],
                    downLinkBypassInterleaver[i]}),
        .dest_clk (lpgbtfpga_mgttxclk[i]),
        .dest_out ({downLinkBypassScrambler_txclk[i],
                    downLinkBypassFECEncoder_txclk[i],
                    downLinkBypassInterleaver_txclk[i]})
    );

    // Fixed-phase CDC and MGT alignment controls are consumed in the
    // free-running DRP clock domain.
    xpm_cdc_array_single #(
        .DEST_SYNC_FF   (2),
        .INIT_SYNC_FF   (0),
        .SIM_ASSERT_CHK (1),
        .SRC_INPUT_REG  (1),
        .WIDTH          (20)
    ) downlink_freedrp_control_sync (
        .src_clk  (lpgbtfpga_clk40),
        .src_in   ({downlinkPhaseForce[i],
                    downlinkPhaseCalib[i],
                    lpgbtfpga_mgt_txpolarity[i],
                    lpgbtfpga_mgt_txcaliben[i],
                    lpgbtfpga_mgt_txpicalib[i]}),
        .dest_clk (mgt_freedrpclk),
        .dest_out ({downlinkPhaseForce_freedrp[i],
                    downlinkPhaseCalib_freedrp[i],
                    lpgbtfpga_mgt_txpolarity_freedrp[i],
                    lpgbtfpga_mgt_txcaliben_freedrp[i],
                    lpgbtfpga_mgt_txpicalib_freedrp[i]})
    );

    // Return the status formerly monitored by the VIO to the Ethernet/readback
    // clock domain.
    xpm_cdc_array_single #(
        .DEST_SYNC_FF   (2),
        .INIT_SYNC_FF   (0),
        .SIM_ASSERT_CHK (1),
        .SRC_INPUT_REG  (0),
        .WIDTH          (18)
    ) downlink_freedrp_status_sync (
        .src_clk  (mgt_freedrpclk),
        .src_in   ({downlinkPhase[i],
                    lpgbtfpga_mgt_txaligned[i],
                    lpgbtfpga_mgt_txpiphase[i]}),
        .dest_clk (lpgbtfpga_clk40),
        .dest_out ({downlinkPhase_sync40[i],
                    lpgbtfpga_mgt_txaligned_sync40[i],
                    lpgbtfpga_mgt_txpiphase_sync40[i]})
    );

    xpm_cdc_single #(
        .DEST_SYNC_FF   (2),
        .INIT_SYNC_FF   (0),
        .SIM_ASSERT_CHK (1),
        .SRC_INPUT_REG  (0)
    ) downlink_ready_sync (
        .src_clk  (lpgbtfpga_mgttxclk[i]),
        .src_in   (lpgbtfpga_downlinkrdy_raw[i]),
        .dest_clk (lpgbtfpga_clk40),
        .dest_out (lpgbtfpga_downlinkrdy[i])
    );

    ic_tx #(
        .g_FIFO_DEPTH      (453),  //Defines the depth of the FIFO used to handle the Internal control (Max. number of words/bytes can be read/write from/to a GBTx)
        .g_LPGBT_VERS      (1'b1)) //Select lpGBT version ('0': 0, '1': 1)
    ic_tx_inst(
        .tx_clk_i          (lpgbtfpga_clk40),
        .tx_clk_en         (1'b1),
        .reset_i           (sc_reset_control), //Reset all TX processes
        .tx_ready_o        (),
        .GBTx_address_i    (ic_GBTx_address_control[i]),
        .Register_addr_i   (ic_Register_addr_control[i]),
        .nb_to_be_read_i   ({8'b0,ic_nb_to_be_read_control[i]}),
        .parity_err_mask_i ('b0),
        .wr_clk_i          (lpgbtfpga_clk40),  //IC tx Fifo's writing clock
        .wr_i              (ic_fifo_wr_control[i]),
        .data_i            (ic_wfifo_data_control[i]),
        .start_read        (ic_rd_start_control[i]),
        .start_write       (ic_wr_start_control[i]),
        .tx_data_o         (lpgbtfpga_downlinkIcData[i])   //(TX) Array of bits to be mapped to the TX GBT-Frame (bits 83/84)
    );

    sca_top #(
        .g_SCA_COUNT(SCA_PER_DOWNLINK)
    )
    sca_inst(
        .tx_clk_i           (lpgbtfpga_clk40),
        .tx_clk_en          (1'b1),
        .rx_clk_i           (lpgbtfpga_clk40),
        .rx_clk_en          (1'b1),
        .rx_reset_i         (sc_reset_control),
        .tx_reset_i         (sc_reset_control),
        .enable_i           (sca_enable_array_mux[i]), //Enable flag to select SCAs
        .start_reset_cmd_i  (sca_start_reset_mux[i]),  //Send a reset command to the enabled SCAs
        .start_connect_cmd_i(sca_start_connect_mux[i]), //Send a connect command to the enabled SCAs
        .start_command_i    (sca_start_command_mux[i]), //Send the command set in input to the enabled SCAs
        .inject_crc_error   (1'b0), //Emulate a CRC error
        .tx_address_i       (sca_tx_address_mux[i]),
        .tx_transid_i       (sca_tx_transID_mux[i]),
        .tx_channel_i       (sca_tx_channel_mux[i]),
        .tx_len_i           (SCA_COMMAND_DATA_BYTES),
        .tx_command_i       (sca_tx_command_mux[i]),
        .tx_data_i          (sca_tx_data_mux[i]),
        .rx_received_o      (sca_rx_done[i]),  //Reply received flag (pulse)
        .rx_address_o       (sca_rx_addr[i]),
        .rx_control_o       (),
        .rx_transid_o       (sca_rx_trid[i]),
        .rx_channel_o       (sca_rx_ch[i]),
        .rx_len_o           (sca_rx_len[i]),
        .rx_error_o         (sca_rx_err[i]),
        .rx_data_o          (sca_rx_data[i]),
        .tx_data_o          (sca_line_tx[i]),  // downlink -- txData_to_gbtExmplDsgn(81 downto 80), (TX) Array of bits to be mapped to the TX GBT-Frame
        .rx_data_i          (sca_line_rx[i])  //uplink  -- rxData_from_gbtExmplDsgn(81 downto 80),  (RX) Array of bits to be mapped to the RX GBT-Frame
    );
end


genvar uplink_reset_i;
for (uplink_reset_i = 0; uplink_reset_i < UPLINKCOUNT;
     uplink_reset_i = uplink_reset_i + 1) begin : uplink_reset_sync
    xpm_cdc_async_rst #(
        .DEST_SYNC_FF    (5),
        .INIT_SYNC_FF    (0),
        .RST_ACTIVE_HIGH (1)
    ) uplink_rst_sync (
        .src_arst  (uplink_reset_control[uplink_reset_i]),
        .dest_clk  (mgt_freedrpclk),
        .dest_arst (uplink_reset_freedrp[uplink_reset_i])
    );
end

xpm_cdc_async_rst #(
 .DEST_SYNC_FF    (5),
 .INIT_SYNC_FF    (0),
 .RST_ACTIVE_HIGH (1)
) downlink_rst_sync (
 .src_arst  (downlink_reset_control),
 .dest_clk  (mgt_freedrpclk),
 .dest_arst (downlink_reset_freedrp)
);

wire [7:0] ethernet_fpga_register_address;
wire [7:0] ethernet_fpga_readback_selector;
wire [159:0] ethernet_fpga_register_write_data;
wire ethernet_fpga_reg_write;
wire ethernet_fpga_reg_reset;
wire ethernet_fpga_reg_read;



MiniDAQ_reg #(
      .UPLINKCOUNT(UPLINKCOUNT),
      .DOWNLINKCOUNT(DOWNLINKCOUNT)
   ) inst_MiniDAQ_reg (
        .clk                         (lpgbtfpga_clk40),
        .rst                         (power_on_reset_40),
        .register_reset_i            (ethernet_fpga_reg_reset),
        .register_address_i          (ethernet_fpga_register_address),
        .readback_selector_i         (ethernet_fpga_readback_selector),
        .register_write_data_i       (ethernet_fpga_register_write_data),
        .register_write_i            (ethernet_fpga_reg_write),
        .register_read_i             (ethernet_fpga_reg_read),

        .locked_dline0               (locked_dline0),
        .locked_dline1               (locked_dline1),
        .lpgbtfpga_uplinkrdy         (lpgbtfpga_uplinkrdy),
        .lpgbtfpga_downlinkrdy       (lpgbtfpga_downlinkrdy),
        .uplink_fec_corrected_latched_i (upLinkFECCorrectedLatched_sync40),
        .uplink_phase_i              (uplinkPhase_sync40),
        .downlink_phase_i            (downlinkPhase_sync40),
        .downlink_tx_aligned_i       (lpgbtfpga_mgt_txaligned_sync40),
        .downlink_tx_pi_phase_i      (lpgbtfpga_mgt_txpiphase_sync40),

        .total_received_40bit_dline1 (total_received_40bit_dline1),
        .total_received_40bit_dline0 (total_received_40bit_dline0),
        .total_error_bit_dline1      (total_error_bit_dline1),
        .total_error_bit_dline0      (total_error_bit_dline0),

        .run_enable_o                (run_enable),
        .stream_hits_only_o          (stream_hits_only),
        .noise_counter_stream_o      (noise_counter_stream),
        .noise_counter_clear_o       (noise_counter_clear),
        .acquisition_mode_o          (acquisition_mode),

        .readback_valid_o            (fpga_readback_valid),
        .readback_data_o             (fpga_readback_data),

        .sc_reset_o                  (sc_reset_control),
        .global_rst_o                (global_rst_control),
        .bc_rst_o                    (bc_rst_control),
        .event_rst_o                 (event_rst_control),
        .master_rst_o                (master_rst_control),
        .mezz_TRST_o                 (mezz_TRST),
        .uplink_reset_o              (uplink_reset_control),
        .downlink_reset_o            (downlink_reset_control),
        .system_reset_pulse_o        (system_reset_pulse),
        .uplink_interleaver_bypass_o (upLinkInterleaverBypass),
        .uplink_fec_bypass_o         (upLinkFecBypass),
        .uplink_scrambler_bypass_o   (upLinkScramblerBypass),
        .uplink_rx_polarity_o        (lpgbtfpga_mgt_rxpolarity),
        .uplink_fec_clear_o          (upLinkFECCorrectedClear),
        .uplink_phase_calib_o        (uplinkPhaseCalib),
        .uplink_phase_force_o        (uplinkPhaseForce),
        .downlink_interleaver_bypass_o (downLinkBypassInterleaver),
        .downlink_fec_bypass_o       (downLinkBypassFECEncoder),
        .downlink_scrambler_bypass_o (downLinkBypassScrambler),
        .downlink_tx_pi_calib_o      (lpgbtfpga_mgt_txpicalib),
        .downlink_tx_calib_enable_o  (lpgbtfpga_mgt_txcaliben),
        .downlink_tx_polarity_o      (lpgbtfpga_mgt_txpolarity),
        .downlink_phase_calib_o      (downlinkPhaseCalib),
        .downlink_phase_force_o      (downlinkPhaseForce),

        .en_int_trigger_o            (en_int_trigger),
        .enable_hit_o                (enable_hit),
        .hit_inv_o                   (hit_inv),
        .hit_single_o                (hit_single),
        .hit_width_o                 (hit_width),
        .hit_interval_o              (hit_interval),

        .correct_counter_th_o        (correct_counter_th),
        .enable_K28_1_o              (enable_K28_1),
        .enable_320M_o               (enable_320M),
        .trigger_deadtime_o          (trigger_deadtime),
        .match_window_o              (match_window),
        .search_margin_o             (search_margin),
        .bc_offset_o                 (bc_offset),
        .reject_offset_o             (reject_offset),
        .rollover_o                  (rollover),
        .coarse_count_offset_o       (coarse_count_offset),
        .en_relative_trig_data_o     (en_relative_trig_data),
        .enable_matching_o           (enable_matching),
        .trigger_redge_o             (trigger_redge),      
        .trigger_latency_o           (trigger_latency),
        .phase_sel_160M_20b_o        (phase_sel_160M_20b),

        .drpen_o                     (drpen_control),
        .drpwe_o                     (drpwe_control),
        .drpaddr_o                   (drpaddr_control),
        .drpdi_o                     (drpdi_control),
        .rxprbscntreset_o            (rxprbscntreset_control),
        .rxprbssel_o                 (rxprbssel_control),
        .window_cycles_o             (window_cycles),
        .hit_threshold_o             (hit_threshold),
        .hit_upper_threshold_o       (hit_upper_threshold),
        .fsm_watchdog_cycles_o       (fsm_watchdog_cycles),
        .tdc_enable_mask_o           (tdc_enable_mask),
        .tdc_chamber1_mask_o         (tdc_chamber1_mask),
        .geometry_lookup_address_i  (geometry_lookup_address),
        .geometry_lookup_data_o     (geometry_lookup_data),
        .geometry_ready_o           (geometry_ready),
        .tube_filter_settings_o     (tube_filter_settings),
        .geometry_mls_o             (geometry_mls),
        .geometry_layers_o          (geometry_layers),
        .diagnostic_pulses_i         (diagnostic_pulses),
        .diagnostic_fifo_lost_words_i(diagnostic_fifo_lost_words),
        .drpdo_i                     (drpdo_ip),
        .rxprbserr_i                 (rxprbserr_ip),
        .rxprbslocked_i              (rxprbslocked_ip)
   );



lpgbtFpga_10g24 #(
    .FEC(FEC5),
    .UPLINKCOUNT(UPLINKCOUNT),
    .DOWNLINKCOUNT(DOWNLINKCOUNT))
lpgbtFpga_top_inst (
//Clocks
    .downlinkClk_i               (lpgbtfpga_clk40), //all downlink data starts from this clock, and will be
                                                  //synced to individual downlink by cdc_tx
    .uplinkClk_i                 (lpgbtfpga_clk40), //all data from different uplinks are synced to 
                                                  //this clock by cdc_rx
    .downlinkRst_i               (downlink_reset_freedrp),
    .uplinkRst_i                 (uplink_reset_freedrp),
//Downlink
    .downlinkUserData_i          (lpgbtfpga_downlinkUserData),
    .downlinkEcData_i            (lpgbtfpga_downlinkIcData),  //IC data are copied to EC line, distinguished by GBT address
    .downlinkIcData_i            (lpgbtfpga_downlinkIcData),
    .downLinkBypassInterleaver_i (downLinkBypassInterleaver_txclk),
    .downLinkBypassFECEncoder_i  (downLinkBypassFECEncoder_txclk),
    .downLinkBypassScrambler_i   (downLinkBypassScrambler_txclk),
    .downlinkReady_o             (lpgbtfpga_downlinkrdy_raw),
    .downlinkPhase_o             (downlinkPhase),
    .downlinkPhaseCalib_i        (downlinkPhaseCalib_freedrp),
    .downlinkPhaseForce_i        (downlinkPhaseForce_freedrp),
//uplink
    .uplinkUserData_o            (lpgbtfpga_uplinkUserData),
    .uplinkEcData_o              (),
    .uplinkIcData_o              (lpgbtfpga_uplinkIcData),
    .uplinkBypassInterleaver_i   (upLinkInterleaverBypass_rxclk),
    .uplinkBypassFECEncoder_i    (upLinkFecBypass_rxclk),
    .uplinkBypassScrambler_i     (upLinkScramblerBypass_rxclk),
    .uplinkFECCorrectedClear_i   (upLinkFECCorrectedClear_rxclk),
    .uplinkFECCorrectedLatched_o (upLinkFECCorrectedLatched),
    .uplinkReady_o               (lpgbtfpga_uplinkrdy_raw),
    .uplinkPhase_o               (uplinkPhase),
    .uplinkPhaseCalib_i          (uplinkPhaseCalib_rxclk),
    .uplinkPhaseForce_i          (uplinkPhaseForce_rxclk),
//MGT
    .mgt_rxn_i                   (SFP_RX_N),
    .mgt_rxp_i                   (SFP_RX_P),
    .mgt_txn_o                   (SFP_TX_N),
    .mgt_txp_o                   (SFP_TX_P),
    .clk_mgtrefclk_i             (mgtRefClk_from_smaMgtRefClkbuf),
    .clk_mgtfreedrpclk_i         (mgt_freedrpclk),
    .clk_mgtRxClk_o              (lpgbtfpga_mgtrxclk),
    .clk_mgtTxClk_o              (lpgbtfpga_mgttxclk),
    .mgt_txpolarity_i            (lpgbtfpga_mgt_txpolarity_freedrp),
    .mgt_rxpolarity_i            (lpgbtfpga_mgt_rxpolarity_rxclk),
    .mgt_txcaliben_i             (lpgbtfpga_mgt_txcaliben_freedrp),
    .mgt_txcalib_i               (lpgbtfpga_mgt_txpicalib_freedrp),
    .mgt_txaligned_o             (lpgbtfpga_mgt_txaligned),
    .mgt_txphase_o               (lpgbtfpga_mgt_txpiphase),
//drp interface
    .drpen_i                     (drpen_control),
    .drpwe_i                     (drpwe_control),
    .drpaddr_i                   (drpaddr_control),
    .drpdi_i                     (drpdi_control),
    .rxprbscntreset_i            (rxprbscntreset_control),
    .rxprbssel_i                 (rxprbssel_control),
    .drpdo_o                     (drpdo_ip),
    .rxprbserr_o                 (rxprbserr_ip),
    .rxprbslocked_o              (rxprbslocked_ip)
);

tdc_decoder_top# (
    .UPLINKCOUNT(UPLINKCOUNT),
    .TDC_COUNT_SINGLE(10))
tdc_decoder_top_inst
(
    .clk_40                (lpgbtfpga_clk40),
    .clk_asyn              (mgt_freedrpclk),
    .rst_in                (system_reset_pulse|global_rst_control),
    .acquisition_mode      (acquisition_mode),
    .run_enable            (run_enable),
    .stream_hits_only      (stream_hits_only),
    .noise_counter_stream  (noise_counter_stream),
    .noise_counter_clear   (noise_counter_clear),
    .userDataUpLink        (lpgbtfpga_uplinkUserData),
    .trigger_in            (trigger_SMA),
    .encode_ttc            (ttc_ctrl),

    .locked_dline1_o       (locked_dline1),
    .locked_dline0_o       (locked_dline0),

    .bc_rst                (bc_rst_control),
    .event_rst             (event_rst_control),
    .master_rst            (master_rst_control),

    .en_int_trigger        (en_int_trigger),
    .enable_hit            (enable_hit),
    .hit_inv               (hit_inv),
    .hit_single            (hit_single),
    .width_hit             (hit_width),
    .hit_interval          (hit_interval),
    
    .correct_counter_th    (correct_counter_th),
    .enable_K28_1          (enable_K28_1),
    .enable_320M           (enable_320M),
    .trigger_deadtime      (trigger_deadtime),
    .match_window          (match_window),
    .search_margin         (search_margin),
    .bc_offset             (bc_offset),
    .reject_offset         (reject_offset),
    .rollover              (rollover),
    .coarse_count_offset   (coarse_count_offset),
    .enable_relative_trigger_data (en_relative_trig_data),
    .enable_matching       (enable_matching),
    .trigger_redge         (trigger_redge),
    .trigger_latency       (trigger_latency),
    .window_cycles         (window_cycles),
    .hit_threshold         (hit_threshold),
    .hit_upper_threshold   (hit_upper_threshold),
    .fsm_watchdog_cycles   (fsm_watchdog_cycles),
    .tdc_enable_mask       (tdc_enable_mask),
    .tdc_chamber1_mask     (tdc_chamber1_mask),
    .geometry_lookup_address(geometry_lookup_address),
    .geometry_lookup_data (geometry_lookup_data),
    .geometry_ready       (geometry_ready),
    .tube_filter_settings (tube_filter_settings),
    .geometry_mls         (geometry_mls),
    .geometry_layers      (geometry_layers),
    .diagnostic_pulses     (diagnostic_pulses),
    .diagnostic_fifo_lost_words(diagnostic_fifo_lost_words),
    .phase_sel_160M_20b    (phase_sel_160M_20b),

    .total_received_40bit_dline1 (total_received_40bit_dline1),
    .total_received_40bit_dline0 (total_received_40bit_dline0),
    .total_error_bit_dline1      (total_error_bit_dline1),
    .total_error_bit_dline0      (total_error_bit_dline0),
    .noise_hit_counts            (),
    .tx_axis_clk                    (tx_axis_clk),
    .ethernet_programming_active    (ethernet_program_session_active_125),
    .tx_axis_fifo_tdata             (hit_tx_axis_tdata),
    .tx_axis_fifo_tvalid            (hit_tx_axis_tvalid),
    .tx_axis_fifo_tready            (hit_tx_axis_tready),
    .tx_axis_fifo_tlast             (hit_tx_axis_tlast),
    .hit_fifo_occupancy             (hit_fifo_occupancy)
);


// KCU105: SGMII variant of the TEMAC example-design wrapper (rtl/board/
// tri_mode_ethernet_mac_0_example_design.v) -- same module name and same user-side AXI-S ports as
// the upstream RGMII wrapper; only the PHY-facing ports differ.
tri_mode_ethernet_mac_0_example_design ethernet_mac
(
    // Keep the Ethernet control plane alive across software datapath resets;
    // otherwise a register-45 request destroys the ACK for its own command.
    .glbl_rst            (power_on_reset_40),
    .free_clk            (mgt_freedrpclk),   // PHY reset timer: must not depend on the PHY's clock

    .gtx_clk_bufg_out    (tx_axis_clk),
    .phy_resetn          (phy_resetn),

    //-- SGMII interface (625 MHz PHY reference clock + LVDS SERDES lane pair)
    .sgmii_refclk625_p   (SGMIICLK_P),
    .sgmii_refclk625_n   (SGMIICLK_N),
    .sgmii_txp           (SGMII_TX_P),
    .sgmii_txn           (SGMII_TX_N),
    .sgmii_rxp           (SGMII_RX_P),
    .sgmii_rxn           (SGMII_RX_N),


    //-- MDIO terface
    .mdio                (mdio),
    .mdc                 (mdc),

    //-- USER side RX AXI-S interface
    .rx_axis_fifo_aclk     (ethernet_rx_axis_clk),
    .rx_axis_fifo_aresetn  (ethernet_rx_axis_resetn),
    .rx_axis_fifo_tdata    (ethernet_rx_axis_tdata),
    .rx_axis_fifo_tvalid   (ethernet_rx_axis_tvalid),
    .rx_axis_fifo_tready   (ethernet_rx_axis_tready),
    .rx_axis_fifo_tlast    (ethernet_rx_axis_tlast),
    .rx_axis_fifo_overflow (ethernet_rx_mac_fifo_overflow),

    //-- USER side TX AXI-S terface       
    .tx_axis_fifo_tdata  (tx_axis_fifo_tdata),
    .tx_axis_fifo_tvalid (tx_axis_fifo_tvalid),
    .tx_axis_fifo_tready (tx_axis_fifo_tready),
    .tx_axis_fifo_tlast  (tx_axis_fifo_tlast)
);

// Keep the vendor TEMAC instance above at board level so its generated
// constraints retain the existing hierarchy. Everything on its client side is
// contained in this application-level Ethernet subsystem.
minidaq_ethernet_subsystem #(
    .UPLINK_COUNT            (UPLINKCOUNT),
    .DOWNLINK_COUNT          (DOWNLINKCOUNT),
    .SCA_COUNT               (SCA_PER_DOWNLINK),
    .FPGA_MAC                (48'h020000C70501),
    .PROGRAM_ETHERTYPE       (16'h88B5),
    .MAX_CHUNK_BYTES         (1408),
    .DATA_FIFO_DEPTH         (128),
    .HIT_COUNT_WIDTH         (16),
    .HIT_HIGH_WATER          (1024),
    .HIT_LOW_WATER           (256),
    .MONITOR_MIN_GAP_CYCLES  (125000)
) ethernet_subsystem (
    .rx_clk                     (ethernet_rx_axis_clk),
    .rx_resetn                  (ethernet_rx_axis_resetn),
    .rx_tdata                   (ethernet_rx_axis_tdata),
    .rx_tvalid                  (ethernet_rx_axis_tvalid),
    .rx_tready                  (ethernet_rx_axis_tready),
    .rx_tlast                   (ethernet_rx_axis_tlast),
    .tx_clk                     (tx_axis_clk),
    .tx_tdata                   (tx_axis_fifo_tdata),
    .tx_tvalid                  (tx_axis_fifo_tvalid),
    .tx_tready                  (tx_axis_fifo_tready),
    .tx_tlast                   (tx_axis_fifo_tlast),
    .control_clk                (lpgbtfpga_clk40),
    .control_reset              (power_on_reset_40),
    .hit_fifo_occupancy         (hit_fifo_occupancy),
    .hit_tdata                  (hit_tx_axis_tdata),
    .hit_tvalid                 (hit_tx_axis_tvalid),
    .hit_tready                 (hit_tx_axis_tready),
    .hit_tlast                  (hit_tx_axis_tlast),
    .fpga_register_address      (ethernet_fpga_register_address),
    .fpga_readback_selector     (ethernet_fpga_readback_selector),
    .fpga_register_write_data   (ethernet_fpga_register_write_data),
    .fpga_register_write        (ethernet_fpga_reg_write),
    .fpga_register_read         (ethernet_fpga_reg_read),
    .fpga_register_reset        (ethernet_fpga_reg_reset),
    .fpga_readback_data         (fpga_readback_data),
    .fpga_readback_valid        (fpga_readback_valid),
    .ic_gbtx_address            (ic_GBTx_address_control),
    .ic_register_address        (ic_Register_addr_control),
    .ic_read_count              (ic_nb_to_be_read_control),
    .ic_start_write             (ic_wr_start_control),
    .ic_start_read              (ic_rd_start_control),
    .ic_write_data              (ic_wfifo_data_control),
    .ic_write_enable            (ic_fifo_wr_control),
    .ic_rx_reset                (ic_rx_reset_control),
    .ic_rx_fifo_empty           (ic_rx_fifo_empty),
    .ic_rx_fifo_data            (data_from_gbtic),
    .ic_rx_fifo_read            (ic_rx_fifo_read_control),
    .sca_enable                 (sca_enable_array_mux),
    .sca_start_reset            (sca_start_reset_mux),
    .sca_start_connect          (sca_start_connect_mux),
    .sca_start_command          (sca_start_command_mux),
    .sca_tx_address             (sca_tx_address_mux),
    .sca_tx_transid             (sca_tx_transID_mux),
    .sca_tx_channel             (sca_tx_channel_mux),
    .sca_tx_command             (sca_tx_command_mux),
    .sca_tx_data                (sca_tx_data_mux),
    .sca_rx_done                (sca_rx_done),
    .sca_rx_address             (sca_rx_addr),
    .sca_rx_transid             (sca_rx_trid),
    .sca_rx_channel             (sca_rx_ch),
    .sca_rx_length              (sca_rx_len),
    .sca_rx_error               (sca_rx_err),
    .sca_rx_data                (sca_rx_data),
    .programming_active         (),
    .programming_session_active (ethernet_program_session_active_125),
    .program_data_fifo_full     (ethernet_program_data_fifo_full),
    .program_data_fifo_overflow (ethernet_program_data_fifo_overflow),
    .program_descriptor_fifo_full
                                  (ethernet_program_descriptor_fifo_full),
    .program_result_fifo_full   (ethernet_program_result_fifo_full)
);


endmodule
