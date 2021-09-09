import re
from aprslib.parsing import logger
from aprslib.parsing.telemetry import parse_telemetry_config

__all__ = [
        'parse_message',
        ]

# MESSAGE PACKET
#
# :ADDRESSEE:Message text ........{XXXXX    Up to 5 char line number
# :ADDRESSEE:ackXXXXX                       Ack for same line number
# :ADDRESSEE:Message text ........{MM}AA    Line# with REPLY ACK
#
# TELEMETRY MESSAGES
#
# :N3MIM:PARM.Battery,BTemp,AirTemp,Pres,Altude,Camra,Chute,Sun,10m,ATV
# :N3MIM:UNIT.Volts,deg.F,deg.F,Mbar,Kfeet,Clik,OPEN!,on,on,high
# :N3MIM:EQNS.0,2.6,0,0,.53,-32,3,4.39,49,-32,3,18,1,2,3
# :N3MIM:BITS.10110101,PROJECT TITLE...
def parse_message(body):
    parsed = {}

    # the while loop is used to easily break out once a match is found
    while True:
        # try to match bulletin
        match = re.findall(r"^BLN([0-9])([a-z0-9_ \-]{5}):(.{0,67})", body, re.I)
        if match:
            bid, identifier, text = match[0]
            identifier = identifier.rstrip(' ')

            mformat = 'bulletin' if identifier == "" else 'group-bulletin'

            parsed.update({
                'format': mformat,
                'message_text': text.strip(' '),
                'bid': bid,
                'identifier': identifier
                })
            break

        # try to match announcement
        match = re.findall(r"^BLN([A-Z])([a-zA-Z0-9_ \-]{5}):(.{0,67})", body)
        if match:
            aid, identifier, text = match[0]
            identifier = identifier.rstrip(' ')

            parsed.update({
                'format': 'announcement',
                'message_text': text.strip(' '),
                'aid': aid,
                'identifier': identifier
                })
            break

        # validate addresse
        match = re.findall(r"^([a-zA-Z0-9_ \-]{9}):(.*)$", body)
        if not match:
            break

        addresse, body = match[0]

        parsed.update({'addresse': addresse.rstrip(' ')})

        # check if it's a telemetry configuration message
        body, result = parse_telemetry_config(body)
        if result:
            parsed.update(result)
            break

        # regular message
        else:
            logger.debug("Packet is just a regular message")
            parsed.update({'format': 'message'})
            has_matched = False

            # APRS supports two different message formats:
            # - the standard format which is described in 'aprs101.pdf':
            #   http://www.aprs.org/doc/APRS101.PDF
            # - an addendum from 1999 which introduces a new format:
            #   http://www.aprs.org/aprs11/replyacks.txt
            #
            # A message (ack/rej as well as a standard msg text body) can either have:
            # - no message number at all
            # - a message number in the old format (1..5 characters / digits)
            # - a message number in the new format (2 characters / digits) without trailing 'ack msg no'
            # - a message number in the new format with trailing 'free ack msg no' (2 characters / digits)

            #
            # ack / rej parser
            #
            # search for: ack/rej new format with msgNo present and ackMsgNo present
            if not has_matched:
                match = re.search(r"^(ack|rej)([A-Za-z0-9]{2})}([A-Za-z0-9]{2})$", body)
                if match:
                    parsed.update({
                        'response': match.group(1),
                        'msgNo': match.group(2),
                        'ackMsgNo': match.group(3)
                    })
                    if "message_text" in parsed:
                        parsed.pop("message_text")
                    has_matched = True

            # search for: ack/rej new format with msgNo present and ackMsgNo not present
            if not has_matched:
                match = re.search(r"^(ack|rej)([A-Za-z0-9]{2})}$", body)
                if match:
                    parsed.update({
                        'response': match.group(1),
                        'msgNo': match.group(2),
                    })
                    if "message_text" in parsed:
                        parsed.pop("message_text")
                    has_matched = True

            # search for: ack/rej standard format as per aprs101.pdf chapter 14
            match = re.search(r"^(ack|rej)([A-Za-z0-9]{1,5})$", body)
            if match:
                parsed.update({
                    'response': match.group(1),
                    'msgNo': match.group(2),
                    })
                if "message_text" in parsed:
                    parsed.pop("message_text")
                has_matched = True

            # escape from the eternal 'while'
            if has_matched:
                break

            #
            # regular message body parser
            #
            if not has_matched:
                # one-time truncate to 67 chars
                body = body[0:67].strip()

                # new message format: http://www.aprs.org/aprs11/replyacks.txt
                # search for: msgText/msgNo/ackMsgNo all present
                match = re.search(r"{([A-Za-z0-9]{2})}([A-Za-z0-9]{2})$", body)
                if match:
                    msgNo = match.group(1)
                    ackMsgNo = match.group(2)
                    body = body[:len(body) - 3 - len(msgNo) - len(ackMsgNo)]
                    parsed.update({'msgNo': msgNo})
                    parsed.update({'ackMsgNo': ackMsgNo})
                    has_matched = True

            # new message format: http://www.aprs.org/aprs11/replyacks.txt
            # search for: msgText/msgNo present and ackMsgNo not present
            if not has_matched:
                match = re.search(r"{([A-Za-z0-9]{2})}$", body)
                if match:
                    msgNo = match.group(1)
                    body = body[:len(body) - 2 - len(msgNo)]
                    parsed.update({'msgNo': msgNo})
                    has_matched = True

            # old message format - see aprs101.pdf.
            # search for: msgNo present
            if not has_matched:
                    match = re.search(r"{([A-Za-z0-9]{1,5})$", body)
                    if match:
                        msgNo = match.group(1)
                        body = body[:len(body) - 1 - len(msgNo)]
                        parsed.update({'msgNo': msgNo})
                        has_matched = True

            # update the potentially changed message body in our dictionary
            parsed.update({'message_text': body[0:67].strip()})

            # break free from the eternal 'while'
            break

    return ('', parsed)
