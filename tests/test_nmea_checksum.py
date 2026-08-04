"""Tests for NMEA checksum validation in parse_raw_gps."""
import unittest
import aprslib


class NmeaChecksumTest(unittest.TestCase):
    """Test NMEA checksum validation."""

    def test_valid_checksum(self):
        """Valid NMEA checksum sets nmea_checksum_ok=True."""
        # Compute a valid checksum for GPRMC,081836,A,3751.65,S,14507.36,E,000.0,360.0,130998,011.3,E
        sentence = "GPRMC,081836,A,3751.65,S,14507.36,E,000.0,360.0,130998,011.3,E"
        checksum = 0
        for c in sentence:
            checksum ^= ord(c)
        checksum_hex = format(checksum, '02X')
        # Build full packet with $ already stripped (raw GPS body after $ DTI)
        body = sentence + "*" + checksum_hex
        packet = "N0CALL>APRS:$" + body
        result = aprslib.parse(packet)
        self.assertTrue(result.get('nmea_checksum_ok'))

    def test_invalid_checksum(self):
        """Invalid NMEA checksum sets nmea_checksum_ok=False."""
        body = "GPRMC,081836,A,3751.65,S,14507.36,E,000.0,360.0,130998,011.3,E*FF"
        packet = "N0CALL>APRS:$" + body
        result = aprslib.parse(packet)
        self.assertFalse(result.get('nmea_checksum_ok'))

    def test_no_checksum(self):
        """No checksum present: nmea_checksum_ok not set."""
        body = "GPRMC,081836,A,3751.65,S,14507.36,E,000.0,360.0,130998,011.3,E"
        packet = "N0CALL>APRS:$" + body
        result = aprslib.parse(packet)
        self.assertNotIn('nmea_checksum_ok', result)

    def test_valid_gpgga_checksum(self):
        """Valid checksum on GPGGA sentence."""
        sentence = "GPGGA,092750.000,5321.6802,N,00630.3372,W,1,8,1.03,61.7,M,55.2,M,,"
        checksum = 0
        for c in sentence:
            checksum ^= ord(c)
        checksum_hex = format(checksum, '02X')
        body = sentence + "*" + checksum_hex
        packet = "N0CALL>APRS:$" + body
        result = aprslib.parse(packet)
        self.assertTrue(result.get('nmea_checksum_ok'))


if __name__ == '__main__':
    unittest.main()
