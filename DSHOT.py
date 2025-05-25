# High Level Analyzer
# For more information and documentation, please go to https://support.saleae.com/extensions/high-level-analyzer-extensions

from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame, StringSetting, NumberSetting, ChoicesSetting


# High level analyzers must subclass the HighLevelAnalyzer class.
class Hla(HighLevelAnalyzer):
    # An optional list of types this analyzer produces, providing a way to customize the way frames are displayed in Logic 2.
    result_types = {
        'DSHOT': {'format': '{{type}}:  Throttle:{{data.Throttle}},  Tel-Req:{{data.Telem-Requested}},  CRC:{{data.Crc}}'},
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

        crc = raw & 0x000F
        data = raw >> 4
        telemetryRequest = data & 1
        throttle = data >> 1
        throttlePercent = throttle * 100 / 0x7FF
        crcCheck = (data ^ (data >> 4) ^ (data >> 8)) & 0x0F;

        telemRequested = "Yes" if telemetryRequest == 1 else "No"
        ok = "Pass" if crc == crcCheck else "Fail"
        crcResult = str(crc) + " (" + ok + ")"

        print(f"Throttle: {str(throttle)} ({throttlePercent:.2f}%), Tel-Req: {telemRequested}, Crc: {crcResult}")

        return AnalyzerFrame('DSHOT', frame.start_time, frame.end_time, {
            'Throttle': str(throttle), 'Throttle(%)': f"{throttlePercent:.2f}", 'Telem-Requested': telemRequested, 'Crc': crcResult
        })
