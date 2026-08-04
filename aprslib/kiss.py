"""
KISS frame <-> TNC-2 format conversion.

KISS (Keep It Simple, Stupid) is the binary protocol used by TNCs
to send/receive AX.25 frames over serial/TCP connections.

TNC-2 format is the human-readable text format used on APRS-IS:
    SOURCE>DEST,DIGI1,DIGI2*:body

References:
    - KISS protocol: http://www.ax25.net/kiss.aspx
    - AX.25 spec: http://www.ax25.net/AX25.2.2-Jul%2098-2.pdf
"""


__all__ = ['kiss_to_tnc2', 'tnc2_to_kiss']

# KISS special bytes
FEND = 0xC0
FESC = 0xDB
TFEND = 0xDC
TFESC = 0xDD

# AX.25 constants
AX25_FLAG = 0x7E
SSID_MASK = 0x1E  # bits 1-4 of SSID byte
LAST_ADDR_MASK = 0x01  # bit 0 of SSID byte = last address flag
HAS_BEEN_REPEATED = 0x80  # bit 7 of SSID byte (H-bit)


def _decode_ax25_call(data):
    """
    Decode a 7-byte AX.25 address field into a callsign string.

    Returns (callsign_with_ssid, has_been_repeated, is_last) or None on error.
    """
    if len(data) < 7:
        return None

    # Characters are shifted left by one bit
    callsign = ''
    for i in range(6):
        c = (data[i] >> 1) & 0x7F
        if c != ord(' '):
            callsign += chr(c)

    if not callsign:
        return None

    # SSID byte
    ssid_byte = data[6]
    ssid = (ssid_byte & SSID_MASK) >> 1
    is_last = bool(ssid_byte & LAST_ADDR_MASK)
    has_been_repeated = bool(ssid_byte & HAS_BEEN_REPEATED)

    if ssid > 0:
        callsign += '-' + str(ssid)

    return (callsign, has_been_repeated, is_last)


def _encode_ax25_call(callsign, is_last=False, has_been_repeated=False):
    """
    Encode a callsign string into 7-byte AX.25 address field.

    Returns bytes(7) or None on error.
    """
    # Split callsign and SSID
    if '-' in callsign:
        parts = callsign.split('-', 1)
        call = parts[0].upper()
        try:
            ssid = int(parts[1])
        except ValueError:
            return None
        if ssid < 0 or ssid > 15:
            return None
    else:
        call = callsign.upper()
        ssid = 0

    # Callsign must be 1-6 alphanumeric chars (ASCII only)
    if not call or len(call) > 6:
        return None
    if not all(c.isascii() and (c.isalnum() or c == ' ') for c in call):
        return None

    # Pad to 6 characters
    call = call.ljust(6)

    # Encode: shift left by one bit
    encoded = bytearray()
    for c in call:
        encoded.append(ord(c) << 1)

    # SSID byte: reserved bits set to 1 (0x60), SSID in bits 1-4
    ssid_byte = 0x60 | (ssid << 1)
    if is_last:
        ssid_byte |= LAST_ADDR_MASK
    if has_been_repeated:
        ssid_byte |= HAS_BEEN_REPEATED

    encoded.append(ssid_byte)
    return bytes(encoded)


def kiss_to_tnc2(kiss_frame):
    """
    Convert a KISS frame (bytes) to TNC-2 format string.

    The KISS frame should have the FEND bytes and command byte already
    stripped (just the raw AX.25 frame content). If FEND framing is
    still present, it will be stripped automatically.

    Returns a TNC-2 format string or None on error.
    """
    if isinstance(kiss_frame, (str,)):
        kiss_frame = kiss_frame.encode('latin-1')

    # Strip FEND framing if present
    frame = bytearray()
    if kiss_frame and kiss_frame[0] == FEND:
        # Un-escape the KISS frame
        i = 1
        # Skip command byte after first FEND
        if i < len(kiss_frame) and kiss_frame[i] != FEND:
            i += 1  # skip command byte (port/command)

        while i < len(kiss_frame):
            b = kiss_frame[i]
            if b == FEND:
                break
            elif b == FESC:
                i += 1
                if i < len(kiss_frame):
                    if kiss_frame[i] == TFEND:
                        frame.append(FEND)
                    elif kiss_frame[i] == TFESC:
                        frame.append(FESC)
                    else:
                        frame.append(kiss_frame[i])
            else:
                frame.append(b)
            i += 1
    else:
        frame = bytearray(kiss_frame)

    if len(frame) < 15:
        # Minimum: dst(7) + src(7) + ctrl(1) = 15
        return None

    # Parse destination address (first 7 bytes)
    dst_result = _decode_ax25_call(frame[0:7])
    if dst_result is None:
        return None
    dst_call, _, dst_last = dst_result

    # Parse source address (next 7 bytes)
    src_result = _decode_ax25_call(frame[7:14])
    if src_result is None:
        return None
    src_call, _, src_last = src_result

    # Parse digipeater addresses (up to 8)
    digipeaters = []
    offset = 14
    last_seen = src_last
    while not last_seen and offset + 7 <= len(frame) and len(digipeaters) < 8:
        digi_result = _decode_ax25_call(frame[offset:offset + 7])
        if digi_result is None:
            break
        digi_call, digi_repeated, digi_last = digi_result
        if digi_repeated:
            digi_call += '*'
        digipeaters.append(digi_call)
        last_seen = digi_last
        offset += 7

    if not last_seen:
        return None

    # Skip control and PID bytes
    offset += 2  # Control + PID
    if offset > len(frame):
        return None

    # Information field (the packet body)
    body = frame[offset:]

    # Build TNC-2 string
    header = src_call + '>' + dst_call
    if digipeaters:
        header += ',' + ','.join(digipeaters)

    try:
        body_str = body.decode('latin-1')
    except (UnicodeDecodeError, AttributeError):
        body_str = bytes(body).decode('latin-1')

    return header + ':' + body_str


def tnc2_to_kiss(tnc2_packet, port=0):
    """
    Convert a TNC-2 format string to a KISS frame (bytes).

    Returns KISS frame bytes (with FEND framing and command byte)
    or None on error.

    Args:
        tnc2_packet: TNC-2 format string (e.g., "SRC>DST,DIGI:body")
        port: KISS port number (0-15, default 0)
    """
    # Split header and body
    try:
        header, body = tnc2_packet.split(':', 1)
    except ValueError:
        return None

    # Parse header: SRC>DST[,DIGI1[*],DIGI2[*],...]
    try:
        src_part, rest = header.split('>', 1)
    except ValueError:
        return None

    parts = rest.split(',')
    dst_call = parts[0]
    digipeaters = parts[1:] if len(parts) > 1 else []

    # Determine last address
    has_digis = len(digipeaters) > 0

    # Encode destination (never the last address — source or final digi is)
    dst_encoded = _encode_ax25_call(dst_call, is_last=False)
    if dst_encoded is None:
        return None

    # Encode source (last address only if no digipeaters follow)
    src_encoded = _encode_ax25_call(src_part, is_last=(not has_digis))
    if src_encoded is None:
        return None

    # Encode digipeaters
    digi_encoded = bytearray()
    for i, digi in enumerate(digipeaters):
        repeated = digi.endswith('*')
        digi_clean = digi.rstrip('*')
        is_last_digi = (i == len(digipeaters) - 1)
        d = _encode_ax25_call(digi_clean, is_last=is_last_digi,
                              has_been_repeated=repeated)
        if d is None:
            return None
        digi_encoded.extend(d)

    # Build AX.25 frame
    ax25_frame = bytearray()
    ax25_frame.extend(dst_encoded)
    ax25_frame.extend(src_encoded)
    ax25_frame.extend(digi_encoded)
    ax25_frame.append(0x03)  # Control: UI frame
    ax25_frame.append(0xF0)  # PID: No layer 3
    try:
        ax25_frame.extend(body.encode('latin-1'))
    except (UnicodeEncodeError, UnicodeDecodeError):
        return None

    # Wrap in KISS framing
    kiss_data = bytearray()
    kiss_data.append(FEND)
    kiss_data.append((port & 0x0F) << 4)  # Command byte (data frame)

    for b in ax25_frame:
        if b == FEND:
            kiss_data.append(FESC)
            kiss_data.append(TFEND)
        elif b == FESC:
            kiss_data.append(FESC)
            kiss_data.append(TFESC)
        else:
            kiss_data.append(b)

    kiss_data.append(FEND)
    return bytes(kiss_data)
