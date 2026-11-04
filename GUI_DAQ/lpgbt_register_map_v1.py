#!/usr/bin/env python3
###############################################################################
#                                                                             #
#        _        _____ ____ _______                                          #
#       | |      / ____|  _ \__   __|                                         #
#       | |_ __ | |  __| |_) | | |                                            #
#       | | '_ \| | |_ |  _ <  | |                                            #
#       | | |_) | |__| | |_) | | |                                            #
#       |_| .__/ \_____|____/  |_|                                            #
#         | |                                                                 #
#         |_|                                                                 #
#                                                                             #
#  Copyright (C) 2020-2021 lpGBT Team, CERN                                   #
#                                                                             #
#  This IP block is free for HEP experiments and other scientific research    #
#  purposes. Commercial exploitation of a chip containing the IP is not       #
#  permitted.  You can not redistribute the IP without written permission     #
#  from the authors. Any modifications of the IP have to be communicated back #
#  to the authors. The use of the IP should be acknowledged in publications,  #
#  public presentations, user manual, and other documents.                    #
#                                                                             #
#  This IP is distributed in the hope that it will be useful, but WITHOUT ANY #
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS  #
#  FOR A PARTICULAR PURPOSE.                                                  #
#                                                                             #
###############################################################################
""" Lpgbt v1 Constants"""

# pylint: disable=too-many-lines,too-few-public-methods,missing-class-docstring
# pylint: disable=empty-docstring,line-too-long,invalid-name
# pylint: disable=missing-function-docstring

from enum import IntEnum, unique


class LpgbtRegisterMapV1:
    """Class containing all lpGBT-related constants"""

    class CHIPID0:
        """Stores bits 31:24 of the CHIPID"""

        address = 0x0000

        @staticmethod
        def __str__():
            return "CHIPID0"

        @staticmethod
        def __int__():
            return 0x0000

        class CHIPID:
            """Bits 31:24 of the CHIPID"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class CHIPID1:
        """Stores bits 23:16 of the CHIPID"""

        address = 0x0001

        @staticmethod
        def __str__():
            return "CHIPID1"

        @staticmethod
        def __int__():
            return 0x0001

        class CHIPID:
            """Bits 23:16 of the CHIPID"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class CHIPID2:
        """Stores bits 15:8 of the CHIPID"""

        address = 0x0002

        @staticmethod
        def __str__():
            return "CHIPID2"

        @staticmethod
        def __int__():
            return 0x0002

        class CHIPID:
            """Bits 15:8 of the CHIPID"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class CHIPID3:
        """Stores bits 7:0 of the CHIPID"""

        address = 0x0003

        @staticmethod
        def __str__():
            return "CHIPID3"

        @staticmethod
        def __int__():
            return 0x0003

        class CHIPID:
            """Bits 7:0 of the CHIPID"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class USERID0:
        """Stores bits 31:24 of the USERID"""

        address = 0x0004

        @staticmethod
        def __str__():
            return "USERID0"

        @staticmethod
        def __int__():
            return 0x0004

        class USERID:
            """Bits 31:24 of the USERID"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class USERID1:
        """Stores bits 23:16 of the USERID"""

        address = 0x0005

        @staticmethod
        def __str__():
            return "USERID1"

        @staticmethod
        def __int__():
            return 0x0005

        class USERID:
            """Bits 23:16 of the USERID"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class USERID2:
        """Stores bits 15:8 of the USERID"""

        address = 0x0006

        @staticmethod
        def __str__():
            return "USERID2"

        @staticmethod
        def __int__():
            return 0x0006

        class USERID:
            """Bits 15:8 of the USERID"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class USERID3:
        """Stores bits 7:0 of the USERID"""

        address = 0x0007

        @staticmethod
        def __str__():
            return "USERID3"

        @staticmethod
        def __int__():
            return 0x0007

        class USERID:
            """Bits 7:0 of the USERID"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class DACCAL0:
        """Calibration data for the voltage DAC. Usage is TBD."""

        address = 0x0008

        @staticmethod
        def __str__():
            return "DACCal0"

        @staticmethod
        def __int__():
            return 0x0008

        class DACCALMINCODE:
            """Calibration data for the voltage DAC. Usage is TBD."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class DACCAL1:
        """Calibration data for the voltage DAC. Usage is TBD."""

        address = 0x0009

        @staticmethod
        def __str__():
            return "DACCal1"

        @staticmethod
        def __int__():
            return 0x0009

        class DACCALMAXCODE:
            """Calibration data for the voltage DAC. Usage is TBD."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class DACCAL2:
        """Calibration data for the voltage DAC. Usage is TBD."""

        address = 0x000A

        @staticmethod
        def __str__():
            return "DACCal2"

        @staticmethod
        def __int__():
            return 0x000A

        class DACCALMINCODE:
            """Calibration data for the voltage DAC. Usage is TBD."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class DACCALMAXCODE:
            """Calibration data for the voltage DAC. Usage is TBD."""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class ADCCAL0:
        """Calibration data for the ADC.Usage is TBD."""

        address = 0x000B

        @staticmethod
        def __str__():
            return "ADCCal0"

        @staticmethod
        def __int__():
            return 0x000B

        class ADCCALGAIN2SEHIGH:
            """Calibration data for the ADC. Usage is TBD."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class ADCCAL1:
        """Calibration data for the ADC.Usage is TBD."""

        address = 0x000C

        @staticmethod
        def __str__():
            return "ADCCal1"

        @staticmethod
        def __int__():
            return 0x000C

        class ADCCALGAIN2SELOW:
            """Calibration data for the ADC. Usage is TBD."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class ADCCAL2:
        """Calibration data for the ADC.Usage is TBD."""

        address = 0x000D

        @staticmethod
        def __str__():
            return "ADCCal2"

        @staticmethod
        def __int__():
            return 0x000D

        class ADCCALGAIN2SEHIGH:
            """Calibration data for the ADC. Usage is TBD."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class ADCCALGAIN2SELOW:
            """Calibration data for the ADC. Usage is TBD."""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class ADCCAL3:
        """Calibration data for the ADC.Usage is TBD."""

        address = 0x000E

        @staticmethod
        def __str__():
            return "ADCCal3"

        @staticmethod
        def __int__():
            return 0x000E

        class ADCCALGAIN2DIFHIGH:
            """Calibration data for the ADC. Usage is TBD."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class ADCCAL4:
        """Calibration data for the ADC.Usage is TBD."""

        address = 0x000F

        @staticmethod
        def __str__():
            return "ADCCal4"

        @staticmethod
        def __int__():
            return 0x000F

        class ADCCALGAIN2DIFLOW:
            """Calibration data for the ADC. Usage is TBD."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class ADCCAL5:
        """Calibration data for the ADC.Usage is TBD."""

        address = 0x0010

        @staticmethod
        def __str__():
            return "ADCCal5"

        @staticmethod
        def __int__():
            return 0x0010

        class ADCCALGAIN2DIFHIGH:
            """Calibration data for the ADC. Usage is TBD."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class ADCCALGAIN2DIRFLOW:
            """Calibration data for the ADC. Usage is TBD."""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class ADCCAL6:
        """Calibration data for the ADC.Usage is TBD."""

        address = 0x0011

        @staticmethod
        def __str__():
            return "ADCCal6"

        @staticmethod
        def __int__():
            return 0x0011

        class ADCCALGAIN4DIFHIGH:
            """Calibration data for the ADC. Usage is TBD."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class ADCCAL7:
        """Calibration data for the ADC.Usage is TBD."""

        address = 0x0012

        @staticmethod
        def __str__():
            return "ADCCal7"

        @staticmethod
        def __int__():
            return 0x0012

        class ADCCALGAIN4DIFLOW:
            """Calibration data for the ADC. Usage is TBD."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class ADCCAL8:
        """Calibration data for the ADC.Usage is TBD."""

        address = 0x0013

        @staticmethod
        def __str__():
            return "ADCCal8"

        @staticmethod
        def __int__():
            return 0x0013

        class ADCCALGAIN4DIFHIGH:
            """Calibration data for the ADC. Usage is TBD."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class ADCCALGAIN4DIRFLOW:
            """Calibration data for the ADC. Usage is TBD."""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class ADCCAL9:
        """Calibration data for the ADC.Usage is TBD."""

        address = 0x0014

        @staticmethod
        def __str__():
            return "ADCCal9"

        @staticmethod
        def __int__():
            return 0x0014

        class ADCCALGAIN8DIFHIGH:
            """Calibration data for the ADC. Usage is TBD."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class ADCCAL10:
        """Calibration data for the ADC.Usage is TBD."""

        address = 0x0015

        @staticmethod
        def __str__():
            return "ADCCal10"

        @staticmethod
        def __int__():
            return 0x0015

        class ADCCALGAIN8DIFLOW:
            """Calibration data for the ADC. Usage is TBD."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class ADCCAL11:
        """Calibration data for the ADC.Usage is TBD."""

        address = 0x0016

        @staticmethod
        def __str__():
            return "ADCCal11"

        @staticmethod
        def __int__():
            return 0x0016

        class ADCCALGAIN8DIFHIGH:
            """Calibration data for the ADC. Usage is TBD."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class ADCCALGAIN8DIRFLOW:
            """Calibration data for the ADC. Usage is TBD."""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class ADCCAL12:
        """Calibration data for the ADC.Usage is TBD."""

        address = 0x0017

        @staticmethod
        def __str__():
            return "ADCCal12"

        @staticmethod
        def __int__():
            return 0x0017

        class ADCCALGAIN16DIFHIGH:
            """Calibration data for the ADC. Usage is TBD."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class ADCCAL13:
        """Calibration data for the ADC.Usage is TBD."""

        address = 0x0018

        @staticmethod
        def __str__():
            return "ADCCal13"

        @staticmethod
        def __int__():
            return 0x0018

        class ADCCALGAIN16DIFLOW:
            """Calibration data for the ADC. Usage is TBD."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class ADCCAL14:
        """Calibration data for the ADC.Usage is TBD."""

        address = 0x0019

        @staticmethod
        def __str__():
            return "ADCCal14"

        @staticmethod
        def __int__():
            return 0x0019

        class ADCCALGAIN16DIFHIGH:
            """Calibration data for the ADC. Usage is TBD."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class ADCCALGAIN16DIRFLOW:
            """Calibration data for the ADC. Usage is TBD."""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class TEMPCALH:
        """Calibration data for the temperature sensor."""

        address = 0x001A

        @staticmethod
        def __str__():
            return "TEMPCalH"

        @staticmethod
        def __int__():
            return 0x001A

        class TEMPCAL:
            """Calibration data for the temperature sensor. Usage is TBD."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class TEMPCALL:
        """Calibration data for the temperature sensor."""

        address = 0x001B

        @staticmethod
        def __str__():
            return "TEMPCalL"

        @staticmethod
        def __int__():
            return 0x001B

        class TEMPCAL:
            """Calibration data for the temperature sensor. Usage is TBD."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class VREFCNTR:
        """Voltage reference control."""

        address = 0x001C

        @staticmethod
        def __str__():
            return "VREFCNTR"

        @staticmethod
        def __int__():
            return 0x001C

        class VREFENABLE:
            """Enable internal voltage reference."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

    class VREFTUNE:
        """Voltage reference tuning register."""

        address = 0x001D

        @staticmethod
        def __str__():
            return "VREFTUNE"

        @staticmethod
        def __int__():
            return 0x001D

        class VREFTUNE:
            """Tuning world for internal voltage reference."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class CURDACCALH:
        """Calibration data for current DAC. Usage is TBD."""

        address = 0x001E

        @staticmethod
        def __str__():
            return "CURDACCalH"

        @staticmethod
        def __int__():
            return 0x001E

        class CURDACCAL:
            """Calibration data for current DAC. Usage is TBD."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class CURDACCALL:
        """Calibration data for current DAC. Usage is TBD."""

        address = 0x001F

        @staticmethod
        def __str__():
            return "CURDACCalL"

        @staticmethod
        def __int__():
            return 0x001F

        class CURDACCAL:
            """Calibration data for current DAC. Usage is TBD."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class CLKGCONFIG0:
        """"""

        address = 0x0020

        @staticmethod
        def __str__():
            return "CLKGConfig0"

        @staticmethod
        def __int__():
            return 0x0020

        class CLKGCALIBRATIONENDOFCOUNT:
            """Selects the VCO calibration race goal in number of clock cycles between refClk (refClkCounter) and vco_40MHz (vcoClkCounter) (2^(CLKGCalibrationEndOfCount[3:0]+1)); default: 14"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class CLKGBIASGENCONFIG:
            """Bias DAC for the charge pumps [0 : 8 : 120] uA; default: 8"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class CLKGCONFIG1:
        """"""

        address = 0x0021

        @staticmethod
        def __str__():
            return "CLKGConfig1"

        @staticmethod
        def __int__():
            return 0x0021

        class CDRCONTROLOVERRIDEENABLE:
            """Enables the control override of the state machine; default: 0"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class CLKGDISABLEFRAMEALIGNERLOCKCONTROL:
            """Disables the use of the frame aligner's lock status; default: 0"""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class CLKGCDRRES:
            """CDR's filter resistor enable; default: 1"""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class CLKGVCORAILMODE:
            """VCO rail mode; [0: voltage mode, fixed to VDDRX; 1: current mode, value selectable using CLKGVcoDAC]; default: 1"""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class CLKGVCODAC:
            """Current DAC for the VCO [0: 0.470 : 7.1] mA; default: 8"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class CLKGPLLRES:
        """"""

        address = 0x0022

        @staticmethod
        def __str__():
            return "CLKGPllRes"

        @staticmethod
        def __int__():
            return 0x0022

        class CLKGPLLRESWHENLOCKED:
            """PLL's filter resistance when PLL is locked [R = 1/2 * 79.8k / CONFIG] Ohm; default: 2"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class CLKGPLLRES:
            """PLL's filter resistance when PLL is locking [R = 1/2 * 79.8k / CONFIG] Ohm; default: 2"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class CLKGPLLINTCUR:
        """"""

        address = 0x0023

        @staticmethod
        def __str__():
            return "CLKGPLLIntCur"

        @staticmethod
        def __int__():
            return 0x0023

        class CLKGPLLINTCURWHENLOCKED:
            """PLL's integral current path when in locked state [0 : 1.1 : 8] uA; default: 9"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class CLKGPLLINTCUR:
            """PLL's integral current path when in locking state [0 : 1.1 : 8] uA; default: 9"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class CLKGPLLPROPCUR:
        """"""

        address = 0x0024

        @staticmethod
        def __str__():
            return "CLKGPLLPropCur"

        @staticmethod
        def __int__():
            return 0x0024

        class CLKGPLLPROPCURWHENLOCKED:
            """PLL's proportional current path when in locked state [0 : 5.46 : 82] uA; default: 9"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class CLKGPLLPROPCUR:
            """PLL's proportional current path when in locking state [0 : 5.46 : 82] uA; default: 9"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class CLKGCDRPROPCUR:
        """"""

        address = 0x0025

        @staticmethod
        def __str__():
            return "CLKGCDRPropCur"

        @staticmethod
        def __int__():
            return 0x0025

        class CLKGCDRPROPCURWHENLOCKED:
            """CDR's Alexander phase detector proportional current path when in locked state [0 : 5.46 : 82] uA; default: 5"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class CLKGCDRPROPCUR:
            """CDR's Alexander phase detector proportional current path when in locking state [0 : 5.46 : 82] uA; default: 5"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class CLKGCDRINTCUR:
        """"""

        address = 0x0026

        @staticmethod
        def __str__():
            return "CLKGCDRIntCur"

        @staticmethod
        def __int__():
            return 0x0026

        class CLKGCDRINTCURWHENLOCKED:
            """CDR's Alexander phase detector integral current path when in locked state [0 : 5.46 : 82] uA; default: 5"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class CLKGCDRINTCUR:
            """CDR's Alexander phase detector integral integral current path when in locking state [0 : 5.46 : 82] uA; default: 5"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class CLKGCDRFFPROPCUR:
        """"""

        address = 0x0027

        @staticmethod
        def __str__():
            return "CLKGCDRFFPropCur"

        @staticmethod
        def __int__():
            return 0x0027

        class CLKGCDRFEEDFORWARDPROPCURWHENLOCKED:
            """CDR's proportional feed forward current path when in locked state [0 : 5.46 : 82] uA; default: 6"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class CLKGCDRFEEDFORWARDPROPCUR:
            """CDR's proportional feed forward current path when in locking state [0 : 5.46 : 82] uA; default: 6"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class CLKGFLLINTCUR:
        """"""

        address = 0x0028

        @staticmethod
        def __str__():
            return "CLKGFLLIntCur"

        @staticmethod
        def __int__():
            return 0x0028

        class CLKGFLLINTCURWHENLOCKED:
            """CDR's frequency detector charge pump when in locked state [0 : 5.46 : 82] uA; default: 5"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class CLKGFLLINTCUR:
            """CDR's frequency detector charge pump when in locking state [0 : 5.46 : 82] uA; default: 5"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class CLKGFFCAP:
        """"""

        address = 0x0029

        @staticmethod
        def __str__():
            return "CLKGFFCAP"

        @staticmethod
        def __int__():
            return 0x0029

        class CDRCOCONNECTCDR:
            """Enables the connectCDR switch [0 - disable, 1 - enable] (only when CDRControlOverrideEnable is 1)"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class CLKGCAPBANKOVERRIDEENABLE:
            """Enables the override of the capacitor search during VCO calibration [0 - disable, 1 - enable]; default: 0"""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class CLKGFEEDFORWARDCAPWHENLOCKED:
            """CDR's feed forward filter's capacitance when in locked state [0: 44 : 308] fF; default: 3"""

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class CLKGFEEDFORWARDCAP:
            """CDR's feed forward filter's capacitance when in locking state [0: 44 : 308] fF; default: 3"""

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class CLKGCNTOVERRIDE:
        """"""

        address = 0x002A

        @staticmethod
        def __str__():
            return "CLKGCntOverride"

        @staticmethod
        def __int__():
            return 0x002A

        class CLKGCOOVERRIDEVC:
            """Forces the VCO's control voltage to be in mid range [0 - disable, 1 - enable] (only when CDRControlOverrideEnable is 1)"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class CDRCOREFCLKSEL:
            """Forces the reference clock selection for the VCO calibration [0 - data/4, 1 - external refClk] (only when CDRControlOverrideEnable is 1)"""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class CDRCOENABLEPLL:
            """Enables the enablePLL switch [0 - disable, 1 - enable] (only when CDRControlOverrideEnable is 1)"""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class CDRCOENABLEFD:
            """Enables the frequency detector [0 - disable, 1 - enable] (only when CDRControlOverrideEnable is 1)"""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class CDRCOENABLECDR:
            """Enables the enableCDR switch [0 - disable, 1 - enable] (only when CDRControlOverrideEnable is 1)"""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class CDRCODISDATACOUNTERREF:
            """Enables the data/4 ripple counter [1 - disable, 0 - enable] (only when CDRControlOverrideEnable is 1)"""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class CDRCODISDESVBIASGEN:
            """Enables the vbias for the CDR [1 - disable, 0 - enable] (only when CDRControlOverrideEnable is 1)"""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class CDRCOCONNECTPLL:
            """Enables the connectPLL switch [0 - disable, 1 - enable] (only when CDRControlOverrideEnable is 1)"""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class CLKGOVERRIDECAPBANK:
        """"""

        address = 0x002B

        @staticmethod
        def __str__():
            return "CLKGOverrideCapBank"

        @staticmethod
        def __int__():
            return 0x002B

        class CLKGCAPBANKSELECT:
            """Selects the capacitor bank value for the VCO (only when CLKGCapBankOverrideEnable is 1); default: n/a"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class CLKGWAITTIME:
        """"""

        address = 0x002C

        @staticmethod
        def __str__():
            return "CLKGWaitTime"

        @staticmethod
        def __int__():
            return 0x002C

        class CLKGWAITCDRTIME:
            """ljCDR state machine waiting for lock, RX/TRX mode, (16'h0001 << CLKGwaitCDRTime); (only when CLKGDisableFrameAlignerLockControl == 1); default: 8"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class CLKGWAITPLLTIME:
            """ljCDR state machine waiting for lock, TX mode, (16'h0001 << CLKGwaitPLLTime); (only when CLKGLockFilterEnable == 0); default: 8"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class CLKGLFCONFIG0:
        """Lock filter configuration for the clock generator block"""

        address = 0x002D

        @staticmethod
        def __str__():
            return "CLKGLFConfig0"

        @staticmethod
        def __int__():
            return 0x002D

        class CLKGLOCKFILTERENABLE:
            """Enables the lock filter on the instant lock signal (default: 1)"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class CLKGLOCKFILTERCLKALWAYSON:
            """Force clock of CLKG lock filter to be always enabled (disables clock gating) (default: 0)"""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class CLKGCAPBANKSELECT:
            """Selects the capacitor bank value for the VCO (only when CLKGCapBankOverrideEnable is 1); default: n/a"""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class CLKGLOCKFILTERLOCKTHRCOUNTER:
            """Sets the lock threshold value of the instant lock low pass filter.
            The number of 40 MHz clock cycles is set to :math:`2^{CLKGLockFilterLockThrCounter}` (default: 15)
            """

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class CLKGLFCONFIG1:
        """Lock filter configuration for the clock generator block"""

        address = 0x002E

        @staticmethod
        def __str__():
            return "CLKGLFConfig1"

        @staticmethod
        def __int__():
            return 0x002E

        class CLKGLOCKFILTERRELOCKTHRCOUNTER:
            """Sets the relock threshold value of the instant lock low pass filter.
            The number of 40 MHz clock cycles is set to :math:`2^{CLKGLockFilterReLockThrCounter}` (default: 15)
            """

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class CLKGLOCKFILTERUNLOCKTHRCOUNTER:
            """Sets the unlock threshold value of the instant lock low pass filter.
            The number of 40 MHz clock cycles is set to :math:`2^{CLKGLockFilterUnLockThrCounter}` (default: 15)
            """

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class FAMAXHEADERFOUNDCOUNT:
        """Frame aligner configuration register."""

        address = 0x002F

        @staticmethod
        def __str__():
            return "FAMaxHeaderFoundCount"

        @staticmethod
        def __int__():
            return 0x002F

        class FAMAXHEADERFOUNDCOUNT:
            """The number of consecutive valid frame headers that have to be detected before frame lock is assumed. Default: 16"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class FAMAXHEADERFOUNDCOUNTAFTERNF:
        """Frame aligner configuration register."""

        address = 0x0030

        @staticmethod
        def __str__():
            return "FAMaxHeaderFoundCountAfterNF"

        @staticmethod
        def __int__():
            return 0x0030

        class FAMAXHEADERFOUNDCOUNTAFTERNF:
            """After frame synchronization and if an invalid header has been detected, this is the minimum number of consecutive valid headers that must be detected before the frame is confirmed to be still synchronized. Default: 16"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class FAMAXHEADERNOTFOUNDCOUNT:
        """Frame aligner configuration register."""

        address = 0x0031

        @staticmethod
        def __str__():
            return "FAMaxHeaderNotFoundCount"

        @staticmethod
        def __int__():
            return 0x0031

        class FAMAXHEADERNOTFOUNDCOUNT:
            """After frame synchronization, this is the maximum number of invalid headers (consecutive or not) that are allowed to occur before the frame is considered to be unlocked. Default: 16"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class RESERVED1:
        """Reserved register."""

        address = 0x0032

        @staticmethod
        def __str__():
            return "RESERVED1"

        @staticmethod
        def __int__():
            return 0x0032

    class PSDLLCONFIG:
        """Configuration for phase-shifter DLL"""

        address = 0x0033

        @staticmethod
        def __str__():
            return "PSDllConfig"

        @staticmethod
        def __int__():
            return 0x0033

        class PSDLLCONFIRMCOUNT:
            """Number of clock cycles (in the 40 MHz clock domain)
            to confirm locked state.

                +----------------------------+---------------------+------------------------+
                | PSDLLConfirmCount[1:0]     | Number of clock cycles                       |
                +============================+=====================+========================+
                | 2'd0                       | 1                                            |
                +----------------------------+---------------------+------------------------+
                | 2'd1                       | 4                                            |
                +----------------------------+---------------------+------------------------+
                | 2'd2                       | 16                                           |
                +----------------------------+---------------------+------------------------+
                | 2'd3                       | 31                                           |
                +----------------------------+---------------------+------------------------+


            """

            offset = 2
            length = 2
            bit_mask = 12

            @staticmethod
            def validate(value):
                return value in range(4)

        class PSDLLCURRENTSEL:
            """Current for the DLL charge pump

            +-----------------------+---------------------+------------------------+
            | PSDllCurrentSel[1:0]  | Current [uA]                                 |
            +=======================+=====================+========================+
            | 2'd0                  | 1                                            |
            +-----------------------+---------------------+------------------------+
            | 2'd1                  | 2                                            |
            +-----------------------+---------------------+------------------------+
            | 2'd2                  | 4                                            |
            +-----------------------+---------------------+------------------------+
            | 2'd3                  | 8                                            |
            +-----------------------+---------------------+------------------------+


            """

            offset = 0
            length = 2
            bit_mask = 3

            @staticmethod
            def validate(value):
                return value in range(4)

    class RESERVED2:
        """Reserved register."""

        address = 0x0034

        @staticmethod
        def __str__():
            return "RESERVED2"

        @staticmethod
        def __int__():
            return 0x0034

    class FORCEENABLE:
        """Enables user to enable specific sub-circuits regardless of the operation mode"""

        address = 0x0035

        @staticmethod
        def __str__():
            return "FORCEEnable"

        @staticmethod
        def __int__():
            return 0x0035

        class FORCETXENABLE:
            """Enable the TX logic  regardless of the operation mode"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class FORCERXENABLE:
            """Enable the RX logic  regardless of the operation mode"""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class LDFORCEENABLE:
            """Enables the Line Driver, regardless of the operation mode, when one of the loop-backs is selected."""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CMCLKALWAYSENABLE:
            """Always enable clock for the I2C masters during the power-on sequence (disable clock gating)"""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class PSFSMCLKALWAYSON:
            """Forces an initialization state machine clock to be always active (disables clock gating)"""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

    class CHIPCONFIG:
        """Miscellaneous chip configurations."""

        address = 0x0036

        @staticmethod
        def __str__():
            return "CHIPCONFIG"

        @staticmethod
        def __int__():
            return 0x0036

        class HIGHSPEEDDATAOUTINVERT:
            """Inverts high speed data output lines (equivalent to swapping HSOUTP and HSOUTN on the PCB)"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class HIGHSPEEDDATAININVERT:
            """Inverts high speed data input lines (equivalent to swapping HSINP and HSINN on the PCB)"""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class CHIPADDRESSBAR:
            """Sets most significant bits of the chip address (see :numref:`chipAddress`)."""

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EQCONFIG:
        """Main equalizer configuration register"""

        address = 0x0037

        @staticmethod
        def __str__():
            return "EQConfig"

        @staticmethod
        def __int__():
            return 0x0037

        class EQATTENUATION:
            """Attenuation of the equalizer. Use a gain setting of `1/1` (`EQAttenuation[1:0]=2'd3`)
            when VTRX+ is used.

                +-----------------------------------+------------------------------------------+
                | EQAttenuation[1:0]                |  Gain [V/V]                              |
                +===================================+==========================================+
                | 2'd0                              | 1/3                                      |
                +-----------------------------------+------------------------------------------+
                | 2'd1                              | 2/3                                      |
                +-----------------------------------+------------------------------------------+
                | 2'd2                              | 2/3                                      |
                +-----------------------------------+------------------------------------------+
                | 2'd3                              | 1/1                                      |
                +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EQCAP:
            """Capacitance select for the equalizer

            +-----------------------------------+------------------------------------------+
            | EQCap[1:0]                        | Capacitance [fF]                         |
            +===================================+==========================================+
            | 2'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | 70                                       |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | 70                                       |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | 140                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 2
            bit_mask = 3

            @staticmethod
            def validate(value):
                return value in range(4)

    class EQRES:
        """Resistance configuration for the equalizer"""

        address = 0x0038

        @staticmethod
        def __str__():
            return "EQRes"

        @staticmethod
        def __int__():
            return 0x0038

        class EQRES3:
            """Resistance to be used in the fourth stage of the data input equalizer

            +-----------------------------------+------------------------------------------+
            | EQRes3[1:0]                       | Resistance [kOhm]                        |
            +===================================+==========================================+
            | 2'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | 4.9                                      |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | 7.1                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 6
            length = 2
            bit_mask = 192

            @staticmethod
            def validate(value):
                return value in range(4)

        class EQRES2:
            """Resistance to be used in the third stage of the data input equalizer

            +-----------------------------------+------------------------------------------+
            | EQRes2[1:0]                       | Resistance [kOhm]                        |
            +===================================+==========================================+
            | 2'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | 4.9                                      |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | 7.1                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 4
            length = 2
            bit_mask = 48

            @staticmethod
            def validate(value):
                return value in range(4)

        class EQRES1:
            """Resistance to be used in the second stage of the data input equalizer

            +-----------------------------------+------------------------------------------+
            | EQRes1[1:0]                       | Resistance [kOhm]                        |
            +===================================+==========================================+
            | 2'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | 4.9                                      |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | 7.1                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 2
            length = 2
            bit_mask = 12

            @staticmethod
            def validate(value):
                return value in range(4)

        class EQRES0:
            """Resistance to be used in the first stage of the data input equalizer

            +-----------------------------------+------------------------------------------+
            | EQRes0[1:0]                       | Resistance [kOhm]                        |
            +===================================+==========================================+
            | 2'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | 4.9                                      |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | 7.1                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 2
            bit_mask = 3

            @staticmethod
            def validate(value):
                return value in range(4)

    class LDCONFIGH:
        """Line driver configuration register"""

        address = 0x0039

        @staticmethod
        def __str__():
            return "LDConfigH"

        @staticmethod
        def __int__():
            return 0x0039

        class LDEMPHASISENABLE:
            """Enable pre-emphasis in the line driver. The amplitude of the pre-emphasis is controlled by LDEmphasisAmp[6:0] and the duration by LDEmphasisShort."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class LDMODULATIONCURRENT:
            """Sets high-speed line driver modulation current: I_m  = 137 uA * LDModulationCurrent[6:0]"""

            offset = 0
            length = 7
            bit_mask = 127

            @staticmethod
            def validate(value):
                return value in range(128)

    class LDCONFIGL:
        """Line driver configuration register"""

        address = 0x003A

        @staticmethod
        def __str__():
            return "LDConfigL"

        @staticmethod
        def __int__():
            return 0x003A

        class LDEMPHASISSHORT:
            """Sets the duration of the pre-emphasis pulse. Please not that pre-emphasis has to be enabled (LDEmphasisEnable) for this field to have any impact."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class LDEMPHASISAMP:
            """Sets high-speed line driver pre-emphasis current: I_pre  = 137 uA * LDEmphasisAmp[6:0]. Please note that pre-emphasis has to be enabled (LDEmphasisEnable) for these registers bits to be active.

            -Note for the LDConfigH and LDConfigL registers: since the high-speed line driver contains an internal 100 Ohm "termination", the currents set by LDModulationCurrent[6:0] and LDEmphasisAmp[6:0] bits are shared between the internal and external load impedances. This needs to be taken into account when computing the output signal amplitude. To calculate the modulation amplitude the user should thus use the equivalent resistor value of 50 Ohm, that is, the internal 100 Ohm resistor in parallel with the external 100 Ohm termination impedance.
            """

            offset = 0
            length = 7
            bit_mask = 127

            @staticmethod
            def validate(value):
                return value in range(128)

    class REFCLK:
        """Configuration for the reference clock pad"""

        address = 0x003B

        @staticmethod
        def __str__():
            return "REFCLK"

        @staticmethod
        def __int__():
            return 0x003B

        class REFCLKFORCEENABLE:
            """Enable the reference clock pad regardless of the operation mode."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class REFCLKACBIAS:
            """Enables the common mode generation for the REFCLK."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class REFCLKTERM:
            """Enables the 100 Ohm termination for the REFCLK input."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class SCCONFIG:
        """Serial interface (IC/EC) configuration register."""

        address = 0x003C

        @staticmethod
        def __str__():
            return "SCCONFIG"

        @staticmethod
        def __int__():
            return 0x003C

        class SCPARITYCHECKDISABLE:
            """Disable parity check for incoming frames. If
            asserted, the data will be copied to registers regardless of parity check.
            """

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class RESETCONFIG:
        """Reset configuration."""

        address = 0x003D

        @staticmethod
        def __str__():
            return "RESETConfig"

        @staticmethod
        def __int__():
            return 0x003D

        class BODENABLE:
            """Enables brownout detector."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class BODLEVEL:
            """

            +---------------+------------------------------------------------------------+
            | BODlevel[2:0] | Brownout voltage level [V]                                 |
            +===============+============================================================+
            | 0             | 0.80                                                       |
            +---------------+------------------------------------------------------------+
            | 1             | 0.85                                                       |
            +---------------+------------------------------------------------------------+
            | 2             | 0.90                                                       |
            +---------------+------------------------------------------------------------+
            | 3             | 0.95                                                       |
            +---------------+------------------------------------------------------------+
            | 4             | 1.00                                                       |
            +---------------+------------------------------------------------------------+
            | 5             | 1.05                                                       |
            +---------------+------------------------------------------------------------+
            | 6             | 1.10                                                       |
            +---------------+------------------------------------------------------------+
            | 7             | 1.15                                                       |
            +---------------+------------------------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class PGCONFIG:
        """Power Good configuration."""

        address = 0x003E

        @staticmethod
        def __str__():
            return "PGConfig"

        @staticmethod
        def __int__():
            return 0x003E

        class PGENABLE:
            """Enable Power Good feature. For more details see :ref:`powerUpStateMachine`."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class PGLEVEL:
            """Enable Power Good feature. For more details see :ref:`powerUpStateMachine`.

            +--------------+------------------------------------------------------------+
            | PGLevel[2:0] | Voltage level [V]                                          |
            +==============+============================================================+
            | 0            | 0.80                                                       |
            +--------------+------------------------------------------------------------+
            | 1            | 0.85                                                       |
            +--------------+------------------------------------------------------------+
            | 2            | 0.90                                                       |
            +--------------+------------------------------------------------------------+
            | 3            | 0.95                                                       |
            +--------------+------------------------------------------------------------+
            | 4            | 1.00                                                       |
            +--------------+------------------------------------------------------------+
            | 5            | 1.05                                                       |
            +--------------+------------------------------------------------------------+
            | 6            | 1.10                                                       |
            +--------------+------------------------------------------------------------+
            | 7            | 1.15                                                       |
            +--------------+------------------------------------------------------------+

            """

            offset = 4
            length = 3
            bit_mask = 112

            @staticmethod
            def validate(value):
                return value in range(8)

        class PGDELAY:
            """

            +--------------+------------------------------------------------------------+
            | PGDelay[3:0] | Wait time                                                  |
            +==============+============================================================+
            | 0            | disabled                                                   |
            +--------------+------------------------------------------------------------+
            | 1            | 1 us                                                       |
            +--------------+------------------------------------------------------------+
            | 2            | 5 us                                                       |
            +--------------+------------------------------------------------------------+
            | 3            | 10 us                                                      |
            +--------------+------------------------------------------------------------+
            | 4            | 50 us                                                      |
            +--------------+------------------------------------------------------------+
            | 5            | 100 us                                                     |
            +--------------+------------------------------------------------------------+
            | 6            | 500 us                                                     |
            +--------------+------------------------------------------------------------+
            | 7            | 1 ms                                                       |
            +--------------+------------------------------------------------------------+
            | 8            | 5 ms                                                       |
            +--------------+------------------------------------------------------------+
            | 9            | 10 ms                                                      |
            +--------------+------------------------------------------------------------+
            | 10           | 20 ms                                                      |
            +--------------+------------------------------------------------------------+
            | 11           | 50 ms                                                      |
            +--------------+------------------------------------------------------------+
            | 12           | 100 ms                                                     |
            +--------------+------------------------------------------------------------+
            | 13           | 200 ms                                                     |
            +--------------+------------------------------------------------------------+
            | 14           | 500 ms                                                     |
            +--------------+------------------------------------------------------------+
            | 15           | 1 s                                                        |
            +--------------+------------------------------------------------------------+

            """

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class I2CMTRANSCONFIG:
        """Configuration register for the I2C transaction executed during initial power-up."""

        address = 0x003F

        @staticmethod
        def __str__():
            return "I2CMTransConfig"

        @staticmethod
        def __int__():
            return 0x003F

        class I2CMTRANSENABLE:
            """Enables the execution of I2C transaction during initial power-up"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CMTRANSCHANNEL:
            """Selects I2C master slave on which the transaction should be executed.

            ====================== ============================================================
            I2CMTransChannel[1:0]   I2C Master
            ====================== ============================================================
             2'd0                   I2CM0
             2'd1                   I2CM1
             2'd2                   I2CM2
             3'd3                   reserved
            ====================== ============================================================

            """

            offset = 5
            length = 2
            bit_mask = 96

            @staticmethod
            def validate(value):
                return value in range(4)

        class I2CMTRANSADDRESSEXT:
            """3 additional bits of address of slave to address in an I2C transaction; only used in commands with 10-bit addressing"""

            offset = 2
            length = 3
            bit_mask = 28

            @staticmethod
            def validate(value):
                return value in range(8)

        class I2CMTRANS10BITADDR:
            """If true, the I2C transaction executed during the initial power-up will use 10 bit addressing."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

    class I2CMTRANSADDRESS:
        """I2C slave address"""

        address = 0x0040

        @staticmethod
        def __str__():
            return "I2CMTransAddress"

        @staticmethod
        def __int__():
            return 0x0040

        class I2CMTRANSADDRESS:
            """Slave address to be used in the I2C transaction executed during initial power-up."""

            offset = 0
            length = 7
            bit_mask = 127

            @staticmethod
            def validate(value):
                return value in range(128)

    class I2CMTRANSCTRL:
        """Control register for the I2C transaction executed during initial power-up."""

        address = 0x0041

        @staticmethod
        def __str__():
            return "I2CMTransCtrl"

        @staticmethod
        def __int__():
            return 0x0041

        class I2CMTRANSCTRL:
            """Control register for the the I2C transaction executed during initial power-up. See :ref:`i2cm_control_register` for more details."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CMTRANSDATA0:
        """Data for the I2C transaction executed during initial power-up."""

        address = 0x0042

        @staticmethod
        def __str__():
            return "I2CMTransData0"

        @staticmethod
        def __int__():
            return 0x0042

        class I2CMTRANSDATA:
            """Byte 0 for the I2C transaction executed during initial power-up."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CMTRANSDATA1:
        """Data for the I2C transaction executed during initial power-up."""

        address = 0x0043

        @staticmethod
        def __str__():
            return "I2CMTransData1"

        @staticmethod
        def __int__():
            return 0x0043

        class I2CMTRANSDATA:
            """Byte 1 for the I2C transaction executed during initial power-up."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CMTRANSDATA2:
        """Data for the I2C transaction executed during initial power-up."""

        address = 0x0044

        @staticmethod
        def __str__():
            return "I2CMTransData2"

        @staticmethod
        def __int__():
            return 0x0044

        class I2CMTRANSDATA:
            """Byte 2 for the I2C transaction executed during initial power-up."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CMTRANSDATA3:
        """Data for the I2C transaction executed during initial power-up."""

        address = 0x0045

        @staticmethod
        def __str__():
            return "I2CMTransData3"

        @staticmethod
        def __int__():
            return 0x0045

        class I2CMTRANSDATA:
            """Byte 3 for the I2C transaction executed during initial power-up."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CMTRANSDATA4:
        """Data for the I2C transaction executed during initial power-up."""

        address = 0x0046

        @staticmethod
        def __str__():
            return "I2CMTransData4"

        @staticmethod
        def __int__():
            return 0x0046

        class I2CMTRANSDATA:
            """Byte 4 for the I2C transaction executed during initial power-up."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CMTRANSDATA5:
        """Data for the I2C transaction executed during initial power-up."""

        address = 0x0047

        @staticmethod
        def __str__():
            return "I2CMTransData5"

        @staticmethod
        def __int__():
            return 0x0047

        class I2CMTRANSDATA:
            """Byte 5 for the I2C transaction executed during initial power-up."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CMTRANSDATA6:
        """Data for the I2C transaction executed during initial power-up."""

        address = 0x0048

        @staticmethod
        def __str__():
            return "I2CMTransData6"

        @staticmethod
        def __int__():
            return 0x0048

        class I2CMTRANSDATA:
            """Byte 6 for the I2C transaction executed during initial power-up."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CMTRANSDATA7:
        """Data for the I2C transaction executed during initial power-up."""

        address = 0x0049

        @staticmethod
        def __str__():
            return "I2CMTransData7"

        @staticmethod
        def __int__():
            return 0x0049

        class I2CMTRANSDATA:
            """Byte 7 for the I2C transaction executed during initial power-up."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CMTRANSDATA8:
        """Data for the I2C transaction executed during initial power-up."""

        address = 0x004A

        @staticmethod
        def __str__():
            return "I2CMTransData8"

        @staticmethod
        def __int__():
            return 0x004A

        class I2CMTRANSDATA:
            """Byte 8 for the I2C transaction executed during initial power-up."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CMTRANSDATA9:
        """Data for the I2C transaction executed during initial power-up."""

        address = 0x004B

        @staticmethod
        def __str__():
            return "I2CMTransData9"

        @staticmethod
        def __int__():
            return 0x004B

        class I2CMTRANSDATA:
            """Byte 9 for the I2C transaction executed during initial power-up."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CMTRANSDATA10:
        """Data for the I2C transaction executed during initial power-up."""

        address = 0x004C

        @staticmethod
        def __str__():
            return "I2CMTransData10"

        @staticmethod
        def __int__():
            return 0x004C

        class I2CMTRANSDATA:
            """Byte 10 for the I2C transaction executed during initial power-up."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CMTRANSDATA11:
        """Data for the I2C transaction executed during initial power-up."""

        address = 0x004D

        @staticmethod
        def __str__():
            return "I2CMTransData11"

        @staticmethod
        def __int__():
            return 0x004D

        class I2CMTRANSDATA:
            """Byte 11 for the I2C transaction executed during initial power-up."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CMTRANSDATA12:
        """Data for the I2C transaction executed during initial power-up."""

        address = 0x004E

        @staticmethod
        def __str__():
            return "I2CMTransData12"

        @staticmethod
        def __int__():
            return 0x004E

        class I2CMTRANSDATA:
            """Byte 12 for the I2C transaction executed during initial power-up."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CMTRANSDATA13:
        """Data for the I2C transaction executed during initial power-up."""

        address = 0x004F

        @staticmethod
        def __str__():
            return "I2CMTransData13"

        @staticmethod
        def __int__():
            return 0x004F

        class I2CMTRANSDATA:
            """Byte 13 for the I2C transaction executed during initial power-up."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CMTRANSDATA14:
        """Data for the I2C transaction executed during initial power-up."""

        address = 0x0050

        @staticmethod
        def __str__():
            return "I2CMTransData14"

        @staticmethod
        def __int__():
            return 0x0050

        class I2CMTRANSDATA:
            """Byte 14 for the I2C transaction executed during initial power-up."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CMTRANSDATA15:
        """Data for the I2C transaction executed during initial power-up."""

        address = 0x0051

        @staticmethod
        def __str__():
            return "I2CMTransData15"

        @staticmethod
        def __int__():
            return 0x0051

        class I2CMTRANSDATA:
            """Byte 15 for the I2C transaction executed during initial power-up."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CMCLKDISABLE:
        """Disables the clock (enables the clock gating) of the I2CMasters"""

        address = 0x0052

        @staticmethod
        def __str__():
            return "I2CMClkDisable"

        @staticmethod
        def __int__():
            return 0x0052

        class I2CM2CLKDISABLE:
            """Disables the clock of channel 2 I2C master (enables the clock gating). One should generate a RSTi2cm2 after enabling the clock (disabling clock gate)."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM1CLKDISABLE:
            """Disables the clock of channel 1 I2C master (enables the clock gating). One should generate a RSTi2cm1 after enabling the clock (disabling clock gate)."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM0CLKDISABLE:
            """Disables the clock of channel 0 I2C master (enables the clock gating). One should generate a RSTi2cm0 after enabling the clock (disabling clock gate)."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class PIODIRH:
        """Direction control for Parallel IO port."""

        address = 0x0053

        @staticmethod
        def __str__():
            return "PIODirH"

        @staticmethod
        def __int__():
            return 0x0053

        class PIODIR:
            """

            =============== ============================================================
            PIODir[n]         Function
            =============== ============================================================
            1'b0             Pin configured as an input
            1'b1             Pin configured as an output
            =============== ============================================================


            """

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class PIODIRL:
        """Direction control for Parallel IO port."""

        address = 0x0054

        @staticmethod
        def __str__():
            return "PIODirL"

        @staticmethod
        def __int__():
            return 0x0054

        class PIODIR:
            """

            =============== ============================================================
            PIODir[n]         Function
            =============== ============================================================
            1'b0             Pin configured as an input
            1'b1             Pin configured as an output
            =============== ============================================================


            """

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class PIOOUTH:
        """Output control for Parallel IO port (when pin is configured as output)."""

        address = 0x0055

        @staticmethod
        def __str__():
            return "PIOOutH"

        @staticmethod
        def __int__():
            return 0x0055

        class PIOOUT:
            """

            =============== ============================================================
            PIOOut[n]        Output
            =============== ============================================================
            1'b0             Low
            1'b1             High
            =============== ============================================================


            """

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class PIOOUTL:
        """Output control for Parallel IO port (when pin is configured as output)."""

        address = 0x0056

        @staticmethod
        def __str__():
            return "PIOOutL"

        @staticmethod
        def __int__():
            return 0x0056

        class PIOOUT:
            """

            =============== ============================================================
            PIOOut[n]        Output
            =============== ============================================================
            1'b0             Low
            1'b1             High
            =============== ============================================================


            """

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class PIOPULLENAH:
        """Pull-up/pull-down control for Parallel IO port."""

        address = 0x0057

        @staticmethod
        def __str__():
            return "PIOPullEnaH"

        @staticmethod
        def __int__():
            return 0x0057

        class PIOPULLENABLE:
            """

            ================ ============================================================
            PIOPullEnable[n]  Pull-up/Pull-down resistor
            ================ ============================================================
            1'b0              Disabled
            1'b1              Enabled
            ================ ============================================================


            """

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class PIOPULLENAL:
        """Pull-up/pull-down control for Parallel IO port."""

        address = 0x0058

        @staticmethod
        def __str__():
            return "PIOPullEnaL"

        @staticmethod
        def __int__():
            return 0x0058

        class PIOPULLENABLE:
            """

            ================ ============================================================
            PIOPullEnable[n]  Pull-up/Pull-down resistor
            ================ ============================================================
            1'b0              Disabled
            1'b1              Enabled
            ================ ============================================================


            """

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class PIOUPDOWNH:
        """Selects pull-up or pull-down resistor for Parallel IO port when enabled in PIOPullEna register. See :ref:`cmos_io_characteristics` for more details."""

        address = 0x0059

        @staticmethod
        def __str__():
            return "PIOUpDownH"

        @staticmethod
        def __int__():
            return 0x0059

        class PIOUPDOWN:
            """

            ================ ============================================================
            PIOPullEnable[n]  Pull-up/Pull-down resistor
            ================ ============================================================
            1'b0              Pull-down
            1'b1              Pull-up
            ================ ============================================================


            """

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class PIOUPDOWNL:
        """Selects pull-up or pull-down resistor for Parallel IO port when enabled in PIOPullEna register. See :ref:`cmos_io_characteristics` for more details."""

        address = 0x005A

        @staticmethod
        def __str__():
            return "PIOUpDownL"

        @staticmethod
        def __int__():
            return 0x005A

        class PIOUPDOWN:
            """

            ================ ============================================================
            PIOPullEnable[n]  Pull-up/Pull-down resistor
            ================ ============================================================
            1'b0              Pull-down
            1'b1              Pull-up
            ================ ============================================================


            """

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class PIODRIVESTRENGTHH:
        """Selects driving strength for Parallel IO port when configured as an output. See :ref:`cmos_io_characteristics` for more details."""

        address = 0x005B

        @staticmethod
        def __str__():
            return "PIODriveStrengthH"

        @staticmethod
        def __int__():
            return 0x005B

        class PIODRIVESTRENGTH:
            """

            =================== ============================================================
            PIODriveStrength[n]  Drive Strength
            =================== ============================================================
            1'b0                 Low
            1'b1                 High
            =================== ============================================================


            """

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class PIODRIVESTRENGTHL:
        """Selects driving strength for Parallel IO port when configured as an output. See :ref:`cmos_io_characteristics` for more details."""

        address = 0x005C

        @staticmethod
        def __str__():
            return "PIODriveStrengthL"

        @staticmethod
        def __int__():
            return 0x005C

        class PIODRIVESTRENGTH:
            """

            =================== ============================================================
            PIODriveStrength[n]  Drive Strength
            =================== ============================================================
            1'b0                 Low
            1'b1                 High
            =================== ============================================================


            """

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class PS0CONFIG:
        """Main configuration of the phase-shifter clock 0"""

        address = 0x005D

        @staticmethod
        def __str__():
            return "PS0Config"

        @staticmethod
        def __int__():
            return 0x005D

        class PS0DELAY:
            """MSB of the delay select for clock 0. For more information check :ref:`REG_PS0DELAY` register."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class PS0ENABLEFINETUNE:
            """Enable fine deskewing for clock 0."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class PS0DRIVESTRENGTH:
            """Sets the driving strength for 0 clock output.

            +-----------------------------------+------------------------------------------+
            | PS0DriveStrength[2:0]             | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class PS0FREQ:
            """Sets the frequency for 0 clock output.

            +-----------------------------------+------------------------------------------+
            | PS0Freq[2:0]                      | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | Reserved                                 |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class PS0DELAY:
        """Delay of the phase-shifter clock 0"""

        address = 0x005E

        @staticmethod
        def __str__():
            return "PS0Delay"

        @staticmethod
        def __int__():
            return 0x005E

        class PS0DELAY:
            """Delay select for clock 0. Please note that that most significant bit of the PS0Delay field is stored in the :ref:`REG_PS0CONFIG` register."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class PS0OUTDRIVER:
        """Output driver configuration for the phase-shifter clock 0"""

        address = 0x005F

        @staticmethod
        def __str__():
            return "PS0OutDriver"

        @staticmethod
        def __int__():
            return 0x005F

        class PS0PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for phase-shifter 0 clock output.

            +-----------------------------------+------------------------------------------+
            | PS0PreEmphasisStrength[2:0]       | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class PS0PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 0.

            +-----------------------------------+------------------------------------------+
            | PS0PreEmphasisMode[1:0]           | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class PS0PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 0 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | PS0PreEmpahasisWidth[2:0]         | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class PS1CONFIG:
        """Main configuration of the phase-shifter clock 1"""

        address = 0x0060

        @staticmethod
        def __str__():
            return "PS1Config"

        @staticmethod
        def __int__():
            return 0x0060

        class PS1DELAY:
            """MSB of the delay select for clock 1. For more information check :ref:`REG_PS1DELAY` register."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class PS1ENABLEFINETUNE:
            """Enable fine deskewing for clock 1."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class PS1DRIVESTRENGTH:
            """Sets the driving strength for 1 clock output.

            +-----------------------------------+------------------------------------------+
            | PS1DriveStrength[2:0]             | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class PS1FREQ:
            """Sets the frequency for 1 clock output.

            +-----------------------------------+------------------------------------------+
            | PS1Freq[2:0]                      | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | Reserved                                 |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class PS1DELAY:
        """Delay of the phase-shifter clock 1"""

        address = 0x0061

        @staticmethod
        def __str__():
            return "PS1Delay"

        @staticmethod
        def __int__():
            return 0x0061

        class PS1DELAY:
            """Delay select for clock 1. Please note that that most significant bit of the PS1Delay field is stored in the :ref:`REG_PS1CONFIG` register."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class PS1OUTDRIVER:
        """Output driver configuration for the phase-shifter clock 1"""

        address = 0x0062

        @staticmethod
        def __str__():
            return "PS1OutDriver"

        @staticmethod
        def __int__():
            return 0x0062

        class PS1PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for phase-shifter 1 clock output.

            +-----------------------------------+------------------------------------------+
            | PS1PreEmphasisStrength[2:0]       | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class PS1PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 1.

            +-----------------------------------+------------------------------------------+
            | PS1PreEmphasisMode[1:0]           | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class PS1PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 1 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | PS1PreEmpahasisWidth[2:0]         | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class PS2CONFIG:
        """Main configuration of the phase-shifter clock 2"""

        address = 0x0063

        @staticmethod
        def __str__():
            return "PS2Config"

        @staticmethod
        def __int__():
            return 0x0063

        class PS2DELAY:
            """MSB of the delay select for clock 2. For more information check :ref:`REG_PS2DELAY` register."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class PS2ENABLEFINETUNE:
            """Enable fine deskewing for clock 2."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class PS2DRIVESTRENGTH:
            """Sets the driving strength for 2 clock output.

            +-----------------------------------+------------------------------------------+
            | PS2DriveStrength[2:0]             | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class PS2FREQ:
            """Sets the frequency for 2 clock output.

            +-----------------------------------+------------------------------------------+
            | PS2Freq[2:0]                      | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | Reserved                                 |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class PS2DELAY:
        """Delay of the phase-shifter clock 2"""

        address = 0x0064

        @staticmethod
        def __str__():
            return "PS2Delay"

        @staticmethod
        def __int__():
            return 0x0064

        class PS2DELAY:
            """Delay select for clock 2. Please note that that most significant bit of the PS2Delay field is stored in the :ref:`REG_PS2CONFIG` register."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class PS2OUTDRIVER:
        """Output driver configuration for the phase-shifter clock 2"""

        address = 0x0065

        @staticmethod
        def __str__():
            return "PS2OutDriver"

        @staticmethod
        def __int__():
            return 0x0065

        class PS2PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for phase-shifter 2 clock output.

            +-----------------------------------+------------------------------------------+
            | PS2PreEmphasisStrength[2:0]       | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class PS2PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 2.

            +-----------------------------------+------------------------------------------+
            | PS2PreEmphasisMode[1:0]           | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class PS2PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 2 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | PS2PreEmpahasisWidth[2:0]         | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class PS3CONFIG:
        """Main configuration of the phase-shifter clock 3"""

        address = 0x0066

        @staticmethod
        def __str__():
            return "PS3Config"

        @staticmethod
        def __int__():
            return 0x0066

        class PS3DELAY:
            """MSB of the delay select for clock 3. For more information check :ref:`REG_PS3DELAY` register."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class PS3ENABLEFINETUNE:
            """Enable fine deskewing for clock 3."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class PS3DRIVESTRENGTH:
            """Sets the driving strength for 3 clock output.

            +-----------------------------------+------------------------------------------+
            | PS3DriveStrength[2:0]             | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class PS3FREQ:
            """Sets the frequency for 3 clock output.

            +-----------------------------------+------------------------------------------+
            | PS3Freq[2:0]                      | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | Reserved                                 |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class PS3DELAY:
        """Delay of the phase-shifter clock 3"""

        address = 0x0067

        @staticmethod
        def __str__():
            return "PS3Delay"

        @staticmethod
        def __int__():
            return 0x0067

        class PS3DELAY:
            """Delay select for clock 3. Please note that that most significant bit of the PS3Delay field is stored in the :ref:`REG_PS3CONFIG` register."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class PS3OUTDRIVER:
        """Output driver configuration for the phase-shifter clock 3"""

        address = 0x0068

        @staticmethod
        def __str__():
            return "PS3OutDriver"

        @staticmethod
        def __int__():
            return 0x0068

        class PS3PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for phase-shifter 3 clock output.

            +-----------------------------------+------------------------------------------+
            | PS3PreEmphasisStrength[2:0]       | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class PS3PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 3.

            +-----------------------------------+------------------------------------------+
            | PS3PreEmphasisMode[1:0]           | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class PS3PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 3 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | PS3PreEmpahasisWidth[2:0]         | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class PSLOWRES:
        """Power supply resistance control for phase-shifter drivers."""

        address = 0x0069

        @staticmethod
        def __str__():
            return "PSLowRes"

        @staticmethod
        def __int__():
            return 0x0069

        class PS3LOWRES:
            """Decreases the power supply filter resistance in PS3 driver."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class PS2LOWRES:
            """Decreases the power supply filter resistance in PS2 driver."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class PS1LOWRES:
            """Decreases the power supply filter resistance in PS1 driver."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class PS0LOWRES:
            """Decreases the power supply filter resistance in PS0 driver."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class DACCONFIGH:
        """DACs configuration register."""

        address = 0x006A

        @staticmethod
        def __str__():
            return "DACConfigH"

        @staticmethod
        def __int__():
            return 0x006A

        class VOLDACENABLE:
            """Enable voltage DAC."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class CURDACENABLE:
            """Enables current DAC."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class VOLDACVALUE:
            """Sets output voltage for the Voltage DAC."""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class DACCONFIGL:
        """DACs configuration register."""

        address = 0x006B

        @staticmethod
        def __str__():
            return "DACConfigL"

        @staticmethod
        def __int__():
            return 0x006B

        class VOLDACVALUE:
            """Sets output voltage for the Voltage DAC."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class CURDACVALUE:
        """Output current"""

        address = 0x006C

        @staticmethod
        def __str__():
            return "CURDACValue"

        @staticmethod
        def __int__():
            return 0x006C

        class CURDACSELECT:
            """Sets output current for the current DAC. Current = CURDACSelect * XX uA."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class CURDACCHN:
        """Current DAC output multiplexer."""

        address = 0x006D

        @staticmethod
        def __str__():
            return "CURDACCHN"

        @staticmethod
        def __int__():
            return 0x006D

        class CURDACCHNENABLE:
            """Setting Nth bit in this register attaches current DAC to ADCN pin.
            Current source can be attached to any number of channels.

            """

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class EPCLK0CHNCNTRH:
        """Configuration of clock output 0"""

        address = 0x006E

        @staticmethod
        def __str__():
            return "EPCLK0ChnCntrH"

        @staticmethod
        def __int__():
            return 0x006E

        class EPCLK0LOWRES:
            """Decreases the power supply filter resistance in EPCLK0 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK0INVERT:
            """Inverts 0 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK0DRIVESTRENGTH:
            """Sets the driving strength for 0 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK0DriveStrength[2:0]          | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK0FREQ:
            """Sets the frequency for 0 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK0Freq[2:0]                   | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN00 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK0CHNCNTRL:
        """Configuration of clock output 0"""

        address = 0x006F

        @staticmethod
        def __str__():
            return "EPCLK0ChnCntrL"

        @staticmethod
        def __int__():
            return 0x006F

        class EPCLK0PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 0 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK0PreEmphasisStrength[2:0]    | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK0PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 0.

            +-----------------------------------+------------------------------------------+
            | EPCLK0PreEmphasisMode[1:0]        | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK0PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 0 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK0PreEmpahasisWidth[2:0]      | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK1CHNCNTRH:
        """Configuration of clock output 1"""

        address = 0x0070

        @staticmethod
        def __str__():
            return "EPCLK1ChnCntrH"

        @staticmethod
        def __int__():
            return 0x0070

        class EPCLK1LOWRES:
            """Decreases the power supply filter resistance in EPCLK1 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK1INVERT:
            """Inverts 1 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK1DRIVESTRENGTH:
            """Sets the driving strength for 1 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK1DriveStrength[2:0]          | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK1FREQ:
            """Sets the frequency for 1 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK1Freq[2:0]                   | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN01 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK1CHNCNTRL:
        """Configuration of clock output 1"""

        address = 0x0071

        @staticmethod
        def __str__():
            return "EPCLK1ChnCntrL"

        @staticmethod
        def __int__():
            return 0x0071

        class EPCLK1PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 1 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK1PreEmphasisStrength[2:0]    | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK1PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 1.

            +-----------------------------------+------------------------------------------+
            | EPCLK1PreEmphasisMode[1:0]        | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK1PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 1 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK1PreEmpahasisWidth[2:0]      | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK2CHNCNTRH:
        """Configuration of clock output 2"""

        address = 0x0072

        @staticmethod
        def __str__():
            return "EPCLK2ChnCntrH"

        @staticmethod
        def __int__():
            return 0x0072

        class EPCLK2LOWRES:
            """Decreases the power supply filter resistance in EPCLK2 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK2INVERT:
            """Inverts 2 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK2DRIVESTRENGTH:
            """Sets the driving strength for 2 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK2DriveStrength[2:0]          | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK2FREQ:
            """Sets the frequency for 2 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK2Freq[2:0]                   | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN02 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK2CHNCNTRL:
        """Configuration of clock output 2"""

        address = 0x0073

        @staticmethod
        def __str__():
            return "EPCLK2ChnCntrL"

        @staticmethod
        def __int__():
            return 0x0073

        class EPCLK2PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 2 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK2PreEmphasisStrength[2:0]    | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK2PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 2.

            +-----------------------------------+------------------------------------------+
            | EPCLK2PreEmphasisMode[1:0]        | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK2PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 2 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK2PreEmpahasisWidth[2:0]      | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK3CHNCNTRH:
        """Configuration of clock output 3"""

        address = 0x0074

        @staticmethod
        def __str__():
            return "EPCLK3ChnCntrH"

        @staticmethod
        def __int__():
            return 0x0074

        class EPCLK3LOWRES:
            """Decreases the power supply filter resistance in EPCLK3 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK3INVERT:
            """Inverts 3 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK3DRIVESTRENGTH:
            """Sets the driving strength for 3 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK3DriveStrength[2:0]          | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK3FREQ:
            """Sets the frequency for 3 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK3Freq[2:0]                   | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN03 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK3CHNCNTRL:
        """Configuration of clock output 3"""

        address = 0x0075

        @staticmethod
        def __str__():
            return "EPCLK3ChnCntrL"

        @staticmethod
        def __int__():
            return 0x0075

        class EPCLK3PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 3 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK3PreEmphasisStrength[2:0]    | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK3PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 3.

            +-----------------------------------+------------------------------------------+
            | EPCLK3PreEmphasisMode[1:0]        | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK3PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 3 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK3PreEmpahasisWidth[2:0]      | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK4CHNCNTRH:
        """Configuration of clock output 4"""

        address = 0x0076

        @staticmethod
        def __str__():
            return "EPCLK4ChnCntrH"

        @staticmethod
        def __int__():
            return 0x0076

        class EPCLK4LOWRES:
            """Decreases the power supply filter resistance in EPCLK4 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK4INVERT:
            """Inverts 4 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK4DRIVESTRENGTH:
            """Sets the driving strength for 4 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK4DriveStrength[2:0]          | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK4FREQ:
            """Sets the frequency for 4 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK4Freq[2:0]                   | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN10 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK4CHNCNTRL:
        """Configuration of clock output 4"""

        address = 0x0077

        @staticmethod
        def __str__():
            return "EPCLK4ChnCntrL"

        @staticmethod
        def __int__():
            return 0x0077

        class EPCLK4PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 4 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK4PreEmphasisStrength[2:0]    | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK4PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 4.

            +-----------------------------------+------------------------------------------+
            | EPCLK4PreEmphasisMode[1:0]        | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK4PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 4 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK4PreEmpahasisWidth[2:0]      | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK5CHNCNTRH:
        """Configuration of clock output 5"""

        address = 0x0078

        @staticmethod
        def __str__():
            return "EPCLK5ChnCntrH"

        @staticmethod
        def __int__():
            return 0x0078

        class EPCLK5LOWRES:
            """Decreases the power supply filter resistance in EPCLK5 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK5INVERT:
            """Inverts 5 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK5DRIVESTRENGTH:
            """Sets the driving strength for 5 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK5DriveStrength[2:0]          | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK5FREQ:
            """Sets the frequency for 5 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK5Freq[2:0]                   | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN11 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK5CHNCNTRL:
        """Configuration of clock output 5"""

        address = 0x0079

        @staticmethod
        def __str__():
            return "EPCLK5ChnCntrL"

        @staticmethod
        def __int__():
            return 0x0079

        class EPCLK5PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 5 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK5PreEmphasisStrength[2:0]    | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK5PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 5.

            +-----------------------------------+------------------------------------------+
            | EPCLK5PreEmphasisMode[1:0]        | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK5PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 5 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK5PreEmpahasisWidth[2:0]      | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK6CHNCNTRH:
        """Configuration of clock output 6"""

        address = 0x007A

        @staticmethod
        def __str__():
            return "EPCLK6ChnCntrH"

        @staticmethod
        def __int__():
            return 0x007A

        class EPCLK6LOWRES:
            """Decreases the power supply filter resistance in EPCLK6 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK6INVERT:
            """Inverts 6 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK6DRIVESTRENGTH:
            """Sets the driving strength for 6 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK6DriveStrength[2:0]          | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK6FREQ:
            """Sets the frequency for 6 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK6Freq[2:0]                   | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN12 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK6CHNCNTRL:
        """Configuration of clock output 6"""

        address = 0x007B

        @staticmethod
        def __str__():
            return "EPCLK6ChnCntrL"

        @staticmethod
        def __int__():
            return 0x007B

        class EPCLK6PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 6 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK6PreEmphasisStrength[2:0]    | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK6PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 6.

            +-----------------------------------+------------------------------------------+
            | EPCLK6PreEmphasisMode[1:0]        | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK6PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 6 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK6PreEmpahasisWidth[2:0]      | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK7CHNCNTRH:
        """Configuration of clock output 7"""

        address = 0x007C

        @staticmethod
        def __str__():
            return "EPCLK7ChnCntrH"

        @staticmethod
        def __int__():
            return 0x007C

        class EPCLK7LOWRES:
            """Decreases the power supply filter resistance in EPCLK7 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK7INVERT:
            """Inverts 7 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK7DRIVESTRENGTH:
            """Sets the driving strength for 7 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK7DriveStrength[2:0]          | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK7FREQ:
            """Sets the frequency for 7 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK7Freq[2:0]                   | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN13 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK7CHNCNTRL:
        """Configuration of clock output 7"""

        address = 0x007D

        @staticmethod
        def __str__():
            return "EPCLK7ChnCntrL"

        @staticmethod
        def __int__():
            return 0x007D

        class EPCLK7PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 7 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK7PreEmphasisStrength[2:0]    | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK7PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 7.

            +-----------------------------------+------------------------------------------+
            | EPCLK7PreEmphasisMode[1:0]        | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK7PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 7 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK7PreEmpahasisWidth[2:0]      | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK8CHNCNTRH:
        """Configuration of clock output 8"""

        address = 0x007E

        @staticmethod
        def __str__():
            return "EPCLK8ChnCntrH"

        @staticmethod
        def __int__():
            return 0x007E

        class EPCLK8LOWRES:
            """Decreases the power supply filter resistance in EPCLK8 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK8INVERT:
            """Inverts 8 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK8DRIVESTRENGTH:
            """Sets the driving strength for 8 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK8DriveStrength[2:0]          | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK8FREQ:
            """Sets the frequency for 8 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK8Freq[2:0]                   | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN20 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK8CHNCNTRL:
        """Configuration of clock output 8"""

        address = 0x007F

        @staticmethod
        def __str__():
            return "EPCLK8ChnCntrL"

        @staticmethod
        def __int__():
            return 0x007F

        class EPCLK8PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 8 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK8PreEmphasisStrength[2:0]    | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK8PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 8.

            +-----------------------------------+------------------------------------------+
            | EPCLK8PreEmphasisMode[1:0]        | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK8PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 8 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK8PreEmpahasisWidth[2:0]      | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK9CHNCNTRH:
        """Configuration of clock output 9"""

        address = 0x0080

        @staticmethod
        def __str__():
            return "EPCLK9ChnCntrH"

        @staticmethod
        def __int__():
            return 0x0080

        class EPCLK9LOWRES:
            """Decreases the power supply filter resistance in EPCLK9 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK9INVERT:
            """Inverts 9 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK9DRIVESTRENGTH:
            """Sets the driving strength for 9 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK9DriveStrength[2:0]          | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK9FREQ:
            """Sets the frequency for 9 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK9Freq[2:0]                   | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN21 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK9CHNCNTRL:
        """Configuration of clock output 9"""

        address = 0x0081

        @staticmethod
        def __str__():
            return "EPCLK9ChnCntrL"

        @staticmethod
        def __int__():
            return 0x0081

        class EPCLK9PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 9 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK9PreEmphasisStrength[2:0]    | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK9PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 9.

            +-----------------------------------+------------------------------------------+
            | EPCLK9PreEmphasisMode[1:0]        | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK9PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 9 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK9PreEmpahasisWidth[2:0]      | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK10CHNCNTRH:
        """Configuration of clock output 10"""

        address = 0x0082

        @staticmethod
        def __str__():
            return "EPCLK10ChnCntrH"

        @staticmethod
        def __int__():
            return 0x0082

        class EPCLK10LOWRES:
            """Decreases the power supply filter resistance in EPCLK10 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK10INVERT:
            """Inverts 10 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK10DRIVESTRENGTH:
            """Sets the driving strength for 10 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK10DriveStrength[2:0]         | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK10FREQ:
            """Sets the frequency for 10 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK10Freq[2:0]                  | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN22 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK10CHNCNTRL:
        """Configuration of clock output 10"""

        address = 0x0083

        @staticmethod
        def __str__():
            return "EPCLK10ChnCntrL"

        @staticmethod
        def __int__():
            return 0x0083

        class EPCLK10PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 10 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK10PreEmphasisStrength[2:0]   | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK10PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 10.

            +-----------------------------------+------------------------------------------+
            | EPCLK10PreEmphasisMode[1:0]       | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK10PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 10 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK10PreEmpahasisWidth[2:0]     | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK11CHNCNTRH:
        """Configuration of clock output 11"""

        address = 0x0084

        @staticmethod
        def __str__():
            return "EPCLK11ChnCntrH"

        @staticmethod
        def __int__():
            return 0x0084

        class EPCLK11LOWRES:
            """Decreases the power supply filter resistance in EPCLK11 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK11INVERT:
            """Inverts 11 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK11DRIVESTRENGTH:
            """Sets the driving strength for 11 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK11DriveStrength[2:0]         | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK11FREQ:
            """Sets the frequency for 11 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK11Freq[2:0]                  | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN23 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK11CHNCNTRL:
        """Configuration of clock output 11"""

        address = 0x0085

        @staticmethod
        def __str__():
            return "EPCLK11ChnCntrL"

        @staticmethod
        def __int__():
            return 0x0085

        class EPCLK11PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 11 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK11PreEmphasisStrength[2:0]   | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK11PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 11.

            +-----------------------------------+------------------------------------------+
            | EPCLK11PreEmphasisMode[1:0]       | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK11PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 11 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK11PreEmpahasisWidth[2:0]     | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK12CHNCNTRH:
        """Configuration of clock output 12"""

        address = 0x0086

        @staticmethod
        def __str__():
            return "EPCLK12ChnCntrH"

        @staticmethod
        def __int__():
            return 0x0086

        class EPCLK12LOWRES:
            """Decreases the power supply filter resistance in EPCLK12 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK12INVERT:
            """Inverts 12 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK12DRIVESTRENGTH:
            """Sets the driving strength for 12 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK12DriveStrength[2:0]         | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK12FREQ:
            """Sets the frequency for 12 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK12Freq[2:0]                  | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN30 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK12CHNCNTRL:
        """Configuration of clock output 12"""

        address = 0x0087

        @staticmethod
        def __str__():
            return "EPCLK12ChnCntrL"

        @staticmethod
        def __int__():
            return 0x0087

        class EPCLK12PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 12 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK12PreEmphasisStrength[2:0]   | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK12PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 12.

            +-----------------------------------+------------------------------------------+
            | EPCLK12PreEmphasisMode[1:0]       | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK12PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 12 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK12PreEmpahasisWidth[2:0]     | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK13CHNCNTRH:
        """Configuration of clock output 13"""

        address = 0x0088

        @staticmethod
        def __str__():
            return "EPCLK13ChnCntrH"

        @staticmethod
        def __int__():
            return 0x0088

        class EPCLK13LOWRES:
            """Decreases the power supply filter resistance in EPCLK13 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK13INVERT:
            """Inverts 13 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK13DRIVESTRENGTH:
            """Sets the driving strength for 13 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK13DriveStrength[2:0]         | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK13FREQ:
            """Sets the frequency for 13 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK13Freq[2:0]                  | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN31 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK13CHNCNTRL:
        """Configuration of clock output 13"""

        address = 0x0089

        @staticmethod
        def __str__():
            return "EPCLK13ChnCntrL"

        @staticmethod
        def __int__():
            return 0x0089

        class EPCLK13PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 13 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK13PreEmphasisStrength[2:0]   | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK13PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 13.

            +-----------------------------------+------------------------------------------+
            | EPCLK13PreEmphasisMode[1:0]       | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK13PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 13 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK13PreEmpahasisWidth[2:0]     | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK14CHNCNTRH:
        """Configuration of clock output 14"""

        address = 0x008A

        @staticmethod
        def __str__():
            return "EPCLK14ChnCntrH"

        @staticmethod
        def __int__():
            return 0x008A

        class EPCLK14LOWRES:
            """Decreases the power supply filter resistance in EPCLK14 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK14INVERT:
            """Inverts 14 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK14DRIVESTRENGTH:
            """Sets the driving strength for 14 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK14DriveStrength[2:0]         | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK14FREQ:
            """Sets the frequency for 14 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK14Freq[2:0]                  | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN32 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK14CHNCNTRL:
        """Configuration of clock output 14"""

        address = 0x008B

        @staticmethod
        def __str__():
            return "EPCLK14ChnCntrL"

        @staticmethod
        def __int__():
            return 0x008B

        class EPCLK14PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 14 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK14PreEmphasisStrength[2:0]   | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK14PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 14.

            +-----------------------------------+------------------------------------------+
            | EPCLK14PreEmphasisMode[1:0]       | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK14PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 14 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK14PreEmpahasisWidth[2:0]     | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK15CHNCNTRH:
        """Configuration of clock output 15"""

        address = 0x008C

        @staticmethod
        def __str__():
            return "EPCLK15ChnCntrH"

        @staticmethod
        def __int__():
            return 0x008C

        class EPCLK15LOWRES:
            """Decreases the power supply filter resistance in EPCLK15 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK15INVERT:
            """Inverts 15 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK15DRIVESTRENGTH:
            """Sets the driving strength for 15 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK15DriveStrength[2:0]         | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK15FREQ:
            """Sets the frequency for 15 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK15Freq[2:0]                  | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN33 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK15CHNCNTRL:
        """Configuration of clock output 15"""

        address = 0x008D

        @staticmethod
        def __str__():
            return "EPCLK15ChnCntrL"

        @staticmethod
        def __int__():
            return 0x008D

        class EPCLK15PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 15 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK15PreEmphasisStrength[2:0]   | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK15PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 15.

            +-----------------------------------+------------------------------------------+
            | EPCLK15PreEmphasisMode[1:0]       | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK15PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 15 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK15PreEmpahasisWidth[2:0]     | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK16CHNCNTRH:
        """Configuration of clock output 16"""

        address = 0x008E

        @staticmethod
        def __str__():
            return "EPCLK16ChnCntrH"

        @staticmethod
        def __int__():
            return 0x008E

        class EPCLK16LOWRES:
            """Decreases the power supply filter resistance in EPCLK16 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK16INVERT:
            """Inverts 16 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK16DRIVESTRENGTH:
            """Sets the driving strength for 16 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK16DriveStrength[2:0]         | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK16FREQ:
            """Sets the frequency for 16 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK16Freq[2:0]                  | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN40 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK16CHNCNTRL:
        """Configuration of clock output 16"""

        address = 0x008F

        @staticmethod
        def __str__():
            return "EPCLK16ChnCntrL"

        @staticmethod
        def __int__():
            return 0x008F

        class EPCLK16PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 16 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK16PreEmphasisStrength[2:0]   | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK16PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 16.

            +-----------------------------------+------------------------------------------+
            | EPCLK16PreEmphasisMode[1:0]       | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK16PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 16 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK16PreEmpahasisWidth[2:0]     | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK17CHNCNTRH:
        """Configuration of clock output 17"""

        address = 0x0090

        @staticmethod
        def __str__():
            return "EPCLK17ChnCntrH"

        @staticmethod
        def __int__():
            return 0x0090

        class EPCLK17LOWRES:
            """Decreases the power supply filter resistance in EPCLK17 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK17INVERT:
            """Inverts 17 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK17DRIVESTRENGTH:
            """Sets the driving strength for 17 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK17DriveStrength[2:0]         | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK17FREQ:
            """Sets the frequency for 17 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK17Freq[2:0]                  | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN41 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK17CHNCNTRL:
        """Configuration of clock output 17"""

        address = 0x0091

        @staticmethod
        def __str__():
            return "EPCLK17ChnCntrL"

        @staticmethod
        def __int__():
            return 0x0091

        class EPCLK17PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 17 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK17PreEmphasisStrength[2:0]   | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK17PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 17.

            +-----------------------------------+------------------------------------------+
            | EPCLK17PreEmphasisMode[1:0]       | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK17PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 17 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK17PreEmpahasisWidth[2:0]     | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK18CHNCNTRH:
        """Configuration of clock output 18"""

        address = 0x0092

        @staticmethod
        def __str__():
            return "EPCLK18ChnCntrH"

        @staticmethod
        def __int__():
            return 0x0092

        class EPCLK18LOWRES:
            """Decreases the power supply filter resistance in EPCLK18 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK18INVERT:
            """Inverts 18 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK18DRIVESTRENGTH:
            """Sets the driving strength for 18 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK18DriveStrength[2:0]         | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK18FREQ:
            """Sets the frequency for 18 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK18Freq[2:0]                  | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN42 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK18CHNCNTRL:
        """Configuration of clock output 18"""

        address = 0x0093

        @staticmethod
        def __str__():
            return "EPCLK18ChnCntrL"

        @staticmethod
        def __int__():
            return 0x0093

        class EPCLK18PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 18 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK18PreEmphasisStrength[2:0]   | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK18PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 18.

            +-----------------------------------+------------------------------------------+
            | EPCLK18PreEmphasisMode[1:0]       | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK18PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 18 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK18PreEmpahasisWidth[2:0]     | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK19CHNCNTRH:
        """Configuration of clock output 19"""

        address = 0x0094

        @staticmethod
        def __str__():
            return "EPCLK19ChnCntrH"

        @staticmethod
        def __int__():
            return 0x0094

        class EPCLK19LOWRES:
            """Decreases the power supply filter resistance in EPCLK19 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK19INVERT:
            """Inverts 19 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK19DRIVESTRENGTH:
            """Sets the driving strength for 19 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK19DriveStrength[2:0]         | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK19FREQ:
            """Sets the frequency for 19 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK19Freq[2:0]                  | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN43 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK19CHNCNTRL:
        """Configuration of clock output 19"""

        address = 0x0095

        @staticmethod
        def __str__():
            return "EPCLK19ChnCntrL"

        @staticmethod
        def __int__():
            return 0x0095

        class EPCLK19PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 19 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK19PreEmphasisStrength[2:0]   | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK19PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 19.

            +-----------------------------------+------------------------------------------+
            | EPCLK19PreEmphasisMode[1:0]       | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK19PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 19 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK19PreEmpahasisWidth[2:0]     | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK20CHNCNTRH:
        """Configuration of clock output 20"""

        address = 0x0096

        @staticmethod
        def __str__():
            return "EPCLK20ChnCntrH"

        @staticmethod
        def __int__():
            return 0x0096

        class EPCLK20LOWRES:
            """Decreases the power supply filter resistance in EPCLK20 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK20INVERT:
            """Inverts 20 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK20DRIVESTRENGTH:
            """Sets the driving strength for 20 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK20DriveStrength[2:0]         | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK20FREQ:
            """Sets the frequency for 20 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK20Freq[2:0]                  | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN50 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK20CHNCNTRL:
        """Configuration of clock output 20"""

        address = 0x0097

        @staticmethod
        def __str__():
            return "EPCLK20ChnCntrL"

        @staticmethod
        def __int__():
            return 0x0097

        class EPCLK20PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 20 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK20PreEmphasisStrength[2:0]   | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK20PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 20.

            +-----------------------------------+------------------------------------------+
            | EPCLK20PreEmphasisMode[1:0]       | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK20PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 20 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK20PreEmpahasisWidth[2:0]     | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK21CHNCNTRH:
        """Configuration of clock output 21"""

        address = 0x0098

        @staticmethod
        def __str__():
            return "EPCLK21ChnCntrH"

        @staticmethod
        def __int__():
            return 0x0098

        class EPCLK21LOWRES:
            """Decreases the power supply filter resistance in EPCLK21 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK21INVERT:
            """Inverts 21 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK21DRIVESTRENGTH:
            """Sets the driving strength for 21 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK21DriveStrength[2:0]         | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK21FREQ:
            """Sets the frequency for 21 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK21Freq[2:0]                  | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN51 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK21CHNCNTRL:
        """Configuration of clock output 21"""

        address = 0x0099

        @staticmethod
        def __str__():
            return "EPCLK21ChnCntrL"

        @staticmethod
        def __int__():
            return 0x0099

        class EPCLK21PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 21 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK21PreEmphasisStrength[2:0]   | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK21PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 21.

            +-----------------------------------+------------------------------------------+
            | EPCLK21PreEmphasisMode[1:0]       | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK21PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 21 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK21PreEmpahasisWidth[2:0]     | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK22CHNCNTRH:
        """Configuration of clock output 22"""

        address = 0x009A

        @staticmethod
        def __str__():
            return "EPCLK22ChnCntrH"

        @staticmethod
        def __int__():
            return 0x009A

        class EPCLK22LOWRES:
            """Decreases the power supply filter resistance in EPCLK22 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK22INVERT:
            """Inverts 22 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK22DRIVESTRENGTH:
            """Sets the driving strength for 22 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK22DriveStrength[2:0]         | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK22FREQ:
            """Sets the frequency for 22 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK22Freq[2:0]                  | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN52 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK22CHNCNTRL:
        """Configuration of clock output 22"""

        address = 0x009B

        @staticmethod
        def __str__():
            return "EPCLK22ChnCntrL"

        @staticmethod
        def __int__():
            return 0x009B

        class EPCLK22PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 22 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK22PreEmphasisStrength[2:0]   | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK22PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 22.

            +-----------------------------------+------------------------------------------+
            | EPCLK22PreEmphasisMode[1:0]       | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK22PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 22 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK22PreEmpahasisWidth[2:0]     | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK23CHNCNTRH:
        """Configuration of clock output 23"""

        address = 0x009C

        @staticmethod
        def __str__():
            return "EPCLK23ChnCntrH"

        @staticmethod
        def __int__():
            return 0x009C

        class EPCLK23LOWRES:
            """Decreases the power supply filter resistance in EPCLK23 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK23INVERT:
            """Inverts 23 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK23DRIVESTRENGTH:
            """Sets the driving strength for 23 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK23DriveStrength[2:0]         | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK23FREQ:
            """Sets the frequency for 23 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK23Freq[2:0]                  | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN53 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK23CHNCNTRL:
        """Configuration of clock output 23"""

        address = 0x009D

        @staticmethod
        def __str__():
            return "EPCLK23ChnCntrL"

        @staticmethod
        def __int__():
            return 0x009D

        class EPCLK23PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 23 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK23PreEmphasisStrength[2:0]   | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK23PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 23.

            +-----------------------------------+------------------------------------------+
            | EPCLK23PreEmphasisMode[1:0]       | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK23PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 23 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK23PreEmpahasisWidth[2:0]     | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK24CHNCNTRH:
        """Configuration of clock output 24"""

        address = 0x009E

        @staticmethod
        def __str__():
            return "EPCLK24ChnCntrH"

        @staticmethod
        def __int__():
            return 0x009E

        class EPCLK24LOWRES:
            """Decreases the power supply filter resistance in EPCLK24 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK24INVERT:
            """Inverts 24 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK24DRIVESTRENGTH:
            """Sets the driving strength for 24 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK24DriveStrength[2:0]         | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK24FREQ:
            """Sets the frequency for 24 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK24Freq[2:0]                  | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN60 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK24CHNCNTRL:
        """Configuration of clock output 24"""

        address = 0x009F

        @staticmethod
        def __str__():
            return "EPCLK24ChnCntrL"

        @staticmethod
        def __int__():
            return 0x009F

        class EPCLK24PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 24 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK24PreEmphasisStrength[2:0]   | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK24PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 24.

            +-----------------------------------+------------------------------------------+
            | EPCLK24PreEmphasisMode[1:0]       | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK24PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 24 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK24PreEmpahasisWidth[2:0]     | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK25CHNCNTRH:
        """Configuration of clock output 25"""

        address = 0x00A0

        @staticmethod
        def __str__():
            return "EPCLK25ChnCntrH"

        @staticmethod
        def __int__():
            return 0x00A0

        class EPCLK25LOWRES:
            """Decreases the power supply filter resistance in EPCLK25 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK25INVERT:
            """Inverts 25 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK25DRIVESTRENGTH:
            """Sets the driving strength for 25 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK25DriveStrength[2:0]         | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK25FREQ:
            """Sets the frequency for 25 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK25Freq[2:0]                  | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN61 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK25CHNCNTRL:
        """Configuration of clock output 25"""

        address = 0x00A1

        @staticmethod
        def __str__():
            return "EPCLK25ChnCntrL"

        @staticmethod
        def __int__():
            return 0x00A1

        class EPCLK25PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 25 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK25PreEmphasisStrength[2:0]   | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK25PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 25.

            +-----------------------------------+------------------------------------------+
            | EPCLK25PreEmphasisMode[1:0]       | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK25PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 25 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK25PreEmpahasisWidth[2:0]     | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK26CHNCNTRH:
        """Configuration of clock output 26"""

        address = 0x00A2

        @staticmethod
        def __str__():
            return "EPCLK26ChnCntrH"

        @staticmethod
        def __int__():
            return 0x00A2

        class EPCLK26LOWRES:
            """Decreases the power supply filter resistance in EPCLK26 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK26INVERT:
            """Inverts 26 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK26DRIVESTRENGTH:
            """Sets the driving strength for 26 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK26DriveStrength[2:0]         | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK26FREQ:
            """Sets the frequency for 26 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK26Freq[2:0]                  | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN62 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK26CHNCNTRL:
        """Configuration of clock output 26"""

        address = 0x00A3

        @staticmethod
        def __str__():
            return "EPCLK26ChnCntrL"

        @staticmethod
        def __int__():
            return 0x00A3

        class EPCLK26PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 26 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK26PreEmphasisStrength[2:0]   | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK26PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 26.

            +-----------------------------------+------------------------------------------+
            | EPCLK26PreEmphasisMode[1:0]       | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK26PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 26 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK26PreEmpahasisWidth[2:0]     | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK27CHNCNTRH:
        """Configuration of clock output 27"""

        address = 0x00A4

        @staticmethod
        def __str__():
            return "EPCLK27ChnCntrH"

        @staticmethod
        def __int__():
            return 0x00A4

        class EPCLK27LOWRES:
            """Decreases the power supply filter resistance in EPCLK27 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK27INVERT:
            """Inverts 27 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK27DRIVESTRENGTH:
            """Sets the driving strength for 27 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK27DriveStrength[2:0]         | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK27FREQ:
            """Sets the frequency for 27 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK27Freq[2:0]                  | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDIN63 loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK27CHNCNTRL:
        """Configuration of clock output 27"""

        address = 0x00A5

        @staticmethod
        def __str__():
            return "EPCLK27ChnCntrL"

        @staticmethod
        def __int__():
            return 0x00A5

        class EPCLK27PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 27 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK27PreEmphasisStrength[2:0]   | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK27PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 27.

            +-----------------------------------+------------------------------------------+
            | EPCLK27PreEmphasisMode[1:0]       | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK27PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 27 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK27PreEmpahasisWidth[2:0]     | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK28CHNCNTRH:
        """Configuration of clock output 28"""

        address = 0x00A6

        @staticmethod
        def __str__():
            return "EPCLK28ChnCntrH"

        @staticmethod
        def __int__():
            return 0x00A6

        class EPCLK28LOWRES:
            """Decreases the power supply filter resistance in EPCLK28 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK28INVERT:
            """Inverts 28 clock output."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPCLK28DRIVESTRENGTH:
            """Sets the driving strength for 28 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK28DriveStrength[2:0]         | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK28FREQ:
            """Sets the frequency for 28 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK28Freq[2:0]                  | Frequency [MHz]                          |
            +===================================+==========================================+
            | 3'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 40                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 80                                       |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 160                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 320                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 640                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 1280                                     |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | EDINEC loopback                          |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPCLK28CHNCNTRL:
        """Configuration of clock output 28"""

        address = 0x00A7

        @staticmethod
        def __str__():
            return "EPCLK28ChnCntrL"

        @staticmethod
        def __int__():
            return 0x00A7

        class EPCLK28PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for 28 clock output.

            +-----------------------------------+------------------------------------------+
            | EPCLK28PreEmphasisStrength[2:0]   | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPCLK28PREEMPHASISMODE:
            """Sets the pre-emphasis mode for clock output 28.

            +-----------------------------------+------------------------------------------+
            | EPCLK28PreEmphasisMode[1:0]       | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPCLK28PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for 28 clock output in self timed mode.

            +-----------------------------------+------------------------------------------+
            | EPCLK28PreEmpahasisWidth[2:0]     | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPTXDATARATE:
        """Data rate control for ePortTx"""

        address = 0x00A8

        @staticmethod
        def __str__():
            return "EPTXDataRate"

        @staticmethod
        def __int__():
            return 0x00A8

        class EPTX3DATARATE:
            """Data rate for ePortTx group 3

            +---------------------+---------------------+
            | EPTX3DataRate[1:0]  | Group 3 data date   |
            +=====================+=====================+
            | 2'd0                | disabled            |
            +---------------------+---------------------+
            | 2'd1                |  80M bps            |
            +---------------------+---------------------+
            | 2'd2                | 160 Mbps            |
            +---------------------+---------------------+
            | 2'd3                | 320 Mbps            |
            +---------------------+---------------------+

            """

            offset = 6
            length = 2
            bit_mask = 192

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPTX2DATARATE:
            """Data rate for ePortTx group 2

            +---------------------+---------------------+
            | EPTX2DataRate[1:0]  | Group 2 data date   |
            +=====================+=====================+
            | 2'd0                | disabled            |
            +---------------------+---------------------+
            | 2'd1                |  80M bps            |
            +---------------------+---------------------+
            | 2'd2                | 160 Mbps            |
            +---------------------+---------------------+
            | 2'd3                | 320 Mbps            |
            +---------------------+---------------------+

            """

            offset = 4
            length = 2
            bit_mask = 48

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPTX1DATARATE:
            """Data rate for ePortTx group 1

            +---------------------+---------------------+
            | EPTX1DataRate[1:0]  | Group 1 data date   |
            +=====================+=====================+
            | 2'd0                | disabled            |
            +---------------------+---------------------+
            | 2'd1                |  80M bps            |
            +---------------------+---------------------+
            | 2'd2                | 160 Mbps            |
            +---------------------+---------------------+
            | 2'd3                | 320 Mbps            |
            +---------------------+---------------------+

            """

            offset = 2
            length = 2
            bit_mask = 12

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPTX0DATARATE:
            """Data rate for ePortTx group 0

            +---------------------+---------------------+
            | EPTX0DataRate[1:0]  | Group 0 data date   |
            +=====================+=====================+
            | 2'd0                | disabled            |
            +---------------------+---------------------+
            | 2'd1                |  80M bps            |
            +---------------------+---------------------+
            | 2'd2                | 160 Mbps            |
            +---------------------+---------------------+
            | 2'd3                | 320 Mbps            |
            +---------------------+---------------------+

            """

            offset = 0
            length = 2
            bit_mask = 3

            @staticmethod
            def validate(value):
                return value in range(4)

    class EPTXCONTROL:
        """EportTx configuration register."""

        address = 0x00A9

        @staticmethod
        def __str__():
            return "EPTXControl"

        @staticmethod
        def __int__():
            return 0x00A9

        class EPTX3MIRRORENABLE:
            """Enables mirror feature for group 3"""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX2MIRRORENABLE:
            """Enables mirror feature for group 2"""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX1MIRRORENABLE:
            """Enables mirror feature for group 1"""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX0MIRRORENABLE:
            """Enables mirror feature for group 0"""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPTX10ENABLE:
        """Channel enable control for EPTX0 and EPTX1."""

        address = 0x00AA

        @staticmethod
        def __str__():
            return "EPTX10Enable"

        @staticmethod
        def __int__():
            return 0x00AA

        class EPTX13ENABLE:
            """Enable channel 3 in group 1"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX12ENABLE:
            """Enable channel 2 in group 1"""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX11ENABLE:
            """Enable channel 1 in group 1"""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX10ENABLE:
            """Enable channel 0 in group 1"""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX03ENABLE:
            """Enable channel 3 in group 0"""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX02ENABLE:
            """Enable channel 2 in group 0"""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX01ENABLE:
            """Enable channel 1 in group 0"""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX00ENABLE:
            """Enable channel 0 in group 0"""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPTX32ENABLE:
        """Channel enable control for EPTX2 and EPTX3."""

        address = 0x00AB

        @staticmethod
        def __str__():
            return "EPTX32Enable"

        @staticmethod
        def __int__():
            return 0x00AB

        class EPTX33ENABLE:
            """Enable channel 3 in group 3"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX32ENABLE:
            """Enable channel 2 in group 3"""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX31ENABLE:
            """Enable channel 1 in group 3"""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX30ENABLE:
            """Enable channel 0 in group 3"""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX23ENABLE:
            """Enable channel 3 in group 2"""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX22ENABLE:
            """Enable channel 2 in group 2"""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX21ENABLE:
            """Enable channel 1 in group 2"""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX20ENABLE:
            """Enable channel 0 in group 2"""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPTXECCHNCNTR:
        """EC channel driver configuration."""

        address = 0x00AC

        @staticmethod
        def __str__():
            return "EPTXEcChnCntr"

        @staticmethod
        def __int__():
            return 0x00AC

        class EPTXECDRIVESTRENGTH:
            """Sets the pre-emphasis strength for the EC channel.

            +-----------------------------------+------------------------------------------+
            | EPTXEcDriveStrength[2:0]          | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPTXECINVERT:
            """Invert data for EC channel output"""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTXECTRISTATE:
            """Enable tri-state operation of EC channel output in simplex modes."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTXECENABLE:
            """Enable EC channel output"""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPTXECCHNCNTR2:
        """Configuration of the EC channel in ePortRx"""

        address = 0x00AD

        @staticmethod
        def __str__():
            return "EPTXEcChnCntr2"

        @staticmethod
        def __int__():
            return 0x00AD

        class EPTXECPREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for EC channel output.

            +-----------------------------------+------------------------------------------+
            | EPTXEcPreEmphasisWidth[2:0]       | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPTXECPREEMPHASISMODE:
            """Sets the pre-emphasis mode for the EC channel.

            +-----------------------------------+------------------------------------------+
            | EPTXEcPreEmphasisMode             | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPTXECPREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for the EC channel.

            +-----------------------------------+------------------------------------------+
            | EPTXEcPreEmphasisStrength[2:0]    | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPTX00CHNCNTR:
        """Control register for output driver of channel 0 in group 0"""

        address = 0x00AE

        @staticmethod
        def __str__():
            return "EPTX00ChnCntr"

        @staticmethod
        def __int__():
            return 0x00AE

        class EPTX00PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for channel 0 in group 0.

            +-----------------------------------+------------------------------------------+
            | EPTX00PreEmphasisStrength[2:0]    | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPTX00PREEMPHASISMODE:
            """Selects the pre-emphasis mode for channel 0 in group 0.

            +-----------------------------------+------------------------------------------+
            | EPTX00PreEmphasisMode[1:0]        | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPTX00DRIVESTRENGTH:
            """Sets the driving strength for channel 0 in group 0.

            +-----------------------------------+------------------------------------------+
            | EPTX00DriveStrength[2:0]          | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPTX01CHNCNTR:
        """Control register for output driver of channel 1 in group 0"""

        address = 0x00AF

        @staticmethod
        def __str__():
            return "EPTX01ChnCntr"

        @staticmethod
        def __int__():
            return 0x00AF

        class EPTX01PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for channel 0 in group 1.

            +-----------------------------------+------------------------------------------+
            | EPTX01PreEmphasisStrength[2:0]    | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPTX01PREEMPHASISMODE:
            """Selects the pre-emphasis mode for channel 0 in group 1.

            +-----------------------------------+------------------------------------------+
            | EPTX01PreEmphasisMode[1:0]        | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPTX01DRIVESTRENGTH:
            """Sets the driving strength for channel 0 in group 1.

            +-----------------------------------+------------------------------------------+
            | EPTX01DriveStrength[2:0]          | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPTX02CHNCNTR:
        """Control register for output driver of channel 2 in group 0"""

        address = 0x00B0

        @staticmethod
        def __str__():
            return "EPTX02ChnCntr"

        @staticmethod
        def __int__():
            return 0x00B0

        class EPTX02PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for channel 0 in group 2.

            +-----------------------------------+------------------------------------------+
            | EPTX02PreEmphasisStrength[2:0]    | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPTX02PREEMPHASISMODE:
            """Selects the pre-emphasis mode for channel 0 in group 2.

            +-----------------------------------+------------------------------------------+
            | EPTX02PreEmphasisMode[1:0]        | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPTX02DRIVESTRENGTH:
            """Sets the driving strength for channel 0 in group 2.

            +-----------------------------------+------------------------------------------+
            | EPTX02DriveStrength[2:0]          | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPTX03CHNCNTR:
        """Control register for output driver of channel 3 in group 0"""

        address = 0x00B1

        @staticmethod
        def __str__():
            return "EPTX03ChnCntr"

        @staticmethod
        def __int__():
            return 0x00B1

        class EPTX03PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for channel 0 in group 3.

            +-----------------------------------+------------------------------------------+
            | EPTX03PreEmphasisStrength[2:0]    | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPTX03PREEMPHASISMODE:
            """Selects the pre-emphasis mode for channel 0 in group 3.

            +-----------------------------------+------------------------------------------+
            | EPTX03PreEmphasisMode[1:0]        | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPTX03DRIVESTRENGTH:
            """Sets the driving strength for channel 0 in group 3.

            +-----------------------------------+------------------------------------------+
            | EPTX03DriveStrength[2:0]          | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPTX10CHNCNTR:
        """Control register for output driver of channel 0 in group 1"""

        address = 0x00B2

        @staticmethod
        def __str__():
            return "EPTX10ChnCntr"

        @staticmethod
        def __int__():
            return 0x00B2

        class EPTX10PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for channel 1 in group 0.

            +-----------------------------------+------------------------------------------+
            | EPTX10PreEmphasisStrength[2:0]    | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPTX10PREEMPHASISMODE:
            """Selects the pre-emphasis mode for channel 1 in group 0.

            +-----------------------------------+------------------------------------------+
            | EPTX10PreEmphasisMode[1:0]        | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPTX10DRIVESTRENGTH:
            """Sets the driving strength for channel 1 in group 0.

            +-----------------------------------+------------------------------------------+
            | EPTX10DriveStrength[2:0]          | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPTX11CHNCNTR:
        """Control register for output driver of channel 1 in group 1"""

        address = 0x00B3

        @staticmethod
        def __str__():
            return "EPTX11ChnCntr"

        @staticmethod
        def __int__():
            return 0x00B3

        class EPTX11PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for channel 1 in group 1.

            +-----------------------------------+------------------------------------------+
            | EPTX11PreEmphasisStrength[2:0]    | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPTX11PREEMPHASISMODE:
            """Selects the pre-emphasis mode for channel 1 in group 1.

            +-----------------------------------+------------------------------------------+
            | EPTX11PreEmphasisMode[1:0]        | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPTX11DRIVESTRENGTH:
            """Sets the driving strength for channel 1 in group 1.

            +-----------------------------------+------------------------------------------+
            | EPTX11DriveStrength[2:0]          | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPTX12CHNCNTR:
        """Control register for output driver of channel 2 in group 1"""

        address = 0x00B4

        @staticmethod
        def __str__():
            return "EPTX12ChnCntr"

        @staticmethod
        def __int__():
            return 0x00B4

        class EPTX12PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for channel 1 in group 2.

            +-----------------------------------+------------------------------------------+
            | EPTX12PreEmphasisStrength[2:0]    | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPTX12PREEMPHASISMODE:
            """Selects the pre-emphasis mode for channel 1 in group 2.

            +-----------------------------------+------------------------------------------+
            | EPTX12PreEmphasisMode[1:0]        | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPTX12DRIVESTRENGTH:
            """Sets the driving strength for channel 1 in group 2.

            +-----------------------------------+------------------------------------------+
            | EPTX12DriveStrength[2:0]          | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPTX13CHNCNTR:
        """Control register for output driver of channel 3 in group 1"""

        address = 0x00B5

        @staticmethod
        def __str__():
            return "EPTX13ChnCntr"

        @staticmethod
        def __int__():
            return 0x00B5

        class EPTX13PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for channel 1 in group 3.

            +-----------------------------------+------------------------------------------+
            | EPTX13PreEmphasisStrength[2:0]    | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPTX13PREEMPHASISMODE:
            """Selects the pre-emphasis mode for channel 1 in group 3.

            +-----------------------------------+------------------------------------------+
            | EPTX13PreEmphasisMode[1:0]        | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPTX13DRIVESTRENGTH:
            """Sets the driving strength for channel 1 in group 3.

            +-----------------------------------+------------------------------------------+
            | EPTX13DriveStrength[2:0]          | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPTX20CHNCNTR:
        """Control register for output driver of channel 0 in group 2"""

        address = 0x00B6

        @staticmethod
        def __str__():
            return "EPTX20ChnCntr"

        @staticmethod
        def __int__():
            return 0x00B6

        class EPTX20PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for channel 2 in group 0.

            +-----------------------------------+------------------------------------------+
            | EPTX20PreEmphasisStrength[2:0]    | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPTX20PREEMPHASISMODE:
            """Selects the pre-emphasis mode for channel 2 in group 0.

            +-----------------------------------+------------------------------------------+
            | EPTX20PreEmphasisMode[1:0]        | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPTX20DRIVESTRENGTH:
            """Sets the driving strength for channel 2 in group 0.

            +-----------------------------------+------------------------------------------+
            | EPTX20DriveStrength[2:0]          | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPTX21CHNCNTR:
        """Control register for output driver of channel 1 in group 2"""

        address = 0x00B7

        @staticmethod
        def __str__():
            return "EPTX21ChnCntr"

        @staticmethod
        def __int__():
            return 0x00B7

        class EPTX21PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for channel 2 in group 1.

            +-----------------------------------+------------------------------------------+
            | EPTX21PreEmphasisStrength[2:0]    | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPTX21PREEMPHASISMODE:
            """Selects the pre-emphasis mode for channel 2 in group 1.

            +-----------------------------------+------------------------------------------+
            | EPTX21PreEmphasisMode[1:0]        | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPTX21DRIVESTRENGTH:
            """Sets the driving strength for channel 2 in group 1.

            +-----------------------------------+------------------------------------------+
            | EPTX21DriveStrength[2:0]          | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPTX22CHNCNTR:
        """Control register for output driver of channel 2 in group 2"""

        address = 0x00B8

        @staticmethod
        def __str__():
            return "EPTX22ChnCntr"

        @staticmethod
        def __int__():
            return 0x00B8

        class EPTX22PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for channel 2 in group 2.

            +-----------------------------------+------------------------------------------+
            | EPTX22PreEmphasisStrength[2:0]    | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPTX22PREEMPHASISMODE:
            """Selects the pre-emphasis mode for channel 2 in group 2.

            +-----------------------------------+------------------------------------------+
            | EPTX22PreEmphasisMode[1:0]        | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPTX22DRIVESTRENGTH:
            """Sets the driving strength for channel 2 in group 2.

            +-----------------------------------+------------------------------------------+
            | EPTX22DriveStrength[2:0]          | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPTX23CHNCNTR:
        """Control register for output driver of channel 3 in group 2"""

        address = 0x00B9

        @staticmethod
        def __str__():
            return "EPTX23ChnCntr"

        @staticmethod
        def __int__():
            return 0x00B9

        class EPTX23PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for channel 2 in group 3.

            +-----------------------------------+------------------------------------------+
            | EPTX23PreEmphasisStrength[2:0]    | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPTX23PREEMPHASISMODE:
            """Selects the pre-emphasis mode for channel 2 in group 3.

            +-----------------------------------+------------------------------------------+
            | EPTX23PreEmphasisMode[1:0]        | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPTX23DRIVESTRENGTH:
            """Sets the driving strength for channel 2 in group 3.

            +-----------------------------------+------------------------------------------+
            | EPTX23DriveStrength[2:0]          | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPTX30CHNCNTR:
        """Control register for output driver of channel 0 in group 3"""

        address = 0x00BA

        @staticmethod
        def __str__():
            return "EPTX30ChnCntr"

        @staticmethod
        def __int__():
            return 0x00BA

        class EPTX30PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for channel 3 in group 0.

            +-----------------------------------+------------------------------------------+
            | EPTX30PreEmphasisStrength[2:0]    | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPTX30PREEMPHASISMODE:
            """Selects the pre-emphasis mode for channel 3 in group 0.

            +-----------------------------------+------------------------------------------+
            | EPTX30PreEmphasisMode[1:0]        | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPTX30DRIVESTRENGTH:
            """Sets the driving strength for channel 3 in group 0.

            +-----------------------------------+------------------------------------------+
            | EPTX30DriveStrength[2:0]          | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPTX31CHNCNTR:
        """Control register for output driver of channel 1 in group 3"""

        address = 0x00BB

        @staticmethod
        def __str__():
            return "EPTX31ChnCntr"

        @staticmethod
        def __int__():
            return 0x00BB

        class EPTX31PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for channel 3 in group 1.

            +-----------------------------------+------------------------------------------+
            | EPTX31PreEmphasisStrength[2:0]    | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPTX31PREEMPHASISMODE:
            """Selects the pre-emphasis mode for channel 3 in group 1.

            +-----------------------------------+------------------------------------------+
            | EPTX31PreEmphasisMode[1:0]        | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPTX31DRIVESTRENGTH:
            """Sets the driving strength for channel 3 in group 1.

            +-----------------------------------+------------------------------------------+
            | EPTX31DriveStrength[2:0]          | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPTX32CHNCNTR:
        """Control register for output driver of channel 2 in group 3"""

        address = 0x00BC

        @staticmethod
        def __str__():
            return "EPTX32ChnCntr"

        @staticmethod
        def __int__():
            return 0x00BC

        class EPTX32PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for channel 3 in group 2.

            +-----------------------------------+------------------------------------------+
            | EPTX32PreEmphasisStrength[2:0]    | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPTX32PREEMPHASISMODE:
            """Selects the pre-emphasis mode for channel 3 in group 2.

            +-----------------------------------+------------------------------------------+
            | EPTX32PreEmphasisMode[1:0]        | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPTX32DRIVESTRENGTH:
            """Sets the driving strength for channel 3 in group 2.

            +-----------------------------------+------------------------------------------+
            | EPTX32DriveStrength[2:0]          | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPTX33CHNCNTR:
        """Control register for output driver of channel 3 in group 3"""

        address = 0x00BD

        @staticmethod
        def __str__():
            return "EPTX33ChnCntr"

        @staticmethod
        def __int__():
            return 0x00BD

        class EPTX33PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for channel 3 in group 3.

            +-----------------------------------+------------------------------------------+
            | EPTX33PreEmphasisStrength[2:0]    | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPTX33PREEMPHASISMODE:
            """Selects the pre-emphasis mode for channel 3 in group 3.

            +-----------------------------------+------------------------------------------+
            | EPTX33PreEmphasisMode[1:0]        | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPTX33DRIVESTRENGTH:
            """Sets the driving strength for channel 3 in group 3.

            +-----------------------------------+------------------------------------------+
            | EPTX33DriveStrength[2:0]          | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPTX01_00CHNCNTR:
        """Output driver settings for ePortTx group 0"""

        address = 0x00BE

        @staticmethod
        def __str__():
            return "EPTX01_00ChnCntr"

        @staticmethod
        def __int__():
            return 0x00BE

        class EPTX01INVERT:
            """Invert data for channel 1 in ePortTx Group 0"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX01PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for channel 1 in ePortTx Group 0.

            +-----------------------------------+------------------------------------------+
            | EPTX01PreEmpahasisWidth[2:0]      | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 4
            length = 3
            bit_mask = 112

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPTX00INVERT:
            """Invert data for channel 0 in ePortTx Group 0"""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX00PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for channel 0 in ePortTx Group 0.

            +-----------------------------------+------------------------------------------+
            | EPTX00PreEmpahasisWidth[2:0]      | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPTX03_02CHNCNTR:
        """Output driver settings for ePortTx group 0"""

        address = 0x00BF

        @staticmethod
        def __str__():
            return "EPTX03_02ChnCntr"

        @staticmethod
        def __int__():
            return 0x00BF

        class EPTX03INVERT:
            """Invert data for channel 3 in ePortTx Group 0"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX03PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for channel 3 in ePortTx Group 0.

            +-----------------------------------+------------------------------------------+
            | EPTX03PreEmpahasisWidth[2:0]      | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 4
            length = 3
            bit_mask = 112

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPTX02INVERT:
            """Invert data for channel 2 in ePortTx Group 0"""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX02PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for channel 2 in ePortTx Group 0.

            +-----------------------------------+------------------------------------------+
            | EPTX02PreEmpahasisWidth[2:0]      | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPTX11_10CHNCNTR:
        """Output driver settings for ePortTx group 1"""

        address = 0x00C0

        @staticmethod
        def __str__():
            return "EPTX11_10ChnCntr"

        @staticmethod
        def __int__():
            return 0x00C0

        class EPTX11INVERT:
            """Invert data for channel 1 in ePortTx Group 1"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX11PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for channel 1 in ePortTx Group 1.

            +-----------------------------------+------------------------------------------+
            | EPTX11PreEmpahasisWidth[2:0]      | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 4
            length = 3
            bit_mask = 112

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPTX10INVERT:
            """Invert data for channel 0 in ePortTx Group 1"""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX10PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for channel 0 in ePortTx Group 1.

            +-----------------------------------+------------------------------------------+
            | EPTX10PreEmpahasisWidth[2:0]      | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPTX13_12CHNCNTR:
        """Output driver settings for ePortTx group 1"""

        address = 0x00C1

        @staticmethod
        def __str__():
            return "EPTX13_12ChnCntr"

        @staticmethod
        def __int__():
            return 0x00C1

        class EPTX13INVERT:
            """Invert data for channel 3 in ePortTx Group 1"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX13PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for channel 3 in ePortTx Group 1.

            +-----------------------------------+------------------------------------------+
            | EPTX13PreEmpahasisWidth[2:0]      | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 4
            length = 3
            bit_mask = 112

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPTX12INVERT:
            """Invert data for channel 2 in ePortTx Group 1"""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX12PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for channel 2 in ePortTx Group 1.

            +-----------------------------------+------------------------------------------+
            | EPTX12PreEmpahasisWidth[2:0]      | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPTX21_20CHNCNTR:
        """Output driver settings for ePortTx group 2"""

        address = 0x00C2

        @staticmethod
        def __str__():
            return "EPTX21_20ChnCntr"

        @staticmethod
        def __int__():
            return 0x00C2

        class EPTX21INVERT:
            """Invert data for channel 1 in ePortTx Group 2"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX21PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for channel 1 in ePortTx Group 2.

            +-----------------------------------+------------------------------------------+
            | EPTX21PreEmpahasisWidth[2:0]      | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 4
            length = 3
            bit_mask = 112

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPTX20INVERT:
            """Invert data for channel 0 in ePortTx Group 2"""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX20PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for channel 0 in ePortTx Group 2.

            +-----------------------------------+------------------------------------------+
            | EPTX20PreEmpahasisWidth[2:0]      | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPTX23_22CHNCNTR:
        """Output driver settings for ePortTx group 2"""

        address = 0x00C3

        @staticmethod
        def __str__():
            return "EPTX23_22ChnCntr"

        @staticmethod
        def __int__():
            return 0x00C3

        class EPTX23INVERT:
            """Invert data for channel 3 in ePortTx Group 2"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX23PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for channel 3 in ePortTx Group 2.

            +-----------------------------------+------------------------------------------+
            | EPTX23PreEmpahasisWidth[2:0]      | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 4
            length = 3
            bit_mask = 112

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPTX22INVERT:
            """Invert data for channel 2 in ePortTx Group 2"""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX22PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for channel 2 in ePortTx Group 2.

            +-----------------------------------+------------------------------------------+
            | EPTX22PreEmpahasisWidth[2:0]      | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPTX31_30CHNCNTR:
        """Output driver settings for ePortTx group 3"""

        address = 0x00C4

        @staticmethod
        def __str__():
            return "EPTX31_30ChnCntr"

        @staticmethod
        def __int__():
            return 0x00C4

        class EPTX31INVERT:
            """Invert data for channel 1 in ePortTx Group 3"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX31PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for channel 1 in ePortTx Group 3.

            +-----------------------------------+------------------------------------------+
            | EPTX31PreEmpahasisWidth[2:0]      | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 4
            length = 3
            bit_mask = 112

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPTX30INVERT:
            """Invert data for channel 0 in ePortTx Group 3"""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX30PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for channel 0 in ePortTx Group 3.

            +-----------------------------------+------------------------------------------+
            | EPTX30PreEmpahasisWidth[2:0]      | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPTX33_32CHNCNTR:
        """Output driver settings for ePortTx group 3"""

        address = 0x00C5

        @staticmethod
        def __str__():
            return "EPTX33_32ChnCntr"

        @staticmethod
        def __int__():
            return 0x00C5

        class EPTX33INVERT:
            """Invert data for channel 3 in ePortTx Group 3"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX33PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for channel 3 in ePortTx Group 3.

            +-----------------------------------+------------------------------------------+
            | EPTX33PreEmpahasisWidth[2:0]      | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 4
            length = 3
            bit_mask = 112

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPTX32INVERT:
            """Invert data for channel 2 in ePortTx Group 3"""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX32PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for channel 2 in ePortTx Group 3.

            +-----------------------------------+------------------------------------------+
            | EPTX32PreEmpahasisWidth[2:0]      | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPTXLOWRES0:
        """Power supply resistance control for ePortTx group 0 and 1 drivers."""

        address = 0x00C6

        @staticmethod
        def __str__():
            return "EPTXLowRes0"

        @staticmethod
        def __int__():
            return 0x00C6

        class EPTX13LOWRES:
            """Decreases the power supply filter resistance in EPTX13 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX12LOWRES:
            """Decreases the power supply filter resistance in EPTX12 driver."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX11LOWRES:
            """Decreases the power supply filter resistance in EPTX11 driver."""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX10LOWRES:
            """Decreases the power supply filter resistance in EPTX10 driver."""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX03LOWRES:
            """Decreases the power supply filter resistance in EPTX03 driver."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX02LOWRES:
            """Decreases the power supply filter resistance in EPTX02 driver."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX01LOWRES:
            """Decreases the power supply filter resistance in EPTX01 driver."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX00LOWRES:
            """Decreases the power supply filter resistance in EPTX00 driver."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPTXLOWRES1:
        """Power supply resistance control for ePortTx group 2 and 3 drivers."""

        address = 0x00C7

        @staticmethod
        def __str__():
            return "EPTXLowRes1"

        @staticmethod
        def __int__():
            return 0x00C7

        class EPTX33LOWRES:
            """Decreases the power supply filter resistance in EPTX33 driver."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX32LOWRES:
            """Decreases the power supply filter resistance in EPTX32 driver."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX31LOWRES:
            """Decreases the power supply filter resistance in EPTX31 driver."""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX30LOWRES:
            """Decreases the power supply filter resistance in EPTX30 driver."""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX23LOWRES:
            """Decreases the power supply filter resistance in EPTX23 driver."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX22LOWRES:
            """Decreases the power supply filter resistance in EPTX22 driver."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX21LOWRES:
            """Decreases the power supply filter resistance in EPTX21 driver."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPTX20LOWRES:
            """Decreases the power supply filter resistance in EPTX20 driver."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX0CONTROL:
        """Configuration of ePortRx Group 0"""

        address = 0x00C8

        @staticmethod
        def __str__():
            return "EPRX0Control"

        @staticmethod
        def __int__():
            return 0x00C8

        class EPRX03ENABLE:
            """Enables channel 3 in group 0."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX02ENABLE:
            """Enables channel 2 in group 0."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX01ENABLE:
            """Enables channel 1 in group 0."""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX00ENABLE:
            """Enables channel 0 in group 0."""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX0DATARATE:
            """Sets the data rate for group 0.

            +---------------------+---------------------+---------------------+
            | EPRX0DataRate[1:0]  | 5 Gbps              | 10 Gbps             |
            +=====================+=====================+=====================+
            | 2'd0                | disabled            | disabled            |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 160M bps            |  320 Mbps           |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 320 Mbps            |  640 Mbps           |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 640 Mbps            |  1280 Mbps          |
            +---------------------+---------------------+---------------------+

            """

            offset = 2
            length = 2
            bit_mask = 12

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPRX0TRACKMODE:
            """Sets the phase tracking mode for group 0.

            +-----------------------+---------------------+------------------------+
            | EPRX0TrackMode[1:0]   | Mode                                         |
            +=======================+=====================+========================+
            | 2'd0                  | Fixed phase                                  |
            +-----------------------+---------------------+------------------------+
            | 2'd1                  | Initial training                             |
            +-----------------------+---------------------+------------------------+
            | 2'd2                  | Continuous phase tracking                    |
            +-----------------------+---------------------+------------------------+
            | 2'd3                  | Continuous phase tracking with initial phase |
            +-----------------------+---------------------+------------------------+


            """

            offset = 0
            length = 2
            bit_mask = 3

            @staticmethod
            def validate(value):
                return value in range(4)

    class EPRX1CONTROL:
        """Configuration of ePortRx Group 1"""

        address = 0x00C9

        @staticmethod
        def __str__():
            return "EPRX1Control"

        @staticmethod
        def __int__():
            return 0x00C9

        class EPRX13ENABLE:
            """Enables channel 3 in group 1."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX12ENABLE:
            """Enables channel 2 in group 1."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX11ENABLE:
            """Enables channel 1 in group 1."""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX10ENABLE:
            """Enables channel 0 in group 1."""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX1DATARATE:
            """Sets the data rate for group 1.

            +---------------------+---------------------+---------------------+
            | EPRX1DataRate[1:0]  | 5 Gbps              | 10 Gbps             |
            +=====================+=====================+=====================+
            | 2'd0                | disabled            | disabled            |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 160M bps            |  320 Mbps           |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 320 Mbps            |  640 Mbps           |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 640 Mbps            |  1280 Mbps          |
            +---------------------+---------------------+---------------------+

            """

            offset = 2
            length = 2
            bit_mask = 12

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPRX1TRACKMODE:
            """Sets the phase tracking mode for group 1.

            +-----------------------+---------------------+------------------------+
            | EPRX1TrackMode[1:0]   | Mode                                         |
            +=======================+=====================+========================+
            | 2'd0                  | Fixed phase                                  |
            +-----------------------+---------------------+------------------------+
            | 2'd1                  | Initial training                             |
            +-----------------------+---------------------+------------------------+
            | 2'd2                  | Continuous phase tracking                    |
            +-----------------------+---------------------+------------------------+
            | 2'd3                  | Continuous phase tracking with initial phase |
            +-----------------------+---------------------+------------------------+


            """

            offset = 0
            length = 2
            bit_mask = 3

            @staticmethod
            def validate(value):
                return value in range(4)

    class EPRX2CONTROL:
        """Configuration of ePortRx Group 2"""

        address = 0x00CA

        @staticmethod
        def __str__():
            return "EPRX2Control"

        @staticmethod
        def __int__():
            return 0x00CA

        class EPRX23ENABLE:
            """Enables channel 3 in group 2."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX22ENABLE:
            """Enables channel 2 in group 2."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX21ENABLE:
            """Enables channel 1 in group 2."""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX20ENABLE:
            """Enables channel 0 in group 2."""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX2DATARATE:
            """Sets the data rate for group 2.

            +---------------------+---------------------+---------------------+
            | EPRX2DataRate[1:0]  | 5 Gbps              | 10 Gbps             |
            +=====================+=====================+=====================+
            | 2'd0                | disabled            | disabled            |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 160M bps            |  320 Mbps           |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 320 Mbps            |  640 Mbps           |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 640 Mbps            |  1280 Mbps          |
            +---------------------+---------------------+---------------------+

            """

            offset = 2
            length = 2
            bit_mask = 12

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPRX2TRACKMODE:
            """Sets the phase tracking mode for group 2.

            +-----------------------+---------------------+------------------------+
            | EPRX2TrackMode[1:0]   | Mode                                         |
            +=======================+=====================+========================+
            | 2'd0                  | Fixed phase                                  |
            +-----------------------+---------------------+------------------------+
            | 2'd1                  | Initial training                             |
            +-----------------------+---------------------+------------------------+
            | 2'd2                  | Continuous phase tracking                    |
            +-----------------------+---------------------+------------------------+
            | 2'd3                  | Continuous phase tracking with initial phase |
            +-----------------------+---------------------+------------------------+


            """

            offset = 0
            length = 2
            bit_mask = 3

            @staticmethod
            def validate(value):
                return value in range(4)

    class EPRX3CONTROL:
        """Configuration of ePortRx Group 3"""

        address = 0x00CB

        @staticmethod
        def __str__():
            return "EPRX3Control"

        @staticmethod
        def __int__():
            return 0x00CB

        class EPRX33ENABLE:
            """Enables channel 3 in group 3."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX32ENABLE:
            """Enables channel 2 in group 3."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX31ENABLE:
            """Enables channel 1 in group 3."""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX30ENABLE:
            """Enables channel 0 in group 3."""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX3DATARATE:
            """Sets the data rate for group 3.

            +---------------------+---------------------+---------------------+
            | EPRX3DataRate[1:0]  | 5 Gbps              | 10 Gbps             |
            +=====================+=====================+=====================+
            | 2'd0                | disabled            | disabled            |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 160M bps            |  320 Mbps           |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 320 Mbps            |  640 Mbps           |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 640 Mbps            |  1280 Mbps          |
            +---------------------+---------------------+---------------------+

            """

            offset = 2
            length = 2
            bit_mask = 12

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPRX3TRACKMODE:
            """Sets the phase tracking mode for group 3.

            +-----------------------+---------------------+------------------------+
            | EPRX3TrackMode[1:0]   | Mode                                         |
            +=======================+=====================+========================+
            | 2'd0                  | Fixed phase                                  |
            +-----------------------+---------------------+------------------------+
            | 2'd1                  | Initial training                             |
            +-----------------------+---------------------+------------------------+
            | 2'd2                  | Continuous phase tracking                    |
            +-----------------------+---------------------+------------------------+
            | 2'd3                  | Continuous phase tracking with initial phase |
            +-----------------------+---------------------+------------------------+


            """

            offset = 0
            length = 2
            bit_mask = 3

            @staticmethod
            def validate(value):
                return value in range(4)

    class EPRX4CONTROL:
        """Configuration of ePortRx Group 4"""

        address = 0x00CC

        @staticmethod
        def __str__():
            return "EPRX4Control"

        @staticmethod
        def __int__():
            return 0x00CC

        class EPRX43ENABLE:
            """Enables channel 3 in group 4."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX42ENABLE:
            """Enables channel 2 in group 4."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX41ENABLE:
            """Enables channel 1 in group 4."""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX40ENABLE:
            """Enables channel 0 in group 4."""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX4DATARATE:
            """Sets the data rate for group 4.

            +---------------------+---------------------+---------------------+
            | EPRX4DataRate[1:0]  | 5 Gbps              | 10 Gbps             |
            +=====================+=====================+=====================+
            | 2'd0                | disabled            | disabled            |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 160M bps            |  320 Mbps           |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 320 Mbps            |  640 Mbps           |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 640 Mbps            |  1280 Mbps          |
            +---------------------+---------------------+---------------------+

            """

            offset = 2
            length = 2
            bit_mask = 12

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPRX4TRACKMODE:
            """Sets the phase tracking mode for group 4.

            +-----------------------+---------------------+------------------------+
            | EPRX4TrackMode[1:0]   | Mode                                         |
            +=======================+=====================+========================+
            | 2'd0                  | Fixed phase                                  |
            +-----------------------+---------------------+------------------------+
            | 2'd1                  | Initial training                             |
            +-----------------------+---------------------+------------------------+
            | 2'd2                  | Continuous phase tracking                    |
            +-----------------------+---------------------+------------------------+
            | 2'd3                  | Continuous phase tracking with initial phase |
            +-----------------------+---------------------+------------------------+


            """

            offset = 0
            length = 2
            bit_mask = 3

            @staticmethod
            def validate(value):
                return value in range(4)

    class EPRX5CONTROL:
        """Configuration of ePortRx Group 5"""

        address = 0x00CD

        @staticmethod
        def __str__():
            return "EPRX5Control"

        @staticmethod
        def __int__():
            return 0x00CD

        class EPRX53ENABLE:
            """Enables channel 3 in group 5."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX52ENABLE:
            """Enables channel 2 in group 5."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX51ENABLE:
            """Enables channel 1 in group 5."""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX50ENABLE:
            """Enables channel 0 in group 5."""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX5DATARATE:
            """Sets the data rate for group 5.

            +---------------------+---------------------+---------------------+
            | EPRX5DataRate[1:0]  | 5 Gbps              | 10 Gbps             |
            +=====================+=====================+=====================+
            | 2'd0                | disabled            | disabled            |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 160M bps            |  320 Mbps           |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 320 Mbps            |  640 Mbps           |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 640 Mbps            |  1280 Mbps          |
            +---------------------+---------------------+---------------------+

            """

            offset = 2
            length = 2
            bit_mask = 12

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPRX5TRACKMODE:
            """Sets the phase tracking mode for group 5.

            +-----------------------+---------------------+------------------------+
            | EPRX5TrackMode[1:0]   | Mode                                         |
            +=======================+=====================+========================+
            | 2'd0                  | Fixed phase                                  |
            +-----------------------+---------------------+------------------------+
            | 2'd1                  | Initial training                             |
            +-----------------------+---------------------+------------------------+
            | 2'd2                  | Continuous phase tracking                    |
            +-----------------------+---------------------+------------------------+
            | 2'd3                  | Continuous phase tracking with initial phase |
            +-----------------------+---------------------+------------------------+


            """

            offset = 0
            length = 2
            bit_mask = 3

            @staticmethod
            def validate(value):
                return value in range(4)

    class EPRX6CONTROL:
        """Configuration of ePortRx Group 6"""

        address = 0x00CE

        @staticmethod
        def __str__():
            return "EPRX6Control"

        @staticmethod
        def __int__():
            return 0x00CE

        class EPRX63ENABLE:
            """Enables channel 3 in group 6."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX62ENABLE:
            """Enables channel 2 in group 6."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX61ENABLE:
            """Enables channel 1 in group 6."""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX60ENABLE:
            """Enables channel 0 in group 6."""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX6DATARATE:
            """Sets the data rate for group 6.

            +---------------------+---------------------+---------------------+
            | EPRX6DataRate[1:0]  | 5 Gbps              | 10 Gbps             |
            +=====================+=====================+=====================+
            | 2'd0                | disabled            | disabled            |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 160M bps            |  320 Mbps           |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 320 Mbps            |  640 Mbps           |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 640 Mbps            |  1280 Mbps          |
            +---------------------+---------------------+---------------------+

            """

            offset = 2
            length = 2
            bit_mask = 12

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPRX6TRACKMODE:
            """Sets the phase tracking mode for group 6.

            +-----------------------+---------------------+------------------------+
            | EPRX6TrackMode[1:0]   | Mode                                         |
            +=======================+=====================+========================+
            | 2'd0                  | Fixed phase                                  |
            +-----------------------+---------------------+------------------------+
            | 2'd1                  | Initial training                             |
            +-----------------------+---------------------+------------------------+
            | 2'd2                  | Continuous phase tracking                    |
            +-----------------------+---------------------+------------------------+
            | 2'd3                  | Continuous phase tracking with initial phase |
            +-----------------------+---------------------+------------------------+


            """

            offset = 0
            length = 2
            bit_mask = 3

            @staticmethod
            def validate(value):
                return value in range(4)

    class EPRXECCONTROL:
        """Configuration of ePortRx EC channel"""

        address = 0x00CF

        @staticmethod
        def __str__():
            return "EPRXEcControl"

        @staticmethod
        def __int__():
            return 0x00CF

        class EPRXECENABLE:
            """Enables the EC channel."""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRXECAUTOPHASERESETDISABLE:
            """Disable the automatic phase reset (in the ePortRxEc channel CDR) in between transactions."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRXECTRACKMODE:
            """Sets the phase tracking mode for the EC channel

            +-----------------------+----------------------------------------------+
            | EPRXEcTrackMode       | Mode                                         |
            +=======================+==============================================+
            | 1'd0                  | Continuous phase tracking                    |
            +-----------------------+----------------------------------------------+
            | 1'd1                  | Fixed phase                                  |
            +-----------------------+----------------------------------------------+

            """

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX00CHNCNTR:
        """Configuration of the channel 0 in group 0"""

        address = 0x00D0

        @staticmethod
        def __str__():
            return "EPRX00ChnCntr"

        @staticmethod
        def __int__():
            return 0x00D0

        class EPRX00PHASESELECT:
            """Selects the phase for channel 0 in group 0."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX00INVERT:
            """Inverts the channel 0 in group 0."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX00ACBIAS:
            """Enables the common mode generation for channel 0 in group 0."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX00TERM:
            """Enables the 100 Ohm termination for channel 0 in group 0."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX00EQ:
            """Equalization control for channel 0 in group 0."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX01CHNCNTR:
        """Configuration of the channel 1 in group 0"""

        address = 0x00D1

        @staticmethod
        def __str__():
            return "EPRX01ChnCntr"

        @staticmethod
        def __int__():
            return 0x00D1

        class EPRX01PHASESELECT:
            """Selects the phase for channel 1 in group 0."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX01INVERT:
            """Inverts the channel 1 in group 0."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX01ACBIAS:
            """Enables the common mode generation for channel 1 in group 0."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX01TERM:
            """Enables the 100 Ohm termination for channel 1 in group 0."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX01EQ:
            """Equalization control for channel 1 in group 0."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX02CHNCNTR:
        """Configuration of the channel 2 in group 0"""

        address = 0x00D2

        @staticmethod
        def __str__():
            return "EPRX02ChnCntr"

        @staticmethod
        def __int__():
            return 0x00D2

        class EPRX02PHASESELECT:
            """Selects the phase for channel 2 in group 0."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX02INVERT:
            """Inverts the channel 2 in group 0."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX02ACBIAS:
            """Enables the common mode generation for channel 2 in group 0."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX02TERM:
            """Enables the 100 Ohm termination for channel 2 in group 0."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX02EQ:
            """Equalization control for channel 2 in group 0."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX03CHNCNTR:
        """Configuration of the channel 3 in group 0"""

        address = 0x00D3

        @staticmethod
        def __str__():
            return "EPRX03ChnCntr"

        @staticmethod
        def __int__():
            return 0x00D3

        class EPRX03PHASESELECT:
            """Selects the phase for channel 3 in group 0."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX03INVERT:
            """Inverts the channel 3 in group 0."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX03ACBIAS:
            """Enables the common mode generation for channel 3 in group 0."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX03TERM:
            """Enables the 100 Ohm termination for channel 3 in group 0."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX03EQ:
            """Equalization control for channel 3 in group 0."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX10CHNCNTR:
        """Configuration of the channel 0 in group 1"""

        address = 0x00D4

        @staticmethod
        def __str__():
            return "EPRX10ChnCntr"

        @staticmethod
        def __int__():
            return 0x00D4

        class EPRX10PHASESELECT:
            """Selects the phase for channel 0 in group 1."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX10INVERT:
            """Inverts the channel 0 in group 1."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX10ACBIAS:
            """Enables the common mode generation for channel 0 in group 1."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX10TERM:
            """Enables the 100 Ohm termination for channel 0 in group 1."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX10EQ:
            """Equalization control for channel 0 in group 1."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX11CHNCNTR:
        """Configuration of the channel 1 in group 1"""

        address = 0x00D5

        @staticmethod
        def __str__():
            return "EPRX11ChnCntr"

        @staticmethod
        def __int__():
            return 0x00D5

        class EPRX11PHASESELECT:
            """Selects the phase for channel 1 in group 1."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX11INVERT:
            """Inverts the channel 1 in group 1."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX11ACBIAS:
            """Enables the common mode generation for channel 1 in group 1."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX11TERM:
            """Enables the 100 Ohm termination for channel 1 in group 1."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX11EQ:
            """Equalization control for channel 1 in group 1."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX12CHNCNTR:
        """Configuration of the channel 2 in group 1"""

        address = 0x00D6

        @staticmethod
        def __str__():
            return "EPRX12ChnCntr"

        @staticmethod
        def __int__():
            return 0x00D6

        class EPRX12PHASESELECT:
            """Selects the phase for channel 2 in group 1."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX12INVERT:
            """Inverts the channel 2 in group 1."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX12ACBIAS:
            """Enables the common mode generation for channel 2 in group 1."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX12TERM:
            """Enables the 100 Ohm termination for channel 2 in group 1."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX12EQ:
            """Equalization control for channel 2 in group 1."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX13CHNCNTR:
        """Configuration of the channel 3 in group 1"""

        address = 0x00D7

        @staticmethod
        def __str__():
            return "EPRX13ChnCntr"

        @staticmethod
        def __int__():
            return 0x00D7

        class EPRX13PHASESELECT:
            """Selects the phase for channel 3 in group 1."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX13INVERT:
            """Inverts the channel 3 in group 1."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX13ACBIAS:
            """Enables the common mode generation for channel 3 in group 1."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX13TERM:
            """Enables the 100 Ohm termination for channel 3 in group 1."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX13EQ:
            """Equalization control for channel 3 in group 1."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX20CHNCNTR:
        """Configuration of the channel 0 in group 2"""

        address = 0x00D8

        @staticmethod
        def __str__():
            return "EPRX20ChnCntr"

        @staticmethod
        def __int__():
            return 0x00D8

        class EPRX20PHASESELECT:
            """Selects the phase for channel 0 in group 2."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX20INVERT:
            """Inverts the channel 0 in group 2."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX20ACBIAS:
            """Enables the common mode generation for channel 0 in group 2."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX20TERM:
            """Enables the 100 Ohm termination for channel 0 in group 2."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX20EQ:
            """Equalization control for channel 0 in group 2."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX21CHNCNTR:
        """Configuration of the channel 1 in group 2"""

        address = 0x00D9

        @staticmethod
        def __str__():
            return "EPRX21ChnCntr"

        @staticmethod
        def __int__():
            return 0x00D9

        class EPRX21PHASESELECT:
            """Selects the phase for channel 1 in group 2."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX21INVERT:
            """Inverts the channel 1 in group 2."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX21ACBIAS:
            """Enables the common mode generation for channel 1 in group 2."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX21TERM:
            """Enables the 100 Ohm termination for channel 1 in group 2."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX21EQ:
            """Equalization control for channel 1 in group 2."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX22CHNCNTR:
        """Configuration of the channel 2 in group 2"""

        address = 0x00DA

        @staticmethod
        def __str__():
            return "EPRX22ChnCntr"

        @staticmethod
        def __int__():
            return 0x00DA

        class EPRX22PHASESELECT:
            """Selects the phase for channel 2 in group 2."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX22INVERT:
            """Inverts the channel 2 in group 2."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX22ACBIAS:
            """Enables the common mode generation for channel 2 in group 2."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX22TERM:
            """Enables the 100 Ohm termination for channel 2 in group 2."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX22EQ:
            """Equalization control for channel 2 in group 2."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX23CHNCNTR:
        """Configuration of the channel 3 in group 2"""

        address = 0x00DB

        @staticmethod
        def __str__():
            return "EPRX23ChnCntr"

        @staticmethod
        def __int__():
            return 0x00DB

        class EPRX23PHASESELECT:
            """Selects the phase for channel 3 in group 2."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX23INVERT:
            """Inverts the channel 3 in group 2."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX23ACBIAS:
            """Enables the common mode generation for channel 3 in group 2."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX23TERM:
            """Enables the 100 Ohm termination for channel 3 in group 2."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX23EQ:
            """Equalization control for channel 3 in group 2."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX30CHNCNTR:
        """Configuration of the channel 0 in group 3"""

        address = 0x00DC

        @staticmethod
        def __str__():
            return "EPRX30ChnCntr"

        @staticmethod
        def __int__():
            return 0x00DC

        class EPRX30PHASESELECT:
            """Selects the phase for channel 0 in group 3."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX30INVERT:
            """Inverts the channel 0 in group 3."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX30ACBIAS:
            """Enables the common mode generation for channel 0 in group 3."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX30TERM:
            """Enables the 100 Ohm termination for channel 0 in group 3."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX30EQ:
            """Equalization control for channel 0 in group 3."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX31CHNCNTR:
        """Configuration of the channel 1 in group 3"""

        address = 0x00DD

        @staticmethod
        def __str__():
            return "EPRX31ChnCntr"

        @staticmethod
        def __int__():
            return 0x00DD

        class EPRX31PHASESELECT:
            """Selects the phase for channel 1 in group 3."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX31INVERT:
            """Inverts the channel 1 in group 3."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX31ACBIAS:
            """Enables the common mode generation for channel 1 in group 3."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX31TERM:
            """Enables the 100 Ohm termination for channel 1 in group 3."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX31EQ:
            """Equalization control for channel 1 in group 3."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX32CHNCNTR:
        """Configuration of the channel 2 in group 3"""

        address = 0x00DE

        @staticmethod
        def __str__():
            return "EPRX32ChnCntr"

        @staticmethod
        def __int__():
            return 0x00DE

        class EPRX32PHASESELECT:
            """Selects the phase for channel 2 in group 3."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX32INVERT:
            """Inverts the channel 2 in group 3."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX32ACBIAS:
            """Enables the common mode generation for channel 2 in group 3."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX32TERM:
            """Enables the 100 Ohm termination for channel 2 in group 3."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX32EQ:
            """Equalization control for channel 2 in group 3."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX33CHNCNTR:
        """Configuration of the channel 3 in group 3"""

        address = 0x00DF

        @staticmethod
        def __str__():
            return "EPRX33ChnCntr"

        @staticmethod
        def __int__():
            return 0x00DF

        class EPRX33PHASESELECT:
            """Selects the phase for channel 3 in group 3."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX33INVERT:
            """Inverts the channel 3 in group 3."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX33ACBIAS:
            """Enables the common mode generation for channel 3 in group 3."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX33TERM:
            """Enables the 100 Ohm termination for channel 3 in group 3."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX33EQ:
            """Equalization control for channel 3 in group 3."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX40CHNCNTR:
        """Configuration of the channel 0 in group 4"""

        address = 0x00E0

        @staticmethod
        def __str__():
            return "EPRX40ChnCntr"

        @staticmethod
        def __int__():
            return 0x00E0

        class EPRX40PHASESELECT:
            """Selects the phase for channel 0 in group 4."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX40INVERT:
            """Inverts the channel 0 in group 4."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX40ACBIAS:
            """Enables the common mode generation for channel 0 in group 4."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX40TERM:
            """Enables the 100 Ohm termination for channel 0 in group 4."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX40EQ:
            """Equalization control for channel 0 in group 4."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX41CHNCNTR:
        """Configuration of the channel 1 in group 4"""

        address = 0x00E1

        @staticmethod
        def __str__():
            return "EPRX41ChnCntr"

        @staticmethod
        def __int__():
            return 0x00E1

        class EPRX41PHASESELECT:
            """Selects the phase for channel 1 in group 4."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX41INVERT:
            """Inverts the channel 1 in group 4."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX41ACBIAS:
            """Enables the common mode generation for channel 1 in group 4."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX41TERM:
            """Enables the 100 Ohm termination for channel 1 in group 4."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX41EQ:
            """Equalization control for channel 1 in group 4."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX42CHNCNTR:
        """Configuration of the channel 2 in group 4"""

        address = 0x00E2

        @staticmethod
        def __str__():
            return "EPRX42ChnCntr"

        @staticmethod
        def __int__():
            return 0x00E2

        class EPRX42PHASESELECT:
            """Selects the phase for channel 2 in group 4."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX42INVERT:
            """Inverts the channel 2 in group 4."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX42ACBIAS:
            """Enables the common mode generation for channel 2 in group 4."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX42TERM:
            """Enables the 100 Ohm termination for channel 2 in group 4."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX42EQ:
            """Equalization control for channel 2 in group 4."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX43CHNCNTR:
        """Configuration of the channel 3 in group 4"""

        address = 0x00E3

        @staticmethod
        def __str__():
            return "EPRX43ChnCntr"

        @staticmethod
        def __int__():
            return 0x00E3

        class EPRX43PHASESELECT:
            """Selects the phase for channel 3 in group 4."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX43INVERT:
            """Inverts the channel 3 in group 4."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX43ACBIAS:
            """Enables the common mode generation for channel 3 in group 4."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX43TERM:
            """Enables the 100 Ohm termination for channel 3 in group 4."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX43EQ:
            """Equalization control for channel 3 in group 4."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX50CHNCNTR:
        """Configuration of the channel 0 in group 5"""

        address = 0x00E4

        @staticmethod
        def __str__():
            return "EPRX50ChnCntr"

        @staticmethod
        def __int__():
            return 0x00E4

        class EPRX50PHASESELECT:
            """Selects the phase for channel 0 in group 5."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX50INVERT:
            """Inverts the channel 0 in group 5."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX50ACBIAS:
            """Enables the common mode generation for channel 0 in group 5."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX50TERM:
            """Enables the 100 Ohm termination for channel 0 in group 5."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX50EQ:
            """Equalization control for channel 0 in group 5."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX51CHNCNTR:
        """Configuration of the channel 1 in group 5"""

        address = 0x00E5

        @staticmethod
        def __str__():
            return "EPRX51ChnCntr"

        @staticmethod
        def __int__():
            return 0x00E5

        class EPRX51PHASESELECT:
            """Selects the phase for channel 1 in group 5."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX51INVERT:
            """Inverts the channel 1 in group 5."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX51ACBIAS:
            """Enables the common mode generation for channel 1 in group 5."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX51TERM:
            """Enables the 100 Ohm termination for channel 1 in group 5."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX51EQ:
            """Equalization control for channel 1 in group 5."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX52CHNCNTR:
        """Configuration of the channel 2 in group 5"""

        address = 0x00E6

        @staticmethod
        def __str__():
            return "EPRX52ChnCntr"

        @staticmethod
        def __int__():
            return 0x00E6

        class EPRX52PHASESELECT:
            """Selects the phase for channel 2 in group 5."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX52INVERT:
            """Inverts the channel 2 in group 5."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX52ACBIAS:
            """Enables the common mode generation for channel 2 in group 5."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX52TERM:
            """Enables the 100 Ohm termination for channel 2 in group 5."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX52EQ:
            """Equalization control for channel 2 in group 5."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX53CHNCNTR:
        """Configuration of the channel 3 in group 5"""

        address = 0x00E7

        @staticmethod
        def __str__():
            return "EPRX53ChnCntr"

        @staticmethod
        def __int__():
            return 0x00E7

        class EPRX53PHASESELECT:
            """Selects the phase for channel 3 in group 5."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX53INVERT:
            """Inverts the channel 3 in group 5."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX53ACBIAS:
            """Enables the common mode generation for channel 3 in group 5."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX53TERM:
            """Enables the 100 Ohm termination for channel 3 in group 5."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX53EQ:
            """Equalization control for channel 3 in group 5."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX60CHNCNTR:
        """Configuration of the channel 0 in group 6"""

        address = 0x00E8

        @staticmethod
        def __str__():
            return "EPRX60ChnCntr"

        @staticmethod
        def __int__():
            return 0x00E8

        class EPRX60PHASESELECT:
            """Selects the phase for channel 0 in group 6."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX60INVERT:
            """Inverts the channel 0 in group 6."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX60ACBIAS:
            """Enables the common mode generation for channel 0 in group 6."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX60TERM:
            """Enables the 100 Ohm termination for channel 0 in group 6."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX60EQ:
            """Equalization control for channel 0 in group 6."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX61CHNCNTR:
        """Configuration of the channel 1 in group 6"""

        address = 0x00E9

        @staticmethod
        def __str__():
            return "EPRX61ChnCntr"

        @staticmethod
        def __int__():
            return 0x00E9

        class EPRX61PHASESELECT:
            """Selects the phase for channel 1 in group 6."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX61INVERT:
            """Inverts the channel 1 in group 6."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX61ACBIAS:
            """Enables the common mode generation for channel 1 in group 6."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX61TERM:
            """Enables the 100 Ohm termination for channel 1 in group 6."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX61EQ:
            """Equalization control for channel 1 in group 6."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX62CHNCNTR:
        """Configuration of the channel 2 in group 6"""

        address = 0x00EA

        @staticmethod
        def __str__():
            return "EPRX62ChnCntr"

        @staticmethod
        def __int__():
            return 0x00EA

        class EPRX62PHASESELECT:
            """Selects the phase for channel 2 in group 6."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX62INVERT:
            """Inverts the channel 2 in group 6."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX62ACBIAS:
            """Enables the common mode generation for channel 2 in group 6."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX62TERM:
            """Enables the 100 Ohm termination for channel 2 in group 6."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX62EQ:
            """Equalization control for channel 2 in group 6."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRX63CHNCNTR:
        """Configuration of the channel 3 in group 6"""

        address = 0x00EB

        @staticmethod
        def __str__():
            return "EPRX63ChnCntr"

        @staticmethod
        def __int__():
            return 0x00EB

        class EPRX63PHASESELECT:
            """Selects the phase for channel 3 in group 6."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX63INVERT:
            """Inverts the channel 3 in group 6."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX63ACBIAS:
            """Enables the common mode generation for channel 3 in group 6."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX63TERM:
            """Enables the 100 Ohm termination for channel 3 in group 6."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX63EQ:
            """Equalization control for channel 3 in group 6."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRXECCHNCNTR:
        """Configuration of the EC channel in ePortRx"""

        address = 0x00EC

        @staticmethod
        def __str__():
            return "EPRXEcChnCntr"

        @staticmethod
        def __int__():
            return 0x00EC

        class EPRXECPHASESELECT:
            """Static phase for the EC channel."""

            offset = 4
            length = 3
            bit_mask = 112

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPRXECINVERT:
            """Inverts the EC channel data input."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRXECACBIAS:
            """Enables the common mode generation for the EC channel."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRXECTERM:
            """Enables the 100 Ohm termination for EC channel."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRXECPULLUPENABLE:
            """Enable pull up for the EC channel."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRXEQ10CONTROL:
        """Eport Rx equalization control for groups 1 and 0"""

        address = 0x00ED

        @staticmethod
        def __str__():
            return "EPRXEq10Control"

        @staticmethod
        def __int__():
            return 0x00ED

        class EPRX13EQ:
            """Equalization control for channel 3 in group 1.

            +---------------------+---------------------+---------------------+
            | EPRX13Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX12EQ:
            """Equalization control for channel 2 in group 1.

            +---------------------+---------------------+---------------------+
            | EPRX12Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX11EQ:
            """Equalization control for channel 1 in group 1.

            +---------------------+---------------------+---------------------+
            | EPRX11Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX10EQ:
            """Equalization control for channel 0 in group 1.

            +---------------------+---------------------+---------------------+
            | EPRX10Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX03EQ:
            """Equalization control for channel 3 in group 0.

            +---------------------+---------------------+---------------------+
            | EPRX03Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX02EQ:
            """Equalization control for channel 2 in group 0.

            +---------------------+---------------------+---------------------+
            | EPRX02Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX01EQ:
            """Equalization control for channel 1 in group 0.

            +---------------------+---------------------+---------------------+
            | EPRX01Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX00EQ:
            """Equalization control for channel 0 in group 0.

            +---------------------+---------------------+---------------------+
            | EPRX00Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRXEQ32CONTROL:
        """Eport Rx equalization control for groups 3 and 2"""

        address = 0x00EE

        @staticmethod
        def __str__():
            return "EPRXEq32Control"

        @staticmethod
        def __int__():
            return 0x00EE

        class EPRX33EQ:
            """Equalization control for channel 3 in group 3.

            +---------------------+---------------------+---------------------+
            | EPRX33Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX32EQ:
            """Equalization control for channel 2 in group 3.

            +---------------------+---------------------+---------------------+
            | EPRX32Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX31EQ:
            """Equalization control for channel 1 in group 3.

            +---------------------+---------------------+---------------------+
            | EPRX31Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX30EQ:
            """Equalization control for channel 0 in group 3.

            +---------------------+---------------------+---------------------+
            | EPRX30Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX23EQ:
            """Equalization control for channel 3 in group 2.

            +---------------------+---------------------+---------------------+
            | EPRX23Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX22EQ:
            """Equalization control for channel 2 in group 2.

            +---------------------+---------------------+---------------------+
            | EPRX22Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX21EQ:
            """Equalization control for channel 1 in group 2.

            +---------------------+---------------------+---------------------+
            | EPRX21Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX20EQ:
            """Equalization control for channel 0 in group 2.

            +---------------------+---------------------+---------------------+
            | EPRX20Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRXEQ54CONTROL:
        """Eport Rx equalization control for groups 5 and 4"""

        address = 0x00EF

        @staticmethod
        def __str__():
            return "EPRXEq54Control"

        @staticmethod
        def __int__():
            return 0x00EF

        class EPRX53EQ:
            """Equalization control for channel 3 in group 5.

            +---------------------+---------------------+---------------------+
            | EPRX53Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX52EQ:
            """Equalization control for channel 2 in group 5.

            +---------------------+---------------------+---------------------+
            | EPRX52Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX51EQ:
            """Equalization control for channel 1 in group 5.

            +---------------------+---------------------+---------------------+
            | EPRX51Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX50EQ:
            """Equalization control for channel 0 in group 5.

            +---------------------+---------------------+---------------------+
            | EPRX50Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX43EQ:
            """Equalization control for channel 3 in group 4.

            +---------------------+---------------------+---------------------+
            | EPRX43Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX42EQ:
            """Equalization control for channel 2 in group 4.

            +---------------------+---------------------+---------------------+
            | EPRX42Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX41EQ:
            """Equalization control for channel 1 in group 4.

            +---------------------+---------------------+---------------------+
            | EPRX41Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX40EQ:
            """Equalization control for channel 0 in group 4.

            +---------------------+---------------------+---------------------+
            | EPRX40Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRXEQ6CONTROL:
        """Eport Rx equalization control for group6"""

        address = 0x00F0

        @staticmethod
        def __str__():
            return "EPRXEq6Control"

        @staticmethod
        def __int__():
            return 0x00F0

        class EPRX63EQ:
            """Equalization control for channel 3 in group 6.

            +---------------------+---------------------+---------------------+
            | EPRX63Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX62EQ:
            """Equalization control for channel 2 in group 6.

            +---------------------+---------------------+---------------------+
            | EPRX62Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX61EQ:
            """Equalization control for channel 1 in group 6.

            +---------------------+---------------------+---------------------+
            | EPRX61Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX60EQ:
            """Equalization control for channel 0 in group 6.

            +---------------------+---------------------+---------------------+
            | EPRX60Eq[1:0]       | Zero location [MHz] | Peaking [dB]        |
            +=====================+=====================+=====================+
            | 2'd0                | N/A                 | N/A                 |
            +---------------------+---------------------+---------------------+
            | 2'd1                | 300                 | 4.9                 |
            +---------------------+---------------------+---------------------+
            | 2'd2                | 125                 | 7.8                 |
            +---------------------+---------------------+---------------------+
            | 2'd3                | 70                  | 10.7                |
            +---------------------+---------------------+---------------------+

            """

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRXDLLCONFIG:
        """Configuration register containing settings for EPRX DLLs. This register contains also auxiliary EPRX setting."""

        address = 0x00F1

        @staticmethod
        def __str__():
            return "EPRXDllConfig"

        @staticmethod
        def __int__():
            return 0x00F1

        class EPRXDLLCURRENT:
            """Current for the DLL charge pump (default: 1).

            +-----------------------+---------------------+------------------------+
            | EPRXDllCurrent[1:0]   | Current [uA]                                 |
            +=======================+=====================+========================+
            | 2'd0                  | 1                                            |
            +-----------------------+---------------------+------------------------+
            | 2'd1                  | 2                                            |
            +-----------------------+---------------------+------------------------+
            | 2'd2                  | 4                                            |
            +-----------------------+---------------------+------------------------+
            | 2'd3                  | 8                                            |
            +-----------------------+---------------------+------------------------+

            """

            offset = 6
            length = 2
            bit_mask = 192

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPRXDLLCONFIRMCOUNT:
            """Number of clock cycles (in the 40 MHz clock domain)
            to confirm locked state  (default: 2).

            +----------------------------+---------------------+------------------------+
            | EPRXDLLConfirmCount[1:0]   | Number of clock cycles                       |
            +============================+=====================+========================+
            | 2'd0                       | 1                                            |
            +----------------------------+---------------------+------------------------+
            | 2'd1                       | 4                                            |
            +----------------------------+---------------------+------------------------+
            | 2'd2                       | 16                                           |
            +----------------------------+---------------------+------------------------+
            | 2'd3                       | 31                                           |
            +----------------------------+---------------------+------------------------+

            """

            offset = 4
            length = 2
            bit_mask = 48

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPRXDLLFSMCLKALWAYSON:
            """Force clock of ePortRx DLL state machine to be always enabled (disables clock gating)"""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRXDLLCOARSELOCKDETECTION:
            """Use coarse detector for the DLL lock condition"""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRXENABLEREINIT:
            """Enables the re-initialization of an ePortRxGroup when the phase-aligner state machine finds the phase-selection to be out of range (default: 0)"""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRXDATAGATINGDISABLE:
            """Disable data gating. When the data gating is enabled (**EPRXDataGatingDisable** bit set to zero) the ePortRx group consumes less power. This is a recommended mode of operation (default: 0)"""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRXLOCKFILTER:
        """Lock filter settings for DLL in ePortRx"""

        address = 0x00F2

        @staticmethod
        def __str__():
            return "EPRXLockFilter"

        @staticmethod
        def __int__():
            return 0x00F2

        class EPRXLOCKTHRESHOLD:
            """Sets the lock threshold value of the instant lock low pass filter for ePortRx DLL's.
            The number of 40 MHz clock cycles is set to :math:`2^{7-EPRXLockThreshold}` (default: 0)
            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class EPRXRELOCKTHRESHOLD:
            """Sets the relock threshold value of the instant lock low pass filter for ePortRx DLL's.
            The number of 40 MHz clock cycles is set to :math:`2^{7-EPRXReLockThreshold}` (default: 0)
            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPRXLOCKFILTER2:
        """Lock filter settings for DLL in ePortRx"""

        address = 0x00F3

        @staticmethod
        def __str__():
            return "EPRXLockFilter2"

        @staticmethod
        def __int__():
            return 0x00F3

        class EPRXUNLOCKTHRESHOLD:
            """Sets the unlock threshold value of the instant lock low pass filter for ePortRx DLL's.
            The number of 40 MHz clock cycles is set to :math:`2^{7-EPRXUnLockThreshold}` (default: 0)
            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class RESERVED4:
        """Reserved register."""

        address = 0x00F4

        @staticmethod
        def __str__():
            return "RESERVED4"

        @staticmethod
        def __int__():
            return 0x00F4

    class RESERVED5:
        """Reserved register."""

        address = 0x00F5

        @staticmethod
        def __str__():
            return "RESERVED5"

        @staticmethod
        def __int__():
            return 0x00F5

    class RESERVED6:
        """Reserved register."""

        address = 0x00F6

        @staticmethod
        def __str__():
            return "RESERVED6"

        @staticmethod
        def __int__():
            return 0x00F6

    class READY:
        """Register controlling the behavior of `READY` pin. The signal for the `READY` pin is calculated according to:  .. code-block::     READY = (!ReadyCHNSEnable | ChannelsLocked) &             (!ReadyDLLSEnable | DLLInstantLock) &                        (!ReadyCHNSEnable | CLKGInstantLock) &                        (!ReadyPUSMDisable & PUSMready)        It is recommended to leave this register set to 0."""

        address = 0x00F7

        @staticmethod
        def __str__():
            return "READY"

        @staticmethod
        def __int__():
            return 0x00F7

        class READYCHNSENABLE:
            """When this bit is set, the `READY` signal will go low when one of the ePortRx channels is unlocked. Not recommended."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class READYDLLSENABLE:
            """When this bit is set, the `READY` signal will go low when one of the DLLs declares a temporary loss of lock. Not recommended."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class READYCLKGENABLE:
            """When this bit is set, the `READY` signal will go low when the clock generator (or frame aligner) declares a temporary loss of lock. Not recommended."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class READYPUSMDISABLE:
            """When this bit is set, the `READY` signal will not depend on PUSM state. Not recommended."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class WATCHDOG:
        """Watchdog configuration register"""

        address = 0x00F8

        @staticmethod
        def __str__():
            return "WATCHDOG"

        @staticmethod
        def __int__():
            return 0x00F8

        class PUSMCHECKSUMWDOGENABLE:
            """Enables watchdog monitoring data integrity of the configuration memory (CRC) when the chip is in the ready state."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class PUSMPLLWDOGDISABLE:
            """Disables watch dog monitoring PLL locked signal"""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class PUSMDLLWDOGDISABLE:
            """Disables watch dog monitoring DLL locked signal"""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class POWERUP0:
        """Controls behavior of the power-up state machine (for more details refer to :ref:`powerUpStateMachine`)"""

        address = 0x00F9

        @staticmethod
        def __str__():
            return "POWERUP0"

        @staticmethod
        def __int__():
            return 0x00F9

        class PUSMREADYWHENCHNSLOCKED:
            """When selected, ready signal is reported only
            after all enabled channels in all ePortRx groups are locked
            """

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class PUSMPLLTIMEOUTCONFIG:
            """Determines the timeout duration  in the **WAIT_PLL_LOCK** state in the power-up state machine. For more details
            see :ref:`powerUpStateMachine`

               +----------------------------------+------------------------------------------------------------+
               | PUSMPllTimeoutConfig[3:0]        | Wait time                                                  |
               +==================================+============================================================+
               | 4'd0                             | 1 s                                                        |
               +----------------------------------+------------------------------------------------------------+
               | 4'd1                             | 500 ms                                                     |
               +----------------------------------+------------------------------------------------------------+
               | 4'd2                             | 100 ms                                                     |
               +----------------------------------+------------------------------------------------------------+
               | 4'd3                             | 50 ms                                                      |
               +----------------------------------+------------------------------------------------------------+
               | 4'd4                             | 20 ms                                                      |
               +----------------------------------+------------------------------------------------------------+
               | 4'd5                             | 10 ms                                                      |
               +----------------------------------+------------------------------------------------------------+
               | 4'd6                             | 5 ms                                                       |
               +----------------------------------+------------------------------------------------------------+
               | 4'd7                             | 2 ms                                                       |
               +----------------------------------+------------------------------------------------------------+
               | 4'd8                             | 1 ms                                                       |
               +----------------------------------+------------------------------------------------------------+
               | 4'd9                             | 500 us                                                     |
               +----------------------------------+------------------------------------------------------------+
               | 4'd10                            | 200 us                                                     |
               +----------------------------------+------------------------------------------------------------+
               | 4'd11                            | 100 us                                                     |
               +----------------------------------+------------------------------------------------------------+
               | 4'd12                            | 50 us                                                      |
               +----------------------------------+------------------------------------------------------------+
               | 4'd13                            | 20 us                                                      |
               +----------------------------------+------------------------------------------------------------+
               | 4'd14                            | 10 us                                                      |
               +----------------------------------+------------------------------------------------------------+
               | 4'd15                            | disabled                                                   |
               +----------------------------------+------------------------------------------------------------+

            """

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class POWERUP1:
        """Controls behavior of the power-up state machine (for more details refer to :ref:`powerUpStateMachine`)"""

        address = 0x00FA

        @staticmethod
        def __str__():
            return "POWERUP1"

        @staticmethod
        def __int__():
            return 0x00FA

        class PUSMDLLTIMEOUTCONFIG:
            """Determines the timeout duration  in the **WAIT_DLL_LOCK** state in the power-up state machine. For more details
            see :ref:`powerUpStateMachine`

               +----------------------------------+------------------------------------------------------------+
               | PUSMDllTimeoutConfig[3:0]        | Wait time                                                  |
               +==================================+============================================================+
               | 4'd0                             | 1 s                                                        |
               +----------------------------------+------------------------------------------------------------+
               | 4'd1                             | 500 ms                                                     |
               +----------------------------------+------------------------------------------------------------+
               | 4'd2                             | 100 ms                                                     |
               +----------------------------------+------------------------------------------------------------+
               | 4'd3                             | 50 ms                                                      |
               +----------------------------------+------------------------------------------------------------+
               | 4'd4                             | 20 ms                                                      |
               +----------------------------------+------------------------------------------------------------+
               | 4'd5                             | 10 ms                                                      |
               +----------------------------------+------------------------------------------------------------+
               | 4'd6                             | 5 ms                                                       |
               +----------------------------------+------------------------------------------------------------+
               | 4'd7                             | 2 ms                                                       |
               +----------------------------------+------------------------------------------------------------+
               | 4'd8                             | 1 ms                                                       |
               +----------------------------------+------------------------------------------------------------+
               | 4'd9                             | 500 us                                                     |
               +----------------------------------+------------------------------------------------------------+
               | 4'd10                            | 200 us                                                     |
               +----------------------------------+------------------------------------------------------------+
               | 4'd11                            | 100 us                                                     |
               +----------------------------------+------------------------------------------------------------+
               | 4'd12                            | 50 us                                                      |
               +----------------------------------+------------------------------------------------------------+
               | 4'd13                            | 20 us                                                      |
               +----------------------------------+------------------------------------------------------------+
               | 4'd14                            | 10 us                                                      |
               +----------------------------------+------------------------------------------------------------+
               | 4'd15                            | disabled                                                   |
               +----------------------------------+------------------------------------------------------------+

            """

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class PUSMCHANNELSTIMEOUTCONFIG:
            """Determines the timeout duration  in the **WAIT_CHNS_LOCKED** state in the power-up state machine. For more details
            see :ref:`powerUpStateMachine`.

               +----------------------------------+------------------------------------------------------------+
               | PUSMChannelsTimeoutConfig[3:0]   | Wait time                                                  |
               +==================================+============================================================+
               | 4'd0                             | 1 s                                                        |
               +----------------------------------+------------------------------------------------------------+
               | 4'd1                             | 500 ms                                                     |
               +----------------------------------+------------------------------------------------------------+
               | 4'd2                             | 100 ms                                                     |
               +----------------------------------+------------------------------------------------------------+
               | 4'd3                             | 50 ms                                                      |
               +----------------------------------+------------------------------------------------------------+
               | 4'd4                             | 20 ms                                                      |
               +----------------------------------+------------------------------------------------------------+
               | 4'd5                             | 10 ms                                                      |
               +----------------------------------+------------------------------------------------------------+
               | 4'd6                             | 5 ms                                                       |
               +----------------------------------+------------------------------------------------------------+
               | 4'd7                             | 2 ms                                                       |
               +----------------------------------+------------------------------------------------------------+
               | 4'd8                             | 1 ms                                                       |
               +----------------------------------+------------------------------------------------------------+
               | 4'd9                             | 500 us                                                     |
               +----------------------------------+------------------------------------------------------------+
               | 4'd10                            | 200 us                                                     |
               +----------------------------------+------------------------------------------------------------+
               | 4'd11                            | 100 us                                                     |
               +----------------------------------+------------------------------------------------------------+
               | 4'd12                            | 50 us                                                      |
               +----------------------------------+------------------------------------------------------------+
               | 4'd13                            | 20 us                                                      |
               +----------------------------------+------------------------------------------------------------+
               | 4'd14                            | 10 us                                                      |
               +----------------------------------+------------------------------------------------------------+
               | 4'd15                            | disabled                                                   |
               +----------------------------------+------------------------------------------------------------+

            """

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class POWERUP2:
        """Controls behavior of the power-up state machine (for more details refer to :ref:`powerUpStateMachine`)"""

        address = 0x00FB

        @staticmethod
        def __str__():
            return "POWERUP2"

        @staticmethod
        def __int__():
            return 0x00FB

        class DLLCONFIGDONE:
            """When asserted, the power-up state machine is allowed to proceed to PLL initialization. Please refer :ref:`configuration` for more details."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class PLLCONFIGDONE:
            """When asserted, the power-up state machine is allowed to proceed to initialization of components containing DLLs (ePortRx, phase-shifter). Please refer :ref:`configuration` for more details."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

    class CRC0:
        """Cyclic redundancy checksum for configuration memory."""

        address = 0x00FC

        @staticmethod
        def __str__():
            return "CRC0"

        @staticmethod
        def __int__():
            return 0x00FC

        class CRC32:
            """Bits 7:0 of CRC. Refer to :ref:`crc` for more details."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class CRC1:
        """Cyclic redundancy checksum for configuration memory."""

        address = 0x00FD

        @staticmethod
        def __str__():
            return "CRC1"

        @staticmethod
        def __int__():
            return 0x00FD

        class CRC32:
            """Bits 15:8 of CRC. Refer to :ref:`crc` for more details."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class CRC2:
        """Cyclic redundancy checksum for configuration memory."""

        address = 0x00FE

        @staticmethod
        def __str__():
            return "CRC2"

        @staticmethod
        def __int__():
            return 0x00FE

        class CRC32:
            """Bits 23:16 of CRC. Refer to :ref:`crc` for more details."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class CRC3:
        """Cyclic redundancy checksum for configuration memory."""

        address = 0x00FF

        @staticmethod
        def __str__():
            return "CRC3"

        @staticmethod
        def __int__():
            return 0x00FF

        class CRC32:
            """Bits 31:24 of CRC. Refer to :ref:`crc` for more details."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM0CONFIG:
        """General configuration register for I2C Master 0"""

        address = 0x0100

        @staticmethod
        def __str__():
            return "I2CM0Config"

        @staticmethod
        def __int__():
            return 0x0100

        class I2CM0SCLPULLUPENABLE:
            """Enable pull up for M0SCL pin."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM0SCLDRIVESTRENGTH:
            """M0SCL drive strength (:ref:`cmos_io_characteristics`)"""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM0SDAPULLUPENABLE:
            """Enable pull up for M0SDA pin."""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM0SDADRIVESTRENGTH:
            """M0SDA drive strength (:ref:`cmos_io_characteristics`)."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM0ADDRESSEXT:
            """3 additional bits of address of slave to address in an I2C transaction for I2C Master 0; only used in commands with 10-bit addressing"""

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class I2CM0ADDRESS:
        """7 bits of address of slave to address in an I2C transaction for I2C Master 0"""

        address = 0x0101

        @staticmethod
        def __str__():
            return "I2CM0Address"

        @staticmethod
        def __int__():
            return 0x0101

        class I2CM0ADDRESS:
            """7 bits of address of slave to address in an I2C transaction"""

            offset = 0
            length = 7
            bit_mask = 127

            @staticmethod
            def validate(value):
                return value in range(128)

    class I2CM0DATA0:
        """Data input for I2C Master 0"""

        address = 0x0102

        @staticmethod
        def __str__():
            return "I2CM0Data0"

        @staticmethod
        def __int__():
            return 0x0102

        class I2CM0DATA:
            """Bits 7:0 of the data input"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM0DATA1:
        """Data input for I2C Master 0"""

        address = 0x0103

        @staticmethod
        def __str__():
            return "I2CM0Data1"

        @staticmethod
        def __int__():
            return 0x0103

        class I2CM0DATA:
            """Bits 15:8 of the data input"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM0DATA2:
        """Data input for I2C Master 0"""

        address = 0x0104

        @staticmethod
        def __str__():
            return "I2CM0Data2"

        @staticmethod
        def __int__():
            return 0x0104

        class I2CM0DATA:
            """Bits 23:16 of the data input"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM0DATA3:
        """Data input for I2C Master 0"""

        address = 0x0105

        @staticmethod
        def __str__():
            return "I2CM0Data3"

        @staticmethod
        def __int__():
            return 0x0105

        class I2CM0DATA:
            """Bits 31:24 of the data input"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM0CMD:
        """Command word register for I2C Master 0"""

        address = 0x0106

        @staticmethod
        def __str__():
            return "I2CM0Cmd"

        @staticmethod
        def __int__():
            return 0x0106

        class I2CM0CMD:
            """Command word."""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class I2CM1CONFIG:
        """General configuration register for I2C Master 1"""

        address = 0x0107

        @staticmethod
        def __str__():
            return "I2CM1Config"

        @staticmethod
        def __int__():
            return 0x0107

        class I2CM1SCLPULLUPENABLE:
            """Enable pull up for M1SCL pin."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM1SCLDRIVESTRENGTH:
            """M1SCL drive strength (:ref:`cmos_io_characteristics`)"""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM1SDAPULLUPENABLE:
            """Enable pull up for M1SDA pin."""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM1SDADRIVESTRENGTH:
            """M1SDA drive strength (:ref:`cmos_io_characteristics`)."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM1ADDRESSEXT:
            """3 additional bits of address of slave to address in an I2C transaction for I2C Master 1; only used in commands with 10-bit addressing"""

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class I2CM1ADDRESS:
        """7 bits of address of slave to address in an I2C transaction for I2C Master 1"""

        address = 0x0108

        @staticmethod
        def __str__():
            return "I2CM1Address"

        @staticmethod
        def __int__():
            return 0x0108

        class I2CM1ADDRESS:
            """7 bits of address of slave to address in an I2C transaction"""

            offset = 0
            length = 7
            bit_mask = 127

            @staticmethod
            def validate(value):
                return value in range(128)

    class I2CM1DATA0:
        """Data input for I2C Master 1"""

        address = 0x0109

        @staticmethod
        def __str__():
            return "I2CM1Data0"

        @staticmethod
        def __int__():
            return 0x0109

        class I2CM1DATA:
            """Bits 7:0 of the data input"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM1DATA1:
        """Data input for I2C Master 1"""

        address = 0x010A

        @staticmethod
        def __str__():
            return "I2CM1Data1"

        @staticmethod
        def __int__():
            return 0x010A

        class I2CM1DATA:
            """Bits 15:8 of the data input"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM1DATA2:
        """Data input for I2C Master 1"""

        address = 0x010B

        @staticmethod
        def __str__():
            return "I2CM1Data2"

        @staticmethod
        def __int__():
            return 0x010B

        class I2CM1DATA:
            """Bits 23:16 of the data input"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM1DATA3:
        """Data input for I2C Master 1"""

        address = 0x010C

        @staticmethod
        def __str__():
            return "I2CM1Data3"

        @staticmethod
        def __int__():
            return 0x010C

        class I2CM1DATA:
            """Bits 31:24 of the data input"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM1CMD:
        """Command word register for I2C Master 1"""

        address = 0x010D

        @staticmethod
        def __str__():
            return "I2CM1Cmd"

        @staticmethod
        def __int__():
            return 0x010D

        class I2CM1CMD:
            """Command word."""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class I2CM2CONFIG:
        """General configuration register for I2C Master 2"""

        address = 0x010E

        @staticmethod
        def __str__():
            return "I2CM2Config"

        @staticmethod
        def __int__():
            return 0x010E

        class I2CM2SCLPULLUPENABLE:
            """Enable pull up for M2SCL pin."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM2SCLDRIVESTRENGTH:
            """M2SCL drive strength (:ref:`cmos_io_characteristics`)"""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM2SDAPULLUPENABLE:
            """Enable pull up for M2SDA pin."""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM2SDADRIVESTRENGTH:
            """M2SDA drive strength (:ref:`cmos_io_characteristics`)."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM2ADDRESSEXT:
            """3 additional bits of address of slave to address in an I2C transaction for I2C Master 2; only used in commands with 10-bit addressing"""

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class I2CM2ADDRESS:
        """7 bits of address of slave to address in an I2C transaction for I2C Master 2"""

        address = 0x010F

        @staticmethod
        def __str__():
            return "I2CM2Address"

        @staticmethod
        def __int__():
            return 0x010F

        class I2CM2ADDRESS:
            """7 bits of address of slave to address in an I2C transaction"""

            offset = 0
            length = 7
            bit_mask = 127

            @staticmethod
            def validate(value):
                return value in range(128)

    class I2CM2DATA0:
        """Data input for I2C Master 2"""

        address = 0x0110

        @staticmethod
        def __str__():
            return "I2CM2Data0"

        @staticmethod
        def __int__():
            return 0x0110

        class I2CM2DATA:
            """Bits 7:0 of the data input"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM2DATA1:
        """Data input for I2C Master 2"""

        address = 0x0111

        @staticmethod
        def __str__():
            return "I2CM2Data1"

        @staticmethod
        def __int__():
            return 0x0111

        class I2CM2DATA:
            """Bits 15:8 of the data input"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM2DATA2:
        """Data input for I2C Master 2"""

        address = 0x0112

        @staticmethod
        def __str__():
            return "I2CM2Data2"

        @staticmethod
        def __int__():
            return 0x0112

        class I2CM2DATA:
            """Bits 23:16 of the data input"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM2DATA3:
        """Data input for I2C Master 2"""

        address = 0x0113

        @staticmethod
        def __str__():
            return "I2CM2Data3"

        @staticmethod
        def __int__():
            return 0x0113

        class I2CM2DATA:
            """Bits 31:24 of the data input"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM2CMD:
        """Command word register for I2C Master 2"""

        address = 0x0114

        @staticmethod
        def __str__():
            return "I2CM2Cmd"

        @staticmethod
        def __int__():
            return 0x0114

        class I2CM2CMD:
            """Command word."""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class EPRXTRAIN10:
        """Channel phase training request for groups 1 and 0"""

        address = 0x0115

        @staticmethod
        def __str__():
            return "EPRXTrain10"

        @staticmethod
        def __int__():
            return 0x0115

        class EPRX1TRAIN:
            """Initialize phase training. N-th bit control N-th channel training.
            One should assert bits corresponding to channels to be trained and dessert them.
            """

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX0TRAIN:
            """Initialize phase training. N-th bit control N-th channel training.
            One should assert bits corresponding to channels to be trained and dessert them.
            """

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class EPRXTRAIN32:
        """Channel phase training request for groups 3 and 2"""

        address = 0x0116

        @staticmethod
        def __str__():
            return "EPRXTrain32"

        @staticmethod
        def __int__():
            return 0x0116

        class EPRX3TRAIN:
            """Initialize phase training. N-th bit control N-th channel training.
            One should assert bits corresponding to channels to be trained and dessert them.
            """

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX2TRAIN:
            """Initialize phase training. N-th bit control N-th channel training.
            One should assert bits corresponding to channels to be trained and dessert them.
            """

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class EPRXTRAIN54:
        """Channel phase training request for groups 5 and 4"""

        address = 0x0117

        @staticmethod
        def __str__():
            return "EPRXTrain54"

        @staticmethod
        def __int__():
            return 0x0117

        class EPRX5TRAIN:
            """Initialize phase training. N-th bit control N-th channel training.
            One should assert bits corresponding to channels to be trained and dessert them.
            """

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX4TRAIN:
            """Initialize phase training. N-th bit control N-th channel training.
            One should assert bits corresponding to channels to be trained and dessert them.
            """

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class EPRXTRAINEC6:
        """Channel phase training request for group 6 and EC channel"""

        address = 0x0118

        @staticmethod
        def __str__():
            return "EPRXTrainEc6"

        @staticmethod
        def __int__():
            return 0x0118

        class EPRX6TRAIN:
            """Initialize phase training. N-th bit control N-th channel training.
            One should assert bits corresponding to channels to be trained and dessert them.
            """

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class FUSECONTROL:
        """Fuse control register."""

        address = 0x0119

        @staticmethod
        def __str__():
            return "FUSEControl"

        @staticmethod
        def __int__():
            return 0x0119

        class FUSEBLOWPULSELENGTH:
            """Duration of fuse blowing pulse (default:12)."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class FUSEREAD:
            """Execute fuse readout sequence."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class FUSEBLOW:
            """Execute fuse blowing sequence."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class FUSEBLOWDATAA:
        """Data to be programmed to the fuses."""

        address = 0x011A

        @staticmethod
        def __str__():
            return "FUSEBlowDataA"

        @staticmethod
        def __int__():
            return 0x011A

        class FUSEBLOWDATA:
            """Bits 7:0 of the data word."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class FUSEBLOWDATAB:
        """Data to be programmed to the fuses."""

        address = 0x011B

        @staticmethod
        def __str__():
            return "FUSEBlowDataB"

        @staticmethod
        def __int__():
            return 0x011B

        class FUSEBLOWDATA:
            """Bits 15:8 of the data word."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class FUSEBLOWDATAC:
        """Data to be programmed to the fuses."""

        address = 0x011C

        @staticmethod
        def __str__():
            return "FUSEBlowDataC"

        @staticmethod
        def __int__():
            return 0x011C

        class FUSEBLOWDATA:
            """Bits 23:16 of the data word."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class FUSEBLOWDATAD:
        """Data to be programmed to the fuses."""

        address = 0x011D

        @staticmethod
        def __str__():
            return "FUSEBlowDataD"

        @staticmethod
        def __int__():
            return 0x011D

        class FUSEBLOWDATA:
            """Bits 31:24 of the data word."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class FUSEBLOWADDH:
        """Address of the fuse block to be programmed."""

        address = 0x011E

        @staticmethod
        def __str__():
            return "FUSEBlowAddH"

        @staticmethod
        def __int__():
            return 0x011E

        class FUSEBLOWADDRESS:
            """Bits 15:8 of the address."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class FUSEBLOWADDL:
        """Address of the fuse block to be programmed."""

        address = 0x011F

        @staticmethod
        def __str__():
            return "FUSEBlowAddL"

        @staticmethod
        def __int__():
            return 0x011F

        class FUSEBLOWADDRESS:
            """Bits 7:0 of the address."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class FUSEMAGIC:
        """Registers containing magic number for the fuse block."""

        address = 0x0120

        @staticmethod
        def __str__():
            return "FuseMagic"

        @staticmethod
        def __int__():
            return 0x0120

        class FUSEMAGICNUMBER:
            """One has to write a magic number ``0xA3`` to this register in order to unlock fuse blowing."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class ADCSELECT:
        """ADC MUXes control."""

        address = 0x0121

        @staticmethod
        def __str__():
            return "ADCSelect"

        @staticmethod
        def __int__():
            return 0x0121

        class ADCINPSELECT:
            """Controls MUX for ADC Positive Input

            =================================  ========================================
            ADCInPSelect[3:0]                     Input
            =================================  ========================================
             4'd0                               ADC0 (external pin)
             4'd1                               ADC1 (external pin)
             4'd2                               ADC2 (external pin)
             4'd3                               ADC3 (external pin)
             4'd4                               ADC4 (external pin)
             4'd5                               ADC5 (external pin)
             4'd6                               ADC6 (external pin)
             4'd7                               ADC7 (external pin)
             4'd8                               Voltage DAC output  (internal signal)
             4'd9                               VSSA  (internal signal)
             4'd10                              VDDTX * 0.42  (internal signal)
             4'd11                              VDDRX * 0.42  (internal signal)
             4'd12                              VDD * 0.42  (internal signal)
             4'd13                              VDDA * 0.42  (internal signal)
             4'd14                              Temperature sensor (internal signal)
             4'd15                              VREF / 2  (internal signal)
            =================================  ========================================

            """

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class ADCINNSELECT:
            """Controls MUX for ADC Negative Input

            =================================  ========================================
            ADCInNSelect[3:0]                     Input
            =================================  ========================================
             4'd0                               ADC0 (external pin)
             4'd1                               ADC1 (external pin)
             4'd2                               ADC2 (external pin)
             4'd3                               ADC3 (external pin)
             4'd4                               ADC4 (external pin)
             4'd5                               ADC5 (external pin)
             4'd6                               ADC6 (external pin)
             4'd7                               ADC7 (external pin)
             4'd8                               Voltage DAC output  (internal signal)
             4'd9                               VSSA  (internal signal)
             4'd10                              VDDTX * 0.42  (internal signal)
             4'd11                              VDDRX * 0.42  (internal signal)
             4'd12                              VDD * 0.42  (internal signal)
             4'd13                              VDDA * 0.42  (internal signal)
             4'd14                              Temperature sensor (internal signal)
             4'd15                              VREF / 2  (internal signal)
            =================================  ========================================

            """

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class ADCMON:
        """Control ADC's internal signals"""

        address = 0x0122

        @staticmethod
        def __str__():
            return "ADCMon"

        @staticmethod
        def __int__():
            return 0x0122

        class TEMPSENSRESET:
            """Resets temperature sensor."""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class VDDMONENA:
            """Enable resistive divider for VDD probing."""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class VDDTXMONENA:
            """Enable resistive divider for VDDTX probing."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class VDDRXMONENA:
            """Enable resistive divider for VDDRX probing."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class VDDANMONENA:
            """Enable resistive divider for VDDAB probing."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class ADCCONFIG:
        """ADC configuration register"""

        address = 0x0123

        @staticmethod
        def __str__():
            return "ADCConfig"

        @staticmethod
        def __int__():
            return 0x0123

        class ADCCONVERT:
            """Start ADC conversion."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class ADCENABLE:
            """Enables ADC core and differential amplifier."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class ADCGAINSELECT:
            """Selects gain for the differential amplifier

            =================================  ========================================
            ADCGainSel[1:0]                     Gain
            =================================  ========================================
             2'd0                               x2
             2'd1                               x8
             2'd2                               x16
             2'd3                               x32
            =================================  ========================================

            """

            offset = 0
            length = 2
            bit_mask = 3

            @staticmethod
            def validate(value):
                return value in range(4)

    class EOMCONFIGH:
        """"""

        address = 0x0124

        @staticmethod
        def __str__():
            return "EOMConfigH"

        @staticmethod
        def __int__():
            return 0x0124

        class EOMENDOFCOUNTSEL:
            """Amount of refClk clock cycles (40 MHz cycles) the EOM counter is gated (2^(selEndOfCount+1)). The maximum allowed is 10 (decimal) to not overflow ``EOMcounterValue[15:0]``."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EOMBYPASSPHASEINTERPOLATOR:
            """Bypass the VCO 5.12 GHz clock (uses the refClk as the phase interpolated clock; the phase interpolation has to be done off-chip) [0 - vco, 1 - refClk]"""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EOMSTART:
            """Starts EOM acquisition"""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EOMENABLE:
            """Enables the EOM; wait few ms for all bias voltages to stabilize before starting EOM measurement"""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EOMCONFIGL:
        """"""

        address = 0x0125

        @staticmethod
        def __str__():
            return "EOMConfigL"

        @staticmethod
        def __int__():
            return 0x0125

        class EOMPHASESEL:
            """Selects the sampling phase from the phase interpolation block; steps [0:1/(fvco*64):63/(fvco*64)] s"""

            offset = 0
            length = 6
            bit_mask = 63

            @staticmethod
            def validate(value):
                return value in range(64)

    class EOMVOFSEL:
        """"""

        address = 0x0126

        @staticmethod
        def __str__():
            return "EOMvofSel"

        @staticmethod
        def __int__():
            return 0x0126

        class EOMVOFSEL:
            """Selects the comparison voltage; the comparator is differential; steps [-VDDRX/2:VDDRX/30:VDDRX/2] V; value 5'd32 is invalid"""

            offset = 0
            length = 5
            bit_mask = 31

            @staticmethod
            def validate(value):
                return value in range(32)

    class PROCESSANDSEUMONITOR:
        """Process Monitor block configuration register"""

        address = 0x0127

        @staticmethod
        def __str__():
            return "ProcessAndSeuMonitor"

        @staticmethod
        def __int__():
            return 0x0127

        class SEUENABLE:
            """Enable SEU counter."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class PMCHANNEL:
            """Select process monitor channel to be measured."""

            offset = 1
            length = 2
            bit_mask = 6

            @staticmethod
            def validate(value):
                return value in range(4)

        class PMENABLE:
            """Enable process monitor block."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class ULDATASOURCE0:
        """Uplink data path test patterns."""

        address = 0x0128

        @staticmethod
        def __str__():
            return "ULDataSource0"

        @staticmethod
        def __int__():
            return 0x0128

        class ULECDATASOURCE:
            """Data source for uplink EC channel

            ======================== ======================== ========================================================================
             ULGECDataSource[2:0]     Name                     Description
            ======================== ======================== ========================================================================
            3'd0                      EPORTRX_DATA             Normal mode of operation, data from ePortRx
            3'd1                      PRBS7                    PRBS7 test pattern
            3'd2                      BIN_CNTR_UP              Binary counter counting up
            3'd3                      BIN_CNTR_DOWN            Binary counter counting down
            3'd4                      CONST_PATTERN            Constant pattern (``DPDataPattern[1:0]``)
            3'd5                      CONST_PATTERN_INV        Constant pattern inverted (``~DPDataPattern[1:0]``)
            3'd6                      DLDATA_LOOPBACK          Loop back, downlink frame data
            3'd7                      Reserved                 Reserved
            ======================== ======================== ========================================================================


            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class ULSERTESTPATTERN:
            """Controls the serializer data source.

            ======================== ======================== ========================================================================
             ULSerTestPattern[3:0]    Name                     Description
            ======================== ======================== ========================================================================
            4'd0                      DATA                     Normal mode of operation
            4'd1                      PRBS7                    PRBS7 test pattern
            4'd2                      PRBS15                   PRBS15 test pattern
            4'd3                      PRBS23                   PRBS23 test pattern
            4'd4                      PRBS31                   PRBS31 test pattern
            4'd5                      CLK5G12                  5.12 GHz clock pattern (in 5Gbps mode it will produce only 2.56 GHz)
            4'd6                      CLK2G56                  2.56 GHz clock pattern
            4'd7                      CLK1G28                  1.28 GHz clock pattern
            4'd8                      CLK40M                   40 MHz clock pattern
            4'd9                      DLFRAME_10G24            Loopback, downlink frame repeated 4 times
            4'd10                     DLFRAME_5G12             Loopback, downlink frame repeated 2 times, each bit repeated 2 times
            4'd11                     DLFRAME_2G56             Loopback, downlink frame repeated 1 times, each bit repeated 4 times
            4'd12                     CONST PATTERN            8 x DPDataPattern[31:0]
            4'd13                     -                        Reserved
            4'd14                     -                        Reserved
            4'd15                     -                        Reserved
            ======================== ======================== ========================================================================


            """

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class ULDATASOURCE1:
        """Uplink data path test patterns."""

        address = 0x0129

        @staticmethod
        def __str__():
            return "ULDataSource1"

        @staticmethod
        def __int__():
            return 0x0129

        class LDDATASOURCE:
            """Data source for the line driver.

            ======================== ========================================================================
             LDDataSource[1:0]        Description
            ======================== ========================================================================
            2'd0                      Data from serializer (normal mode of operation)
            2'd1                      Data resampled by CDR loopback
            2'd2                      Equalizer output data loopback
            2'd3                      reserved
            ======================== ========================================================================

            """

            offset = 6
            length = 2
            bit_mask = 192

            @staticmethod
            def validate(value):
                return value in range(4)

        class ULG1DATASOURCE:
            """Data source for uplink data group 1

            ======================== ======================== ========================================================================
             ULG1DataSource[2:0]      Name                     Description
            ======================== ======================== ========================================================================
            3'd0                      EPORTRX_DATA             Normal mode of operation, data from ePortRx
            3'd1                      PRBS7                    PRBS7 test pattern
            3'd2                      BIN_CNTR_UP              Binary counter counting up
            3'd3                      BIN_CNTR_DOWN            Binary counter counting down
            3'd4                      CONST_PATTERN            Constant pattern (``DPDataPattern[31:0]``)
            3'd5                      CONST_PATTERN_INV        Constant pattern inverted (``~DPDataPattern[31:0]``)
            3'd6                      DLDATA_LOOPBACK          Loop back, downlink frame data
            3'd7                      Reserved                 Reserved
            ======================== ======================== ========================================================================


            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class ULG0DATASOURCE:
            """Data source for uplink data group 0

            ======================== ======================== ========================================================================
             ULG0DataSource[2:0]      Name                     Description
            ======================== ======================== ========================================================================
            3'd0                      EPORTRX_DATA             Normal mode of operation, data from ePortRx
            3'd1                      PRBS7                    PRBS7 test pattern
            3'd2                      BIN_CNTR_UP              Binary counter counting up
            3'd3                      BIN_CNTR_DOWN            Binary counter counting down
            3'd4                      CONST_PATTERN            Constant pattern (``DPDataPattern[31:0]``)
            3'd5                      CONST_PATTERN_INV        Constant pattern inverted (``~DPDataPattern[31:0]``)
            3'd6                      DLDATA_LOOPBACK          Loop back, downlink frame data
            3'd7                      Reserved                 Reserved
            ======================== ======================== ========================================================================


            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class ULDATASOURCE2:
        """Uplink data path test patterns."""

        address = 0x012A

        @staticmethod
        def __str__():
            return "ULDataSource2"

        @staticmethod
        def __int__():
            return 0x012A

        class ULG3DATASOURCE:
            """Data source for uplink data group 3

            ======================== ======================== ========================================================================
             ULG3DataSource[2:0]      Name                     Description
            ======================== ======================== ========================================================================
            3'd0                      EPORTRX_DATA             Normal mode of operation, data from ePortRx
            3'd1                      PRBS7                    PRBS7 test pattern
            3'd2                      BIN_CNTR_UP              Binary counter counting up
            3'd3                      BIN_CNTR_DOWN            Binary counter counting down
            3'd4                      CONST_PATTERN            Constant pattern (``DPDataPattern[31:0]``)
            3'd5                      CONST_PATTERN_INV        Constant pattern inverted (``~DPDataPattern[31:0]``)
            3'd6                      DLDATA_LOOPBACK          Loop back, downlink frame data
            3'd7                      Reserved                 Reserved
            ======================== ======================== ========================================================================


            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class ULG2DATASOURCE:
            """Data source for uplink data group 2

            ======================== ======================== ========================================================================
             ULG2DataSource[2:0]      Name                     Description
            ======================== ======================== ========================================================================
            3'd0                      EPORTRX_DATA             Normal mode of operation, data from ePortRx
            3'd1                      PRBS7                    PRBS7 test pattern
            3'd2                      BIN_CNTR_UP              Binary counter counting up
            3'd3                      BIN_CNTR_DOWN            Binary counter counting down
            3'd4                      CONST_PATTERN            Constant pattern (``DPDataPattern[31:0]``)
            3'd5                      CONST_PATTERN_INV        Constant pattern inverted (``~DPDataPattern[31:0]``)
            3'd6                      DLDATA_LOOPBACK          Loop back, downlink frame data
            3'd7                      Reserved                 Reserved
            ======================== ======================== ========================================================================


            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class ULDATASOURCE3:
        """Uplink data path test patterns."""

        address = 0x012B

        @staticmethod
        def __str__():
            return "ULDataSource3"

        @staticmethod
        def __int__():
            return 0x012B

        class ULG5DATASOURCE:
            """Data source for uplink data group 5

            ======================== ======================== ========================================================================
             ULG5DataSource[2:0]      Name                     Description
            ======================== ======================== ========================================================================
            3'd0                      EPORTRX_DATA             Normal mode of operation, data from ePortRx
            3'd1                      PRBS7                    PRBS7 test pattern
            3'd2                      BIN_CNTR_UP              Binary counter counting up
            3'd3                      BIN_CNTR_DOWN            Binary counter counting down
            3'd4                      CONST_PATTERN            Constant pattern (``DPDataPattern[31:0]``)
            3'd5                      CONST_PATTERN_INV        Constant pattern inverted (``~DPDataPattern[31:0]``)
            3'd6                      DLDATA_LOOPBACK          Loop back, downlink frame data
            3'd7                      Reserved                 Reserved
            ======================== ======================== ========================================================================


            """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class ULG4DATASOURCE:
            """Data source for uplink data group 4

            ======================== ======================== ========================================================================
             ULG4DataSource[2:0]      Name                     Description
            ======================== ======================== ========================================================================
            3'd0                      EPORTRX_DATA             Normal mode of operation, data from ePortRx
            3'd1                      PRBS7                    PRBS7 test pattern
            3'd2                      BIN_CNTR_UP              Binary counter counting up
            3'd3                      BIN_CNTR_DOWN            Binary counter counting down
            3'd4                      CONST_PATTERN            Constant pattern (``DPDataPattern[31:0]``)
            3'd5                      CONST_PATTERN_INV        Constant pattern inverted (``~DPDataPattern[31:0]``)
            3'd6                      DLDATA_LOOPBACK          Loop back, downlink frame data
            3'd7                      Reserved                 Reserved
            ======================== ======================== ========================================================================


            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class ULDATASOURCE4:
        """Uplink data path test patterns."""

        address = 0x012C

        @staticmethod
        def __str__():
            return "ULDataSource4"

        @staticmethod
        def __int__():
            return 0x012C

        class DLECDATASOURCE:
            """ """

            offset = 6
            length = 2
            bit_mask = 192

            @staticmethod
            def validate(value):
                return value in range(4)

        class ULICDATASOURCE:
            """ """

            offset = 3
            length = 3
            bit_mask = 56

            @staticmethod
            def validate(value):
                return value in range(8)

        class ULG6DATASOURCE:
            """Data source for uplink data group 6

            ======================== ======================== ========================================================================
             ULG6DataSource[2:0]      Name                     Description
            ======================== ======================== ========================================================================
            3'd0                      EPORTRX_DATA             Normal mode of operation, data from ePortRx
            3'd1                      PRBS7                    PRBS7 test pattern
            3'd2                      BIN_CNTR_UP              Binary counter counting up
            3'd3                      BIN_CNTR_DOWN            Binary counter counting down
            3'd4                      CONST_PATTERN            Constant pattern (``DPDataPattern[31:0]``)
            3'd5                      CONST_PATTERN_INV        Constant pattern inverted (``~DPDataPattern[31:0]``)
            3'd6                      DLDATA_LOOPBACK          Loop back, downlink frame data
            3'd7                      Reserved                 Reserved
            ======================== ======================== ========================================================================


            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class ULDATASOURCE5:
        """"""

        address = 0x012D

        @staticmethod
        def __str__():
            return "ULDataSource5"

        @staticmethod
        def __int__():
            return 0x012D

        class DLG3DATASOURCE:
            """Controls the ePortTx group 3 data source

            ======================== ======================== ========================================================================
             DLG3DataSource[1:0]      Name                     Description
            ======================== ======================== ========================================================================
            2'd0                      LINK_DATA                Normal mode of operation, data from ePortRx
            2'd1                      PRBS7                    PRBS7 patter on each channel
            2'd2                      BIN_CNTR_UP              Binary counter counting up on each channel
            2'd3                      CONST_PATTERN            Constant pattern
            ======================== ======================== ========================================================================


            """

            offset = 6
            length = 2
            bit_mask = 192

            @staticmethod
            def validate(value):
                return value in range(4)

        class DLG2DATASOURCE:
            """Controls the ePortTx group 2 data source

            ======================== ======================== ========================================================================
             DLG2DataSource[1:0]      Name                     Description
            ======================== ======================== ========================================================================
            2'd0                      LINK_DATA                Normal mode of operation, data from ePortRx
            2'd1                      PRBS7                    PRBS7 patter on each channel
            2'd2                      BIN_CNTR_UP              Binary counter counting up on each channel
            2'd3                      CONST_PATTERN            Constant pattern
            ======================== ======================== ========================================================================


            """

            offset = 4
            length = 2
            bit_mask = 48

            @staticmethod
            def validate(value):
                return value in range(4)

        class DLG1DATASOURCE:
            """Controls the ePortTx group 1 data source

            ======================== ======================== ========================================================================
             DLG1DataSource[1:0]      Name                     Description
            ======================== ======================== ========================================================================
            2'd0                      LINK_DATA                Normal mode of operation, data from ePortRx
            2'd1                      PRBS7                    PRBS7 patter on each channel
            2'd2                      BIN_CNTR_UP              Binary counter counting up on each channel
            2'd3                      CONST_PATTERN            Constant pattern
            ======================== ======================== ========================================================================


            """

            offset = 2
            length = 2
            bit_mask = 12

            @staticmethod
            def validate(value):
                return value in range(4)

        class DLG0DATASOURCE:
            """Controls the ePortTx group 0 data source

            ======================== ======================== ========================================================================
             DLG0DataSource[1:0]      Name                     Description
            ======================== ======================== ========================================================================
            2'd0                      LINK_DATA                Normal mode of operation, data from ePortRx
            2'd1                      PRBS7                    PRBS7 patter on each channel
            2'd2                      BIN_CNTR_UP              Binary counter counting up on each channel
            2'd3                      CONST_PATTERN            Constant pattern
            ======================== ======================== ========================================================================


            """

            offset = 0
            length = 2
            bit_mask = 3

            @staticmethod
            def validate(value):
                return value in range(4)

    class DPDATAPATTERN3:
        """Constant pattern to be used in test pattern generation/checking"""

        address = 0x012E

        @staticmethod
        def __str__():
            return "DPDataPattern3"

        @staticmethod
        def __int__():
            return 0x012E

        class DPDATAPATTERN:
            """Bits 31:24 of the constant pattern."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class DPDATAPATTERN2:
        """Constant pattern to be used in test pattern generation/checking"""

        address = 0x012F

        @staticmethod
        def __str__():
            return "DPDataPattern2"

        @staticmethod
        def __int__():
            return 0x012F

        class DPDATAPATTERN:
            """Bits 23:16 of the constant pattern."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class DPDATAPATTERN1:
        """Constant pattern to be used in test pattern generation/checking"""

        address = 0x0130

        @staticmethod
        def __str__():
            return "DPDataPattern1"

        @staticmethod
        def __int__():
            return 0x0130

        class DPDATAPATTERN:
            """Bits 15:8 of the constant pattern."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class DPDATAPATTERN0:
        """Constant pattern to be used in test pattern generation/checking"""

        address = 0x0131

        @staticmethod
        def __str__():
            return "DPDataPattern0"

        @staticmethod
        def __int__():
            return 0x0131

        class DPDATAPATTERN:
            """Bits 7:0 of the constant pattern."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class EPRXPRBS3:
        """Control registers for build-in PRBS7 generators in ePortRx."""

        address = 0x0132

        @staticmethod
        def __str__():
            return "EPRXPRBS3"

        @staticmethod
        def __int__():
            return 0x0132

        class EPRXECPRBSENABLE:
            """ """

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX63PRBSENABLE:
            """Enables PRBS7 generator for channel 3 in group 6. If enabled, the data from the input pin are discarded."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX62PRBSENABLE:
            """Enables PRBS7 generator for channel 2 in group 6. If enabled, the data from the input pin are discarded."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX61PRBSENABLE:
            """Enables PRBS7 generator for channel 1 in group 6. If enabled, the data from the input pin are discarded."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX60PRBSENABLE:
            """Enables PRBS7 generator for channel 0 in group 6. If enabled, the data from the input pin are discarded."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRXPRBS2:
        """Control registers for build-in PRBS7 generators in ePortRx."""

        address = 0x0133

        @staticmethod
        def __str__():
            return "EPRXPRBS2"

        @staticmethod
        def __int__():
            return 0x0133

        class EPRX53PRBSENABLE:
            """Enables PRBS7 generator for channel 3 in group 5. If enabled, the data from the input pin are discarded."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX52PRBSENABLE:
            """Enables PRBS7 generator for channel 2 in group 5. If enabled, the data from the input pin are discarded."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX51PRBSENABLE:
            """Enables PRBS7 generator for channel 1 in group 5. If enabled, the data from the input pin are discarded."""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX50PRBSENABLE:
            """Enables PRBS7 generator for channel 0 in group 5. If enabled, the data from the input pin are discarded."""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX43PRBSENABLE:
            """Enables PRBS7 generator for channel 3 in group 4. If enabled, the data from the input pin are discarded."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX42PRBSENABLE:
            """Enables PRBS7 generator for channel 2 in group 4. If enabled, the data from the input pin are discarded."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX41PRBSENABLE:
            """Enables PRBS7 generator for channel 1 in group 4. If enabled, the data from the input pin are discarded."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX40PRBSENABLE:
            """Enables PRBS7 generator for channel 0 in group 4. If enabled, the data from the input pin are discarded."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRXPRBS1:
        """Control registers for build-in PRBS7 generators in ePortRx."""

        address = 0x0134

        @staticmethod
        def __str__():
            return "EPRXPRBS1"

        @staticmethod
        def __int__():
            return 0x0134

        class EPRX33PRBSENABLE:
            """Enables PRBS7 generator for channel 3 in group 3. If enabled, the data from the input pin are discarded."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX32PRBSENABLE:
            """Enables PRBS7 generator for channel 2 in group 3. If enabled, the data from the input pin are discarded."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX31PRBSENABLE:
            """Enables PRBS7 generator for channel 1 in group 3. If enabled, the data from the input pin are discarded."""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX30PRBSENABLE:
            """Enables PRBS7 generator for channel 0 in group 3. If enabled, the data from the input pin are discarded."""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX23PRBSENABLE:
            """Enables PRBS7 generator for channel 3 in group 2. If enabled, the data from the input pin are discarded."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX22PRBSENABLE:
            """Enables PRBS7 generator for channel 2 in group 2. If enabled, the data from the input pin are discarded."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX21PRBSENABLE:
            """Enables PRBS7 generator for channel 1 in group 2. If enabled, the data from the input pin are discarded."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX20PRBSENABLE:
            """Enables PRBS7 generator for channel 0 in group 2. If enabled, the data from the input pin are discarded."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EPRXPRBS0:
        """Control registers for build-in PRBS7 generators in ePortRx."""

        address = 0x0135

        @staticmethod
        def __str__():
            return "EPRXPRBS0"

        @staticmethod
        def __int__():
            return 0x0135

        class EPRX13PRBSENABLE:
            """Enables PRBS7 generator for channel 3 in group 1. If enabled, the data from the input pin are discarded."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX12PRBSENABLE:
            """Enables PRBS7 generator for channel 2 in group 1. If enabled, the data from the input pin are discarded."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX11PRBSENABLE:
            """Enables PRBS7 generator for channel 1 in group 1. If enabled, the data from the input pin are discarded."""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX10PRBSENABLE:
            """Enables PRBS7 generator for channel 0 in group 1. If enabled, the data from the input pin are discarded."""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX03PRBSENABLE:
            """Enables PRBS7 generator for channel 3 in group 0. If enabled, the data from the input pin are discarded."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX02PRBSENABLE:
            """Enables PRBS7 generator for channel 2 in group 0. If enabled, the data from the input pin are discarded."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX01PRBSENABLE:
            """Enables PRBS7 generator for channel 1 in group 0. If enabled, the data from the input pin are discarded."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX00PRBSENABLE:
            """Enables PRBS7 generator for channel 0 in group 0. If enabled, the data from the input pin are discarded."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class BERTSOURCE:
        """Data source for the built-in BER checker."""

        address = 0x0136

        @staticmethod
        def __str__():
            return "BERTSource"

        @staticmethod
        def __int__():
            return 0x0136

        class BERTSOURCE:
            """Please refer to :numref:`bert_checker` for more details."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class BERTCONFIG:
        """Configuration for the Bit Error Rate Test."""

        address = 0x0137

        @staticmethod
        def __str__():
            return "BERTConfig"

        @staticmethod
        def __int__():
            return 0x0137

        class BERTMEASTIME:
            """Test time. For more details please refer to :numref:`bert_meas_time`"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class SKIPDISABLE:
            """Disable the skip cycle signal originating from the frame aligner. It is used
            when testing raw PRBS sequences on the downlink.
            """

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class BERTSTART:
            """Asserting this bit start the BERT measurement."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class BERTDATAPATTERN3:
        """Fixed data pattern used by the BERT checker."""

        address = 0x0138

        @staticmethod
        def __str__():
            return "BERTDataPattern3"

        @staticmethod
        def __int__():
            return 0x0138

        class BERTDATAPATTERN:
            """Bits 31:24 of the fixed pattern for BERT."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class BERTDATAPATTERN2:
        """Fixed data pattern used by the BERT checker."""

        address = 0x0139

        @staticmethod
        def __str__():
            return "BERTDataPattern2"

        @staticmethod
        def __int__():
            return 0x0139

        class BERTDATAPATTERN:
            """Bits 23:16 of the fixed pattern for BERT."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class BERTDATAPATTERN1:
        """Fixed data pattern used by the BERT checker."""

        address = 0x013A

        @staticmethod
        def __str__():
            return "BERTDataPattern1"

        @staticmethod
        def __int__():
            return 0x013A

        class BERTDATAPATTERN:
            """Bits 15:8 of the fixed pattern for BERT."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class BERTDATAPATTERN0:
        """Fixed data pattern used by the BERT checker."""

        address = 0x013B

        @staticmethod
        def __str__():
            return "BERTDataPattern0"

        @staticmethod
        def __int__():
            return 0x013B

        class BERTDATAPATTERN:
            """Bits 7:0 of the fixed pattern for BERT."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class RST0:
        """Reset related register. Enables resetting several components."""

        address = 0x013C

        @staticmethod
        def __str__():
            return "RST0"

        @staticmethod
        def __int__():
            return 0x013C

        class RSTPLLDIGITAL:
            """Resets the PLL control logic."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class RSTFUSES:
            """Resets the e-fuses control logic."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class RSTCONFIG:
            """Resets the configuration block."""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class RSTRXLOGIC:
            """Resets the RXphy of serial configuration interface."""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class RSTTXLOGIC:
            """Resets the TXphy of serial configuration interface."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class RSTI2CM0:
            """Resets channel 0 I2C master. One should generate a pulse on this bit (0->1->0)."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class RSTI2CM1:
            """Resets channel 1 I2C master. One should generate a pulse on this bit (0->1->0)."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class RSTI2CM2:
            """Resets channel 2 I2C master. One should generate a pulse on this bit (0->1->0)."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class RST1:
        """Reset related register. Enables resetting several components."""

        address = 0x013D

        @staticmethod
        def __str__():
            return "RST1"

        @staticmethod
        def __int__():
            return 0x013D

        class RSTFRAMEALIGNER:
            """Resets the frame aligner."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class RSTEPRX6DLL:
            """Resets the master DLL in ePortRx group 6."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class RSTEPRX5DLL:
            """Resets the master DLL in ePortRx group 5."""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class RSTEPRX4DLL:
            """Resets the master DLL in ePortRx group 4."""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class RSTEPRX3DLL:
            """Resets the master DLL in ePortRx group 3."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class RSTEPRX2DLL:
            """Resets the master DLL in ePortRx group 2."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class RSTEPRX1DLL:
            """Resets the master DLL in ePortRx group 1."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class RSTEPRX0DLL:
            """Resets the master DLL in ePortRx group 0."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class RST2:
        """Reset related register. Enables resetting several components."""

        address = 0x013E

        @staticmethod
        def __str__():
            return "RST2"

        @staticmethod
        def __int__():
            return 0x013E

        class SKIPFORCE:
            """Toggling this bit allows to issue a skip cycle command (equivalent to the one issued by the frame aligner). This functionality is is foreseen only for debugging purposes."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class RESETOUTFORCEACTIVE:
            """As long as this bit is set low, the ``RSTOUTB`` signal is active (low level)."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class RSTPS3DLL:
            """Resets DLL in 3 phase aligner channel."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class RSTPS2DLL:
            """Resets DLL in 2 phase aligner channel."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class RSTPS1DLL:
            """Resets DLL in 1 phase aligner channel."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class RSTPS0DLL:
            """Resets DLL in 0 phase aligner channel."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class POWERUP3:
        """Controls behavior of the power-up state machine (for more details refer to :ref:`powerUpStateMachine`)"""

        address = 0x013F

        @staticmethod
        def __str__():
            return "POWERUP3"

        @staticmethod
        def __int__():
            return 0x013F

        class PUSMFORCESTATE:
            """Allows to override the state of power-up state machine. To enable this feature, register ``PUSMForceMagic`` has to be set to 0xA3 (magic number)"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class PUSMSTATEFORCED:
            """Selects state of the power-up state machine when ``PUSMForceState`` bit is asserted.
            For more details refer to :ref:`powerUpStateMachine`).

            """

            offset = 0
            length = 5
            bit_mask = 31

            @staticmethod
            def validate(value):
                return value in range(32)

    class POWERUP4:
        """Controls behavior of the power-up state machine (for more details refer to :ref:`powerUpStateMachine`)"""

        address = 0x0140

        @staticmethod
        def __str__():
            return "POWERUP4"

        @staticmethod
        def __int__():
            return 0x0140

        class PUSMFORCEMAGIC:
            """Has to be set to 0xA3 (magic number) in order to enable ``PUSMForceState`` feature."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class CLKTREE:
        """Clock tree disable feature. Could be used for TMR testing."""

        address = 0x0141

        @staticmethod
        def __str__():
            return "CLKTree"

        @staticmethod
        def __int__():
            return 0x0141

        class CLKTREEMAGICNUMBER:
            """Has to be set to 5'h15 in order for clock masking (disabling) to be active"""

            offset = 3
            length = 5
            bit_mask = 248

            @staticmethod
            def validate(value):
                return value in range(32)

        class CLKTREECDISABLE:
            """If asserted and ClkTreeMagicNumber set to 5'h15, branch C of clock tree is disabled"""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class CLKTREEBDISABLE:
            """If asserted and ClkTreeMagicNumber set to 5'h15, branch B of clock tree is disabled"""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class CLKTREEADISABLE:
            """If asserted and ClkTreeMagicNumber set to 5'h15, branch A of clock tree is disabled"""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class DATAPATH:
        """Data path configuration."""

        address = 0x0142

        @staticmethod
        def __str__():
            return "DataPath"

        @staticmethod
        def __int__():
            return 0x0142

        class DLDPBYPASDEINTERLEVEAR:
            """Bypass de-interleaver in the downlink data path."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class DLDPBYPASFECDECODER:
            """Bypass FEC decoder in the downlink data path."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class DLDPBYPASSDESCRAMBLER:
            """Bypass de-scrambler in the downlink data path."""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class DLDPFECCOUNTERENABLE:
            """Enable downlink FEC counter."""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class ULDPBYPASSINTERLEAVER:
            """Bypass interleaver in the uplink data path."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class ULDPBYPASSSCRAMBLER:
            """Bypass scrambler in the uplink data path."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class ULDPBYPASSFECCODER:
            """Bypass FEC coder in the uplink data path."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class TO0SEL:
        """Control register for test output 0"""

        address = 0x0143

        @staticmethod
        def __str__():
            return "TO0Sel"

        @staticmethod
        def __int__():
            return 0x0143

        class TO0SELECT:
            """Selects a signal to be outputted on TSTOUT0 according to :ref:`tab_toselect`"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class TO1SEL:
        """Control register for test output 1"""

        address = 0x0144

        @staticmethod
        def __str__():
            return "TO1Sel"

        @staticmethod
        def __int__():
            return 0x0144

        class TO1SELECT:
            """Selects a signal to be outputted on TSTOUT1 according to :ref:`tab_toselect`"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class TO2SEL:
        """Control register for test output 2"""

        address = 0x0145

        @staticmethod
        def __str__():
            return "TO2Sel"

        @staticmethod
        def __int__():
            return 0x0145

        class TO2SELECT:
            """Selects a signal to be outputted on TSTOUT2 according to :ref:`tab_toselect`"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class TO3SEL:
        """Control register for test output 3"""

        address = 0x0146

        @staticmethod
        def __str__():
            return "TO3Sel"

        @staticmethod
        def __int__():
            return 0x0146

        class TO3SELECT:
            """Selects a signal to be outputted on TSTOUT3 according to :ref:`tab_toselect`"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class TO4SEL:
        """Control register for test output 4"""

        address = 0x0147

        @staticmethod
        def __str__():
            return "TO4Sel"

        @staticmethod
        def __int__():
            return 0x0147

        class TO4SELECT:
            """Selects a signal to be outputted on TSTOUT4 according to :ref:`tab_toselect`"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class TO5SEL:
        """Control register for test output 5"""

        address = 0x0148

        @staticmethod
        def __str__():
            return "TO5Sel"

        @staticmethod
        def __int__():
            return 0x0148

        class TO5SELECT:
            """Selects a signal to be outputted on TSTOUT5 according to :ref:`tab_toselect`"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class TODRIVINGSTRENGTH:
        """Driving strength control for CMOS test outputs"""

        address = 0x0149

        @staticmethod
        def __str__():
            return "TODrivingStrength"

        @staticmethod
        def __int__():
            return 0x0149

        class TO3DS:
            """Drive strength for TSTOUT3 (:ref:`cmos_io_characteristics`)"""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class TO2DS:
            """Drive strength for TSTOUT2 (:ref:`cmos_io_characteristics`)"""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class TO1DS:
            """Drive strength for TSTOUT1 (:ref:`cmos_io_characteristics`)"""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class TO0DS:
            """Drive strength for TSTOUT0 (:ref:`cmos_io_characteristics`)"""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class TO4DRIVER:
        """Output driver control for test output 4"""

        address = 0x014A

        @staticmethod
        def __str__():
            return "TO4Driver"

        @staticmethod
        def __int__():
            return 0x014A

        class TO4PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for TO4.

            +-----------------------------------+------------------------------------------+
            | TO4PreEmphasisStrength[2:0]       | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class TO4PREEMPHASISMODE:
            """Selects the pre-emphasis mode for TO4.

            +-----------------------------------+------------------------------------------+
            | TO4PreEmphasisMode[1:0]           | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class TO4DRIVESTRENGTH:
            """Sets the pre-emphasis strength for TO4.

            +-----------------------------------+------------------------------------------+
            | TO4DriveStrength[2:0]             | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class TO5DRIVER:
        """Output driver control for test output 5"""

        address = 0x014B

        @staticmethod
        def __str__():
            return "TO5Driver"

        @staticmethod
        def __int__():
            return 0x014B

        class TO5PREEMPHASISSTRENGTH:
            """Sets the pre-emphasis strength for TO5.

            +-----------------------------------+------------------------------------------+
            | TO5PreEmphasisStrength[2:0]       | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 5
            length = 3
            bit_mask = 224

            @staticmethod
            def validate(value):
                return value in range(8)

        class TO5PREEMPHASISMODE:
            """Selects the pre-emphasis mode for TO5.

            +-----------------------------------+------------------------------------------+
            | TO5PreEmphasisMode[1:0]           | Mode                                     |
            +===================================+==========================================+
            | 2'd0                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd1                              | disabled                                 |
            +-----------------------------------+------------------------------------------+
            | 2'd2                              | Self timed                               |
            +-----------------------------------+------------------------------------------+
            | 2'd3                              | Clock timed                              |
            +-----------------------------------+------------------------------------------+

            """

            offset = 3
            length = 2
            bit_mask = 24

            @staticmethod
            def validate(value):
                return value in range(4)

        class TO5DRIVESTRENGTH:
            """Sets the pre-emphasis strength for TO5.

            +-----------------------------------+------------------------------------------+
            | TO5DriveStrength[2:0]             | Strength [mA]                            |
            +===================================+==========================================+
            | 3'd0                              | 0                                        |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 1.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 1.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 2.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 2.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 3.0                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 3.5                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 4.0                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class TOPREEMP:
        """Pre-emphasis control for differential test outputs"""

        address = 0x014C

        @staticmethod
        def __str__():
            return "TOPreEmp"

        @staticmethod
        def __int__():
            return 0x014C

        class TO5INVERT:
            """Inverts data for TO5"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class TO5PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for TO5.

            +-----------------------------------+------------------------------------------+
            | TO5PreEmphasisWidth[2:0]          | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 4
            length = 3
            bit_mask = 112

            @staticmethod
            def validate(value):
                return value in range(8)

        class TO4INVERT:
            """Inverts data for TO4"""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class TO4PREEMPHASISWIDTH:
            """Sets the width of pre-emphasis pulse for TO4.

            +-----------------------------------+------------------------------------------+
            | TO4PreEmphasisWidth[2:0]          | Pulse length [ps]                        |
            +===================================+==========================================+
            | 3'd0                              | 120                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd1                              | 240                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd2                              | 360                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd3                              | 480                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd4                              | 600                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd5                              | 720                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd6                              | 840                                      |
            +-----------------------------------+------------------------------------------+
            | 3'd7                              | 960                                      |
            +-----------------------------------+------------------------------------------+

            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class RESERVED10:
        """Reserved register."""

        address = 0x014D

        @staticmethod
        def __str__():
            return "RESERVED10"

        @staticmethod
        def __int__():
            return 0x014D

    class RESERVED11:
        """Reserved register."""

        address = 0x014E

        @staticmethod
        def __str__():
            return "RESERVED11"

        @staticmethod
        def __int__():
            return 0x014E

    class RESERVED12:
        """Reserved register."""

        address = 0x014F

        @staticmethod
        def __str__():
            return "RESERVED12"

        @staticmethod
        def __int__():
            return 0x014F

    class CONFIGPINS:
        """Status of the lpGBT external configuration pins"""

        address = 0x0150

        @staticmethod
        def __str__():
            return "ConfigPins"

        @staticmethod
        def __int__():
            return 0x0150

        class LPGBTMODE:
            """State of ``MODE`` pins. The function of the pin is described in :ref:`modePins`."""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class BOOTCONFIG:
            """State of the ``BOOTCNF[1:0]`` pins. The function of these pins is described in :ref:`BOOTCNF`."""

            offset = 2
            length = 2
            bit_mask = 12

            @staticmethod
            def validate(value):
                return value in range(4)

        class LOCKMODE:
            """State of the ``LOCKMODE`` pin.  The function of the pin is described in :ref:`LOCKMODE`."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

    class I2CSLAVEADDRESS:
        """Chip address."""

        address = 0x0151

        @staticmethod
        def __str__():
            return "I2CSlaveAddress"

        @staticmethod
        def __int__():
            return 0x0151

        class ASICCONTROLADR:
            """Address of the chip used in slow control protocols (I2C, IC, EC)."""

            offset = 0
            length = 7
            bit_mask = 127

            @staticmethod
            def validate(value):
                return value in range(128)

    class EPRX0LOCKED:
        """ePortRx group 0 status register"""

        address = 0x0152

        @staticmethod
        def __str__():
            return "EPRX0Locked"

        @staticmethod
        def __int__():
            return 0x0152

        class EPRX0CHNLOCKED:
            """Status of phase selection logic for channels in group 0.
            Bit 0 corresponds to channel 0, bit 1 to channel 1 and so on. Logic value of 1 means that the channel is locked.

            """

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX0STATE:
            """State of initialization state machine for ePortRx group 0. State can be according to the table:

            +-----------------------+---------------------+------------------------+
            | EPRX0State[1:0]       | State                                        |
            +=======================+=====================+========================+
            | 2'd0                  | Reset                                        |
            +-----------------------+---------------------+------------------------+
            | 2'd1                  | Force down                                   |
            +-----------------------+---------------------+------------------------+
            | 2'd2                  | Confirm early state                          |
            +-----------------------+---------------------+------------------------+
            | 2'd3                  | Free running state                           |
            +-----------------------+---------------------+------------------------+

            """

            offset = 0
            length = 2
            bit_mask = 3

            @staticmethod
            def validate(value):
                return value in range(4)

    class EPRX0CURRENTPHASE10:
        """Currently selected phases for channels 0 and 1 in ePortRx group 0"""

        address = 0x0153

        @staticmethod
        def __str__():
            return "EPRX0CurrentPhase10"

        @staticmethod
        def __int__():
            return 0x0153

        class EPRX0CURRENTPHASE1:
            """Currently selected phases for channels 1 in ePortRx group 0"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX0CURRENTPHASE0:
            """Currently selected phases for channels 0 in ePortRx group 0"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class EPRX0CURRENTPHASE32:
        """Currently selected phases for channels 2 and 3 in ePortRx group 0"""

        address = 0x0154

        @staticmethod
        def __str__():
            return "EPRX0CurrentPhase32"

        @staticmethod
        def __int__():
            return 0x0154

        class EPRX0CURRENTPHASE3:
            """Currently selected phases for channels 3 in ePortRx group 0"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX0CURRENTPHASE2:
            """Currently selected phases for channels 2 in ePortRx group 0"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class EPRX1LOCKED:
        """ePortRx group 1 status register"""

        address = 0x0155

        @staticmethod
        def __str__():
            return "EPRX1Locked"

        @staticmethod
        def __int__():
            return 0x0155

        class EPRX1CHNLOCKED:
            """Status of phase selection logic for channels in group 1.
            Bit 0 corresponds to channel 0, bit 1 to channel 1 and so on. Logic value of 1 means that the channel is locked.

            """

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX1STATE:
            """State of initialization state machine for ePortRx group 1. State can be according to the table:

            +-----------------------+---------------------+------------------------+
            | EPRX1State[1:0]       | State                                        |
            +=======================+=====================+========================+
            | 2'd0                  | Reset                                        |
            +-----------------------+---------------------+------------------------+
            | 2'd1                  | Force down                                   |
            +-----------------------+---------------------+------------------------+
            | 2'd2                  | Confirm early state                          |
            +-----------------------+---------------------+------------------------+
            | 2'd3                  | Free running state                           |
            +-----------------------+---------------------+------------------------+

            """

            offset = 0
            length = 2
            bit_mask = 3

            @staticmethod
            def validate(value):
                return value in range(4)

    class EPRX1CURRENTPHASE10:
        """Currently selected phases for channels 0 and 1 in ePortRx group 1"""

        address = 0x0156

        @staticmethod
        def __str__():
            return "EPRX1CurrentPhase10"

        @staticmethod
        def __int__():
            return 0x0156

        class EPRX1CURRENTPHASE1:
            """Currently selected phases for channels 1 in ePortRx group 1"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX1CURRENTPHASE0:
            """Currently selected phases for channels 0 in ePortRx group 1"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class EPRX1CURRENTPHASE32:
        """Currently selected phases for channels 2 and 3 in ePortRx group 1"""

        address = 0x0157

        @staticmethod
        def __str__():
            return "EPRX1CurrentPhase32"

        @staticmethod
        def __int__():
            return 0x0157

        class EPRX1CURRENTPHASE3:
            """Currently selected phases for channels 3 in ePortRx group 1"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX1CURRENTPHASE2:
            """Currently selected phases for channels 2 in ePortRx group 1"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class EPRX2LOCKED:
        """ePortRx group 2 status register"""

        address = 0x0158

        @staticmethod
        def __str__():
            return "EPRX2Locked"

        @staticmethod
        def __int__():
            return 0x0158

        class EPRX2CHNLOCKED:
            """Status of phase selection logic for channels in group 2.
            Bit 0 corresponds to channel 0, bit 1 to channel 1 and so on. Logic value of 1 means that the channel is locked.

            """

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX2STATE:
            """State of initialization state machine for ePortRx group 2. State can be according to the table:

            +-----------------------+---------------------+------------------------+
            | EPRX2State[1:0]       | State                                        |
            +=======================+=====================+========================+
            | 2'd0                  | Reset                                        |
            +-----------------------+---------------------+------------------------+
            | 2'd1                  | Force down                                   |
            +-----------------------+---------------------+------------------------+
            | 2'd2                  | Confirm early state                          |
            +-----------------------+---------------------+------------------------+
            | 2'd3                  | Free running state                           |
            +-----------------------+---------------------+------------------------+

            """

            offset = 0
            length = 2
            bit_mask = 3

            @staticmethod
            def validate(value):
                return value in range(4)

    class EPRX2CURRENTPHASE10:
        """Currently selected phases for channels 0 and 1 in ePortRx group 2"""

        address = 0x0159

        @staticmethod
        def __str__():
            return "EPRX2CurrentPhase10"

        @staticmethod
        def __int__():
            return 0x0159

        class EPRX2CURRENTPHASE1:
            """Currently selected phases for channels 1 in ePortRx group 2"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX2CURRENTPHASE0:
            """Currently selected phases for channels 0 in ePortRx group 2"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class EPRX2CURRENTPHASE32:
        """Currently selected phases for channels 2 and 3 in ePortRx group 2"""

        address = 0x015A

        @staticmethod
        def __str__():
            return "EPRX2CurrentPhase32"

        @staticmethod
        def __int__():
            return 0x015A

        class EPRX2CURRENTPHASE3:
            """Currently selected phases for channels 3 in ePortRx group 2"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX2CURRENTPHASE2:
            """Currently selected phases for channels 2 in ePortRx group 2"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class EPRX3LOCKED:
        """ePortRx group 3 status register"""

        address = 0x015B

        @staticmethod
        def __str__():
            return "EPRX3Locked"

        @staticmethod
        def __int__():
            return 0x015B

        class EPRX3CHNLOCKED:
            """Status of phase selection logic for channels in group 3.
            Bit 0 corresponds to channel 0, bit 1 to channel 1 and so on. Logic value of 1 means that the channel is locked.

            """

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX3STATE:
            """State of initialization state machine for ePortRx group 3. State can be according to the table:

            +-----------------------+---------------------+------------------------+
            | EPRX3State[1:0]       | State                                        |
            +=======================+=====================+========================+
            | 2'd0                  | Reset                                        |
            +-----------------------+---------------------+------------------------+
            | 2'd1                  | Force down                                   |
            +-----------------------+---------------------+------------------------+
            | 2'd2                  | Confirm early state                          |
            +-----------------------+---------------------+------------------------+
            | 2'd3                  | Free running state                           |
            +-----------------------+---------------------+------------------------+

            """

            offset = 0
            length = 2
            bit_mask = 3

            @staticmethod
            def validate(value):
                return value in range(4)

    class EPRX3CURRENTPHASE10:
        """Currently selected phases for channels 0 and 1 in ePortRx group 3"""

        address = 0x015C

        @staticmethod
        def __str__():
            return "EPRX3CurrentPhase10"

        @staticmethod
        def __int__():
            return 0x015C

        class EPRX3CURRENTPHASE1:
            """Currently selected phases for channels 1 in ePortRx group 3"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX3CURRENTPHASE0:
            """Currently selected phases for channels 0 in ePortRx group 3"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class EPRX3CURRENTPHASE32:
        """Currently selected phases for channels 2 and 3 in ePortRx group 3"""

        address = 0x015D

        @staticmethod
        def __str__():
            return "EPRX3CurrentPhase32"

        @staticmethod
        def __int__():
            return 0x015D

        class EPRX3CURRENTPHASE3:
            """Currently selected phases for channels 3 in ePortRx group 3"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX3CURRENTPHASE2:
            """Currently selected phases for channels 2 in ePortRx group 3"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class EPRX4LOCKED:
        """ePortRx group 4 status register"""

        address = 0x015E

        @staticmethod
        def __str__():
            return "EPRX4Locked"

        @staticmethod
        def __int__():
            return 0x015E

        class EPRX4CHNLOCKED:
            """Status of phase selection logic for channels in group 4.
            Bit 0 corresponds to channel 0, bit 1 to channel 1 and so on. Logic value of 1 means that the channel is locked.

            """

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX4STATE:
            """State of initialization state machine for ePortRx group 4. State can be according to the table:

            +-----------------------+---------------------+------------------------+
            | EPRX4State[1:0]       | State                                        |
            +=======================+=====================+========================+
            | 2'd0                  | Reset                                        |
            +-----------------------+---------------------+------------------------+
            | 2'd1                  | Force down                                   |
            +-----------------------+---------------------+------------------------+
            | 2'd2                  | Confirm early state                          |
            +-----------------------+---------------------+------------------------+
            | 2'd3                  | Free running state                           |
            +-----------------------+---------------------+------------------------+

            """

            offset = 0
            length = 2
            bit_mask = 3

            @staticmethod
            def validate(value):
                return value in range(4)

    class EPRX4CURRENTPHASE10:
        """Currently selected phases for channels 0 and 1 in ePortRx group 4"""

        address = 0x015F

        @staticmethod
        def __str__():
            return "EPRX4CurrentPhase10"

        @staticmethod
        def __int__():
            return 0x015F

        class EPRX4CURRENTPHASE1:
            """Currently selected phases for channels 1 in ePortRx group 4"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX4CURRENTPHASE0:
            """Currently selected phases for channels 0 in ePortRx group 4"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class EPRX4CURRENTPHASE32:
        """Currently selected phases for channels 2 and 3 in ePortRx group 4"""

        address = 0x0160

        @staticmethod
        def __str__():
            return "EPRX4CurrentPhase32"

        @staticmethod
        def __int__():
            return 0x0160

        class EPRX4CURRENTPHASE3:
            """Currently selected phases for channels 3 in ePortRx group 4"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX4CURRENTPHASE2:
            """Currently selected phases for channels 2 in ePortRx group 4"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class EPRX5LOCKED:
        """ePortRx group 5 status register"""

        address = 0x0161

        @staticmethod
        def __str__():
            return "EPRX5Locked"

        @staticmethod
        def __int__():
            return 0x0161

        class EPRX5CHNLOCKED:
            """Status of phase selection logic for channels in group 5.
            Bit 0 corresponds to channel 0, bit 1 to channel 1 and so on. Logic value of 1 means that the channel is locked.

            """

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX5STATE:
            """State of initialization state machine for ePortRx group 5. State can be according to the table:

            +-----------------------+---------------------+------------------------+
            | EPRX5State[1:0]       | State                                        |
            +=======================+=====================+========================+
            | 2'd0                  | Reset                                        |
            +-----------------------+---------------------+------------------------+
            | 2'd1                  | Force down                                   |
            +-----------------------+---------------------+------------------------+
            | 2'd2                  | Confirm early state                          |
            +-----------------------+---------------------+------------------------+
            | 2'd3                  | Free running state                           |
            +-----------------------+---------------------+------------------------+

            """

            offset = 0
            length = 2
            bit_mask = 3

            @staticmethod
            def validate(value):
                return value in range(4)

    class EPRX5CURRENTPHASE10:
        """Currently selected phases for channels 0 and 1 in ePortRx group 5"""

        address = 0x0162

        @staticmethod
        def __str__():
            return "EPRX5CurrentPhase10"

        @staticmethod
        def __int__():
            return 0x0162

        class EPRX5CURRENTPHASE1:
            """Currently selected phases for channels 1 in ePortRx group 5"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX5CURRENTPHASE0:
            """Currently selected phases for channels 0 in ePortRx group 5"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class EPRX5CURRENTPHASE32:
        """Currently selected phases for channels 2 and 3 in ePortRx group 5"""

        address = 0x0163

        @staticmethod
        def __str__():
            return "EPRX5CurrentPhase32"

        @staticmethod
        def __int__():
            return 0x0163

        class EPRX5CURRENTPHASE3:
            """Currently selected phases for channels 3 in ePortRx group 5"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX5CURRENTPHASE2:
            """Currently selected phases for channels 2 in ePortRx group 5"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class EPRX6LOCKED:
        """ePortRx group 6 status register"""

        address = 0x0164

        @staticmethod
        def __str__():
            return "EPRX6Locked"

        @staticmethod
        def __int__():
            return 0x0164

        class EPRX6CHNLOCKED:
            """Status of phase selection logic for channels in group 6.
            Bit 0 corresponds to channel 0, bit 1 to channel 1 and so on. Logic value of 1 means that the channel is locked.

            """

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX6STATE:
            """State of initialization state machine for ePortRx group 6. State can be according to the table:

            +-----------------------+---------------------+------------------------+
            | EPRX6State[1:0]       | State                                        |
            +=======================+=====================+========================+
            | 2'd0                  | Reset                                        |
            +-----------------------+---------------------+------------------------+
            | 2'd1                  | Force down                                   |
            +-----------------------+---------------------+------------------------+
            | 2'd2                  | Confirm early state                          |
            +-----------------------+---------------------+------------------------+
            | 2'd3                  | Free running state                           |
            +-----------------------+---------------------+------------------------+

            """

            offset = 0
            length = 2
            bit_mask = 3

            @staticmethod
            def validate(value):
                return value in range(4)

    class EPRX6CURRENTPHASE10:
        """Currently selected phases for channels 0 and 1 in ePortRx group 6"""

        address = 0x0165

        @staticmethod
        def __str__():
            return "EPRX6CurrentPhase10"

        @staticmethod
        def __int__():
            return 0x0165

        class EPRX6CURRENTPHASE1:
            """Currently selected phases for channels 1 in ePortRx group 6"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX6CURRENTPHASE0:
            """Currently selected phases for channels 0 in ePortRx group 6"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class EPRX6CURRENTPHASE32:
        """Currently selected phases for channels 2 and 3 in ePortRx group 6"""

        address = 0x0166

        @staticmethod
        def __str__():
            return "EPRX6CurrentPhase32"

        @staticmethod
        def __int__():
            return 0x0166

        class EPRX6CURRENTPHASE3:
            """Currently selected phases for channels 3 in ePortRx group 6"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class EPRX6CURRENTPHASE2:
            """Currently selected phases for channels 2 in ePortRx group 6"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class EPRXECCURRENTPHASE:
        """Status register for ePortRxEc"""

        address = 0x0167

        @staticmethod
        def __str__():
            return "EPRXEcCurrentPhase"

        @staticmethod
        def __int__():
            return 0x0167

        class EPRXECCURRENTPHASE:
            """Currently selected phase for EC channel phase aligner"""

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class EPRX0DLLSTATUS:
        """Status register of lock filter for ePortRxGroup0"""

        address = 0x0168

        @staticmethod
        def __str__():
            return "EPRX0DllStatus"

        @staticmethod
        def __int__():
            return 0x0168

        class EPRX0DLLLOCKED:
            """Lock status of the master DLL"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX0DLLLFSTATE:
            """State of lock filter state machine

            +----------------------+---------------------------------------------+
            | EPRX0DllLFState[1:0] | Description                                 |
            +======================+=============================================+
            | 2'b00                | Unlocked State                              |
            +----------------------+---------------------------------------------+
            | 2'b01                | Confirm Lock State                          |
            +----------------------+---------------------------------------------+
            | 2'b10                | Locked State                                |
            +----------------------+---------------------------------------------+
            | 2'b11                | Confirm Unlock State                        |
            +----------------------+---------------------------------------------+

            """

            offset = 5
            length = 2
            bit_mask = 96

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPRX0DLLLOLCNT:
            """Loss of Lock counter value"""

            offset = 0
            length = 5
            bit_mask = 31

            @staticmethod
            def validate(value):
                return value in range(32)

    class EPRX1DLLSTATUS:
        """Status register of lock filter for ePortRxGroup1"""

        address = 0x0169

        @staticmethod
        def __str__():
            return "EPRX1DllStatus"

        @staticmethod
        def __int__():
            return 0x0169

        class EPRX1DLLLOCKED:
            """Lock status of the master DLL"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX1DLLLFSTATE:
            """State of lock filter state machine

            +----------------------+---------------------------------------------+
            | EPRX1DllLFState[1:0] | Description                                 |
            +======================+=============================================+
            | 2'b00                | Unlocked State                              |
            +----------------------+---------------------------------------------+
            | 2'b01                | Confirm Lock State                          |
            +----------------------+---------------------------------------------+
            | 2'b10                | Locked State                                |
            +----------------------+---------------------------------------------+
            | 2'b11                | Confirm Unlock State                        |
            +----------------------+---------------------------------------------+

            """

            offset = 5
            length = 2
            bit_mask = 96

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPRX1DLLLOLCNT:
            """Loss of Lock counter value"""

            offset = 0
            length = 5
            bit_mask = 31

            @staticmethod
            def validate(value):
                return value in range(32)

    class EPRX2DLLSTATUS:
        """Status register of lock filter for ePortRxGroup2"""

        address = 0x016A

        @staticmethod
        def __str__():
            return "EPRX2DllStatus"

        @staticmethod
        def __int__():
            return 0x016A

        class EPRX2DLLLOCKED:
            """Lock status of the master DLL"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX2DLLLFSTATE:
            """State of lock filter state machine

            +----------------------+---------------------------------------------+
            | EPRX2DllLFState[1:0] | Description                                 |
            +======================+=============================================+
            | 2'b00                | Unlocked State                              |
            +----------------------+---------------------------------------------+
            | 2'b01                | Confirm Lock State                          |
            +----------------------+---------------------------------------------+
            | 2'b10                | Locked State                                |
            +----------------------+---------------------------------------------+
            | 2'b11                | Confirm Unlock State                        |
            +----------------------+---------------------------------------------+

            """

            offset = 5
            length = 2
            bit_mask = 96

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPRX2DLLLOLCNT:
            """Loss of Lock counter value"""

            offset = 0
            length = 5
            bit_mask = 31

            @staticmethod
            def validate(value):
                return value in range(32)

    class EPRX3DLLSTATUS:
        """Status register of lock filter for ePortRxGroup3"""

        address = 0x016B

        @staticmethod
        def __str__():
            return "EPRX3DllStatus"

        @staticmethod
        def __int__():
            return 0x016B

        class EPRX3DLLLOCKED:
            """Lock status of the master DLL"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX3DLLLFSTATE:
            """State of lock filter state machine

            +----------------------+---------------------------------------------+
            | EPRX3DllLFState[1:0] | Description                                 |
            +======================+=============================================+
            | 2'b00                | Unlocked State                              |
            +----------------------+---------------------------------------------+
            | 2'b01                | Confirm Lock State                          |
            +----------------------+---------------------------------------------+
            | 2'b10                | Locked State                                |
            +----------------------+---------------------------------------------+
            | 2'b11                | Confirm Unlock State                        |
            +----------------------+---------------------------------------------+

            """

            offset = 5
            length = 2
            bit_mask = 96

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPRX3DLLLOLCNT:
            """Loss of Lock counter value"""

            offset = 0
            length = 5
            bit_mask = 31

            @staticmethod
            def validate(value):
                return value in range(32)

    class EPRX4DLLSTATUS:
        """Status register of lock filter for ePortRxGroup4"""

        address = 0x016C

        @staticmethod
        def __str__():
            return "EPRX4DllStatus"

        @staticmethod
        def __int__():
            return 0x016C

        class EPRX4DLLLOCKED:
            """Lock status of the master DLL"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX4DLLLFSTATE:
            """State of lock filter state machine

            +----------------------+---------------------------------------------+
            | EPRX4DllLFState[1:0] | Description                                 |
            +======================+=============================================+
            | 2'b00                | Unlocked State                              |
            +----------------------+---------------------------------------------+
            | 2'b01                | Confirm Lock State                          |
            +----------------------+---------------------------------------------+
            | 2'b10                | Locked State                                |
            +----------------------+---------------------------------------------+
            | 2'b11                | Confirm Unlock State                        |
            +----------------------+---------------------------------------------+

            """

            offset = 5
            length = 2
            bit_mask = 96

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPRX4DLLLOLCNT:
            """Loss of Lock counter value"""

            offset = 0
            length = 5
            bit_mask = 31

            @staticmethod
            def validate(value):
                return value in range(32)

    class EPRX5DLLSTATUS:
        """Status register of lock filter for ePortRxGroup5"""

        address = 0x016D

        @staticmethod
        def __str__():
            return "EPRX5DllStatus"

        @staticmethod
        def __int__():
            return 0x016D

        class EPRX5DLLLOCKED:
            """Lock status of the master DLL"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX5DLLLFSTATE:
            """State of lock filter state machine

            +----------------------+---------------------------------------------+
            | EPRX5DllLFState[1:0] | Description                                 |
            +======================+=============================================+
            | 2'b00                | Unlocked State                              |
            +----------------------+---------------------------------------------+
            | 2'b01                | Confirm Lock State                          |
            +----------------------+---------------------------------------------+
            | 2'b10                | Locked State                                |
            +----------------------+---------------------------------------------+
            | 2'b11                | Confirm Unlock State                        |
            +----------------------+---------------------------------------------+

            """

            offset = 5
            length = 2
            bit_mask = 96

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPRX5DLLLOLCNT:
            """Loss of Lock counter value"""

            offset = 0
            length = 5
            bit_mask = 31

            @staticmethod
            def validate(value):
                return value in range(32)

    class EPRX6DLLSTATUS:
        """Status register of lock filter for ePortRxGroup6"""

        address = 0x016E

        @staticmethod
        def __str__():
            return "EPRX6DllStatus"

        @staticmethod
        def __int__():
            return 0x016E

        class EPRX6DLLLOCKED:
            """Lock status of the master DLL"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class EPRX6DLLLFSTATE:
            """State of lock filter state machine

            +----------------------+---------------------------------------------+
            | EPRX6DllLFState[1:0] | Description                                 |
            +======================+=============================================+
            | 2'b00                | Unlocked State                              |
            +----------------------+---------------------------------------------+
            | 2'b01                | Confirm Lock State                          |
            +----------------------+---------------------------------------------+
            | 2'b10                | Locked State                                |
            +----------------------+---------------------------------------------+
            | 2'b11                | Confirm Unlock State                        |
            +----------------------+---------------------------------------------+

            """

            offset = 5
            length = 2
            bit_mask = 96

            @staticmethod
            def validate(value):
                return value in range(4)

        class EPRX6DLLLOLCNT:
            """Loss of Lock counter value"""

            offset = 0
            length = 5
            bit_mask = 31

            @staticmethod
            def validate(value):
                return value in range(32)

    class I2CM0CTRL:
        """Contents of control register written by user for I2C Master 0"""

        address = 0x016F

        @staticmethod
        def __str__():
            return "I2CM0Ctrl"

        @staticmethod
        def __int__():
            return 0x016F

        class I2CM0SCLDRIVEMODE:
            """

            ================== =================================================================================================================================
            I2CM0SCLDriveMode  Pull-up/Pull-down resistor
            ================== =================================================================================================================================
            1'b0                SCL pad is open-drain, so it pulls down the line to VSS or is in high impedance. A pull-up resistor must be used.
            1'b1                SCL is driven by a CMOS buffer, so it pulls down the line to VSS or pulls up the line to VDD. No pull-up resistor is required.
            ================== =================================================================================================================================


            """

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM0NBYTE:
            """Number of bytes in an I2C multi-byte write or read (maximum d'16 and d'15 in 7-bit and 10-bit addressing modes respectively)"""

            offset = 2
            length = 5
            bit_mask = 124

            @staticmethod
            def validate(value):
                return value in range(32)

        class I2CM0FREQ:
            """Frequency of I2C bus transaction according to:

            ================================== ==================================
            I2CM0Freq[1:0]                          frequency
            ================================== ==================================
             2'b00                               100 kHz
             2'b01                               200 kHz
             2'b10                               400 kHz
             2'b11                               1 MHz
            ================================== ==================================


            """

            offset = 0
            length = 2
            bit_mask = 3

            @staticmethod
            def validate(value):
                return value in range(4)

    class I2CM0MASK:
        """Contents of mask register written by user for I2C Master 0"""

        address = 0x0170

        @staticmethod
        def __str__():
            return "I2CM0Mask"

        @staticmethod
        def __int__():
            return 0x0170

    class I2CM0STATUS:
        """Contents of status register for I2C Master 0"""

        address = 0x0171

        @staticmethod
        def __str__():
            return "I2CM0Status"

        @staticmethod
        def __int__():
            return 0x0171

        class I2CM0CLOCKDISABLED:
            """Set if the 40 MHz clock of the I2C master 0 channel is disabled."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM0NOACK:
            """Set if the last transaction was not acknowledged by the I2C slave. Value is valid at the end of the I2C transaction. Reset if a slave acknowledges the next I2C transaction."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM0RESERVED3:
            """Reserved."""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM0RESERVED2:
            """Reserved."""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM0LEVELERROR:
            """Set if the I2C master port finds that the SDA line is pulled low '0' before initiating a transaction. Indicates a problem with the I2C bus. Represents the status of the SDA line and cannot be reset."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM0SUCCESS:
            """Set when the last I2C transaction was executed successfully. Reset by the start of the next I2C transaction."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM0RESERVED1:
            """Reserved."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM0RESERVED0:
            """Reserved."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class I2CM0TRANCNT:
        """Contents of transaction counter for I2C Master 0"""

        address = 0x0172

        @staticmethod
        def __str__():
            return "I2CM0TranCnt"

        @staticmethod
        def __int__():
            return 0x0172

        class I2CM0TRANCNT:
            """Content of transaction counter."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM0READBYTE:
        """Data read from an I2C slave in a single-byte-read for I2C Master 0"""

        address = 0x0173

        @staticmethod
        def __str__():
            return "I2CM0ReadByte"

        @staticmethod
        def __int__():
            return 0x0173

        class I2CM0READBYTE:
            """Data read from an I2C slave in a single-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM0READ0:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 0"""

        address = 0x0174

        @staticmethod
        def __str__():
            return "I2CM0Read0"

        @staticmethod
        def __int__():
            return 0x0174

        class I2CM0READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM0READ1:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 0"""

        address = 0x0175

        @staticmethod
        def __str__():
            return "I2CM0Read1"

        @staticmethod
        def __int__():
            return 0x0175

        class I2CM0READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM0READ2:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 0"""

        address = 0x0176

        @staticmethod
        def __str__():
            return "I2CM0Read2"

        @staticmethod
        def __int__():
            return 0x0176

        class I2CM0READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM0READ3:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 0"""

        address = 0x0177

        @staticmethod
        def __str__():
            return "I2CM0Read3"

        @staticmethod
        def __int__():
            return 0x0177

        class I2CM0READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM0READ4:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 0"""

        address = 0x0178

        @staticmethod
        def __str__():
            return "I2CM0Read4"

        @staticmethod
        def __int__():
            return 0x0178

        class I2CM0READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM0READ5:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 0"""

        address = 0x0179

        @staticmethod
        def __str__():
            return "I2CM0Read5"

        @staticmethod
        def __int__():
            return 0x0179

        class I2CM0READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM0READ6:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 0"""

        address = 0x017A

        @staticmethod
        def __str__():
            return "I2CM0Read6"

        @staticmethod
        def __int__():
            return 0x017A

        class I2CM0READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM0READ7:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 0"""

        address = 0x017B

        @staticmethod
        def __str__():
            return "I2CM0Read7"

        @staticmethod
        def __int__():
            return 0x017B

        class I2CM0READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM0READ8:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 0"""

        address = 0x017C

        @staticmethod
        def __str__():
            return "I2CM0Read8"

        @staticmethod
        def __int__():
            return 0x017C

        class I2CM0READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM0READ9:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 0"""

        address = 0x017D

        @staticmethod
        def __str__():
            return "I2CM0Read9"

        @staticmethod
        def __int__():
            return 0x017D

        class I2CM0READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM0READ10:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 0"""

        address = 0x017E

        @staticmethod
        def __str__():
            return "I2CM0Read10"

        @staticmethod
        def __int__():
            return 0x017E

        class I2CM0READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM0READ11:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 0"""

        address = 0x017F

        @staticmethod
        def __str__():
            return "I2CM0Read11"

        @staticmethod
        def __int__():
            return 0x017F

        class I2CM0READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM0READ12:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 0"""

        address = 0x0180

        @staticmethod
        def __str__():
            return "I2CM0Read12"

        @staticmethod
        def __int__():
            return 0x0180

        class I2CM0READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM0READ13:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 0"""

        address = 0x0181

        @staticmethod
        def __str__():
            return "I2CM0Read13"

        @staticmethod
        def __int__():
            return 0x0181

        class I2CM0READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM0READ14:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 0"""

        address = 0x0182

        @staticmethod
        def __str__():
            return "I2CM0Read14"

        @staticmethod
        def __int__():
            return 0x0182

        class I2CM0READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM0READ15:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 0"""

        address = 0x0183

        @staticmethod
        def __str__():
            return "I2CM0Read15"

        @staticmethod
        def __int__():
            return 0x0183

        class I2CM0READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM1CTRL:
        """Contents of control register written by user for I2C Master 1"""

        address = 0x0184

        @staticmethod
        def __str__():
            return "I2CM1Ctrl"

        @staticmethod
        def __int__():
            return 0x0184

        class I2CM1SCLDRIVEMODE:
            """

            ================== =================================================================================================================================
            I2CM1SCLDriveMode  Pull-up/Pull-down resistor
            ================== =================================================================================================================================
            1'b0                SCL pad is open-drain, so it pulls down the line to VSS or is in high impedance. A pull-up resistor must be used.
            1'b1                SCL is driven by a CMOS buffer, so it pulls down the line to VSS or pulls up the line to VDD. No pull-up resistor is required.
            ================== =================================================================================================================================


            """

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM1NBYTE:
            """Number of bytes in an I2C multi-byte write or read (maximum d'16 and d'15 in 7-bit and 10-bit addressing modes respectively)"""

            offset = 2
            length = 5
            bit_mask = 124

            @staticmethod
            def validate(value):
                return value in range(32)

        class I2CM1FREQ:
            """Frequency of I2C bus transaction according to:

            ================================== ==================================
            I2CM1Freq[1:0]                          frequency
            ================================== ==================================
             2'b00                               100 kHz
             2'b01                               200 kHz
             2'b10                               400 kHz
             2'b11                               1 MHz
            ================================== ==================================


            """

            offset = 0
            length = 2
            bit_mask = 3

            @staticmethod
            def validate(value):
                return value in range(4)

    class I2CM1MASK:
        """Contents of mask register written by user for I2C Master 1"""

        address = 0x0185

        @staticmethod
        def __str__():
            return "I2CM1Mask"

        @staticmethod
        def __int__():
            return 0x0185

        class I2CM1MASK:
            """Content of the status register."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM1STATUS:
        """Contents of status register for I2C Master 1"""

        address = 0x0186

        @staticmethod
        def __str__():
            return "I2CM1Status"

        @staticmethod
        def __int__():
            return 0x0186

        class I2CM1CLOCKDISABLED:
            """Set if the 40 MHz clock of the I2C master 1 channel is disabled."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM1NOACK:
            """Set if the last transaction was not acknowledged by the I2C slave. Value is valid at the end of the I2C transaction. Reset if a slave acknowledges the next I2C transaction."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM1RESERVED3:
            """Reserved."""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM1RESERVED2:
            """Reserved."""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM1LEVELERROR:
            """Set if the I2C master port finds that the SDA line is pulled low '0' before initiating a transaction. Indicates a problem with the I2C bus. Represents the status of the SDA line and cannot be reset."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM1SUCCESS:
            """Set when the last I2C transaction was executed successfully. Reset by the start of the next I2C transaction."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM1RESERVED1:
            """Reserved."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM1RESERVED0:
            """Reserved."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class I2CM1TRANCNT:
        """Contents of transaction counter for I2C Master 1"""

        address = 0x0187

        @staticmethod
        def __str__():
            return "I2CM1TranCnt"

        @staticmethod
        def __int__():
            return 0x0187

        class I2CM1TRANCNT:
            """Content of transaction counter."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM1READBYTE:
        """Data read from an I2C slave in a single-byte-read for I2C Master 1"""

        address = 0x0188

        @staticmethod
        def __str__():
            return "I2CM1ReadByte"

        @staticmethod
        def __int__():
            return 0x0188

        class I2CM1READBYTE:
            """Data read from an I2C slave in a single-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM1READ0:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 1"""

        address = 0x0189

        @staticmethod
        def __str__():
            return "I2CM1Read0"

        @staticmethod
        def __int__():
            return 0x0189

        class I2CM1READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM1READ1:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 1"""

        address = 0x018A

        @staticmethod
        def __str__():
            return "I2CM1Read1"

        @staticmethod
        def __int__():
            return 0x018A

        class I2CM1READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM1READ2:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 1"""

        address = 0x018B

        @staticmethod
        def __str__():
            return "I2CM1Read2"

        @staticmethod
        def __int__():
            return 0x018B

        class I2CM1READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM1READ3:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 1"""

        address = 0x018C

        @staticmethod
        def __str__():
            return "I2CM1Read3"

        @staticmethod
        def __int__():
            return 0x018C

        class I2CM1READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM1READ4:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 1"""

        address = 0x018D

        @staticmethod
        def __str__():
            return "I2CM1Read4"

        @staticmethod
        def __int__():
            return 0x018D

        class I2CM1READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM1READ5:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 1"""

        address = 0x018E

        @staticmethod
        def __str__():
            return "I2CM1Read5"

        @staticmethod
        def __int__():
            return 0x018E

        class I2CM1READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM1READ6:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 1"""

        address = 0x018F

        @staticmethod
        def __str__():
            return "I2CM1Read6"

        @staticmethod
        def __int__():
            return 0x018F

        class I2CM1READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM1READ7:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 1"""

        address = 0x0190

        @staticmethod
        def __str__():
            return "I2CM1Read7"

        @staticmethod
        def __int__():
            return 0x0190

        class I2CM1READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM1READ8:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 1"""

        address = 0x0191

        @staticmethod
        def __str__():
            return "I2CM1Read8"

        @staticmethod
        def __int__():
            return 0x0191

        class I2CM1READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM1READ9:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 1"""

        address = 0x0192

        @staticmethod
        def __str__():
            return "I2CM1Read9"

        @staticmethod
        def __int__():
            return 0x0192

        class I2CM1READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM1READ10:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 1"""

        address = 0x0193

        @staticmethod
        def __str__():
            return "I2CM1Read10"

        @staticmethod
        def __int__():
            return 0x0193

        class I2CM1READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM1READ11:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 1"""

        address = 0x0194

        @staticmethod
        def __str__():
            return "I2CM1Read11"

        @staticmethod
        def __int__():
            return 0x0194

        class I2CM1READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM1READ12:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 1"""

        address = 0x0195

        @staticmethod
        def __str__():
            return "I2CM1Read12"

        @staticmethod
        def __int__():
            return 0x0195

        class I2CM1READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM1READ13:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 1"""

        address = 0x0196

        @staticmethod
        def __str__():
            return "I2CM1Read13"

        @staticmethod
        def __int__():
            return 0x0196

        class I2CM1READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM1READ14:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 1"""

        address = 0x0197

        @staticmethod
        def __str__():
            return "I2CM1Read14"

        @staticmethod
        def __int__():
            return 0x0197

        class I2CM1READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM1READ15:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 1"""

        address = 0x0198

        @staticmethod
        def __str__():
            return "I2CM1Read15"

        @staticmethod
        def __int__():
            return 0x0198

        class I2CM1READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM2CTRL:
        """Contents of control register written by user for I2C Master 2"""

        address = 0x0199

        @staticmethod
        def __str__():
            return "I2CM2Ctrl"

        @staticmethod
        def __int__():
            return 0x0199

        class I2CM2SCLDRIVEMODE:
            """

            ================== =================================================================================================================================
            I2CM2SCLDriveMode  Pull-up/Pull-down resistor
            ================== =================================================================================================================================
            1'b0                SCL pad is open-drain, so it pulls down the line to VSS or is in high impedance. A pull-up resistor must be used.
            1'b1                SCL is driven by a CMOS buffer, so it pulls down the line to VSS or pulls up the line to VDD. No pull-up resistor is required.
            ================== =================================================================================================================================


            """

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM2NBYTE:
            """Number of bytes in an I2C multi-byte write or read (maximum d'16 and d'15 in 7-bit and 10-bit addressing modes respectively)"""

            offset = 2
            length = 5
            bit_mask = 124

            @staticmethod
            def validate(value):
                return value in range(32)

        class I2CM2FREQ:
            """Frequency of I2C bus transaction according to:

            ================================== ==================================
            I2CM2Freq[1:0]                          frequency
            ================================== ==================================
             2'b00                               100 kHz
             2'b01                               200 kHz
             2'b10                               400 kHz
             2'b11                               1 MHz
            ================================== ==================================


            """

            offset = 0
            length = 2
            bit_mask = 3

            @staticmethod
            def validate(value):
                return value in range(4)

    class I2CM2MASK:
        """Contents of mask register written by user for I2C Master 2"""

        address = 0x019A

        @staticmethod
        def __str__():
            return "I2CM2Mask"

        @staticmethod
        def __int__():
            return 0x019A

        class I2CM2MASK:
            """Content of the status register."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM2STATUS:
        """Contents of status register for I2C Master 2"""

        address = 0x019B

        @staticmethod
        def __str__():
            return "I2CM2Status"

        @staticmethod
        def __int__():
            return 0x019B

        class I2CM2CLOCKDISABLED:
            """Set if the 40 MHz clock of the I2C master 2 channel is disabled."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM2NOACK:
            """Set if the last transaction was not acknowledged by the I2C slave. Value is valid at the end of the I2C transaction. Reset if a slave acknowledges the next I2C transaction."""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM2RESERVED3:
            """Reserved."""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM2RESERVED2:
            """Reserved."""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM2LEVELERROR:
            """Set if the I2C master port finds that the SDA line is pulled low '0' before initiating a transaction. Indicates a problem with the I2C bus. Represents the status of the SDA line and cannot be reset."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM2SUCCESS:
            """Set when the last I2C transaction was executed successfully. Reset by the start of the next I2C transaction."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM2RESERVED1:
            """Reserved."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class I2CM2RESERVED0:
            """Reserved."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class I2CM2TRANCNT:
        """Contents of transaction counter for I2C Master 2"""

        address = 0x019C

        @staticmethod
        def __str__():
            return "I2CM2TranCnt"

        @staticmethod
        def __int__():
            return 0x019C

        class I2CM2TRANCNT:
            """Content of transaction counter."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM2READBYTE:
        """Data read from an I2C slave in a single-byte-read for I2C Master 2"""

        address = 0x019D

        @staticmethod
        def __str__():
            return "I2CM2ReadByte"

        @staticmethod
        def __int__():
            return 0x019D

        class I2CM2READBYTE:
            """Data read from an I2C slave in a single-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM2READ0:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 2"""

        address = 0x019E

        @staticmethod
        def __str__():
            return "I2CM2Read0"

        @staticmethod
        def __int__():
            return 0x019E

        class I2CM2READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM2READ1:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 2"""

        address = 0x019F

        @staticmethod
        def __str__():
            return "I2CM2Read1"

        @staticmethod
        def __int__():
            return 0x019F

        class I2CM2READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM2READ2:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 2"""

        address = 0x01A0

        @staticmethod
        def __str__():
            return "I2CM2Read2"

        @staticmethod
        def __int__():
            return 0x01A0

        class I2CM2READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM2READ3:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 2"""

        address = 0x01A1

        @staticmethod
        def __str__():
            return "I2CM2Read3"

        @staticmethod
        def __int__():
            return 0x01A1

        class I2CM2READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM2READ4:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 2"""

        address = 0x01A2

        @staticmethod
        def __str__():
            return "I2CM2Read4"

        @staticmethod
        def __int__():
            return 0x01A2

        class I2CM2READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM2READ5:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 2"""

        address = 0x01A3

        @staticmethod
        def __str__():
            return "I2CM2Read5"

        @staticmethod
        def __int__():
            return 0x01A3

        class I2CM2READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM2READ6:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 2"""

        address = 0x01A4

        @staticmethod
        def __str__():
            return "I2CM2Read6"

        @staticmethod
        def __int__():
            return 0x01A4

        class I2CM2READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM2READ7:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 2"""

        address = 0x01A5

        @staticmethod
        def __str__():
            return "I2CM2Read7"

        @staticmethod
        def __int__():
            return 0x01A5

        class I2CM2READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM2READ8:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 2"""

        address = 0x01A6

        @staticmethod
        def __str__():
            return "I2CM2Read8"

        @staticmethod
        def __int__():
            return 0x01A6

        class I2CM2READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM2READ9:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 2"""

        address = 0x01A7

        @staticmethod
        def __str__():
            return "I2CM2Read9"

        @staticmethod
        def __int__():
            return 0x01A7

        class I2CM2READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM2READ10:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 2"""

        address = 0x01A8

        @staticmethod
        def __str__():
            return "I2CM2Read10"

        @staticmethod
        def __int__():
            return 0x01A8

        class I2CM2READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM2READ11:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 2"""

        address = 0x01A9

        @staticmethod
        def __str__():
            return "I2CM2Read11"

        @staticmethod
        def __int__():
            return 0x01A9

        class I2CM2READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM2READ12:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 2"""

        address = 0x01AA

        @staticmethod
        def __str__():
            return "I2CM2Read12"

        @staticmethod
        def __int__():
            return 0x01AA

        class I2CM2READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM2READ13:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 2"""

        address = 0x01AB

        @staticmethod
        def __str__():
            return "I2CM2Read13"

        @staticmethod
        def __int__():
            return 0x01AB

        class I2CM2READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM2READ14:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 2"""

        address = 0x01AC

        @staticmethod
        def __str__():
            return "I2CM2Read14"

        @staticmethod
        def __int__():
            return 0x01AC

        class I2CM2READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class I2CM2READ15:
        """Data read from an I2C slave in a multi-byte-read by I2C Master 2"""

        address = 0x01AD

        @staticmethod
        def __str__():
            return "I2CM2Read15"

        @staticmethod
        def __int__():
            return 0x01AD

        class I2CM2READ:
            """Data read from an I2C slave in a multi-byte-read"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class PSSTATUS:
        """Status of phase-shifter DLL initialization state machines"""

        address = 0x01AE

        @staticmethod
        def __str__():
            return "PSStatus"

        @staticmethod
        def __int__():
            return 0x01AE

        class PS3DLLINITSTATE:
            """Status of the DLL initialization state machine for phase-shifter channel 3"""

            offset = 6
            length = 2
            bit_mask = 192

            @staticmethod
            def validate(value):
                return value in range(4)

        class PS2DLLINITSTATE:
            """Status of the DLL initialization state machine for phase-shifter channel 2"""

            offset = 4
            length = 2
            bit_mask = 48

            @staticmethod
            def validate(value):
                return value in range(4)

        class PS1DLLINITSTATE:
            """Status of the DLL initialization state machine for phase-shifter channel 1"""

            offset = 2
            length = 2
            bit_mask = 12

            @staticmethod
            def validate(value):
                return value in range(4)

        class PS0DLLINITSTATE:
            """Status of the DLL initialization state machine for phase-shifter channel 0"""

            offset = 0
            length = 2
            bit_mask = 3

            @staticmethod
            def validate(value):
                return value in range(4)

    class PIOINH:
        """Allows read back of the PIO state."""

        address = 0x01AF

        @staticmethod
        def __str__():
            return "PIOInH"

        @staticmethod
        def __int__():
            return 0x01AF

        class PIOIN:
            """

            =============== ============================================================
            PIOIn[n]         Input signal level
            =============== ============================================================
            1'b0             Low
            1'b1             High
            =============== ============================================================


            """

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class PIOINL:
        """Allows read back of the PIO state."""

        address = 0x01B0

        @staticmethod
        def __str__():
            return "PIOInL"

        @staticmethod
        def __int__():
            return 0x01B0

        class PIOIN:
            """

            =============== ============================================================
            PIOIn[n]         Input signal level
            =============== ============================================================
            1'b0             Low
            1'b1             High
            =============== ============================================================


            """

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class FUSESTATUS:
        """Status of fuse block."""

        address = 0x01B1

        @staticmethod
        def __str__():
            return "FUSEStatus"

        @staticmethod
        def __int__():
            return 0x01B1

        class FUSEBLOWERROR:
            """Error flag (attempt to blow fuses without magic number)."""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class FUSEDATAVALID:
            """Fuse read sequence was successful, ``SelectedFuseValues[31:0]`` is valid."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class FUSEBLOWDONE:
            """Fuse blowing sequence was successful."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class FUSEBLOWBUSY:
            """Fuse block is busy (either read or blowing sequence)."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class FUSEVALUESA:
        """Value of selected FUSE block. (should be accessed only if ``FuseDataValid`` bit is set in :ref:`REG_FUSESTATUS` register)."""

        address = 0x01B2

        @staticmethod
        def __str__():
            return "FUSEValuesA"

        @staticmethod
        def __int__():
            return 0x01B2

        class SELECTEDFUSEVALUES:
            """Bits 7:0 of the data word."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class FUSEVALUESB:
        """Value of selected FUSE block. (should be accessed only if ``FuseDataValid`` bit is set in :ref:`REG_FUSESTATUS` register)."""

        address = 0x01B3

        @staticmethod
        def __str__():
            return "FUSEValuesB"

        @staticmethod
        def __int__():
            return 0x01B3

        class SELECTEDFUSEVALUES:
            """Bits 15:8 of the data word."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class FUSEVALUESC:
        """Value of selected FUSE block. (should be accessed only if ``FuseDataValid`` bit is set in :ref:`REG_FUSESTATUS` register)."""

        address = 0x01B4

        @staticmethod
        def __str__():
            return "FUSEValuesC"

        @staticmethod
        def __int__():
            return 0x01B4

        class SELECTEDFUSEVALUES:
            """Bits 23:16 of the data word."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class FUSEVALUESD:
        """Value of selected FUSE block. (should be accessed only if ``FuseDataValid`` bit is set in :ref:`REG_FUSESTATUS` register)."""

        address = 0x01B5

        @staticmethod
        def __str__():
            return "FUSEValuesD"

        @staticmethod
        def __int__():
            return 0x01B5

        class SELECTEDFUSEVALUES:
            """Bits 31:24 of the data word."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class PROCESSMONITORSTATUS:
        """Process Monitor block status register."""

        address = 0x01B6

        @staticmethod
        def __str__():
            return "ProcessMonitorStatus"

        @staticmethod
        def __int__():
            return 0x01B6

        class PMDONE:
            """Measurement done."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class PMBUSY:
            """Measurement in progress."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class PMFREQA:
        """Process Monitor frequency measurement result."""

        address = 0x01B7

        @staticmethod
        def __str__():
            return "PMFreqA"

        @staticmethod
        def __int__():
            return 0x01B7

        class PMFREQ:
            """Bits 23:16 of frequency measurement result."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class PMFREQB:
        """Process Monitor frequency measurement result."""

        address = 0x01B8

        @staticmethod
        def __str__():
            return "PMFreqB"

        @staticmethod
        def __int__():
            return 0x01B8

        class PMFREQ:
            """Bits 15:8 of frequency measurement result."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class PMFREQC:
        """Process Monitor frequency measurement result."""

        address = 0x01B9

        @staticmethod
        def __str__():
            return "PMFreqC"

        @staticmethod
        def __int__():
            return 0x01B9

        class PMFREQ:
            """Bits 7:0 of frequency measurement result."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class SEUCOUNTH:
        """Value of SEU counter."""

        address = 0x01BA

        @staticmethod
        def __str__():
            return "SEUCountH"

        @staticmethod
        def __int__():
            return 0x01BA

        class SEUCOUNT:
            """Bits 15:8 of SEU counter."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class SEUCOUNTL:
        """Value of SEU counter."""

        address = 0x01BB

        @staticmethod
        def __str__():
            return "SEUCountL"

        @staticmethod
        def __int__():
            return 0x01BB

        class SEUCOUNT:
            """Bits 7:0 of SEU counter."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class CLKGSTATUS0:
        """"""

        address = 0x01BC

        @staticmethod
        def __str__():
            return "CLKGStatus0"

        @staticmethod
        def __int__():
            return 0x01BC

        class CLKG_PLL_R_CONFIG:
            """Selected PLL's filter resistance value [min:step:max] Ohm"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class CLKG_CONFIG_I_PLL:
            """Selected PLL's integral current [min:step:max] uA"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class CLKGSTATUS1:
        """"""

        address = 0x01BD

        @staticmethod
        def __str__():
            return "CLKGStatus1"

        @staticmethod
        def __int__():
            return 0x01BD

        class CLKG_CONFIG_I_FLL:
            """Selected CDR's FLL current [min:step:max] uA"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class CLKG_CONFIG_I_CDR:
            """Selected CDR's integral current [min:step:max] uA"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class CLKGSTATUS2:
        """"""

        address = 0x01BE

        @staticmethod
        def __str__():
            return "CLKGStatus2"

        @staticmethod
        def __int__():
            return 0x01BE

        class CLKG_CONFIG_P_FF_CDR:
            """Selected CDR's proportional feedforward current [min:step:max] uA"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class CLKG_CONFIG_P_CDR:
            """Selected CDR's phase detector proportional current [min:step:max] uA"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class CLKGSTATUS3:
        """"""

        address = 0x01BF

        @staticmethod
        def __str__():
            return "CLKGStatus3"

        @staticmethod
        def __int__():
            return 0x01BF

        class CLKG_LFLOSSOFLOCKCOUNT:
            """Lock filter loss of lock (increases when lock filter's state goes lfConfirmUnlockState -> lfUnLockedState). A write access to this register will clear it."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class CLKGSTATUS4:
        """"""

        address = 0x01C0

        @staticmethod
        def __str__():
            return "CLKGStatus4"

        @staticmethod
        def __int__():
            return 0x01C0

        class CLKG_CONFIG_P_PLL:
            """Selected PLL's proportional current [min:step:max] uA"""

            offset = 4
            length = 4
            bit_mask = 240

            @staticmethod
            def validate(value):
                return value in range(16)

        class CLKG_BIASGEN_CONFIG:
            """Selected bias DAC for the charge pumps [min:step:max] uA"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class CLKGSTATUS5:
        """"""

        address = 0x01C1

        @staticmethod
        def __str__():
            return "CLKGStatus5"

        @staticmethod
        def __int__():
            return 0x01C1

        class CLKG_VCOCAPSELECT:
            """Selected vco capacitor bank (thermistor value)"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class CLKGSTATUS6:
        """"""

        address = 0x01C2

        @staticmethod
        def __str__():
            return "CLKGStatus6"

        @staticmethod
        def __int__():
            return 0x01C2

        class CLKG_VCOCAPSELECT:
            """Selected vco capacitor bank (thermistor value)"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class CLKG_DATAMUXCFG:
            """Selected data MUX loopback (test only)

            ======================== ========================================================================
             CLKG_dataMuxCfg[1:0]     Description
            ======================== ========================================================================
            2'd0                      invalid state
            2'd1                      Equalizer output data loopback
            2'd2                      Data resampled by CDR loopback
            2'd3                      disabled
            ======================== ========================================================================


            """

            offset = 5
            length = 2
            bit_mask = 96

            @staticmethod
            def validate(value):
                return value in range(4)

        class CLKG_VCODAC:
            """Selected current DAC for the VCO [min:step:max] uA"""

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class CLKGSTATUS7:
        """"""

        address = 0x01C3

        @staticmethod
        def __str__():
            return "CLKGStatus7"

        @staticmethod
        def __int__():
            return 0x01C3

        class CLKG_CONNECTCDR:
            """0: CDR loop is disconnected from VCO; 1: CDR loop is connected to VCO;"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class CLKG_CONNECTPLL:
            """0: PLL loop is disconnected from VCO; 1: PLL loop is connected to VCO;"""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class CLKG_DISDATACOUNTERREF:
            """0: data/4 ripple counter is enabled; 1: disabled"""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class CLKG_ENABLECDR:
            """0: Alexander PD UP/DOWN buffers + Alexander PD are disabled; 1: enabled"""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class CLKG_ENABLEFD:
            """0: PLL's FD + FD up/down signals are disabled; 1: enabled"""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class CLKG_ENABLEPLL:
            """0: PLL's PFD up/down signals are disabled; 1: enabled"""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class CLKG_OVERRIDEVC:
            """0: The VCO's control voltage override is disabled; 1: enabled vcoControlVoltage is mid range"""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class CLKG_REFCLKSEL:
            """0: clkRef-> data counter; 1: clkRef->40MHz ref"""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class CLKGSTATUS8:
        """"""

        address = 0x01C4

        @staticmethod
        def __str__():
            return "CLKGStatus8"

        @staticmethod
        def __int__():
            return 0x01C4

        class CLKG_VCORAILMODE:
            """0: voltage mode, 1: current mode"""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class CLKG_ENABLE_CDR_R:
            """0: CDR's resistor is disconnected; 1: connected"""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class CLKG_SMLOCKED:
            """ljCDR state machine locked flag"""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class CLKG_LFINSTLOCK:
            """lock filter instant lock signal (only in TX mode)"""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class CLKG_LFLOCKED:
            """lock filter locked signal (only in TX mode)"""

            offset = 3
            length = 1
            bit_mask = 8

            @staticmethod
            def validate(value):
                return value in range(2)

        class CLKG_CONFIG_FF_CAP:
            """CDR's feed forward filter's capacitance"""

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class CLKGSTATUS9:
        """"""

        address = 0x01C5

        @staticmethod
        def __str__():
            return "CLKGStatus9"

        @staticmethod
        def __int__():
            return 0x01C5

        class CLKG_LFSTATE:
            """ljCDR's lock filter state machine

            ===================== ======= ===================================================
             CLKG_lfState[1:0]     Value   Description
            ===================== ======= ===================================================
            lfUnLockedState        2'b00   low-pass lock filter is unlocked
            lfConfirmLockState     2'b01   low-pass lock filter is confirming lock
            lfLockedState          2'b10   low-pass lock filter is locked
            lfConfirmUnlockState   2'b11   low-pass lock filter is confirming unlock
            ===================== ======= ===================================================


            """

            offset = 4
            length = 2
            bit_mask = 48

            @staticmethod
            def validate(value):
                return value in range(4)

        class CLKG_SMSTATE:
            """ljCDR's state machine

            =========================== ======= ===================================================
             CLKG_smState[3:0]           Value   Description
            =========================== ======= ===================================================
            smResetState                 4'h0    reset state
            smInit                       4'h1    initialization state (1cycle)
            smCapSearchStart             4'h2    start VCO calibration (jump to smPLLInit or smCDRInit when finished)
            smCapSearchClearCounters0    4'h3    VCO calibration step; clear counters
            smCapSearchClearCounters1    4'h4    VCO calibration step; clear counters
            smCapSearchEnableCounter     4'h5    VCO calibration step; start counters
            smCapSearchWaitFreqDecision  4'h6    VCO calibration step; wait for race end
            smCapSearchVCOFaster         4'h7    VCO calibration step; VCO is faster than refClk, increase capBank
            smCapSearchRefClkFaster      4'h8    VCO calibration step; refClk is faster than VCO, decrease capBank
            smPLLInit                    4'h9    PLL step; closing PLL loop and waiting for lock state
            smCDRInit                    4'hA    CDR step; closing CDR loop and waiting for lock state
            smPLLEnd                     4'hB    PLL step; PLL is locked
            smCDREnd                     4'hC    CDR step; CDR is locked
            =========================== ======= ===================================================


            """

            offset = 0
            length = 4
            bit_mask = 15

            @staticmethod
            def validate(value):
                return value in range(16)

    class DLDPFECCORRECTIONCOUNT0:
        """Number of error reported by the FEC decoder in the downlink data path. A write access to this register will clear the whole DLDPFecCorrectionCount."""

        address = 0x01C6

        @staticmethod
        def __str__():
            return "DLDPFecCorrectionCount0"

        @staticmethod
        def __int__():
            return 0x01C6

        class DLDPFECCORRECTIONCOUNT:
            """Bits 31:24 of the FEC correction counter."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class DLDPFECCORRECTIONCOUNT1:
        """Number of error reported by the FEC decoder in the downlink data path. A write access to this register will clear the whole DLDPFecCorrectionCount."""

        address = 0x01C7

        @staticmethod
        def __str__():
            return "DLDPFecCorrectionCount1"

        @staticmethod
        def __int__():
            return 0x01C7

        class DLDPFECCORRECTIONCOUNT:
            """Bits 23:16 of the FEC correction counter."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class DLDPFECCORRECTIONCOUNT2:
        """Number of error reported by the FEC decoder in the downlink data path. A write access to this register will clear the whole DLDPFecCorrectionCount."""

        address = 0x01C8

        @staticmethod
        def __str__():
            return "DLDPFecCorrectionCount2"

        @staticmethod
        def __int__():
            return 0x01C8

        class DLDPFECCORRECTIONCOUNT:
            """Bits 15:8 of the FEC correction counter."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class DLDPFECCORRECTIONCOUNT3:
        """Number of error reported by the FEC decoder in the downlink data path. A write access to this register will clear the whole DLDPFecCorrectionCount."""

        address = 0x01C9

        @staticmethod
        def __str__():
            return "DLDPFecCorrectionCount3"

        @staticmethod
        def __int__():
            return 0x01C9

        class DLDPFECCORRECTIONCOUNT:
            """Bits 7:0 of the FEC correction counter."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class ADCSTATUSH:
        """ADC status register"""

        address = 0x01CA

        @staticmethod
        def __str__():
            return "ADCStatusH"

        @staticmethod
        def __int__():
            return 0x01CA

        class ADCBUSY:
            """ADC core is performing conversion."""

            offset = 7
            length = 1
            bit_mask = 128

            @staticmethod
            def validate(value):
                return value in range(2)

        class ADCDONE:
            """ADC conversion is done. Result of conversion can be accessed in ADCValue"""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class ADCVALUE:
            """Result of the last conversion."""

            offset = 0
            length = 2
            bit_mask = 3

            @staticmethod
            def validate(value):
                return value in range(4)

    class ADCSTATUSL:
        """ADC status register"""

        address = 0x01CB

        @staticmethod
        def __str__():
            return "ADCStatusL"

        @staticmethod
        def __int__():
            return 0x01CB

        class ADCVALUE:
            """Result of the last conversion."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class EOMSTATUS:
        """"""

        address = 0x01CC

        @staticmethod
        def __str__():
            return "EOMStatus"

        @staticmethod
        def __int__():
            return 0x01CC

        class EOMSMSTATE:
            """EOM state machine

            ================= ======= ===================================================
             EOMsmState[1:0]   Value   Description
            ================= ======= ===================================================
            smIdle             2'b00   idle state
            smResetCounters    2'b01   resets the EOM ripple counter
            smCount            2'b10   EOM ripple counter is counting
            smEndOfCount       2'b11   finished state; waiting for EOMStart to go down
            ================= ======= ===================================================


            """

            offset = 2
            length = 2
            bit_mask = 12

            @staticmethod
            def validate(value):
                return value in range(4)

        class EOMBUSY:
            """Its hold high by the state machine when the ripple counter is in use"""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class EOMEND:
            """Its hold high when the counting is done. It is kept high until (EOMStart | EOMEnable) goes low"""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class EOMCOUTERVALUEH:
        """"""

        address = 0x01CD

        @staticmethod
        def __str__():
            return "EOMCouterValueH"

        @staticmethod
        def __int__():
            return 0x01CD

        class EOMCOUNTERVALUE:
            """MSB word of EOM ripple counter (bigger the value, more the eye is open in this (x,y) position)"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class EOMCOUTERVALUEL:
        """"""

        address = 0x01CE

        @staticmethod
        def __str__():
            return "EOMCouterValueL"

        @staticmethod
        def __int__():
            return 0x01CE

        class EOMCOUNTERVALUE:
            """LSB word of EOM ripple counter (bigger the value, more the eye is open in this (x,y) position)"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class EOMCOUNTER40MH:
        """"""

        address = 0x01CF

        @staticmethod
        def __str__():
            return "EOMCounter40MH"

        @staticmethod
        def __int__():
            return 0x01CF

        class EOMCOUNTER40M:
            """MSB word of EOM gating counter (toggles at 40 MHz); used to estimate number of data transitions"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class EOMCOUNTER40ML:
        """"""

        address = 0x01D0

        @staticmethod
        def __str__():
            return "EOMCounter40ML"

        @staticmethod
        def __int__():
            return 0x01D0

        class EOMCOUNTER40M:
            """LSB word of EOM gating counter (toggles at 40 MHz); used to estimate number of data transitions"""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class BERTSTATUS:
        """Status register of BERT checker."""

        address = 0x01D1

        @staticmethod
        def __str__():
            return "BERTStatus"

        @staticmethod
        def __int__():
            return 0x01D1

        class BERTPRBSERRORFLAG:
            """This flag is set when data input was always zero during the test."""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class BERTBUSY:
            """Measurement is ongoing when this bit is asserted."""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class BERTDONE:
            """Measurement is down when this bit is asserted."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class BERTRESULT4:
        """BERT result."""

        address = 0x01D2

        @staticmethod
        def __str__():
            return "BERTResult4"

        @staticmethod
        def __int__():
            return 0x01D2

        class BERTERRORCOUNT:
            """Bits 39:32 of BERT result."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class BERTRESULT3:
        """BERT result."""

        address = 0x01D3

        @staticmethod
        def __str__():
            return "BERTResult3"

        @staticmethod
        def __int__():
            return 0x01D3

        class BERTERRORCOUNT:
            """Bits 31:24 of BERT result."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class BERTRESULT2:
        """BERT result."""

        address = 0x01D4

        @staticmethod
        def __str__():
            return "BERTResult2"

        @staticmethod
        def __int__():
            return 0x01D4

        class BERTERRORCOUNT:
            """Bits 23:16 of BERT result."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class BERTRESULT1:
        """BERT result."""

        address = 0x01D5

        @staticmethod
        def __str__():
            return "BERTResult1"

        @staticmethod
        def __int__():
            return 0x01D5

        class BERTERRORCOUNT:
            """Bits 15:8 of BERT result."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class BERTRESULT0:
        """BERT result."""

        address = 0x01D6

        @staticmethod
        def __str__():
            return "BERTResult0"

        @staticmethod
        def __int__():
            return 0x01D6

        class BERTERRORCOUNT:
            """Bits 7:0 of BERT result."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class ROM:
        """Register with fixed (non zero value). Can be used for testing purposes."""

        address = 0x01D7

        @staticmethod
        def __str__():
            return "ROM"

        @staticmethod
        def __int__():
            return 0x01D7

        class ROMREG:
            """All read requests for this register should yield value `0xA6` (as opposed to `0xA5` for lpGBTv0)."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class PORBOR:
        """Status of POR and BOR instances"""

        address = 0x01D8

        @staticmethod
        def __str__():
            return "PORBOR"

        @staticmethod
        def __int__():
            return 0x01D8

        class PORC:
            """State of PORC output"""

            offset = 6
            length = 1
            bit_mask = 64

            @staticmethod
            def validate(value):
                return value in range(2)

        class PORB:
            """State of PORB output"""

            offset = 5
            length = 1
            bit_mask = 32

            @staticmethod
            def validate(value):
                return value in range(2)

        class PORA:
            """State of PORA output"""

            offset = 4
            length = 1
            bit_mask = 16

            @staticmethod
            def validate(value):
                return value in range(2)

        class BODC:
            """State of BORC output"""

            offset = 2
            length = 1
            bit_mask = 4

            @staticmethod
            def validate(value):
                return value in range(2)

        class BODB:
            """State of BORB output"""

            offset = 1
            length = 1
            bit_mask = 2

            @staticmethod
            def validate(value):
                return value in range(2)

        class BODA:
            """State of BORA output"""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class PUSMSTATUS:
        """Status of power-up state machine"""

        address = 0x01D9

        @staticmethod
        def __str__():
            return "PUSMStatus"

        @staticmethod
        def __int__():
            return 0x01D9

        class PUSMSTATE:
            """Current state of the power-up state machine.

            ======================= ===================================================
             PUSMState[4:0]          State name
            ======================= ===================================================
              5'h00                  ARESET
              5'h01                  RESET1
              5'h02                  WAIT_VDD_STABLE
              5'h03                  WAIT_VDD_HIGHER_THAN_0V90
              5'h04                  COPY_FUSES
              5'h05                  CALCULATE_CHECKSUM
              5'h06                  COPY_ROM
              5'h07                  PAUSE_FOR_PLL_CONFIG_DONE
              5'h08                  WAIT_POWER_GOOD
              5'h09                  RESET_PLL
              5'h0A                  WAIT_PLL_LOCK
              5'h0B                  INIT_SCRAM
              5'h0C                  RESETOUT
              5'h0D                  I2C_TRANS
              5'h0E                  PAUSE_FOR_DLL_CONFIG_DONE
              5'h0F                  RESET_DLLS
              5'h10                  WAIT_DLL_LOCK
              5'h11                  RESET_LOGIC_USING_DLL
              5'h12                  WAIT_CHNS_LOCKED
              5'h13                  READY
            ======================= ===================================================


            """

            offset = 0
            length = 5
            bit_mask = 31

            @staticmethod
            def validate(value):
                return value in range(32)

    class PUSMPLLWATCHDOG:
        """PLL watchdog action counter"""

        address = 0x01DA

        @staticmethod
        def __str__():
            return "PUSMPLLWATCHDOG"

        @staticmethod
        def __int__():
            return 0x01DA

        class PUSMPLLWATCHDOGACTIONS:
            """This register stores the number of PLL watchdog action
            occurrences that have occurred since the last chip reset. This register is reset by the
            asynchronous reset originating from a power-on reset block or external RSTB pin. It can also be
            reset by the user by executing a write access.
            """

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class PUSMDLLWATCHDOG:
        """DLL watchdog action counter"""

        address = 0x01DB

        @staticmethod
        def __str__():
            return "PUSMDLLWATCHDOG"

        @staticmethod
        def __int__():
            return 0x01DB

        class PUSMDLLWATCHDOGACTIONS:
            """This register stores the number of DLL watchdog action
            occurrences that have occurred since the last chip reset. This register is reset by the
            asynchronous reset originating from a power-on reset block or external RSTB pin. It can also be
            reset by the user by executing a write access.
            """

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class PUSMCSUMWATCHDOG:
        """Checksum watchdog action counter"""

        address = 0x01DC

        @staticmethod
        def __str__():
            return "PUSMCSUMWATCHDOG"

        @staticmethod
        def __int__():
            return 0x01DC

        class PUSMCHECKSUMWATCHDOGACTIONS:
            """This register stores the number of checksum watchdog action
            occurrences that have occurred since the last chip reset. This register is reset by the
            asynchronous reset originating from a power-on reset block or external RSTB pin. It can also be
            reset by the user by executing a write access.
            """

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class PUSMBROWNOUTWATCHDOG:
        """Brownout status register"""

        address = 0x01DD

        @staticmethod
        def __str__():
            return "PUSMBROWNOUTWATCHDOG"

        @staticmethod
        def __int__():
            return 0x01DD

        class PUSMBROWNOUTACTIONFLAG:
            """This flag is set when a brownout condition is detected (VDD lower than brownout voltage level).
            This flag is not reset by the asynchronous reset originating from a power-on reset block or external RSTB pin.
            It can only be reset by the user by executing a write access. The value of the flag after power-up
            can be random, the user should not rely on this flag before clearing it first.
            """

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class PUSMPLLTIMEOUT:
        """PLL timeout action counter"""

        address = 0x01DE

        @staticmethod
        def __str__():
            return "PUSMPLLTIMEOUT"

        @staticmethod
        def __int__():
            return 0x01DE

        class PUSMPLLTIMEOUTACTIONS:
            """This register stores the number of PLL timeout action
            occurrences that have occurred since the last chip reset. This register is reset by the
            asynchronous reset originating from a power-on reset block or external RSTB pin. It can also be
            reset by the user by executing a write access.
            """

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class PUSMDLLTIMEOUT:
        """DLL timeout action counter"""

        address = 0x01DF

        @staticmethod
        def __str__():
            return "PUSMDLLTIMEOUT"

        @staticmethod
        def __int__():
            return 0x01DF

        class PUSMDLLTIMEOUTACTIONS:
            """This register stores the number of DLL timeout action
            occurrences that have occurred since the last chip reset. This register is reset by the
            asynchronous reset originating from a power-on reset block or external RSTB pin. It can also be
            reset by the user by executing a write access.
            """

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class PUSMCHANNELSTIMEOUT:
        """Channels locking timeout action counter"""

        address = 0x01E0

        @staticmethod
        def __str__():
            return "PUSMCHANNELSTIMEOUT"

        @staticmethod
        def __int__():
            return 0x01E0

        class PUSMCHANNELSTIMEOUTACTIONS:
            """This register stores the number of channels locking timeout action
            occurrences that have occurred since the last chip reset. This register is reset by the
            asynchronous reset originating from a power-on reset block or external RSTB pin. It can also be
            reset by the user by executing a write access.
            """

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class CRCVALUE0:
        """Value of the recently calculated CRC."""

        address = 0x01E1

        @staticmethod
        def __str__():
            return "CRCValue0"

        @staticmethod
        def __int__():
            return 0x01E1

        class CRCVALUE:
            """Bits 7:0 of the recently calculated CRC. Refer to :ref:`crc` for more details."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class CRCVALUE1:
        """Value of the recently calculated CRC."""

        address = 0x01E2

        @staticmethod
        def __str__():
            return "CRCValue1"

        @staticmethod
        def __int__():
            return 0x01E2

        class CRCVALUE:
            """Bits 15:8 of the recently calculated CRC. Refer to :ref:`crc` for more details."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class CRCVALUE2:
        """Value of the recently calculated CRC."""

        address = 0x01E3

        @staticmethod
        def __str__():
            return "CRCValue2"

        @staticmethod
        def __int__():
            return 0x01E3

        class CRCVALUE:
            """Bits 23:16 of the recently calculated CRC. Refer to :ref:`crc` for more details."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class CRCVALUE3:
        """Value of the recently calculated CRC."""

        address = 0x01E4

        @staticmethod
        def __str__():
            return "CRCValue3"

        @staticmethod
        def __int__():
            return 0x01E4

        class CRCVALUE:
            """Bits 31:24 of the recently calculated CRC. Refer to :ref:`crc` for more details."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class FAILEDCRC:
        """Counter of invalid CRC cycles."""

        address = 0x01E5

        @staticmethod
        def __str__():
            return "FailedCRC"

        @staticmethod
        def __int__():
            return 0x01E5

        class FAILEDCRCCOUNTER:
            """Counts number of CRC calculations which resulted in invalid checksum."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class TOVALUE:
        """Value of this register reflects current values of the signals selected test outputs (`TOnSelect`)."""

        address = 0x01E6

        @staticmethod
        def __str__():
            return "TOValue"

        @staticmethod
        def __int__():
            return 0x01E6

        class TOVAL:
            """Each bit corresponds to one output from test output multiplexer. E.g. reading the bit `0` allows to probe the signal currently selected by `TO0Select` in :ref:`REG_TO0SEL`."""

            offset = 0
            length = 6
            bit_mask = 63

            @staticmethod
            def validate(value):
                return value in range(64)

    class SCSTATUS:
        """Serial interface (IC/EC) status register."""

        address = 0x01E7

        @staticmethod
        def __str__():
            return "SCStatus"

        @staticmethod
        def __int__():
            return 0x01E7

        class SCPARITYVALID:
            """The last parity bit check result."""

            offset = 0
            length = 1
            bit_mask = 1

            @staticmethod
            def validate(value):
                return value in range(2)

    class FASTATE:
        """State of the frame aligner state machine"""

        address = 0x01E8

        @staticmethod
        def __str__():
            return "FAState"

        @staticmethod
        def __int__():
            return 0x01E8

        class FASTATE:
            """State of the frame aligner state machine.

            ======================= ===================================================
             FAState[2:0]            State name
            ======================= ===================================================
              3'h0                   START
              3'h1                   SEARCH_HEADER
              3'h2                   SKIP_CYCLE
              3'h3                   WAIT
              3'h4                   CONFIRM_HEADER_IN_PHASE_1
              3'h5                   TRACK_HEADER
              3'h6                   CONFIRM_HEADER_LOSS
              3'h7                   CONFIRM_HEADER_IN_PHASE_2
            ======================= ===================================================


            """

            offset = 0
            length = 3
            bit_mask = 7

            @staticmethod
            def validate(value):
                return value in range(8)

    class FAHEADERFOUNDCOUNT:
        """Frame aligner status register."""

        address = 0x01E9

        @staticmethod
        def __str__():
            return "FAHeaderFoundCount"

        @staticmethod
        def __int__():
            return 0x01E9

        class FAHEADERFOUNDCOUNT:
            """Number of valid headers found."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class FAHEADERNOTFOUNDCOUNT:
        """Frame aligner status register."""

        address = 0x01EA

        @staticmethod
        def __str__():
            return "FAHeaderNotFoundCount"

        @staticmethod
        def __int__():
            return 0x01EA

        class FAHEADERNOTFOUNDCOUNT:
            """Number of invalid headers found."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class FALOSSOFLOCKCOUNT:
        """Frame aligner status register."""

        address = 0x01EB

        @staticmethod
        def __str__():
            return "FALossOfLockCount"

        @staticmethod
        def __int__():
            return 0x01EB

        class FALOSSOFLOCKCOUNT:
            """Counts frame aligner unlocks (increases when the state goes from CONFIRM_HEADER_LOSS to SEARCH_HEADER). A write access to this register will clear it."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class CONFIGERRORCOUNTERH:
        """Counter of SEU events in configuration memory."""

        address = 0x01EC

        @staticmethod
        def __str__():
            return "ConfigErrorCounterH"

        @staticmethod
        def __int__():
            return 0x01EC

        class CONFIGERRORCOUNTER:
            """Bits 15:8 of the configuration memory SEU counter."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    class CONFIGERRORCOUNTERL:
        """Counter of SEU events in configuration memory."""

        address = 0x01ED

        @staticmethod
        def __str__():
            return "ConfigErrorCounterL"

        @staticmethod
        def __int__():
            return 0x01ED

        class CONFIGERRORCOUNTER:
            """Bits 7:0 of the configuration memory SEU counter."""

            offset = 0
            length = 8
            bit_mask = 255

            @staticmethod
            def validate(value):
                return value in range(256)

    @unique
    class Reg(IntEnum):
        CHIPID0 = 0x0000
        CHIPID1 = 0x0001
        CHIPID2 = 0x0002
        CHIPID3 = 0x0003
        USERID0 = 0x0004
        USERID1 = 0x0005
        USERID2 = 0x0006
        USERID3 = 0x0007
        DACCAL0 = 0x0008
        DACCAL1 = 0x0009
        DACCAL2 = 0x000A
        ADCCAL0 = 0x000B
        ADCCAL1 = 0x000C
        ADCCAL2 = 0x000D
        ADCCAL3 = 0x000E
        ADCCAL4 = 0x000F
        ADCCAL5 = 0x0010
        ADCCAL6 = 0x0011
        ADCCAL7 = 0x0012
        ADCCAL8 = 0x0013
        ADCCAL9 = 0x0014
        ADCCAL10 = 0x0015
        ADCCAL11 = 0x0016
        ADCCAL12 = 0x0017
        ADCCAL13 = 0x0018
        ADCCAL14 = 0x0019
        TEMPCALH = 0x001A
        TEMPCALL = 0x001B
        VREFCNTR = 0x001C
        VREFTUNE = 0x001D
        CURDACCALH = 0x001E
        CURDACCALL = 0x001F
        CLKGCONFIG0 = 0x0020
        CLKGCONFIG1 = 0x0021
        CLKGPLLRES = 0x0022
        CLKGPLLINTCUR = 0x0023
        CLKGPLLPROPCUR = 0x0024
        CLKGCDRPROPCUR = 0x0025
        CLKGCDRINTCUR = 0x0026
        CLKGCDRFFPROPCUR = 0x0027
        CLKGFLLINTCUR = 0x0028
        CLKGFFCAP = 0x0029
        CLKGCNTOVERRIDE = 0x002A
        CLKGOVERRIDECAPBANK = 0x002B
        CLKGWAITTIME = 0x002C
        CLKGLFCONFIG0 = 0x002D
        CLKGLFCONFIG1 = 0x002E
        FAMAXHEADERFOUNDCOUNT = 0x002F
        FAMAXHEADERFOUNDCOUNTAFTERNF = 0x0030
        FAMAXHEADERNOTFOUNDCOUNT = 0x0031
        RESERVED1 = 0x0032
        PSDLLCONFIG = 0x0033
        RESERVED2 = 0x0034
        FORCEENABLE = 0x0035
        CHIPCONFIG = 0x0036
        EQCONFIG = 0x0037
        EQRES = 0x0038
        LDCONFIGH = 0x0039
        LDCONFIGL = 0x003A
        REFCLK = 0x003B
        SCCONFIG = 0x003C
        RESETCONFIG = 0x003D
        PGCONFIG = 0x003E
        I2CMTRANSCONFIG = 0x003F
        I2CMTRANSADDRESS = 0x0040
        I2CMTRANSCTRL = 0x0041
        I2CMTRANSDATA0 = 0x0042
        I2CMTRANSDATA1 = 0x0043
        I2CMTRANSDATA2 = 0x0044
        I2CMTRANSDATA3 = 0x0045
        I2CMTRANSDATA4 = 0x0046
        I2CMTRANSDATA5 = 0x0047
        I2CMTRANSDATA6 = 0x0048
        I2CMTRANSDATA7 = 0x0049
        I2CMTRANSDATA8 = 0x004A
        I2CMTRANSDATA9 = 0x004B
        I2CMTRANSDATA10 = 0x004C
        I2CMTRANSDATA11 = 0x004D
        I2CMTRANSDATA12 = 0x004E
        I2CMTRANSDATA13 = 0x004F
        I2CMTRANSDATA14 = 0x0050
        I2CMTRANSDATA15 = 0x0051
        I2CMCLKDISABLE = 0x0052
        PIODIRH = 0x0053
        PIODIRL = 0x0054
        PIOOUTH = 0x0055
        PIOOUTL = 0x0056
        PIOPULLENAH = 0x0057
        PIOPULLENAL = 0x0058
        PIOUPDOWNH = 0x0059
        PIOUPDOWNL = 0x005A
        PIODRIVESTRENGTHH = 0x005B
        PIODRIVESTRENGTHL = 0x005C
        PS0CONFIG = 0x005D
        PS0DELAY = 0x005E
        PS0OUTDRIVER = 0x005F
        PS1CONFIG = 0x0060
        PS1DELAY = 0x0061
        PS1OUTDRIVER = 0x0062
        PS2CONFIG = 0x0063
        PS2DELAY = 0x0064
        PS2OUTDRIVER = 0x0065
        PS3CONFIG = 0x0066
        PS3DELAY = 0x0067
        PS3OUTDRIVER = 0x0068
        PSLOWRES = 0x0069
        DACCONFIGH = 0x006A
        DACCONFIGL = 0x006B
        CURDACVALUE = 0x006C
        CURDACCHN = 0x006D
        EPCLK0CHNCNTRH = 0x006E
        EPCLK0CHNCNTRL = 0x006F
        EPCLK1CHNCNTRH = 0x0070
        EPCLK1CHNCNTRL = 0x0071
        EPCLK2CHNCNTRH = 0x0072
        EPCLK2CHNCNTRL = 0x0073
        EPCLK3CHNCNTRH = 0x0074
        EPCLK3CHNCNTRL = 0x0075
        EPCLK4CHNCNTRH = 0x0076
        EPCLK4CHNCNTRL = 0x0077
        EPCLK5CHNCNTRH = 0x0078
        EPCLK5CHNCNTRL = 0x0079
        EPCLK6CHNCNTRH = 0x007A
        EPCLK6CHNCNTRL = 0x007B
        EPCLK7CHNCNTRH = 0x007C
        EPCLK7CHNCNTRL = 0x007D
        EPCLK8CHNCNTRH = 0x007E
        EPCLK8CHNCNTRL = 0x007F
        EPCLK9CHNCNTRH = 0x0080
        EPCLK9CHNCNTRL = 0x0081
        EPCLK10CHNCNTRH = 0x0082
        EPCLK10CHNCNTRL = 0x0083
        EPCLK11CHNCNTRH = 0x0084
        EPCLK11CHNCNTRL = 0x0085
        EPCLK12CHNCNTRH = 0x0086
        EPCLK12CHNCNTRL = 0x0087
        EPCLK13CHNCNTRH = 0x0088
        EPCLK13CHNCNTRL = 0x0089
        EPCLK14CHNCNTRH = 0x008A
        EPCLK14CHNCNTRL = 0x008B
        EPCLK15CHNCNTRH = 0x008C
        EPCLK15CHNCNTRL = 0x008D
        EPCLK16CHNCNTRH = 0x008E
        EPCLK16CHNCNTRL = 0x008F
        EPCLK17CHNCNTRH = 0x0090
        EPCLK17CHNCNTRL = 0x0091
        EPCLK18CHNCNTRH = 0x0092
        EPCLK18CHNCNTRL = 0x0093
        EPCLK19CHNCNTRH = 0x0094
        EPCLK19CHNCNTRL = 0x0095
        EPCLK20CHNCNTRH = 0x0096
        EPCLK20CHNCNTRL = 0x0097
        EPCLK21CHNCNTRH = 0x0098
        EPCLK21CHNCNTRL = 0x0099
        EPCLK22CHNCNTRH = 0x009A
        EPCLK22CHNCNTRL = 0x009B
        EPCLK23CHNCNTRH = 0x009C
        EPCLK23CHNCNTRL = 0x009D
        EPCLK24CHNCNTRH = 0x009E
        EPCLK24CHNCNTRL = 0x009F
        EPCLK25CHNCNTRH = 0x00A0
        EPCLK25CHNCNTRL = 0x00A1
        EPCLK26CHNCNTRH = 0x00A2
        EPCLK26CHNCNTRL = 0x00A3
        EPCLK27CHNCNTRH = 0x00A4
        EPCLK27CHNCNTRL = 0x00A5
        EPCLK28CHNCNTRH = 0x00A6
        EPCLK28CHNCNTRL = 0x00A7
        EPTXDATARATE = 0x00A8
        EPTXCONTROL = 0x00A9
        EPTX10ENABLE = 0x00AA
        EPTX32ENABLE = 0x00AB
        EPTXECCHNCNTR = 0x00AC
        EPTXECCHNCNTR2 = 0x00AD
        EPTX00CHNCNTR = 0x00AE
        EPTX01CHNCNTR = 0x00AF
        EPTX02CHNCNTR = 0x00B0
        EPTX03CHNCNTR = 0x00B1
        EPTX10CHNCNTR = 0x00B2
        EPTX11CHNCNTR = 0x00B3
        EPTX12CHNCNTR = 0x00B4
        EPTX13CHNCNTR = 0x00B5
        EPTX20CHNCNTR = 0x00B6
        EPTX21CHNCNTR = 0x00B7
        EPTX22CHNCNTR = 0x00B8
        EPTX23CHNCNTR = 0x00B9
        EPTX30CHNCNTR = 0x00BA
        EPTX31CHNCNTR = 0x00BB
        EPTX32CHNCNTR = 0x00BC
        EPTX33CHNCNTR = 0x00BD
        EPTX01_00CHNCNTR = 0x00BE
        EPTX03_02CHNCNTR = 0x00BF
        EPTX11_10CHNCNTR = 0x00C0
        EPTX13_12CHNCNTR = 0x00C1
        EPTX21_20CHNCNTR = 0x00C2
        EPTX23_22CHNCNTR = 0x00C3
        EPTX31_30CHNCNTR = 0x00C4
        EPTX33_32CHNCNTR = 0x00C5
        EPTXLOWRES0 = 0x00C6
        EPTXLOWRES1 = 0x00C7
        EPRX0CONTROL = 0x00C8
        EPRX1CONTROL = 0x00C9
        EPRX2CONTROL = 0x00CA
        EPRX3CONTROL = 0x00CB
        EPRX4CONTROL = 0x00CC
        EPRX5CONTROL = 0x00CD
        EPRX6CONTROL = 0x00CE
        EPRXECCONTROL = 0x00CF
        EPRX00CHNCNTR = 0x00D0
        EPRX01CHNCNTR = 0x00D1
        EPRX02CHNCNTR = 0x00D2
        EPRX03CHNCNTR = 0x00D3
        EPRX10CHNCNTR = 0x00D4
        EPRX11CHNCNTR = 0x00D5
        EPRX12CHNCNTR = 0x00D6
        EPRX13CHNCNTR = 0x00D7
        EPRX20CHNCNTR = 0x00D8
        EPRX21CHNCNTR = 0x00D9
        EPRX22CHNCNTR = 0x00DA
        EPRX23CHNCNTR = 0x00DB
        EPRX30CHNCNTR = 0x00DC
        EPRX31CHNCNTR = 0x00DD
        EPRX32CHNCNTR = 0x00DE
        EPRX33CHNCNTR = 0x00DF
        EPRX40CHNCNTR = 0x00E0
        EPRX41CHNCNTR = 0x00E1
        EPRX42CHNCNTR = 0x00E2
        EPRX43CHNCNTR = 0x00E3
        EPRX50CHNCNTR = 0x00E4
        EPRX51CHNCNTR = 0x00E5
        EPRX52CHNCNTR = 0x00E6
        EPRX53CHNCNTR = 0x00E7
        EPRX60CHNCNTR = 0x00E8
        EPRX61CHNCNTR = 0x00E9
        EPRX62CHNCNTR = 0x00EA
        EPRX63CHNCNTR = 0x00EB
        EPRXECCHNCNTR = 0x00EC
        EPRXEQ10CONTROL = 0x00ED
        EPRXEQ32CONTROL = 0x00EE
        EPRXEQ54CONTROL = 0x00EF
        EPRXEQ6CONTROL = 0x00F0
        EPRXDLLCONFIG = 0x00F1
        EPRXLOCKFILTER = 0x00F2
        EPRXLOCKFILTER2 = 0x00F3
        RESERVED4 = 0x00F4
        RESERVED5 = 0x00F5
        RESERVED6 = 0x00F6
        READY = 0x00F7
        WATCHDOG = 0x00F8
        POWERUP0 = 0x00F9
        POWERUP1 = 0x00FA
        POWERUP2 = 0x00FB
        CRC0 = 0x00FC
        CRC1 = 0x00FD
        CRC2 = 0x00FE
        CRC3 = 0x00FF
        I2CM0CONFIG = 0x0100
        I2CM0ADDRESS = 0x0101
        I2CM0DATA0 = 0x0102
        I2CM0DATA1 = 0x0103
        I2CM0DATA2 = 0x0104
        I2CM0DATA3 = 0x0105
        I2CM0CMD = 0x0106
        I2CM1CONFIG = 0x0107
        I2CM1ADDRESS = 0x0108
        I2CM1DATA0 = 0x0109
        I2CM1DATA1 = 0x010A
        I2CM1DATA2 = 0x010B
        I2CM1DATA3 = 0x010C
        I2CM1CMD = 0x010D
        I2CM2CONFIG = 0x010E
        I2CM2ADDRESS = 0x010F
        I2CM2DATA0 = 0x0110
        I2CM2DATA1 = 0x0111
        I2CM2DATA2 = 0x0112
        I2CM2DATA3 = 0x0113
        I2CM2CMD = 0x0114
        EPRXTRAIN10 = 0x0115
        EPRXTRAIN32 = 0x0116
        EPRXTRAIN54 = 0x0117
        EPRXTRAINEC6 = 0x0118
        FUSECONTROL = 0x0119
        FUSEBLOWDATAA = 0x011A
        FUSEBLOWDATAB = 0x011B
        FUSEBLOWDATAC = 0x011C
        FUSEBLOWDATAD = 0x011D
        FUSEBLOWADDH = 0x011E
        FUSEBLOWADDL = 0x011F
        FUSEMAGIC = 0x0120
        ADCSELECT = 0x0121
        ADCMON = 0x0122
        ADCCONFIG = 0x0123
        EOMCONFIGH = 0x0124
        EOMCONFIGL = 0x0125
        EOMVOFSEL = 0x0126
        PROCESSANDSEUMONITOR = 0x0127
        ULDATASOURCE0 = 0x0128
        ULDATASOURCE1 = 0x0129
        ULDATASOURCE2 = 0x012A
        ULDATASOURCE3 = 0x012B
        ULDATASOURCE4 = 0x012C
        ULDATASOURCE5 = 0x012D
        DPDATAPATTERN3 = 0x012E
        DPDATAPATTERN2 = 0x012F
        DPDATAPATTERN1 = 0x0130
        DPDATAPATTERN0 = 0x0131
        EPRXPRBS3 = 0x0132
        EPRXPRBS2 = 0x0133
        EPRXPRBS1 = 0x0134
        EPRXPRBS0 = 0x0135
        BERTSOURCE = 0x0136
        BERTCONFIG = 0x0137
        BERTDATAPATTERN3 = 0x0138
        BERTDATAPATTERN2 = 0x0139
        BERTDATAPATTERN1 = 0x013A
        BERTDATAPATTERN0 = 0x013B
        RST0 = 0x013C
        RST1 = 0x013D
        RST2 = 0x013E
        POWERUP3 = 0x013F
        POWERUP4 = 0x0140
        CLKTREE = 0x0141
        DATAPATH = 0x0142
        TO0SEL = 0x0143
        TO1SEL = 0x0144
        TO2SEL = 0x0145
        TO3SEL = 0x0146
        TO4SEL = 0x0147
        TO5SEL = 0x0148
        TODRIVINGSTRENGTH = 0x0149
        TO4DRIVER = 0x014A
        TO5DRIVER = 0x014B
        TOPREEMP = 0x014C
        RESERVED10 = 0x014D
        RESERVED11 = 0x014E
        RESERVED12 = 0x014F
        CONFIGPINS = 0x0150
        I2CSLAVEADDRESS = 0x0151
        EPRX0LOCKED = 0x0152
        EPRX0CURRENTPHASE10 = 0x0153
        EPRX0CURRENTPHASE32 = 0x0154
        EPRX1LOCKED = 0x0155
        EPRX1CURRENTPHASE10 = 0x0156
        EPRX1CURRENTPHASE32 = 0x0157
        EPRX2LOCKED = 0x0158
        EPRX2CURRENTPHASE10 = 0x0159
        EPRX2CURRENTPHASE32 = 0x015A
        EPRX3LOCKED = 0x015B
        EPRX3CURRENTPHASE10 = 0x015C
        EPRX3CURRENTPHASE32 = 0x015D
        EPRX4LOCKED = 0x015E
        EPRX4CURRENTPHASE10 = 0x015F
        EPRX4CURRENTPHASE32 = 0x0160
        EPRX5LOCKED = 0x0161
        EPRX5CURRENTPHASE10 = 0x0162
        EPRX5CURRENTPHASE32 = 0x0163
        EPRX6LOCKED = 0x0164
        EPRX6CURRENTPHASE10 = 0x0165
        EPRX6CURRENTPHASE32 = 0x0166
        EPRXECCURRENTPHASE = 0x0167
        EPRX0DLLSTATUS = 0x0168
        EPRX1DLLSTATUS = 0x0169
        EPRX2DLLSTATUS = 0x016A
        EPRX3DLLSTATUS = 0x016B
        EPRX4DLLSTATUS = 0x016C
        EPRX5DLLSTATUS = 0x016D
        EPRX6DLLSTATUS = 0x016E
        I2CM0CTRL = 0x016F
        I2CM0MASK = 0x0170
        I2CM0STATUS = 0x0171
        I2CM0TRANCNT = 0x0172
        I2CM0READBYTE = 0x0173
        I2CM0READ0 = 0x0174
        I2CM0READ1 = 0x0175
        I2CM0READ2 = 0x0176
        I2CM0READ3 = 0x0177
        I2CM0READ4 = 0x0178
        I2CM0READ5 = 0x0179
        I2CM0READ6 = 0x017A
        I2CM0READ7 = 0x017B
        I2CM0READ8 = 0x017C
        I2CM0READ9 = 0x017D
        I2CM0READ10 = 0x017E
        I2CM0READ11 = 0x017F
        I2CM0READ12 = 0x0180
        I2CM0READ13 = 0x0181
        I2CM0READ14 = 0x0182
        I2CM0READ15 = 0x0183
        I2CM1CTRL = 0x0184
        I2CM1MASK = 0x0185
        I2CM1STATUS = 0x0186
        I2CM1TRANCNT = 0x0187
        I2CM1READBYTE = 0x0188
        I2CM1READ0 = 0x0189
        I2CM1READ1 = 0x018A
        I2CM1READ2 = 0x018B
        I2CM1READ3 = 0x018C
        I2CM1READ4 = 0x018D
        I2CM1READ5 = 0x018E
        I2CM1READ6 = 0x018F
        I2CM1READ7 = 0x0190
        I2CM1READ8 = 0x0191
        I2CM1READ9 = 0x0192
        I2CM1READ10 = 0x0193
        I2CM1READ11 = 0x0194
        I2CM1READ12 = 0x0195
        I2CM1READ13 = 0x0196
        I2CM1READ14 = 0x0197
        I2CM1READ15 = 0x0198
        I2CM2CTRL = 0x0199
        I2CM2MASK = 0x019A
        I2CM2STATUS = 0x019B
        I2CM2TRANCNT = 0x019C
        I2CM2READBYTE = 0x019D
        I2CM2READ0 = 0x019E
        I2CM2READ1 = 0x019F
        I2CM2READ2 = 0x01A0
        I2CM2READ3 = 0x01A1
        I2CM2READ4 = 0x01A2
        I2CM2READ5 = 0x01A3
        I2CM2READ6 = 0x01A4
        I2CM2READ7 = 0x01A5
        I2CM2READ8 = 0x01A6
        I2CM2READ9 = 0x01A7
        I2CM2READ10 = 0x01A8
        I2CM2READ11 = 0x01A9
        I2CM2READ12 = 0x01AA
        I2CM2READ13 = 0x01AB
        I2CM2READ14 = 0x01AC
        I2CM2READ15 = 0x01AD
        PSSTATUS = 0x01AE
        PIOINH = 0x01AF
        PIOINL = 0x01B0
        FUSESTATUS = 0x01B1
        FUSEVALUESA = 0x01B2
        FUSEVALUESB = 0x01B3
        FUSEVALUESC = 0x01B4
        FUSEVALUESD = 0x01B5
        PROCESSMONITORSTATUS = 0x01B6
        PMFREQA = 0x01B7
        PMFREQB = 0x01B8
        PMFREQC = 0x01B9
        SEUCOUNTH = 0x01BA
        SEUCOUNTL = 0x01BB
        CLKGSTATUS0 = 0x01BC
        CLKGSTATUS1 = 0x01BD
        CLKGSTATUS2 = 0x01BE
        CLKGSTATUS3 = 0x01BF
        CLKGSTATUS4 = 0x01C0
        CLKGSTATUS5 = 0x01C1
        CLKGSTATUS6 = 0x01C2
        CLKGSTATUS7 = 0x01C3
        CLKGSTATUS8 = 0x01C4
        CLKGSTATUS9 = 0x01C5
        DLDPFECCORRECTIONCOUNT0 = 0x01C6
        DLDPFECCORRECTIONCOUNT1 = 0x01C7
        DLDPFECCORRECTIONCOUNT2 = 0x01C8
        DLDPFECCORRECTIONCOUNT3 = 0x01C9
        ADCSTATUSH = 0x01CA
        ADCSTATUSL = 0x01CB
        EOMSTATUS = 0x01CC
        EOMCOUTERVALUEH = 0x01CD
        EOMCOUTERVALUEL = 0x01CE
        EOMCOUNTER40MH = 0x01CF
        EOMCOUNTER40ML = 0x01D0
        BERTSTATUS = 0x01D1
        BERTRESULT4 = 0x01D2
        BERTRESULT3 = 0x01D3
        BERTRESULT2 = 0x01D4
        BERTRESULT1 = 0x01D5
        BERTRESULT0 = 0x01D6
        ROM = 0x01D7
        PORBOR = 0x01D8
        PUSMSTATUS = 0x01D9
        PUSMPLLWATCHDOG = 0x01DA
        PUSMDLLWATCHDOG = 0x01DB
        PUSMCSUMWATCHDOG = 0x01DC
        PUSMBROWNOUTWATCHDOG = 0x01DD
        PUSMPLLTIMEOUT = 0x01DE
        PUSMDLLTIMEOUT = 0x01DF
        PUSMCHANNELSTIMEOUT = 0x01E0
        CRCVALUE0 = 0x01E1
        CRCVALUE1 = 0x01E2
        CRCVALUE2 = 0x01E3
        CRCVALUE3 = 0x01E4
        FAILEDCRC = 0x01E5
        TOVALUE = 0x01E6
        SCSTATUS = 0x01E7
        FASTATE = 0x01E8
        FAHEADERFOUNDCOUNT = 0x01E9
        FAHEADERNOTFOUNDCOUNT = 0x01EA
        FALOSSOFLOCKCOUNT = 0x01EB
        CONFIGERRORCOUNTERH = 0x01EC
        CONFIGERRORCOUNTERL = 0x01ED
