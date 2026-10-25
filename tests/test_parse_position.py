import unittest
from datetime import datetime

from aprslib.parsing import parse_position

class ParsePositionDataExtAndWeather(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def timestamp_from_partial(self, day, hour, minute):
        now = datetime.now()
        corrected = now.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)
        return int((corrected - datetime(1970, 1, 1)).total_seconds())

    def test_position_packet_only_weather_valid(self):
        packet_type = '@'
        packet = "092345z4903.50N/07201.75W_g000t066r000p000...dUII"
        expected = {
            'messagecapable': True,
            'raw_timestamp': '092345z',
            'timestamp': self.timestamp_from_partial(9, 23, 45),
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
            'timestamp': self.timestamp_from_partial(9, 23, 45),
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
            'timestamp': self.timestamp_from_partial(9, 23, 45),
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
            'timestamp': self.timestamp_from_partial(9, 23, 45),
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
            'timestamp': self.timestamp_from_partial(9, 23, 45),
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
            'timestamp': self.timestamp_from_partial(9, 23, 45),
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

class ParseCompressedPosition(unittest.TestCase):
    def test_numeric_symbol_overlays(self):
        for encoded, expected in zip('abcdefghij', '0123456789'):
            _, result = parse_position('!', encoded + '5L!!<*e7#7P[')
            self.assertEqual(expected, result['symbol_table'])
            self.assertEqual('#', result['symbol'])

    def test_other_symbol_tables(self):
        for symbol_table in '/\\ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            _, result = parse_position('!', symbol_table + '5L!!<*e7#7P[')
            self.assertEqual(symbol_table, result['symbol_table'])


if __name__ == '__main__':
    unittest.main()
