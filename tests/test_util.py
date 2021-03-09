
import unittest

from aprslib import util


class UtilTC(unittest.TestCase):
    def test_latitude(self):
        self.assertEqual(util.latitude_to_ddm(0), "0000.00N")
        self.assertEqual(util.latitude_to_ddm(45), "4500.00N")
        self.assertEqual(util.latitude_to_ddm(90), "9000.00N")
        self.assertEqual(util.latitude_to_ddm(0.5), "0030.00N")
        self.assertEqual(util.latitude_to_ddm(0.55), "0033.00N")
        self.assertEqual(util.latitude_to_ddm(0.555), "0033.30N")
        self.assertEqual(util.latitude_to_ddm(0.5555), "0033.33N")
        self.assertEqual(util.latitude_to_ddm(0.9999), "0059.99N")
        self.assertEqual(util.latitude_to_ddm(0.99999), "0060.00N")

    def test_latitude_negative(self):
        self.assertEqual(util.latitude_to_ddm(-45), "4500.00S")
        self.assertEqual(util.latitude_to_ddm(-90), "9000.00S")
        self.assertEqual(util.latitude_to_ddm(-0.5), "0030.00S")
        self.assertEqual(util.latitude_to_ddm(-0.55), "0033.00S")
        self.assertEqual(util.latitude_to_ddm(-0.555), "0033.30S")
        self.assertEqual(util.latitude_to_ddm(-0.5555), "0033.33S")
        self.assertEqual(util.latitude_to_ddm(-0.9999), "0059.99S")
        self.assertEqual(util.latitude_to_ddm(-0.99999), "0060.00S")

    def test_longitude(self):
        self.assertEqual(util.longitude_to_ddm(0), "00000.00E")
        self.assertEqual(util.longitude_to_ddm(45), "04500.00E")
        self.assertEqual(util.longitude_to_ddm(90), "09000.00E")
        self.assertEqual(util.longitude_to_ddm(135), "13500.00E")
        self.assertEqual(util.longitude_to_ddm(180), "18000.00E")
        self.assertEqual(util.longitude_to_ddm(0.5), "00030.00E")
        self.assertEqual(util.longitude_to_ddm(0.55), "00033.00E")
        self.assertEqual(util.longitude_to_ddm(0.555), "00033.30E")
        self.assertEqual(util.longitude_to_ddm(0.5555), "00033.33E")
        self.assertEqual(util.longitude_to_ddm(0.9999), "00059.99E")
        self.assertEqual(util.longitude_to_ddm(0.99999), "00060.00E")

    def test_longitude_negative(self):
        self.assertEqual(util.longitude_to_ddm(-45), "04500.00W")
        self.assertEqual(util.longitude_to_ddm(-90), "09000.00W")
        self.assertEqual(util.longitude_to_ddm(-135), "13500.00W")
        self.assertEqual(util.longitude_to_ddm(-180), "18000.00W")
        self.assertEqual(util.longitude_to_ddm(-0.5), "00030.00W")
        self.assertEqual(util.longitude_to_ddm(-0.55), "00033.00W")
        self.assertEqual(util.longitude_to_ddm(-0.555), "00033.30W")
        self.assertEqual(util.longitude_to_ddm(-0.5555), "00033.33W")
        self.assertEqual(util.longitude_to_ddm(-0.9999), "00059.99W")
        self.assertEqual(util.longitude_to_ddm(-0.99999), "00060.00W")

    def test_comment_altitude(self):
        self.assertEqual(util.comment_altitude(0), "/A=000000")

        # top limit
        self.assertEqual(util.comment_altitude(100000000), "/A=999999")
        # bottom limit
        self.assertEqual(util.comment_altitude(-100000000), "/A=-99999")

        self.assertEqual(util.comment_altitude(1.524), "/A=000005")
        self.assertEqual(util.comment_altitude(15.24), "/A=000050")
        self.assertEqual(util.comment_altitude(152.4), "/A=000500")
        self.assertEqual(util.comment_altitude(1524), "/A=005000")
        self.assertEqual(util.comment_altitude(3048), "/A=010000")
        self.assertEqual(util.comment_altitude(6096), "/A=020000")
        self.assertEqual(util.comment_altitude(30480), "/A=100000")


