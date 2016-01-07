import unittest2 as unittest

from aprslib.parsing import _parse_comment_weather

wind_multiplier = 0.44704
mm_multiplier = 0.254

class ParseCommentWeather(unittest.TestCase):

    def test_wind(self):
        # misc value
        expected = "", {
            "wind_speed": (9 * wind_multiplier),
            "wind_direction": 9
        }
        result = _parse_comment_weather("009/009")
        self.assertEqual(expected, result)

        # Daft result but possible
        expected = "", {
            "wind_speed": (999 * wind_multiplier),
            "wind_direction": 999
        }
        result = _parse_comment_weather("999/999")
        self.assertEqual(expected, result)

        #Positionless packet
        expected = "", {
            "wind_speed": float(9 * wind_multiplier),
            "wind_direction": 9
        }
        result = _parse_comment_weather("c009s009")
        self.assertEqual(expected, result)

        # Daft result but possible
        expected = "", {
            "wind_speed": (999 * wind_multiplier),
            "wind_direction": 999
        }
        result = _parse_comment_weather("c999s999")
        self.assertEqual(expected, result)

    def test_temp(self):
        # Min
        expected = "", {
            "temperature": float((-99.0 - 32) / 1.8)
        }
        result = _parse_comment_weather("t-99")
        self.assertEqual(expected, result)

        # Misc
        expected = "", {
            "temperature": -40.0
        }
        result = _parse_comment_weather("t-40")
        self.assertEqual(expected, result)

        # Zero F
        expected = "", {
            "temperature": -17.77777777777778
        }
        result = _parse_comment_weather("t000")
        self.assertEqual(expected, result)

        # Daft, but possible
        expected = "", {
            "temperature": 537.2222222222222
        }
        result = _parse_comment_weather("t999")
        self.assertEqual(expected, result)

    def test_rain_1h(self):
        expected = "", {
            "rain_1h": 0.0
        }
        result = _parse_comment_weather("r000")
        self.assertEqual(expected, result)

        expected = "", {
            "rain_1h": float(999 * mm_multiplier)
        }
        result = _parse_comment_weather("r999")
        self.assertEqual(expected, result)

    def test_rain_24h(self):
        expected = "", {
            "rain_24h": 0.0
        }
        result = _parse_comment_weather("p000")
        self.assertEqual(expected, result)

        expected = "", {
            "rain_24h": float(999 * mm_multiplier)
        }
        result = _parse_comment_weather("p999")
        self.assertEqual(expected, result)

    def test_rain_since_midnight(self):
        expected = "", {
            "rain_since_midnight": 0.0
        }
        result = _parse_comment_weather("P000")
        self.assertEqual(expected, result)

        expected = "", {
            "rain_since_midnight": float(999 * mm_multiplier)
        }
        result = _parse_comment_weather("P999")
        self.assertEqual(expected, result)

    def test_humidity(self):
        expected = "", {
            "humidity": 0.0
        }
        result = _parse_comment_weather("h00")
        self.assertEqual(expected, result)

        expected = "", {
            "humidity": 99
        }
        result = _parse_comment_weather("h99")
        self.assertEqual(expected, result)

    def test_pressure(self):
        expected = "", {
            "pressure": 0.0
        }
        result = _parse_comment_weather("b00000")
        self.assertEqual(expected, result)

        expected = "", {
            "pressure": 9999.9
        }
        result = _parse_comment_weather("b99999")
        self.assertEqual(expected, result)

    def test_luminosity(self):
        expected = "", {
            "luminosity": 000
        }
        result = _parse_comment_weather("L000")
        self.assertEqual(expected, result)

        expected = "", {
            "luminosity": 999
        }
        result = _parse_comment_weather("L999")
        self.assertEqual(expected, result)

        expected = "", {
            "luminosity": 1123
        }
        result = _parse_comment_weather("l123")
        self.assertEqual(expected, result)

        expected = "", {
            "luminosity": 1999
        }
        result = _parse_comment_weather("l999")
        self.assertEqual(expected, result)

    def test_snow(self):
        expected = "", {
            "snow": 000
        }
        result = _parse_comment_weather("s...s000")
        self.assertEqual(expected, result)

        expected = "", {
            "snow": float(5.5 * 25.4)
        }
        result = _parse_comment_weather("s...s5.5")
        self.assertEqual(expected, result)

        expected = "", {
            "snow": float(999 * 25.4)
        }
        result = _parse_comment_weather("s...s999")
        self.assertEqual(expected, result)

    def test_rain_raw(self):
        expected = "", {
            "rain_raw": 000
        }
        result = _parse_comment_weather("#000")
        self.assertEqual(expected, result)

        expected = "", {
            "rain_raw": 999
        }
        result = _parse_comment_weather("#999")
        self.assertEqual(expected, result)

    # Not possible in real world (rain and snow measurements)
    def test_positionless_packet(self):
        expected = "10090556wRSW", {
            "pressure": 990.0,
            "humidity": 50,
            "rain_1h": float(010.0 * mm_multiplier),
            "rain_24h": float(020.0 * mm_multiplier),
            "rain_since_midnight": float(030.0 * mm_multiplier),
            "snow": float(5.5 * 25.4),
            "temperature": float((77.0 - 32) / 1.8),
            "wind_direction": 220,
            "wind_gust": 5.0 * wind_multiplier,
            "wind_speed": 4.0 * wind_multiplier
        }

        result = _parse_comment_weather("10090556c220s004g005t077r010p020P030h50b09900s5.5wRSW")
        self.assertEqual(expected, result)

        expected = "10090556wRSW", {
            "wind_direction": 220,
            "wind_speed": 112 * wind_multiplier
        }

        result = _parse_comment_weather("10090556c220s112g   t   r   p   P   h  b     wRSW")
        self.assertEqual(expected, result)

        expected = "10090556wRSW", {
            "wind_direction": 220,
            "wind_speed": 112 * wind_multiplier
        }
        result = _parse_comment_weather("10090556c220s112g...t...r...p...P...h..b.....wRSW")
        self.assertEqual(expected, result)

    def test_position_packet(self):
        expected = "eCumulusWMR100", {
            "pressure": 1029.4,
            "humidity": 19,
            "rain_since_midnight": 0.0,
            "temperature": (48.0 - 32) / 1.8,
            "wind_direction": 319,
            "wind_gust": 4.0 * wind_multiplier,
            "wind_speed": 1 * wind_multiplier
        }

        result = _parse_comment_weather("319/001g004t048r...p   P000h19b10294eCumulusWMR100")
        self.assertEqual(expected, result)

if __name__ == '__main__':
    unittest.main()
