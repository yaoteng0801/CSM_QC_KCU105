##===================================================================================================##
## GTH CHANNEL SITES (KCU105): master lpGBT on SFP0, slave lpGBT on SFP1                              ##
##                                                                                                  ##
## The transceiver-wizard IP (ip_minidaq/xlx_ku_mgt_ip_10g24, generated unchanged from the upstream  ##
## .xci) places its channel 0 on GTHE3_CHANNEL_X0Y9 and channel 1 on X0Y10 (ascending site order).   ##
## On the KCU105 that is the wrong way round for this setup:                                         ##
##   * the MASTER lpGBT (uplink 0 + the single downlink 0, i.e. wizard channel 0) is on cage SFP0 =  ##
##     connector P5 = GTHE3_CHANNEL_X0Y10 (TX U4/U3, RX T2/T1)                                       ##
##   * the SLAVE lpGBT (uplink 1 only, wizard channel 1) is on cage SFP1 = connector P4 =            ##
##     GTHE3_CHANNEL_X0Y9 (TX W4/W3, RX V2/V1)                                                       ##
## The two channels are interchangeable inside quad 226 (same QPLL, same reference clock), so the    ##
## swap is a constraint only: rtl/minidaq and the IP configuration stay bit-exact with upstream.     ##
## This file is read LAST (PROCESSING_ORDER LATE, tcl/create_project.tcl) so it overrides the IP's   ##
## own LOCs; tcl/build_full.tcl checks the result before implementation.                             ##
##===================================================================================================##
## A direct swap fails (each LOC is refused while the other channel still occupies the site), so channel 0
## is parked on the unused X0Y11 first.  The sequence is idempotent.
set_property LOC GTHE3_CHANNEL_X0Y11 [get_cells -hierarchical -filter {NAME =~ *gen_channel_container[2].*gen_gthe3_channel_inst[0].GTHE3_CHANNEL_PRIM_INST}]
set_property LOC GTHE3_CHANNEL_X0Y9  [get_cells -hierarchical -filter {NAME =~ *gen_channel_container[2].*gen_gthe3_channel_inst[1].GTHE3_CHANNEL_PRIM_INST}]
set_property LOC GTHE3_CHANNEL_X0Y10 [get_cells -hierarchical -filter {NAME =~ *gen_channel_container[2].*gen_gthe3_channel_inst[0].GTHE3_CHANNEL_PRIM_INST}]
