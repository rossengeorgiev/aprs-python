import unittest
from aprslib.path import analyze_path


class TestAnalyzePath(unittest.TestCase):
    def test_simple_wide_path(self):
        result = analyze_path(['WIDE1-1', 'WIDE2-1'])
        self.assertEqual(result['hops_remaining'], 2)
        self.assertEqual(result['hops_consumed'], 0)
        self.assertFalse(result['is_internet'])
    
    def test_partially_consumed(self):
        result = analyze_path(['WIDE1*', 'WIDE2-1'])
        self.assertEqual(result['hops_consumed'], 1)
        self.assertEqual(result['hops_remaining'], 1)
    
    def test_fully_consumed(self):
        result = analyze_path(['WIDE1*', 'WIDE2*'])
        self.assertEqual(result['hops_consumed'], 3)  # 1 + 2
        self.assertEqual(result['hops_remaining'], 0)
    
    def test_internet_qar(self):
        result = analyze_path(['TCPIP*', 'qAR', 'IGATE1'])
        self.assertTrue(result['is_internet'])
        self.assertEqual(result['q_construct'], 'qAR')
        self.assertEqual(result['igate'], 'IGATE1')
    
    def test_nogate(self):
        result = analyze_path(['RFONLY', 'WIDE1-1'])
        self.assertTrue(result['no_gate'])
        self.assertEqual(result['hops_remaining'], 1)
    
    def test_specific_digi(self):
        result = analyze_path(['N0CALL*', 'WIDE2-1'])
        self.assertEqual(result['digipeaters'], ['N0CALL'])
        self.assertEqual(result['hops_consumed'], 1)
    
    def test_empty_path(self):
        result = analyze_path([])
        self.assertEqual(result['total_hops'], 0)
        self.assertFalse(result['is_internet'])


class TestDecodeSymbol(unittest.TestCase):
    def test_primary_car(self):
        from aprslib.symbols import decode_symbol
        result = decode_symbol('/', '>')
        self.assertEqual(result['description'], 'Car')
        self.assertNotIn('overlay', result)
    
    def test_alternate_emergency(self):
        from aprslib.symbols import decode_symbol
        result = decode_symbol('\\', '!')
        self.assertEqual(result['description'], 'Emergency')
    
    def test_overlay(self):
        from aprslib.symbols import decode_symbol
        result = decode_symbol('1', '>')
        self.assertEqual(result['description'], 'Car (overlay)')
        self.assertEqual(result['overlay'], '1')
    
    def test_weather_station(self):
        from aprslib.symbols import decode_symbol
        result = decode_symbol('/', '_')
        self.assertEqual(result['description'], 'Weather Station')


class TestWeatherExtensions(unittest.TestCase):
    def test_radiation(self):
        from aprslib.parsing.weather import parse_weather_data
        body, result = parse_weather_data("c180s005g010t077X123")
        self.assertIn('radiation', result)
        self.assertEqual(result['radiation'], 12000)  # 12 * 10^3 nSv/hr
    
    def test_battery_voltage(self):
        from aprslib.parsing.weather import parse_weather_data
        body, result = parse_weather_data("c090s010g015t065V128")
        self.assertIn('battery', result)
        self.assertAlmostEqual(result['battery'], 12.8)


if __name__ == '__main__':
    unittest.main()
