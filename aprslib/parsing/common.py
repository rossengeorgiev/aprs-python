import re
from math import sqrt
from datetime import datetime
from aprslib import base91
from aprslib.exceptions import ParseError
from aprslib.parsing import logger
from aprslib.parsing.telemetry import parse_comment_telemetry

__all__ = [
    'validate_callsign',
    'parse_header',
    'parse_timestamp',
    'parse_comment',
    'parse_data_extentions',
    'parse_comment_altitude',
    'parse_comment_frequency',
    'parse_dao',
    'parse_area_data_extension',
    'parse_signpost_comment',
    ]

def validate_callsign(callsign, prefix=""):
    prefix = '%s: ' % prefix if bool(prefix) else ''

    match = re.findall(r"^([A-Z0-9]{1,6})(-(\d{1,2}))?$", callsign)

    if not match:
        raise ParseError("%sinvalid callsign" % prefix)

    callsign, _, ssid = match[0]

    if bool(ssid) and int(ssid) > 15:
        raise ParseError("%sssid not in 0-15 range" % prefix)


def parse_header(head):
    """
    Parses the header part of packet
    Returns a dict
    """
    try:
        (fromcall, path) = head.split('>', 1)
    except:
        raise ParseError("invalid packet header")

    if (not 1 <= len(fromcall) <= 9 or
       not re.findall(r"^[a-z0-9]{0,9}(\-[a-z0-9]{1,8})?$", fromcall, re.I)):

        raise ParseError("fromcallsign is invalid")

    path = path.split(',')

    if len(path[0]) == 0:
        raise ParseError("no tocallsign in header")

    tocall = path[0]
    path = path[1:]

    validate_callsign(tocall, "tocallsign")

    for digi in path:
        if not re.findall(r"^[A-Z0-9\-]{1,9}\*?$", digi, re.I):
            raise ParseError("invalid callsign in path")

    parsed = {
        'from': fromcall,
        'to': tocall,
        'path': path,
        }

    viacall = ""
    if len(path) >= 2 and re.match(r"^q..$", path[-2]):
        viacall = path[-1]

    parsed.update({'via': viacall})

    return parsed


def parse_timestamp(body, packet_type=''):
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

                td = utc.strptime(timestamp, "%Y%m%d%H%M%S") - datetime(1970, 1, 1)
                timestamp = int((td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6)
            except Exception as exp:
                timestamp = 0
                logger.debug(exp)

        parsed.update({
            'raw_timestamp': rawts,
            'timestamp': int(timestamp),
            })

    return (body, parsed)


def parse_comment(body, parsed):
    body, result = parse_data_extentions(body)
    parsed.update(result)

    body, result = parse_comment_altitude(body)
    parsed.update(result)

    body, result = parse_comment_frequency(body)
    parsed.update(result)

    body, result = parse_comment_telemetry(body)
    parsed.update(result)

    body = parse_dao(body, parsed)

    if len(body) > 0 and body[0] == "/":
        body = body[1:]

    # Strip control characters (bytes < 0x20 except tab) and trim whitespace
    body = ''.join(c for c in body if ord(c) >= 0x20 or c == '\t')
    parsed.update({'comment': body.strip()})


def parse_data_extentions(body):
    parsed = {}

    # course speed bearing nrq
    # Page 27 of the spec
    # format: 111/222/333/444text
    match = re.findall(r"^([0-9 \.]{3})/([0-9 \.]{3})", body)
    if match:
        cse, spd = match[0]
        body = body[7:]
        if cse.isdigit() and cse != "000":
            parsed.update({'course': int(cse) if 1 <= int(cse) <= 360 else 0})
        if spd.isdigit() and spd != "000":
            parsed.update({'speed': int(spd)*1.852})

        # DF Report format
        # Page 29 of teh spec
        match = re.findall(r"^/([0-9 \.]{3})/([0-9 \.]{3})", body)
        if match:
            # cse=000 means stations is fixed, Page 29 of the spec
            if cse == '000':
                parsed.update({'course': 0})
            brg, nrq = match[0]
            body = body[8:]
            if brg.isdigit():
                parsed.update({'bearing': int(brg)})
            if nrq.isdigit():
                parsed.update({'nrq': int(nrq)})
    else:
        # DFS format: DFSshgd
        match = re.findall(r"^DFS(\d)([\x30-\x7e])(\d)(\d)", body)
        if match:
            s, h, g, d = match[0]
            body = body[7:]

            height_code = ord(h) - 0x30
            height_ft = 10 * (2 ** height_code)

            directivity = int(d) * 45 if int(d) > 0 else 0

            parsed.update({
                'df_signal': int(s),
                'df_height': height_ft * 0.3048,  # meters
                'df_gain': int(g),
                'df_directivity': directivity if int(d) > 0 else 'omni',
            })
        else:
            # PHG format: PHGabcd....
            # RHGR format: RHGabcdr/....
            match = re.findall(r"^(PHG(\d[\x30-\x7e]\d\d)([0-9A-F]\/)?)", body)
            if match:
                ext, phg, phgr = match[0]
                body = body[len(ext):]
                parsed.update({
                    'phg': phg,
                    'phg_power': int(phg[0]) ** 2, # watts
                    'phg_height': (10 * (2 ** (ord(phg[1]) - 0x30))) * 0.3048, # in meters
                    'phg_gain': 10 ** (int(phg[2]) / 10.0), # dB
                    })

                phg_dir = int(phg[3])
                if phg_dir == 0:
                    phg_dir = 'omni'
                elif phg_dir == 9:
                    phg_dir = 'invalid'
                else:
                    phg_dir = 45 * phg_dir

                parsed['phg_dir'] = phg_dir
                # range in km
                parsed['phg_range'] = sqrt(2 * (parsed['phg_height'] / 0.3048)
                                           * sqrt((parsed['phg_power'] / 10.0)
                                                   * (parsed['phg_gain'] / 2.0)
                                                  )
                                           ) * 1.60934

                if phgr:
                    # PHG rate per hour
                    parsed['phg'] += phgr[0]
                    parsed.update({'phg_rate': int(phgr[0], 16)}) # as decimal
            else:
                match = re.findall(r"^RNG(\d{4})", body)
                if match:
                    rng = match[0]
                    body = body[7:]
                    parsed.update({'rng': int(rng) * 1.609344})  # miles to km

    return body, parsed

def parse_comment_altitude(body):
    parsed = {}
    match = re.findall(r"^(.*?)/A=(\-\d{5}|\d{6})(.*)$", body)
    if match:
        body, altitude, rest = match[0]
        body += rest
        parsed.update({'altitude': int(altitude)*0.3048})

    return body, parsed


def parse_comment_frequency(body):
    """
    Extract frequency/tone/offset info from position comment.
    APRS 1.2 frequency spec format.
    """
    parsed = {}

    # Match frequency: FFF.FFFMHz or FFF.FF MHz (case-insensitive)
    freq_match = re.match(r'^(\d{3}\.\d{2,3})\s?[Mm][Hh][Zz]', body)
    if not freq_match:
        return (body, parsed)

    parsed['frequency'] = float(freq_match.group(1))
    body = body[freq_match.end():]

    # Parse optional tone: Tnnn or tnnn (lowercase = narrow)
    tone_match = re.match(r'^\s+[Tt](\d{3})', body)
    if tone_match:
        parsed['tone'] = int(tone_match.group(1))
        body = body[tone_match.end():]

    # Parse optional DCS: Dnnn
    dcs_match = re.match(r'^\s+[Dd](\d{3})', body)
    if dcs_match:
        parsed['dcs'] = int(dcs_match.group(1))
        body = body[dcs_match.end():]

    # Parse optional offset: +nnn or -nnn (in 10s of KHz)
    offset_match = re.match(r'^\s+([+-]\d{3})', body)
    if offset_match:
        parsed['offset'] = int(offset_match.group(1)) * 10  # convert to KHz
        body = body[offset_match.end():]

    # Parse optional range: Rnnm or Rnnk
    range_match = re.match(r'^\s+[Rr](\d{2,3})([mk])', body)
    if range_match:
        range_val = int(range_match.group(1))
        range_unit = range_match.group(2)
        if range_unit == 'm':
            parsed['range'] = range_val * 1.609344  # miles to km
        else:
            parsed['range'] = float(range_val)
        body = body[range_match.end():]

    return (body, parsed)


def parse_dao(body, parsed):
    match = re.findall("^(.*)\!([\x21-\x7b])([\x20-\x7b]{2})\!(.*?)$", body)
    if match:
        body, daobyte, dao, rest = match[0]
        body += rest

        parsed.update({'daodatumbyte': daobyte.upper()})
        lat_offset = lon_offset = 0

        if daobyte == 'W' and dao.isdigit():
            lat_offset = int(dao[0]) * 0.001 / 60
            lon_offset = int(dao[1]) * 0.001 / 60
        elif daobyte == 'w' and ' ' not in dao:
            lat_offset = (base91.to_decimal(dao[0]) / 91.0) * 0.01 / 60
            lon_offset = (base91.to_decimal(dao[1]) / 91.0) * 0.01 / 60

        parsed['latitude'] += lat_offset if parsed['latitude'] >= 0 else -lat_offset
        parsed['longitude'] += lon_offset if parsed['longitude'] >= 0 else -lon_offset

    return body


AREA_TYPES = {
    0: 'circle', 1: 'line', 2: 'ellipse', 3: 'triangle', 4: 'rectangle',
    5: 'circle', 6: 'line', 7: 'ellipse', 8: 'triangle', 9: 'rectangle',
}

AREA_COLORS = {
    0: 'black', 1: 'blue', 2: 'green', 3: 'cyan',
    4: 'red', 5: 'violet', 6: 'yellow', 7: 'grey',
}


def parse_area_data_extension(body):
    """Parse area object data extension. Format: Tyy/Cxx"""
    parsed = {}
    match = re.match(r'^(\d)(\d{2})/(\d)(\d{2})', body)
    if match:
        type_id = int(match.group(1))
        lat_offset = int(match.group(2))
        color_id = int(match.group(3))
        lon_offset = int(match.group(4))
        body = body[7:]

        parsed['area_object'] = {
            'type': AREA_TYPES.get(type_id, 'unknown'),
            'type_id': type_id,
            'filled': type_id >= 5,
            'color': AREA_COLORS.get(color_id, 'unknown'),
            'color_id': color_id,
            'lat_offset': lat_offset / 60.0,
            'lon_offset': lon_offset / 60.0,
        }
    return (body, parsed)


def parse_signpost_comment(body):
    """Parse signpost object comment. Format: SSS/DDD text"""
    parsed = {}
    match = re.match(r'^(\d{3})/(\d{3})\s*(.*)', body)
    if match:
        speed_mph = int(match.group(1))
        bearing = int(match.group(2))
        text = match.group(3)
        parsed['signpost'] = {
            'speed': speed_mph * 1.609344,
            'speed_mph': speed_mph,
            'bearing': bearing,
            'text': text.strip(),
        }
        body = ''
    return (body, parsed)
