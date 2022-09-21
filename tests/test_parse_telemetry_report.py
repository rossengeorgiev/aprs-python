import unittest

from aprslib.parsing import parse_telemetry_report


class ParseTelemetryReport(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_valid_telemetry_report(self):
        packet = "#111,13.64,0.37,5,16.96,33.38,11110000"
        expected = {'format': 'telemetry-report',
                    'telemetry':
                        {'bits': '11110000',
                         'seq': 111,
                         'vals': [13.64, 0.37, 5, 16.96, 33.38]}}

        _, result = parse_telemetry_report(packet)
        self.assertEqual(expected, result)

    def test_invalid_telemetry_report(self):
        packet = "#111a,Nan,0.37,5.10,16.96,33.38,11110000"
        expected = {}

        rest, result = parse_telemetry_report(packet)
        self.assertEqual(expected, result)
        self.assertEqual(rest,packet)


if __name__ == '__main__':
    unittest.main()
