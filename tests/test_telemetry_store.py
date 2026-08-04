import unittest
from aprslib.telemetry_store import TelemetryStore
from aprslib.parsing import parse


class TestTelemetryStore(unittest.TestCase):
    def setUp(self):
        self.store = TelemetryStore()
    
    def test_update_and_retrieve_config(self):
        config = {'tPARM': ['Battery', 'Temp', 'Pressure', '', '', '', '', '', '', '', '', '', '']}
        self.store.update_config('N3MIM', config)
        self.assertTrue(self.store.has_config('N3MIM'))
        self.assertEqual(self.store.get_config('N3MIM')['tPARM'][0], 'Battery')
    
    def test_case_insensitive(self):
        self.store.update_config('n3mim', {'tPARM': ['A'] * 13})
        self.assertTrue(self.store.has_config('N3MIM'))
    
    def test_apply_default_coefficients(self):
        """Without EQNS config, default is identity (0*x^2 + 1*x + 0)."""
        telemetry = {'seq': 1, 'vals': [100, 200, 150, 75, 25], 'bits': '11001100'}
        result = self.store.apply('UNKNOWN', telemetry)
        self.assertEqual(result['seq'], 1)
        self.assertEqual(len(result['channels']), 5)
        # Default equation: 0*x^2 + 1*x + 0 = x
        self.assertEqual(result['channels'][0]['value'], 100)
        self.assertEqual(result['channels'][0]['raw'], 100)
    
    def test_apply_with_equations(self):
        """Test quadratic conversion: a*x^2 + b*x + c."""
        self.store.update_config('TEST', {
            'tEQNS': [[0, 2.6, 0], [0, 0.53, -32], [3, 4.39, 49], [0, 1, 0], [0, 1, 0]],
            'tPARM': ['Battery', 'BTemp', 'AirTemp', 'Pres', 'Alt', '', '', '', '', '', '', '', ''],
            'tUNIT': ['Volts', 'deg.F', 'deg.F', 'Mbar', 'Kfeet', '', '', '', '', '', '', '', ''],
        })
        
        telemetry = {'seq': 123, 'vals': [100, 200, 10, 50, 25], 'bits': '10110101'}
        result = self.store.apply('TEST', telemetry)
        
        # Channel 0: 0*100^2 + 2.6*100 + 0 = 260.0
        self.assertAlmostEqual(result['channels'][0]['value'], 260.0)
        self.assertEqual(result['channels'][0]['name'], 'Battery')
        self.assertEqual(result['channels'][0]['unit'], 'Volts')
        
        # Channel 1: 0*200^2 + 0.53*200 + (-32) = 74.0
        self.assertAlmostEqual(result['channels'][1]['value'], 74.0)
        
        # Channel 2: 3*10^2 + 4.39*10 + 49 = 300 + 43.9 + 49 = 392.9
        self.assertAlmostEqual(result['channels'][2]['value'], 392.9)
    
    def test_apply_digital_channels(self):
        """Test digital channel sense bit XOR."""
        self.store.update_config('TEST', {
            'tBITS': '10110101',
            'tPARM': ['', '', '', '', '', 'Camera', 'Chute', 'Sun', 'Switch', '', '', '', ''],
        })
        
        telemetry = {'seq': 1, 'vals': [0] * 5, 'bits': '11001100'}
        result = self.store.apply('TEST', telemetry)
        
        # With tBITS='10110101' and bits_data='11001100':
        # bit 0: data=1, sense=1 → match → active
        self.assertTrue(result['digital'][0]['active'])
        # bit 1: data=1, sense=0 → no match → not active
        self.assertFalse(result['digital'][1]['active'])
        # bit 2: data=0, sense=1 → no match → not active
        self.assertFalse(result['digital'][2]['active'])
        # bit 3: data=0, sense=1 → no match → not active
        self.assertFalse(result['digital'][3]['active'])
        
        self.assertEqual(result['digital'][0]['name'], 'Camera')
    
    def test_apply_with_title(self):
        self.store.update_config('TEST', {'title': 'My Project'})
        telemetry = {'seq': 1, 'vals': [0] * 5, 'bits': '00000000'}
        result = self.store.apply('TEST', telemetry)
        self.assertEqual(result['title'], 'My Project')
    
    def test_clear_specific(self):
        self.store.update_config('A', {'tPARM': ['x'] * 13})
        self.store.update_config('B', {'tPARM': ['y'] * 13})
        self.store.clear('A')
        self.assertFalse(self.store.has_config('A'))
        self.assertTrue(self.store.has_config('B'))
    
    def test_clear_all(self):
        self.store.update_config('A', {'tPARM': ['x'] * 13})
        self.store.update_config('B', {'tPARM': ['y'] * 13})
        self.store.clear()
        self.assertFalse(self.store.has_config('A'))
        self.assertFalse(self.store.has_config('B'))
    
    def test_integration_with_parse(self):
        """Test using actual parsed packets."""
        # Parse EQNS config
        pkt = parse("N3MIM>APRS::N3MIM    :EQNS.0,2.6,0,0,.53,-32,3,4.39,49,0,1,0,0,1,0")
        self.store.update_config('N3MIM', pkt)
        
        # Parse telemetry data
        pkt = parse("N3MIM>APRS:T#100,100,200,010,050,025,10110101")
        result = self.store.apply('N3MIM', pkt['telemetry'])
        
        self.assertEqual(result['seq'], 100)
        self.assertAlmostEqual(result['channels'][0]['value'], 260.0)
    
    def test_partial_config(self):
        """Config can arrive in pieces."""
        self.store.update_config('TEST', {
            'tPARM': ['Volts', 'Temp', '', '', '', '', '', '', '', '', '', '', '']
        })
        self.store.update_config('TEST', {
            'tEQNS': [[0, 0.01, 0], [0, 0.1, -40], [0, 1, 0], [0, 1, 0], [0, 1, 0]]
        })
        
        config = self.store.get_config('TEST')
        self.assertIn('tPARM', config)
        self.assertIn('tEQNS', config)


if __name__ == '__main__':
    unittest.main()
