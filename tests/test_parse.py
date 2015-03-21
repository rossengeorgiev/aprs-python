# encoding: utf-8

import unittest

from aprslib.parse import parse


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


if __name__ == '__main__':
    unittest.main()
