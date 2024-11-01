import unittest
from aprslib.parsing.message import parse_message

# ack/rej assertion tests
class AckRejTests(unittest.TestCase):

    # errorneus rej
    def test_errorneus_rej(self):
        unparsed, result = parse_message("WXBOT    :red12345")
        expected = {
            'format': 'message',
            'addresse': 'WXBOT',
            'message_text': 'red12345',
        }

        self.assertEqual(unparsed, '')
        self.assertEqual(expected, result)

    # reject with "old" msgno
    def test_reject_old_msgno(self):
        unparsed, result = parse_message("WXBOT    :rej123")
        expected = {
            'format': 'message',
            'addresse': 'WXBOT',
            'msgNo': '123',
            'msgNo101': '123',
            'response': 'rej'
        }

        self.assertEqual(unparsed, '')
        self.assertEqual(expected, result)

    # ack with new msgNo but no ackMsgNo
    def test_ack_new_msgno_but_no_ack_msgno(self):
        unparsed, result = parse_message("WXBOT    :ackAB}")
        expected = {
            'format': 'message',
            'addresse': 'WXBOT',
            'response': 'ack',
            'msgNo': 'AB',
            'msgNo101': 'AB}',
            'isReplyAck': True,
        }

        self.assertEqual(unparsed, '')
        self.assertEqual(expected, result)

    # ack with new msgNo and ackMsgNo
    def test_ack_new_msgno_and_ackmsgno(self):
        unparsed, result = parse_message("WXBOT    :ackAB}CD")
        expected = {
            'format': 'message',
            'addresse': 'WXBOT',
            'response': 'ack',
            'msgNo': 'AB',
            'msgNo101': 'AB}CD',
            'ackMsgNo': 'CD',
            'isReplyAck': True,
        }

        self.assertEqual(unparsed, '')
        self.assertEqual(expected, result)

# message text body tests
class MessageTestBodyTests(unittest.TestCase):

    # message body without msg no
    def test_message_without_msgno(self):
        unparsed, result = parse_message("WXBOT    :HelloWorld  ")
        expected = {
            'format': 'message',
            'addresse': 'WXBOT',
            'message_text': 'HelloWorld',
        }

        self.assertEqual(unparsed, '')
        self.assertEqual(expected, result)

    # message body with msg no - old format
    def test_message_body_with_no_msgno_oldformat(self):
        unparsed, result = parse_message("WXBOT    :HelloWorld  {ABCDE")
        expected = {
            'format': 'message',
            'addresse': 'WXBOT',
            'message_text': 'HelloWorld',
            'msgNo': 'ABCDE',
            'msgNo101': 'ABCDE',
        }

        self.assertEqual(unparsed, '')
        self.assertEqual(expected, result)

    # message body with msgNo (new format) and ackMsgNo missing
    def test_message_body_with_msgno_and_ackmsgno_missing_newformat(self):
        unparsed, result = parse_message("WXBOT    :HelloWorld  {AB}")
        expected = {
            'format': 'message',
            'addresse': 'WXBOT',
            'message_text': 'HelloWorld',
            'msgNo': 'AB',
            'msgNo101': 'AB}',
            'isReplyAck': True,
        }

        self.assertEqual(unparsed, '')
        self.assertEqual(expected, result)

    # message body with msgNo and ackMsgNo (new format)
    def test_message_body_with_msgno_and_ackmsgno_newformat(self):
        unparsed, result = parse_message("WXBOT    :HelloWorld  {AB}CD")
        expected = {
            'format': 'message',
            'addresse': 'WXBOT',
            'message_text': 'HelloWorld',
            'msgNo': 'AB',
            'msgNo101': 'AB}CD',
            'ackMsgNo': 'CD',
            'isReplyAck': True,
        }

        self.assertEqual(unparsed, '')
        self.assertEqual(expected, result)

    # message body with really long message
    def test_message_body_with_long_message(self):
        unparsed, result = parse_message("WXBOT    :00000000001111111111222222222233333333334444444444555555555566666666667777777777")
        expected = {
            'format': 'message',
            'addresse': 'WXBOT',
            'message_text': '00000000001111111111222222222233333333334444444444555555555566666666667777777777',
        }

        self.assertEqual(unparsed, '')
        self.assertEqual(expected, result)
