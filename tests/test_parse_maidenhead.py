import unittest
from aprslib.parsing import parse
from aprslib.parsing.misc import parse_maidenhead_locator
from aprslib.exceptions import ParseError


class ParseMaidenheadLocator(unittest.TestCase):
    """Test suite for APRS maidenhead locator beacon parsing"""

    def test_valid_4_char_locator(self):
        """Test 4-character maidenhead locator (field + square)"""
        packet = "TEST>APRS:[FN31]"
        result = parse(packet)

        self.assertEqual(result['format'], 'maidenhead-locator')
        self.assertEqual(result['locator'], 'FN31')
        self.assertEqual(result['locator_precision'], 4)

    def test_valid_6_char_locator(self):
        """Test 6-character maidenhead locator (field + square + subsquare)"""
        packet = "TEST>APRS:[IO91SX]"
        result = parse(packet)

        self.assertEqual(result['format'], 'maidenhead-locator')
        self.assertEqual(result['locator'], 'IO91SX')
        self.assertEqual(result['locator_precision'], 6)

    def test_valid_8_char_locator(self):
        """Test 8-character maidenhead locator (field + square + subsquare + extended)"""
        packet = "TEST>APRS:[FN31pr45]"
        result = parse(packet)

        self.assertEqual(result['format'], 'maidenhead-locator')
        self.assertEqual(result['locator'], 'FN31PR45')
        self.assertEqual(result['locator_precision'], 8)

    def test_locator_with_symbol(self):
        """Test locator with symbol table and symbol"""
        packet = "TEST>APRS:[IO91SX/-]"
        result = parse(packet)

        self.assertEqual(result['format'], 'maidenhead-locator')
        self.assertEqual(result['locator'], 'IO91SX')
        self.assertEqual(result['locator_precision'], 6)
        self.assertEqual(result['symbol_table'], '/')
        self.assertEqual(result['symbol'], '-')

    def test_locator_with_comment(self):
        """Test locator with comment"""
        packet = "TEST>APRS:[IO91SX]Test comment"
        result = parse(packet)

        self.assertEqual(result['format'], 'maidenhead-locator')
        self.assertEqual(result['locator'], 'IO91SX')
        self.assertEqual(result['comment'], 'Test comment')

    def test_locator_with_symbol_and_comment(self):
        """Test locator with symbol and comment"""
        packet = "TEST>APRS:[IO91SX/-]Test comment"
        result = parse(packet)

        self.assertEqual(result['format'], 'maidenhead-locator')
        self.assertEqual(result['locator'], 'IO91SX')
        self.assertEqual(result['symbol_table'], '/')
        self.assertEqual(result['symbol'], '-')
        self.assertEqual(result['comment'], 'Test comment')

    def test_locator_with_slash_in_comment(self):
        """Test locator where / is part of comment, not symbol table"""
        packet = "TEST>APRS:[FN31pr/Test comment]"
        result = parse(packet)

        self.assertEqual(result['format'], 'maidenhead-locator')
        self.assertEqual(result['locator'], 'FN31PR')
        self.assertNotIn('symbol', result)
        self.assertEqual(result['comment'], '/Test comment')

    def test_locator_case_insensitive(self):
        """Test that locator letters are case-insensitive and normalized to uppercase"""
        packet = "TEST>APRS:[io91sx]"
        result = parse(packet)

        self.assertEqual(result['locator'], 'IO91SX')
        self.assertEqual(result['locator_precision'], 6)

    def test_locator_mixed_case(self):
        """Test locator with mixed case letters"""
        packet = "TEST>APRS:[Fn31Pr]"
        result = parse(packet)

        self.assertEqual(result['locator'], 'FN31PR')
        self.assertEqual(result['locator_precision'], 6)

    def test_locator_with_backslash_symbol_table(self):
        """Test locator with backslash symbol table"""
        packet = "TEST>APRS:[IO91SX\\-]"
        result = parse(packet)

        self.assertEqual(result['format'], 'maidenhead-locator')
        self.assertEqual(result['locator'], 'IO91SX')
        self.assertEqual(result['symbol_table'], '\\')
        self.assertEqual(result['symbol'], '-')

    def test_locator_no_closing_bracket(self):
        """Test locator without closing bracket"""
        packet = "TEST>APRS:[IO91SX"
        result = parse(packet)

        self.assertEqual(result['format'], 'maidenhead-locator')
        self.assertEqual(result['locator'], 'IO91SX')

    def test_locator_empty_body(self):
        """Test locator with empty body"""
        packet = "TEST>APRS:["
        result = parse(packet)

        self.assertEqual(result['format'], 'maidenhead-locator')
        self.assertNotIn('locator', result)

    def test_invalid_locator_too_short(self):
        """Test that invalid locator (too short) raises error"""
        packet = "TEST>APRS:[FN3]"

        with self.assertRaises(ParseError) as context:
            parse(packet)

        self.assertIn("invalid maidenhead locator format", str(context.exception))

    def test_invalid_locator_wrong_format(self):
        """Test that invalid locator format raises error"""
        packet = "TEST>APRS:[1234]"

        with self.assertRaises(ParseError) as context:
            parse(packet)

        self.assertIn("invalid maidenhead locator format", str(context.exception))

    def test_invalid_locator_letters_out_of_range(self):
        """Test that locator with letters outside A-R range raises error"""
        packet = "TEST>APRS:[ZZ31]"

        with self.assertRaises(ParseError) as context:
            parse(packet)

        self.assertIn("invalid maidenhead locator format", str(context.exception))

    def test_parse_maidenhead_locator_function_direct(self):
        """Test parse_maidenhead_locator function directly"""
        body = "IO91SX/-]Comment"
        remaining, result = parse_maidenhead_locator(body)

        self.assertEqual(remaining, '')
        self.assertEqual(result['format'], 'maidenhead-locator')
        self.assertEqual(result['locator'], 'IO91SX')
        self.assertEqual(result['locator_precision'], 6)
        self.assertEqual(result['symbol_table'], '/')
        self.assertEqual(result['symbol'], '-')
        self.assertEqual(result['comment'], 'Comment')

    def test_parse_maidenhead_locator_4_char_direct(self):
        """Test parse_maidenhead_locator function with 4-char locator"""
        body = "FN31]"
        remaining, result = parse_maidenhead_locator(body)

        self.assertEqual(remaining, '')
        self.assertEqual(result['format'], 'maidenhead-locator')
        self.assertEqual(result['locator'], 'FN31')
        self.assertEqual(result['locator_precision'], 4)

    def test_parse_maidenhead_locator_8_char_direct(self):
        """Test parse_maidenhead_locator function with 8-char locator"""
        body = "FN31pr45]"
        remaining, result = parse_maidenhead_locator(body)

        self.assertEqual(remaining, '')
        self.assertEqual(result['format'], 'maidenhead-locator')
        self.assertEqual(result['locator'], 'FN31PR45')
        self.assertEqual(result['locator_precision'], 8)

    def test_locator_with_symbol_only_no_comment(self):
        """Test locator with symbol but no comment"""
        packet = "TEST>APRS:[IO91SX/-]"
        result = parse(packet)

        self.assertEqual(result['format'], 'maidenhead-locator')
        self.assertEqual(result['locator'], 'IO91SX')
        self.assertEqual(result['symbol_table'], '/')
        self.assertEqual(result['symbol'], '-')
        self.assertNotIn('comment', result)

    def test_locator_with_trailing_bracket_in_comment(self):
        """Test locator where closing bracket appears in comment"""
        packet = "TEST>APRS:[IO91SX/- Test]"
        result = parse(packet)

        self.assertEqual(result['format'], 'maidenhead-locator')
        self.assertEqual(result['locator'], 'IO91SX')
        self.assertEqual(result['symbol_table'], '/')
        self.assertEqual(result['symbol'], '-')
        self.assertEqual(result['comment'], 'Test')

    def test_real_world_winlink_packet(self):
        """Test real-world packet from error log: WinLink RMS Packet Node"""
        packet = "J73GPG-10>WL2K,STSHD,WIDE2*,qAR,J73Z-10:[FK95HI] J73GPG-10 WinLink RMS Packet Node"
        result = parse(packet)

        self.assertEqual(result['format'], 'maidenhead-locator')
        self.assertEqual(result['locator'], 'FK95HI')
        self.assertEqual(result['locator_precision'], 6)
        self.assertEqual(result['comment'], 'J73GPG-10 WinLink RMS Packet Node')
        # Verify header parsing
        self.assertEqual(result['from'], 'J73GPG-10')
        self.assertEqual(result['to'], 'WL2K')


if __name__ == '__main__':
    unittest.main()
