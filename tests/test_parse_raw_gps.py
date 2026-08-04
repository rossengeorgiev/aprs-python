import unittest

from aprslib import parse


class ParseRawGPS(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_ultimeter_format(self):
        """Test ULTW (Ultimeter weather) format routed to Peet Bros parser"""
        packet = "NE4SC-12>APRS,WIDE1-1,qAR,KW4BET-3:$ULTW00A100EB013E1152----000086A0000103190013006E0000006E"
        result = parse(packet)

        self.assertEqual(result['format'], 'peet-bros-weather')
        self.assertIn('weather', result)

    def test_ultimeter_format_short_data(self):
        """Test ULTW format with short data"""
        packet = "TEST>APRS:$ULTW00A100EB"
        result = parse(packet)

        self.assertEqual(result['format'], 'peet-bros-weather')
        self.assertEqual(result['raw_data'], '00A100EB')

    def test_nmea_rmc_basic(self):
        """Test NMEA RMC sentence parsing"""
        packet = "TEST>APRS:$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A"
        result = parse(packet)

        self.assertEqual(result['format'], 'raw-gps')
        self.assertEqual(result['nmea_talker'], 'GP')
        self.assertEqual(result['nmea_sentence'], 'RMC')
        self.assertIn('latitude', result)
        self.assertIn('longitude', result)
        self.assertIn('speed', result)
        self.assertIn('course', result)
        self.assertIn('gps_status', result)
        self.assertEqual(result['gps_status'], 'A')  # A = valid

    def test_nmea_rmc_south_west(self):
        """Test NMEA RMC with South and West coordinates"""
        packet = "TEST>APRS:$GPRMC,123519,A,4807.038,S,01131.000,W,022.4,084.4,230394,003.1,W*65"
        result = parse(packet)

        self.assertEqual(result['format'], 'raw-gps')
        self.assertLess(result['latitude'], 0)  # South is negative
        self.assertLess(result['longitude'], 0)  # West is negative

    def test_nmea_rmc_invalid_status(self):
        """Test NMEA RMC with invalid GPS status"""
        packet = "TEST>APRS:$GPRMC,123519,V,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*7D"
        result = parse(packet)

        self.assertEqual(result['format'], 'raw-gps')
        self.assertEqual(result['gps_status'], 'V')  # V = invalid

    def test_nmea_gga_basic(self):
        """Test NMEA GGA sentence parsing"""
        packet = "TEST>APRS:$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"
        result = parse(packet)

        self.assertEqual(result['format'], 'raw-gps')
        self.assertEqual(result['nmea_talker'], 'GP')
        self.assertEqual(result['nmea_sentence'], 'GGA')
        self.assertIn('latitude', result)
        self.assertIn('longitude', result)
        self.assertIn('altitude', result)
        self.assertIn('gps_fix_quality', result)
        self.assertIn('gps_satellites', result)
        self.assertEqual(result['gps_fix_quality'], 1)
        self.assertEqual(result['gps_satellites'], 8)
        self.assertEqual(result['altitude'], 545.4)

    def test_nmea_gga_south_west(self):
        """Test NMEA GGA with South and West coordinates"""
        packet = "TEST>APRS:$GPGGA,123519,4807.038,S,01131.000,W,1,08,0.9,545.4,M,46.9,M,,*48"
        result = parse(packet)

        self.assertEqual(result['format'], 'raw-gps')
        self.assertLess(result['latitude'], 0)
        self.assertLess(result['longitude'], 0)

    def test_nmea_gga_no_fix(self):
        """Test NMEA GGA with no GPS fix"""
        packet = "TEST>APRS:$GPGGA,123519,4807.038,N,01131.000,E,0,00,0.9,,M,,M,,*75"
        result = parse(packet)

        self.assertEqual(result['format'], 'raw-gps')
        self.assertEqual(result['gps_fix_quality'], 0)
        self.assertEqual(result['gps_satellites'], 0)

    def test_nmea_other_sentence_types(self):
        """Test other NMEA sentence types (not parsed, just stored)"""
        packet = "TEST>APRS:$GPGLL,4807.038,N,01131.000,E,123519,A*25"
        result = parse(packet)

        self.assertEqual(result['format'], 'raw-gps')
        self.assertEqual(result['nmea_talker'], 'GP')
        self.assertEqual(result['nmea_sentence'], 'GLL')
        self.assertIn('nmea_data', result)

    def test_nmea_different_talker(self):
        """Test NMEA with different talker ID"""
        packet = "TEST>APRS:$GLRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*76"
        result = parse(packet)

        self.assertEqual(result['format'], 'raw-gps')
        self.assertEqual(result['nmea_talker'], 'GL')  # GLONASS
        self.assertEqual(result['nmea_sentence'], 'RMC')

    def test_raw_gps_empty_body(self):
        """Test raw GPS with empty body"""
        packet = "TEST>APRS:$"
        result = parse(packet)

        self.assertEqual(result['format'], 'raw-gps')
        self.assertEqual(result['raw_data'], '')

    def test_raw_gps_unknown_format(self):
        """Test raw GPS with unknown format"""
        packet = "TEST>APRS:$UNKNOWN12345"
        result = parse(packet)

        self.assertEqual(result['format'], 'raw-gps')
        self.assertEqual(result['raw_data'], 'UNKNOWN12345')

    def test_raw_gps_proprietary_format(self):
        """Test raw GPS with proprietary 4-character format"""
        packet = "TEST>APRS:$ABCD1234567890"
        result = parse(packet)

        self.assertEqual(result['format'], 'raw-gps')
        self.assertEqual(result['format_id'], 'ABCD')
        self.assertEqual(result['hex_data'], '1234567890')

    def test_raw_gps_output_format(self):
        """Test that parsed raw GPS has correct output format"""
        packet = "TEST>APRS:$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A"
        result = parse(packet)

        # Check structure
        self.assertIn('format', result)
        self.assertEqual(result['format'], 'raw-gps')
        self.assertIn('raw_data', result)
        self.assertIn('nmea_talker', result)
        self.assertIn('nmea_sentence', result)

        # Check types
        self.assertIsInstance(result['raw_data'], str)
        self.assertIsInstance(result['nmea_talker'], str)
        self.assertIsInstance(result['nmea_sentence'], str)

        # Check parsed coordinates if available
        if 'latitude' in result:
            self.assertIsInstance(result['latitude'], (int, float))
            self.assertGreaterEqual(result['latitude'], -90)
            self.assertLessEqual(result['latitude'], 90)

        if 'longitude' in result:
            self.assertIsInstance(result['longitude'], (int, float))
            self.assertGreaterEqual(result['longitude'], -180)
            self.assertLessEqual(result['longitude'], 180)

    def test_raw_gps_with_path(self):
        """Test raw GPS packet with path"""
        packet = "TEST>APRS,WIDE1-1,WIDE2-2:$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A"
        result = parse(packet)

        self.assertEqual(result['format'], 'raw-gps')
        self.assertEqual(result['from'], 'TEST')
        self.assertEqual(result['to'], 'APRS')
        self.assertEqual(len(result['path']), 2)

    def test_nmea_rmc_coordinate_parsing(self):
        """Test NMEA RMC coordinate parsing accuracy"""
        packet = "TEST>APRS:$GPRMC,123519,A,4903.50,N,07201.75,W,022.4,084.4,230394,003.1,W*77"
        result = parse(packet)

        # 4903.50N = 49 degrees 3.5 minutes = 49.0583...
        # 07201.75W = 72 degrees 1.75 minutes = -72.0291...
        self.assertAlmostEqual(result['latitude'], 49.058333, places=4)
        self.assertAlmostEqual(result['longitude'], -72.029166, places=4)

    def test_nmea_gga_coordinate_parsing(self):
        """Test NMEA GGA coordinate parsing accuracy"""
        packet = "TEST>APRS:$GPGGA,123519,4903.50,N,07201.75,W,1,08,0.9,545.4,M,46.9,M,,*5A"
        result = parse(packet)

        self.assertAlmostEqual(result['latitude'], 49.058333, places=4)
        self.assertAlmostEqual(result['longitude'], -72.029166, places=4)

    def test_nmea_rmc_speed_conversion(self):
        """Test NMEA RMC speed conversion (knots to km/h)"""
        packet = "TEST>APRS:$GPRMC,123519,A,4807.038,N,01131.000,E,10.0,084.4,230394,003.1,W*5F"
        result = parse(packet)

        # 10 knots = 18.52 km/h
        self.assertAlmostEqual(result['speed'], 18.52, places=2)

    def test_nmea_incomplete_data(self):
        """Test NMEA sentence with incomplete data"""
        packet = "TEST>APRS:$GPRMC,123519,A"
        result = parse(packet)

        self.assertEqual(result['format'], 'raw-gps')
        self.assertEqual(result['nmea_talker'], 'GP')
        self.assertEqual(result['nmea_sentence'], 'RMC')
        # Should not have coordinates if data is incomplete
        self.assertNotIn('latitude', result)
        self.assertNotIn('longitude', result)


if __name__ == '__main__':
    unittest.main()
