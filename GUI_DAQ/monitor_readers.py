"""Acquisition-only readers shared by combined monitoring and debug tests.

Readers own no threads, scan loops, timers, or CSV writers. Worker_Monitor owns
normal scheduling and output; debug workers can call the same acquisition code.
"""

import math
import time
from pathlib import Path
import pandas as pd
from PyQt5 import QtCore
from TDC_config_low_level_function import (
    SCA_connect, SCA_config, SCA_share, ethernet_exclusive_session,
    lpgbt_read, lpgbt_config_write, LpgbtRegisterMapV1,
)
from mezz_monitor_limits import DEFAULT_MONITOR_LIMITS, range_error
from monitor_display_buffer import MonitorDisplayBuffer


class MonitorReader(QtCore.QObject):
    message_out = QtCore.pyqtSignal(str)

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.eth = controller.eth
        self.current_scan_row = None

    def initialize_csm(self, which_csm):
        with ethernet_exclusive_session(self.eth):
            SCA_connect(self.eth, sca_enable=0b1111, which_csm=which_csm, sca_address=0, verbose=0)
            SCA_config(self.eth, sca_enable=0b1111, which_csm=which_csm, sca_address=0,
                       transID=self.controller.get_transID(), channel=SCA_share.CR_CHANNEL,
                       datalen=4, command=SCA_share.CTRL_W_CRD, data=SCA_share.ENADC_DATA, wait=0.001)


class MezzMonitorReader(MonitorReader):
    display_update = QtCore.pyqtSignal(int, int, str, bool)

    def __init__(self, controller):
        super().__init__(controller)
        self.sca_tab = controller
        self.limits = (controller.get_monitor_limits() if hasattr(controller, 'get_monitor_limits')
                       else dict(DEFAULT_MONITOR_LIMITS))
        self.csv_fieldnames = self.build_csv_fieldnames()
        self.df = pd.read_csv(Path(__file__).with_name('sca_mapping.csv'), header=[0], index_col=[0])

    def format_display_text(self, value, unit=None):
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return "NA"

        if not math.isfinite(numeric_value):
            return "NA"
        return format(numeric_value, ".3f")

    def csv_item_name(self, mezz_index, label):
        return f'CSM{mezz_index//self.sca_tab.mezz_per_CSM}_Mezz{mezz_index}_{label}'

    def build_csv_fieldnames(self):
        fieldnames = []
        display_items = [('AVDD', 'V'), ('DVDD', 'V'), ('Temp', 'C')]
        for mezz_index, enabled in enumerate(self.sca_tab.mezz_enable):
            if enabled != '1':
                continue
            for label, unit in display_items:
                item_name = self.csv_item_name(mezz_index, label)
                fieldnames.extend([f'{item_name}_signal_raw_adc',
                                   f'{item_name}_ground_reference_raw_adc',
                                   f'{item_name}_display_{unit}'])
        return fieldnames

    def record_display_value(self, mezz_index, label, unit, raw_adc, display_value):
        if self.current_scan_row is None:
            return
        item_name = self.csv_item_name(mezz_index, label)
        signal, ground = raw_adc
        self.current_scan_row[f'{item_name}_signal_raw_adc'] = 'NA' if signal is None else signal
        self.current_scan_row[f'{item_name}_ground_reference_raw_adc'] = 'NA' if ground is None else ground
        self.current_scan_row[f'{item_name}_display_{unit}'] = self.format_display_text(
            display_value,
            unit=unit,
        )

    def update_display_item(self, mezz_index, label_index, label, unit, raw_adc, display_value):
        display_text = self.format_display_text(display_value, unit=unit)
        self.display_update.emit(mezz_index, label_index, display_text,
                                 range_error(label, display_value, self.limits) is not None)
        self.record_display_value(mezz_index, label, unit, raw_adc, display_value)


    def scan_mezz(self, i):
        mux_list = ['AVDD','AVDD_GND','DVDD','DVDD_GND','TEMP','TEMP_GND']
        raw_values = [None]*len(mux_list)
        voltage_values = [None]*len(mux_list)
        updated = set()
        for j in range(len(mux_list)):
            try:
                with ethernet_exclusive_session(self.eth):
                    SCA_config(self.eth,sca_enable=2**self.df[str(i%20)]['SCA'],which_csm=i//20,sca_address=0x00,transID=self.sca_tab.get_transID(),channel=SCA_share.ADC_CHANNEL,datalen=4,command=SCA_share.ADC_W_MUX,data=self.df[str(i%20)][mux_list[j]])
                    [SCA_channel,error,adc]=SCA_config(self.eth,sca_enable=2**self.df[str(i%20)]['SCA'],which_csm=i//20,sca_address=0x00,transID=self.sca_tab.get_transID(),channel=SCA_share.ADC_CHANNEL,datalen=4,command=SCA_share.ADC_GO,data=SCA_share.ADC_GO_DATA)
            except Exception as e:
                self.message_out.emit(('TDC'+str(i%20)+' '+mux_list[j]+' read back error'));
                self.message_out.emit(str(e))

            else:
                raw_values[j] = adc
                voltage = adc/4096.0
                voltage_values[j] = voltage
                self.sca_tab.cell_list[i//20][i%20].value_list[j]=voltage
                if j==1 and voltage_values[0] is not None:

                    # 1k resistor in mezz, 4.7k + 1k resistor in CSM, probe point on 1K
                    cal = voltage_values[0]*6.7-voltage_values[1]
                    raw_adc = (raw_values[0], raw_values[1])
                    self.update_display_item(i, 0, 'AVDD', 'V', raw_adc, cal)
                    updated.add(0)
                elif j==3 and voltage_values[2] is not None:

                    # 1k resistor in mezz, 4.7k + 1k resistor in CSM, probe point on 1K
                    cal = voltage_values[2]*6.7-voltage_values[3]
                    raw_adc = (raw_values[2], raw_values[3])
                    self.update_display_item(i, 1, 'DVDD', 'V', raw_adc, cal)
                    updated.add(1)
                elif j==5 and voltage_values[4] is not None:
                    # 1k resistor in mezz, 1k + 1k resistor in CSM, probe point on 1K
                    cal = voltage_values[4]*3-voltage_values[5]
                    temp = (cal-0.5)*100
                    raw_adc = (raw_values[4], raw_values[5])
                    self.update_display_item(i, 2, 'Temp', 'C', raw_adc, temp)
                    updated.add(2)
        for index, label, unit in ((0, 'AVDD', 'V'), (1, 'DVDD', 'V'), (2, 'Temp', 'C')):
            if index not in updated:
                raw_adc = tuple(raw_values[index * 2:index * 2 + 2])
                self.update_display_item(i, index, label, unit, raw_adc, None)



class CSMMonitorReader(MonitorReader):
    def __init__(self, controller):
        super().__init__(controller)
        self.csm_tab = controller
        self.display_values = MonitorDisplayBuffer()
        self.lpgbt_calibration_cache = {}
        self.csv_fieldnames = self.build_csv_fieldnames()

    def format_display_text(self, value, unit):
        return "{:.3f}".format(value)+' '+unit

    def csv_item_name(self, which_csm, source, label, lpgbt_addr=''):
        source_name = source.replace(' ', '_')
        if lpgbt_addr != '':
            return f'CSM{which_csm}_{source_name}_{lpgbt_addr}_{label}'
        return f'CSM{which_csm}_{source_name}_{label}'

    def build_csv_fieldnames(self):
        fieldnames = []
        for i in range(self.csm_tab.CSM_count):
            if not self.csm_tab.checkbox_list[i].isChecked():
                continue

            for j, label in enumerate(self.csm_tab.cell_list[i].SCA_temp_label):
                unit = self.csm_tab.cell_list[i].SCA_temp_unit[j]
                item_name = self.csv_item_name(i, 'SCA', label)
                fieldnames.extend([f'{item_name}_raw_adc', f'{item_name}_display_{unit}'])

            for k in range(2):
                lpgbt_cell = self.csm_tab.cell_list[i].lpGBT_list[k]
                source = 'lpGBT_master' if k == 0 else 'lpGBT_slave'
                for j, label in enumerate(lpgbt_cell.lpGBT_monitor_label):
                    unit = lpgbt_cell.lpGBT_monitor_unit[j]
                    item_name = self.csv_item_name(i, source, label, lpgbt_cell.address)
                    fieldnames.extend([f'{item_name}_raw_adc', f'{item_name}_display_{unit}'])
        return fieldnames

    def record_monitor_value(self, scan_index, which_csm, source, label, raw_adc, display_value, unit, display_text, lpgbt_addr='', monitor_index=''):
        if self.current_scan_row is None:
            return
        item_name = self.csv_item_name(which_csm, source, label, lpgbt_addr)
        self.current_scan_row[f'{item_name}_raw_adc'] = raw_adc
        self.current_scan_row[f'{item_name}_display_{unit}'] = "{:.3f}".format(display_value)

    def rotate_right_32(self, value, shift):
        shift %= 32
        return ((value >> shift) | ((value << (32-shift)) & 0xffffffff)) & 0xffffffff

    def read_lpgbt_u32(self, which_csm, lpgbt_addr, reg_addr_list):
        value = 0
        for reg_addr in reg_addr_list:
            value = (value << 8) | self.read_lpgbt_reg_byte(which_csm, lpgbt_addr, reg_addr)
        return value

    def read_lpgbt_reg_byte(self, which_csm, lpgbt_addr, reg_addr):
        data = lpgbt_read(self.eth, lpgbt_addr=lpgbt_addr, reg_addr=reg_addr, nb_to_be_read=1, verbose=False, which_csm=which_csm)
        if not isinstance(data, list) or len(data) != 1:
            raise RuntimeError(f'bad readback from reg {reg_addr}: {data}')
        return data[0]

    def majority_vote_u32(self, values):
        values = [value for value in values if value is not None]
        if not values:
            return None
        vote = 0
        for bit in range(32):
            ones = sum((value >> bit) & 1 for value in values)
            if ones > len(values)/2.0:
                vote |= 1 << bit
        return vote

    def read_lpgbt_fuse_block(self, which_csm, lpgbt_addr, block_addr):
        control = self.read_lpgbt_reg_byte(which_csm, lpgbt_addr, LpgbtRegisterMapV1.FUSECONTROL.address)
        lpgbt_config_write(self.eth, reg_addr=LpgbtRegisterMapV1.FUSECONTROL.address, value_list=[control | 0x02], which_csm=which_csm, lpgbt_addr=lpgbt_addr, verbose=False)
        for _ in range(100):
            status = self.read_lpgbt_reg_byte(which_csm, lpgbt_addr, LpgbtRegisterMapV1.FUSESTATUS.address)
            if status & LpgbtRegisterMapV1.FUSESTATUS.FUSEDATAVALID.bit_mask:
                break
            time.sleep(0.001)
        else:
            raise RuntimeError(f'fuse data not valid for block 0x{block_addr:04X}')
        lpgbt_config_write(self.eth, reg_addr=LpgbtRegisterMapV1.FUSEBLOWADDH.address, value_list=[(block_addr >> 8) & 0xff], which_csm=which_csm, lpgbt_addr=lpgbt_addr, verbose=False)
        lpgbt_config_write(self.eth, reg_addr=LpgbtRegisterMapV1.FUSEBLOWADDL.address, value_list=[block_addr & 0xff], which_csm=which_csm, lpgbt_addr=lpgbt_addr, verbose=False)
        fuse_a = self.read_lpgbt_reg_byte(which_csm, lpgbt_addr, LpgbtRegisterMapV1.FUSEVALUESA.address)
        fuse_b = self.read_lpgbt_reg_byte(which_csm, lpgbt_addr, LpgbtRegisterMapV1.FUSEVALUESB.address)
        fuse_c = self.read_lpgbt_reg_byte(which_csm, lpgbt_addr, LpgbtRegisterMapV1.FUSEVALUESC.address)
        fuse_d = self.read_lpgbt_reg_byte(which_csm, lpgbt_addr, LpgbtRegisterMapV1.FUSEVALUESD.address)
        lpgbt_config_write(self.eth, reg_addr=LpgbtRegisterMapV1.FUSECONTROL.address, value_list=[control & ~0x02], which_csm=which_csm, lpgbt_addr=lpgbt_addr, verbose=False)
        return (fuse_d << 24) | (fuse_c << 16) | (fuse_b << 8) | fuse_a

    def read_lpgbt_chipid(self, which_csm, lpgbt_addr):
        replica_defs = [
            ('A', [
                LpgbtRegisterMapV1.CHIPID0.address,
                LpgbtRegisterMapV1.CHIPID1.address,
                LpgbtRegisterMapV1.CHIPID2.address,
                LpgbtRegisterMapV1.CHIPID3.address,
            ], 0),
            ('B', [
                LpgbtRegisterMapV1.DACCAL0.address,
                LpgbtRegisterMapV1.DACCAL1.address,
                LpgbtRegisterMapV1.DACCAL2.address,
                LpgbtRegisterMapV1.ADCCAL0.address,
            ], 6),
            ('C', [
                LpgbtRegisterMapV1.ADCCAL1.address,
                LpgbtRegisterMapV1.ADCCAL2.address,
                LpgbtRegisterMapV1.ADCCAL3.address,
                LpgbtRegisterMapV1.ADCCAL4.address,
            ], 12),
            ('D', [
                LpgbtRegisterMapV1.ADCCAL5.address,
                LpgbtRegisterMapV1.ADCCAL6.address,
                LpgbtRegisterMapV1.ADCCAL7.address,
                LpgbtRegisterMapV1.ADCCAL8.address,
            ], 18),
            ('E', [
                LpgbtRegisterMapV1.ADCCAL9.address,
                LpgbtRegisterMapV1.ADCCAL10.address,
                LpgbtRegisterMapV1.ADCCAL11.address,
                LpgbtRegisterMapV1.ADCCAL12.address,
            ], 24),
        ]
        ram_candidates = {}
        for name, reg_addr_list, rotate_right in replica_defs:
            try:
                raw_value = self.read_lpgbt_u32(which_csm, lpgbt_addr, reg_addr_list)
                ram_candidates[name] = self.rotate_right_32(raw_value, rotate_right)
            except Exception:
                ram_candidates[name] = None
        fuse_candidates = {}
        for name, reg_addr_list, rotate_right in replica_defs:
            try:
                raw_value = self.read_lpgbt_fuse_block(which_csm, lpgbt_addr, reg_addr_list[0])
                fuse_candidates[name] = self.rotate_right_32(raw_value, rotate_right)
            except Exception:
                fuse_candidates[name] = None
        ram_chipid = self.majority_vote_u32(ram_candidates.values())
        fuse_chipid = self.majority_vote_u32(fuse_candidates.values())
        chipid = fuse_chipid if fuse_chipid not in (None, 0) else ram_chipid
        ram_text = ' '.join(
            f'{name}={value:08X}' if value is not None else f'{name}=----'
            for name, value in ram_candidates.items()
        )
        fuse_text = ' '.join(
            f'{name}={value:08X}' if value is not None else f'{name}=----'
            for name, value in fuse_candidates.items()
        )
        if chipid in (None, 0):
            self.message_out.emit(f'WARNING: CSM{which_csm} lpGBT{lpgbt_addr} CHIPID read failed (RAM {ram_text}; FUSE {fuse_text}); using typical temp fallback')
        else:
            self.message_out.emit(f'CSM{which_csm} lpGBT{lpgbt_addr} CHIPID {chipid:08X} (RAM {ram_text}; FUSE {fuse_text}); using typical temp fallback')
        return None

    def get_lpgbt_calibration(self, which_csm, lpgbt_addr):
        key = (which_csm, lpgbt_addr)
        if key not in self.lpgbt_calibration_cache:
            self.lpgbt_calibration_cache[key] = self.read_lpgbt_chipid(which_csm, lpgbt_addr)
        return self.lpgbt_calibration_cache[key]

    def validate_sca_adc(self, channel, error, value):
        """Optional stricter reply validation used by the debug test."""

    def validate_lpgbt_adc(self, busy, done, value):
        """Optional conversion-status validation used by the debug test."""

    def scan_csm(self, scan_index, i):

        for j in range(len(self.csm_tab.cell_list[i].SCA_temp_label)):
            try:
                with ethernet_exclusive_session(self.eth):
                    SCA_config(self.eth,sca_enable=self.csm_tab.cell_list[i].SCA_mapping[j],which_csm=i,sca_address=0x00,transID=self.csm_tab.get_transID(),channel=SCA_share.ADC_CHANNEL,datalen=4,command=SCA_share.ADC_W_MUX,data=self.csm_tab.cell_list[i].SCA_ADC_input[j],wait = 0.001)
                    [SCA_channel,error,adc]=SCA_config(self.eth,sca_enable=self.csm_tab.cell_list[i].SCA_mapping[j],which_csm=i,sca_address=0x00,transID=self.csm_tab.get_transID(),channel=SCA_share.ADC_CHANNEL,datalen=4,command=SCA_share.ADC_GO,data=SCA_share.ADC_GO_DATA,wait = 0.001)
                self.validate_sca_adc(SCA_channel, error, adc)
            except Exception as e:
                self.message_out.emit((f'CSM{i} {self.csm_tab.cell_list[i].SCA_temp_label[j]} read back error'));
                self.message_out.emit(str(e))
                self.display_values.put((i, -1, j), 'NA')

            else:
                if(j<2):
                    display_value=adc/4096.0*5.7
                else:
                    voltage_mv = adc/4096.0*1000.0
                    display_value = (716.0-voltage_mv)/1.829
                unit = self.csm_tab.cell_list[i].SCA_temp_unit[j]
                label = self.csm_tab.cell_list[i].SCA_temp_label[j]
                display_text = self.format_display_text(display_value, unit)
                self.record_monitor_value(scan_index, i, 'SCA', label, adc, display_value, unit, display_text)
                self.display_values.put((i, -1, j), display_text)

        # set which CSM
        for k in range(2):  # lpgbt master and slave
            lpgbt_addr = self.csm_tab.cell_list[i].lpGBT_list[k].address
            lpgbt_calibration = self.get_lpgbt_calibration(i, lpgbt_addr)
            vref_tune = 128 if lpgbt_calibration is None else int(round(lpgbt_calibration['VREF_OFFSET']))
            vref_tune = max(0, min(255, vref_tune))
            def write_lpgbt(reg_addr, value_list):
                return lpgbt_config_write(self.eth, reg_addr=reg_addr, value_list=value_list, which_csm=i, lpgbt_addr=lpgbt_addr, verbose=False)

            # enable VREF
            write_lpgbt(LpgbtRegisterMapV1.VREFCNTR.address, [128])

            #set VREF to chip specific tuned value
            write_lpgbt(LpgbtRegisterMapV1.VREFTUNE.address, [vref_tune])

            curdac_value = 200
            curdac_uA_per_code = 3.6
            vtrx_baseline_voltage = 0.0352
            for j in range(len(self.csm_tab.cell_list[i].lpGBT_list[k].lpGBT_monitor_index)):
                monitor_index = self.csm_tab.cell_list[i].lpGBT_list[k].lpGBT_monitor_index[j]
                if monitor_index == 1:
                    try:
                        # enable current DAC
                        write_lpgbt(LpgbtRegisterMapV1.DACCONFIGH.address, [0b01000000])

                        # set DAC current
                        write_lpgbt(LpgbtRegisterMapV1.CURDACVALUE.address, [curdac_value])

                        # enable current source for pin ADC1
                        write_lpgbt(LpgbtRegisterMapV1.CURDACCHN.address, [0b00000010])
                    except Exception as e:
                        self.message_out.emit(str(e))

                try:
                    # set ADCInPSelect to lpGBT_monitor_index[k] and ADCInNSelect to VREF/2
                    write_lpgbt(LpgbtRegisterMapV1.ADCSELECT.address, [monitor_index*16+15])

                    if monitor_index == 14:
                        write_lpgbt(LpgbtRegisterMapV1.ADCMON.address, [32])
                    write_lpgbt(LpgbtRegisterMapV1.ADCMON.address, [self.csm_tab.cell_list[i].lpGBT_list[k].lpGBT_monitor_ADCmon[j]])
                    write_lpgbt(LpgbtRegisterMapV1.ADCCONFIG.address, [0+4+0]) #reset start bit
                    write_lpgbt(LpgbtRegisterMapV1.ADCCONFIG.address, [128+4+0])
                    readback=write_lpgbt(LpgbtRegisterMapV1.ADCSTATUSH.address, [0,0])
                    adcbusy = (readback[0]&LpgbtRegisterMapV1.ADCSTATUSH.ADCBUSY.bit_mask)>>LpgbtRegisterMapV1.ADCSTATUSH.ADCBUSY.offset
                    adcdone = (readback[0]&LpgbtRegisterMapV1.ADCSTATUSH.ADCDONE.bit_mask)>>LpgbtRegisterMapV1.ADCSTATUSH.ADCDONE.offset
                    adcvalue= (((readback[0]&LpgbtRegisterMapV1.ADCSTATUSH.ADCVALUE.bit_mask)>>LpgbtRegisterMapV1.ADCSTATUSH.ADCVALUE.offset)<<8)+((readback[1]&LpgbtRegisterMapV1.ADCSTATUSL.ADCVALUE.bit_mask)>>LpgbtRegisterMapV1.ADCSTATUSL.ADCVALUE.offset)
                    self.validate_lpgbt_adc(adcbusy, adcdone, adcvalue)
                except Exception as e:
                    # self.message_out.emit((f'CSM{i} {self.csm_tab.cell_list[i].SCA_temp_label[j]} read back error'));
                    self.message_out.emit(str(e))
                    self.display_values.put((i, k, j), 'NA')

                else:
                    # (voltage*0.42-0.5)*2=(adcvalue-512)/1024*2  ## diff = -1 when adcvalue=0
                    if monitor_index == 1:
                        voltage = adcvalue/1024.0
                        delta_voltage = voltage-vtrx_baseline_voltage
                        current_a = curdac_value*curdac_uA_per_code*1.0e-6
                        r_kohm = delta_voltage/current_a/1000.0
                        display_value = float("nan") if r_kohm <= 0 else 1.0/(math.log(r_kohm/1.0)/3500.0+1.0/298.15)-273.15
                    elif monitor_index == 14:
                        if lpgbt_calibration is not None:
                            display_value = adcvalue*lpgbt_calibration['TEMPERATURE_UNCALVREF_SLOPE']+lpgbt_calibration['TEMPERATURE_UNCALVREF_OFFSET']
                        else:
                            voltage = adcvalue/1024.0
                            display_value = (voltage-0.448)/0.00242
                    elif monitor_index >=10 and monitor_index <=13:
                        display_value = adcvalue/1024.0/0.428
                    else:
                        display_value = adcvalue/1024.0
                    unit = self.csm_tab.cell_list[i].lpGBT_list[k].lpGBT_monitor_unit[j]
                    label = self.csm_tab.cell_list[i].lpGBT_list[k].lpGBT_monitor_label[j]
                    display_text = self.format_display_text(display_value, unit)
                    source = 'lpGBT master' if k == 0 else 'lpGBT slave'
                    self.record_monitor_value(scan_index, i, source, label, adcvalue, display_value, unit, display_text, lpgbt_addr, monitor_index)
                    self.display_values.put((i, k, j), display_text)

