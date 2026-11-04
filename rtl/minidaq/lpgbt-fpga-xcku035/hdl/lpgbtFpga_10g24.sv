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
// File   : lpgbtFpga_10g24.sv
// Create : 2023-10-02 17:05:45
// Revise : 2025-09-18 16:48:27
// Editor : sublime text4, tab size (4)
// Description: 
//
// -----------------------------------------------------------------------------
module lpgbtFpga_10g24

    #(parameter FEC = 1,
    parameter UPLINKCOUNT = 2,
    parameter DOWNLINKCOUNT = 1
    )
(
    //clocks
    input                           downlinkClk_i,                //40MHz user clock
    input                           uplinkClk_i,                  //40MHz user clock
    input                           downlinkRst_i,                //Reset the downlink path
    input   [UPLINKCOUNT-1:0]       uplinkRst_i,                 //Independent reset for each uplink path

    //downlinks
    input   [31:0]                  downlinkUserData_i[DOWNLINKCOUNT-1:0],    //Downlink data (user)
    input   [1:0]                   downlinkEcData_i[DOWNLINKCOUNT-1:0],       //Downlink EC field
    input   [1:0]                   downlinkIcData_i[DOWNLINKCOUNT-1:0],       //Downlink IC field
    input   [DOWNLINKCOUNT-1:0]     downLinkBypassInterleaver_i,  //Bypass downlink interleaver (test purpose only)
    input   [DOWNLINKCOUNT-1:0]     downLinkBypassFECEncoder_i,   //Bypass downlink FEC (test purpose only)
    input   [DOWNLINKCOUNT-1:0]     downLinkBypassScrambler_i,    //Bypass downlink scrambler (test purpose only)
    output  [DOWNLINKCOUNT-1:0]     downlinkReady_o,             //Downlink ready status
    output  [9:0]                   downlinkPhase_o[DOWNLINKCOUNT-1:0],       //Phase to check fixed-phase
    input   [9:0]                   downlinkPhaseCalib_i[DOWNLINKCOUNT-1:0],   //Phase measured in first reset
    input   [DOWNLINKCOUNT-1:0]     downlinkPhaseForce_i,          //Force phase after first reset to ensure fixed-phase operation

    //uplinks
    output  [229:0]                 uplinkUserData_o[UPLINKCOUNT-1:0],   //Uplink data (user)
    output  [1:0]                   uplinkEcData_o[UPLINKCOUNT-1:0],       //Uplink EC field
    output  [1:0]                   uplinkIcData_o[UPLINKCOUNT-1:0],       //Uplink IC field
    input   [UPLINKCOUNT-1:0]       uplinkBypassInterleaver_i,  //Bypass uplink interleaver (test purpose only)
    input   [UPLINKCOUNT-1:0]       uplinkBypassFECEncoder_i,   //Bypass uplink FEC (test purpose only)
    input   [UPLINKCOUNT-1:0]       uplinkBypassScrambler_i,    //Bypass uplink scrambler (test purpose only)
    input   [UPLINKCOUNT-1:0]       uplinkFECCorrectedClear_i,  //Uplink FEC corrected error clear (debugging)
    output reg  [UPLINKCOUNT-1:0]   uplinkFECCorrectedLatched_o, //Uplink FEC corrected error latched (debugging)
    output  [UPLINKCOUNT-1:0]       uplinkReady_o,             //Uplink ready status

    //Fixed-phase uplink CDC operation - master
    output  [2:0]                   uplinkPhase_o[UPLINKCOUNT-1:0],     //Phase to check fixed-phase
    input   [2:0]                   uplinkPhaseCalib_i[UPLINKCOUNT-1:0],     //Phase measured in first reset
    input   [UPLINKCOUNT-1:0]       uplinkPhaseForce_i,       //Force the phase to be the calibrated one

    //MGT
    input   [UPLINKCOUNT-1:0]       mgt_rxn_i,
    input   [UPLINKCOUNT-1:0]       mgt_rxp_i,
    output  [UPLINKCOUNT-1:0]     mgt_txn_o,
    output  [UPLINKCOUNT-1:0]     mgt_txp_o,

    input                           clk_mgtrefclk_i,      //Transceiver serial clock
    input                           clk_mgtfreedrpclk_i,      //125MHz Free-running clock

    output  [UPLINKCOUNT-1:0]       clk_mgtRxClk_o,
    output  [DOWNLINKCOUNT-1:0]     clk_mgtTxClk_o,

    input   [DOWNLINKCOUNT-1:0]     mgt_txpolarity_i,
    input   [UPLINKCOUNT-1:0]       mgt_rxpolarity_i,

    input   [DOWNLINKCOUNT-1:0]     mgt_txcaliben_i,
    input   [6:0]                   mgt_txcalib_i[DOWNLINKCOUNT-1:0],
    output  [DOWNLINKCOUNT-1:0]     mgt_txaligned_o,
    output  [6:0]                   mgt_txphase_o[DOWNLINKCOUNT-1:0],

    input   [UPLINKCOUNT-1:0]       drpen_i,
    input   [UPLINKCOUNT-1:0]       drpwe_i,
    input   [UPLINKCOUNT*9-1:0]     drpaddr_i,
    input   [UPLINKCOUNT*16-1:0]    drpdi_i,
    input   [UPLINKCOUNT-1:0]       rxprbscntreset_i,
    input   [UPLINKCOUNT*4-1:0]     rxprbssel_i,
    output  [UPLINKCOUNT*16-1:0]    drpdo_o,
    output  [UPLINKCOUNT-1:0]       rxprbserr_o,
    output  [UPLINKCOUNT-1:0]       rxprbslocked_o
);

    wire [UPLINKCOUNT-1:0]     mgt_txcaliben_mgt;
    wire [UPLINKCOUNT-1:0]     mgt_txaligned_mgt;
    wire [UPLINKCOUNT-1:0]     mgt_txpolarity_mgt;
    wire  [6:0]                   mgt_txphase_mgt[UPLINKCOUNT-1:0];

    wire [6:0]                   mgt_txcalib_mgt[UPLINKCOUNT-1:0];

    // User CDC Tx    
    // wire    [DOWNLINKCOUNT*36-1:0]  downlinkData40;
    wire    [35:0]              downlinkData320[DOWNLINKCOUNT-1:0];
    wire    [DOWNLINKCOUNT-1:0] downlinkStrobe320;
    wire    [DOWNLINKCOUNT-1:0] mgt_txrdy_sync40;
    wire    [DOWNLINKCOUNT-1:0] cdc_tx_reset;
    wire    [DOWNLINKCOUNT-1:0] cdc_tx_ready;
    
    // User CDC Rx
    wire    [233:0]             uplinkData320[UPLINKCOUNT-1:0];
    wire    [UPLINKCOUNT-1:0]   uplinkStrobe320;
    wire    [233:0]             uplinkData40[UPLINKCOUNT-1:0];
    wire    [UPLINKCOUNT-1:0]   cdc_rx_reset;
    wire    [UPLINKCOUNT-1:0]   cdc_rx_ready;

    //MGT
    wire    [UPLINKCOUNT-1:0]   uplinkReady;
    wire    [31:0]              downlink_mgtword[UPLINKCOUNT-1:0];

    wire    [31:0]              uplink_mgtword[UPLINKCOUNT-1:0];
    wire    [UPLINKCOUNT-1:0]   mgt_rxslide;

    wire    [DOWNLINKCOUNT-1:0] mgt_txrdy;
    wire    [UPLINKCOUNT-1:0] mgt_txrdy_mgt;
    wire    [UPLINKCOUNT-1:0]   mgt_rxrdy;
    wire    [UPLINKCOUNT-1:0] clk_mgtTxClk;
    wire    [UPLINKCOUNT-1:0]   clk_mgtRxClk;

    // PRBS controls are written in the 40 MHz user domain but are consumed by
    // the GT in each channel's RXUSRCLK2 domain. The values remain static
    // between writes; synchronize each bit before driving the GT primitive.
    wire    [UPLINKCOUNT-1:0]   rxprbscntreset_rxclk;
    wire    [UPLINKCOUNT*4-1:0] rxprbssel_rxclk;

    // FEC latch flag
    wire    [229:0]             uplinkDataCorrected[UPLINKCOUNT-1:0];
    wire    [1:0]               uplinkIcCorrected[UPLINKCOUNT-1:0];
    wire    [1:0]     uplinkEcCorrected[UPLINKCOUNT-1:0];

    wire    [DOWNLINKCOUNT*7-1:0]   mgt_txphase;

    
    // Reset scheme for downlink:
    // -- downlinkRst_i     => Resets MGT Tx
    // -- MGT Tx ready      => Resets User CDC Tx (responsible for generating the stable strobe aligned to 40MHz clock)
    // -- User CDC Tx ready => Resets downlink datapath

    assign cdc_rx_reset = ~ uplinkReady;
    assign cdc_tx_reset = ~mgt_txrdy_sync40;




genvar j;
for (j = 0; j < DOWNLINKCOUNT; j++) begin : downlink
    assign mgt_txrdy[j] = mgt_txrdy_mgt[2*j];
    assign mgt_txaligned_o[j] = mgt_txaligned_mgt[2*j];
    assign clk_mgtTxClk_o[j] = clk_mgtTxClk[j*2];
    assign downlink_mgtword[j*2+1]='b0;

    xpm_cdc_single #(
        .DEST_SYNC_FF   (2),
        .INIT_SYNC_FF   (0),
        .SIM_ASSERT_CHK (1),
        .SRC_INPUT_REG  (1)
    ) txrdy_sync (
        .src_clk  (clk_mgtfreedrpclk_i),
        .src_in   (mgt_txrdy[j]),
        .dest_clk (downlinkClk_i),
        .dest_out (mgt_txrdy_sync40[j])
    );

    lpgbtfpga_downlink
    #(
        //Expert parameters
        .c_multicyleDelay    (3),
        .c_clockRatio        (8),
        .c_outputWidth       (32)
    )
    downlink_inst(
        //Clocks
        .clk_i               (clk_mgtTxClk_o[j]),
        .clkEn_i             (downlinkStrobe320[j]),
        .rst_n_i             (cdc_tx_ready[j]),
        //Down link
        .userData_i          (downlinkData320[j][31:0]),
        .ECData_i            (downlinkData320[j][33:32]),
        .ICData_i            (downlinkData320[j][35:34]),
        //Output
        .mgt_word_o          (downlink_mgtword[2*j]),
        //Configuration
        .interleaverBypass_i (downLinkBypassInterleaver_i[j]),
        .encoderBypass_i     (downLinkBypassFECEncoder_i[j]),
        .scramblerBypass_i   (downLinkBypassScrambler_i[j]),
        //Status
        .rdy_o               (downlinkReady_o[j])
    );

    cdc_tx
    #(
        .g_CLOCK_A_RATIO (1),
        .g_CLOCK_B_RATIO (8),
        .g_ACC_PHASE     (125*8),
        .g_PHASE_SIZE    (10),
        .data_SIZE       (36)
    )
    cdc_tx_inst(
        //Interface A (latch - from where data comes)
        .reset_a_i       (cdc_tx_reset[j]),
        .clk_a_i         (downlinkClk_i),
        .data_a_i        ({downlinkIcData_i[j],downlinkEcData_i[j],downlinkUserData_i[j]}),
        .strobe_a_i      (1'b1),
        //Interface B (capture - to where data goes)
        .clk_b_i         (clk_mgtTxClk_o[j]),
        .data_b_o        (downlinkData320[j]),
        .strobe_b_o      (downlinkStrobe320[j]),
        .ready_b_o       (cdc_tx_ready[j]),
        //Only relevant for fixed-phase operation
        .clk_freerun_i   (clk_mgtfreedrpclk_i),
        .phase_o         (downlinkPhase_o[j]),
        .phase_calib_i   (downlinkPhaseCalib_i[j]),
        .phase_force_i   (downlinkPhaseForce_i[j])
    );
end


assign clk_mgtRxClk_o = clk_mgtRxClk;

genvar i;
for (i = 0; i < UPLINKCOUNT; i++) begin : uplink

    assign uplinkUserData_o[i] = uplinkData40[i][229:0];
    assign uplinkEcData_o[i]   = uplinkData40[i][231:230];
    assign uplinkIcData_o[i]   = uplinkData40[i][233:232];
    assign uplinkReady_o[i]    = cdc_rx_ready[i];

    xpm_cdc_array_single #(
        .DEST_SYNC_FF   (2),
        .INIT_SYNC_FF   (0),
        .SIM_ASSERT_CHK (1),
        .SRC_INPUT_REG  (0),
        .WIDTH          (4)
    ) rxprbssel_cdc_inst (
        .src_clk        (uplinkClk_i),
        .src_in         (rxprbssel_i[i*4 +: 4]),
        .dest_clk       (clk_mgtRxClk[i]),
        .dest_out       (rxprbssel_rxclk[i*4 +: 4])
    );

    xpm_cdc_single #(
        .DEST_SYNC_FF   (2),
        .INIT_SYNC_FF   (0),
        .SIM_ASSERT_CHK (1),
        .SRC_INPUT_REG  (0)
    ) rxprbscntreset_cdc_inst (
        .src_clk        (uplinkClk_i),
        .src_in         (rxprbscntreset_i[i]),
        .dest_clk       (clk_mgtRxClk[i]),
        .dest_out       (rxprbscntreset_rxclk[i])
    );


    assign mgt_txcalib_mgt[i] = mgt_txcalib_i[i/2];
    assign mgt_txcaliben_mgt[i] = mgt_txcaliben_i[i/2];
    assign mgt_txpolarity_mgt[i] = mgt_txpolarity_i[i/2];

    //FEC Corrected Flag for debugging
    always @(posedge clk_mgtRxClk[i]) begin
        if(uplinkFECCorrectedClear_i[i])
            uplinkFECCorrectedLatched_o[i] <= 1'b0;
        else if (((|(uplinkDataCorrected[i]))!=1'b0) 
            || ((|uplinkIcCorrected[i])!=1'b0)
            || ((|uplinkEcCorrected[i])!=1'b0))
            uplinkFECCorrectedLatched_o[i] <= 1'b1;
    end

    // --========####   Uplink datapath   ####========--
    // -- Reset scheme for uplink:
    // -- uplinkRst_i           => Resets MGT Rx
    // -- MGT Rx ready          => Resets uplink datapath
    // -- Uplink datapath ready => Resets User CDC Rx
    lpgbtfpga_uplink 
    #(
        //General configuration
        .DATARATE                  (2), //10G24=2
        .FEC                       (1), //FEC5=1
        //Expert parameters
        .c_multicyleDelay          (3),
        .c_clockRatio              (8),
        .c_mgtWordWidth            (32),
        .c_allowedFalseHeader      (5),
        .c_allowedFalseHeaderOverN (64),
        .c_requiredTrueHeader      (30),
        .c_bitslip_mindly          (1),
        .c_bitslip_waitdly         (40)
    )
    uplink_inst(
        //Clock and reset
        .uplinkClk_i               (clk_mgtRxClk[i]),
        .uplinkClkOutEn_o          (uplinkStrobe320[i]),
        .uplinkRst_n_i             (mgt_rxrdy[i]),
        //Input
        .mgt_word_i                (uplink_mgtword[i]),
        //Data
        .userData_o                (uplinkData320[i][229:0]),
        .EcData_o                  (uplinkData320[i][231:230]),
        .IcData_o                  (uplinkData320[i][233:232]),
        //Control
        .bypassInterleaver_i       (uplinkBypassInterleaver_i[i]),
        .bypassFECEncoder_i        (uplinkBypassFECEncoder_i[i]),
        .bypassScrambler_i         (uplinkBypassScrambler_i[i]),
        //Transceiver control
        .mgt_bitslipCtrl_o         (mgt_rxslide[i]),
        //Status
        .dataCorrected_o           (uplinkDataCorrected[i]),
        .IcCorrected_o             (uplinkIcCorrected[i]),
        .EcCorrected_o             (uplinkEcCorrected[i]),
        .rdy_o                     (uplinkReady[i]),
        .frameAlignerEven_o        ()
    );

    cdc_rx  
    #(
        .g_CLOCK_A_RATIO (8),    //Frequency ratio between slow and fast frequencies (>4)
        .g_PHASE_SIZE    (3),       //log2(g_CLOCK_A_RATIO)
        .data_SIZE       (234)
    )
    cdc_rx_inst(
        //-- Interface A (latch - from where data comes)
        .reset_a_i       (cdc_rx_reset[i]), 
        .clk_a_i         (clk_mgtRxClk[i]),
        .data_a_i        (uplinkData320[i]),
        .strobe_a_i      (uplinkStrobe320[i]),

        //Interface B (capture_a - to where data goes) 
        .clk_b_i         (uplinkClk_i),
        .data_b_o        (uplinkData40[i]),
        .strobe_b_i      (1'b1),
        .ready_b_o       (cdc_rx_ready[i]),

        //Only relevant for fixed-phase operation
        .phase_o         (uplinkPhase_o[i]),
        .phase_calib_i   (uplinkPhaseCalib_i[i]),
        .phase_force_i   (uplinkPhaseForce_i[i])
    );

end


mgt_top #(
    .UPLINKCOUNT(UPLINKCOUNT),
    .CLKREFCOUNT((UPLINKCOUNT+1)/2)
) mgt_inst (
    .MGT_REFCLK_i      (clk_mgtrefclk_i),
    .MGT_FREEDRPCLK_i  (clk_mgtfreedrpclk_i),
    .MGT_RXUSRCLK_o    (clk_mgtRxClk),
    .MGT_TXUSRCLK_o    (clk_mgtTxClk),
    .MGT_TXRESET_i     (downlinkRst_i),
    .MGT_RXRESET_i     (uplinkRst_i),
    .MGT_TXPolarity_i  (mgt_txpolarity_mgt),
    .MGT_RXPolarity_i  (mgt_rxpolarity_i),
    .MGT_RXSlide_i     (mgt_rxslide),
    .MGT_ENTXCALIBIN_i (mgt_txcaliben_mgt),
    .MGT_TXCALIB_i     (mgt_txcalib_mgt),
    .MGT_TXREADY_o     (mgt_txrdy_mgt),
    .MGT_RXREADY_o     (mgt_rxrdy),
    .MGT_TX_ALIGNED_o  (mgt_txaligned_mgt),
    .MGT_TX_PIPHASE_o  (mgt_txphase_mgt),
    .MGT_TX_USRWORD_i  (downlink_mgtword),
    .MGT_RX_USRWORD_o  (uplink_mgtword),
    .RXn_i             (mgt_rxn_i),
    .RXp_i             (mgt_rxp_i),
    .TXn_o             (mgt_txn_o),
    .TXp_o             (mgt_txp_o),

    .drpen_i           (drpen_i),
    .drpwe_i           (drpwe_i),
    .drpaddr_i         (drpaddr_i),
    .drpdi_i           (drpdi_i),
    .rxprbscntreset_i  (rxprbscntreset_rxclk),
    .rxprbssel_i       (rxprbssel_rxclk),
    .drpdo_o           (drpdo_o),
    .rxprbserr_o       (rxprbserr_o),
    .rxprbslocked_o    (rxprbslocked_o)
);
 
   
endmodule
