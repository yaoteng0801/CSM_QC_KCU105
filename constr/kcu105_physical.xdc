##===================================================================================================##
##========================================  I/O PINS  ===============================================##
## KCU105 (xcku040-ffva1156-2-e) pinout for rtl/board/xcku040_10g24_top.sv (MiniDAQ port,         ##
## UPLINKCOUNT = 2, DOWNLINKCOUNT = 1).  Pin sources: the installed Vivado 2024.1 KCU105 board    ##
## file (XilinxBoardStore .../kcu105/1.7/part0_pins.xml) and the KU040-FFVA1156 package (GTH       ##
## sites checked with get_package_pins); USER_SMA_CLOCK per UG917 -- see the note at TRIGGER0.    ##
## The MiniDAQ board's own pinout (xcku035-fbva676) is in the upstream repo, NOT used here.       ##
##===================================================================================================##

##====================================##
## BITSTREAM CONFIGURATION (KCU105)  ##
## KCU105's configuration bank (bank 0) is 1.8V: CONFIG_VOLTAGE 1.8 requires CFGBVS GND
## (report_drc CFGBVS-4).
##====================================##
set_property CFGBVS GND [current_design]
set_property CONFIG_VOLTAGE 1.8 [current_design]

##==============##
## FABRIC CLOCK ##
## 125 MHz differential user clock (the MiniDAQ board has 200 MHz).  sys_clk (clk_wiz, 125 -> 100
## MHz) turns it into mgt_freedrpclk, so every free-running-clock timing stays as upstream.
##==============##
set_property PACKAGE_PIN G10 [get_ports USER_CLOCK_P]
set_property PACKAGE_PIN F10 [get_ports USER_CLOCK_N]
set_property IOSTANDARD LVDS [get_ports USER_CLOCK_P]
set_property IOSTANDARD LVDS [get_ports USER_CLOCK_N]
set_property DIFF_TERM_ADV TERM_100 [get_ports USER_CLOCK_P]
set_property DIFF_TERM_ADV TERM_100 [get_ports USER_CLOCK_N]

##==========##
## MGT(GTH) ##
##==========##

## MGT CLOCK (320 MHz, external generator on the SMA pair; MGTREFCLK0 of quad 226).  Cables: J33 =
## SMA_MGT_REFCLK_P (V6), J32 = SMA_MGT_REFCLK_N (V5) -- note the P input is the higher-numbered SMA.
set_property PACKAGE_PIN V6 [get_ports SMA_MGT_REFCLK_P]
set_property PACKAGE_PIN V5 [get_ports SMA_MGT_REFCLK_N]

## SERIAL LANES.  Port bit i = GT wizard channel i.  The wizard IP would put channel 0 on X0Y9 and
## channel 1 on X0Y10; constr/kcu105_gth_sites.xdc swaps them so that the cabling is:
##   logical link 0 = channel 0 = GTHE3_CHANNEL_X0Y10 = cage SFP0 (connector P5, U4/U3 tx, T2/T1 rx)
##                    -> MASTER lpGBT: uplink 0 + the (single) downlink 0
##   logical link 1 = channel 1 = GTHE3_CHANNEL_X0Y9  = cage SFP1 (connector P4, W4/W3 tx, V2/V1 rx)
##                    -> SLAVE lpGBT: uplink 1 only (its TX transmits the all-zero downlink word, as in upstream)
## The GT serial pins are NOT constrained by PACKAGE_PIN: a transceiver channel's LOC fixes its pads, and
## the swapped LOCs (constr/kcu105_gth_sites.xdc) are applied after this file is parsed, so PACKAGE_PIN lines
## here would be rejected (critical warning) against the IP's original sites.  The pads are:
##   SFP_TX_P/N[0] U4/U3   SFP_RX_P/N[0] T2/T1      (master, X0Y10)
##   SFP_TX_P/N[1] W4/W3   SFP_RX_P/N[1] V2/V1      (slave,  X0Y9)
## tcl/build_full.tcl checks these on the routed design (pin gate) before the bitstream is written.

## SFP CONTROL (same index convention): TX_DISABLE out, RX_LOS in (high = no light / no module).
## POLARITY: the board drives the module's TX_DISABLE through an NDS331N MOSFET (Q12/Q13), so the
## FPGA pin is INVERTED -- high = transmitter ON (schematic 0381556 rev 02, sheets 27/28; the RTL
## drives it high).  RX_LOS goes through a non-inverting level shifter: high = loss of signal.
set_property PACKAGE_PIN AL8 [get_ports {SFP_TX_DISABLE[0]}]
set_property PACKAGE_PIN D28 [get_ports {SFP_TX_DISABLE[1]}]
set_property PACKAGE_PIN K21 [get_ports {SFP_RX_LOS[0]}]
set_property PACKAGE_PIN AM9 [get_ports {SFP_RX_LOS[1]}]
set_property IOSTANDARD LVCMOS18 [get_ports {SFP_TX_DISABLE[*]}]
set_property IOSTANDARD LVCMOS18 [get_ports {SFP_RX_LOS[*]}]

##====================##
## SIGNALS FORWARDING ##
##====================##

## SMA output: the 40 MHz user clock as a differential pair (USER_SMA_GPIO_P/N = true P/N pair
## IO_L1P/L1N_T0L_65).  The MiniDAQ board drives its SMA pair as LVDS, but bank 65 here is a
## High-Range bank (DRC BIVB-1: "LVDS is not supported for banks of type High Range"), so the pair
## is driven as DIFF_SSTL18_I (true differential, 1.8 V swing) -- same OBUFDS, same pins.
set_property PACKAGE_PIN H27 [get_ports USER_SMA_GPIO_P]
set_property PACKAGE_PIN G27 [get_ports USER_SMA_GPIO_N]
set_property IOSTANDARD DIFF_SSTL18_I [get_ports USER_SMA_GPIO_P]
set_property IOSTANDARD DIFF_SSTL18_I [get_ports USER_SMA_GPIO_N]

## External trigger input (TRIGGER0): the KCU105's differential SMA input pair USER_SMA_CLOCK_P/N
## (J34/J35, D23/C23 = true P/N pair IO_L13P/L13N_T2L_67, clock-capable, bank 67 VCCO = VADJ_1V8).
## Pins confirmed against the board schematic (doc/kcu105_pin_audit.md).  The trigger may be moved to
## any other user SMA pin pair without affecting the design; USER_SMA_GPIO (J36/J37) already carries
## the 40 MHz clock output.  TRIGGER1 (unused upstream) is not brought out.
set_property PACKAGE_PIN D23 [get_ports TRIGGER0_P]
set_property PACKAGE_PIN C23 [get_ports TRIGGER0_N]
set_property IOSTANDARD LVDS [get_ports TRIGGER0_P]
set_property IOSTANDARD LVDS [get_ports TRIGGER0_N]
set_property DIFF_TERM_ADV TERM_100 [get_ports TRIGGER0_P]
set_property DIFF_TERM_ADV TERM_100 [get_ports TRIGGER0_N]

## mezz_TRST (JTAG TRST to the CSM mezzanine on the MiniDAQ board): no mezzanine on the KCU105, so
## the line is brought to GPIO_LED_7 -- lit while the register bank drives TRST high.
set_property PACKAGE_PIN P23 [get_ports mezz_TRST]
set_property IOSTANDARD LVCMOS18 [get_ports mezz_TRST]

##=================##
## ETHERNET: SGMII to the onboard Marvell 88E1111 PHY (PHY MDIO address 7)
## Pins/standards exactly as the Xilinx KCU105 board file's sgmii_lvds / sgmii_phyclk / mdio_mdc
## interfaces resolve them (the same values the Stage-3 design placed and routed with).  The
## PCS/PMA (gig_ethernet_pcs_pma_0) is the soft LVDS-SERDES variant on ordinary HP-bank pins --
## not a GTH lane.
##=================##
set_property PACKAGE_PIN N24 [get_ports SGMII_TX_P]
set_property PACKAGE_PIN M24 [get_ports SGMII_TX_N]
set_property PACKAGE_PIN P24 [get_ports SGMII_RX_P]
set_property PACKAGE_PIN P25 [get_ports SGMII_RX_N]
set_property IOSTANDARD DIFF_HSTL_I_18 [get_ports SGMII_TX_P]
set_property IOSTANDARD DIFF_HSTL_I_18 [get_ports SGMII_TX_N]
set_property IOSTANDARD DIFF_HSTL_I_18 [get_ports SGMII_RX_P]
set_property IOSTANDARD DIFF_HSTL_I_18 [get_ports SGMII_RX_N]

## 625 MHz reference clock FROM the PHY (board file "sgmii_phyclk")
set_property PACKAGE_PIN P26 [get_ports SGMIICLK_P]
set_property PACKAGE_PIN N26 [get_ports SGMIICLK_N]
set_property IOSTANDARD LVDS_25 [get_ports SGMIICLK_P]
set_property IOSTANDARD LVDS_25 [get_ports SGMIICLK_N]

## MDIO/MDC management bus and PHY reset
set_property PACKAGE_PIN L25 [get_ports mdc]
set_property PACKAGE_PIN H26 [get_ports mdio]
set_property PACKAGE_PIN J23 [get_ports phy_resetn]
set_property IOSTANDARD LVCMOS18 [get_ports mdc]
set_property IOSTANDARD LVCMOS18 [get_ports mdio]
set_property IOSTANDARD LVCMOS18 [get_ports phy_resetn]
