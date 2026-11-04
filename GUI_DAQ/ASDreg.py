class ASD_chip(object):
    def __init__(self):
        self.channel_0_mode = ['10']
        self.channel_1_mode = ['10']
        self.channel_2_mode = ['10']
        self.channel_3_mode = ['10']
        self.channel_4_mode = ['10']
        self.channel_5_mode = ['10']
        self.channel_6_mode = ['10']
        self.channel_7_mode = ['10']
        self.chip_mode =['0']
        self.deadtime =['111']
        self.int_gate =['0100']
        self.rundown_curr =['010']
        self.hyst =['1110']
        self.wilk_thr =['010']
        self.main_thr =['01110010']
        self.unused =['0000000000000']
        # self.unused =['1111000100101']
        self.setup =   [self.channel_0_mode,self.channel_1_mode,self.channel_2_mode,self.channel_3_mode,
                        self.channel_4_mode,self.channel_5_mode,self.channel_6_mode,self.channel_7_mode,
                        self.chip_mode,self.deadtime,self.int_gate,self.rundown_curr,self.hyst,
                        self.wilk_thr,self.main_thr,self.unused]


# class ASD_mezz(object):
#     def __init__(self):
#         self.ASD0 = ASD_chip()   
#         self.ASD1 = ASD_chip()
#         self.ASD2 = ASD_chip()
#         self.ASD_mezz_setup = [self.ASD2.setup, self.ASD1.setup, self.ASD0.setup]

    
         


    # def update_ASD(self):
    #     self.asd_bin_str = ''.join(self.asd_align)
    #     for s in self.ASD_setup:
    #         self.asd_bin_str = self.asd_bin_str + ''.join(s)
    #     self.setup_0_str=bin_to_hex(self.asd_bin_str)


    # def list_to_string(self,var):
    #     string_temp = ''
    #     for s in self.__dict__[var]:
    #         string_temp=string_temp+''.join(s)
    #     return string_temp
