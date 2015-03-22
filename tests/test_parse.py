# encoding: utf-8

import unittest
import mox

from aprslib import parse
from aprslib import parsing
from aprslib.exceptions import ParseError, UnknownFormat


class ParseTestCase(unittest.TestCase):
    def test_unicode(self):
        # 7bit ascii
        result = parse("A>B:>status")

        self.assertIsInstance(result['status'], unicode)
        self.assertEqual(result['status'], u"status")

        # string with degree sign
        result = parse("A>B:>status\xb0")

        self.assertIsInstance(result['status'], unicode)
        self.assertEqual(result['status'], u"status\xb0")

        # str with unicode
        result = parse("A>B:>статус")

        self.assertIsInstance(result['status'], unicode)
        self.assertEqual(result['status'], u"статус")

        # uncide input
        result = parse(u"A>B:>статус")

        self.assertIsInstance(result['status'], unicode)
        self.assertEqual(result['status'], u"статус")

    def test_empty_packet(self):
        self.assertRaises(ParseError, parse, "")

    def test_no_body(self):
        self.assertRaises(ParseError, parse, "A>B")

    def test_empty_body(self):
        self.assertRaises(ParseError, parse, "A>B:")

    def test_parse_header_exception(self):
        self.assertRaises(ParseError, parse, "A:asd")

    def test_empty_body_of_format_that_is_not_status(self):
        self.assertRaises(ParseError, parse, "A>B:!")

        try:
            parse("A>B:>")
        except:
            self.fail("empty status packed shouldn't raise exception")

    def test_unsupported_formats_raising(self):
        with self.assertRaises(UnknownFormat):
            for packet_type in '#$%)*,<?T[_{}':
                parse("A>B:%saaa" % packet_type)


class ParseBranchesTestCase(unittest.TestCase):
    def setUp(self):
        self.m = mox.Mox()

    def tearDown(self):
        self.m.UnsetStubs()

    def test_status_format_branch(self):
        self.m.StubOutWithMock(parsing, "_parse_timestamp")
        parsing._parse_timestamp(mox.IgnoreArg(), mox.IgnoreArg()).AndReturn(("test", {}))
        self.m.ReplayAll()

        expected = {
            'status': 'test',
            'raw': u'A>B:>test',
            'via': '',
            'from': u'A',
            'to': u'B',
            'path': [],
            'format': 'status'
        }
        result =  parse("A>B:>test")

        self.assertEqual(result, expected)
        self.m.VerifyAll()

    def test_mice_format_branch(self):
        self.m.StubOutWithMock(parsing, "_parse_mice")
        parsing._parse_mice("B","test").AndReturn(('', {'format':''}))
        parsing._parse_mice("D","test").AndReturn(('', {'format':''}))
        self.m.ReplayAll()

        parse("A>B:`test")
        parse("C>D:'test")

        self.m.VerifyAll()

    def test_message_format_branch(self):
        self.m.StubOutWithMock(parsing, "_parse_message")
        parsing._parse_message("test").AndReturn(('', {'format':''}))
        self.m.ReplayAll()

        parse("A>B::test")

        self.m.VerifyAll()


if __name__ == '__main__':
    unittest.main()
