"""Tests for symbol-from-destination (GPSxyz/SPCxyz) lookup."""
import unittest
from aprslib.parsing.dstsymbol import get_symbol_from_destination


class DstSymbolTest(unittest.TestCase):
    """Test destination callsign symbol lookup."""

    def test_primary_table_car(self):
        """GPSMV = primary table, car symbol '>'"""
        result = get_symbol_from_destination("GPSMV")
        self.assertEqual(result, ('/', '>'))

    def test_primary_table_aid_station(self):
        """GPSPA = primary table, 'A'"""
        result = get_symbol_from_destination("GPSPA")
        self.assertEqual(result, ('/', 'A'))

    def test_secondary_table(self):
        """GPSAA = secondary table, 'A'"""
        result = get_symbol_from_destination("GPSAA")
        self.assertEqual(result, ('\\', 'A'))

    def test_spc_prefix(self):
        """SPC prefix works same as GPS."""
        result = get_symbol_from_destination("SPCMV")
        self.assertEqual(result, ('/', '>'))

    def test_primary_numeric_encoding(self):
        """GPSC33 = primary table, chr(33+32)=chr(65)='A'... wait, chr(33)='!' actually"""
        # C + NN: code = chr(NN + 32). C01 = chr(33) = '!'
        result = get_symbol_from_destination("GPSC01")
        self.assertEqual(result, ('/', '!'))

    def test_secondary_numeric_encoding(self):
        """GPSE01 = secondary table, chr(33)='!'"""
        result = get_symbol_from_destination("GPSE01")
        self.assertEqual(result, ('\\', '!'))

    def test_numeric_boundary(self):
        """GPSC94 = primary table, chr(94+32)=chr(126)='~'"""
        result = get_symbol_from_destination("GPSC94")
        self.assertEqual(result, ('/', '~'))

    def test_numeric_out_of_range(self):
        """GPSC00 is invalid (0 not in 1-94)."""
        result = get_symbol_from_destination("GPSC00")
        self.assertIsNone(result)

    def test_numeric_too_high(self):
        """GPSC95 is invalid."""
        result = get_symbol_from_destination("GPSC95")
        self.assertIsNone(result)

    def test_overlay(self):
        """GPSAA3 = secondary symbol 'A' with overlay '3'."""
        result = get_symbol_from_destination("GPSAA3")
        self.assertEqual(result, ('3', 'A'))

    def test_overlay_letter(self):
        """GPSAAX = secondary symbol 'A' with overlay 'X'."""
        result = get_symbol_from_destination("GPSAAX")
        self.assertEqual(result, ('X', 'A'))

    def test_not_gps_or_spc(self):
        """Non GPSxxx/SPCxxx returns None."""
        self.assertIsNone(get_symbol_from_destination("APRS"))
        self.assertIsNone(get_symbol_from_destination("WIDE1-1"))

    def test_ssid_stripped(self):
        """SSID in destination is stripped."""
        result = get_symbol_from_destination("GPSMV-5")
        self.assertEqual(result, ('/', '>'))

    def test_empty(self):
        self.assertIsNone(get_symbol_from_destination(""))
        self.assertIsNone(get_symbol_from_destination(None))

    def test_invalid_suffix(self):
        """GPS with 1-char suffix is invalid."""
        self.assertIsNone(get_symbol_from_destination("GPSA"))

    def test_primary_numbers(self):
        """P0-P9 = primary table numbers 0-9."""
        result = get_symbol_from_destination("GPSP0")
        self.assertEqual(result, ('/', '0'))
        result = get_symbol_from_destination("GPSP9")
        self.assertEqual(result, ('/', '9'))

    def test_secondary_numbers(self):
        """A0-A9 = secondary table 0-9."""
        result = get_symbol_from_destination("GPSA0")
        self.assertEqual(result, ('\\', '0'))


if __name__ == '__main__':
    unittest.main()
