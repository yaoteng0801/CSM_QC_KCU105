----------------------------------------------------------------------------------
-- Company: Universtiy of Michigan
-- Engineer: Xueye
-- 
-- Create Date: 04/17/2020 11:49:27 AM
-- Design Name: 
-- Module Name: t0_timestamp - Behavioral
-- Project Name: 
-- Target Devices: 
-- Tool Versions: 
-- Description: 
-- 
-- Dependencies: 
-- 
-- Revision:
-- Revision 0.01 - File Created
-- Additional Comments:
-- resolution 390ps
-- coarse clock 320MHz
----------------------------------------------------------------------------------


library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;
use IEEE.std_logic_unsigned.all;



library UNISIM;
use UNISIM.VComponents.all;

library XPM;
use XPM.VComponents.all;

entity t0_timestamp is
  Port (
        clk_40             : in std_logic;
        reset_in           : in std_logic; 
        trigger_ext         : in std_logic;

        t0_timestamp        : out std_logic_vector(16 downto 0);
        t0_ready            : out std_logic;
        clk0                : inout std_logic;

        is_rising_edge      : in std_logic;       
        coarse_count_offset : in std_logic_vector(11 downto 0);
        rollover            : in std_logic_vector(11 downto 0)      
  );
end t0_timestamp;

architecture Behavioral of t0_timestamp is

--------------------------------------------------------------------------
  --Output     Output      Phase    Duty Cycle   Pk-to-Pk     Phase
   --Clock     Freq (MHz)  (degrees)    (%)     Jitter (ps)  Error (ps)
--------------------------------------------------------------------------
 --clk_out1__160.00000______0.000______50.0______108.430_____95.076
 --clk_out2__160.00000_____45.000______50.0______108.430_____95.076
 --clk_out3__160.00000_____90.000______50.0______108.430_____95.076
 --clk_out4__160.00000____135.000______50.0______108.430_____95.076
 --clk_out5__160.00000______0.000______50.0______108.430_____95.076
--
--------------------------------------------------------------------------
 --Input Clock   Freq (MHz)    Input Jitter (UI)
--------------------------------------------------------------------------
 --__primary_____________160____________0.01


-- The following code must appear in the VHDL architecture header:
------------- Begin Cut here for COMPONENT Declaration ------ COMP_TAG
component fpga_tdc_clock
port
 (
  -- Clock out ports
  clk_out1          : out    std_logic;
  clk_out2          : out    std_logic;
  clk_out3          : out    std_logic;
  clk_out4          : out    std_logic;
  clk_out5          : out    std_logic;
  -- Clock in ports
  clk_in1           : in     std_logic
 );
end component;

-- Purpose: This function performs a bitwise or on the input vector
  function f_BITWISE_OR (
    r_SLV_IN    : in std_logic_vector)
    return std_logic is
    variable v_OR : std_logic := '0';
  begin
    for i in 0 to r_SLV_IN'length-1 loop
      v_OR := v_OR or r_SLV_IN(i);
    end loop;
    return v_OR;
     
  end function f_BITWISE_OR;

signal hit_in                   : std_logic;
signal hit_in_pre               : std_logic_vector (7 downto 0):= x"00";
signal hit_chain1_tmp           : std_logic;
signal hit_chain2_tmp           : std_logic;
signal hit_chain6_tmp           : std_logic;


signal coarse_time              : std_logic_vector (13 downto 0):= "00"&x"000";
signal coarse_cnt               : std_logic_vector (13 downto 0):= "00"&x"000";
--signal coarse_invcnt            : std_logic_vector (13 downto 0):= "00"&x"000";
signal fine_time                : std_logic_vector (2 downto 0):= "000";
signal TH2B                     : std_logic_vector (2 downto 0):= "000";
signal sample_reg_stage1        : std_logic_vector (7 downto 0):= x"00";
signal sample_reg_stage2        : std_logic_vector (7 downto 0):= x"00";
signal sample_reg_stage3        : std_logic_vector (7 downto 0):= x"00";
signal sync_reg2encoder         : std_logic_vector (7 downto 0):= x"00";

--signal clk0             : std_logic;
signal clk1             : std_logic;
signal clk2             : std_logic;
signal clk3             : std_logic;
signal clk_coarse       : std_logic;

signal stage2_bitor_mask        : std_logic:= '0';
signal stage3_bitor_mask        : std_logic:= '0';
signal en, en_r, en_f           : std_logic := '0';

signal reset_clk0               : std_logic;
signal reset_clk1               : std_logic;
signal reset_clk2               : std_logic;
signal reset_clk3               : std_logic;
signal reset_r                  : std_logic;

begin

hit_in  <= trigger_ext when is_rising_edge = '1' else (not trigger_ext);


sample_clk_gen : fpga_tdc_clock
   port map ( 
  -- Clock out ports  
   clk_out1 => clk0,
   clk_out2 => clk1,
   clk_out3 => clk2,
   clk_out4 => clk3,
   clk_out5 => clk_coarse,
  -- Status and control signals                
   -- Clock in ports
   clk_in1 => clk_40
 );

-- Each phase domain needs its own synchronized reset.  A reset synchronized
-- only to clk0 must not directly drive registers clocked by clk1/clk2/clk3.
bcr_clk0_sync : xpm_cdc_sync_rst
   generic map (
      DEST_SYNC_FF   => 5,
      INIT           => 1,
      INIT_SYNC_FF   => 0,
      SIM_ASSERT_CHK => 1
   )
   port map (
      src_rst  => reset_in,
      dest_clk => clk0,
      dest_rst => reset_clk0
   );

bcr_clk1_sync : xpm_cdc_sync_rst
   generic map (
      DEST_SYNC_FF   => 5,
      INIT           => 1,
      INIT_SYNC_FF   => 0,
      SIM_ASSERT_CHK => 1
   )
   port map (
      src_rst  => reset_in,
      dest_clk => clk1,
      dest_rst => reset_clk1
   );

bcr_clk2_sync : xpm_cdc_sync_rst
   generic map (
      DEST_SYNC_FF   => 5,
      INIT           => 1,
      INIT_SYNC_FF   => 0,
      SIM_ASSERT_CHK => 1
   )
   port map (
      src_rst  => reset_in,
      dest_clk => clk2,
      dest_rst => reset_clk2
   );

bcr_clk3_sync : xpm_cdc_sync_rst
   generic map (
      DEST_SYNC_FF   => 5,
      INIT           => 1,
      INIT_SYNC_FF   => 0,
      SIM_ASSERT_CHK => 1
   )
   port map (
      src_rst  => reset_in,
      dest_clk => clk3,
      dest_rst => reset_clk3
   );



-- Sampling hit with 780ps resolution

sample_chain0_proc0: process (clk0) 
    begin
        if rising_edge (clk0) then
            if reset_clk0 = '1' then
                hit_in_pre(0)           <= '0';
                sample_reg_stage1(0)    <= '0';
                sample_reg_stage2(0)    <= '0';
                sample_reg_stage3(0)    <= '0';
            else
                hit_in_pre(0)           <= hit_in;
                sample_reg_stage1(0)    <= hit_in_pre(0);
                sample_reg_stage2(0)    <= sample_reg_stage1(0);
                sample_reg_stage3(0)    <= sample_reg_stage2(0);
            end if;
        end if;
    end process;
    

sample_chain1_proc0: process (clk1) 
    begin
        if rising_edge (clk1) then
            if reset_clk1 = '1' then
                hit_in_pre(1) <= '0';
            else
                hit_in_pre(1) <= hit_in;
            end if;
        end if;
    end process;

sample_chain1_proc1: process (clk0) 
    begin
        if falling_edge (clk0) then
            if reset_clk0 = '1' then
                hit_chain1_tmp <= '0';
            else
                hit_chain1_tmp <= hit_in_pre(1);
            end if;
        end if;
    end process;                     

sample_chain1_proc2: process (clk0) 
    begin
        if rising_edge (clk0) then
            if reset_clk0 = '1' then
                sample_reg_stage1(1) <= '0';
                sample_reg_stage2(1) <= '0';
                sample_reg_stage3(1) <= '0';
            else
                sample_reg_stage1(1) <= hit_chain1_tmp;
                sample_reg_stage2(1) <= sample_reg_stage1(1);
                sample_reg_stage3(1) <= sample_reg_stage2(1);
            end if;
        end if;
    end process; 



sample_chain2_proc0: process (clk2) 
    begin
        if rising_edge (clk2) then
            if reset_clk2 = '1' then
                hit_in_pre(2) <= '0';
            else
                hit_in_pre(2) <= hit_in;
            end if;
        end if;
    end process;

sample_chain2_proc1: process (clk1) 
    begin
        if falling_edge (clk1) then
            if reset_clk1 = '1' then
                hit_chain2_tmp <= '0';
            else
                hit_chain2_tmp <= hit_in_pre(2);
            end if;
        end if;
    end process;                     

sample_chain2_proc2: process (clk0) 
    begin
        if rising_edge (clk0) then
            if reset_clk0 = '1' then
                sample_reg_stage1(2) <= '0';
                sample_reg_stage2(2) <= '0';
                sample_reg_stage3(2) <= '0';
            else
                sample_reg_stage1(2) <= hit_chain2_tmp;
                sample_reg_stage2(2) <= sample_reg_stage1(2);
                sample_reg_stage3(2) <= sample_reg_stage2(2);
            end if;
        end if;
    end process; 
        


sample_chain3_proc0: process (clk3) 
    begin
        if rising_edge (clk3) then
            if reset_clk3 = '1' then
                hit_in_pre(3) <= '0';
            else
                hit_in_pre(3) <= hit_in;
            end if;
        end if;
    end process;

sample_chain3_proc1: process (clk0) 
    begin
        if rising_edge (clk0) then
            if reset_clk0 = '1' then
                sample_reg_stage1(3) <= '0';
                sample_reg_stage2(3) <= '0';
                sample_reg_stage3(3) <= '0';
            else
                sample_reg_stage1(3) <= hit_in_pre(3);
                sample_reg_stage2(3) <= sample_reg_stage1(3);
                sample_reg_stage3(3) <= sample_reg_stage2(3);
            end if;
        end if;
    end process;                     


sample_chain4_proc0: process (clk0) 
    begin
        if falling_edge (clk0) then --"clk4"
            if reset_clk0 = '1' then
                hit_in_pre(4) <= '0';
            else
                hit_in_pre(4) <= hit_in;
            end if;
        end if;
    end process;

sample_chain4_proc1: process (clk0) 
    begin
        if rising_edge (clk0) then
            if reset_clk0 = '1' then
                sample_reg_stage1(4) <= '0';
                sample_reg_stage2(4) <= '0';
                sample_reg_stage3(4) <= '0';
            else
                sample_reg_stage1(4) <= hit_in_pre(4);
                sample_reg_stage2(4) <= sample_reg_stage1(4);
                sample_reg_stage3(4) <= sample_reg_stage2(4);
            end if;
        end if;
    end process;


sample_chain5_proc0: process (clk1) 
    begin
        if falling_edge (clk1) then --"clk5"
            if reset_clk1 = '1' then
                hit_in_pre(5) <= '0';
            else
                hit_in_pre(5) <= hit_in;
            end if;
        end if;
    end process;

sample_chain5_proc1: process (clk0) 
    begin
        if rising_edge (clk0) then
            if reset_clk0 = '1' then
                sample_reg_stage1(5) <= '0';
                sample_reg_stage2(5) <= '0';
                sample_reg_stage3(5) <= '0';
            else
                sample_reg_stage1(5) <= hit_in_pre(5);
                sample_reg_stage2(5) <= sample_reg_stage1(5);
                sample_reg_stage3(5) <= sample_reg_stage2(5);
            end if;
        end if;
    end process;
    

sample_chain6_proc0: process (clk2) 
    begin
        if falling_edge (clk2) then --"clk6"
            if reset_clk2 = '1' then
                hit_in_pre(6) <= '0';
            else
                hit_in_pre(6) <= hit_in;
            end if;
        end if;
    end process;

sample_chain6_proc1: process (clk1) 
    begin
        if rising_edge (clk1) then
            if reset_clk1 = '1' then
                sample_reg_stage1(6) <= '0';
            else
                sample_reg_stage1(6) <= hit_in_pre(6);
            end if;
        end if;
    end process;

sample_chain6_proc2: process (clk0) 
    begin
        if falling_edge (clk0) then
            if reset_clk0 = '1' then
                hit_chain6_tmp <= '0';
            else
                hit_chain6_tmp <= sample_reg_stage1(6);
            end if;
        end if;
    end process;
    
    
sample_chain6_proc3: process (clk0) 
    begin
        if rising_edge (clk0) then
            if reset_clk0 = '1' then
                sample_reg_stage2(6) <= '0';
                sample_reg_stage3(6) <= '0';
            else
                sample_reg_stage2(6) <= sample_reg_stage1(6);
                sample_reg_stage3(6) <= sample_reg_stage2(6);
            end if;
        end if;
    end process;    



sample_chain7_proc0: process (clk3) 
    begin
        if falling_edge (clk3) then --"clk7"
            if reset_clk3 = '1' then
                hit_in_pre(7) <= '0';
            else
                hit_in_pre(7) <= hit_in;
            end if;
        end if;
    end process;

sample_chain7_proc1: process (clk0) 
    begin
        if falling_edge (clk0) then
            if reset_clk0 = '1' then
                sample_reg_stage1(7) <= '0';
            else
                sample_reg_stage1(7) <= hit_in_pre(7);
            end if;
        end if;
    end process;        
        

sample_chain7_proc2: process (clk0) 
    begin
        if rising_edge (clk0) then
            if reset_clk0 = '1' then
                sample_reg_stage2(7) <= '0';
                sample_reg_stage3(7) <= '0';
            else
                sample_reg_stage2(7) <= sample_reg_stage1(7);
                sample_reg_stage3(7) <= sample_reg_stage2(7);
            end if;
        end if;
    end process;     
        
---------------------------------
------------------
-- latch
------------------
stage2_bitor_mask <= f_BITWISE_OR(sample_reg_stage2);
stage3_bitor_mask <= f_BITWISE_OR(sample_reg_stage3);


enable_proc: process(stage2_bitor_mask, stage3_bitor_mask)
    begin
        if stage3_bitor_mask = '0' and stage2_bitor_mask = '1' then
            en <= '1';
        else
            en <= '0';
        end if;
    end process;

en_gen: process (clk0) 
    begin
        if rising_edge (clk0) then
            if reset_clk0 = '1' then
                en_r <= '0';
            else
                en_r <= en;
            end if;
        end if;
    end process; 

en_f <= en and (not en_r);   

latch_proc: process (clk0) 
    begin
        if rising_edge (clk0) then
            if reset_clk0 = '1' then
                sync_reg2encoder <= (others =>'0');
            elsif en_f = '1' then
                sync_reg2encoder <= sample_reg_stage2;
            end if;
        end if;
    end process; 

---------------------------------
------------------
-- TH2B fine time encoder
------------------ 

encoding_proc: process (sync_reg2encoder, reset_clk0)
    begin
        
        if reset_clk0 = '1' then
            TH2B <= "000";
        else
            if sync_reg2encoder (0) = '1' then
                TH2B <= "000";
            elsif sync_reg2encoder (1) = '1' then
                TH2B <= "001";
            elsif sync_reg2encoder (2) = '1' then
                TH2B <= "010";
            elsif sync_reg2encoder (3) = '1' then
                 TH2B <= "011";
            elsif sync_reg2encoder (4) = '1' then
                 TH2B <= "100";
            elsif sync_reg2encoder (5) = '1' then
                 TH2B <= "101";
            elsif sync_reg2encoder (6) = '1' then
                 TH2B <= "110";
            elsif sync_reg2encoder (7) = '1' then
                 TH2B <= "111";
            else
                TH2B <= "000";
            end if;
        end if;
    end process; 

---------------------------------
------------------
-- coarse time 
------------------  

-- there will be a fixed delay due to coarse_counter and coarse_cnt use different reset

--coarse_counter_40M_pro: process (clk_40) 
--    begin
--        if rising_edge (clk_40) then
--            if reset_in = '1' then
--                coarse_counter <= coarse_count_offset;
--            else 
--                if coarse_counter = rollover then
--                    coarse_counter <= (others =>'0');
--                else coarse_counter <= coarse_counter + 1;
--                end if;
--            end if;
--        end if;
--    end process;


coarse_cnt_proc: process (clk0) 
    begin
        if rising_edge (clk0) then
            if reset_clk0 = '1' then
                coarse_cnt <= coarse_count_offset&"00";
            else 
                if coarse_cnt = rollover&"11" then
                    coarse_cnt <= (others =>'0');
                else coarse_cnt <= coarse_cnt + 1;
                end if;
            end if;
        end if;
    end process; 

--coarse_invcnt_proc: process (clk0) 
--    begin
--        if falling_edge (clk0) then
--            if reset = '1' then
--                coarse_invcnt <= coarse_count_offset&"00";
--            else 
--                if coarse_invcnt = rollover&"11" then
--                    coarse_invcnt <= (others =>'0');
--                else coarse_invcnt <= coarse_invcnt + 1;
--                end if;
--            end if;
--        end if;
--    end process; 

reset_proc: process (clk0) 
    begin
        if falling_edge (clk0) then
           reset_r  <= reset_clk0;
        end if;
    end process;


coarse_sel_proc: process (clk0) 
    begin
        if rising_edge (clk0) then
            if reset_r = '1' then
                --coarse_time <= (others =>'0');
                coarse_time <= coarse_count_offset&"00";
            elsif en_f = '1' then
                coarse_time <= coarse_cnt; 
            end if;
        end if;
    end process; 
   
t0_timestamp    <= coarse_time & TH2B;


ready_proc: process (clk0) 
    begin
        if rising_edge (clk0) then
            t0_ready <= en_f;
        end if;
    end process;

     
end Behavioral;
