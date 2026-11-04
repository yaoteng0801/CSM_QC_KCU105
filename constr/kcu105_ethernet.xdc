##===================================================================================================##
## Ethernet MAC wrapper (rtl/board/tri_mode_ethernet_mac_0_example_design.v) timing exceptions.        ##
##                                                                                                     ##
## The upstream MiniDAQ project keeps these in its RGMII-specific example-design XDC                   ##
## (constrains/tri_mode_ethernet_mac_0_example_design.xdc), which is not used here (its pin and RGMII  ##
## placement constraints are for the MiniDAQ board).  The clock-domain-crossing exceptions in it are   ##
## board independent and apply unchanged to the SGMII wrapper -- same reset_sync / client-FIFO         ##
## cells -- so they are carried over below.  The PCS/PMA and TEMAC IPs bring their own scoped XDC for  ##
## their internals (clk625/clk312/clk125 groups, SERDES, MDIO).                                         ##
##===================================================================================================##

## --- carried over from the Xilinx TEMAC example-design XDC (unchanged) ---------------------------
# phy_resetn is an asynchronous output; the PHY reset also feeds the AXI-Lite reset synchronizer
set_false_path -from [get_cells -hier -filter {name =~ *phy_resetn_int_reg}] -to [get_ports phy_resetn]
set_false_path -from [get_cells -hier -filter {name =~ *phy_resetn_int_reg}] -to [get_cells -hier -filter {name =~ *axi_lite_reset_gen/reset_sync*}]

# reset synchronizers: asynchronous assertion into the PRE pins is by design
set_false_path -to [get_pins -filter {REF_PIN_NAME =~ PRE} -of [get_cells -hier -regexp {.*\/reset_sync.*}]]

# user-side TX client FIFO (tri_mode_ethernet_mac_0_tx_client_fifo): gray/toggle crossings
set_max_delay -datapath_only -from [get_cells -hier -filter {name =~ *tx_fifo_i/rd_addr_txfer_reg[*]}] -to [get_cells -hier -filter {name =~ *fifo*wr_rd_addr_reg[*]}] 3.200
set_max_delay -datapath_only -from [get_cells -hier -filter {name =~ *tx_fifo_i/wr_frame_in_fifo_reg}] -to [get_cells -hier -filter {name =~ *tx_fifo_i/resync_wr_frame_in_fifo/data_sync_reg0}] 3.200
set_max_delay -datapath_only -from [get_cells -hier -filter {name =~ *tx_fifo_i/wr_frames_in_fifo_reg}] -to [get_cells -hier -filter {name =~ *tx_fifo_i/resync_wr_frames_in_fifo/data_sync_reg0}] 3.200
set_max_delay -datapath_only -from [get_cells -hier -filter {name =~ *tx_fifo_i/frame_in_fifo_valid_tog_reg}] -to [get_cells -hier -filter {name =~ *tx_fifo_i/resync_fif_valid_tog/data_sync_reg0}] 3.200
set_max_delay -datapath_only -from [get_cells -hier -filter {name =~ *tx_fifo_i/rd_txfer_tog_reg}] -to [get_cells -hier -filter {name =~ *tx_fifo_i/resync_rd_txfer_tog/data_sync_reg0}] 3.200
set_max_delay -datapath_only -from [get_cells -hier -filter {name =~ *tx_fifo_i/rd_tran_frame_tog_reg}] -to [get_cells -hier -filter {name =~ *tx_fifo_i/resync_rd_tran_frame_tog/data_sync_reg0}] 3.200

## --- KCU105 addition ------------------------------------------------------------------------------
# Reset crossings into the Ethernet subsystem's xpm_fifo_async reset FSMs.  Upstream's RTL (kept
# bit-exact in rtl/minidaq) hands one reset to FIFOs whose write clock is in the other domain:
#   - ethernet_mac/gtx_resetn (125 MHz; = rx_axis_fifo_aresetn, wired as tx_reset(~rx_resetn) in
#     ethernet_control_top) -> the two *result* FIFOs, write side = 40 MHz control clock
#   - power_on_reset_40 (40 MHz; = control_reset) -> the *request* FIFOs, write side = 125 MHz RX clock
# Each is an unsynchronised crossing of a quasi-static reset level (asserted for many cycles, only at
# power-up and around Ethernet link resets), so the ~1 ns inter-clock edge requirement Vivado derives
# for unrelated 40/125 MHz clocks is meaningless; bound the data path to 8 ns instead of cutting it.
set_max_delay -datapath_only     -from [get_cells -hier -filter {NAME =~ power_on_reset_shift_reg* || NAME =~ ethernet_mac/gtx_resetn_reg*}]     -to   [get_pins  -hier -filter {NAME =~ ethernet_subsystem/*xpm_fifo_rst_inst/*/D}] 8.000
