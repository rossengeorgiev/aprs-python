import re
from aprslib.exceptions import ParseError

__all__ = ['parse_peetbros', 'parse_peetbros_logging']

def parse_peetbros(body):
    """
    Parse Peet Bros U-II raw weather data (# DTI / $ULTW format).

    The $ULTW packet format uses 13 fields of 4-character hex values
    (signed 16-bit big-endian). Fields in order:
        0: wind gust (tenths of km/h)
        1: wind direction (0-255 maps to 0-360)
        2: outdoor temperature (tenths of degree F)
        3: rain since midnight (hundredths of inches)
        4: barometric pressure (tenths of mbar)
        5: barometer delta (unused)
        6: barometer correction factor LSW (unused)
        7: barometer correction factor MSW (unused)
        8: outdoor humidity (tenths of percent)
        9: date (unused)
        10: time (unused)
        11: today's rain total (hundredths of inches, overrides field 3)
        12: average wind speed (tenths of km/h)

    Reference: FAP.pm _wx_parse_peet_packet()
    Note: In APRS, the # DTI indicates $ULTW format which always uses
    metric units (tenths of km/h for wind). The serial protocol's * (mph)
    vs # (km/h) distinction applies to the raw RS-232 stream, not to
    APRS-IS packets.
    """
    parsed = {'format': 'peet-bros-weather'}

    if not body:
        parsed['raw_data'] = ''
        return ('', parsed)

    # Must be complete 4-char hex groups or '----' for missing
    hex_data = body.strip()
    if not re.fullmatch(r'(?:[0-9A-Fa-f]{4}|----)+', hex_data):
        raise ParseError("invalid Peet Bros format: must be 4-char hex groups")

    parsed['raw_data'] = hex_data

    # Parse 4-char groups
    vals = []
    remaining = hex_data
    while remaining:
        if remaining[:4] == '----':
            vals.append(None)
            remaining = remaining[4:]
        else:
            match = re.match(r'^([0-9A-Fa-f]{4})', remaining)
            if not match:
                break
            v = int(match.group(1), 16)
            # Interpret as signed 16-bit
            if v >= 32768:
                v -= 65536
            vals.append(v)
            remaining = remaining[4:]

    if not vals:
        return ('', parsed)

    # All-zero frame: station online but no valid data yet
    if all(v == 0 for v in vals if v is not None):
        parsed['weather'] = {}
        return ('', parsed)

    weather = {}
    KMH_TO_MS = 1.0 / 3.6
    HINCH_TO_MM = 0.254

    def fahrenheit_to_celsius(f):
        return (f - 32.0) * 5.0 / 9.0

    # Field 0: wind gust (tenths of km/h)
    if len(vals) > 0 and vals[0] is not None:
        weather['wind_gust'] = round(vals[0] * KMH_TO_MS / 10.0, 1)

    # Field 1: wind direction (0-255 → 0-360)
    if len(vals) > 1 and vals[1] is not None:
        weather['wind_direction'] = round((vals[1] & 0xFF) * 1.41176)

    # Field 2: outdoor temperature (tenths of degree F)
    if len(vals) > 2 and vals[2] is not None:
        weather['temperature'] = round(fahrenheit_to_celsius(vals[2] / 10.0), 1)

    # Field 3: rain since midnight (hundredths of inches)
    if len(vals) > 3 and vals[3] is not None:
        weather['rain_midnight'] = round(vals[3] * HINCH_TO_MM, 1)

    # Field 4: barometric pressure (tenths of mbar)
    if len(vals) > 4 and vals[4] is not None and vals[4] >= 10:
        weather['pressure'] = round(vals[4] / 10.0, 1)

    # Fields 5-7: barometer delta/correction (skip)

    # Field 8: outdoor humidity (tenths of percent)
    if len(vals) > 8 and vals[8] is not None:
        hum = round(vals[8] / 10.0)
        if 1 <= hum <= 100:
            weather['humidity'] = hum

    # Fields 9-10: date and time (skip)

    # Field 11: today's rain total (overrides field 3)
    if len(vals) > 11 and vals[11] is not None:
        weather['rain_midnight'] = round(vals[11] * HINCH_TO_MM, 1)

    # Field 12: average wind speed (tenths of km/h)
    if len(vals) > 12 and vals[12] is not None:
        weather['wind_speed'] = round(vals[12] * KMH_TO_MS / 10.0, 1)

    if weather:
        parsed['weather'] = weather

    return ('', parsed)


def parse_peetbros_logging(body):
    """
    Parse Peet Bros !! logging frame.

    The !! format is a series of 4-character hex values (signed 16-bit big-endian)
    or '----' for missing values. Fields in order:
        0: instant wind speed (tenths of km/h)
        1: wind direction (0-255 maps to 0-360)
        2: outdoor temperature (tenths of degree F)
        3: rain (total since midnight, hundredths of inches)
        4: barometric pressure (tenths of mbar)
        5: indoor temperature (tenths of degree F)
        6: outdoor humidity (tenths of percent)
        7: indoor humidity (tenths of percent)
        8: date
        9: time
        10: today's rain total (hundredths of inches)
        11: average wind speed (tenths of km/h)

    Reference: FAP.pm _wx_parse_peet_logging()
    """
    parsed = {'format': 'peet-bros-logging'}

    if not body:
        return ('', parsed)

    hex_data = body.strip()
    if not re.fullmatch(r'(?:[0-9A-Fa-f]{4}|----)+', hex_data):
        raise ParseError("invalid Peet Bros logging format: must be 4-char hex groups")
    parsed['raw_data'] = hex_data

    # Parse 4-char groups (signed 16-bit big-endian hex or '----')
    vals = []
    remaining = hex_data
    while remaining:
        if remaining[:4] == '----':
            vals.append(None)
            remaining = remaining[4:]
        else:
            match = re.match(r'^([0-9A-Fa-f]{4})', remaining)
            if not match:
                break
            v = int(match.group(1), 16)
            # Interpret as signed 16-bit
            if v >= 32768:
                v -= 65536
            vals.append(v)
            remaining = remaining[4:]

    if not vals:
        return ('', parsed)

    # All-zero frame: station online but no valid data yet
    if all(v == 0 for v in vals if v is not None):
        parsed['weather'] = {}
        return ('', parsed)

    weather = {}
    KMH_TO_MS = 1.0 / 3.6
    HINCH_TO_MM = 0.254

    def fahrenheit_to_celsius(f):
        return (f - 32.0) * 5.0 / 9.0

    # Field 0: instant wind speed (tenths of km/h)
    if len(vals) > 0 and vals[0] is not None:
        weather['wind_speed'] = round(vals[0] * KMH_TO_MS / 10.0, 1)

    # Field 1: wind direction (0-255 → 0-360)
    if len(vals) > 1 and vals[1] is not None:
        weather['wind_direction'] = round((vals[1] & 0xFF) * 1.41176)

    # Field 2: outdoor temperature (tenths of degree F)
    if len(vals) > 2 and vals[2] is not None:
        weather['temperature'] = round(fahrenheit_to_celsius(vals[2] / 10.0), 1)

    # Field 3: rain since midnight (hundredths of inches)
    if len(vals) > 3 and vals[3] is not None:
        weather['rain_midnight'] = round(vals[3] * HINCH_TO_MM, 1)

    # Field 4: barometric pressure (tenths of mbar)
    if len(vals) > 4 and vals[4] is not None and vals[4] >= 10:
        weather['pressure'] = round(vals[4] / 10.0, 1)

    # Field 5: indoor temperature (tenths of degree F)
    if len(vals) > 5 and vals[5] is not None:
        weather['temp_indoor'] = round(fahrenheit_to_celsius(vals[5] / 10.0), 1)

    # Field 6: outdoor humidity (tenths of percent)
    if len(vals) > 6 and vals[6] is not None:
        hum = round(vals[6] / 10.0)
        if 1 <= hum <= 100:
            weather['humidity'] = hum

    # Field 7: indoor humidity (tenths of percent)
    if len(vals) > 7 and vals[7] is not None:
        hum_in = round(vals[7] / 10.0)
        if 1 <= hum_in <= 100:
            weather['humidity_indoor'] = hum_in

    # Fields 8-9: date and time (skip)

    # Field 10: today's rain total (overrides field 3)
    if len(vals) > 10 and vals[10] is not None:
        weather['rain_midnight'] = round(vals[10] * HINCH_TO_MM, 1)

    # Field 11: average wind speed (overrides field 0)
    if len(vals) > 11 and vals[11] is not None:
        weather['wind_speed'] = round(vals[11] * KMH_TO_MS / 10.0, 1)

    # Fallback: use indoor values when outdoor are missing
    if 'temperature' not in weather and 'temp_indoor' in weather:
        weather['temperature'] = weather['temp_indoor']
    if 'humidity' not in weather and 'humidity_indoor' in weather:
        weather['humidity'] = weather['humidity_indoor']

    if weather:
        parsed['weather'] = weather

    return ('', parsed)
