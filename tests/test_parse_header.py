import unittest
import string
from random import randint, randrange, sample

from aprslib.parsing import _parse_header
from aprslib.parsing import _validate_callsign
from aprslib.exceptions import ParseError


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
            "from": "A",
            "to": "B",
            "via": "",
            "path": []
            }
        result = _parse_header("A>B")

        self.assertEqual(expected, result)

        # with path
        expected2 = {
            "from": "A",
            "to": "B",
            "via": "",
            "path": list('CDE')
            }
        result2 = _parse_header("A>B,C,D,E")

        self.assertEqual(expected2, result2)

        # test all currently valid q-cosntructs
        expected3 = {
            "from": "A",
            "to": "B",
            "via": "E",
            "path": ['C', 'D', 'qAR', 'E']
            }
        result3 = _parse_header("A>B,C,D,qAR,E")

        self.assertEqual(expected3, result3)

        for qCon in map(lambda x: "qA"+x, list("CXUoOSrRRZI")):
            expected4 = {
                "from": "A",
                "to": "B",
                "via": "C",
                "path": [qCon, 'C']
                }
            result4 = _parse_header("A>B,%s,C" % qCon)

            self.assertEqual(expected4, result4)

    def test_valid_fromcallsigns(self):
        testData = [
            "A>CALL",
            "4>CALL",
            "aaabbbccc>CALL",
            "AAABBBCCC>CALL",
            "AA1B2BCC9>CALL",
            "aa1b2bcc9>CALL",
            "-1>CALL",
            "-111>CALL",
            "-98765432>CALL",
            "-a>CALL",
            "-abcZZZxx>CALL",
            "a-a>CALL",
            "a-aaaaaa>CALL",
            "callsign1>CALL",
            "AAABBB-9>CALL",
            "AAABBBC-9>CALL",
            "AAABBB-S>CALL",
            "AAABBBC-S>CALL",
            ]

        for head in testData:
            try:
                _parse_header(head)
            except ParseError, msg:
                self.fail("{0}('{1}') PraseError, {2}"
                          .format(_parse_header.__name__, head, msg))

    def test_invalid_format(self):
        testData = [
            "",     # empty header
            ">CALL;>test",    # empty fromcall
            "A>:>test",   # empty tocall
            "A>-99:>test",  # invalid tocall
            "aaaAAAaaaA>CALL",  # fromcall too long
            "->CALL",  # invalid fromcall
            "A->CALL",  # invalid fromcall
            "AB->CALL",  # invalid fromcall
            "ABC->CALL",  # invalid fromcall
            "9999->CALL",  # invalid fromcall
            "999aaa11->CALL",  # invalid fromcall
            "-AAA999AAA>CALL",  # invalid fromcall, too long
            "A>aaaaaaaaaaa",  # invalid tocall
            "A>B,1234567890,C",  # invalid call in path
            "A>B,C,1234567890,D",  # invalid call in path
            "A>B,C,1234567890",  # invalid call in path
            ]

        for head in testData:
            try:
                _parse_header(head)
                self.fail("{0} didn't raise exception for: {1}"
                          .format(_parse_header.__name__, head))
            except ParseError:
                continue


if __name__ == '__main__':
    unittest.main()
