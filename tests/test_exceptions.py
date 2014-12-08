
import unittest

from aprs.exceptions import *


class TestExceptions(unittest.TestCase):
    def test_exception_correctness(self):

        # GenericErrror
        excpInst = GenericError("test")

        self.assertIsInstance(excpInst, Exception)
        self.assertEqual(str(excpInst), "test")

        # UnknownFormat
        excpInst = UnknownFormat("test", "packet")

        self.assertIsInstance(excpInst, GenericError)
        self.assertEqual(str(excpInst), "test")
        self.assertEqual(excpInst.packet, "packet")

        # ParseError
        excpInst = ParseError("test", "packet")

        self.assertIsInstance(excpInst, GenericError)
        self.assertEqual(str(excpInst), "test")
        self.assertEqual(excpInst.packet, "packet")

        # LoginError
        excpInst = LoginError("test")

        self.assertIsInstance(excpInst, GenericError)
        self.assertEqual(str(excpInst), "test")

        # ConnectionError
        excpInst = ConnectionError("test")

        self.assertIsInstance(excpInst, GenericError)

        # ConnectionDrop
        excpInst = ConnectionDrop("test")

        self.assertIsInstance(excpInst, GenericError)
