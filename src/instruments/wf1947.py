import pyvisa
import time
import numpy as np

rm = pyvisa.ResourceManager()

class WF1947:
    """
    Class for controlling NF Corporation WF1947/WF1948 multifunction signal source via VISA (USB-TMC or GPIB).

    Initialization parameters:
    resource_address: String, VISA resource address of the device.
                    e.g. 'USB0::0x0D4A::0x000D::[serial]::INSTR' or 'GPIB0::2::INSTR'
    channel:          Integer, specify the channel to control (1 or 2). Default is 1.

    Attributes:
    .inst:            pyVISA resource object for hardware communication.
    .channel:         Current channel number.
    .waveforms:       Dictionary mapping short waveform names to SCPI command keywords.
    
    Main methods:
    .reset():                       Send *RST command to reset the instrument to default settings.
    .set_output(state):             Turn signal output ON or OFF (True/False).
    .get_output():                  Query current output state.
    .set_waveform(shape):           Set output waveform ('SIN', 'SQU', 'RAMP', etc).
    .get_waveform():                Query current waveform.
    .set_frequency(freq_hz):        Set output frequency (Hz).
    .get_frequency():               Query current frequency (Hz).
    .set_amplitude(amp_vpp):        Set output amplitude (Vp-p).
    .get_amplitude():               Query current amplitude (Vp-p).
    .set_offset(offset_v):          Set DC offset (V).
    .get_offset():                  Query current DC offset (V).
    .set_load(impedance_ohm):       Set output load impedance (ohm or 'INF' for high-Z).
    .get_load():                    Query current load impedance.
    .setup_frequency_sweep(...):    Convenience method for quick frequency sweep configuration.
    .setup_external_fm(...):        Convenience method for quick external FM configuration.
    .close():                       Close the connection to the instrument.
    """
    type = "WF1947"
    
    def __init__(self, resource_address, channel=1):
        if channel not in [1, 2]:
            raise ValueError("Channel must be 1 or 2.")
        
        self.channel = channel
        try:
            self.inst = rm.open_resource(resource_address)
            idn = self.inst.query("*IDN?")
            print(f"Connected to: {idn}")
        except Exception as e:
            print(f"Error connecting to WF1947/WF1948: {e}")
            print("Please check the connection and VISA address, and ensure NI-VISA driver is installed.")
            raise e

        self.waveforms = {
            "SIN": "SINusoid",
            "SQU": "SQUare",
            "RAMP": "RAMP",
            "PULSE": "PULSE",
            "NOISE": "NOISE",
            "DC": "DC",
            "USER": "USER"
        }
        
        # 应用初始设置
        self.apply_initial_settings()

    def apply_initial_settings(self):
        """
        应用初始设置：10mV Vpp，1kHz，正弦波形，0V直流偏置
        """
        try:
            print("正在应用初始设置...")
            self.set_waveform("SIN")          # 正弦波形
            self.set_frequency(1000)          # 1kHz频率
            self.set_amplitude(0.01)          # 10mV Vpp (0.01V)
            self.set_offset(0)                # 0V直流偏置
            self.set_output(False)            # 初始关闭输出
            print("初始设置完成：10mV Vpp，1kHz，正弦波形，0V直流偏置，输出关闭")
        except Exception as e:
            print(f"应用初始设置时出错: {e}")

    def _write(self, command):
        """Internal method, send command to the specified channel."""
        if command.upper().startswith(('FREQ', 'VOLT', 'PHAS', 'FUNC', 'SWE', 'FM', 'PM', 'AM', 'BURS')):
            self.inst.write(f'SOURce{self.channel}:{command}')
        elif command.upper().startswith(('OUTP', 'LOAD')):
            self.inst.write(f'OUTPut{self.channel}:{command}')
        else:
            self.inst.write(command)

    def _query(self, command):
        """Internal method, query information from the specified channel."""
        if command.upper().startswith(('FREQ', 'VOLT', 'PHAS', 'FUNC', 'SWE', 'FM', 'PM', 'AM', 'BURS')):
            return self.inst.query(f'SOURce{self.channel}:{command}').strip()
        elif command.upper().startswith(('OUTP', 'LOAD')):
            return self.inst.query(f'OUTPut{self.channel}:{command}').strip()
        else:
            return self.inst.query(command).strip()

    def reset(self):
        """Reset the instrument to default settings."""
        self.inst.write('*RST')
        self.inst.write('*WAI') # Wait for operation to complete
        print("Instrument reset.")

    def set_output(self, state):
        """Set output state. state: bool (True=ON, False=OFF)"""
        cmd_state = "ON" if state else "OFF"
        self._write(f'OUTPut:STATe {cmd_state}')
        
    def get_output(self):
        """Get output state. Returns 'ON' or 'OFF'."""
        state = self._query('OUTPut:STATe?')
        return 'ON' if state == '1' else 'OFF'

    def set_waveform(self, shape="SIN"):
        """Set output waveform. shape: 'SIN', 'SQU', 'RAMP', etc."""
        shape_cmd = self.waveforms.get(shape.upper())
        if shape_cmd:
            self._write(f'FUNCtion:SHAPe {shape_cmd}')
        else:
            raise ValueError(f"Invalid waveform: {shape}. Available: {list(self.waveforms.keys())}")

    def get_waveform(self):
        """Get current waveform."""
        return self._query('FUNCtion:SHAPe?')

    def set_frequency(self, freq_hz):
        """Set output frequency (Hz)."""
        self._write(f'FREQuency {freq_hz}')

    def get_frequency(self):
        """Get current frequency (Hz). Returns float."""
        return float(self._query('FREQuency?'))

    def set_amplitude(self, amp_vpp):
        """Set output amplitude (Vp-p)."""
        self._write(f'VOLTage:AMPLitude {amp_vpp}VPP')

    def get_amplitude(self):
        """Get current amplitude (Vp-p). Returns float."""
        return float(self._query('VOLTage:AMPLitude?'))

    def set_offset(self, offset_v):
        """Set DC offset (V)."""
        self._write(f'VOLTage:OFFSet {offset_v}')

    def get_offset(self):
        """Get current DC offset (V). Returns float."""
        return float(self._query('VOLTage:OFFSet?'))
        
    def set_load(self, impedance_ohm):
        """
        Set output load impedance. impedance_ohm: int or 'INF' (high-Z).
        Load impedance: 1 Ω to 10 kΩ, Resolution: 1 Ω
        Setting example: :OUTPut1:LOAD 50OHM
        """
        if isinstance(impedance_ohm, str) and impedance_ohm.upper() == 'INF':
            self._write('LOAD INFinity')
        else:
            self._write(f'LOAD {impedance_ohm} OHM')

    def get_load(self):
        """Get current load impedance."""
        return self._query('LOAD?')

    def setup_frequency_sweep(self, start_hz, stop_hz, sweep_time_s, spacing='LINear', direction='RAMP', load='INF'):
        """
        Convenience method: configure frequency sweep mode.
        start_hz:       Start frequency (Hz)
        stop_hz:        Stop frequency (Hz)
        sweep_time_s:   Sweep time (seconds)
        spacing:        Sweep spacing, 'LINear' or 'LOGarithmic'
        direction:      Sweep direction, 'RAMP' or 'TRIangle'
        load:           Load impedance, int(1-10000) or 'INF'
        """
        print(f"Configuring frequency sweep: {start_hz} Hz -> {stop_hz} Hz in {sweep_time_s}s...")
        self._write('FREQuency:MODE SWEep')
        self._write(f'FREQuency:STARt {start_hz}')
        self._write(f'FREQuency:STOP {stop_hz}')
        self._write(f'SWEep:TIME {sweep_time_s}')
        self._write(f'SWEep:SPACing {spacing}')
        self._write(f'SWEep:INTernal:FUNCtion {direction}')
        self.set_load(load)
        print("Frequency sweep mode configured.")

    def setup_external_fm(self, carrier_hz, deviation_hz, load='INF'):
        """
        Convenience method: configure external FM mode.
        carrier_hz:     Carrier frequency (Hz)
        deviation_hz:   Peak frequency deviation (Hz)
        load:           Load impedance, int(1-10000) or 'INF'
        """
        print(f"Configuring external FM: carrier {carrier_hz} Hz, deviation {deviation_hz} Hz...")
        self._write('FM:STATe ON')
        self._write('FM:SOURce EXTernal')
        self._write(f'FREQuency {carrier_hz}')
        self._write(f'FM:DEViation {deviation_hz}')
        self.set_load(load)
        print("External FM mode configured.")

    def close(self):
        """Close the connection to the instrument."""
        self.inst.close()
        print("FW1974 Device connection closed.")