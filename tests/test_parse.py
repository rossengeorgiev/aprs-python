# encoding: utf-8

import sys
import unittest2 as unittest
from mox3 import mox

from aprslib import parse
from aprslib import parsing
from aprslib.exceptions import ParseError, UnknownFormat


def _u(text, c='utf8'):
    if sys.version_info[0] >= 3:
        return text
    else:
        return text.decode(c)


class ParseTestCase(unittest.TestCase):
    def test_unicode(self):
        _unicode = str if sys.version_info[0] >= 3 else unicode

        # 7bit ascii
        result = parse("A>B:>status")

        self.assertIsInstance(result['status'], _unicode)
        self.assertEqual(result['status'], _u("status"))

        # string with degree sign
        result = parse("A>B:>status\xb0")

        self.assertIsInstance(result['status'], _unicode)
        self.assertEqual(result['status'], _u("status\xb0", 'latin-1'))

        # str with utf8
        result = parse("A>B:>статус")

        self.assertIsInstance(result['status'], _unicode)
        self.assertEqual(result['status'], _u("статус"))

        # unicode input
        result = parse(_u("A>B:>статус"))

        self.assertIsInstance(result['status'], _unicode)
        self.assertEqual(result['status'], _u("статус"))

    def test_empty_packet(self):
        self.assertRaises(ParseError, parse, "")

    def test_no_body(self):
        self.assertRaises(ParseError, parse, "A>B")

    def test_empty_body(self):
        self.assertRaises(ParseError, parse, "A>B:")

    def testparse_header_exception(self):
        self.assertRaises(ParseError, parse, "A:asd")

    def test_empty_body_of_format_that_is_not_status(self):
        self.assertRaises(ParseError, parse, "A>B:!")

        try:
            parse("A>B:>")
        except:
            self.fail("empty status packet shouldn't raise exception")

    def test_unsupported_formats_raising(self):
        with self.assertRaises(UnknownFormat):
            for packet_type in '#$%)*,<?T[_{':
                packet = "A>B:%saaa" % packet_type

                try:
                    parse(packet)
                except UnknownFormat as exp:
                    self.assertEqual(exp.packet, packet)
                    raise


class ParseBranchesTestCase(unittest.TestCase):
    def setUp(self):
        self.m = mox.Mox()

    def tearDown(self):
        self.m.UnsetStubs()

    def test_status_format_branch(self):
        def _u(text, c='utf8'):
            if sys.version_info[0] >= 3:
                return text
            else:
                return text.decode(c)

        expected = {
            'status': 'test',
            'raw': _u('A>B:>test'),
            'via': '',
            'from': _u('A'),
            'to': _u('B'),
            'path': [],
            'format': 'status'
        }
        result = parse("A>B:>test")

        self.assertEqual(result, expected)

    def test_mice_format_branch(self):
        self.m.StubOutWithMock(parsing, "parse_mice")
        parsing.parse_mice("B", "test").AndReturn(('', {'format': ''}))
        parsing.parse_mice("D", "test").AndReturn(('', {'format': ''}))
        self.m.ReplayAll()

        parse("A>B:`test")
        parse("C>D:'test")

        self.m.VerifyAll()

    def test_message_format_branch(self):
        self.m.StubOutWithMock(parsing, "parse_message")
        parsing.parse_message("test").AndReturn(('', {'format': ''}))
        self.m.ReplayAll()

        parse("A>B::test")

        self.m.VerifyAll()


if __name__ == '__main__':
    unittest.main()
