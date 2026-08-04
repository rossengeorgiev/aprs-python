"""Tests for duplicate detection utilities."""
import unittest
from aprslib.dedup import dedup_key, DuplicateFilter


class DedupKeyTest(unittest.TestCase):
    """Test dedup_key extraction."""

    def test_simple_packet(self):
        key = dedup_key("N0CALL>APRS:!4903.50N/07201.75W-")
        self.assertEqual(key, "N0CALL-0:APRS:!4903.50N/07201.75W-")

    def test_source_with_ssid(self):
        key = dedup_key("N0CALL-5>APRS:test")
        self.assertEqual(key, "N0CALL-5:APRS:test")

    def test_destination_ssid_stripped(self):
        key = dedup_key("N0CALL>APRS-0,WIDE1-1:test")
        self.assertEqual(key, "N0CALL-0:APRS:test")

    def test_path_ignored(self):
        key1 = dedup_key("N0CALL>APRS,WIDE1-1,WIDE2-1:test body")
        key2 = dedup_key("N0CALL>APRS,RELAY*,WIDE:test body")
        # Same source, dest, body → same key
        self.assertEqual(key1, key2)

    def test_third_party_unwrap(self):
        """Third-party packets unwrap to inner packet."""
        inner = "N0CALL>APRS:!4903.50N/07201.75W-"
        outer = "RELAY>APRS,TCPIP*:}" + inner
        key = dedup_key(outer)
        expected = dedup_key(inner)
        self.assertEqual(key, expected)

    def test_nested_third_party(self):
        """Multiple third-party wraps are unwrapped."""
        inner = "N0CALL>APRS:test"
        wrap1 = "RELAY1>APRS:}" + inner
        wrap2 = "RELAY2>APRS:}" + wrap1
        key = dedup_key(wrap2)
        expected = dedup_key(inner)
        self.assertEqual(key, expected)

    def test_trailing_whitespace_stripped(self):
        key1 = dedup_key("N0CALL>APRS:test")
        key2 = dedup_key("N0CALL>APRS:test   ")
        self.assertEqual(key1, key2)

    def test_case_normalization(self):
        key1 = dedup_key("n0call>aprs:test")
        key2 = dedup_key("N0CALL>APRS:test")
        self.assertEqual(key1, key2)

    def test_empty_returns_none(self):
        self.assertIsNone(dedup_key(""))
        self.assertIsNone(dedup_key(None))

    def test_no_body_returns_none(self):
        self.assertIsNone(dedup_key("N0CALL>APRS"))


class DuplicateFilterTest(unittest.TestCase):
    """Test DuplicateFilter class."""

    def test_first_packet_not_duplicate(self):
        df = DuplicateFilter(ttl=28)
        parsed = {'raw': 'N0CALL>APRS:test'}
        result = df.check(parsed)
        self.assertFalse(result)
        self.assertFalse(parsed['is_duplicate'])
        self.assertIsNotNone(parsed['dedup_key'])

    def test_same_packet_is_duplicate(self):
        df = DuplicateFilter(ttl=28)
        parsed1 = {'raw': 'N0CALL>APRS:test'}
        parsed2 = {'raw': 'N0CALL>APRS:test'}
        df.check(parsed1)
        result = df.check(parsed2)
        self.assertTrue(result)
        self.assertTrue(parsed2['is_duplicate'])

    def test_different_path_same_content_is_duplicate(self):
        df = DuplicateFilter(ttl=28)
        parsed1 = {'raw': 'N0CALL>APRS,WIDE1-1:test'}
        parsed2 = {'raw': 'N0CALL>APRS,RELAY*:test'}
        df.check(parsed1)
        result = df.check(parsed2)
        self.assertTrue(result)

    def test_different_body_not_duplicate(self):
        df = DuplicateFilter(ttl=28)
        parsed1 = {'raw': 'N0CALL>APRS:test1'}
        parsed2 = {'raw': 'N0CALL>APRS:test2'}
        df.check(parsed1)
        result = df.check(parsed2)
        self.assertFalse(result)

    def test_ttl_expiry(self):
        df = DuplicateFilter(ttl=1)
        parsed1 = {'raw': 'N0CALL>APRS:test'}
        df.check(parsed1)
        # Manually expire
        df._seen = {k: t - 2 for k, t in df._seen.items()}
        parsed2 = {'raw': 'N0CALL>APRS:test'}
        result = df.check(parsed2)
        self.assertFalse(result)

    def test_clear(self):
        df = DuplicateFilter(ttl=28)
        df.check({'raw': 'N0CALL>APRS:test'})
        self.assertEqual(df.size, 1)
        df.clear()
        self.assertEqual(df.size, 0)

    def test_unparseable_packet(self):
        df = DuplicateFilter(ttl=28)
        parsed = {'raw': 'garbage'}
        result = df.check(parsed)
        self.assertFalse(result)
        self.assertIsNone(parsed['dedup_key'])


if __name__ == '__main__':
    unittest.main()
