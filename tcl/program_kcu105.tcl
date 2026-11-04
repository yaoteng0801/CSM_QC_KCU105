####################################################################################################
# program_kcu105.tcl
#
# Loads the prebuilt bitstream into a KCU105 over JTAG.  Run from the repo root:
#   vivado -mode batch -nojournal -nolog -source tcl/program_kcu105.tcl
# To find the board without programming it, add:  -tclargs check
####################################################################################################

set repo_root [file normalize [file dirname [info script]]/..]
set bit "$repo_root/bitstreams/kcu105_minidaq.bit"
set ltx "$repo_root/bitstreams/kcu105_minidaq.ltx"

open_hw_manager
connect_hw_server
open_hw_target
set device [lindex [get_hw_devices xcku040*] 0]
if {$device eq ""} { error "No xcku040 found on the JTAG chain: [get_hw_devices]" }
current_hw_device $device
puts "Found $device"
if {[lindex $argv 0] eq "check"} { return }

set_property PROGRAM.FILE $bit $device
set_property PROBES.FILE  $ltx $device
program_hw_devices $device
refresh_hw_device $device
puts "Programmed $device with $bit"
