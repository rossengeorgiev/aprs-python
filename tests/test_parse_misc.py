import unittest2 as unittest

from aprslib.parsing.misc import parse_status, parse_invalid, parse_user_defined


class MiscTC(unittest.TestCase):
    def test_status(self):
        body = "test status text  "
        _, result = parse_status('>', body)

        self.assertEqual(result['format'], 'status')
        self.assertEqual(result['status'], 'test status text')

        # with timestamp
        body = "111111ztest status text  "
        _, result = parse_status('>', body)

        self.assertEqual(result['format'], 'status')
        self.assertEqual(result['status'], 'test status text')
        self.assertTrue('timestamp' in result)

    def test_invalid(self):
        body = "invalid packet text"
        _, result = parse_invalid(body)

        self.assertEqual(result['format'], 'invalid')
        self.assertEqual(result['body'], body)

    def test_user_defined(self):
        body = "{zinvalid packet text"
        _, result = parse_user_defined(body)

        self.assertEqual(result['format'], 'user-defined')
        self.assertEqual(result['body'], body[2:])
        self.assertEqual(result['id'], body[0])
        self.assertEqual(result['type'], body[1])


