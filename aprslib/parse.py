# aprs - Python library for dealing with APRS
# Copyright (C) 2013-2014 Rossen Georgiev
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
This module contains all function used in parsing packets
"""
import time
import re
import math
import logging
from datetime import datetime

from .exceptions import (UnknownFormat, ParseError)
from . import base91

__all__ = ['parse']

logger = logging.getLogger(__name__)

# Mic-e message type table

MTYPE_TABLE_STD = {
    "111": "M0: Off Duty",
    "110": "M1: En Route",
    "101": "M2: In Service",
    "100": "M3: Returning",
    "011": "M4: Committed",
    "010": "M5: Special",
    "001": "M6: Priority",
    "000": "Emergency",
    }
MTYPE_TABLE_CUSTOM = {
    "111": "C0: Custom-0",
    "110": "C1: Custom-1",
    "101": "C2: Custom-2",
    "100": "C3: Custom-3",
    "011": "C4: Custom-4",
    "010": "C5: Custom-5",
    "001": "C6: Custom-6",
    "000": "Emergency",
    }


def parse(raw_sentence):
    """
    Parses an APRS packet and returns a dict with decoded data

     - All attributes are in meteric units

     Supports:
      * normal/compressed/mic-e position reports
        - including comment extentions for altitude and telemetry
      * messages including bulletins, announcements and telemetry
      * status message
    """

    raw_sentence = raw_sentence.rstrip("\r\n")
    logger.debug("Parsing: %s", raw_sentence)

    if len(raw_sentence) == 0:
        raise ParseError("packet is empty", raw_sentence)

    # typical packet format
    #
    #  CALL1>CALL2,CALL3,CALL4:>longtext......
    # |--------header--------|-----body-------|
    #
    try:
        (head, body) = raw_sentence.split(':', 1)
    except:
        raise ParseError("packet has no body", raw_sentence)

    if len(body) == 0:
        raise ParseError("packet body is empty", raw_sentence)

    parsed = {
        'raw': raw_sentence,
        }

    try:
        parsed.update(_parse_header(head))
    except ParseError, msg:
        raise ParseError(str(msg), raw_sentence)

    packet_type = body[0]
    body = body[1:]

    if len(body) == 0 and packet_type != '>':
        raise ParseError("packet body is empty after packet type character", raw_sentence)

    # attempt to parse the body
    # ------------------------------------------------------------------------------

    # try and parse timestamp first for status and position reports
    if packet_type in '>/@':
        # try to parse timestamp
        match = re.findall(r"^((\d{6})(.))$", body[0:7])
        if match:
            rawts, ts, form = match[0]
            utc = datetime.utcnow()

            if packet_type == '>' and form != 'z':
                raise ParseError("Time format for status reports should be zulu", raw_sentence)

            parsed.update({'raw_timestamp': rawts})

            timestamp = 0
            try:
                if form in "hz/":
                    # zulu hhmmss format
                    if form == 'h':
                        timestamp = "%s%s%s%s" % (utc.year, utc.month, utc.day, ts)
                    # zulu ddhhmm format
                    # '/' local ddhhmm format
                    elif form in 'z/':
                        timestamp = "%s%s%s%s" % (utc.year, utc.month, ts, utc.second)

                    timestamp = utc.strptime(timestamp, "%Y%m%d%H%M%S")
                    timestamp = time.mktime(timestamp.timetuple())
            except Exception as exp:
                logger.debug(exp)
                pass

            parsed.update({'timestamp': int(timestamp)})

            # remove datetime from the body for further parsing
            body = body[7:]

    # Mic-encoded packet
    #
    # 'lllc/s$/.........         Mic-E no message capability
    # 'lllc/s$/>........         Mic-E message capability
    # `lllc/s$/>........         Mic-E old posit

    if packet_type in "`'":
        logger.debug("Attempting to parse as mic-e packet")
        parsed.update({'format': 'mic-e'})

        dstcall = parsed['to'].split('-')[0]

        # verify mic-e format
        if len(dstcall) != 6:
            raise ParseError("dstcall has to be 6 characters", raw_sentence)
        if len(body) < 8:
            raise ParseError("packet data field is too short", raw_sentence)
        if not re.match(r"^[0-9A-Z]{3}[0-9L-Z]{3}$", dstcall):
            raise ParseError("invalid dstcall", raw_sentence)
        if not re.match(r"^[&-\x7f][&-a][\x1c-\x7f]{2}[\x1c-\x7d][\x1c-\x7f][\x21-\x7e][\/\\0-9A-Z]", body):
            raise ParseError("invalid data format", raw_sentence)

        # get symbol table and symbol
        parsed.update({
            'symbol': body[6],
            'symbol_table': body[7]
            })

        # parse latitude
        # the routine translates each characters into a lat digit as described in
        # 'Mic-E Destination Address Field Encoding' table
        tmpdstcall = ""
        for i in dstcall:
            if i in "KLZ":  # spaces
                tmpdstcall += " "
            elif ord(i) > 76:  # P-Y
                tmpdstcall += chr(ord(i) - 32)
            elif ord(i) > 57:  # A-J
                tmpdstcall += chr(ord(i) - 16)
            else:  # 0-9
                tmpdstcall += i

        # determine position ambiguity
        match = re.findall(r"^\d+( *)$", tmpdstcall)
        if not match:
            raise ParseError("invalid latitude ambiguity", raw_sentence)

        posambiguity = len(match[0])
        parsed.update({
            'posambiguity': posambiguity
            })

        # adjust the coordinates be in center of ambiguity box
        tmpdstcall = list(tmpdstcall)
        if posambiguity > 0:
            if posambiguity >= 4:
                tmpdstcall[2] = '3'
            else:
                tmpdstcall[6 - posambiguity] = '5'

        tmpdstcall = "".join(tmpdstcall)

        latminutes = float(("%s.%s" % (tmpdstcall[2:4], tmpdstcall[4:6])).replace(" ", "0"))

        if latminutes >= 60:
            raise ParseError("Latitude minutes >= 60", raw_sentence)

        latitude = int(tmpdstcall[0:2]) + (latminutes / 60.0)

        # determine the sign N/S
        latitude = -latitude if ord(dstcall[3]) <= 0x4c else latitude

        parsed.update({
            'latitude': latitude
            })

        # parse message bits

        mbits = re.sub(r"[0-9L]", "0", dstcall[0:3])
        mbits = re.sub(r"[P-Z]", "1", mbits)
        mbits = re.sub(r"[A-K]", "2", mbits)

        parsed.update({
            'mbits': mbits
            })

        # resolve message type

        if mbits.find("2") > -1:
            parsed.update({
                'mtype': MTYPE_TABLE_CUSTOM[mbits.replace("2", "1")]
                })
        else:
            parsed.update({
                'mtype': MTYPE_TABLE_STD[mbits]
                })

        # parse longitude

        longitude = ord(body[0]) - 28  # decimal part of longitude
        longitude += 100 if ord(dstcall[4]) >= 0x50 else 0  # apply lng offset
        longitude += -80 if longitude >= 180 and longitude <= 189 else 0
        longitude += -190 if longitude >= 190 and longitude <= 199 else 0

        # long minutes
        lngminutes = ord(body[1]) - 28.0
        lngminutes += -60 if lngminutes >= 60 else 0

        # + (long hundredths of minutes)
        lngminutes += ((ord(body[2]) - 28.0) / 100.0)

        # apply position ambiguity
        # routines adjust longitude to center of the ambiguity box
        if posambiguity is 4:
            lngminutes = 30
        elif posambiguity is 3:
            lngminutes = (math.floor(lngminutes/10) + 0.5) * 10
        elif posambiguity is 2:
            lngminutes = math.floor(lngminutes) + 0.5
        elif posambiguity is 1:
            lngminutes = (math.floor(lngminutes*10) + 0.5) / 10.0
        elif posambiguity is not 0:
            raise ParseError("Unsupported position ambiguity: %d" % posambiguity, raw_sentence)

        longitude += lngminutes / 60.0

        # apply E/W sign
        longitude = 0 - longitude if ord(dstcall[5]) >= 0x50 else longitude

        parsed.update({
            'longitude': longitude
            })

        # parse speed and course
        speed = (ord(body[3]) - 28) * 10
        course = ord(body[4]) - 28
        quotient = int(course / 10.0)
        course += -(quotient * 10)
        course = course*100 + ord(body[5]) - 28
        speed += quotient

        speed += -800 if speed >= 800 else 0
        course += -400 if course >= 400 else 0

        speed *= 1.852  # knots * 1.852 = kmph
        parsed.update({
            'speed': speed,
            'course': course
            })

        # the rest of the packet can contain telemetry and comment

        if len(body) > 8:
            body = body[8:]

            # check for optional 2 or 5 channel telemetry
            match = re.findall(r"^('[0-9a-f]{10}|`[0-9-af]{4})(.*)$", body)
            if match:
                hexdata, body = match[0]

                hexdata = hexdata[1:]           # remove telemtry flag
                channels = len(hexdata) / 2     # determine number of channels
                hexdata = int(hexdata, 16)      # convert hex to int

                telemetry = []
                for i in range(channels):
                    telemetry.insert(0, int(hexdata >> 8*i & 255))

                parsed.update({'telemetry': telemetry})

            # check for optional altitude
            match = re.findall(r"^(.*)([!-{]{3})\}(.*)$", body)
            if match:
                body, altitude, extra = match[0]

                altitude = base91.to_decimal(altitude) - 10000
                parsed.update({'altitude': altitude})

                body = body + extra

            # attempt to parsed comment telemetry
            body, telemetry = _parse_comment_telemetry(body)
            parsed.update(telemetry)

            #TODO !DAO! parsing

            # rest is a comment
            parsed.update({'comment': body.strip(' ')})

    # STATUS PACKET
    #
    # >DDHHMMzComments
    # >Comments

    elif packet_type == '>':
        logger.debug("Packet is just a status message")
        parsed.update({
            'format': 'status',
            'status': body.strip(' ')
            })

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

    elif packet_type == ':':
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
            match = re.findall(r"^BLN([A-Z])([a-zA-Z0-9 \-]{5}):(.{0,67})", body)
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
            match = re.findall(r"^([a-zA-Z0-9 \-]{9}):(.*)$", body)
            if not match:
                raise ParseError("invalid addresse in message", raw_sentence)

            addresse, body = match[0]

            parsed.update({'addresse': addresse.rstrip(' ')})

            # check if it's a telemetry configuration message
            match = re.findall(r"^(PARM|UNIT|EQNS|BITS)\.(.*)$", body)
            if match:
                logger.debug("Attempting to parse telemetry-message packet")
                form, body = match[0]

                parsed.update({'format': 'telemetry-message'})

                if form in ["PARM", "UNIT"]:
                    vals = body.split(',')[:13]

                    for val in vals:
                        if not re.match(r"^(.{1,20}|)$", val):
                            raise ParseError("incorrect format of %s (name too long?)" % form, raw_sentence)

                    defvals = [''] * 13
                    defvals[:len(vals)] = vals

                    parsed.update({
                        't%s' % form: defvals
                        })
                elif form == "EQNS":
                    eqns = body.split(',')[:15]
                    teqns = [0, 1, 0] * 5

                    for idx, val in enumerate(eqns):
                        if not re.match(r"^([-]?\d*\.?\d+|)$", val):
                            raise ParseError("value at %d is not a number in %s" % (idx+1, form), raw_sentence)
                        else:
                            try:
                                val = int(val)
                            except:
                                val = float(val) if val != "" else 0

                            teqns[idx] = val

                    # group values in 5 list of 3
                    teqns = [teqns[i*3:(i+1)*3] for i in range(5)]

                    parsed.update({
                        't%s' % form: teqns
                        })
                elif form == "BITS":
                    match = re.findall(r"^([01]{8}),(.{0,23})$", body)
                    if not match:
                        raise ParseError("incorrect format of %s (title too long?)" % form, raw_sentence)

                    bits, title = match[0]

                    parsed.update({
                        't%s' % form: bits,
                        'title': title.strip(' ')
                        })

            # regular message
            else:
                logger.debug("Packet is just a regular message")
                parsed.update({'format': 'message'})

                match = re.findall(r"^(ack|rej)\{([0-9]{1,5})$", body)
                if match:
                    response, number = match[0]

                    parsed.update({
                        'response': response,
                        'msgNo': number
                        })
                else:
                    body = body[0:70]

                    match = re.findall(r"\{([0-9]{1,5})$", body)
                    if match:
                        msgid = match[0]
                        body = body[:len(body) - 1 - len(msgid)]

                        parsed.update({'msgNo': int(msgid)})

                    parsed.update({'message_text': body.strip(' ')})

            break

    # postion report (regular or compressed)
    #
    # !DDMM.hhN/DDDMM.hhW$...                           POSIT ( no APRS)
    # =DDMM.hhN/DDDMM.hhW$...                           POSIT (APRS message capable)
    # /DDHHMM/DDMM.hhN/DDDMM.hhW$...                    Time of last fix (No APRS)
    # @DDHHMM/DDMM.hhN/DDDMM.hhW$CSE/SPD/...            Moving (with APRS)
    # @DDHHMM/DDMM.hhN/DDDMM.hhW\CSE/SPD/BRG/NRQ/....   DF report
    # ./YYYYXXXX$csT                                    Compressed (Used in any !=/@ format)

    elif packet_type in '!=/@':
        parsed.update({"messagecapable": packet_type in '@='})

        if len(body) == 0 and 'timestamp' in parsed:
            raise ParseError("invalid position report format", raw_sentence)

        # comprossed packets start with /
        if re.match(r"^[\/\\A-Za-j][!-|]{8}[!-{}][ -|]{3}", body):
            logger.debug("Attempting to parse as compressed position report")

            if len(body) < 13:
                raise ParseError("Invalid compressed packet (less than 13 characters)", raw_sentence)

            parsed.update({'format': 'compressed'})

            packet = body[:13]
            extra = body[13:]

            symbol_table = packet[0]
            symbol = packet[9]

            try:
                latitude = 90 - (base91.to_decimal(packet[1:5]) / 380926.0)
                longitude = -180 + (base91.to_decimal(packet[5:9]) / 190463.0)
            except ValueError:
                raise ParseError("invalid characters in latitude/longitude encoding")

            # parse csT

            # converts the relevant characters from base91
            c1, s1, ctype = [ord(x) - 33 for x in packet[10:13]]

            if c1 == -1:
                parsed.update({'gpsfixstatus': 1 if ctype & 0x20 == 0x20 else 0})

            if -1 in [c1, s1]:
                pass
            elif ctype & 0x18 == 0x10:
                parsed.update({'altitude': (1.002 ** (c1 * 91 + s1)) * 0.3048})
            elif c1 >= 0 and c1 <= 89:
                parsed.update({'course': 360 if c1 == 0 else c1 * 4})
                parsed.update({'speed': (1.08 ** s1 - 1) * 1.852})  # mul = convert knts to kmh
            elif c1 == 90:
                parsed.update({'radiorange': (2 * 1.08 ** s1) * 1.609344})  # mul = convert mph to kmh


        # normal position report
        else:
            logger.debug("Attempting to parse as normal position report")
            parsed.update({'format': 'uncompressed'})

            try:
                (
                    lat_deg,
                    lat_min,
                    lat_dir,
                    symbol_table,
                    lon_deg,
                    lon_min,
                    lon_dir,
                    symbol,
                    extra
                ) = re.match(r"^(\d{2})([0-9 ]{2}\.[0-9 ]{2})([NnSs])([\/\\0-9A-Z])(\d{3})([0-9 ]{2}\.[0-9 ]{2})([EeWw])([\x21-\x7e])(.*)$", body).groups()

                # TODO: position ambiguity

                # validate longitude and latitude

                if int(lat_deg) > 89 or int(lat_deg) < 0:
                    raise ParseError("latitude is out of range (0-90 degrees)", raw_sentence)
                if int(lon_deg) > 179 or int(lon_deg) < 0:
                    raise ParseError("longitutde is out of range (0-180 degrees)", raw_sentence)
                """
                f float(lat_min) >= 60:
                    raise ParseError("latitude minutes are out of range (0-60)", raw_sentence)
                if float(lon_min) >= 60:
                    raise ParseError("longitude minutes are out of range (0-60)", raw_sentence)

                the above is commented out intentionally
                apperantly aprs.fi doesn't bound check minutes
                and there are actual packets that have >60min
                i don't even know why that's the case
                """

                # convert coordinates from DDMM.MM to decimal

                latitude = int(lat_deg) + (float(lat_min) / 60.0)
                longitude = int(lon_deg) + (float(lon_min) / 60.0)

                latitude *= -1 if lat_dir in 'Ss' else 1
                longitude *= -1 if lon_dir in 'Ww' else 1

            except:
                # failed to match normal sentence sentence
                raise ParseError("invalid format", raw_sentence)

        # include symbol in the result

        parsed.update({
            'symbol': symbol,
            'symbol_table': symbol_table
            })

        # include longitude and latitude in the result

        parsed.update({'latitude': latitude, 'longitude': longitude})

        # attempt to parse remaining part of the packet (comment field)

        # try CRS/SPD/

        match = re.findall(r"^([0-9]{3})/([0-9]{3})", extra)
        if match:
            cse, spd = match[0]
            extra = extra[7:]
            parsed.update({
                'course': int(cse),
                'speed': int(spd)*1.852  # knots to kms
                })

            # try BRG/NRQ/
            match = re.findall(r"^([0-9]{3})/([0-9]{3})", extra)
            if match:
                brg, nrq = match[0]
                extra = extra[7:]
                parsed.update({'bearing': int(brg), 'nrq': int(nrq)})

        #TODO parse PHG

        # try find altitude in comment /A=dddddd
        match = re.findall(r"^(.*?)/A=(\-\d{5}|\d{6})(.*)$", extra)

        if match:
            extra, altitude, post = match[0]
            extra += post  # glue front and back part together, DONT ASK

            parsed.update({'altitude': int(altitude)*0.3048})

        extra, telemetry = _parse_comment_telemetry(extra)
        parsed.update(telemetry)

        if len(extra) > 0 and extra[0] == "/":
            extra = extra[1:]

        parsed.update({'comment': extra.strip(' ')})
    else:
        raise UnknownFormat("format is not supported", raw_sentence)

    logger.debug("Parsed ok.")
    return parsed


def _validate_callsign(callsign, prefix=""):
    prefix = '%s: ' % prefix if bool(prefix) else ''

    match = re.findall(r"^([A-Z0-9]{1,6})(-(\d{1,2}))?$", callsign)

    if not match:
        raise ParseError("%sinvalid callsign" % prefix)

    callsign, x, ssid = match[0]

    if bool(ssid) and int(ssid) > 15:
        raise ParseError("%sssid not in 0-15 range" % prefix)


def _parse_header(head):
    """
    Parses the header part of packet
    Returns a dict
    """
    #  CALL1>CALL2,CALL3,CALL4,CALL5:
    # |from-|--to-|------path-------|
    #
    try:
        (fromcall, path) = head.split('>', 1)
    except:
        raise ParseError("invalid packet header")

    # looking at aprs.fi, the rules for from/src callsign
    # are a lot looser, causing a lot of packets to fail
    # this check.
    #
    # if len(fromcall) == 0:
    #    raise ParseError("no fromcallsign in header")
    # _validate_callsign(fromcall, "fromcallsign")

    if not 1 <= len(fromcall) <= 9 or not re.findall(r"^[a-z0-9]{0,9}(\-[a-z0-9]{1,8})?$", fromcall, re.I):
        raise ParseError("fromcallsign is invalid")

    path = path.split(',')

    if len(path) < 1 or len(path[0]) == 0:
        raise ParseError("no tocallsign in header")

    tocall = path[0]
    path = path[1:]

    _validate_callsign(tocall, "tocallsign")

    for digi in path:
        if not re.findall(r"^[A-Z0-9\-]{1,9}\*?$", digi, re.I):
            raise ParseError("invalid callsign in path")

    parsed = {
        'from': fromcall,
        'to': tocall,
        'path': path,
        }

    # viacall is the callsign that gated the packet to the net
    # it's located behind the q-contructed
    #
    #  CALL1>CALL2,CALL3,qAR,CALL5:
    #  .....................|-via-|
    #
    viacall = ""
    if len(path) >= 2 and re.match(r"^q..$", path[-2]):
        viacall = path[-1]

    parsed.update({'via': viacall})

    return parsed


def _parse_comment_telemetry(text):
    """
    Looks for base91 telemetry found in comment field
    Returns [remaining_text, telemetry]
    """
    match = re.findall(r"^(.*?)\|([!-{]{4,14})\|(.*)$", text)
    if match and len(match[0][1]) % 2 == 0:
        text, telemetry, post = match[0]
        text += post

        temp = [0] * 7
        for i in range(7):
            temp[i] = base91.to_decimal(telemetry[i*2:i*2+2])

        parsed = {
            'telemetry': {
                'seq': temp[0],
                'vals': temp[1:6]
                }
            }

        if temp[6] != '':
            parsed['telemetry'].update({
                'bits': "{0:08b}".format(int(temp[6]))
                })

        return (text, parsed)
    else:
        return (text, {})
