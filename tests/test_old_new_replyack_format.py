import unittest
from aprslib.parsing.message import parse_message

# ack/rej assertion tests
class AckRejTests(unittest.TestCase):

    # errorneus rej
    def test_errorneus_rej(self):
        with self.assertRaises(AssertionError):
            packet = parse_message("DF1JSL-4>APOSB,TCPIP*,qAS,DF1JSL::WXBOT    :red12345")
            assert ("msgNo" not in packet)
            assert ("ackMsgNo" not in packet)
            assert ("message_text" in packet)
            assert (packet["format"] == "message")
            assert (packet["message_text"] == "red12345")

    # reject with "old" msgno
    def test_reject_old_msgno(self):
        with self.assertRaises(AssertionError):
            packet = parse_message("DF1JSL-4>APOSB,TCPIP*,qAS,DF1JSL::WXBOT    :rej123")
            assert ("msgNo" in packet)
            assert ("ackMsgNo" not in packet)
            assert ("response" in packet)
            assert (packet["format"] == "message")
            assert ("message_text" not in packet)
            assert (packet["response"] == "rej")
            assert (packet["msgNo"] == "123")

    # ack with new msgNo but no ackMsgNo
    def test_ack_new_msgno_but_no_ack_msgno(self):
        with self.assertRaises(AssertionError):
            packet = parse_message("DF1JSL-4>APOSB,TCPIP*,qAS,DF1JSL::WXBOT    :ackAB}")
            assert ("msgNo" in packet)
            assert ("ackMsgNo" not in packet)
            assert ("response" in packet)
            assert (packet["format"] == "message")
            assert ("message_text" not in packet)
            assert (packet["response"] == "ack")
            assert (packet["msgNo"] == "AB")

    # ack with new msgNo and ackMsgNo
    def test_ack_new_msgno_and_ackmsgno(self):
        with self.assertRaises(AssertionError):
            packet = parse_message("DF1JSL-4>APOSB,TCPIP*,qAS,DF1JSL::WXBOT    :ackAB}CD")
            assert ("msgNo" in packet)
            assert ("ackMsgNo" in packet)
            assert ("response" in packet)
            assert (packet["format"] == "message")
            assert ("message_text" not in packet)
            assert (packet["response"] == "ack")
            assert (packet["msgNo"] == "AB")
            assert (packet["ackMsgNo"] == "CD")

# message text body tests
class MessageTestBodyTests(unittest.TestCase):

    # message body without msg no
    def test_message_without_msgno(self):
        with self.assertRaises(AssertionError):
            packet = parse_message("DF1JSL-4>APOSB,TCPIP*,qAS,DF1JSL::WXBOT    :HelloWorld  ")
            assert ("msgNo" not in packet)
            assert ("ackMsgNo" not in packet)
            assert ("message_text" in packet)
            assert (packet["format"] == "message")
            assert (packet["message_text"] == "HelloWorld")

    # message body with msg no - old format
    def test_message_body_with_no_msgno_oldformat(self):
        with self.assertRaises(AssertionError):
            packet = parse_message("DF1JSL-4>APOSB,TCPIP*,qAS,DF1JSL::WXBOT    :HelloWorld  {ABCDE")
            assert ("msgNo" in packet)
            assert ("ackMsgNo" not in packet)
            assert ("response" not in packet)
            assert (packet["format"] == "message")
            assert ("message_text" in packet)
            assert (packet["message_text"] == "HelloWorld")
            assert (packet["msgNo"] == "ABCDE")

    # message body with msgNo (new format) and ackMsgNo missing
    def test_message_body_with_msgno_and_ackmsgno_missing_newformat(self):
        with self.assertRaises(AssertionError):
            packet = parse_message("DF1JSL-4>APOSB,TCPIP*,qAS,DF1JSL::WXBOT    :HelloWorld  {AB}")
            assert ("msgNo" in packet)
            assert ("ackMsgNo" not in packet)
            assert ("response" not in packet)
            assert (packet["format"] == "message")
            assert ("message_text" in packet)
            assert (packet["message_text"] == "HelloWorld")
            assert (packet["msgNo"] == "AB")

    # message body with msgNo and ackMsgNo (new format)
    def test_message_body_with_msgno_and_ackmsgno_newformat(self):
        with self.assertRaises(AssertionError):
            packet = parse_message("DF1JSL-4>APOSB,TCPIP*,qAS,DF1JSL::WXBOT    :HelloWorld  {AB}CD")
            assert ("msgNo" in packet)
            assert ("ackMsgNo" in packet)
            assert ("response" not in packet)
            assert (packet["format"] == "message")
            assert ("message_text" in packet)
            assert (packet["message_text"] == "HelloWorld")
            assert (packet["msgNo"] == "AB")
            assert (packet["ackMsgNo"] == "CD")

    # message body with really long message
    def test_message_body_with_long_message(self):
        with self.assertRaises(AssertionError):
            packet = parse_message("DF1JSL-4>APOSB,TCPIP*,qAS,DF1JSL::WXBOT    :00000000001111111111222222222233333333334444444444555555555566666666667777777777")
            assert ("msgNo" not in packet)
            assert ("ackMsgNo" not in packet)
            assert ("message_text" in packet)
            assert (packet["format"] == "message")
            assert (packet["message_text"] == "0000000000111111111122222222223333333333444444444455555555556666666")
