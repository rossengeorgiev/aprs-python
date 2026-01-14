import unittest

from aprslib import parse
from aprslib.exceptions import ParseError


class ParseItemReport(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_valid_item_basic(self):
        """Test basic item report with live item"""
        packet = "TEST>APRS:)AIDV#2!4903.50N/07201.75WA"
        result = parse(packet)

        self.assertEqual(result['format'], 'item')
        self.assertEqual(result['item_name'], 'AIDV#2')
        self.assertTrue(result['alive'])
        self.assertEqual(result['item_format'], 'uncompressed')
        self.assertEqual(result['latitude'], 49.05833333333333)
        self.assertEqual(result['longitude'], -72.02916666666667)
        self.assertEqual(result['symbol'], 'A')
        self.assertEqual(result['symbol_table'], '/')

    def test_valid_item_kill(self):
        """Test item report with kill indicator"""
        packet = "TEST>APRS:)AIDV#2_4903.50N/07201.75WA"
        result = parse(packet)

        self.assertEqual(result['format'], 'item')
        self.assertEqual(result['item_name'], 'AIDV#2')
        self.assertFalse(result['alive'])
        self.assertEqual(result['latitude'], 49.05833333333333)
        self.assertEqual(result['longitude'], -72.02916666666667)

    def test_valid_item_short_name(self):
        """Test item report with short name (3 characters)"""
        packet = "TEST>APRS:)ABC!4903.50N/07201.75WA"
        result = parse(packet)

        self.assertEqual(result['format'], 'item')
        self.assertEqual(result['item_name'], 'ABC')
        self.assertTrue(result['alive'])

    def test_valid_item_long_name(self):
        """Test item report with long name (9 characters)"""
        packet = "TEST>APRS:)ABCDEFGHI!4903.50N/07201.75WA"
        result = parse(packet)

        self.assertEqual(result['format'], 'item')
        self.assertEqual(result['item_name'], 'ABCDEFGHI')
        self.assertTrue(result['alive'])

    def test_valid_item_with_comment(self):
        """Test item report with comment"""
        packet = "TEST>APRS:)AIDV#2!4903.50N/07201.75WAComment text"
        result = parse(packet)

        self.assertEqual(result['format'], 'item')
        self.assertEqual(result['item_name'], 'AIDV#2')
        self.assertEqual(result['comment'], 'Comment text')

    def test_valid_item_with_timestamp(self):
        """Test item report with timestamp"""
        packet = "TEST>APRS:)AIDV#2!092345z4903.50N/07201.75WA"
        result = parse(packet)

        self.assertEqual(result['format'], 'item')
        self.assertEqual(result['item_name'], 'AIDV#2')
        self.assertIn('timestamp', result)
        self.assertIn('raw_timestamp', result)

    def test_valid_item_compressed_position(self):
        """Test item report with compressed position"""
        packet = "TEST>APRS:)AIDV#2!/5L!!<*e7>7P["
        result = parse(packet)

        self.assertEqual(result['format'], 'item')
        self.assertEqual(result['item_name'], 'AIDV#2')
        self.assertEqual(result['item_format'], 'compressed')
        self.assertIn('latitude', result)
        self.assertIn('longitude', result)

    def test_valid_item_special_characters_in_name(self):
        """Test item report with special characters in name"""
        packet = "TEST>APRS:)AID#2!4903.50N/07201.75WA"
        result = parse(packet)

        self.assertEqual(result['format'], 'item')
        self.assertEqual(result['item_name'], 'AID#2')
        self.assertTrue(result['alive'])

    def test_valid_item_different_symbol(self):
        """Test item report with different symbol"""
        packet = "TEST>APRS:)AIDV#2!4903.50N/07201.75W-"
        result = parse(packet)

        self.assertEqual(result['format'], 'item')
        self.assertEqual(result['item_name'], 'AIDV#2')
        self.assertEqual(result['symbol'], '-')
        self.assertEqual(result['symbol_table'], '/')

    def test_valid_item_with_data_extensions(self):
        """Test item report with data extensions"""
        packet = "TEST>APRS:)AIDV#2!4903.50N/07201.75WA090/001"
        result = parse(packet)

        self.assertEqual(result['format'], 'item')
        self.assertEqual(result['item_name'], 'AIDV#2')
        self.assertIn('course', result)
        self.assertIn('speed', result)

    def test_invalid_item_too_short_name(self):
        """Test that item name shorter than 3 characters raises error"""
        packet = "TEST>APRS:)AB!4903.50N/07201.75WA"

        with self.assertRaises(ParseError) as context:
            parse(packet)

        self.assertIn("invalid item report format", str(context.exception))

    def test_invalid_item_too_long_name(self):
        """Test that item name longer than 9 characters raises error"""
        packet = "TEST>APRS:)ABCDEFGHIJ!4903.50N/07201.75WA"

        with self.assertRaises(ParseError) as context:
            parse(packet)

        self.assertIn("invalid item report format", str(context.exception))

    def test_invalid_item_missing_flag(self):
        """Test that item report without ! or _ flag raises error"""
        packet = "TEST>APRS:)AIDV#24903.50N/07201.75WA"

        with self.assertRaises(ParseError) as context:
            parse(packet)

        self.assertIn("invalid item report format", str(context.exception))

    def test_invalid_item_wrong_flag(self):
        """Test that item report with wrong flag character raises error"""
        packet = "TEST>APRS:)AIDV#2*4903.50N/07201.75WA"

        with self.assertRaises(ParseError) as context:
            parse(packet)

        self.assertIn("invalid item report format", str(context.exception))

    def test_item_output_format(self):
        """Test that parsed item report has correct output format"""
        packet = "TEST>APRS:)AIDV#2!4903.50N/07201.75WAComment"
        result = parse(packet)

        # Check structure
        self.assertIn('format', result)
        self.assertEqual(result['format'], 'item')
        self.assertIn('item_name', result)
        self.assertIn('alive', result)
        self.assertIn('item_format', result)
        self.assertIn('latitude', result)
        self.assertIn('longitude', result)
        self.assertIn('symbol', result)
        self.assertIn('symbol_table', result)

        # Check types
        self.assertIsInstance(result['item_name'], str)
        self.assertIsInstance(result['alive'], bool)
        self.assertIsInstance(result['latitude'], (int, float))
        self.assertIsInstance(result['longitude'], (int, float))

    def test_item_vs_object_difference(self):
        """Test that item reports are different from object reports"""
        item_packet = "TEST>APRS:)AIDV#2!4903.50N/07201.75WA"
        # Object reports require exactly 9 characters for name
        object_packet = "TEST>APRS:;AIDV#2   *4903.50N/07201.75WA"

        item_result = parse(item_packet)
        object_result = parse(object_packet)

        self.assertEqual(item_result['format'], 'item')
        self.assertEqual(object_result['format'], 'object')
        self.assertIn('item_name', item_result)
        self.assertIn('object_name', object_result)
        self.assertEqual(item_result['item_name'], 'AIDV#2')
        self.assertEqual(object_result['object_name'], 'AIDV#2   ')

    def test_item_with_path(self):
        """Test item report packet with path"""
        packet = "TEST>APRS,WIDE1-1,WIDE2-2:)AIDV#2!4903.50N/07201.75WA"
        result = parse(packet)

        self.assertEqual(result['format'], 'item')
        self.assertEqual(result['from'], 'TEST')
        self.assertEqual(result['to'], 'APRS')
        self.assertEqual(len(result['path']), 2)
        self.assertEqual(result['item_name'], 'AIDV#2')

    def test_item_kill_vs_live(self):
        """Test that kill and live items are correctly identified"""
        live_packet = "TEST>APRS:)AIDV#2!4903.50N/07201.75WA"
        kill_packet = "TEST>APRS:)AIDV#2_4903.50N/07201.75WA"

        live_result = parse(live_packet)
        kill_result = parse(kill_packet)

        self.assertTrue(live_result['alive'])
        self.assertFalse(kill_result['alive'])
        self.assertEqual(live_result['item_name'], kill_result['item_name'])

    def test_item_with_space_in_name(self):
        """Test item report with space in item name (real-world packet)"""
        packet = "KL7BX-10>APWW11,TCPIP*,qAC,T2LANE:)MARC VHF2!3222.60N/09438.49WrPHG5360 Marshall ARC Rptr2  Analog 145.300MHz -600kHz Tn146.2  !w^t!"
        result = parse(packet)

        self.assertEqual(result['format'], 'item')
        self.assertEqual(result['item_name'], 'MARC VHF2')
        self.assertEqual(result['alive'], True)
        self.assertIn('latitude', result)
        self.assertIn('longitude', result)

    def test_item_with_all_spaces_name(self):
        """Test item report with all spaces as item name (real-world packet)"""
        packet = "JH9XXF-E>API705,DSTAR*,qAS,JP9YEH-IS:)   !0000.00N\\00000.00E>/"
        result = parse(packet)

        self.assertEqual(result['format'], 'item')
        self.assertEqual(result['item_name'], '   ')  # 3 spaces
        self.assertEqual(len(result['item_name']), 3)
        self.assertEqual(result['alive'], True)
        self.assertIn('latitude', result)
        self.assertIn('longitude', result)


if __name__ == '__main__':
    unittest.main()
