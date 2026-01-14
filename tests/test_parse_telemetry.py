import unittest

from aprslib import parse
from aprslib.parsing.telemetry import parse_telemetry_report
from aprslib.exceptions import ParseError


class ParseTelemetryReport(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_valid_telemetry_basic(self):
        """Test basic valid telemetry packet with integers"""
        packet = "TESTCALL>APRS:T#123,456,789,012,345,678,11001010"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry')
        self.assertEqual(result['telemetry']['seq'], 123)
        self.assertEqual(result['telemetry']['vals'], [456, 789, 12, 345, 678])
        self.assertEqual(result['telemetry']['bits'], '11001010')
        self.assertNotIn('comment', result)

    def test_valid_telemetry_with_comment(self):
        """Test telemetry packet with comment"""
        packet = "TESTCALL>APRS:T#123,456,789,012,345,678,11001010,Test comment"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry')
        self.assertEqual(result['telemetry']['seq'], 123)
        self.assertEqual(result['telemetry']['vals'], [456, 789, 12, 345, 678])
        self.assertEqual(result['telemetry']['bits'], '11001010')
        self.assertEqual(result['comment'], 'Test comment')

    def test_valid_telemetry_with_decimal_values(self):
        """Test telemetry packet with decimal analog values (APRS 1.2)"""
        packet = "EL-PS7AD>RXTLM-1,TCPIP,qAR,PS7AD:T#121,0.00,0.00,0,0,0.0,00000000,SimplexLogic"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry')
        self.assertEqual(result['from'], 'EL-PS7AD')
        self.assertEqual(result['to'], 'RXTLM-1')
        self.assertEqual(result['telemetry']['seq'], 121)
        self.assertEqual(result['telemetry']['vals'], [0.0, 0.0, 0.0, 0.0, 0.0])
        self.assertEqual(result['telemetry']['bits'], '00000000')
        self.assertEqual(result['comment'], 'SimplexLogic')

    def test_valid_telemetry_with_negative_values(self):
        """Test telemetry packet with negative analog values"""
        packet = "TEST>APRS:T#123,-45.67,123.456,999,0,0.0,11111111"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry')
        self.assertEqual(result['telemetry']['seq'], 123)
        self.assertEqual(result['telemetry']['vals'], [-45.67, 123.456, 999.0, 0.0, 0.0])
        self.assertEqual(result['telemetry']['bits'], '11111111')

    def test_valid_telemetry_mixed_integer_decimal(self):
        """Test telemetry packet with mix of integer and decimal values"""
        packet = "TEST>APRS:T#001,100,200.5,300,400.25,500,01010101"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry')
        self.assertEqual(result['telemetry']['seq'], 1)
        self.assertEqual(result['telemetry']['vals'], [100.0, 200.5, 300.0, 400.25, 500.0])
        self.assertEqual(result['telemetry']['bits'], '01010101')

    def test_valid_telemetry_min_values(self):
        """Test telemetry packet with minimum values"""
        packet = "TEST>APRS:T#000,0,0,0,0,0,00000000"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry')
        self.assertEqual(result['telemetry']['seq'], 0)
        self.assertEqual(result['telemetry']['vals'], [0.0, 0.0, 0.0, 0.0, 0.0])
        self.assertEqual(result['telemetry']['bits'], '00000000')

    def test_valid_telemetry_max_values(self):
        """Test telemetry packet with maximum sequence number"""
        packet = "TEST>APRS:T#999,999,999,999,999,999,11111111"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry')
        self.assertEqual(result['telemetry']['seq'], 999)
        self.assertEqual(result['telemetry']['vals'], [999.0, 999.0, 999.0, 999.0, 999.0])
        self.assertEqual(result['telemetry']['bits'], '11111111')

    def test_valid_telemetry_comment_with_commas(self):
        """Test telemetry packet with comment containing commas"""
        packet = "TEST>APRS:T#123,456,789,012,345,678,11001010,Comment with, commas"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry')
        self.assertEqual(result['comment'], 'Comment with, commas')

    def test_valid_telemetry_comment_without_comma_separator(self):
        """Test telemetry packet with comment concatenated without comma separator"""
        packet = "VK2RAY>APRS,TCPIP*,qAC,T2SYDNEY:T#195,094,030,105,119,119,00000000VK3ERW aprslog"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry')
        self.assertEqual(result['telemetry']['seq'], 195)
        self.assertEqual(result['telemetry']['bits'], '00000000')
        self.assertEqual(result['comment'], 'VK3ERW aprslog')

    def test_valid_telemetry_incomplete_packet(self):
        """Test telemetry packet with incomplete data (real-world case)"""
        packet = "TF3IRA-1>APDW17,TCPIP*,qAC,T2CSNGRAD:T#749,45084"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry')
        self.assertEqual(result['telemetry']['seq'], 749)
        # Only one analog value provided, rest should be padded with 0
        self.assertEqual(result['telemetry']['vals'], [45084.0, 0.0, 0.0, 0.0, 0.0])
        # Digital I/O should default to all zeros
        self.assertEqual(result['telemetry']['bits'], '00000000')

    def test_valid_telemetry_minimal_packet(self):
        """Test telemetry packet with only sequence number"""
        packet = "TEST>APRS:T#123"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry')
        self.assertEqual(result['telemetry']['seq'], 123)
        # All analog values should be 0
        self.assertEqual(result['telemetry']['vals'], [0.0, 0.0, 0.0, 0.0, 0.0])
        # Digital I/O should default to all zeros
        self.assertEqual(result['telemetry']['bits'], '00000000')

    def test_valid_telemetry_missing_digital_with_binary_in_next(self):
        """Test telemetry packet with missing digital I/O field, binary digits in next position"""
        packet = "E25HML-13>APRS,TCPIP*,qAC,T2PERTH:T#075,039,,,000,000,,0000,ESP8266 Test WX DHT22 version"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry')
        self.assertEqual(result['telemetry']['seq'], 75)
        self.assertEqual(result['telemetry']['vals'], [39.0, 0.0, 0.0, 0.0, 0.0])
        # 0000 should be padded to 8 digits
        self.assertEqual(result['telemetry']['bits'], '00000000')
        self.assertEqual(result['comment'], 'ESP8266 Test WX DHT22 version')

    def test_valid_telemetry_empty_analog_value(self):
        """Test telemetry packet with empty analog value"""
        packet = "VU2IB-13>APRS,TCPIP*,qAC,T2DENMARK:T#126,250,057,000,040,,1011,Solar Power WX Station"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry')
        self.assertEqual(result['telemetry']['seq'], 126)
        self.assertEqual(result['telemetry']['vals'], [250.0, 57.0, 0.0, 40.0, 0.0])
        # Short binary string should be padded to 8 digits
        self.assertEqual(result['telemetry']['bits'], '00001011')
        self.assertEqual(result['comment'], 'Solar Power WX Station')

    def test_valid_telemetry_short_binary_string(self):
        """Test telemetry packet with short binary string (less than 8 digits)"""
        packet = "TEST>APRS:T#123,456,789,012,345,678,101,Comment"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry')
        # Short binary should be padded with leading zeros
        self.assertEqual(result['telemetry']['bits'], '00000101')
        self.assertEqual(result['comment'], 'Comment')

    def test_valid_telemetry_all_bits_set(self):
        """Test telemetry packet with all digital bits set"""
        packet = "TEST>APRS:T#123,456,789,012,345,678,11111111"
        result = parse(packet)

        self.assertEqual(result['telemetry']['bits'], '11111111')

    def test_valid_telemetry_no_bits_set(self):
        """Test telemetry packet with no digital bits set"""
        packet = "TEST>APRS:T#123,456,789,012,345,678,00000000"
        result = parse(packet)

        self.assertEqual(result['telemetry']['bits'], '00000000')

    def test_valid_telemetry_leading_zeros(self):
        """Test telemetry packet with leading zeros in sequence and values"""
        packet = "TEST>APRS:T#001,002,003,004,005,006,11001010"
        result = parse(packet)

        self.assertEqual(result['telemetry']['seq'], 1)
        self.assertEqual(result['telemetry']['vals'], [2.0, 3.0, 4.0, 5.0, 6.0])

    def test_invalid_telemetry_missing_hash(self):
        """Test that telemetry packet without '#' raises error"""
        packet = "TEST>APRS:T123,456,789,012,345,678,11001010"

        with self.assertRaises(ParseError) as context:
            parse(packet)

        self.assertIn("telemetry report must start with '#'", str(context.exception))

    def test_valid_telemetry_few_fields(self):
        """Test that telemetry packet with few fields is accepted (incomplete packets)"""
        packet = "TEST>APRS:T#123,456"
        result = parse(packet)

        # Incomplete packets are now accepted with padding
        self.assertEqual(result['format'], 'telemetry')
        self.assertEqual(result['telemetry']['seq'], 123)
        self.assertEqual(result['telemetry']['vals'], [456.0, 0.0, 0.0, 0.0, 0.0])
        self.assertEqual(result['telemetry']['bits'], '00000000')

    def test_invalid_telemetry_invalid_sequence(self):
        """Test that invalid sequence number raises error"""
        packet = "TEST>APRS:T#abc,456,789,012,345,678,11001010"

        with self.assertRaises(ParseError) as context:
            parse(packet)

        self.assertIn("telemetry sequence number must be numeric", str(context.exception))

    def test_valid_telemetry_large_sequence_number(self):
        """Test that large sequence numbers are accepted (real-world packets)"""
        packet = "TEST>APRS:T#1814,1,0,0,71,4.88,00000000"
        result = parse(packet)

        # Large sequence numbers are now accepted
        self.assertEqual(result['format'], 'telemetry')
        self.assertEqual(result['telemetry']['seq'], 1814)

    def test_invalid_telemetry_sequence_range_check(self):
        """Test that sequence number range validation works (999 is max)"""
        # Test that 999 is valid (boundary case)
        packet = "TEST>APRS:T#999,456,789,012,345,678,11001010"
        result = parse(packet)
        self.assertEqual(result['telemetry']['seq'], 999)

    def test_invalid_telemetry_invalid_analog_value(self):
        """Test that invalid analog value raises error"""
        packet = "TEST>APRS:T#123,abc,789,012,345,678,11001010"

        with self.assertRaises(ParseError) as context:
            parse(packet)

        self.assertIn("telemetry analog value", str(context.exception))
        self.assertIn("invalid format", str(context.exception))

    def test_invalid_telemetry_invalid_digital_bits(self):
        """Test that digital I/O with no binary digits raises error"""
        packet = "TEST>APRS:T#123,456,789,012,345,678,123"

        with self.assertRaises(ParseError) as context:
            parse(packet)

        self.assertIn("telemetry digital I/O must be binary digits", str(context.exception))

    def test_valid_telemetry_digital_bits_short_length(self):
        """Test that digital I/O with short length is padded (real-world packets)"""
        packet = "TEST>APRS:T#123,456,789,012,345,678,1100101"
        result = parse(packet)

        # Short binary strings are padded with leading zeros
        self.assertEqual(result['telemetry']['bits'], '01100101')

    def test_valid_telemetry_digital_bits_with_non_binary_suffix(self):
        """Test that digital I/O with leading binary digits and non-binary suffix is handled (real-world packets)"""
        packet = "TEST>APRS:T#123,456,789,012,345,678,11001012"
        result = parse(packet)

        # Should extract leading binary digits (7 digits), pad to 8, and treat '2' as comment
        self.assertEqual(result['telemetry']['bits'], '01100101')
        self.assertEqual(result.get('comment', ''), '2')

    def test_valid_telemetry_leading_decimal_analog_value(self):
        """Test telemetry packet with leading decimal in analog value (e.g., .10 = 0.10)"""
        packet = "IT9FDP-15>APRTLM,TCPIP*,qAC,T2CZECH:T#720,.10,12.83,12.19,14.0,14.8,00000000"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry')
        self.assertEqual(result['telemetry']['seq'], 720)
        # .10 should be parsed as 0.1
        self.assertEqual(result['telemetry']['vals'], [0.1, 12.83, 12.19, 14.0, 14.8])
        self.assertEqual(result['telemetry']['bits'], '00000000')

    def test_valid_telemetry_analog_value_with_data_extension(self):
        """Test telemetry packet with data extension concatenated to analog value (real-world packet)"""
        packet = "IZ1DNG-10>WIDE1-1,WIDE2-2,qAR,IR1UFB:T#8,205,114,170,115,0>/A=9125"
        result = parse(packet)

        self.assertEqual(result['format'], 'telemetry')
        self.assertEqual(result['telemetry']['seq'], 8)
        # Analog value 5 is "0>/A=9125" - should extract "0" and preserve "/A=9125" in comment
        self.assertEqual(result['telemetry']['vals'], [205.0, 114.0, 170.0, 115.0, 0.0])
        self.assertEqual(result['telemetry']['bits'], '00000000')
        # The data extension should be preserved in comment
        self.assertIn('comment', result)
        self.assertIn('/A=9125', result['comment'])

    def test_parse_telemetry_report_function_direct(self):
        """Test parse_telemetry_report function directly"""
        body = "#123,456,789,012,345,678,11001010,Test"
        remaining, result = parse_telemetry_report(body)

        self.assertEqual(remaining, '')
        self.assertEqual(result['format'], 'telemetry')
        self.assertEqual(result['telemetry']['seq'], 123)
        self.assertEqual(result['telemetry']['vals'], [456, 789, 12, 345, 678])
        self.assertEqual(result['telemetry']['bits'], '11001010')
        self.assertEqual(result['comment'], 'Test')

    def test_parse_telemetry_report_function_no_hash(self):
        """Test parse_telemetry_report function with body not starting with '#'"""
        body = "123,456,789,012,345,678,11001010"

        with self.assertRaises(ParseError) as context:
            parse_telemetry_report(body)

        self.assertIn("telemetry report must start with '#'", str(context.exception))

    def test_telemetry_output_format(self):
        """Test that parsed telemetry has correct output format"""
        packet = "TEST>APRS:T#123,456,789,012,345,678,11001010,Comment"
        result = parse(packet)

        # Check structure
        self.assertIn('format', result)
        self.assertIn('telemetry', result)
        self.assertIn('seq', result['telemetry'])
        self.assertIn('vals', result['telemetry'])
        self.assertIn('bits', result['telemetry'])

        # Check types
        self.assertIsInstance(result['telemetry']['seq'], int)
        self.assertIsInstance(result['telemetry']['vals'], list)
        self.assertEqual(len(result['telemetry']['vals']), 5)
        self.assertIsInstance(result['telemetry']['bits'], str)
        self.assertEqual(len(result['telemetry']['bits']), 8)

        # Check that all vals are numbers (int or float)
        for val in result['telemetry']['vals']:
            self.assertIsInstance(val, (int, float))

        # Check that bits are binary
        self.assertTrue(all(c in '01' for c in result['telemetry']['bits']))


if __name__ == '__main__':
    unittest.main()
