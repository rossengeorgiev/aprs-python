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

            match = re.search(r"^(ack|rej)([A-Za-z0-9]{1,5})$", body)
            if match:
                parsed.update({
                    'response': match.group(1),
                    'msgNo': match.group(2),
                    })
            else:
                body = body[0:70]

                match = re.search(r"{([A-Za-z0-9]{1,5})$", body)
                if match:
                    msgNo = match.group(1)
                    body = body[:len(body) - 1 - len(msgNo)]

                    parsed.update({'msgNo': msgNo})

                parsed.update({'message_text': body.strip(' ')})

        break

    return ('', parsed)
