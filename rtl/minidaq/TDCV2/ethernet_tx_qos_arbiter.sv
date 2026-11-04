// Frame-locked hit/control/monitor AXI-Stream scheduler.
//
// Hierarchy and interfaces:
//
//   Parent: minidaq_ethernet_subsystem.tx_qos
//   Children: none; this is the final application TX scheduler
//
//   detector hit-frame FIFO --------------------+
//   combined programming/generic control -------+--> this scheduler --> TEMAC
//   monitoring response stream -----------------+
//
// All streams and occupancy information are synchronous to the 125 MHz TEMAC
// TX clock. This is the only module that decides between detector data and the
// two control-plane traffic classes.
//
// High hit-FIFO occupancy always selects a waiting hit frame.  Below the high
// water mark, control replies may run before hits.  Monitoring is allowed only
// below the low water mark and at most once per MONITOR_MIN_GAP_CYCLES.  Once
// a source starts, it owns TEMAC TX through an accepted TLAST, so traffic
// classes can never be interleaved within one Ethernet frame.

`timescale 1ns / 1ps

module ethernet_tx_qos_arbiter #(
    parameter integer HIT_COUNT_WIDTH = 16,
    parameter integer HIT_HIGH_WATER = 1024,
    parameter integer HIT_LOW_WATER = 256,
    parameter integer MONITOR_MIN_GAP_CYCLES = 125000
) (
    input  wire clk,
    input  wire rst,
    input  wire [HIT_COUNT_WIDTH-1:0] hit_fifo_occupancy,

    input  wire [7:0] hit_tdata,
    input  wire hit_tvalid,
    output reg  hit_tready,
    input  wire hit_tlast,

    input  wire [7:0] control_tdata,
    input  wire control_tvalid,
    output reg  control_tready,
    input  wire control_tlast,

    input  wire [7:0] monitor_tdata,
    input  wire monitor_tvalid,
    output reg  monitor_tready,
    input  wire monitor_tlast,

    output reg [7:0] tx_tdata,
    output reg tx_tvalid,
    input  wire tx_tready,
    output reg tx_tlast
);

    localparam [1:0] IDLE = 2'd0;
    localparam [1:0] HIT = 2'd1;
    localparam [1:0] CONTROL = 2'd2;
    localparam [1:0] MONITOR = 2'd3;
    localparam integer GAP_WIDTH = $clog2(MONITOR_MIN_GAP_CYCLES + 1);

    reg [1:0] grant = IDLE;
    reg [GAP_WIDTH-1:0] monitor_gap = {GAP_WIDTH{1'b0}};
    wire hit_urgent = hit_fifo_occupancy >= HIT_HIGH_WATER;
    wire monitor_safe = hit_fifo_occupancy <= HIT_LOW_WATER
                      && monitor_gap == {GAP_WIDTH{1'b0}};

    reg [1:0] idle_choice;
    always @(*) begin
        if (hit_tvalid && hit_urgent)
            idle_choice = HIT;
        else if (control_tvalid)
            idle_choice = CONTROL;
        else if (monitor_tvalid && monitor_safe)
            idle_choice = MONITOR;
        else if (hit_tvalid)
            idle_choice = HIT;
        else
            idle_choice = IDLE;
    end

    always @(*) begin
        tx_tdata = 8'b0;
        tx_tvalid = 1'b0;
        tx_tlast = 1'b0;
        hit_tready = 1'b0;
        control_tready = 1'b0;
        monitor_tready = 1'b0;
        case (grant == IDLE ? idle_choice : grant)
            HIT: begin
                tx_tdata = hit_tdata; tx_tvalid = hit_tvalid;
                tx_tlast = hit_tlast; hit_tready = tx_tready;
            end
            CONTROL: begin
                tx_tdata = control_tdata; tx_tvalid = control_tvalid;
                tx_tlast = control_tlast; control_tready = tx_tready;
            end
            MONITOR: begin
                tx_tdata = monitor_tdata; tx_tvalid = monitor_tvalid;
                tx_tlast = monitor_tlast; monitor_tready = tx_tready;
            end
            default: begin end
        endcase
    end

    wire transfer = tx_tvalid && tx_tready;
    wire final_transfer = transfer && tx_tlast;
    always @(posedge clk) begin
        if (rst) begin
            grant <= IDLE;
            monitor_gap <= {GAP_WIDTH{1'b0}};
        end else begin
            if (monitor_gap != {GAP_WIDTH{1'b0}})
                monitor_gap <= monitor_gap - 1'b1;
            if (grant == IDLE) begin
                if (idle_choice != IDLE && !(transfer && tx_tlast))
                    grant <= idle_choice;
                if (idle_choice == MONITOR && final_transfer)
                    monitor_gap <= MONITOR_MIN_GAP_CYCLES;
            end else if (final_transfer) begin
                if (grant == MONITOR)
                    monitor_gap <= MONITOR_MIN_GAP_CYCLES;
                grant <= IDLE;
            end
        end
    end

endmodule
