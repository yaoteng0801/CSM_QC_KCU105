// Per-candidate, per-chamber distinct-tube accounting. No raw hits are removed.
// Geometry entry: valid[0], chamber[1], ML[5:2], layer[13:6], column[22:14],
// canonical tube ID[32:23]. All aliases of one tube must use the same ID.
module tube_event_filter #(
    parameter integer CHAMBER_ID = 0,
    parameter integer TUBE_COUNT = 960
) (
    input wire clk,
    input wire clear,
    input wire hit_accept,
    input wire geometry_ready,
    input wire [47:0] geometry,
    // enable[3:0], min total[13:4], min/ML[23:14], min/layer[33:24],
    // min hit layers/ML[42:34]. Enabled requirements are ANDed.
    input wire [42:0] settings,
    input wire [15:0] selected_mls,
    input wire [255:0] selected_layers,
    output wire pass,
    output reg [9:0] tube_count,
    output wire new_tube,
    output wire [3:0] failed_filters
);
    reg [TUBE_COUNT-1:0] seen_tubes;
    reg [255:0] seen_layers;
    reg [9:0] ml_tubes [0:15];
    reg [9:0] layer_tubes [0:255];
    reg [8:0] ml_hit_layers [0:15];
    wire [9:0] tube = geometry[32:23];
    wire [3:0] ml = geometry[5:2];
    wire [7:0] layer = geometry[13:6];
    wire mapped = geometry_ready && geometry[0] &&
                  geometry[1] == (CHAMBER_ID != 0) && tube < TUBE_COUNT;
    assign new_tube = hit_accept && mapped && !seen_tubes[tube];

    integer i;
    always @(posedge clk) begin
        if (clear) begin
            seen_tubes <= '0;
            seen_layers <= '0;
            tube_count <= 10'd0;
            for (i = 0; i < 16; i = i + 1) begin
                ml_tubes[i] <= 10'd0;
                ml_hit_layers[i] <= 9'd0;
            end
            for (i = 0; i < 256; i = i + 1)
                layer_tubes[i] <= 10'd0;
        end else if (new_tube) begin
            seen_tubes[tube] <= 1'b1;
            tube_count <= tube_count + 10'd1;
            ml_tubes[ml] <= ml_tubes[ml] + 10'd1;
            layer_tubes[layer] <= layer_tubes[layer] + 10'd1;
            if (!seen_layers[layer]) begin
                seen_layers[layer] <= 1'b1;
                ml_hit_layers[ml] <= ml_hit_layers[ml] + 9'd1;
            end
        end
    end

    reg [15:0] ml_tubes_ok;
    reg [15:0] ml_layers_ok;
    reg [255:0] layers_ok;
    integer j;
    always @(*) begin
        for (j = 0; j < 16; j = j + 1) begin
            ml_tubes_ok[j] = !selected_mls[j] || ml_tubes[j] >= settings[23:14];
            ml_layers_ok[j] = !selected_mls[j] || ml_hit_layers[j] >= settings[42:34];
        end
        for (j = 0; j < 256; j = j + 1)
            layers_ok[j] = !selected_layers[j] || layer_tubes[j] >= settings[33:24];
    end
    // Even with all cuts disabled, require a nonempty mapped-tube event.
    // An enabled "every" cut with an empty selected set cannot pass.
    assign failed_filters[0] = settings[0] && tube_count < settings[13:4];
    assign failed_filters[1] = settings[1] && !((|selected_mls) && (&ml_tubes_ok));
    assign failed_filters[2] = settings[2] && !((|selected_layers) && (&layers_ok));
    assign failed_filters[3] = settings[3] && !((|selected_mls) && (&ml_layers_ok));
    assign pass = geometry_ready && tube_count != 0 && !(|failed_filters);
endmodule
