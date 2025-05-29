# High Level Analyzer
# For more information and documentation, please go to https://support.saleae.com/extensions/high-level-analyzer-extensions

from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame, StringSetting, NumberSetting, ChoicesSetting


# High level analyzers must subclass the HighLevelAnalyzer class.
class Hla(HighLevelAnalyzer):
    # An optional list of types this analyzer produces, providing a way to customize the way frames are displayed in Logic 2.
    result_types = {
        'Throttle': {'format': 'DSHOT:  Throttle:{{data.Throttle}},  Tel-Req:{{data.Telem-Requested}},  CRC:{{data.Crc}}'},
        'Command': {'format': 'DSHOT:  Command:{{data.Command}},  Tel-Req:{{data.Telem-Requested}},  CRC:{{data.Crc}}'},
        'Disarmed': {'format': 'DSHOT:  Disarmed,  Tel-Req:{{data.Telem-Requested}},  CRC:{{data.Crc}}'},
    }

    def __init__(self):
        '''
        Initialize HLA.
        '''

    def decode(self, frame: AnalyzerFrame):
        '''
        Process a frame from the input analyzer, and optionally return a single `AnalyzerFrame` or a list of `AnalyzerFrame`s.

        The type and data values in `frame` will depend on the input analyzer.
        '''

        # Return the data frame itself
        data = frame.data['data']
        res = 0
        for i in range(6):
            res = (res << 8) | data[i]
        res ^= 0xFFFFFFFFFFFF
        back = res
        res <<= 1 # Add the start bit.
        res |= 1  # Add the start bit.
        raw = 0x0000
        for i in range(16):
            raw <<= 1
            bit = res & 2
            if bit > 0:
                raw |= 1
            res >>= 3

        # Timing Specification:
        #   DSHOT Bitrate     T1H    T0H    Bit (µs)  Frame (µs)
        #   150   150kbit/s   5.00   2.50   6.67      106.72
        #   300   300kbit/s   2.50   1.25   3.33      53.28
        #   600   600kbit/s   1.25   0.625  1.67      26.72
        #   1200  1200kbit/s  0.625  0.313  0.83      13.28
        #
        # Frame Specification:
        #   Total Bits: 16
        #   D: Data (11)
        #   T: Telemetry Request (1)
        #   C: Crc bits (4)
        #   Format: MSB -------- LSB 
        #           DDDDDDDDDDDTCCCC
        #   
        # Data Value Specification:
        #         0: Disarmed
        #      1-47: Command
        #   48-2048: Throttle Values: 0-1999
        #
        # Crc Calculation:
        # Crc = (value ^ (value >> 4) ^ (value >> 8)) & 0x0F;

        THROTTLE_START = 48

        crc = raw & 0x000F
        data = raw >> 4
        telemetryRequest = data & 1
        throttle = data >> 1
        throttlePercent = (throttle - THROTTLE_START) * 100 / 1999
        crcCheck = (data ^ (data >> 4) ^ (data >> 8)) & 0x0F;

        telemRequested = "Yes" if telemetryRequest == 1 else "No"
        ok = "Pass" if crc == crcCheck else "Fail"
        crcResult = str(crc) + " (" + ok + ")"

        if throttle == 0:
            print(f"DSHOT-Disarmed, Tel-Req: {telemRequested}, Crc: {crcResult}")
            return AnalyzerFrame('Disarmed', frame.start_time, frame.end_time, {
                'Throttle': '', 'Throttle(%)': '', 'Command': '', 'Telem-Requested': telemRequested, 'Crc': crcResult })

        if throttle < THROTTLE_START:
            print(f"DSHOT-Command: {str(throttle)}, Tel-Req: {telemRequested}, Crc: {crcResult}")
            return AnalyzerFrame('Command', frame.start_time, frame.end_time, {
                'Throttle': '', 'Throttle(%)': '', 'Command': str(throttle), 'Telem-Requested': telemRequested, 'Crc': crcResult })

        throttle -= THROTTLE_START
        print(f"DSHOT-Throttle: {str(throttle)} ({throttlePercent:.2f}%), Tel-Req: {telemRequested}, Crc: {crcResult}")
        return AnalyzerFrame('Throttle', frame.start_time, frame.end_time, {
            'Throttle': str(throttle), 'Throttle(%)': f"{throttlePercent:.2f}", 'Command': '', 'Telem-Requested': telemRequested, 'Crc': crcResult })
