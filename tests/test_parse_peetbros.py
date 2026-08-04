import unittest
from aprslib.parsing.peetbros import parse_peetbros, parse_peetbros_logging
from aprslib.exceptions import ParseError
from aprslib.parsing import parse


class TestPeetBrosParser(unittest.TestCase):
    """Tests for $ULTW Peet Bros weather parsing (# DTI)."""

    def test_valid_packet_with_all_fields(self):
        """Full 13-field $ULTW packet (52 hex chars)."""
        # Field layout: gust dir temp rain pressure delta corrLSW corrMSW humidity date time rain2 windspeed
        # 0064 005A 02BC 0032 2710 0000 0000 0000 01F4 0000 0000 0064 00C8
        data = "0064005A02BC003227100000000000000lF400000000006400C8"
        # That has a typo. Let me use clean hex:
        # gust=100(0x0064) dir=90(0x005A) temp=700(0x02BC=70.0F) rain=50(0x0032)
        # pressure=10000(0x2710=1000.0mbar) skip*3 humidity=500(0x01F4=50%)
        # date time rain2=100(0x0064) windspeed=200(0x00C8)
        data = (
            "0064" "005A" "02BC" "0032" "2710" "0000" "0000"
            "0000" "01F4" "0000" "0000" "0064" "00C8"
        )
        body, parsed = parse_peetbros(data)
        self.assertEqual(parsed['format'], 'peet-bros-weather')
        self.assertIn('weather', parsed)
        weather = parsed['weather']

        # wind_gust: 100 * (1/3.6) / 10 = 2.78 m/s → rounded to 2.8
        self.assertAlmostEqual(weather['wind_gust'], 2.8, places=1)

        # wind_direction: (90 & 0xFF) * 1.41176 = 127
        self.assertEqual(weather['wind_direction'], 127)

        # temperature: 700/10 = 70.0 F → (70-32)*5/9 = 21.1 C
        self.assertAlmostEqual(weather['temperature'], 21.1, places=1)

        # pressure: 10000/10 = 1000.0 mbar
        self.assertAlmostEqual(weather['pressure'], 1000.0, places=1)

        # humidity: 500/10 = 50%
        self.assertEqual(weather['humidity'], 50)

        # rain_midnight: field 11 overrides field 3 → 100 * 0.254 = 25.4
        self.assertAlmostEqual(weather['rain_midnight'], 25.4, places=1)

        # wind_speed: 200 * (1/3.6) / 10 = 5.56 → 5.6
        self.assertAlmostEqual(weather['wind_speed'], 5.6, places=1)

    def test_missing_fields_with_dashes(self):
        """Fields marked as ---- are treated as missing."""
        # 4 dashes per field. 3 fields: gust=----, dir=90, temp=----
        data = "----005A----"
        body, parsed = parse_peetbros(data)
        weather = parsed.get('weather', {})
        self.assertNotIn('wind_gust', weather)
        self.assertEqual(weather['wind_direction'], 127)
        self.assertNotIn('temperature', weather)

    def test_non_hex_raises_error(self):
        data = "ZZZZ005A020003000FA0000000646400"
        with self.assertRaises(ParseError):
            parse_peetbros(data)

    def test_empty_body(self):
        body, parsed = parse_peetbros('')
        self.assertEqual(parsed['format'], 'peet-bros-weather')
        self.assertEqual(parsed['raw_data'], '')

    def test_full_packet_through_main_parse(self):
        """Full APRS packet with # DTI."""
        data = "0064005A02BC"
        packet = "N0CALL>APRS:#" + data
        result = parse(packet)
        self.assertEqual(result['format'], 'peet-bros-weather')
        self.assertEqual(result['from'], 'N0CALL')
        self.assertIn('weather', result)

    def test_negative_temperature(self):
        """Negative temperature via signed 16-bit: 0xFFCE = -50 → -50/10 = -5.0F → -20.6C"""
        # gust=0 dir=0 temp=0xFFCE(-50)
        data = "00000000FFCE"
        body, parsed = parse_peetbros(data)
        weather = parsed['weather']
        # -50/10 = -5.0F → (-5-32)*5/9 = -20.6C
        self.assertAlmostEqual(weather['temperature'], -20.6, places=1)

    def test_short_packet(self):
        """Short packet still parses available fields."""
        data = "00C8"  # Just one field: wind_gust=200
        body, parsed = parse_peetbros(data)
        weather = parsed['weather']
        self.assertIn('wind_gust', weather)


class TestPeetBrosLoggingParser(unittest.TestCase):
    """Tests for !! Peet Bros logging frame parsing."""

    def test_basic_logging_frame(self):
        """Parse a basic !! logging frame."""
        # Fields: windspeed dir temp rain pressure indoor_temp humidity humidity_in
        # 0064    005A 02BC 0032 2710    02D0       01F4     0258
        data = "0064005A02BC003227100002D001F40258"
        # Count: 0064|005A|02BC|0032|2710|0002|D001|F402|58 — WRONG alignment!
        # Must be exact 4-char per field:
        # field0=0064 field1=005A field2=02BC field3=0032 field4=2710
        # field5=02D0 field6=01F4 field7=0258
        data = "0064" + "005A" + "02BC" + "0032" + "2710" + "02D0" + "01F4" + "0258"
        body, parsed = parse_peetbros_logging(data)
        self.assertEqual(parsed['format'], 'peet-bros-logging')
        self.assertIn('weather', parsed)
        weather = parsed['weather']

        # wind_speed: 100 * (1/3.6) / 10 = 2.8
        self.assertAlmostEqual(weather['wind_speed'], 2.8, places=1)
        # wind_direction: (90 & 0xFF) * 1.41176 = 127
        self.assertEqual(weather['wind_direction'], 127)
        # temperature: 700/10 = 70F → 21.1C
        self.assertAlmostEqual(weather['temperature'], 21.1, places=1)
        # pressure: 10000/10 = 1000
        self.assertAlmostEqual(weather['pressure'], 1000.0, places=1)
        # indoor temp: 0x02D0 = 720 → 720/10 = 72F → (72-32)*5/9 = 22.2C
        self.assertAlmostEqual(weather['temp_indoor'], 22.2, places=1)
        # humidity: 0x01F4 = 500 → 500/10 = 50
        self.assertEqual(weather['humidity'], 50)
        # indoor humidity: 0x0258 = 600 → 600/10 = 60
        self.assertEqual(weather['humidity_indoor'], 60)

    def test_missing_fields(self):
        """---- fields are treated as missing."""
        data = "----005A----"
        body, parsed = parse_peetbros_logging(data)
        weather = parsed.get('weather', {})
        self.assertNotIn('wind_speed', weather)
        self.assertEqual(weather['wind_direction'], 127)

    def test_empty_body(self):
        body, parsed = parse_peetbros_logging('')
        self.assertEqual(parsed['format'], 'peet-bros-logging')

    def test_dispatch_via_double_bang(self):
        """!! packets dispatched correctly through main parse."""
        data = "0064005A02BC"
        packet = "N0CALL>APRS:!!" + data
        result = parse(packet)
        self.assertEqual(result['format'], 'peet-bros-logging')
        self.assertIn('weather', result)

    def test_humidity_out_of_range(self):
        """Humidity > 100% is discarded."""
        # outdoor humidity (field 6) = 044C = 1100 → 1100/10 = 110 → discarded
        data = "0000" * 6 + "044C" + "0000"
        body, parsed = parse_peetbros_logging(data)
        weather = parsed.get('weather', {})
        self.assertNotIn('humidity', weather)


if __name__ == '__main__':
    unittest.main()
