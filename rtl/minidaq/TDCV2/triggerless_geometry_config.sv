// Geometry/filter register endpoint in the 40 MHz control domain.
// Addresses 62..67; see firmware/triggerless_tube_filters.md for the wire format.
// The asynchronous lookup ports deliberately infer distributed RAM: both event
// builders see metadata for their CURRENT FWFT hit, without a delayed hit at a
// bank/window boundary. Configuration writes are forbidden while running.
module triggerless_geometry_config (
    input wire clk,
    input wire rst,
    input wire run_enable,
    input wire write_enable,
    input wire [7:0] address,
    input wire [7:0] selector,
    input wire [159:0] write_data,
    input wire [39:0] tdc_enable,
    input wire [39:0] tdc_chamber1,
    input wire [21:0] lookup_address,
    output wire [95:0] lookup_data,
    output reg ready,
    output wire busy,
    output reg [85:0] filter_settings,
    output reg [31:0] selected_mls,
    output reg [511:0] selected_layers,
    output reg [159:0] read_data
);
    localparam integer DEPTH = 40 * 32;
    localparam integer TUBES = 960;
    localparam [2:0] IDLE = 0, SCAN = 1, CHECK_ALIAS = 2, FINISH = 3;
    localparam [42:0] DEFAULT_FILTER = 43'h41; // total-tube cut enabled, N=4
    (* ram_style = "distributed" *) reg [47:0] mapping [0:DEPTH-1];
    reg [DEPTH-1:0] written;
    reg [10:0] index;
    reg [10:0] scan_index;
    reg [9:0] alias_index;
    reg [2:0] state;
    reg [7:0] error_code;
    reg [10:0] error_index;
    reg [31:0] generation;
    reg [TUBES-1:0] used_tubes;
    (* ram_style = "distributed" *) reg [21:0] tube_geometry [0:TUBES-1];
    reg [3:0] layer_ml [0:511];
    wire [47:0] entry = written[scan_index] ? mapping[scan_index] : 48'd0;
    wire [9:0] tube = entry[32:23];
    wire chamber = entry[1];
    wire [3:0] ml = entry[5:2];
    wire [7:0] layer = entry[13:6];
    wire [8:0] chamber_layer = {chamber, layer};
    wire [4:0] chamber_ml = {chamber, ml};
    assign busy = state != IDLE;

    genvar port;
    generate for (port = 0; port < 2; port = port + 1) begin: lookup
        wire [10:0] addr = lookup_address[port*11 +: 11];
        assign lookup_data[port*48 +: 48] =
            ready && addr < DEPTH && written[addr] ? mapping[addr] : 48'd0;
    end endgenerate

    // Stop-only writes to register 61 also invalidate the geometry; all table
    // entries must agree with the separately programmed physical TDC routing.
    wire routing_write = write_enable && address == 61 && !run_enable;
    wire legacy_threshold_write = write_enable && address == 38 && !run_enable;
    wire config_write = write_enable && address >= 62 && address <= 67;

    always @(posedge clk) begin
        if (rst) begin
            written <= '0;
            index <= 0;
            scan_index <= 0;
            alias_index <= 0;
            state <= IDLE;
            ready <= 0;
            error_code <= 0;
            error_index <= 0;
            generation <= 0;
            filter_settings <= {DEFAULT_FILTER, DEFAULT_FILTER};
            selected_mls <= 0;
            selected_layers <= 0;
            used_tubes <= '0;
        end else begin
            if (routing_write || legacy_threshold_write) begin
                ready <= 0;
                state <= IDLE;
                if (legacy_threshold_write) begin
                    // Compatibility address 38 now sets BOTH chamber total-
                    // tube thresholds; it never restores raw-hit acceptance.
                    filter_settings[13:4] <= write_data[9:0] > 256 ? 10'd256 : write_data[9:0];
                    filter_settings[56:47] <= write_data[9:0] > 256 ? 10'd256 : write_data[9:0];
                end
            end else if (config_write && !run_enable && !busy) begin
                case (address)
                    62: begin
                        if (write_data < DEPTH) index <= write_data[10:0];
                        else begin error_code <= 1; ready <= 0; end
                    end
                    63: begin
                        ready <= 0;
                        if (index[4:0] >= 24 || write_data[159:33] != 0 ||
                            (write_data[0] && write_data[32:23] >= TUBES)) begin
                            error_code <= 2;
                            error_index <= index;
                        end else begin
                            mapping[index] <= write_data[47:0];
                            written[index] <= 1'b1;
                        end
                    end
                    64: begin
                        ready <= 0;
                        if (write_data == 1) begin // BEGIN a fresh image
                            written <= '0;
                            selected_mls <= 0;
                            selected_layers <= 0;
                            error_code <= 0;
                            error_index <= 0;
                        end else if (write_data == 2 && error_code == 0) begin // APPLY
                            scan_index <= 0;
                            used_tubes <= '0;
                            selected_mls <= 0;
                            selected_layers <= 0;
                            state <= SCAN;
                        end else if (write_data != 2) error_code <= 3;
                    end
                    66, 67: begin
                        ready <= 0;
                        if (write_data[159:43] != 0 || write_data[13:4] > 256 ||
                            write_data[23:14] > 256 || write_data[33:24] > 256 ||
                            write_data[42:34] > 256) error_code <= 4;
                        else if (address == 66) filter_settings[42:0] <= write_data[42:0];
                        else filter_settings[85:43] <= write_data[42:0];
                    end
                    default: begin end // 65 is read-only masks/capability
                endcase
            end else if (state == SCAN) begin
                if (scan_index[4:0] < 24 && tdc_enable[scan_index >> 5]) begin
                    if (!written[scan_index]) begin
                        error_code <= 5; error_index <= scan_index; state <= FINISH;
                    end else if (entry[0]) begin
                        if (chamber != tdc_chamber1[scan_index >> 5]) begin
                            error_code <= 6; error_index <= scan_index; state <= FINISH;
                        end else if (selected_layers[chamber_layer] && layer_ml[chamber_layer] != ml) begin
                            error_code <= 7; error_index <= scan_index; state <= FINISH;
                        end else if (used_tubes[tube] && tube_geometry[tube] != entry[22:1]) begin
                            error_code <= 8; error_index <= scan_index; state <= FINISH;
                        end else begin
                            selected_mls[chamber_ml] <= 1;
                            selected_layers[chamber_layer] <= 1;
                            layer_ml[chamber_layer] <= ml;
                            used_tubes[tube] <= 1;
                            tube_geometry[tube] <= entry[22:1];
                            if (!used_tubes[tube]) begin
                                alias_index <= 0;
                                state <= CHECK_ALIAS;
                            end else if (scan_index == DEPTH-1) state <= FINISH;
                            else scan_index <= scan_index + 1'b1;
                        end
                    end else if (scan_index == DEPTH-1) state <= FINISH;
                    else scan_index <= scan_index + 1'b1;
                end else if (scan_index == DEPTH-1) state <= FINISH;
                else scan_index <= scan_index + 1'b1;
            end else if (state == CHECK_ALIAS) begin
                // Also reject two DIFFERENT IDs for the same geometry position.
                // This serial check keeps the datapath small; <=~24 ms for 960
                // unique tubes at 40 MHz, entirely while acquisition is stopped.
                if (alias_index != tube && used_tubes[alias_index] &&
                    tube_geometry[alias_index] == entry[22:1]) begin
                    error_code <= 9; error_index <= scan_index; state <= FINISH;
                end else if (alias_index == TUBES-1) begin
                    if (scan_index == DEPTH-1) state <= FINISH;
                    else begin scan_index <= scan_index + 1'b1; state <= SCAN; end
                end else alias_index <= alias_index + 1'b1;
            end else if (state == FINISH) begin
                ready <= error_code == 0 && (|selected_mls);
                if (error_code == 0 && (|selected_mls)) generation <= generation + 1'b1;
                else if (error_code == 0) error_code <= 10;
                state <= IDLE;
            end
        end
    end

    always @(*) begin
        read_data = 0;
        case (address)
            62: read_data[10:0] = index;
            63: read_data[47:0] = written[index] ? mapping[index] : 48'd0;
            64: begin
                read_data[0] = ready;
                read_data[1] = busy;
                read_data[15:8] = error_code;
                read_data[26:16] = error_index;
                read_data[63:32] = generation;
                read_data[95:64] = 32'h54464201; // 'TFB', protocol version 1
                read_data[106:96] = DEPTH;
                read_data[121:112] = TUBES;
            end
            65: begin
                // selector[2]: chamber; selector[1:0]: ML mask / layer halves
                case (selector[1:0])
                    0: read_data[15:0] = selected_mls[selector[2]*16 +: 16];
                    1: read_data[127:0] = selected_layers[selector[2]*256 +: 128];
                    2: read_data[127:0] = selected_layers[selector[2]*256+128 +: 128];
                    default: begin end
                endcase
            end
            66: read_data[42:0] = filter_settings[42:0];
            67: read_data[42:0] = filter_settings[85:43];
            default: begin end
        endcase
    end
endmodule
