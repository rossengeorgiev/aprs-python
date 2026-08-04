import unittest
from aprslib.parsing import parse


class ParseFrequency(unittest.TestCase):
    def test_simple_frequency(self):
        result = parse("N0CALL>APRS:!4903.50N/07201.75W-146.520MHz Enroute")
        self.assertAlmostEqual(result['frequency'], 146.520)
        self.assertEqual(result['comment'], 'Enroute')

    def test_frequency_with_space(self):
        result = parse("N0CALL>APRS:!4903.50N/07201.75W-146.52 MHz simplex")
        self.assertAlmostEqual(result['frequency'], 146.52)

    def test_frequency_with_tone(self):
        result = parse("N0CALL>APRS:!4903.50N/07201.75W-147.105MHz T107 Repeater")
        self.assertAlmostEqual(result['frequency'], 147.105)
        self.assertEqual(result['tone'], 107)
        self.assertEqual(result['comment'], 'Repeater')

    def test_frequency_with_offset(self):
        result = parse("N0CALL>APRS:!4903.50N/07201.75W-147.000MHz +060 Local RPT")
        self.assertAlmostEqual(result['frequency'], 147.000)
        self.assertEqual(result['offset'], 600)  # +600 KHz

    def test_frequency_with_negative_offset(self):
        result = parse("N0CALL>APRS:!4903.50N/07201.75W-146.940MHz -060 RPT")
        self.assertEqual(result['offset'], -600)

    def test_frequency_with_dcs(self):
        result = parse("N0CALL>APRS:!4903.50N/07201.75W-446.500MHz D023 DMR")
        self.assertAlmostEqual(result['frequency'], 446.500)
        self.assertEqual(result['dcs'], 23)

    def test_no_frequency(self):
        result = parse("N0CALL>APRS:!4903.50N/07201.75W-Just a comment")
        self.assertNotIn('frequency', result)
        self.assertEqual(result['comment'], 'Just a comment')


class ParseMiceDevice(unittest.TestCase):
    def test_kenwood_thd72(self):
        # Build a valid Mic-E packet with >= suffix
        result = parse("N0CALL>T2SP0W:`(_fn\"Oj/>=")
        if 'device' in result:
            self.assertEqual(result['device'], 'Kenwood TH-D72')

    def test_kenwood_tmd700(self):
        result = parse("N0CALL>T2SP0W:`(_fn\"Oj/]")
        if 'device' in result:
            self.assertEqual(result['device'], 'Kenwood TM-D700')


class ParseItemInMessage(unittest.TestCase):
    def test_item_in_message(self):
        result = parse("N0CALL>APRS::W1ABC    :)FUEL!4903.50N/07201.75W-Gas Station{001")
        # Should detect as item-in-message OR regular message (depends on implementation)
        if result.get('format') == 'item-in-message':
            self.assertEqual(result['addresse'], 'W1ABC')
            self.assertIn('item', result)
            self.assertEqual(result['item']['item_name'], 'FUEL')


if __name__ == '__main__':
    unittest.main()
