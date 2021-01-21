import unittest
from aprslib import passcode


class TC_pascode(unittest.TestCase):
    def test_nonstring(self):
        with self.assertRaises(AssertionError):
            passcode(5)

    def test_valid_input(self):
        testData = [
            ['TESTCALL', 31742],
            ['testcall', 31742],
            ['tEsTcAlL', 31742],
            ['tEsTcAlL', 31742],
            ['TESTCALL-', 31742],
            ['TESTCALL-12', 31742],
            ['TESTCALL-0', 31742],
            ['N0CALL', 13023],
            ['SUCHCALL', 27890],
            ['MUCHSIGN', 27128],
            ['WOW', 29613],
            ]

        results = []

        for callsign, x in testData:
            results.append([callsign, passcode(callsign)])

        self.assertEqual(testData, results)
