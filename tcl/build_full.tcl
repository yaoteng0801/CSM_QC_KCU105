####################################################################################################
# build_full.tcl
#
# Full, reproducible build of the KCU105 port of the MiniDAQ firmware (UPLINKCOUNT 2 / DOWNLINKCOUNT 1:
# lpGBT-FPGA + GBT-SC SCA/IC + TDC/DAQ + Ethernet control plane over SGMII), from a clean checkout to
# a bitstream: project -> IP -> synth -> impl -> reports -> bitstream. Every step the design depends
# on is in this one script (or the tcl/ scripts it sources), so nothing lives only in a scratch file.
#
# Run from the repo root:
#   mkdir build
#   vivado -mode batch -nojournal -log build/vivado_build.log -source tcl/build_full.tcl
#
# Outputs (build/, gitignored):
#   kcu105_minidaq.bit / kcu105_minidaq.ltx   bitstream + ILA debug-probe file for Hardware Manager
#   post_synth.dcp / post_route.dcp       checkpoints
#   *.rpt                                 timing summary, DRC, methodology, CDC, clock
#                                         interaction, utilization, IP status
#   build_info.txt                        git commit + dirty flag, and the final timing numbers
#
# The build stops before write_bitstream if routed timing is not met (WNS or WHS < 0): a
# bitstream that fails timing is not a trustworthy bring-up artifact.
#
# Implementation directives: place_design Explore + phys_opt_design AggressiveExplore +
# route_design Explore (carried over from the superseded UART/VIO build, where the defaults left
# failing endpoints in the 320 MHz uplink gearbox logic -- a routing-congestion effect). Revisit
# if timing closes easily with defaults on this design.
####################################################################################################

set repo_root [file normalize [file dirname [info script]]/..]
set out_dir   "$repo_root/build"
file mkdir $out_dir

# ---------------------------------------------------------------------------------------------- #
# 1. Project + IP. tcl/generate_minidaq_ip.tcl is idempotent: it creates each IP if missing,
#    re-applies its configuration, generates output products and runs the out-of-context
#    synthesis the project-mode synth_design below needs (first run ~10 min, then seconds).
# ---------------------------------------------------------------------------------------------- #
source "$repo_root/tcl/create_project.tcl"
source "$repo_root/tcl/generate_minidaq_ip.tcl"
source "$repo_root/tcl/temac_support_files.tcl"

report_ip_status -file "$out_dir/ip_status.rpt"

# ---------------------------------------------------------------------------------------------- #
# 2. Synthesis
# ---------------------------------------------------------------------------------------------- #
update_compile_order -fileset sources_1
synth_design -top [get_property top [current_fileset]] -part [get_property part [current_project]]

# GTH site swap: master lpGBT (wizard channel 0) on SFP0 = X0Y10, slave (channel 1) on SFP1 = X0Y9.
# In this in-session synth_design flow the transceiver IP's own LOC constraints are applied after the
# user XDC and win (seen: channel 0 stayed on X0Y9), so the same file is applied again here, on the
# synthesized netlist.  Then gate on the result: fail now, not after place+route.
read_xdc -unmanaged "$repo_root/constr/kcu105_gth_sites.xdc"
foreach {chan site} {0 GTHE3_CHANNEL_X0Y10 1 GTHE3_CHANNEL_X0Y9} {
    set pat [string map [list @CH@ $chan] {NAME =~ *gen_channel_container[2].*gen_gthe3_channel_inst[@CH@].GTHE3_CHANNEL_PRIM_INST}]
    set cell [get_cells -hierarchical -filter $pat]
    set loc  [get_property LOC $cell]
    puts "GTH-SITE-GATE: channel $chan LOC = $loc (expected $site)"
    if {$loc ne $site} { error "GTH site gate failed: wizard channel $chan is on '$loc', expected $site" }
}
write_checkpoint -force "$out_dir/post_synth.dcp"
report_utilization -file "$out_dir/post_synth_utilization.rpt"

# ---------------------------------------------------------------------------------------------- #
# 3. Implementation
# ---------------------------------------------------------------------------------------------- #
opt_design
place_design    -directive Explore
phys_opt_design -directive AggressiveExplore
route_design    -directive Explore
write_checkpoint -force "$out_dir/post_route.dcp"

# ---------------------------------------------------------------------------------------------- #
# 4. Reports
# ---------------------------------------------------------------------------------------------- #
report_timing_summary -max_paths 20 -report_unconstrained -warn_on_violation \
                      -file "$out_dir/timing_summary.rpt"
report_clock_interaction -delay_type min_max -file "$out_dir/clock_interaction.rpt"
report_cdc              -details             -file "$out_dir/cdc.rpt"
report_drc                                   -file "$out_dir/drc.rpt"
report_methodology                           -file "$out_dir/methodology.rpt"
report_utilization                           -file "$out_dir/utilization.rpt"
report_io                                    -file "$out_dir/io.rpt"

set wns [get_property SLACK [get_timing_paths -max_paths 1 -nworst 1 -setup]]
set whs [get_property SLACK [get_timing_paths -max_paths 1 -nworst 1 -hold]]

set git_rev   "unknown"
set git_dirty "unknown"
catch {set git_rev [string trim [exec git -C $repo_root rev-parse HEAD]]}
catch {set git_dirty [expr {[string trim [exec git -C $repo_root status --porcelain]] ne "" ? "yes" : "no"}]}

set fh [open "$out_dir/build_info.txt" w]
puts $fh "git_rev   $git_rev"
puts $fh "git_dirty $git_dirty"
puts $fh "part      [get_property part [current_project]]"
puts $fh "WNS       $wns"
puts $fh "WHS       $whs"
close $fh

puts "BUILD TIMING: WNS=$wns ns, WHS=$whs ns (git $git_rev, dirty=$git_dirty)"

if {$wns eq "" || $whs eq "" || $wns < 0 || $whs < 0} {
    error "Routed timing not met (WNS=$wns, WHS=$whs) -- see $out_dir/timing_summary.rpt. No bitstream written."
}

# ---------------------------------------------------------------------------------------------- #
# Pin gate: every top-level port must sit on the pad the board schematic requires
# (doc/kcu105_pin_audit.md).  The GT serial pads follow the channel LOCs, so they are checked here.
# ---------------------------------------------------------------------------------------------- #
set expected_pins {
    USER_CLOCK_P G10  USER_CLOCK_N F10  SMA_MGT_REFCLK_P V6  SMA_MGT_REFCLK_N V5
    SFP_TX_P[0] U4  SFP_TX_N[0] U3  SFP_RX_P[0] T2  SFP_RX_N[0] T1
    SFP_TX_P[1] W4  SFP_TX_N[1] W3  SFP_RX_P[1] V2  SFP_RX_N[1] V1
    SFP_TX_DISABLE[0] AL8  SFP_TX_DISABLE[1] D28  SFP_RX_LOS[0] K21  SFP_RX_LOS[1] AM9
    USER_SMA_GPIO_P H27  USER_SMA_GPIO_N G27  TRIGGER0_P D23  TRIGGER0_N C23  mezz_TRST P23
    SGMII_TX_P N24  SGMII_TX_N M24  SGMII_RX_P P24  SGMII_RX_N P25  SGMIICLK_P P26  SGMIICLK_N N26
    mdc L25  mdio H26  phy_resetn J23
}
set pin_errors 0
foreach {port want} $expected_pins {
    set got [get_property PACKAGE_PIN [get_ports -quiet [list $port]]]
    if {$got ne $want} { puts "PIN-GATE ERROR: $port is on '$got', schematic requires $want"; incr pin_errors }     else               { puts "PIN-GATE ok: $port = $got" }
}
if {$pin_errors != 0} { error "Pin gate failed: $pin_errors port(s) not on the schematic pin. No bitstream written." }

# ---------------------------------------------------------------------------------------------- #
# 5. Bitstream + debug probes
# ---------------------------------------------------------------------------------------------- #
write_bitstream    -force "$out_dir/kcu105_minidaq.bit"
write_debug_probes -force "$out_dir/kcu105_minidaq.ltx"

puts "BUILD DONE: $out_dir/kcu105_minidaq.bit"
