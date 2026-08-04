"""Tests for GPGLL coordinate extraction, broken Mic-E fixup, and comment cleanup."""
import unittest
import aprslib
from aprslib.parsing.mice import _fix_broken_mice


class GpgllTest(unittest.TestCase):
    """Test GPGLL full coordinate extraction."""

    def test_gpgll_basic(self):
        """GPGLL sentence extracts lat/lon."""
        # $GPGLL,4916.45,N,12311.12,W,225444,A
        packet = "N0CALL>APRS:$GPGLL,4916.45,N,12311.12,W,225444,A"
        result = aprslib.parse(packet)
        self.assertAlmostEqual(result['latitude'], 49.274167, places=4)
        self.assertAlmostEqual(result['longitude'], -123.1853, places=3)
        self.assertEqual(result['nmea_time'], '225444')
        self.assertEqual(result['gps_status'], 'A')

    def test_gpgll_southern_hemisphere(self):
        """GPGLL with South and East coordinates."""
        packet = "N0CALL>APRS:$GPGLL,3345.00,S,15130.00,E,120000,A"
        result = aprslib.parse(packet)
        self.assertAlmostEqual(result['latitude'], -33.75, places=4)
        self.assertAlmostEqual(result['longitude'], 151.5, places=4)

    def test_gpgll_no_time(self):
        """GPGLL without time field still extracts coordinates."""
        packet = "N0CALL>APRS:$GPGLL,4916.45,N,12311.12,W"
        result = aprslib.parse(packet)
        self.assertAlmostEqual(result['latitude'], 49.274167, places=4)
        self.assertNotIn('nmea_time', result)

    def test_gpgll_with_checksum(self):
        """GPGLL with checksum validates correctly."""
        # Compute valid checksum
        sentence = "GPGLL,4916.45,N,12311.12,W,225444,A"
        checksum = 0
        for c in sentence:
            checksum ^= ord(c)
        body = sentence + "*" + format(checksum, '02X')
        packet = "N0CALL>APRS:$" + body
        result = aprslib.parse(packet)
        self.assertTrue(result.get('nmea_checksum_ok'))
        self.assertAlmostEqual(result['latitude'], 49.274167, places=4)


class BrokenMiceTest(unittest.TestCase):
    """Test broken Mic-E fixup."""

    def test_fix_broken_mice_spaces_in_pos01(self):
        """Spaces in positions 0-1 are replaced with '&'."""
        # Normal mic-e body starts with chars >= 0x26
        body = " (L!l>/>"  # space at pos 0 (below 0x26)
        fixed = _fix_broken_mice(body)
        self.assertIsNotNone(fixed)
        self.assertEqual(fixed[0], '&')  # replaced

    def test_fix_returns_none_short(self):
        """Too-short body returns None."""
        self.assertIsNone(_fix_broken_mice("abc"))
        self.assertIsNone(_fix_broken_mice(""))
        self.assertIsNone(_fix_broken_mice(None))

    def test_valid_mice_not_broken(self):
        """Valid Mic-E packet doesn't trigger fixup."""
        # This is a valid mic-e format string (won't fail the regex)
        # So parse_mice should not set mice_fixed
        packet = "N0CALL>T2SP0W:`(_fn\"Oj/>"
        result = aprslib.parse(packet)
        self.assertEqual(result['format'], 'mic-e')
        self.assertNotIn('mice_fixed', result)


class CommentCleanupTest(unittest.TestCase):
    """Test comment control character cleanup."""

    def test_control_chars_stripped(self):
        """Control characters are removed from comments."""
        # Position report with control chars in comment
        packet = "N0CALL>APRS:!4903.50N/07201.75W-test\x01\x02\x03end"
        result = aprslib.parse(packet)
        # Control chars 0x01-0x03 should be stripped
        self.assertNotIn('\x01', result.get('comment', ''))
        self.assertNotIn('\x02', result.get('comment', ''))
        self.assertIn('test', result.get('comment', ''))
        self.assertIn('end', result.get('comment', ''))

    def test_tab_preserved(self):
        """Tab characters are preserved in comments."""
        packet = "N0CALL>APRS:!4903.50N/07201.75W-test\tend"
        result = aprslib.parse(packet)
        self.assertIn('\t', result.get('comment', ''))

    def test_normal_comment_unchanged(self):
        """Normal ASCII comment passes through unchanged."""
        packet = "N0CALL>APRS:!4903.50N/07201.75W-Hello World 73"
        result = aprslib.parse(packet)
        self.assertEqual(result.get('comment', ''), 'Hello World 73')


class WeatherSoftwareIdTest(unittest.TestCase):
    """Test weather software ID extraction."""

    def test_davis_software_id(self):
        """Davis weather software ID 'eDvs' extracted."""
        # Positionless weather with software ID at end
        packet = "N0CALL>APRS:_10090556c220s004g005t077r000p000P000h50b09900eDvs"
        result = aprslib.parse(packet)
        self.assertEqual(result['weather'].get('wx_software'), 'eDvs')

    def test_no_software_id(self):
        """Long comment after weather is not treated as software ID."""
        packet = "N0CALL>APRS:_10090556c220s004g005t077r000p000P000h50b09900this is a long comment"
        result = aprslib.parse(packet)
        self.assertNotIn('wx_software', result.get('weather', {}))


if __name__ == '__main__':
    unittest.main()
