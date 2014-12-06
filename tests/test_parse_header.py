import unittest
import string
from random import randint, randrange, sample

from aprs.parse import _parse_header
from aprs.parse import _validate_callsign
from aprs.exceptions import ParseError


class ValidateCallsign(unittest.TestCase):

    def test_valid_input(self):
        chars = string.letters.upper() + string.digits

        def random_valid_callsigns():
            for x in xrange(0, 500):
                call = "".join(sample(chars, randrange(1, 6)))

                if bool(randint(0, 1)):
                    call += "-%d" % randint(0, 15)

                yield call

        for call in random_valid_callsigns():
            try:
                _validate_callsign(call)
            except ParseError:
                self.fail(
                    "%s('%s') raised ParseError" %
                    (_validate_callsign.__name__, call)
                    )

    def test_invalid_input(self):
        testData = [
            "",
            "-",
            "-1",
            "---1",
            "1234567",
            "CALL-",
            "CALL-16",
            "CALLCALL",
            ]

        for call in testData:
            self.assertRaises(ParseError, _validate_callsign, call)


class ParseHeader(unittest.TestCase):

    def test_valid_input_and_format(self):
        # empty path header
        expected = {
            "to": "B",
            "from": "A",
            "via": "",
            "path": []
            }
        result = _parse_header("A>B")

        self.assertEqual(expected, result)

        # with path
        expected2 = {
            "to": "B",
            "from": "A",
            "via": "",
            "path": list('CDE')
            }
        result2 = _parse_header("A>B,C,D,E")

        self.assertEqual(expected2, result2)

        # test all currently valid q-cosntructs

        for qCon in map(lambda x: "qA"+x, list("CXUoOSrRRZI")):
            expected3 = {
                "to": "B",
                "from": "A",
                "via": "D",
                "path": ['C', qCon, 'D']
                }
            result3 = _parse_header("A>B,C,%s,D" % qCon)

            self.assertEqual(expected3, result3)

    def test_invalid_format(self):
        testData = [
            "",     # empty header
            ">",    # empty fromcall
            "A>",   # empty tocall
            "A>b",  # invalid tocall
            "aaaaaaaaaaa",  # invalid fromcall
            "A>aaaaaaaaaaa",  # invalid tocall
            "A>B,1234567890,C",  # invalid call in path
            "A>B,C,1234567890,D",  # invalid call in path
            "A>B,C,1234567890",  # invalid call in path
            ]

        for head in testData:
            self.assertRaises(ParseError, _parse_header, head)

if __name__ == '__main__':
    unittest.main()
