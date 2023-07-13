import unittest

from aprslib.parsing import parse_weather_data
from aprslib.parsing import parse

wind_multiplier = 1
mm_multiplier = 0.010

class ParseCommentWeather(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_wind(self):
        # misc value
        expected = "", {
            "wind_speed": (9 * wind_multiplier),
            "wind_direction": 9
        }
        result = parse_weather_data("009/009")
        self.assertEqual(expected, result)

        # Daft result but possible
        expected = "", {
            "wind_speed": (999 * wind_multiplier),
            "wind_direction": 999
        }
        result = parse_weather_data("999/999")
        self.assertEqual(expected, result)

        #Positionless packet
        expected = "", {
            "wind_speed": float(9 * wind_multiplier),
            "wind_direction": 9
        }
        result = parse_weather_data("c009s009")
        self.assertEqual(expected, result)

        # Daft result but possible
        expected = "", {
            "wind_speed": (999 * wind_multiplier),
            "wind_direction": 999
        }
        result = parse_weather_data("c999s999")
        self.assertEqual(expected, result)

    def test_temp(self):
        # Min
        expected = "", {
            "temperature": float((-99.0 - 32) / 1.8)
        }
        result = parse_weather_data("t-99")
        self.assertEqual(expected, result)

        # Misc
        expected = "", {
            "temperature": -40.0
        }
        result = parse_weather_data("t-40")
        self.assertEqual(expected, result)

        # Zero F
        expected = "", {
            "temperature": -17.77777777777778
        }
        result = parse_weather_data("t000")
        self.assertEqual(expected, result)

        # Daft, but possible
        expected = "", {
            "temperature": 537.2222222222222
        }
        result = parse_weather_data("t999")
        self.assertEqual(expected, result)

    def test_rain_1h(self):
        expected = "", {
            "rain_1h": 0.0
        }
        result = parse_weather_data("r000")
        self.assertEqual(expected, result)

        expected = "", {
            "rain_1h": float(999 * mm_multiplier)
        }
        result = parse_weather_data("r999")
        self.assertEqual(expected, result)

    def test_rain_24h(self):
        expected = "", {
            "rain_24h": 0.0
        }
        result = parse_weather_data("p000")
        self.assertEqual(expected, result)

        expected = "", {
            "rain_24h": float(999 * mm_multiplier)
        }
        result = parse_weather_data("p999")
        self.assertEqual(expected, result)

    def test_rain_since_midnight(self):
        expected = "", {
            "rain_since_midnight": 0.0
        }
        result = parse_weather_data("P000")
        self.assertEqual(expected, result)

        expected = "", {
            "rain_since_midnight": float(999 * mm_multiplier)
        }
        result = parse_weather_data("P999")
        self.assertEqual(expected, result)

    def test_humidity(self):
        expected = "", {
            "humidity": 100
        }
        result = parse_weather_data("h00")
        self.assertEqual(expected, result)

        expected = "", {
            "humidity": 1
        }
        result = parse_weather_data("h01")
        self.assertEqual(expected, result)

        expected = "", {
            "humidity": 99
        }
        result = parse_weather_data("h99")
        self.assertEqual(expected, result)

    def test_pressure(self):
        expected = "", {
            "pressure": 0.0
        }
        result = parse_weather_data("b00000")
        self.assertEqual(expected, result)

        expected = "", {
            "pressure": 9999.9
        }
        result = parse_weather_data("b99999")
        self.assertEqual(expected, result)

    def test_luminosity(self):
        expected = "", {
            "luminosity": 000
        }
        result = parse_weather_data("L000")
        self.assertEqual(expected, result)

        expected = "", {
            "luminosity": 999
        }
        result = parse_weather_data("L999")
        self.assertEqual(expected, result)

        expected = "", {
            "luminosity": 1123
        }
        result = parse_weather_data("l123")
        self.assertEqual(expected, result)

        expected = "", {
            "luminosity": 1999
        }
        result = parse_weather_data("l999")
        self.assertEqual(expected, result)

    def test_snow(self):
        expected = "", {
            "snow": 000
        }
        result = parse_weather_data("s...s000")
        self.assertEqual(expected, result)

        expected = "", {
            "snow": float(5.5 * 25.4)
        }
        result = parse_weather_data("s...s5.5")
        self.assertEqual(expected, result)

        expected = "", {
            "snow": float(999 * 25.4)
        }
        result = parse_weather_data("s...s999")
        self.assertEqual(expected, result)

    def test_rain_raw(self):
        expected = "", {
            "rain_raw": 000
        }
        result = parse_weather_data("#000")
        self.assertEqual(expected, result)

        expected = "", {
            "rain_raw": 999
        }
        result = parse_weather_data("#999")
        self.assertEqual(expected, result)

    # Not possible in real world (rain and snow measurements)
    def test_positionless_packet(self):

        expected = {
            'comment': '.ABS1.2CDF',
            'format': 'wx',
            'from': 'A',
            'path': [],
            'raw': 'A>B:_10090556c220s004g005t077r010p020P030h50b09900s5.5.ABS1.2CDF',
            'to': 'B',
            'via': '',
            'wx_raw_timestamp': '10090556',
            "weather": {
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
        }

        packet = "A>B:_10090556c220s004g005t077r010p020P030h50b09900s5.5.ABS1.2CDF"

        self.assertEqual(expected, parse(packet))

        packet2 = "A>B:_10090556c220s112g   t   r   h  b     .ABS1.2CDF"
        expected['raw'] = packet2
        expected['weather'] = {
            "wind_direction": 220,
            "wind_speed": 112 * wind_multiplier
        }

        self.assertEqual(expected, parse(packet2))

        packet3 = "A>B:_10090556c220s112g...t...r...p...P...b......ABS1.2CDF"
        expected['raw'] = packet3
        expected['weather'] = {
            "wind_direction": 220,
            "wind_speed": 112 * wind_multiplier
        }

        self.assertEqual(expected, parse(packet3))

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

        result = parse_weather_data("319/001g004t048r...p   P000h19b10294eCumulusWMR100")
        self.assertEqual(expected, result)

if __name__ == '__main__':
    unittest.main()
