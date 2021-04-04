import unittest
import string
from random import randint, randrange, sample
from datetime import datetime

from aprslib import base91
from aprslib.parsing.common import *
from aprslib.exceptions import ParseError


class ValidateCallsign(unittest.TestCase):

    def testvalid_input(self):
        chars = string.ascii_letters.upper() + string.digits

        def randomvalid_callsigns():
            for x in range(0, 500):
                call = "".join(sample(chars, randrange(1, 6)))

                if bool(randint(0, 1)):
                    call += "-%d" % randint(0, 15)

                yield call

        for call in randomvalid_callsigns():
            try:
                validate_callsign(call)
            except ParseError:
                self.fail(
                    "%s('%s') raised ParseError" %
                    (validate_callsign.__name__, call)
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
            self.assertRaises(ParseError, validate_callsign, call)


class ParseHeader(unittest.TestCase):
    def test_no_tocall(self):
        with self.assertRaises(ParseError):
            parse_header("AAA>")
            parse_header("AAA>,")

    def testvalid_input_and_format(self):
        # empty path header
        expected = {
            "from": "A",
            "to": "B",
            "via": "",
            "path": []
            }
        result = parse_header("A>B")

        self.assertEqual(expected, result)

        # with path
        expected2 = {
            "from": "A",
            "to": "B",
            "via": "",
            "path": list('CDE')
            }
        result2 = parse_header("A>B,C,D,E")

        self.assertEqual(expected2, result2)

        # test all currently valid q-cosntructs
        expected3 = {
            "from": "A",
            "to": "B",
            "via": "E",
            "path": ['C', 'D', 'qAR', 'E']
            }
        result3 = parse_header("A>B,C,D,qAR,E")

        self.assertEqual(expected3, result3)

        for qCon in map(lambda x: "qA"+x, list("CXUoOSrRRZI")):
            expected4 = {
                "from": "A",
                "to": "B",
                "via": "C",
                "path": [qCon, 'C']
                }
            result4 = parse_header("A>B,%s,C" % qCon)

            self.assertEqual(expected4, result4)

    def testvalid_fromcallsigns(self):
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
                parse_header(head)
            except ParseError as msg:
                self.fail("{0}('{1}') PraseError, {2}"
                          .format(parse_header.__name__, head, msg))

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
                parse_header(head)
                self.fail("{0} didn't raise exception for: {1}"
                          .format(parse_header.__name__, head))
            except ParseError:
                continue


class TimestampTC(unittest.TestCase):
    def test_timestamp_invalid(self):
        body = "000000ntext"
        remaining, parsed = parse_timestamp(body)

        self.assertEqual(remaining, 'text')
        self.assertEqual(parsed, {
            'timestamp': 0,
            'raw_timestamp': '000000n',
            })

    def test_status_timestamp_invalid(self):
        body = "000000htext"
        remaining, parsed = parse_timestamp(body, '>')

        self.assertEqual(remaining, body)
        self.assertEqual(parsed, {
            'timestamp': 0,
            'raw_timestamp': '000000h',
            })

    def test_timestamp_valid(self):
        date = datetime.utcnow()
        td = date - datetime(1970, 1, 1)
        timestamp = int((td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6)

        # hhmmss format
        body = date.strftime("%H%M%Shtext")
        remaining, parsed = parse_timestamp(body)

        self.assertEqual(remaining, 'text')
        self.assertEqual(parsed, {
            'timestamp': timestamp,
            'raw_timestamp': body[:7],
            })

        # ddhhmm format
        body = date.strftime("%d%H%Mztext")
        remaining, parsed = parse_timestamp(body)

        self.assertEqual(remaining, 'text')
        self.assertEqual(parsed, {
            'timestamp': timestamp - date.second,
            'raw_timestamp': body[:7],
            })

        # ddhhmm format, local time, we parse as zulu
        body = date.strftime("%d%H%M/text")
        remaining, parsed = parse_timestamp(body)

        self.assertEqual(remaining, 'text')
        self.assertEqual(parsed, {
            'timestamp': timestamp - date.second,
            'raw_timestamp': body[:7],
            })

    def test_invalid_date(self):
        body = "999999ztext"

        remaining, parsed = parse_timestamp(body)

        self.assertEqual(remaining, 'text')
        self.assertEqual(parsed, {
            'timestamp': 0,
            'raw_timestamp': '999999z',
            })


class CommentTC(unittest.TestCase):
    def test_comment(self):
        body = "test body"
        parsed = {}
        parse_comment(body, parsed)

        self.assertEqual(parsed, {'comment': body})

        body = "/test body"
        parsed = {}
        parse_comment(body, parsed)

        self.assertEqual(parsed, {'comment': body[1:]})

        body = "  test body     "
        parsed = {}
        parse_comment(body, parsed)

        self.assertEqual(parsed, {'comment': body.strip(' ')})


class DataExtentionsTC(unittest.TestCase):
    def test_course_speed(self):
        body = "123/100/text"
        remaining, parsed = parse_data_extentions(body)

        self.assertEqual(remaining, '/text')
        self.assertEqual(parsed, {
            'course': 123,
            'speed': 100*1.852,
            })

    def test_empty_course_speed(self):
        body = "   /   /text"
        remaining, parsed = parse_data_extentions(body)

        self.assertEqual(remaining, '/text')
        self.assertEqual(parsed, {
            'course': 0,
            })

        body = ".../.../text"
        remaining, parsed = parse_data_extentions(body)

        self.assertEqual(remaining, '/text')
        self.assertEqual(parsed, {
            'course': 0,
            })

        body = "22./33 /text"
        remaining, parsed = parse_data_extentions(body)

        self.assertEqual(remaining, '/text')
        self.assertEqual(parsed, {
            'course': 0,
            })

    def test_empty_bearing_nrq(self):
        body = "111/100/   /...text"
        remaining, parsed = parse_data_extentions(body)

        self.assertEqual(remaining, 'text')
        self.assertEqual(parsed, {
            'course': 111,
            'speed': 100*1.852,
            })

        body = "111/100/2  /33.text"
        remaining, parsed = parse_data_extentions(body)

        self.assertEqual(remaining, 'text')
        self.assertEqual(parsed, {
            'course': 111,
            'speed': 100*1.852,
            })

    def test_course_speed_bearing_nrq(self):
        body = "123/100/234/345text"
        remaining, parsed = parse_data_extentions(body)

        self.assertEqual(remaining, 'text')
        self.assertEqual(parsed, {
            'course': 123,
            'speed': 100*1.852,
            'bearing': 234,
            'nrq': 345,
            })

    def test_PHG(self):
        body = "PHG1234Atext"
        remaining, parsed = parse_data_extentions(body)

        self.assertEqual(remaining, 'text')
        self.assertEqual(parsed, { 'phg': {
            'dir': 180,
            'gain': '3db',
            'haat': '12.192m',
            'period': 10,
            'power': '1W',
            'range': '8.088km'}})

        body = "PHG1234text"
        remaining, parsed = parse_data_extentions(body)

        self.assertEqual(remaining, 'text')
        self.assertEqual(parsed, { 'phg': {
            'dir': 180,
            'gain': '3db',
            'haat': '12.192m',
            'power': '1W',
            'range': '8.088km'}})

    def test_range(self):
        body = "RNG1000text"
        remaining, parsed = parse_data_extentions(body)

        self.assertEqual(remaining, 'text')
        self.assertEqual(parsed, {
            'rng': 1000*1.609344,
            })



class CommentAltitudeTC(unittest.TestCase):
    def test_valid_inputs(self):
        body = "asdasd/A=10000078zxc"
        remaining, parsed = parse_comment_altitude(body)

        self.assertEqual(remaining, "asdasd78zxc")
        self.assertEqual(parsed, {'altitude': 30480})

        body = "asdasd/A=-1000078zxc"
        remaining, parsed = parse_comment_altitude(body)

        self.assertEqual(remaining, "asdasd78zxc")
        self.assertEqual(parsed, {'altitude': -3048})

    def test_invalid(self):
        tests = [
            "",
            "aaaaaaaaaaaaaaaaaaaaa",
            "sdfsdfsdf/A=00000aaaa",
            "sdfsdfsdf/A=0000aaaaa",
            "sdfsdfsdf/A=000aaaaaa",
            "sdfsdfsdf/A=00aaaaaaa",
            "sdfsdfsdf/A=0aaaaaaaa",
            "sdfsdfsdf/A=aaaaaaaaa",
            "sdfsdfsdf/Aa000000aaa",
            "sdfsdfsdf/A=+00000aaa",
            "sdfsdfsdf/A=00a000aaa",
            ]

        for body in tests:
            remaining, parsed = parse_comment_altitude(body)
            self.assertEqual(remaining, body)
            self.assertEqual(parsed, {})


class DAO_TC(unittest.TestCase):
    def test_wgs84_human_readable(self):
        body = "!W36!"
        parsed = {'latitude': 0, 'longitude': 0}
        remaining = parse_dao(body, parsed)

        self.assertEqual(remaining, '')
        self.assertEqual(parsed, {
            'daodatumbyte': 'W',
            'latitude': 0.00005,
            'longitude': 0.0001,
            })

    def test_wgs84_human_readable_nagarive(self):
        body = "!W36!"
        parsed = {'latitude': -1, 'longitude': -1}
        remaining = parse_dao(body, parsed)

        self.assertEqual(remaining, '')
        self.assertEqual(parsed, {
            'daodatumbyte': 'W',
            'latitude': -1.00005,
            'longitude': -1.0001,
            })

    def test_wgs84_human_readable_blank(self):
        body = "!W  !"
        parsed = {'latitude': 1, 'longitude': 2}
        remaining = parse_dao(body, parsed)

        self.assertEqual(remaining, '')
        self.assertEqual(parsed, {
            'daodatumbyte': 'W',
            'latitude': 1,
            'longitude': 2,
            })

    def test_wgs84_base91(self):
        body = "!w??!"
        parsed = {'latitude': 0, 'longitude': 0}
        remaining = parse_dao(body, parsed)

        self.assertEqual(remaining, '')
        self.assertEqual(parsed, {
            'daodatumbyte': 'W',
            'latitude': 5.4945054945054945e-05,
            'longitude': 5.4945054945054945e-05,
            })

    def test_wgs84_base91_blank(self):
        body = "!w  !"
        parsed = {'latitude': 1, 'longitude': 2}
        remaining = parse_dao(body, parsed)

        self.assertEqual(remaining, '')
        self.assertEqual(parsed, {
            'daodatumbyte': 'W',
            'latitude': 1,
            'longitude': 2,
            })

    def test_dao_matching(self):
        body = "aaa!W12!bbb!W23!ccc!W45!ddd"
        parsed = {'latitude': 0, 'longitude': 0}
        remaining = parse_dao(body, parsed)

        self.assertEqual(remaining, 'aaa!W12!bbb!W23!cccddd')

    def test_other_datum_bytes(self):
        for datum in [chr(x) for x in range(0x21,0x7c)]:
            body = "!" + datum + "  !"
            parsed = {'latitude': 1, 'longitude': 2}
            remaining = parse_dao(body, parsed)

            self.assertEqual(remaining, '')
            self.assertEqual(parsed, {
                'daodatumbyte': datum.upper(),
                'latitude': 1,
                'longitude': 2,
                })
