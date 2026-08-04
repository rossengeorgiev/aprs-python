"""
DX Spot parsing for APRS.

DX spots on APRS-IS are formatted as:
    DX de <source>: <freq> <dxcall> <info> <time>

Example:
    DX de N0CALL: 14250.0 VK2ABC calling CQ 1234Z
"""

import re

__all__ = ['parse_dx']


def parse_dx(body):
    """
    Parse a DX spot report body.

    The body arrives after the main packet DTI has been stripped.
    The full body (including 'DX de') is passed in.

    Args:
        body: Packet body string starting with "DX de "

    Returns:
        Tuple of (remaining_body, result_dict)
    """
    result = {
        'format': 'dx',
    }

    # Expect: DX de CALLSIGN: freq dxcall info [time]
    # The "DX de " prefix should already be part of body
    match = re.match(
        r'^DX\s+de\s+([A-Za-z0-9\-/]+)\s*:\s*(.+)$',
        body, re.IGNORECASE
    )
    if not match:
        return body, result

    source_call = match.group(1)
    info = match.group(2).strip()
    result['dxsource'] = source_call

    # Extract optional timestamp (3-4 digit + Z at end)
    time_match = re.search(r'\s+(\d{3,4}Z)\s*$', info)
    if time_match:
        result['dxtime'] = time_match.group(1)
        info = info[:time_match.start()].strip()

    # Extract frequency (digits.digits at start)
    freq_match = re.match(r'^(\d+\.\d+)\s*', info)
    if freq_match:
        result['dxfreq'] = float(freq_match.group(1))
        info = info[freq_match.end():]
    else:
        # No valid frequency found
        result['dxinfo'] = info
        return '', result

    # Extract DX callsign (next token)
    call_match = re.match(r'^([A-Za-z0-9\-/]+)\s*', info)
    if call_match:
        result['dxcall'] = call_match.group(1)
        info = info[call_match.end():]

    # Remaining is info text (collapse whitespace)
    info = re.sub(r'\s+', ' ', info).strip()
    if info:
        result['dxinfo'] = info

    return '', result
