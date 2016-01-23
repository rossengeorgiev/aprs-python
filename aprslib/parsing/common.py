import re
import time
from datetime import datetime
from aprslib import base91
from aprslib.exceptions import ParseError
from aprslib.parsing import logger
from aprslib.parsing.telemetry import _parse_comment_telemetry

__all__ = [
    '_validate_callsign',
    '_parse_header',
    '_parse_timestamp',
    '_parse_comment',
    ]

def _validate_callsign(callsign, prefix=""):
    prefix = '%s: ' % prefix if bool(prefix) else ''

    match = re.findall(r"^([A-Z0-9]{1,6})(-(\d{1,2}))?$", callsign)

    if not match:
        raise ParseError("%sinvalid callsign" % prefix)

    callsign, _, ssid = match[0]

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

    if (not 1 <= len(fromcall) <= 9 or
       not re.findall(r"^[a-z0-9]{0,9}(\-[a-z0-9]{1,8})?$", fromcall, re.I)):

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


def _parse_timestamp(body, packet_type=''):
    parsed = {}

    match = re.findall(r"^((\d{6})(.))$", body[0:7])
    if match:
        rawts, ts, form = match[0]
        utc = datetime.utcnow()

        timestamp = 0

        if packet_type == '>' and form != 'z':
            pass
        else:
            body = body[7:]

            try:
                # zulu hhmmss format
                if form == 'h':
                    timestamp = "%d%02d%02d%s" % (utc.year, utc.month, utc.day, ts)
                # zulu ddhhmm format
                # '/' local ddhhmm format
                elif form in 'z/':
                    timestamp = "%d%02d%s%02d" % (utc.year, utc.month, ts, 0)
                else:
                    timestamp = "19700101000000"

                timestamp = utc.strptime(timestamp, "%Y%m%d%H%M%S")
                timestamp = time.mktime(timestamp.timetuple())

                parsed.update({'raw_timestamp': rawts})
            except Exception as exp:
                timestamp = 0
                logger.debug(exp)

        parsed.update({'timestamp': int(timestamp)})

    return (body, parsed)


def _parse_comment(body, parsed):
    # attempt to parse remaining part of the packet (comment field)
    # try CRS/SPD
    match = re.findall(r"^([0-9]{3})/([0-9]{3})", body)
    if match:
        cse, spd = match[0]
        body = body[7:]
        parsed.update({
            'course': int(cse),
            'speed': int(spd)*1.852  # knots to kms
            })

        # try BRG/NRQ/
        match = re.findall(r"^([0-9]{3})/([0-9]{3})", body)
        if match:
            brg, nrq = match[0]
            body = body[7:]
            parsed.update({'bearing': int(brg), 'nrq': int(nrq)})
    else:
        match = re.findall(r"^(PHG(\d[\x30-\x7e]\d\d[0-9A-Z]?))\/", body)
        if match:
            ext, phg = match[0]
            body = body[len(ext):]
            parsed.update({'phg': phg})
        else:
            match = re.findall(r"^(RNG(\d{4}))\/", body)
            if match:
                ext, rng = match[0]
                body = body[len(ext):]
                parsed.update({'rng': int(rng) * 1.609344})  # miles to km

    # try find altitude in comment /A=dddddd
    match = re.findall(r"^(.*?)/A=(\-\d{5}|\d{6})(.*)$", body)

    if match:
        body, altitude, rest = match[0]
        body += rest

        parsed.update({'altitude': int(altitude)*0.3048})

    body, telemetry = _parse_comment_telemetry(body)
    parsed.update(telemetry)

    # parse DAO extention
    body = _parse_dao(body, parsed)

    if len(body) > 0 and body[0] == "/":
        body = body[1:]

    parsed.update({'comment': body.strip(' ')})


def _parse_dao(body, parsed):
    match = re.findall("^(.*)\!([\x21-\x7b][\x20-\x7b]{2})\!(.*?)$", body)
    if match:
        body, dao, rest = match[0]
        body += rest

        parsed.update({'daodatumbyte': dao[0].upper()})

        lat_offset = lon_offset = 0

        if re.match("^[A-Z]", dao):
            lat_offset = int(dao[1]) * 0.001 / 60
            lon_offset = int(dao[2]) * 0.001 / 60
        elif re.match("^[a-z]", dao):
            lat_offset = base91.to_decimal(dao[1]) / 91.0 * 0.01 / 60
            lon_offset = base91.to_decimal(dao[2]) / 91.0 * 0.01 / 60

        parsed['latitude'] += lat_offset if parsed['latitude'] >= 0 else -lat_offset
        parsed['longitude'] += lon_offset if parsed['longitude'] >= 0 else -lon_offset

    return body
