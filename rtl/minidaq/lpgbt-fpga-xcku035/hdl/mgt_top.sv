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
// File   : mgt_top.sv
// Create : 2023-10-02 18:56:05
// Revise : 2025-09-18 16:47:00
// Editor : sublime text4, tab size (4)
// Description: 
//
// -----------------------------------------------------------------------------



module mgt_top
    #(parameter UPLINKCOUNT = 2,
                CLKREFCOUNT = 1
    )

(
    input                               MGT_REFCLK_i,
    input                               MGT_FREEDRPCLK_i,
             
    output  [UPLINKCOUNT-1:0]           MGT_RXUSRCLK_o,
    output  [UPLINKCOUNT-1:0]           MGT_TXUSRCLK_o,
       
    // -- Resets      --
    input                               MGT_TXRESET_i,
    input   [UPLINKCOUNT-1:0]           MGT_RXRESET_i,
       
    // -- Control     --
    input   [UPLINKCOUNT-1:0]           MGT_TXPolarity_i,
    input   [UPLINKCOUNT-1:0]           MGT_RXPolarity_i,
       
    input   [UPLINKCOUNT-1:0]           MGT_RXSlide_i,

    input   [UPLINKCOUNT-1:0]           MGT_ENTXCALIBIN_i,
    input   [6:0]                       MGT_TXCALIB_i[UPLINKCOUNT-1:0],
                    
    // -- Status      --
    output  [UPLINKCOUNT-1:0]           MGT_TXREADY_o,
    output  [UPLINKCOUNT-1:0]           MGT_RXREADY_o,
    output  [UPLINKCOUNT-1:0]           MGT_TX_ALIGNED_o,
    output  [6:0]                       MGT_TX_PIPHASE_o[UPLINKCOUNT-1:0],

    // -- Data         --
    input   [31:0]                      MGT_TX_USRWORD_i[UPLINKCOUNT-1:0],
    output  reg [31:0]                  MGT_RX_USRWORD_o[UPLINKCOUNT-1:0],

    // -- Serial intf.  --
    input   [UPLINKCOUNT-1:0]           RXn_i,
    input   [UPLINKCOUNT-1:0]           RXp_i,
    output  [UPLINKCOUNT-1:0]           TXn_o,
    output  [UPLINKCOUNT-1:0]           TXp_o,

    // drp interface
    input   [UPLINKCOUNT-1:0]       drpen_i,
    input   [UPLINKCOUNT-1:0]       drpwe_i,
    input   [UPLINKCOUNT*9-1:0]     drpaddr_i,
    input   [UPLINKCOUNT*16-1:0]    drpdi_i,
    input   [UPLINKCOUNT-1:0]       rxprbscntreset_i,
    input   [UPLINKCOUNT*4-1:0]     rxprbssel_i,

    output  reg [UPLINKCOUNT*16-1:0]    drpdo_o,
    output  [UPLINKCOUNT-1:0]       rxprbserr_o,
    output  [UPLINKCOUNT-1:0]       rxprbslocked_o
); 

wire                            rx_reset_done;
wire    [(UPLINKCOUNT*32-1):0]  MGT_RX_USRWORD;
wire    [(UPLINKCOUNT*32-1):0]  MGT_TX_USRWORD;
wire    [UPLINKCOUNT-1:0]       gtwiz_buffbypass_rx_reset_in;
wire    [CLKREFCOUNT-1:0]       gtrefclk00_in;
// wire [CLKREFCOUNT-1:0] qpll0outclk_out;
// wire [CLKREFCOUNT-1:0] qpll0outrefclk_out;
wire    [UPLINKCOUNT-1:0]       rx_wordclk_sig;
wire    [UPLINKCOUNT-1:0]       rxoutclk_sig;

wire    [UPLINKCOUNT-1:0]       drpclk_in;

wire    [UPLINKCOUNT*9-1:0]     drpaddr_toip;
wire    [UPLINKCOUNT*16-1:0]    drpdi_toip;
wire    [UPLINKCOUNT-1:0]       drpen_toip;
wire    [UPLINKCOUNT-1:0]       drpwe_toip;
wire    [UPLINKCOUNT*16-1:0]    drpdo_fromip;
wire    [15:0]                  drpdo[UPLINKCOUNT-1:0];




wire    [8:0]                   drpaddr[UPLINKCOUNT-1:0];
wire    [15:0]                  drpdi[UPLINKCOUNT-1:0];
wire    [UPLINKCOUNT-1:0]       drpen;
wire    [UPLINKCOUNT-1:0]       drpwe;




wire    [UPLINKCOUNT*4-1:0]     rxprbssel_toip;
wire    [UPLINKCOUNT-1:0]       rxusrclk_in;
wire    [UPLINKCOUNT-1:0]       rxusrclk2_in;

wire    [UPLINKCOUNT-1:0]       txpippmen;
wire    [UPLINKCOUNT-1:0]       txpippmovrden;
wire    [UPLINKCOUNT-1:0]       txpippmpd;
wire    [UPLINKCOUNT-1:0]       txpippmsel;
wire    [4:0]                   txpippmstepsize[UPLINKCOUNT-1:0];
wire    [UPLINKCOUNT*5-1:0]     txpippmstepsize_toip;
wire    [UPLINKCOUNT-1:0]       txusrclk_in;
wire    [UPLINKCOUNT-1:0]       txusrclk2_in;
wire    [UPLINKCOUNT-1:0]       tx_wordclk_sig;


wire    [UPLINKCOUNT-1:0]       drprdy;
wire    [UPLINKCOUNT-1:0]       rxpmaresetdone;


wire    [1:0]                   txbufstatus[UPLINKCOUNT-1:0];
wire    [UPLINKCOUNT*2-1:0]     txbufstatus_fromip;
wire    [UPLINKCOUNT-1:0]       txoutclk_sig;
wire    [UPLINKCOUNT-1:0]       txpmaresetdone;

wire    [UPLINKCOUNT-1:0]       rxfsm_reset_done;
wire    [UPLINKCOUNT-1:0]       rxfsm_reset_error;
wire    [UPLINKCOUNT-1:0]       mgt_rx_ready;
wire                            rx_reset_sig;
wire                            tx_reset_sig;
wire                            tx_reset_done;
wire    [UPLINKCOUNT-1:0]       MGT_TX_ALIGNED;
wire    [UPLINKCOUNT-1:0]       tx_reset_hptd_ip;
wire    [UPLINKCOUNT-1:0]       tx_reset_hptd_ip_sync;
wire    [UPLINKCOUNT-1:0]       gtwiz_userclk_tx_reset_int;
wire    [UPLINKCOUNT-1:0]       gtwiz_userclk_rx_reset_int;
wire    [UPLINKCOUNT-1:0]       inv_gtwiz_userclk_tx_reset_int;
wire    [UPLINKCOUNT-1:0]       inv_gtwiz_userclk_rx_reset_int;
reg     [UPLINKCOUNT-1:0]       gtwiz_userclk_tx_active_int;
reg     [UPLINKCOUNT-1:0]       gtwiz_userclk_rx_active_int;
wire    [UPLINKCOUNT-1:0]       rxBuffBypassRst;

reg     [UPLINKCOUNT-1:0]       drpen_reg0,drpen_reg1;
reg     [UPLINKCOUNT-1:0]       drpwe_reg0,drpwe_reg1;
wire    [UPLINKCOUNT-1:0]       drpen_syn;
wire    [UPLINKCOUNT-1:0]       drpwe_syn;

always @(posedge MGT_FREEDRPCLK_i) begin
    drpen_reg0 <= drpen_i|drpwe_i;
    drpwe_reg0 <= drpwe_i;
    drpen_reg1 <= drpen_reg0;
    drpwe_reg1 <= drpwe_reg0;
end
assign drpen_syn = (~drpen_reg1) & drpen_reg0;
assign drpwe_syn = (~drpwe_reg1) & drpwe_reg0;

genvar i;
for (i = 0; i < UPLINKCOUNT; i++) begin : uplink
    reg [4:0] tx_phase_reset_pipe = 5'b11111;

    // SINGLE buffer-bypass mode supplies one helper per channel. Assert its
    // reset asynchronously and release it in the corresponding RXUSRCLK2
    // domain after that recovered clock is stable.
    xpm_cdc_async_rst #(
        .DEST_SYNC_FF    (5),
        .INIT_SYNC_FF    (0),
        .RST_ACTIVE_HIGH (1)
    ) resetDoneSynch_rx (
        .src_arst  (rxBuffBypassRst[i]),
        .dest_clk  (rx_wordclk_sig[i]),
        .dest_arst (gtwiz_buffbypass_rx_reset_in[i])
    );

    assign MGT_TX_USRWORD[32*(i+1)-1:32*i]   = MGT_TX_USRWORD_i[i];
    assign drpclk_in[i]                      = MGT_FREEDRPCLK_i;
    assign rxusrclk_in[i]                    = rx_wordclk_sig[i];
    assign rxusrclk2_in[i]                   = rx_wordclk_sig[i];
    assign txusrclk_in[i]                    = tx_wordclk_sig[i];
    assign txusrclk2_in[i]                   = tx_wordclk_sig[i];
    assign drpaddr_toip[(i+1)*9-1:i*9]       = drpen[i]==1 ? drpaddr[i] : drpaddr_i[(i+1)*9-1:i*9];
    assign drpen_toip[i]                     = drpen[i]==1 ? drpen[i]   : drpen_syn[i];
    assign drpdi_toip[(i+1)*16-1:i*16]       = drpen[i]==1 ? drpdi[i]   : drpdi_i[(i+1)*16-1:i*16];
    assign drpwe_toip[i]                     = drpen[i]==1 ? drpwe[i]   : drpwe_syn[i];
    assign drpdo[i]                          = drpdo_fromip[(i+1)*16-1:i*16];
    // Both terms are generated in the 100 MHz freerun domain. Keep ready in
    // that domain and synchronize the combined status once at its consumer.
    assign MGT_TXREADY_o[i]                  = tx_reset_done && MGT_TX_ALIGNED[i];
    assign tx_reset_hptd_ip[i]               = ~tx_reset_done;
    assign mgt_rx_ready[i]                   = gtwiz_userclk_rx_active_int[i]
                                             && rxfsm_reset_done[i]
                                             && ~rxfsm_reset_error[i];
    assign MGT_RXREADY_o[i]                  = mgt_rx_ready[i];
    assign gtwiz_userclk_tx_reset_int[i]     = ~txpmaresetdone[i];
    assign gtwiz_userclk_rx_reset_int[i]     = ~rxpmaresetdone[i]; 
    assign inv_gtwiz_userclk_tx_reset_int[i] = ~gtwiz_userclk_tx_reset_int[i];
    assign inv_gtwiz_userclk_rx_reset_int[i] = ~gtwiz_userclk_rx_reset_int[i];
    assign rxBuffBypassRst[i]                = MGT_RXRESET_i[i]
                                            || ~(gtwiz_userclk_rx_active_int[i]);
    assign txbufstatus[i]                    = txbufstatus_fromip[(i+1)*2-1:i*2];
    assign txpippmstepsize_toip[(i+1)*5-1:i*5]= txpippmstepsize[i];


    // tx_reset_done and the phase aligner both use MGT_FREEDRPCLK_i. Keep
    // reset asserted for five additional clocks without creating a CDC.
    always @(posedge MGT_FREEDRPCLK_i) begin
        if (tx_reset_hptd_ip[i])
            tx_phase_reset_pipe <= 5'b11111;
        else
            tx_phase_reset_pipe <= {tx_phase_reset_pipe[3:0], 1'b0};
    end

    assign tx_reset_hptd_ip_sync[i] = tx_phase_reset_pipe[4];


    BUFG_GT rxWordClkBuf_inst(
        .O(rx_wordclk_sig[i]),
        .I(rxoutclk_sig[i]),
        .CE(inv_gtwiz_userclk_rx_reset_int[i]),
        .DIV('b0),
        .CLR('b0),
        .CLRMASK('b0),
        .CEMASK('b0)
    );
    BUFG_GT txWordClkBuf_inst(
        .O(tx_wordclk_sig[i]),
        .I(txoutclk_sig[i]),
        .CE(inv_gtwiz_userclk_tx_reset_int[i]),
        .DIV('b0),
        .CLR('b0),
        .CLRMASK('b0),
        .CEMASK('b0)
    );

    always @(posedge gtwiz_userclk_tx_reset_int[i] or posedge tx_wordclk_sig[i]) begin : activetxUsrClk_proc
        if (gtwiz_userclk_tx_reset_int[i]) 
            gtwiz_userclk_tx_active_int[i] <= 1'b0;
        else
            gtwiz_userclk_tx_active_int[i] <= 1'b1;
    end

    always @(posedge MGT_FREEDRPCLK_i) begin
        if (drprdy[i]) begin
            drpdo_o[i*16+15:i*16] <= drpdo_fromip[i*16+15:i*16];
        end
    end

    always @(posedge gtwiz_userclk_rx_reset_int[i] or posedge rx_wordclk_sig[i]) begin : activerxUsrClk_proc
        if (gtwiz_userclk_rx_reset_int[i]) 
            gtwiz_userclk_rx_active_int[i] <= 1'b0;
        else
            gtwiz_userclk_rx_active_int[i] <= 1'b1;
    end

    always @(negedge mgt_rx_ready[i] or posedge rx_wordclk_sig[i]) begin : rxWordPipeline_proc
        if (~mgt_rx_ready[i])
            MGT_RX_USRWORD_o[i] <= 'b0;
        else
            MGT_RX_USRWORD_o[i] <= MGT_RX_USRWORD[(i+1)*32-1:i*32];
    end

    tx_phase_aligner 
    #(  .g_DRP_NPORT_CTRL(1'b1),
        .g_DRP_ADDR_TXPI_PPM_CFG(9'b010011010))
    tx_phase_aligner_inst(
        // --==============================================================================
        // --! User control/monitor ports
        // --==============================================================================    
        // -- Clock / reset  
        .clk_sys_i             (MGT_FREEDRPCLK_i),
        .reset_i               (tx_reset_hptd_ip_sync[i]),
        .tx_aligned_o          (MGT_TX_ALIGNED[i]),
        .tx_pi_phase_calib_i   (MGT_TXCALIB_i[i]),
        .tx_ui_align_calib_i   (MGT_ENTXCALIBIN_i[i]),
        .tx_fifo_fill_pd_max_i (32'h00400000),
        .tx_fine_realign_i     ('b0),
        .ps_strobe_i           ('b0),
        .ps_inc_ndec_i         ('b0),
        .ps_phase_step_i       ('b0),
        .ps_done_o             (),
        .tx_pi_phase_o         (MGT_TX_PIPHASE_o[i]),
        .tx_fifo_fill_pd_o     (),

        // --==============================================================================
        // --! MGT ports
        // --==============================================================================
        .clk_txusr_i           (tx_wordclk_sig[i]),
        .tx_fifo_fill_level_i  (txbufstatus[i][0]),
        .txpippmen_o           (txpippmen[i]),
        .txpippmovrden_o       (txpippmovrden[i]),
        .txpippmsel_o          (txpippmsel[i]),
        .txpippmpd_o           (txpippmpd[i]),
        .txpippmstepsize_o     (txpippmstepsize[i]),

        .drpaddr_o             (drpaddr[i]),
        .drpen_o               (drpen[i]),
        .drpdi_o               (drpdi[i]),
        .drprdy_i              (drprdy[i]),
        .drpdo_i               (drpdo[i]),
        .drpwe_o               (drpwe[i])
    );
end


assign MGT_TX_ALIGNED_o   = MGT_TX_ALIGNED;

// The Wizard reset controller remains shared because all channels use shared
// QPLLs. Per-uplink Ethernet resets restart only that lane's bypass controller and
// downstream datapath. A simultaneous reset of every lane also restarts the
// shared GT RX reset sequence.
assign rx_reset_sig = (&MGT_RXRESET_i) || !(tx_reset_done && (&MGT_TX_ALIGNED));
assign tx_reset_sig = MGT_TXRESET_i; 

assign MGT_RXUSRCLK_o = rx_wordclk_sig;   
assign MGT_TXUSRCLK_o = tx_wordclk_sig;


genvar j;
for (j = 0; j < CLKREFCOUNT; j++) begin
    assign gtrefclk00_in[j] = MGT_REFCLK_i;
end

xlx_ku_mgt_ip_10g24 xlx_ku_mgt_std_inst (
    .gtwiz_userclk_tx_active_in         (gtwiz_userclk_tx_active_int[0]),  // input wire [0 : 0] gtwiz_userclk_tx_active_in
    .gtwiz_userclk_rx_active_in         (gtwiz_userclk_rx_active_int),
    .gtwiz_buffbypass_rx_reset_in       (gtwiz_buffbypass_rx_reset_in),
    .gtwiz_buffbypass_rx_start_user_in  ({UPLINKCOUNT{1'b0}}),
    .gtwiz_buffbypass_rx_done_out       (rxfsm_reset_done),
    .gtwiz_buffbypass_rx_error_out      (rxfsm_reset_error),
    .gtwiz_reset_clk_freerun_in         (MGT_FREEDRPCLK_i),     // input wire [0 : 0] gtwiz_reset_clk_freerun_in
    .gtwiz_reset_all_in                 (1'b0),                 // input wire [0 : 0] gtwiz_reset_all_in
    .gtwiz_reset_tx_pll_and_datapath_in (tx_reset_sig),         // input wire [0 : 0] gtwiz_reset_tx_pll_and_datapath_in
    .gtwiz_reset_tx_datapath_in         (1'b0),                 // input wire [0 : 0] gtwiz_reset_tx_datapath_in
    .gtwiz_reset_rx_pll_and_datapath_in (1'b0),                 // input wire [0 : 0] gtwiz_reset_rx_pll_and_datapath_in
    .gtwiz_reset_rx_datapath_in         (rx_reset_sig),         // input wire [0 : 0] gtwiz_reset_rx_datapath_in
    .gtwiz_reset_rx_cdr_stable_out      (),                     // output wire [0 : 0] gtwiz_reset_rx_cdr_stable_out
    .gtwiz_reset_tx_done_out            (tx_reset_done),        // output wire [0 : 0] gtwiz_reset_tx_done_out
    .gtwiz_reset_rx_done_out            (rx_reset_done),        // output wire [0 : 0] gtwiz_reset_rx_done_out
    
    .gtwiz_userdata_tx_in  (MGT_TX_USRWORD),                     // input wire [63 : 0] gtwiz_userdata_tx_in
    .gtwiz_userdata_rx_out (MGT_RX_USRWORD),                       // output wire [63 : 0] gtwiz_userdata_rx_out
    
    .gtrefclk00_in         (gtrefclk00_in),                     // input wire [0 : 0] gtrefclk00_in
    .qpll0outclk_out       (),                                  // output wire [0 : 0] qpll0outclk_out
    .qpll0outrefclk_out    (),                                  // output wire [0 : 0] qpll0outrefclk_out
    
    .drpaddr_in            (drpaddr_toip),                      // input wire [17 : 0] drpaddr_in
    .drpclk_in             (drpclk_in),                         // input wire [1 : 0] drpclk_in
    .drpdi_in              (drpdi_toip),                        // input wire [31 : 0] drpdi_in
    .drpen_in              (drpen_toip),                        // input wire [1 : 0] drpen_in
    .drpwe_in              (drpwe_toip),                        // input wire [1 : 0] drpwe_in
    .gthrxn_in             (RXn_i),                             // input wire [1 : 0] gthrxn_in
    .gthrxp_in             (RXp_i),                             // input wire [1 : 0] gthrxp_in
    .rxcommadeten_in       ({UPLINKCOUNT{1'b1}}),               // input wire [1 : 0] rxcommadeten_in
    .rxmcommaalignen_in    ({UPLINKCOUNT{1'b0}}),               // input wire [1 : 0] rxmcommaalignen_in
    .rxpcommaalignen_in    ({UPLINKCOUNT{1'b0}}),               // input wire [1 : 0] rxpcommaalignen_in
    .rxpolarity_in         (MGT_RXPolarity_i),                  // input wire [1 : 0] rxpolarity_in
    .rxprbscntreset_in     (rxprbscntreset_i),                    // input wire [1 : 0] rxprbscntreset_in
    .rxprbssel_in          (rxprbssel_i),                    // input wire [7 : 0] rxprbssel_in
    .rxslide_in            (MGT_RXSlide_i),                     // input wire [1 : 0] rxslide_in
    .rxusrclk_in           (rxusrclk_in),                       // input wire [1 : 0] rxusrclk_in
    .rxusrclk2_in          (rxusrclk2_in),                      // input wire [1 : 0] rxusrclk2_in
    .txpippmen_in          (txpippmen),                         // input wire [1 : 0] txpippmen_in
    .txpippmovrden_in      (txpippmovrden),                     // input wire [1 : 0] txpippmovrden_in
    .txpippmpd_in          (txpippmpd),                         // input wire [1 : 0] txpippmpd_in
    .txpippmsel_in         (txpippmsel),                        // input wire [1 : 0] txpippmsel_in
    .txpippmstepsize_in    (txpippmstepsize_toip),              // input wire [9 : 0] txpippmstepsize_in
    .txpolarity_in         (MGT_TXPolarity_i),                  // input wire [1 : 0] txpolarity_in
    .txusrclk_in           (txusrclk_in),                       // input wire [1 : 0] txusrclk_in
    .txusrclk2_in          (txusrclk2_in),                      // input wire [1 : 0] txusrclk2_in
    .drpdo_out             (drpdo_fromip),                      // output wire [31 : 0] drpdo_out
    .drprdy_out            (drprdy),                            // output wire [1 : 0] drprdy_out
    .gthtxn_out            (TXn_o),                             // output wire [1 : 0] gthtxn_out
    .gthtxp_out            (TXp_o),                             // output wire [1 : 0] gthtxp_out
    .gtpowergood_out       (),                                  // output wire [1 : 0] gtpowergood_out
    .rxbyteisaligned_out   (),                                  // output wire [1 : 0] rxbyteisaligned_out
    .rxbyterealign_out     (),                                  // output wire [1 : 0] rxbyterealign_out
    .rxcommadet_out        (),                                  // output wire [1 : 0] rxcommadet_out
    .rxoutclk_out          (rxoutclk_sig),                      // output wire [1 : 0] rxoutclk_out
    .rxpmaresetdone_out    (rxpmaresetdone),                    // output wire [1 : 0] rxpmaresetdone_out
    .rxprbserr_out         (rxprbserr_o),                         // output wire [1 : 0] rxprbserr_out
    .rxprbslocked_out      (rxprbslocked_o),                      // output wire [1 : 0] rxprbslocked_out
    .txbufstatus_out       (txbufstatus_fromip),                // output wire [3 : 0] txbufstatus_out
    .txoutclk_out          (txoutclk_sig),                      // output wire [1 : 0] txoutclk_out
    .txpmaresetdone_out    (txpmaresetdone)                     // output wire [1 : 0] txpmaresetdone_out
);



endmodule
