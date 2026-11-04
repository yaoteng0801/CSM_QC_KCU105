####################################################################################################
# create_project.tcl
#
# Creates (or recreates) the Vivado project for the KCU105 port of the MiniDAQ firmware
# (UPLINKCOUNT = 2, DOWNLINKCOUNT = 1; see rtl/board/xcku040_10g24_top.sv).
# Run from the repo root:
#   vivado -mode batch -source tcl/create_project.tcl
#
# Source layout (the checked-in source of truth; vivado_proj/ is gitignored and disposable):
#   rtl/minidaq/   bit-exact copy of the authoritative upstream MiniDAQ sources
#                  (gitlab.cern.ch/yuxiangg/phase2_MiniDAQ @ 124dc6d); never edited by hand --
#                  tools/check_upstream_sync.py verifies it against an upstream checkout
#   rtl/board/     KCU105 board layer (top level, SGMII Ethernet MAC wrapper, PHY init FSM)
#   ip_minidaq/    Vivado IP (.xci), created by tcl/generate_minidaq_ip.tcl
#   constr/        KCU105 constraints
# Nothing else under rtl/ or ip/ is part of this build.
####################################################################################################

set proj_name   "kcu105_minidaq"
set part_name   "xcku040-ffva1156-2-e"
set repo_root   [file normalize [file dirname [info script]]/..]
set proj_dir    "$repo_root/vivado_proj"

create_project $proj_name $proj_dir -part $part_name -force

set_property target_language Verilog [current_project]
set_property simulator_language Mixed [current_project]

# xpm_cdc_* / xpm_fifo_async are instantiated throughout the MiniDAQ sources.
set_property XPM_LIBRARIES {XPM_CDC XPM_FIFO XPM_MEMORY} [current_project]

# ---------------------------------------------------------------------------------------------- #
# RTL sources (Verilog / SystemVerilog / VHDL), recursively
# ---------------------------------------------------------------------------------------------- #
proc rglob {dir pats} {
    set found {}
    foreach f [glob -nocomplain -directory $dir -types f -- {*}$pats] { lappend found $f }
    foreach d [glob -nocomplain -directory $dir -types d -- *] { lappend found {*}[rglob $d $pats] }
    return $found
}

# Upstream files that are RGMII/RGMII-wrapper specific.  rtl/board/ provides the SGMII replacements (tri_mode_ethernet_mac_0_example_design.v and the
# fifo-block/AXI-Lite pieces folded into it).
set excluded_names {
    tri_mode_ethernet_mac_0_axi_lite_sm.v
    tri_mode_ethernet_mac_0_fifo_block.v
}

set hdl {}
foreach f [concat [rglob "$repo_root/rtl/minidaq" {*.v *.sv *.vhd}] \
                  [rglob "$repo_root/rtl/board"   {*.v *.sv *.vhd}]] {
    if {[lsearch -exact $excluded_names [file tail $f]] < 0} { lappend hdl $f }
}
add_files -norecurse $hdl

# ---------------------------------------------------------------------------------------------- #
# IP (.xci) -- present once tcl/generate_minidaq_ip.tcl has run
# ---------------------------------------------------------------------------------------------- #
foreach xci [glob -nocomplain -directory "$repo_root/ip_minidaq" -- */*.xci] {
    add_files -norecurse $xci
}

# ---------------------------------------------------------------------------------------------- #
# Constraints
# ---------------------------------------------------------------------------------------------- #
add_files -fileset constrs_1 -norecurse [glob -nocomplain -directory "$repo_root/constr" -- *.xdc]
# The GTH site swap (master lpGBT on SFP0) must override the transceiver IP's own LOC constraints.
set_property PROCESSING_ORDER LATE [get_files -of_objects [get_filesets constrs_1] kcu105_gth_sites.xdc]

set_property top xcku040_10g24_top [current_fileset]
update_compile_order -fileset sources_1

puts "Project '$proj_name' created for part $part_name at $proj_dir ([llength $hdl] HDL files)"
