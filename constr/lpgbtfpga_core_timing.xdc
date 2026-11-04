##====================##
## TIMING CONSTRAINTS ##
##====================##

# Multicycle constraints: ease the timing constraints

# Uplink constraints: Values depend on the c_multicyleDelay. Shall be the same one for setup time and -1 for the hold time
set_multicycle_path -setup -from [get_pins {lpgbtFpga_top_inst/*uplink_inst/frame_pipelined_s_reg[*]/C}] 3
set_multicycle_path -hold -from [get_pins {lpgbtFpga_top_inst/*uplink_inst/frame_pipelined_s_reg[*]/C}] 2
set_multicycle_path -setup -from [get_pins -hierarchical -filter {NAME =~ lpgbtFpga_top_inst/*uplink_inst/*descrambledData_reg[*]/C}] 3
set_multicycle_path -hold -from [get_pins -hierarchical -filter {NAME =~ lpgbtFpga_top_inst/*uplink_inst/*descrambledData_reg[*]/C}] 2

# All Ethernet-configurable uplink controls are changed only while the
# corresponding uplink is held in reset. Cut only the paths launched by the
# final RX-clock synchronizer stages; the CDC paths into the synchronizer
# remain constrained by the XPM CDC constraints.
set_false_path -quiet -from [get_cells -quiet -hierarchical -regexp \
    {.*uplink\[[0-9]+\]\.uplink_control_sync/syncstages_ff_reg\[1\]\[[0-8]\]$}]

# Downlink constraints: Values depend on the c_multicyleDelay. Shall be the same one for setup time and -1 for the hold time
set_multicycle_path -setup -to [get_pins -hierarchical -filter {NAME =~ lpgbtFpga_top_inst/*downlink_inst/lpgbtfpga_scrambler_inst/scrambledData*/D}] 3
set_multicycle_path -hold -to [get_pins -hierarchical -filter {NAME =~ lpgbtFpga_top_inst/*downlink_inst/lpgbtfpga_scrambler_inst/scrambledData*/D}] 2
