####################################################################################################
# temac_support_files.tcl
#
# The Ethernet FIFO and synchroniser modules used by rtl/board/tri_mode_ethernet_mac_0_example_design.v
# come from the Tri-Mode Ethernet MAC example design, which is AMD's and is not redistributed in this
# repo.  This takes them from Vivado's own example design for the generated core, into
# rtl/minidaq/tri_mode_ethernet_mac/.  Nothing happens if they are already there.
#
# Sourced by tcl/build_full.tcl after tcl/generate_minidaq_ip.tcl, with that project open.
####################################################################################################

set temac_dir  "$repo_root/rtl/minidaq/tri_mode_ethernet_mac"
set temac_missing {}
foreach suffix {bram_tdp reset_sync rx_client_fifo sync_block ten_100_1g_eth_fifo tx_client_fifo} {
    set name "tri_mode_ethernet_mac_0_$suffix.v"
    if {![file exists "$temac_dir/$name"]} { lappend temac_missing $name }
}

if {[llength $temac_missing] > 0} {
    set temac_main [current_project]
    set temac_ex   "$repo_root/vivado_proj/temac_ex"
    file delete -force $temac_ex
    # The example design's own final step can fail after its sources are written, so the check that
    # counts is the one on the copied files below.
    if {[catch {open_example_project -force -in_process -dir $temac_ex [get_ips tri_mode_ethernet_mac_0]} err]} {
        puts "INFO: example design step reported: $err"
    }
    if {[current_project] ne $temac_main} { close_project }
    current_project $temac_main

    file mkdir $temac_dir
    foreach name $temac_missing {
        set source_file "$temac_ex/tri_mode_ethernet_mac_0_ex/imports/$name"
        if {![file exists $source_file]} { error "TEMAC example design did not produce $name" }
        file copy -force $source_file "$temac_dir/$name"
        add_files -norecurse "$temac_dir/$name"
    }
    update_compile_order -fileset sources_1
    puts "TEMAC support files generated: $temac_missing"
}
