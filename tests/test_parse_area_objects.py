import unittest
from aprslib.parsing import parse


class ParseAreaObjects(unittest.TestCase):
    def test_open_circle(self):
        result = parse("N0CALL>APRS:;AREA1    *092345z4903.50N\\07201.75Wl088/036")
        self.assertEqual(result['format'], 'object')
        self.assertIn('area_object', result)
        self.assertEqual(result['area_object']['type'], 'circle')
        self.assertEqual(result['area_object']['type_id'], 0)
        self.assertFalse(result['area_object']['filled'])
        self.assertEqual(result['area_object']['color'], 'black')
        self.assertAlmostEqual(result['area_object']['lat_offset'], 88/60.0)
        self.assertAlmostEqual(result['area_object']['lon_offset'], 36/60.0)

    def test_filled_rectangle(self):
        result = parse("N0CALL>APRS:;ZONE1    *092345z4903.50N\\07201.75Wl910/120")
        self.assertIn('area_object', result)
        self.assertEqual(result['area_object']['type'], 'rectangle')
        self.assertTrue(result['area_object']['filled'])
        self.assertEqual(result['area_object']['color'], 'blue')

    def test_line_with_color(self):
        result = parse("N0CALL>APRS:;LINE1    *092345z4903.50N\\07201.75Wl145/440")
        self.assertIn('area_object', result)
        self.assertEqual(result['area_object']['type'], 'line')
        self.assertFalse(result['area_object']['filled'])
        self.assertEqual(result['area_object']['color'], 'red')


class ParseNWSAlerts(unittest.TestCase):
    def test_tornado_warning(self):
        result = parse("N0CALL>APRS:;TORNC025 *241800z3918.00N/07630.00W_000/000TORN>241800z,MD_C025,MD_C027")
        self.assertEqual(result['format'], 'object')
        self.assertIn('nws_alert', result)
        self.assertEqual(result['nws_alert']['advisory_type'], 'TORN')
        self.assertEqual(result['nws_alert']['expiration'], '241800z')
        self.assertEqual(result['nws_alert']['zones'], ['MD_C025', 'MD_C027'])

    def test_flood_warning(self):
        result = parse("N0CALL>APRS:;FLOODC001*010000z4000.00N/08000.00W_000/000FLOOD>311200z,OH_C001,OH_C003")
        self.assertIn('nws_alert', result)
        self.assertEqual(result['nws_alert']['advisory_type'], 'FLOOD')
        self.assertEqual(len(result['nws_alert']['zones']), 2)

    def test_non_nws_object(self):
        result = parse("N0CALL>APRS:;HOUSE    *092345z4903.50N/07201.75W-Just a house")
        self.assertNotIn('nws_alert', result)


class ParseSignpost(unittest.TestCase):
    def test_speed_limit(self):
        result = parse("N0CALL>APRS:;SIGN-I95A*111111z3918.00N\\07630.00Wm055/180 Speed Limit 55")
        self.assertEqual(result['format'], 'object')
        self.assertIn('signpost', result)
        self.assertEqual(result['signpost']['speed_mph'], 55)
        self.assertAlmostEqual(result['signpost']['speed'], 55 * 1.609344)
        self.assertEqual(result['signpost']['bearing'], 180)
        self.assertEqual(result['signpost']['text'], 'Speed Limit 55')


if __name__ == '__main__':
    unittest.main()
