from TDCreg import *

class CSMreg(object):
    def __init__(self):
        self.mezz_per_CSM = 20
        self.TDC_enable = [self.mezz_per_CSM*'1']
        self.TDC_list=[]
        for i in range(self.mezz_per_CSM):
            self.TDC_list.append(TDCreg())