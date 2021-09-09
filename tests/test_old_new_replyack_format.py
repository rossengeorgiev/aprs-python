import aprslib
import logging

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


if __name__ == "__main__":

    # ack/rej assertion tests

    # erroneous rej
    packet = aprslib.parse("DF1JSL-4>APOSB,TCPIP*,qAS,DF1JSL::WXBOT    :red12345")
    assert ("msgNo" not in packet)
    assert ("ackMsgNo" not in packet)
    assert ("message_text" in packet)
    assert (packet["format"] == "message")
    assert (packet["message_text"] == "red12345")

    # reject with "old" msgno
    packet = aprslib.parse("DF1JSL-4>APOSB,TCPIP*,qAS,DF1JSL::WXBOT    :rej123")
    assert ("msgNo" in packet)
    assert ("ackMsgNo" not in packet)
    assert ("response" in packet)
    assert (packet["format"] == "message")
    assert ("message_text" not in packet)
    assert (packet["response"] == "rej")
    assert (packet["msgNo"] == "123")

    # ack with new msgNo but no ackMsgNo
    packet = aprslib.parse("DF1JSL-4>APOSB,TCPIP*,qAS,DF1JSL::WXBOT    :ackAB}")
    assert ("msgNo" in packet)
    assert ("ackMsgNo" not in packet)
    assert ("response" in packet)
    assert (packet["format"] == "message")
    assert ("message_text" not in packet)
    assert (packet["response"] == "ack")
    assert (packet["msgNo"] == "AB")

    # ack with new msgNo and ackMsgNo
    packet = aprslib.parse("DF1JSL-4>APOSB,TCPIP*,qAS,DF1JSL::WXBOT    :ackAB}CD")
    assert ("msgNo" in packet)
    assert ("ackMsgNo" in packet)
    assert ("response" in packet)
    assert (packet["format"] == "message")
    assert ("message_text" not in packet)
    assert (packet["response"] == "ack")
    assert (packet["msgNo"] == "AB")
    assert (packet["ackMsgNo"] == "CD")

    # message text body tests

    # message body without msg no
    packet = aprslib.parse("DF1JSL-4>APOSB,TCPIP*,qAS,DF1JSL::WXBOT    :HelloWorld  ")
    assert ("msgNo" not in packet)
    assert ("ackMsgNo" not in packet)
    assert ("message_text" in packet)
    assert (packet["format"] == "message")
    assert (packet["message_text"] == "HelloWorld")

    # message body with msg no - old format
    packet = aprslib.parse("DF1JSL-4>APOSB,TCPIP*,qAS,DF1JSL::WXBOT    :HelloWorld  {ABCDE")
    assert ("msgNo" in packet)
    assert ("ackMsgNo" not in packet)
    assert ("response" not in packet)
    assert (packet["format"] == "message")
    assert ("message_text" in packet)
    assert (packet["message_text"] == "HelloWorld")
    assert (packet["msgNo"] == "ABCDE")

    # message body with msgNo (new format) and ackMsgNo missing
    packet = aprslib.parse("DF1JSL-4>APOSB,TCPIP*,qAS,DF1JSL::WXBOT    :HelloWorld  {AB}")
    assert ("msgNo" in packet)
    assert ("ackMsgNo" not in packet)
    assert ("response" not in packet)
    assert (packet["format"] == "message")
    assert ("message_text" in packet)
    assert (packet["message_text"] == "HelloWorld")
    assert (packet["msgNo"] == "AB")

    # message body with msgNo and ackMsgNo (new format)
    packet = aprslib.parse("DF1JSL-4>APOSB,TCPIP*,qAS,DF1JSL::WXBOT    :HelloWorld  {AB}CD")
    assert ("msgNo" in packet)
    assert ("ackMsgNo" in packet)
    assert ("response" not in packet)
    assert (packet["format"] == "message")
    assert ("message_text" in packet)
    assert (packet["message_text"] == "HelloWorld")
    assert (packet["msgNo"] == "AB")
    assert (packet["ackMsgNo"] == "CD")

    # message body with really long message
    packet = aprslib.parse("DF1JSL-4>APOSB,TCPIP*,qAS,DF1JSL::WXBOT    :00000000001111111111222222222233333333334444444444555555555566666666667777777777")
    assert ("msgNo" not in packet)
    assert ("ackMsgNo" not in packet)
    assert ("message_text" in packet)
    assert (packet["format"] == "message")
    assert (packet["message_text"] == "0000000000111111111122222222223333333333444444444455555555556666666")
