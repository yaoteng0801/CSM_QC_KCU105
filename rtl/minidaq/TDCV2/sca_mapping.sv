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
// File   : sca_mapping.sv
// Create : 2024-07-24 20:39:17
// Revise : 2024-11-01 14:21:00
// Editor : sublime text4, tab size (4)
// Description: 
//
// -----------------------------------------------------------------------------
  
module sca_mapping
    #(parameter SCA_PER_DOWNLINK = 4)
    (
    input   [1:0]   sca_line_tx[SCA_PER_DOWNLINK-1:0],
    input   [1:0]   ttc_ctrl,
    input   [229:0] uplinkUserData,

    output  [1:0]   sca_line_rx[SCA_PER_DOWNLINK-1:0],    
    output  [31:0]  downlinkUserData

);

wire    [1:0]   down_elink_80m_sca_pri[SCA_PER_DOWNLINK-1:0];
wire    [1:0]   down_elink_80m_sca_aux[SCA_PER_DOWNLINK-1:0];
wire    [7:0]   uplink_320m [27:0];
wire    [7:0]   uplink_320m_sca_pri[SCA_PER_DOWNLINK-1:0];

genvar m,k;
// Complete GBT-SCA connectivity from
// LpGBT_CSM_preprod_010324_sch.pdf, sheet 5 ("Master LpGBT0").
// The P/N suffix is omitted below; every listed net is a differential pair.
// TX and RX are named from the GBT-SCA point of view:
//   SCA TX -> lpGBT EDIN  -> FPGA uplinkUserData
//   SCA RX <- lpGBT EDOUT <- FPGA downlinkUserData
//
// SCA0:
//   AUX_TX -> EDIN40 -> uplink byte 16
//   PRI_TX -> EDIN41 -> uplink byte 17
//   AUX_RX <- EDOUT30 <- downlink bits [25:24]
//   PRI_RX <- EDOUT31 <- downlink bits [27:26]
//   AUX_CLK <- ECLK19
//   PRI_CLK <- ECLK21
//
// SCA1:
//   AUX_TX -> EDIN22 -> uplink byte 10
//   PRI_TX -> EDIN23 -> uplink byte 11
//   AUX_RX <- EDOUT12 <- downlink bits [13:12]
//   PRI_RX <- EDOUT11 <- downlink bits [11:10]
//   AUX_CLK <- ECLK8
//   PRI_CLK <- ECLK9
//
// SCA2:
//   AUX_TX -> EDIN30 -> uplink byte 12
//   PRI_TX -> EDIN31 -> uplink byte 13
//   AUX_RX <- EDOUT13 <- downlink bits [15:14]
//   PRI_RX <- EDOUT20 <- downlink bits [17:16]
//   AUX_CLK <- ECLK11
//   PRI_CLK <- ECLK12
//
// SCA3:
//   AUX_TX -> EDIN32 -> uplink byte 14
//   PRI_TX -> EDIN33 -> uplink byte 15
//   AUX_RX <- EDOUT21 <- downlink bits [19:18]
//   PRI_RX <- EDOUT23 <- downlink bits [23:22]
//   AUX_CLK <- ECLK14
//   PRI_CLK <- ECLK17
//
// At 320 Mbps, each of the 28 lpGBT ePortRx channels occupies one 8-bit
// slice of uplinkUserData[223:0].  For EDINxy, where x is the ePort group
// and y is the channel within that group, the slice index is 4*x+y.
for (m = 0; m < 28; m=m+1) begin
    assign uplink_320m[m] = uplinkUserData[m*8+7:m*8]; 
end

for (k = 0; k < SCA_PER_DOWNLINK; k=k+1) begin
    //2-bit downlink sca tx mapping
    assign down_elink_80m_sca_pri[k] = sca_line_tx[k];
    assign down_elink_80m_sca_aux[k] = 2'b0;
     
    // Implemented reply selection: all four SCAs use PRI_TX.
    assign uplink_320m_sca_pri[k] = k==0? uplink_320m[17] :
                                    k==1? uplink_320m[11] :
                                    k==2? uplink_320m[13] : uplink_320m[15];

    //2-bit uplink sca rx mapping
    //sca bits are quadruple (80Mbps sampled by 320Mbps)
    // assign sca_line_rx[k] = {uplink_320m_sca_pri[k][4],uplink_320m_sca_pri[k][0]}; 
    //here used voting to select the best phase
    majority_voter_one_bit
    inst_majority_voter_one_bit_LSB (
        .inA(uplink_320m_sca_pri[k][0]), 
        .inB(uplink_320m_sca_pri[k][1]), 
        .inC(uplink_320m_sca_pri[k][2]), 
        .out(sca_line_rx[k][0]), 
        .err());

    majority_voter_one_bit 
    inst_majority_voter_one_bit_MSB (
        .inA(uplink_320m_sca_pri[k][4]), 
        .inB(uplink_320m_sca_pri[k][5]), 
        .inC(uplink_320m_sca_pri[k][6]), 
        .out(sca_line_rx[k][1]), 
        .err());
end

// for 4 SCA version 
// At 80 Mbps, EDOUTxy consumes downlinkUserData[8*x+2*y +: 2].
// The implementation drives all four PRI_RX paths and holds all AUX_RX
// paths at zero; the complete schematic mapping is documented above.
assign downlinkUserData = {4'b0,down_elink_80m_sca_pri[0],down_elink_80m_sca_aux[0],
                                             down_elink_80m_sca_pri[3],2'b00,down_elink_80m_sca_aux[3],
                                             down_elink_80m_sca_pri[2],down_elink_80m_sca_aux[2],
                                             down_elink_80m_sca_aux[1],down_elink_80m_sca_pri[1],
                                             4'b0000,ttc_ctrl,2'b00,ttc_ctrl};   
// for 3 SCA version
// assign downlinkUserData = {8'b0,down_elink_80m_sca_aux[0],2'b00,down_elink_80m_sca_pri[0],
//                                             down_elink_80m_sca_pri[2],2'b00,down_elink_80m_sca_aux[2],
//                                             down_elink_80m_sca_aux[1],down_elink_80m_sca_pri[1],8'b0,ttc_ctrl};
      


endmodule
