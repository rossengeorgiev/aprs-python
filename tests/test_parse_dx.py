"""Tests for DX spot parsing."""
import unittest
from aprslib.parsing.dx import parse_dx
import aprslib


class DxParseTest(unittest.TestCase):
    """Test DX spot parser."""

    def test_basic_dx_spot(self):
        """Test a complete DX spot."""
        body = "DX de N0CALL: 14250.0 VK2ABC calling CQ 1234Z"
        _, result = parse_dx(body)
        self.assertEqual(result['format'], 'dx')
        self.assertEqual(result['dxsource'], 'N0CALL')
        self.assertEqual(result['dxfreq'], 14250.0)
        self.assertEqual(result['dxcall'], 'VK2ABC')
        self.assertEqual(result['dxinfo'], 'calling CQ')
        self.assertEqual(result['dxtime'], '1234Z')

    def test_dx_no_time(self):
        """Test DX spot without time."""
        body = "DX de WB4BOR: 7035.0 UA3ABC strong signal"
        _, result = parse_dx(body)
        self.assertEqual(result['dxsource'], 'WB4BOR')
        self.assertEqual(result['dxfreq'], 7035.0)
        self.assertEqual(result['dxcall'], 'UA3ABC')
        self.assertEqual(result['dxinfo'], 'strong signal')
        self.assertNotIn('dxtime', result)

    def test_dx_minimal(self):
        """Test DX spot with just freq and call."""
        body = "DX de N0CALL: 21300.5 JA1XYZ"
        _, result = parse_dx(body)
        self.assertEqual(result['dxsource'], 'N0CALL')
        self.assertEqual(result['dxfreq'], 21300.5)
        self.assertEqual(result['dxcall'], 'JA1XYZ')
        self.assertNotIn('dxinfo', result)

    def test_dx_three_digit_time(self):
        """Test DX spot with 3-digit time."""
        body = "DX de W1AW: 14195.0 K6TEST cq 830Z"
        _, result = parse_dx(body)
        self.assertEqual(result['dxtime'], '830Z')
        self.assertEqual(result['dxfreq'], 14195.0)

    def test_dx_with_ssid(self):
        """Test DX spot source with SSID."""
        body = "DX de N0CALL-5: 14250.0 VK2ABC test"
        _, result = parse_dx(body)
        self.assertEqual(result['dxsource'], 'N0CALL-5')

    def test_dx_colon_separator(self):
        """Test DX with colon separator."""
        body = "DX de N0CALL: 28450.3 PY1ZZ"
        _, result = parse_dx(body)
        self.assertEqual(result['dxfreq'], 28450.3)
        self.assertEqual(result['dxcall'], 'PY1ZZ')

    def test_full_packet_dispatch(self):
        """Test that full packets dispatch correctly to DX parser."""
        # DX spot uses "D" as first char then "X de ..."
        packet = "N0CALL>APRS:DX de WB4BOR: 14250.0 VK2ABC calling CQ 1234Z"
        result = aprslib.parse(packet)
        self.assertEqual(result['format'], 'dx')
        self.assertEqual(result['dxsource'], 'WB4BOR')
        self.assertEqual(result['dxfreq'], 14250.0)


if __name__ == '__main__':
    unittest.main()
