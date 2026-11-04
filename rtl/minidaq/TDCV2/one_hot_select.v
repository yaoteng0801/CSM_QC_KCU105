/* 
       _________   ________     ________       
      / U OF M  \ | LSA    \   / Physics\
      \__ATLAS__/ |   ___   | |   ______/
         |   |    |  |   \  | |  |
         |   |    |  |___/  | |  \______     
         |   |    |         | |         \
         \___/    |________/   \________/
*/  
//  File Name  : one_hot_select.v
//  Author     : Yu Liang
//  Revision   : 
//               First created on June 30st, 2017
//  Note       : 
// 

module one_hot_select #(
	parameter DATA_WIDTH=32,
	parameter DATA_DEPTH=8
	)
(
    input  [DATA_DEPTH-1:0] one_hot_code,
    input  [(DATA_WIDTH*DATA_DEPTH-1):0] data_in,
    output [DATA_WIDTH-1:0] data_out
    );

	wire [DATA_WIDTH-1:0] data_out_inner [DATA_DEPTH-1:0];
	
	generate	
	   genvar i;	       
		for (i = 0; i < DATA_DEPTH; i = i + 1)
		begin:identifier0
			assign data_out_inner[i]  = data_in[(i+1)*DATA_WIDTH-1:i*DATA_WIDTH] & {DATA_WIDTH{one_hot_code[i]}};
		end
	endgenerate
	
	wire [DATA_DEPTH-1:0] data_out_inner_interest [DATA_WIDTH-1:0];
	generate	
       genvar k,j;           
        for (k = 0; k < DATA_WIDTH; k = k + 1)
        begin:identifier1            
            for(j = 0; j < DATA_DEPTH; j = j + 1)
            begin:identifier12
                assign data_out_inner_interest[k][j]  = data_out_inner[j][k];
            end
            assign data_out[k]=|(data_out_inner_interest[k]);
        end
    endgenerate


endmodule