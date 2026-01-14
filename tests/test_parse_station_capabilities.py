import unittest

from aprslib import parse
from aprslib.parsing.misc import parse_station_capabilities
from aprslib.exceptions import ParseError


class ParseStationCapabilities(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_valid_capabilities_basic_token(self):
        """Test basic station capabilities with single token"""
        packet = "TEST>APRS:<IGATE"
        result = parse(packet)

        self.assertEqual(result['format'], 'station-capabilities')
        self.assertIn('capabilities', result)
        self.assertEqual(result['capabilities']['IGATE'], True)

    def test_valid_capabilities_multiple_tokens(self):
        """Test station capabilities with multiple tokens"""
        packet = "TEST>APRS:<IGATE,DIGI,RF"
        result = parse(packet)

        self.assertEqual(result['format'], 'station-capabilities')
        self.assertEqual(result['capabilities']['IGATE'], True)
        self.assertEqual(result['capabilities']['DIGI'], True)
        self.assertEqual(result['capabilities']['RF'], True)

    def test_valid_capabilities_with_values(self):
        """Test station capabilities with TOKEN=VALUE format"""
        packet = "TEST>APRS:<IGATE,MSG_CNT=123,LOC_CNT=5"
        result = parse(packet)

        self.assertEqual(result['format'], 'station-capabilities')
        self.assertEqual(result['capabilities']['IGATE'], True)
        self.assertEqual(result['capabilities']['MSG_CNT'], 123)
        self.assertEqual(result['capabilities']['LOC_CNT'], 5)

    def test_valid_capabilities_mixed_tokens_and_values(self):
        """Test station capabilities with mix of tokens and TOKEN=VALUE"""
        packet = "TEST>APRS:<IGATE,MSG_CNT=123,DIGI,LOC_CNT=5"
        result = parse(packet)

        self.assertEqual(result['format'], 'station-capabilities')
        self.assertEqual(result['capabilities']['IGATE'], True)
        self.assertEqual(result['capabilities']['MSG_CNT'], 123)
        self.assertEqual(result['capabilities']['DIGI'], True)
        self.assertEqual(result['capabilities']['LOC_CNT'], 5)

    def test_valid_capabilities_integer_values(self):
        """Test station capabilities with integer values"""
        packet = "TEST>APRS:<MSG_CNT=123,LOC_CNT=456,OTHER=789"
        result = parse(packet)

        self.assertEqual(result['format'], 'station-capabilities')
        self.assertEqual(result['capabilities']['MSG_CNT'], 123)
        self.assertEqual(result['capabilities']['LOC_CNT'], 456)
        self.assertEqual(result['capabilities']['OTHER'], 789)
        self.assertIsInstance(result['capabilities']['MSG_CNT'], int)

    def test_valid_capabilities_float_values(self):
        """Test station capabilities with float values"""
        packet = "TEST>APRS:<MSG_CNT=123.45,LOC_CNT=5.67"
        result = parse(packet)

        self.assertEqual(result['format'], 'station-capabilities')
        self.assertEqual(result['capabilities']['MSG_CNT'], 123.45)
        self.assertEqual(result['capabilities']['LOC_CNT'], 5.67)
        self.assertIsInstance(result['capabilities']['MSG_CNT'], float)

    def test_valid_capabilities_negative_values(self):
        """Test station capabilities with negative values"""
        packet = "TEST>APRS:<MSG_CNT=-123,LOC_CNT=-5"
        result = parse(packet)

        self.assertEqual(result['format'], 'station-capabilities')
        self.assertEqual(result['capabilities']['MSG_CNT'], -123)
        self.assertEqual(result['capabilities']['LOC_CNT'], -5)

    def test_valid_capabilities_string_values(self):
        """Test station capabilities with string values"""
        packet = "TEST>APRS:<NAME=TESTSTATION,VERSION=1.0"
        result = parse(packet)

        self.assertEqual(result['format'], 'station-capabilities')
        self.assertEqual(result['capabilities']['NAME'], 'TESTSTATION')
        # Numeric-looking values are converted to numbers
        self.assertEqual(result['capabilities']['VERSION'], 1.0)
        self.assertIsInstance(result['capabilities']['NAME'], str)
        self.assertIsInstance(result['capabilities']['VERSION'], float)

    def test_valid_capabilities_empty_body(self):
        """Test station capabilities with empty body"""
        packet = "TEST>APRS:<"
        result = parse(packet)

        self.assertEqual(result['format'], 'station-capabilities')
        self.assertEqual(result['capabilities'], {})

    def test_valid_capabilities_with_spaces(self):
        """Test station capabilities with spaces around commas"""
        packet = "TEST>APRS:<IGATE , MSG_CNT=123 , LOC_CNT=5"
        result = parse(packet)

        self.assertEqual(result['format'], 'station-capabilities')
        self.assertEqual(result['capabilities']['IGATE'], True)
        self.assertEqual(result['capabilities']['MSG_CNT'], 123)
        self.assertEqual(result['capabilities']['LOC_CNT'], 5)

    def test_valid_capabilities_empty_tokens_ignored(self):
        """Test that empty tokens between commas are ignored"""
        packet = "TEST>APRS:<IGATE,,MSG_CNT=123,,LOC_CNT=5"
        result = parse(packet)

        self.assertEqual(result['format'], 'station-capabilities')
        self.assertEqual(result['capabilities']['IGATE'], True)
        self.assertEqual(result['capabilities']['MSG_CNT'], 123)
        self.assertEqual(result['capabilities']['LOC_CNT'], 5)
        # Should not have empty string keys
        self.assertNotIn('', result['capabilities'])

    def test_valid_capabilities_complex_example(self):
        """Test complex real-world station capabilities example"""
        packet = "IGATE>APRS:<IGATE,MSG_CNT=1500,LOC_CNT=25,DIGI"
        result = parse(packet)

        self.assertEqual(result['format'], 'station-capabilities')
        self.assertEqual(result['from'], 'IGATE')
        self.assertEqual(result['capabilities']['IGATE'], True)
        self.assertEqual(result['capabilities']['MSG_CNT'], 1500)
        self.assertEqual(result['capabilities']['LOC_CNT'], 25)
        self.assertEqual(result['capabilities']['DIGI'], True)

    def test_valid_capabilities_multiple_equals_signs(self):
        """Test that values with multiple equals signs only split on first"""
        packet = "TEST>APRS:<KEY=value=with=equals"
        result = parse(packet)

        self.assertEqual(result['format'], 'station-capabilities')
        self.assertEqual(result['capabilities']['KEY'], 'value=with=equals')

    def test_valid_capabilities_numeric_strings(self):
        """Test that numeric strings are kept as strings when appropriate"""
        # Values that look like numbers but might be identifiers should stay as strings
        packet = "TEST>APRS:<VERSION=1.0.0,ID=001"
        result = parse(packet)

        self.assertEqual(result['format'], 'station-capabilities')
        # 1.0.0 should be a string (not a valid float)
        self.assertEqual(result['capabilities']['VERSION'], '1.0.0')
        # 001 should be an int (leading zeros preserved in string, but converted)
        self.assertEqual(result['capabilities']['ID'], 1)

    def test_parse_station_capabilities_function_direct(self):
        """Test parse_station_capabilities function directly"""
        body = "IGATE,MSG_CNT=123,LOC_CNT=5"
        remaining, result = parse_station_capabilities(body)

        self.assertEqual(remaining, '')
        self.assertEqual(result['format'], 'station-capabilities')
        self.assertEqual(result['capabilities']['IGATE'], True)
        self.assertEqual(result['capabilities']['MSG_CNT'], 123)
        self.assertEqual(result['capabilities']['LOC_CNT'], 5)

    def test_parse_station_capabilities_function_empty(self):
        """Test parse_station_capabilities function with empty body"""
        body = ""
        remaining, result = parse_station_capabilities(body)

        self.assertEqual(remaining, '')
        self.assertEqual(result['format'], 'station-capabilities')
        self.assertEqual(result['capabilities'], {})

    def test_station_capabilities_output_format(self):
        """Test that parsed station capabilities have correct output format"""
        packet = "TEST>APRS:<IGATE,MSG_CNT=123"
        result = parse(packet)

        # Check structure
        self.assertIn('format', result)
        self.assertIn('capabilities', result)
        self.assertEqual(result['format'], 'station-capabilities')

        # Check that capabilities is a dict
        self.assertIsInstance(result['capabilities'], dict)

        # Check that boolean tokens are True
        self.assertEqual(result['capabilities']['IGATE'], True)

        # Check that numeric values are numbers
        self.assertIsInstance(result['capabilities']['MSG_CNT'], (int, float))

    def test_station_capabilities_with_path(self):
        """Test station capabilities packet with path"""
        packet = "IGATE>APRS,WIDE1-1,WIDE2-2:<IGATE,MSG_CNT=100"
        result = parse(packet)

        self.assertEqual(result['format'], 'station-capabilities')
        self.assertEqual(result['from'], 'IGATE')
        self.assertEqual(result['to'], 'APRS')
        self.assertEqual(len(result['path']), 2)
        self.assertEqual(result['capabilities']['IGATE'], True)
        self.assertEqual(result['capabilities']['MSG_CNT'], 100)

    def test_station_capabilities_case_sensitive(self):
        """Test that capability names are case-sensitive"""
        packet = "TEST>APRS:<IGATE,igate,Msg_Cnt=123"
        result = parse(packet)

        self.assertEqual(result['format'], 'station-capabilities')
        # Should have separate entries for different cases
        self.assertEqual(result['capabilities']['IGATE'], True)
        self.assertEqual(result['capabilities']['igate'], True)
        self.assertEqual(result['capabilities']['Msg_Cnt'], 123)

    def test_station_capabilities_special_characters_in_values(self):
        """Test that special characters in values are preserved"""
        packet = "TEST>APRS:<NAME=Test-Station_1.0"
        result = parse(packet)

        self.assertEqual(result['format'], 'station-capabilities')
        self.assertEqual(result['capabilities']['NAME'], 'Test-Station_1.0')

    def test_station_capabilities_whitespace_trimmed(self):
        """Test that whitespace around tokens and values is trimmed"""
        packet = "TEST>APRS:<  IGATE  ,  MSG_CNT = 123  "
        result = parse(packet)

        self.assertEqual(result['format'], 'station-capabilities')
        self.assertEqual(result['capabilities']['IGATE'], True)
        self.assertEqual(result['capabilities']['MSG_CNT'], 123)


if __name__ == '__main__':
    unittest.main()
