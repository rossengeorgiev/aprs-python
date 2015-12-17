import unittest2 as unittest

from aprslib.parsing import _parse_comment_weather

wind_multiplier = 0.44704
mm_multiplier = 0.254

class ParseCommentWeather(unittest.TestCase):

    def test_wind(self):
        # misc value
        expected = "009/009", {
            "wind_speed": (9 * wind_multiplier),
            "wind_direction": 9
        }
        result = _parse_comment_weather("009/009")
        self.assertEqual(expected, result)

        # Daft result but possible
        expected = "999/999", {
            "wind_speed": (999 * wind_multiplier),
            "wind_direction": 999
        }
        result = _parse_comment_weather("999/999")
        self.assertEqual(expected, result)

        #Positionless packet
        expected = "c009s009", {
            "wind_speed": float(9 * wind_multiplier),
            "wind_direction": 9
        }
        result = _parse_comment_weather("c009s009")
        self.assertEqual(expected, result)

        # Daft result but possible
        expected = "c999s999", {
            "wind_speed": (999 * wind_multiplier),
            "wind_direction": 999
        }
        result = _parse_comment_weather("c999s999")
        self.assertEqual(expected, result)

    def test_temp(self):
        # Min
        expected = "t-99", {
            "temp": float((-99.0 - 32) / 1.8)
        }
        result = _parse_comment_weather("t-99")
        self.assertEqual(expected, result)

        # Misc
        expected = "t-40", {
            "temp": -40.0
        }
        result = _parse_comment_weather("t-40")
        self.assertEqual(expected, result)

        # Zero F
        expected = "t000", {
            "temp": -17.77777777777778
        }
        result = _parse_comment_weather("t000")
        self.assertEqual(expected, result)

        # Daft, but possible
        expected = "t999", {
            "temp": 537.2222222222222
        }
        result = _parse_comment_weather("t999")
        self.assertEqual(expected, result)

    def test_rain_1h(self):
        expected = "r000", {
            "rain_1h": 0.0
        }
        result = _parse_comment_weather("r000")
        self.assertEqual(expected, result)

        expected = "r999", {
            "rain_1h": float(999 * mm_multiplier)
        }
        result = _parse_comment_weather("r999")
        self.assertEqual(expected, result)

    def test_rain_24h(self):
        expected = "p000", {
            "rain_24h": 0.0
        }
        result = _parse_comment_weather("p000")
        self.assertEqual(expected, result)

        expected = "p999", {
            "rain_24h": float(999 * mm_multiplier)
        }
        result = _parse_comment_weather("p999")
        self.assertEqual(expected, result)

    def test_rain_since_mid(self):
        expected = "P000", {
            "rain_since_mid": 0.0
        }
        result = _parse_comment_weather("P000")
        self.assertEqual(expected, result)

        expected = "P999", {
            "rain_since_mid": float(999 * mm_multiplier)
        }
        result = _parse_comment_weather("P999")
        self.assertEqual(expected, result)

    def test_humidity(self):
        expected = "h00", {
            "humidity": 0.0
        }
        result = _parse_comment_weather("h00")
        self.assertEqual(expected, result)

        expected = "h99", {
            "humidity": 99
        }
        result = _parse_comment_weather("h99")
        self.assertEqual(expected, result)

        # Invalid value
        expected = "h9", {
        }
        result = _parse_comment_weather("h9")
        self.assertEqual(expected, result)

    def test_pressure(self):
        expected = "b00000", {
            "hPa": 0.0
        }
        result = _parse_comment_weather("b00000")
        self.assertEqual(expected, result)

        expected = "b99999", {
            "hPa": 9999.9
        }
        result = _parse_comment_weather("b99999")
        self.assertEqual(expected, result)

    def test_luminosity(self):
        expected = "L000", {
            "luminosity": 000
        }
        result = _parse_comment_weather("L000")
        self.assertEqual(expected, result)

        expected = "L999", {
            "luminosity": 999
        }
        result = _parse_comment_weather("L999")
        self.assertEqual(expected, result)

        expected = "l123", {
            "luminosity": 1123
        }
        result = _parse_comment_weather("l123")
        self.assertEqual(expected, result)

        expected = "l999", {
            "luminosity": 1999
        }
        result = _parse_comment_weather("l999")
        self.assertEqual(expected, result)

    def test_snow(self):
        expected = "s000", {
            "snow": 000
        }
        result = _parse_comment_weather("s000")
        self.assertEqual(expected, result)

        expected = "s5.5", {
            "snow": float(5.5 * 25.4)
        }
        result = _parse_comment_weather("s5.5")
        self.assertEqual(expected, result)

        expected = "s999", {
            "snow": float(999 * 25.4)
        }
        result = _parse_comment_weather("s999")
        self.assertEqual(expected, result)

    def test_rain_raw(self):
        expected = "#000", {
            "rain_raw": 000
        }
        result = _parse_comment_weather("#000")
        self.assertEqual(expected, result)

        expected = "#999", {
            "rain_raw": 999
        }
        result = _parse_comment_weather("#999")
        self.assertEqual(expected, result)

    # Not possible in real world (rain and snow measurements)
    def test_positionless_packet(self):
        expected = "10090556c220s004g005t077r010p020P030h50b09900s5.5wRSW", {
            "hPa": 990.0,
            "humidity": 50,
            "rain_1h": float(010.0 * mm_multiplier),
            "rain_24h": float(020.0 * mm_multiplier),
            "rain_since_mid": float(030.0 * mm_multiplier),
            "snow": float(5.5 * 25.4),
            "temp": float((77.0 - 32) / 1.8),
            "wind_direction": 220,
            "wind_gust": 5.0 * wind_multiplier,
            "wind_speed": 4.0 * wind_multiplier
        }

        result = _parse_comment_weather("10090556c220s004g005t077r010p020P030h50b09900s5.5wRSW")
        self.assertEqual(expected, result)

        expected = "10090556c220s112g   t   r   p   P   h  b     wRSW", {
            "wind_direction": 220,
            "wind_speed": 112 * wind_multiplier
        }

        result = _parse_comment_weather("10090556c220s112g   t   r   p   P   h  b     wRSW")
        self.assertEqual(expected, result)

        expected = "10090556c220s112g...t...r...p...P...h..b.....wRSW", {
            "wind_direction": 220,
            "wind_speed": 112 * wind_multiplier
        }
        result = _parse_comment_weather("10090556c220s112g...t...r...p...P...h..b.....wRSW")
        self.assertEqual(expected, result)

        expected = "_10090556s9.9", {
            "snow": 9.9 * 25.4
        }
        result = _parse_comment_weather("_10090556s9.9")
        self.assertEqual(expected, result)

    def test_position_packet(self):
        expected = "319/001g004t048r...p   P000h19b10294eCumulusWMR100", {
            "hPa": 1029.4,
            "humidity": 19,
            "rain_since_mid": 0.0,
            "temp": (48.0 - 32) / 1.8,
            "wind_direction": 319,
            "wind_gust": 4.0 * wind_multiplier,
            "wind_speed": 1 * wind_multiplier
        }

        result = _parse_comment_weather("319/001g004t048r...p   P000h19b10294eCumulusWMR100")
        self.assertEqual(expected, result)

if __name__ == '__main__':
    unittest.main()
