##===================================================================================================##
## KCU105 port of upstream constrains/kcu105_timing.xdc (gitlab.cern.ch/yuxiangg/phase2_MiniDAQ).      ##
## Only change vs upstream: the 320 MHz RGMII reference clock constraint (user_320_clk) is removed --  ##
## the KCU105 build has no such clock.  The 125 MHz USER_CLOCK is constrained by sys_clk's own IP      ##
## XDC (as upstream does for its 200 MHz clock).  Board-specific additions are in the section at the  ##
## end of this file.                                                                                   ##
##===================================================================================================##
##===================================================================================================##
##=========================================  CLOCKS  ================================================##
##===================================================================================================##

##==============##
## FABRIC CLOCK ##
##==============##
# create_clock -period 10.0000 -name mgt_freedrpclk [get_pins sys_clk_inst/mgt_freedrpclk]


##===========##
## MGT CLOCK ##
##===========##
create_clock -period 3.125 -name SMA_MGT_REFCLK [get_ports SMA_MGT_REFCLK_P]

##===========##
## User CDC  ##
##===========##
set_max_delay -datapath_only -from [get_pins -hierarchical -filter {NAME =~ *cdc_tx_inst/data_a_reg_reg*/C}] -to [get_pins -hierarchical -filter {NAME =~ *cdc_tx_inst/data_b_reg_reg*/D}] 6.250
set_max_delay -datapath_only -from [get_pins -hierarchical -filter {NAME =~ *cdc_tx_inst/reset_a_strobe_sync_reg/C}] -to [get_pins -hierarchical -filter {NAME =~ *cdc_tx_inst/reset_b_meta_reg/D}] 6.250
set_false_path -to [get_pins -hierarchical -filter {NAME =~ *cdc_tx_inst/advance_toggle_meta_reg/D}]
set_false_path -to [get_pins -hierarchical -filter {NAME =~ *cdc_tx_inst/retard_toggle_meta_reg/D}]

set_max_delay -datapath_only -from [get_pins -hierarchical -filter {NAME =~ *cdc_rx_inst/data_a_reg_reg*/C}] -to [get_pins -hierarchical -filter {NAME =~ *cdc_rx_inst/data_b_reg_reg*/D}] 6.250
set_max_delay -datapath_only -from [get_pins -hierarchical -filter {NAME =~ *cdc_rx_inst/strobe_b_toggle_reg/C}] -to [get_pins -hierarchical -filter {NAME =~ *cdc_rx_inst/strobe_b_toggle_meta_reg/D}] 6.250
set_false_path -to [get_pins -hierarchical -filter {NAME =~ *cdc_rx_inst/phase_calib_a_reg*/D}]
set_false_path -to [get_pins -hierarchical -filter {NAME =~ *cdc_rx_inst/phase_force_a_reg/D}]

##==================================##
## Timing exceptions for MGT design ##
##==================================##
# The generated clock mgt_freedrpclk is asynchronous to other clocks in design

set_clock_groups -quiet -asynchronous \
    -group [get_clocks -quiet mgt_freedrpclk_sys_clk]

# Reset synchronizer
# all replaced by XPM CDC
# set_false_path -to [get_pins lpgbtFpga_top_inst/mgt_inst/resetDoneSynch_rx/rst_in_*_reg/PRE]
# set_false_path -to [get_pins lpgbtFpga_top_inst/mgt_inst/*txAlignedSynch_tx/rst_in_*_reg/PRE]
# set_false_path -to [get_pins lpgbtFpga_top_inst/mgt_inst/*txPhaseAlignerResetSynch_sys/rst_in_*_reg/PRE]
# set_false_path -to [get_pins lpgbtFpga_top_inst/*txrdy_sync/rst_in_*_reg/PRE]


#set_false_path -to [get_pins -filter {REF_PIN_NAME =~ PRE} -of [get_cells -hier -regexp {.*\/*rst_sync.*}]]
#set_false_path -to [get_pins -hierarchical *rst_sync*/rst_in*reg*/PRE]

# replaced by XPM CDC
# set_false_path -to [get_pins tdc_decoder_top_inst/*rst_sync*/rst_in_*_reg/PRE]
# set_false_path -to [get_pins *rst_sync*/rst_in_*_reg/PRE]

# The trigger input is intentionally sampled as an asynchronous edge by the
# eight multi-phase T0 timestamp input registers. Cut only the paths into
# these first-stage samplers; keep all downstream retiming and timestamp
# processing paths timed.
set_false_path -quiet -to [get_pins -quiet -hierarchical -regexp \
    {.*t0_timestamp_inst/hit_in_pre_reg\[[0-7]\]/D$}]
