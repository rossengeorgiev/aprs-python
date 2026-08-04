import unittest
from aprslib.parsing.common import parse_data_extentions
from aprslib.parsing import parse


class TestDFSParsing(unittest.TestCase):

    def test_dfs_basic(self):
        # DFS2360: signal=2, height_code=ord('3')-0x30=3, gain=6, dir=0 (omni)
        body = "DFS2360"
        body_out, parsed = parse_data_extentions(body)
        self.assertEqual(parsed['df_signal'], 2)
        # height: 10 * 2^3 = 80 ft * 0.3048 = 24.384 m
        self.assertAlmostEqual(parsed['df_height'], 80 * 0.3048, places=3)
        self.assertEqual(parsed['df_gain'], 6)
        self.assertEqual(parsed['df_directivity'], 'omni')

    def test_dfs_with_directivity(self):
        # DFS5432: signal=5, height_code=ord('4')-0x30=4, gain=3, dir=2 (90 deg E)
        body = "DFS5432"
        body_out, parsed = parse_data_extentions(body)
        self.assertEqual(parsed['df_signal'], 5)
        # height: 10 * 2^4 = 160 ft * 0.3048 = 48.768 m
        self.assertAlmostEqual(parsed['df_height'], 160 * 0.3048, places=3)
        self.assertEqual(parsed['df_gain'], 3)
        self.assertEqual(parsed['df_directivity'], 90)

    def test_dfs_in_full_packet(self):
        # Position packet with DFS extension
        packet = "N0CALL>APRS:!4903.50N/07201.75W\\DFS2360"
        result = parse(packet)
        self.assertEqual(result['df_signal'], 2)
        self.assertAlmostEqual(result['df_height'], 80 * 0.3048, places=2)
        self.assertEqual(result['df_gain'], 6)
        self.assertEqual(result['df_directivity'], 'omni')

    def test_cse_spd_still_works(self):
        # Regular CSE/SPD should still parse (no regression)
        body = "090/045some comment"
        body_out, parsed = parse_data_extentions(body)
        self.assertEqual(parsed['course'], 90)
        self.assertAlmostEqual(parsed['speed'], 45 * 1.852, places=2)

    def test_phg_still_works(self):
        # PHG should still parse when DFS doesn't match
        body = "PHG5360"
        body_out, parsed = parse_data_extentions(body)
        self.assertIn('phg', parsed)
        self.assertEqual(parsed['phg'], '5360')
        self.assertEqual(parsed['phg_power'], 25)  # 5^2
        self.assertEqual(parsed['phg_dir'], 'omni')  # dir=0

    def test_dfs_body_consumed(self):
        # After parsing DFS, the 7 chars should be consumed
        body = "DFS2360extra text"
        body_out, parsed = parse_data_extentions(body)
        self.assertEqual(body_out, "extra text")


if __name__ == '__main__':
    unittest.main()
