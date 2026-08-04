# aprslib - Python library for working with APRS
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
import re
import logging

logger = logging.getLogger(__name__)

try:
    import chardet
except ImportError:
    # create fake chardet

    class chardet:
        @staticmethod
        def detect(x):
            return {'confidence': 0.0, 'encoding': 'windows-1252'}

from aprslib import string_type_parse
from aprslib.exceptions import (UnknownFormat, ParseError)
from aprslib.parsing.common import *
from aprslib.parsing.misc import *
from aprslib.parsing.position import *
from aprslib.parsing.mice import *
from aprslib.parsing.message import *
from aprslib.parsing.telemetry import *
from aprslib.parsing.thirdparty import *
from aprslib.parsing.weather import *
from aprslib.parsing.query import *
from aprslib.parsing.nws import *
from aprslib.parsing.peetbros import *
from aprslib.parsing.dx import *

unsupported_formats = {
        '%':'agrelo',
        '&':'reserved',
        '(':'unused',
        '+':'reserved',
        '-':'unused',
        '.':'reserved',

        '\\':'unused',
        ']':'unused',
        '^':'unused',
}

def _unicode_packet(packet):
    # attempt utf-8
    try:
        return packet.decode('utf-8')
    except UnicodeDecodeError:
        pass

    # attempt to detect encoding
    res = chardet.detect(packet.split(b':', 1)[-1])
    if res['confidence'] > 0.7 and res['encoding'] != 'EUC-TW':
        try:
            return packet.decode(res['encoding'])
        except UnicodeDecodeError:
            pass

    # if everything fails
    return packet.decode('latin-1')


def parse(packet):
    """
    Parses an APRS packet and returns a dict with decoded data

    - All attributes are in metric units
    """

    if not isinstance(packet, string_type_parse):
        raise TypeError("Expected packet to be str/unicode/bytes, got %s", type(packet))

    if len(packet) == 0:
        raise ParseError("packet is empty", packet)

    # attempt to detect encoding
    if isinstance(packet, bytes):
        packet = _unicode_packet(packet)

    packet = packet.rstrip("\r\n")
    logger.debug("Parsing: %s", packet)

    # split into head and body
    try:
        (head, body) = packet.split(':', 1)
    except:
        raise ParseError("packet has no body", packet)

    if len(body) == 0:
        raise ParseError("packet body is empty", packet)

    parsed = {
        'raw': packet,
        }

    # parse head
    try:
        parsed.update(parse_header(head))
    except ParseError as msg:
        raise ParseError(str(msg), packet)

    # parse body
    packet_type = body[0]
    body = body[1:]

    if len(body) == 0 and packet_type not in '><$[':
        raise ParseError("packet body is empty after packet type character", packet)

    # attempt to parse the body
    try:
        _try_toparse_body(packet_type, body, parsed)

    # capture ParseErrors and attach the packet
    except (UnknownFormat, ParseError) as exp:
        exp.packet = packet
        raise

    # if we fail all attempts to parse, try beacon packet
    if 'format' not in parsed:
        if not re.match(r"^(AIR.*|ALL.*|AP.*|BEACON|CQ.*|GPS.*|DF.*|DGPS.*|"
                        "DRILL.*|DX.*|ID.*|JAVA.*|MAIL.*|MICE.*|QST.*|QTH.*|"
                        "RTCM.*|SKY.*|SPACE.*|SPC.*|SYM.*|TEL.*|TEST.*|TLM.*|"
                        "WX.*|ZIP.*|UIDIGI)$", parsed['to']):
            raise UnknownFormat("format is not supported", packet)

        parsed.update({
            'format': 'beacon',
            'text': packet_type + body,
            })

    logger.debug("Parsed ok.")
    return parsed


def _try_toparse_body(packet_type, body, parsed):
    result = {}

    # DX spot: check full body (packet_type + body) for "DX de" pattern
    # before normal DTI dispatch (per FAP.pm behavior)
    full_body = packet_type + body
    if re.match(r'^DX\s+de\s+', full_body, re.IGNORECASE):
        logger.debug("Attempting to parse as DX spot")
        _, result = parse_dx(full_body)
        parsed.update(result)
        return

    if packet_type in unsupported_formats:
        raise UnknownFormat("Format is not supported: '{}' {}".format(packet_type, unsupported_formats[packet_type]))

    # 3rd party traffic
    elif packet_type == '}':
        logger.debug("Packet is third-party")
        body, result = parse_thirdparty(body)

    # user defined
    elif packet_type == ',':
        logger.debug("Packet is invalid format")

        body, result = parse_invalid(body)

    # user defined
    elif packet_type == '{':
        logger.debug("Packet is user-defined")

        body, result = parse_user_defined(body)

    # General query
    elif packet_type == '?':
        logger.debug("Attempting to parse as query packet")

        body, result = parse_query(body)

    # Status report
    elif packet_type == '>':
        logger.debug("Packet is just a status message")

        body, result = parse_status(packet_type, body)

    # Mic-encoded packet
    elif packet_type in "`'":
        logger.debug("Attempting to parse as mic-e packet")

        body, result = parse_mice(parsed['to'], body)

    # Peet Bros raw weather report
    elif packet_type == '#':
        logger.debug("Attempting to parse as Peet Bros raw weather")
        body, result = parse_peetbros(body)

    # Message packet
    elif packet_type == ':':
        logger.debug("Attempting to parse as message packet")

        body, result = parse_message(body)

    # Positionless weather report
    elif packet_type == '_':
        logger.debug("Attempting to parse as positionless weather report")

        body, result = parse_weather(body)

    # Telemetry report
    elif packet_type == 'T':
        logger.debug("Attempting to parse as telemetry report")

        body, result = parse_telemetry_report(body)

    # Station capabilities
    elif packet_type == '<':
        logger.debug("Attempting to parse as station capabilities")

        body, result = parse_station_capabilities(body)

    # Raw GPS
    elif packet_type == '$':
        logger.debug("Attempting to parse as raw GPS")

        body, result = parse_raw_gps(body)

    # Maidenhead locator beacon
    elif packet_type == '[':
        logger.debug("Attempting to parse as maidenhead locator beacon")

        body, result = parse_maidenhead_locator(body)

    # Item report
    elif packet_type == ')':
        logger.debug("Attempting to parse as item report")

        body, result = parse_position(packet_type, body)

    # Complete weather report (position report with weather data)
    elif packet_type == '*':
        logger.debug("Attempting to parse as complete weather report (position)")

        body, result = parse_position(packet_type, body)

    # postion report (regular or compressed)
    # Check for Peet Bros !! logging frame first (packet_type=! and body starts with !)
    elif packet_type == '!' and body and body[0] == '!':
        logger.debug("Attempting to parse as Peet Bros !! logging frame")
        body, result = parse_peetbros_logging(body[1:])

    elif (packet_type in '!=/@;' or
          0 <= body.find('!') < 40):  # page 28 of spec (PDF)

        body, result = parse_position(packet_type, body)

    # we are done
    parsed.update(result)

