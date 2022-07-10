import unittest

from aprslib.parsing import parse_position

wind_multiplier = 0.44704
mm_multiplier = 0.254

class ParsePositionDataExtAndWeather(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_position_packet_only_weather_valid(self):
        packet_type = '@'
        packet = "092345z4903.50N/07201.75W_g000t066r000p000...dUII"
        expected = {
            'messagecapable': True,
            'raw_timestamp': '092345z',
            'timestamp': 1657410300,
            'format': 'uncompressed',
            'posambiguity': 0,
            'symbol': '_',
            'symbol_table': '/',
            'latitude': 49.05833333333333,
            'longitude': -72.02916666666667,
            'comment': '...dUII',
            'weather': {
                'wind_gust': 0.0,
                'temperature': 18.88888888888889,
                'rain_1h': 0.0,
                'rain_24h': 0.0
            }
        }

        _, result = parse_position(packet_type, packet)
        self.assertEqual(expected, result)

    def test_position_packet_data_ext_and_weather_valid(self):
        packet_type = '@'
        packet = "092345z4903.50N/07201.75W_090/001g000t066r000p000...dUII"
        expected = {
            'messagecapable': True,
            'raw_timestamp': '092345z',
            'timestamp': 1657410300,
            'format': 'uncompressed',
            'posambiguity': 0,
            'symbol': '_',
            'symbol_table': '/',
            'latitude': 49.05833333333333,
            'longitude': -72.02916666666667,
            'course': 90,
            'speed': 1*1.852,
            'comment': '...dUII',
            'weather': {
                'wind_gust': 0.0,
                'temperature': 18.88888888888889,
                'rain_1h': 0.0,
                'rain_24h': 0.0
            }
        }

        _, result = parse_position(packet_type, packet)
        self.assertEqual(expected, result)

    def test_position_packet_optional_speed(self):
        packet_type = '@'
        packet = "092345z4903.50N/07201.75W_090/...g000t066r000p000...dUII"
        expected = {
            'messagecapable': True,
            'raw_timestamp': '092345z',
            'timestamp': 1657410300,
            'format': 'uncompressed',
            'posambiguity': 0,
            'symbol': '_',
            'symbol_table': '/',
            'latitude': 49.05833333333333,
            'longitude': -72.02916666666667,
            'course': 90,
            'comment': '...dUII',
            'weather': {
                'wind_gust': 0.0,
                'temperature': 18.88888888888889,
                'rain_1h': 0.0,
                'rain_24h': 0.0
            }
        }

        _, result = parse_position(packet_type, packet)
        self.assertEqual(expected, result)

    def test_position_packet_optional_course(self):
        packet_type = '@'
        packet = "092345z4903.50N/07201.75W_   /001g000t066r000p000...dUII"
        expected = {
            'messagecapable': True,
            'raw_timestamp': '092345z',
            'timestamp': 1657410300,
            'format': 'uncompressed',
            'posambiguity': 0,
            'symbol': '_',
            'symbol_table': '/',
            'latitude': 49.05833333333333,
            'longitude': -72.02916666666667,
            'speed': 1*1.852,
            'comment': '...dUII',
            'weather': {
                'wind_gust': 0.0,
                'temperature': 18.88888888888889,
                'rain_1h': 0.0,
                'rain_24h': 0.0
            }
        }

        _, result = parse_position(packet_type, packet)
        self.assertEqual(expected, result)

    def test_position_packet_optional_speed_and_course(self):
        packet_type = '@'
        packet = "092345z4903.50N/07201.75W_.../...g000t066r000p000...dUII"
        expected = {
            'messagecapable': True,
            'raw_timestamp': '092345z',
            'timestamp': 1657410300,
            'format': 'uncompressed',
            'posambiguity': 0,
            'symbol': '_',
            'symbol_table': '/',
            'latitude': 49.05833333333333,
            'longitude': -72.02916666666667,
            'comment': '...dUII',
            'weather': {
                'wind_gust': 0.0,
                'temperature': 18.88888888888889,
                'rain_1h': 0.0,
                'rain_24h': 0.0
            }
        }

        _, result = parse_position(packet_type, packet)
        self.assertEqual(expected, result)
    def test_position_packet_optional_course(self):
        packet_type = '@'
        packet = "092345z4903.50N/07201.75W_   /001g000t066r000p000...dUII"
        expected = {
            'messagecapable': True,
            'raw_timestamp': '092345z',
            'timestamp': 1657410300,
            'format': 'uncompressed',
            'posambiguity': 0,
            'symbol': '_',
            'symbol_table': '/',
            'latitude': 49.05833333333333,
            'longitude': -72.02916666666667,
            'speed': 1*1.852,
            'comment': '...dUII',
            'weather': {
                'wind_gust': 0.0,
                'temperature': 18.88888888888889,
                'rain_1h': 0.0,
                'rain_24h': 0.0
            }
        }

        _, result = parse_position(packet_type, packet)
        self.assertEqual(expected, result)

if __name__ == '__main__':
    unittest.main()
