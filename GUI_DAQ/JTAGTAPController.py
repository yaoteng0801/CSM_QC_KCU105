from SCA_share import *

class JTAGTAPController:
    def __init__(self):
        """
        Initialize the JTAG TAP controller with the starting state.
        """
        # Define the initial TAP state
        self.state = "Run-Test/Idle"
        self.state_transitions = self._build_state_transitions()

    def _build_state_transitions(self):
        """
        Define the JTAG state machine transitions based on TMS values.

        Returns:
            dict: A dictionary representing state transitions for each state
                  based on the TMS bit (0 or 1).
        """
        return {
            "Test-Logic-Reset": {0: "Run-Test/Idle", 1: "Test-Logic-Reset"},
            "Run-Test/Idle": {0: "Run-Test/Idle", 1: "Select-DR-Scan"},
            "Select-DR-Scan": {0: "Capture-DR", 1: "Select-IR-Scan"},
            "Capture-DR": {0: "Shift-DR", 1: "Exit1-DR"},
            "Shift-DR": {0: "Shift-DR", 1: "Exit1-DR"},
            "Exit1-DR": {0: "Pause-DR", 1: "Update-DR"},
            "Pause-DR": {0: "Pause-DR", 1: "Exit2-DR"},
            "Exit2-DR": {0: "Shift-DR", 1: "Update-DR"},
            "Update-DR": {0: "Run-Test/Idle", 1: "Select-DR-Scan"},
            "Select-IR-Scan": {0: "Capture-IR", 1: "Test-Logic-Reset"},
            "Capture-IR": {0: "Shift-IR", 1: "Exit1-IR"},
            "Shift-IR": {0: "Shift-IR", 1: "Exit1-IR"},
            "Exit1-IR": {0: "Pause-IR", 1: "Update-IR"},
            "Pause-IR": {0: "Pause-IR", 1: "Exit2-IR"},
            "Exit2-IR": {0: "Shift-IR", 1: "Update-IR"},
            "Update-IR": {0: "Run-Test/Idle", 1: "Select-DR-Scan"}
        }

    def apply_tms(self, tms, tdi_sequence, tms_sequence, tdi_mask, tdi='0',tdi_valid=''):
        """
        Move to the next state based on the current TMS bit, pad TDI with '0' for non-shifting states,
        and update the TDI_mask accordingly.

        Args:
            tms (int): The TMS bit (0 or 1).
            tdi_sequence (list): The TDI sequence to be padded.
            tms_sequence (list): The TMS sequence to be appended.
            tdi_mask (list): The TDI mask sequence to be updated.
        """
        tms_sequence[0]+=tms
        tdi_sequence[0]+=tdi

        # Pad TDI with '1' (don't care) bit and set mask to '0' for each TMS transition in non-shifting states
        if len(tdi_valid):
            tdi_mask[0]+=tdi_valid
        else:
            if self.state not in ["Shift-DR"]:
                tdi_mask[0]+='0'  # Mark as 'don't care' in the mask
            else:
                tdi_mask[0]+='1'  # Mark as 'valid' in the mask
        self.state = self.state_transitions[self.state][int(tms)]

    def shift_ir(self, instruction, reset_after=False, capture_readback=False):  # starts from RTI and ends at RTI
        """
        Shift an instruction into the IR register and produce TDI, TMS, and TDI_mask sequences.

        Args:
            instruction (int): Instruction bits to shift in.
            reset_after (bool): Reset the TAP after updating the instruction,
                then return to Run-Test/Idle.
            capture_readback (bool): Mark TDO captured while shifting the IR as
                valid in the returned mask. Disabled by default so existing
                full-sequence callers continue to receive DR readback only.
            ir_length (int): Length of the IR register in bits.

        Returns:
            list, list, list: TDI, TMS, and TDI_mask sequences for IR shift.
        """
        tdi_sequence = ['']
        tms_sequence = ['']
        tdi_mask = ['']
        ir_tdi_valid = '1' if capture_readback else '0'

        # Move from Run-Test/Idle to Select-DR-Scan, then to Select-IR-Scan
        self.apply_tms('1', tdi_sequence, tms_sequence, tdi_mask)  # enter Select-DR-Scan
        self.apply_tms('1', tdi_sequence, tms_sequence, tdi_mask)  # enter Select-IR-Scan
        self.apply_tms('0', tdi_sequence, tms_sequence, tdi_mask)  # enter Capture-IR
        self.apply_tms('0', tdi_sequence, tms_sequence, tdi_mask)  # enter Shift-IR

        # Shift the instruction into IR
        for i in range(len(instruction)-1):
            self.apply_tms('0', tdi_sequence, tms_sequence, tdi_mask, instruction[-i-1], ir_tdi_valid)  # Shift-IR

        
        # Exit Shift-IR state
        self.apply_tms('1', tdi_sequence, tms_sequence, tdi_mask, instruction[0], ir_tdi_valid)  # Exit1-IR
        if reset_after:
            # Both branches finish in RTI, but UG470 requires JPROGRAM to
            # traverse and hold TLR after Update-IR; going directly from
            # Update-IR to RTI is not the same TAP sequence.
            # Exit1-IR -> Update-IR -> Select-DR -> Select-IR -> TLR,
            # then hold TLR for one clock before returning to RTI.
            for _ in range(5):
                self.apply_tms('1', tdi_sequence, tms_sequence, tdi_mask)
            self.apply_tms('0', tdi_sequence, tms_sequence, tdi_mask)  # Run-Test/Idle
        else:
            self.apply_tms('1', tdi_sequence, tms_sequence, tdi_mask)  # Update-IR
            self.apply_tms('0', tdi_sequence, tms_sequence, tdi_mask)  # Run-Test/Idle

        return tdi_sequence, tms_sequence, tdi_mask

    def shift_dr(self, data, isASD=False):  #data is MSB first, so need a reverse when generating JTAG sequence
        """
        Shift data into the DR register and produce TDI, TMS, and TDI_mask sequences.

        Args:
            data (int): Data bits to shift in.
            dr_length (int): Length of the DR register in bits.

        Returns:
            list, list, list: TDI, TMS, and TDI_mask sequences for DR shift.
        """
        tdi_sequence = ['']
        tms_sequence = ['']
        tdi_mask = ['']

        # Enter DR shift state
        self.apply_tms('1', tdi_sequence, tms_sequence, tdi_mask)  # entering Select-DR-Scan
        self.apply_tms('0', tdi_sequence, tms_sequence, tdi_mask)  # entering Capture-DR
        self.apply_tms('0', tdi_sequence, tms_sequence, tdi_mask)  # entering Shift-DR
        if isASD: 
            #add one additional bits for ASD shifting at the beginning. This is due to a SCLK block at the beginning.
            self.apply_tms('0', tdi_sequence, tms_sequence, tdi_mask,tdi='0',tdi_valid='0')  # entering Shift-DR
            # Add a known extra bit for ASD TDO reg
            self.apply_tms('0', tdi_sequence, tms_sequence, tdi_mask,tdi='0',tdi_valid='0')  # entering Shift-DR

        # Shift the data into DR
        for i in range(len(data)-1):
            self.apply_tms('0', tdi_sequence, tms_sequence, tdi_mask, data[-i-1])  # Shift-DR

        # Exit Shift-DR state
        self.apply_tms('1', tdi_sequence, tms_sequence, tdi_mask, data[0])  # Exit1-DR
        self.apply_tms('1', tdi_sequence, tms_sequence, tdi_mask)  # Update-DR
        self.apply_tms('0', tdi_sequence, tms_sequence, tdi_mask)  # Run-Test/Idle

        return tdi_sequence, tms_sequence, tdi_mask

    def full_sequence(self, ir_value, dr_value, isASD=False):
        """
        Generate the full TDI, TMS, and separate IR/DR readback masks for
        shifting IR, DR, and returning to Run-Test/Idle.

        Args:
            ir_value (int): The instruction value for IR shift.
            dr_value (int): The data value for DR shift.
            ir_length (int): The length of the instruction register in bits.
            dr_length (int): The length of the data register in bits.

        Returns:
            str, str, str, str: The combined TDI and TMS sequences, followed
                by aligned IR and DR readback masks.
        """
        # Shift IR and mark the captured IR bits in its local mask.
        ir_tdi, ir_tms, ir_mask = self.shift_ir(ir_value, False, True)

        # Shift DR and get the TDI, TMS, and TDI_mask sequences
        dr_tdi, dr_tms, dr_mask = self.shift_dr(dr_value,isASD)

        # Combine TDI and TMS, and align separate IR/DR masks to the entire
        # clock sequence. This avoids mixing captured IR status with DR data.
        tdi_RTI  = '000000'
        tms_RTI  = '111110'
        mask_RTI = '000000'

        combined_tdi = tdi_RTI + ir_tdi[0] + dr_tdi[0]
        combined_tms = tms_RTI + ir_tms[0] + dr_tms[0]
        combined_ir_mask = mask_RTI + ir_mask[0] + '0' * len(dr_mask[0])
        combined_dr_mask = mask_RTI + '0' * len(ir_mask[0]) + dr_mask[0]
        return combined_tdi, combined_tms, combined_ir_mask, combined_dr_mask



# Example Usage
if __name__ == "__main__":
    jtag_tap = JTAGTAPController()

    # Example Instruction Register (IR) and Data Register (DR) values
    ir_value = '10001'  # Example binary value for IR
    dr_value = 32*'0'  # Example binary value for DR
    # ir_length = 5  # Example IR length in bits
    # dr_length = 9  # Example DR length in bits

    # Generate the full TDI, TMS, and TDI_mask sequences
    full_tdi, full_tms, ir_mask, dr_mask = jtag_tap.full_sequence(ir_value, dr_value)

    print("Full TDI Sequence:", full_tdi)
    print("Full TMS Sequence:", full_tms)
    print("IR Readback Mask:", ir_mask)
    print("DR Readback Mask:", dr_mask)
