// Request-driven, coherent diagnostics. All inputs and registers are clk_40.
// Counters survive run stop, FIFO clears and datapath resets. They reset only on
// register reset or a stop-only CLEAR command. Snapshot never clears live counts.
// Counter order, per chamber (64-bit modulo): processed, accepted, rejected,
// fail total / every ML / every layer / hit layers per ML, prebuffer discard,
// raw-limit discard, hit FIFO lost writes, watchdog aborts, unmapped popped hits,
// interrupted undecided candidates, committed raw-limit aborts.
module triggerless_diagnostics (
    input wire clk,
    input wire rst,
    input wire register_reset,
    input wire run_enable,
    input wire write_enable,
    input wire [7:0] address,
    input wire [7:0] selector,
    input wire [159:0] write_data,
    input wire [27:0] increments,
    input wire [11:0] fifo_lost_words,
    output reg [159:0] read_data
);
    localparam integer COUNTERS = 14;
    reg [63:0] live [0:27];
    reg [63:0] frozen [0:27];
    reg [63:0] clock_cycles, snapshot_cycles;
    reg [31:0] sequence_id, epoch;
    reg snapshot_valid, snapshot_running;
    wire take_snapshot = write_enable && address == 68 && write_data == 160'd1;
    wire clear_counts = register_reset ||
        (write_enable && address == 68 && write_data == 160'd2 && !run_enable);
    integer i;
    always @(posedge clk) begin
        if (rst) begin
            clock_cycles <= 0;
            snapshot_cycles <= 0;
            sequence_id <= 0;
            epoch <= 0;
            snapshot_valid <= 0;
            snapshot_running <= 0;
            for (i=0; i<28; i=i+1) begin live[i] <= 0; frozen[i] <= 0; end
        end else begin
            clock_cycles <= clock_cycles + 64'd1;
            if (clear_counts) begin
                epoch <= epoch + 32'd1;
                snapshot_valid <= 0;
                for (i=0; i<28; i=i+1) live[i] <= 0;
            end else begin
                for (i=0; i<28; i=i+1) begin
                    if (i % COUNTERS == 9)
                        live[i] <= live[i] + fifo_lost_words[(i/COUNTERS)*6 +: 6];
                    else
                        live[i] <= live[i] + increments[i];
                end
                if (take_snapshot) begin
                    for (i=0; i<28; i=i+1) frozen[i] <= live[i];
                    snapshot_cycles <= clock_cycles;
                    sequence_id <= sequence_id + 32'd1;
                    snapshot_valid <= 1;
                    snapshot_running <= run_enable;
                end
            end
        end
    end

    integer base;
    always @(*) begin
        read_data = 0;
        base = (selector[7] ? COUNTERS : 0) + selector[6:0]*2;
        case (address)
            8'd68: begin
                read_data[31:0] = 32'h44494101; // DIA protocol v1
                read_data[63:32] = sequence_id;
                read_data[95:64] = epoch;
                read_data[103:96] = COUNTERS;
                read_data[111:104] = 64;
                read_data[112] = snapshot_valid;
                read_data[113] = snapshot_running;
            end
            8'd69: if (snapshot_valid && selector[6:0] < COUNTERS/2) begin
                read_data[63:0] = frozen[base];
                read_data[127:64] = frozen[base+1];
                read_data[159:128] = sequence_id;
            end
            8'd70: if (snapshot_valid) begin
                read_data[63:0] = snapshot_cycles;
                read_data[95:64] = epoch;
                read_data[127:96] = sequence_id;
            end
            default: read_data = 0;
        endcase
    end
endmodule
