import unittest

from aprslib import parse
from aprslib.parsing.telemetry import parse_telemetry_config


class ParseTelemetryConfig(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_bits_with_short_title(self):
        """Test BITS telemetry config with title within spec limit"""
        packet = "TEST>APRS::TESTCALL :BITS.11001010,Short Title"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry-message')
        self.assertEqual(result['tBITS'], '11001010')
        self.assertEqual(result['title'], 'Short Title')

    def test_bits_with_long_title(self):
        """Test BITS telemetry config with title exceeding spec limit (real-world case)"""
        packet = "SP4MAZ>APN001::SP4MAZ-10:BITS.00000000,Hotspot CPU AVG/Temperature"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry-message')
        self.assertEqual(result['tBITS'], '00000000')
        self.assertEqual(result['title'], 'Hotspot CPU AVG/Temperature')
        self.assertEqual(len(result['title']), 27)

    def test_bits_with_very_long_title(self):
        """Test BITS telemetry config with very long title"""
        long_title = "A" * 50
        packet = f"TEST>APRS::TESTCALL :BITS.11111111,{long_title}"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry-message')
        self.assertEqual(result['tBITS'], '11111111')
        self.assertEqual(result['title'], long_title)
        self.assertEqual(len(result['title']), 50)

    def test_bits_with_no_title(self):
        """Test BITS telemetry config with no title"""
        packet = "TEST>APRS::TESTCALL :BITS.11001010,"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry-message')
        self.assertEqual(result['tBITS'], '11001010')
        self.assertEqual(result['title'], '')

    def test_bits_with_spaces_in_title(self):
        """Test BITS telemetry config with spaces in title"""
        packet = "TEST>APRS::TESTCALL :BITS.11001010,Title With Spaces"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry-message')
        self.assertEqual(result['tBITS'], '11001010')
        self.assertEqual(result['title'], 'Title With Spaces')

    def test_bits_with_special_characters(self):
        """Test BITS telemetry config with special characters in title"""
        packet = "TEST>APRS::TESTCALL :BITS.11001010,Title-With/Special_Chars"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry-message')
        self.assertEqual(result['tBITS'], '11001010')
        self.assertEqual(result['title'], 'Title-With/Special_Chars')

    def test_parse_telemetry_config_bits_direct(self):
        """Test parse_telemetry_config function directly with BITS"""
        body = "BITS.11001010,Test Title"
        remaining, result = parse_telemetry_config(body)

        self.assertEqual(result['format'], 'telemetry-message')
        self.assertEqual(result['tBITS'], '11001010')
        self.assertEqual(result['title'], 'Test Title')

    def test_parse_telemetry_config_parm(self):
        """Test PARM telemetry config"""
        packet = "TEST>APRS::TESTCALL :PARM.Battery,BTemp,AirTemp,Pres,Altude"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry-message')
        self.assertIn('tPARM', result)
        self.assertEqual(len(result['tPARM']), 13)
        self.assertEqual(result['tPARM'][0], 'Battery')
        self.assertEqual(result['tPARM'][1], 'BTemp')
        self.assertEqual(result['tPARM'][2], 'AirTemp')

    def test_parse_telemetry_config_unit(self):
        """Test UNIT telemetry config"""
        packet = "TEST>APRS::TESTCALL :UNIT.Volts,deg.F,deg.F,Mbar,Kfeet"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry-message')
        self.assertIn('tUNIT', result)
        self.assertEqual(len(result['tUNIT']), 13)
        self.assertEqual(result['tUNIT'][0], 'Volts')
        self.assertEqual(result['tUNIT'][1], 'deg.F')

    def test_parse_telemetry_config_eqns(self):
        """Test EQNS telemetry config"""
        packet = "TEST>APRS::TESTCALL :EQNS.0,2.6,0,0,.53,-32,3,4.39,49,-32"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry-message')
        self.assertIn('tEQNS', result)
        self.assertIsInstance(result['tEQNS'], list)
        self.assertEqual(len(result['tEQNS']), 5)

    def test_parse_telemetry_config_eqns_with_spaces(self):
        """Test EQNS telemetry config with spaces after commas (real-world packet)"""
        packet = "IZ6RND>IESPX,TCPIP*,qAC,T2NL::IZ6RND   :EQNS.0,0.392,-20, 0,0.235,0, 0,0.1,0, 0,1,0, 0,1,0"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry-message')
        self.assertIn('tEQNS', result)
        self.assertIsInstance(result['tEQNS'], list)
        self.assertEqual(len(result['tEQNS']), 5)
        # Verify the values are correctly parsed (spaces should be stripped)
        expected = [[0, 0.392, -20], [0, 0.235, 0], [0, 0.1, 0], [0, 1, 0], [0, 1, 0]]
        self.assertEqual(result['tEQNS'], expected)

    def test_parse_telemetry_config_eqns_with_non_numeric_suffix(self):
        """Test EQNS telemetry config with non-numeric characters in last value (real-world packet)"""
        packet = "DB0PBG-5>APMI03,DB0OL-10*,WIDE2-1,qAR,DB0PDF-10::DB0PBG-5 :EQNS.0,0.075,0,0,0.5,-64,0,10,0,0,1,0,0,0,03n"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry-message')
        self.assertIn('tEQNS', result)
        self.assertIsInstance(result['tEQNS'], list)
        self.assertEqual(len(result['tEQNS']), 5)
        # Verify the values are correctly parsed (03n should be parsed as 3)
        expected = [[0, 0.075, 0], [0, 0.5, -64], [0, 10, 0], [0, 1, 0], [0, 0, 3]]
        self.assertEqual(result['tEQNS'], expected)

    def test_bits_without_binary_bits(self):
        """Test BITS telemetry config without binary bits (malformed packet)"""
        packet = "E25HML-13>APRS,TCPIP*,qAC,T2PERTH::E25HML-13:BITS.ESP8266 Test WX DHT22 version"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry-message')
        self.assertEqual(result['tBITS'], '00000000')  # Default to all zeros
        self.assertEqual(result['title'], 'ESP8266 Test WX DHT22 version')


if __name__ == '__main__':
    unittest.main()
