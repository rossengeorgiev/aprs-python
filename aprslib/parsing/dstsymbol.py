"""
Symbol lookup from destination callsign (GPSxyz/SPCxyz encoding).

Legacy NMEA-only trackers that cannot set symbol in the packet body encode
their symbol in the destination callsign field using the GPSxyz or SPCxyz
format defined in APRS101 Chapter 20.

Encoding format:
  GPS + 2 chars = primary/secondary table lookup (no overlay)
  GPS + 3 chars = either numeric (C/E prefix) or overlay (secondary table)
  SPC is equivalent to GPS for this purpose.

References:
  - APRS101 PDF Chapter 20: APRS Symbols
  - perl-aprs-fap FAP.pm %dstsymbol hash and _get_symbol_fromdst()
"""

__all__ = ['get_symbol_from_destination']

# Destination symbol lookup table
# Maps 2-letter code to (table_char, symbol_char)
# Primary table (/) entries
_DST_SYMBOL = {
    'BB': '/!', 'BC': '/"', 'BD': '/#', 'BE': '/$',
    'BF': '/%', 'BG': '/&', 'BH': "/\'", 'BI': '/(', 'BJ': '/)',
    'BK': '/*', 'BL': '/+', 'BM': '/,', 'BN': '/-', 'BO': '/.',
    'BP': '//',

    'P0': '/0', 'P1': '/1', 'P2': '/2', 'P3': '/3',
    'P4': '/4', 'P5': '/5', 'P6': '/6', 'P7': '/7',
    'P8': '/8', 'P9': '/9',

    'MR': '/:', 'MS': '/;', 'MT': '/<', 'MU': '/=',
    'MV': '/>', 'MW': '/?', 'MX': '/@',

    'PA': '/A', 'PB': '/B', 'PC': '/C', 'PD': '/D',
    'PE': '/E', 'PF': '/F', 'PG': '/G', 'PH': '/H',
    'PI': '/I', 'PJ': '/J', 'PK': '/K', 'PL': '/L',
    'PM': '/M', 'PN': '/N', 'PO': '/O', 'PP': '/P',
    'PQ': '/Q', 'PR': '/R', 'PS': '/S', 'PT': '/T',
    'PU': '/U', 'PV': '/V', 'PW': '/W', 'PX': '/X',
    'PY': '/Y', 'PZ': '/Z',

    'HS': '/[', 'HT': '/\\', 'HU': '/]', 'HV': '/^',
    'HW': '/_', 'HX': '/`',

    'LA': '/a', 'LB': '/b', 'LC': '/c', 'LD': '/d',
    'LE': '/e', 'LF': '/f', 'LG': '/g', 'LH': '/h',
    'LI': '/i', 'LJ': '/j', 'LK': '/k', 'LL': '/l',
    'LM': '/m', 'LN': '/n', 'LO': '/o', 'LP': '/p',
    'LQ': '/q', 'LR': '/r', 'LS': '/s', 'LT': '/t',
    'LU': '/u', 'LV': '/v', 'LW': '/w', 'LX': '/x',
    'LY': '/y', 'LZ': '/z',

    'J1': '/{', 'J2': '/|', 'J3': '/}', 'J4': '/~',

    # Secondary table (\) entries
    'OB': '\\!', 'OC': '\\"', 'OD': '\\#', 'OE': '\\$',
    'OF': '\\%', 'OG': '\\&', 'OH': "\\\'", 'OI': '\\(', 'OJ': '\\)',
    'OK': '\\*', 'OL': '\\+', 'OM': '\\,', 'ON': '\\-', 'OO': '\\.',
    'OP': '\\/',

    'A0': '\\0', 'A1': '\\1', 'A2': '\\2', 'A3': '\\3',
    'A4': '\\4', 'A5': '\\5', 'A6': '\\6', 'A7': '\\7',
    'A8': '\\8', 'A9': '\\9',

    'NR': '\\:', 'NS': '\\;', 'NT': '\\<', 'NU': '\\=',
    'NV': '\\>', 'NW': '\\?', 'NX': '\\@',

    'AA': '\\A', 'AB': '\\B', 'AC': '\\C', 'AD': '\\D',
    'AE': '\\E', 'AF': '\\F', 'AG': '\\G', 'AH': '\\H',
    'AI': '\\I', 'AJ': '\\J', 'AK': '\\K', 'AL': '\\L',
    'AM': '\\M', 'AN': '\\N', 'AO': '\\O', 'AP': '\\P',
    'AQ': '\\Q', 'AR': '\\R', 'AS': '\\S', 'AT': '\\T',
    'AU': '\\U', 'AV': '\\V', 'AW': '\\W', 'AX': '\\X',
    'AY': '\\Y', 'AZ': '\\Z',

    'DS': '\\[', 'DT': '\\\\', 'DU': '\\]', 'DV': '\\^',
    'DW': '\\_', 'DX': '\\`',

    'SA': '\\a', 'SB': '\\b', 'SC': '\\c', 'SD': '\\d',
    'SE': '\\e', 'SF': '\\f', 'SG': '\\g', 'SH': '\\h',
    'SI': '\\i', 'SJ': '\\j', 'SK': '\\k', 'SL': '\\l',
    'SM': '\\m', 'SN': '\\n', 'SO': '\\o', 'SP': '\\p',
    'SQ': '\\q', 'SR': '\\r', 'SS': '\\s', 'ST': '\\t',
    'SU': '\\u', 'SV': '\\v', 'SW': '\\w', 'SX': '\\x',
    'SY': '\\y', 'SZ': '\\z',

    'Q1': '\\{', 'Q2': '\\|', 'Q3': '\\}', 'Q4': '\\~',
}


def get_symbol_from_destination(destination):
    """
    Look up APRS symbol from a GPSxyz or SPCxyz destination callsign.

    Args:
        destination: Destination callsign (e.g., "GPSMV", "SPCPA3")

    Returns:
        Tuple of (symbol_table, symbol_code) or None if not a valid
        symbol destination. symbol_table may be an overlay character
        (A-Z, 0-9) for secondary table symbols with overlay.

    Examples:
        get_symbol_from_destination("GPSMV")  -> ('/', '>')  # Car
        get_symbol_from_destination("GPSPA")  -> ('/', 'A')  # Aid station
        get_symbol_from_destination("GPSC32") -> ('/', ' ')  # Numeric: chr(32+32)='@' actually chr(32)=' '
        get_symbol_from_destination("SPCAA3") -> ('3', 'A')  # Secondary with overlay '3'
    """
    if not destination:
        return None

    # Strip SSID if present
    dest = destination.split('-', 1)[0].upper()

    # Must start with GPS or SPC
    if not (dest.startswith('GPS') or dest.startswith('SPC')):
        return None

    suffix = dest[3:]

    if len(suffix) == 2:
        # 2-char: direct lookup from table
        sym = _DST_SYMBOL.get(suffix)
        if sym:
            return (sym[0], sym[1])
        return None

    elif len(suffix) == 3:
        type_char = suffix[0]
        number_id = suffix[1:3]

        # Numeric encoding: C=primary, E=secondary
        if type_char in ('C', 'E'):
            try:
                num = int(number_id)
            except ValueError:
                return None
            if 1 <= num <= 94:
                code = chr(num + 32)
                table = '/' if type_char == 'C' else '\\'
                return (table, code)
            return None

        # Overlay encoding: type is first 2 chars of suffix used for lookup,
        # third char is the overlay (A-Z, 0-9)
        overlay = suffix[2]
        if type_char in ('O', 'A', 'N', 'D', 'S', 'Q'):
            if overlay.isalpha() and overlay.isupper() or overlay.isdigit():
                dst_type = suffix[0:2]
                sym = _DST_SYMBOL.get(dst_type)
                if sym:
                    code = sym[1]
                    return (overlay, code)
            return None
        return None

    return None
