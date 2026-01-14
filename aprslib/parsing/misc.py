import re
from aprslib.exceptions import ParseError
from aprslib.parsing.common import parse_timestamp

__all__ = [
        'parse_status',
        'parse_invalid',
        'parse_user_defined',
        'parse_station_capabilities',
        'parse_raw_gps',
        'parse_maidenhead_locator',
        ]


# STATUS PACKET
#
# >DDHHMMzComments
# >Comments
def parse_status(packet_type, body):
    body, result = parse_timestamp(body, packet_type)

    result.update({
        'format': 'status',
        'status': body.strip(' ')
        })

    return (body, result)


# INVALID
#
# ,.........................
def parse_invalid(body):
    return ('', {
        'format': 'invalid',
        'body': body
        })


# USER DEFINED
#
# {A1................
# {{.................
def parse_user_defined(body):
    return ('', {
        'format': 'user-defined',
        'id': body[0],
        'type': body[1],
        'body': body[2:],
        })


# STATION CAPABILITIES
#
# <IGATE,MSG_CNT=n,LOC_CNT=n
# Format: <TOKEN,TOKEN=VALUE,TOKEN=VALUE,...
def parse_station_capabilities(body):
    """
    Parses APRS station capabilities format: <TOKEN,TOKEN=VALUE,TOKEN=VALUE,...

    Format:
    - < indicates station capabilities packet
    - Comma-separated list of capabilities
    - Each capability can be:
      - TOKEN (e.g., "IGATE")
      - TOKEN=VALUE (e.g., "MSG_CNT=123", "LOC_CNT=5")

    Returns (remaining_body, parsed_dict)
    """
    parsed = {
        'format': 'station-capabilities',
        'capabilities': {}
    }

    if not body:
        return ('', parsed)

    # Split by comma to get individual capabilities
    capabilities = body.split(',')

    for cap in capabilities:
        cap = cap.strip()
        if not cap:
            continue

        # Check if it's TOKEN=VALUE format
        if '=' in cap:
            parts = cap.split('=', 1)
            if len(parts) != 2:
                continue

            token = parts[0].strip()
            value = parts[1].strip()

            # Try to convert value to number if possible
            try:
                # Try integer first
                if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                    value = int(value)
                else:
                    # Try float
                    try:
                        value = float(value)
                    except ValueError:
                        pass  # Keep as string
            except (ValueError, AttributeError):
                pass  # Keep as string

            parsed['capabilities'][token] = value
        else:
            # It's just a TOKEN (boolean capability)
            parsed['capabilities'][cap] = True

    return ('', parsed)


# RAW GPS
#
# $GPRMC,...
# $GPGGA,...
# $ULTW...
# Format: $<FORMAT><DATA>
def parse_raw_gps(body):
    """
    Parses APRS raw GPS format: $<FORMAT><DATA>

    Format:
    - $ indicates raw GPS/data packet
    - Can be NMEA sentences (e.g., $GPRMC, $GPGGA, $GPGLL)
    - Can be proprietary formats (e.g., $ULTW for weather)
    - Data can be comma-separated (NMEA) or hex-encoded

    Returns (remaining_body, parsed_dict)
    """
    parsed = {
        'format': 'raw-gps',
        'raw_data': body
    }

    if not body:
        return ('', parsed)

    # Try to identify the format
    # NMEA sentences start with GP, GL, GN, etc. followed by sentence type (note: $ is already stripped)
    nmea_match = re.match(r'^([A-Z]{2})([A-Z]{3,5})(,.*)?$', body)
    if nmea_match:
        talker_id = nmea_match.group(1)  # GP, GL, GN, etc.
        sentence_type = nmea_match.group(2)  # RMC, GGA, GLL, etc.
        data = nmea_match.group(3) if nmea_match.group(3) else ''

        # Clean the data (remove leading comma, strip checksum if present)
        clean_data = data.lstrip(',') if data else ''
        # Remove checksum if present (format: *HH)
        if '*' in clean_data:
            clean_data = clean_data[:clean_data.rfind('*')]

        parsed.update({
            'nmea_talker': talker_id,
            'nmea_sentence': sentence_type,
            'nmea_data': clean_data
        })

        # Try to parse common NMEA sentences
        if sentence_type == 'RMC' and clean_data:
            # Recommended Minimum Course
            # Format: $GPRMC,hhmmss.ss,A,llll.ll,a,yyyyy.yy,a,x.x,x.x,ddmmyy,x.x,a*hh
            parts = clean_data.split(',')
            if len(parts) >= 10:
                try:
                    time_str = parts[0] if parts[0] else None
                    status = parts[1] if len(parts) > 1 else None
                    lat_str = parts[2] if len(parts) > 2 else None
                    lat_dir = parts[3] if len(parts) > 3 else None
                    lon_str = parts[4] if len(parts) > 4 else None
                    lon_dir = parts[5] if len(parts) > 5 else None
                    speed = parts[6] if len(parts) > 6 else None
                    course = parts[7] if len(parts) > 7 else None
                    date_str = parts[8] if len(parts) > 8 else None

                    if lat_str and lat_dir and lon_str and lon_dir:
                        # Parse latitude (DDMM.MMMM format)
                        lat_deg = float(lat_str[:2])
                        lat_min = float(lat_str[2:])
                        latitude = lat_deg + lat_min / 60.0
                        if lat_dir == 'S':
                            latitude = -latitude

                        # Parse longitude (DDDMM.MMMM format)
                        lon_deg = float(lon_str[:3])
                        lon_min = float(lon_str[3:])
                        longitude = lon_deg + lon_min / 60.0
                        if lon_dir == 'W':
                            longitude = -longitude

                        parsed.update({
                            'latitude': latitude,
                            'longitude': longitude,
                        })

                        if speed:
                            try:
                                parsed['speed'] = float(speed) * 1.852  # knots to km/h
                            except (ValueError, TypeError):
                                pass

                        if course:
                            try:
                                parsed['course'] = float(course)
                            except (ValueError, TypeError):
                                pass

                        if time_str and date_str:
                            try:
                                # Combine date and time for timestamp
                                # Format: hhmmss.ss and ddmmyy
                                parsed['nmea_time'] = time_str
                                parsed['nmea_date'] = date_str
                            except (ValueError, TypeError):
                                pass

                        if status:
                            parsed['gps_status'] = status  # A = valid, V = invalid
                except (ValueError, IndexError, AttributeError):
                    pass  # If parsing fails, just store raw data

        elif sentence_type == 'GGA' and clean_data:
            # Global Positioning System Fix Data
            # Format: $GPGGA,hhmmss.ss,llll.ll,a,yyyyy.yy,a,x,xx,x.x,x.x,M,x.x,M,x.x,xxxx*hh
            parts = clean_data.split(',')
            if len(parts) >= 10:
                try:
                    time_str = parts[0] if parts[0] else None
                    lat_str = parts[1] if len(parts) > 1 else None
                    lat_dir = parts[2] if len(parts) > 2 else None
                    lon_str = parts[3] if len(parts) > 3 else None
                    lon_dir = parts[4] if len(parts) > 4 else None
                    fix_quality = parts[5] if len(parts) > 5 else None
                    num_satellites = parts[6] if len(parts) > 6 else None
                    hdop = parts[7] if len(parts) > 7 else None
                    altitude = parts[8] if len(parts) > 8 else None
                    altitude_units = parts[9] if len(parts) > 9 else None

                    if lat_str and lat_dir and lon_str and lon_dir:
                        # Parse latitude
                        lat_deg = float(lat_str[:2])
                        lat_min = float(lat_str[2:])
                        latitude = lat_deg + lat_min / 60.0
                        if lat_dir == 'S':
                            latitude = -latitude

                        # Parse longitude
                        lon_deg = float(lon_str[:3])
                        lon_min = float(lon_str[3:])
                        longitude = lon_deg + lon_min / 60.0
                        if lon_dir == 'W':
                            longitude = -longitude

                        parsed.update({
                            'latitude': latitude,
                            'longitude': longitude,
                        })

                        if altitude and altitude_units == 'M':
                            try:
                                parsed['altitude'] = float(altitude)
                            except (ValueError, TypeError):
                                pass

                        if fix_quality:
                            try:
                                parsed['gps_fix_quality'] = int(fix_quality)
                            except (ValueError, TypeError):
                                pass

                        if num_satellites:
                            try:
                                parsed['gps_satellites'] = int(num_satellites)
                            except (ValueError, TypeError):
                                pass
                except (ValueError, IndexError, AttributeError):
                    pass

    # Check for proprietary formats like ULTW (4-letter format ID)
    elif re.match(r'^[A-Z]{4}', body) and len(body) >= 4:
        format_id = body[0:4]
        hex_data = body[4:] if len(body) > 4 else ''

        parsed.update({
            'format_id': format_id,
            'hex_data': hex_data
        })

        # ULTW is Ultimeter weather format
        if format_id == 'ULTW' and hex_data:
            parsed['ultimeter_format'] = True
            # ULTW data is 52 hex characters (13 fields of 4 hex chars each)
            if len(hex_data) >= 52:
                parsed['ultimeter_data'] = hex_data[:52]
                if len(hex_data) > 52:
                    parsed['ultimeter_extra'] = hex_data[52:]

    return ('', parsed)


# MAIDENHEAD LOCATOR BEACON
#
# [IO91SX]
# [FN31pr]
# [FN31pr45]
# Format: [LOCATOR][SYMBOL][COMMENT]
# LOCATOR: 4, 6, or 8 characters (2 letters + 2 digits + optional 2 letters + optional 2 digits)
def parse_maidenhead_locator(body):
    """
    Parses APRS maidenhead locator beacon format: [LOCATOR][SYMBOL][COMMENT]

    Format:
    - [ indicates maidenhead locator beacon
    - LOCATOR: 4, 6, or 8 character maidenhead grid square
      - 4 chars: 2 letters + 2 digits (e.g., FN31)
      - 6 chars: 2 letters + 2 digits + 2 letters (e.g., FN31pr)
      - 8 chars: 2 letters + 2 digits + 2 letters + 2 digits (e.g., FN31pr45)
    - Optional symbol table and symbol code
    - Optional comment

    Returns (remaining_body, parsed_dict)
    """
    parsed = {
        'format': 'maidenhead-locator',
    }

    if not body:
        return ('', parsed)

    # Match maidenhead locator: 2 letters, 2 digits, optionally 2 letters, optionally 2 digits
    # Total: 4, 6, or 8 characters
    locator_match = re.match(r'^([A-R]{2})([0-9]{2})([A-X]{2})?([0-9]{2})?', body, re.IGNORECASE)
    if not locator_match:
        raise ParseError("invalid maidenhead locator format")

    field = locator_match.group(1).upper()  # First 2 letters (field)
    square = locator_match.group(2)  # Next 2 digits (square)
    subsquare = locator_match.group(3).upper() if locator_match.group(3) else None  # Optional 2 letters (subsquare)
    extended = locator_match.group(4) if locator_match.group(4) else None  # Optional 2 digits (extended)

    # Build the full locator string
    locator = field + square
    if subsquare:
        locator += subsquare
    if extended:
        locator += extended

    parsed['locator'] = locator

    # Determine precision
    if extended:
        parsed['locator_precision'] = 8
    elif subsquare:
        parsed['locator_precision'] = 6
    else:
        parsed['locator_precision'] = 4

    # Consume the locator from body
    body = body[len(locator):]

    # Check for closing bracket right after locator
    if body and body[0] == ']':
        body = body[1:]

    # Check for symbol table and symbol (optional)
    # Symbol table is typically / or \ followed by a single symbol character
    # If / or \ is followed by text (space, letter, etc.), treat as part of comment
    if body and body[0] in '/\\':
        symbol_table = body[0]
        if len(body) > 1:
            next_char = body[1]
            # Check if next character looks like a symbol (single printable char, not space)
            # Symbols are typically single characters like -, _, ., etc.
            if next_char != ' ' and len(body) > 2 and body[2] not in ' ]':
                # Looks like text after /, not a symbol - treat / as part of comment
                pass  # Don't parse as symbol
            else:
                # Single symbol character
                parsed['symbol_table'] = symbol_table
                parsed['symbol'] = next_char
                body = body[2:]
                # Check for closing bracket after symbol
                if body and body[0] == ']':
                    body = body[1:]
        else:
            # Just symbol table, no symbol
            parsed['symbol_table'] = symbol_table
            body = body[1:]
            # Check for closing bracket
            if body and body[0] == ']':
                body = body[1:]

    # Remaining body is comment
    # Strip closing bracket if present at the end
    if body:
        comment = body.strip(' ')
        # Remove trailing closing bracket if present
        if comment.endswith(']'):
            comment = comment[:-1].rstrip(' ')
        parsed['comment'] = comment

    return ('', parsed)
