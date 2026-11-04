from TDC_config_low_level_function import *
from ASDreg import *
from crc8_D81 import *


class TDCreg(object):
    def __init__(self):
        self.init_all_reg()
        self.ASD0 = ASD_chip()
        self.ASD1 = ASD_chip()
        self.ASD2 = ASD_chip()
        self.ASD_list=[self.ASD0,self.ASD1,self.ASD2]

        # self.asd_mezz = ASD_mezz()

    def init_setup_0(self):
        #setup_0
        #TTC_setup
        self.enable_new_ttc = ['0']
        self.enable_master_reset_code =['1']
        self.enable_direct_bunch_reset = ['0']
        self.enable_direct_event_reset = ['0']
        self.enable_direct_trigger = ['0']
        #bcr_distribute
        self.auto_roll_over = ['0']
        self.bypass_bcr_distribution =['0']
        #tdc_mode
        self.enable_trigger = ['0']
        self.channel_data_debug = ['0']
        self.enable_leading = ['0']
        self.enable_pair = ['1']
        self.enable_fake_hit = ['0']
        self.rising_is_leading = ['000000000000000000000000']
        self.channel_enable_r = ['111111111111111111111111']
        self.channel_enable_f = ['111111111111111111111111']
        #readout
        self.TDC_ID = ['1111010101010101010'] #FADEC001
        self.enable_trigger_timeout = ['0']
        self.enable_high_speed = ['1']
        self.enable_legacy = ['0']
        self.full_width_res = ['0']
        self.width_select = ['001']
        self.enable_8b10b = ['1']
        self.enable_insert =['0']
        self.enable_error_packet = ['0']
        self.enable_TDC_ID = ['0']
        self.enable_error_notify = ['0']
        #setup_0
        self.TTC_setup = [self.enable_new_ttc , self.enable_master_reset_code , self.enable_direct_bunch_reset , self.enable_direct_event_reset , self.enable_direct_trigger]
        self.bcr_distribute = [self.auto_roll_over , self.bypass_bcr_distribution]
        self.tdc_mode = [self.enable_trigger , self.channel_data_debug , self.enable_leading , self.enable_pair , self.enable_fake_hit ,self.rising_is_leading , self.channel_enable_r , self.channel_enable_f]
        self.TDC_ID_l = [self.TDC_ID]
        self.readout = [self.enable_trigger_timeout , self.enable_high_speed , self.enable_legacy , self.full_width_res , self.width_select , self.enable_8b10b , self.enable_insert , self.enable_error_packet , self.enable_TDC_ID , self.enable_error_notify]
        self.setup_0 = self.TTC_setup + self.bcr_distribute + self.tdc_mode + self.TDC_ID_l + self.readout
        # self.setup_0_indictor = ['0']

    def init_setup_1(self):
        ##setup_1
        #timer_out
        self.combine_time_out_config = ['0001010000']
        self.fake_hit_time_interval =['000100000000']
        self.syn_packet_number = ['111111111111']        
        #coarse_out
        self.roll_over = ['111111111111']
        self.coarse_count_offset = ['000000000000']
        self.bunch_offset = ['111110011100']
        self.event_offset = ['000000000000']
        self.match_window = ['000000011111']
        #setup_1
        self.timer_out = [self.combine_time_out_config , self.fake_hit_time_interval , self.syn_packet_number]
        self.coarse_out = [self.roll_over , self.coarse_count_offset , self.bunch_offset , self.event_offset , self.match_window]
        self.setup_1 = self.timer_out +self.coarse_out 
        # self.setup_1_indictor = ['0']

    def init_setup_2(self):
        ##setup_2
        #timer_out
        self.fine_sel = ['0011']
        self.lut0 = ['00']
        self.lut1 = ['01']
        self.lut2 = ['10']
        self.lut3 = ['01']
        self.lut4 = ['11']
        self.lut5 = ['00']
        self.lut6 = ['10']
        self.lut7 = ['10']
        self.lut8 = ['00']
        self.lut9 = ['00']
        self.luta = ['00']
        self.lutb = ['01']
        self.lutc = ['11']
        self.lutd = ['00']
        self.lute = ['11']
        self.lutf = ['00']
        self.chnl_decode = [self.fine_sel , self.lut0 ,self.lut1 ,self.lut2, self.lut3 ,self.lut4 ,self.lut5 ,self.lut6 ,self.lut7 ,self.lut8 ,self.lut9 ,self.luta ,self.lutb ,self.lutc ,self.lutd ,self.lute ,self.lutf]
        self.setup_2 = self.chnl_decode
        # self.setup_2_indictor = ['0']

    def init_setup(self):
        self.init_setup_0()
        self.init_setup_1()
        self.init_setup_2()
        self.setup = [self.setup_0, self.setup_1, self.setup_2]

    def init_control_0(self):
        ##control_0
        #reset_control
        self.rst_ePLL = ['0']
        self.reset_jtag_in = ['0']
        self.event_reset_jtag_in = ['0']
        self.chnl_fifo_overflow_clear = ['0']
        self.debug_port_select =['0000']
        #control_0
        self.reset_control = [self.rst_ePLL , self.reset_jtag_in , self.event_reset_jtag_in , self.chnl_fifo_overflow_clear , self.debug_port_select]
        self.control_0 = self.reset_control
        # self.control_0_indictor = ['0']

    def init_control_1(self):
        ##control_1
        self.phase_clk160 = ['01000']
        self.phase_clk320_0 = ['0100']
        self.phase_clk320_1 = ['0000']
        self.phase_clk320_2 = ['0010']
        self.ePllRes = ['0010']
        self.ePllIcp = ['0100']
        self.ePllCap = ['10']
        self.ePLL_control = [self.phase_clk160 , self.phase_clk320_0 , self.phase_clk320_1 , self.phase_clk320_2 , self.ePllRes , self.ePllIcp , self.ePllCap,self.ePllRes , self.ePllIcp , self.ePllCap,self.ePllRes , self.ePllIcp , self.ePllCap]
        self.control_1 = self.ePLL_control
        # self.control_1_indictor = ['0']

    def init_conttrol(self):
        self.init_control_0()
        self.init_control_1()
        self.control = [self.control_0 , self.control_1]

    def init_status_0(self):
        self.instruction_error = ['0']
        self.CRC = ['00000000000000000000000000000000']
        self.status_0 = [self.instruction_error,self.CRC]

    def init_status_1(self):
        self.ePll_lock = ['0']
        self.chnl_fifo_overflow = ['000000000000000000000000']
        self.status_1 = [self.ePll_lock,self.chnl_fifo_overflow]

    def init_status(self):
        self.init_status_0()
        self.init_status_1()
        self.status = [self.status_0 , self.status_1]
        self.IDCODE = [32*'0']

    def init_all_reg(self):
        self.init_setup()
        self.init_conttrol()
        self.init_status()
        # print("All GUI regs reset!")

