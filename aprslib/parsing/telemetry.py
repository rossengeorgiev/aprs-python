import re
from aprslib import base91
from aprslib.exceptions import ParseError
from aprslib.parsing import logger

__all__ = [
        'parse_comment_telemetry',
        'parse_telemetry_config',
        'parse_telemetry_report',
        ]


def parse_comment_telemetry(text):
    """
    Looks for base91 telemetry found in comment field
    Returns [remaining_text, telemetry]
    """
    parsed = {}
    match = re.findall(r"^(.*?)\|([!-{]{4,14})\|(.*)$", text)

    if match and len(match[0][1]) % 2 == 0:
        text, telemetry, post = match[0]
        text += post

        temp = [0] * 7
        for i in range(7):
            temp[i] = base91.to_decimal(telemetry[i*2:i*2+2])

        parsed.update({
            'telemetry': {
                'seq': temp[0],
                'vals': temp[1:6]
                }
            })

        if temp[6] != '':
            parsed['telemetry'].update({
                'bits': "{0:08b}".format(temp[6] & 0xFF)[::-1]
                })

    return (text, parsed)


def parse_telemetry_config(body):
    parsed = {}

    match = re.findall(r"^(PARM|UNIT|EQNS|BITS)\.(.*)$", body)
    if match:
        logger.debug("Attempting to parse telemetry-message packet")
        form, body = match[0]

        parsed.update({'format': 'telemetry-message'})

        if form in ["PARM", "UNIT"]:
            vals = body.rstrip().split(',')[:13]

            for val in vals:
                if not re.match(r"^(.{1,20}|)$", val):
                    raise ParseError("incorrect format of %s (name too long?)" % form)

            defvals = [''] * 13
            defvals[:len(vals)] = vals

            parsed.update({
                't%s' % form: defvals
                })
        elif form == "EQNS":
            eqns = body.rstrip().split(',')[:15]
            teqns = [0, 1, 0] * 5

            for idx, val in enumerate(eqns):
                # Strip whitespace from values (some packets have spaces after commas)
                val = val.strip()
                # Extract numeric part if there are non-numeric characters (e.g., "03n" -> "03")
                # This handles cases where comments or extra data are concatenated
                numeric_match = re.match(r'^([-]?\d*\.?\d+)', val)
                if numeric_match:
                    val = numeric_match.group(1)
                elif not re.match(r"^([-]?\d*\.?\d+|)$", val):
                    raise ParseError("value at %d is not a number in %s" % (idx+1, form))

                # Convert to number
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
            # APRS spec says 23 chars, but real-world packets may be longer
            # Accept any reasonable length (up to 100 chars to be safe)
            # Some packets may be missing binary bits (just title)
            match = re.findall(r"^([01]{8}),(.*)$", body.rstrip())
            if match:
                bits, title = match[0]
                parsed.update({
                    't%s' % form: bits,
                    'title': title.strip(' ')
                })
            else:
                # No binary bits found - treat entire body as title
                # This handles malformed packets like "BITS.title" without bits
                parsed.update({
                    't%s' % form: '00000000',  # Default to all zeros
                    'title': body.rstrip().strip(' ')
                })

    return (body, parsed)


def parse_telemetry_report(body):
    """
    Parses APRS 1.2 telemetry report format: T#sss,aaa,bbb,ccc,ddd,eee,bbbbbbbb,comment

    Format:
    - T# indicates telemetry report
    - sss is sequence number (000-999)
    - aaa to eee are 5 analog values (000-999)
    - bbbbbbbb is 8 binary digits (digital I/O)
    - comment is optional text

    Returns (remaining_body, parsed_dict)
    """
    parsed = {}

    # Check if body starts with '#'
    if not body.startswith('#'):
        raise ParseError("telemetry report must start with '#'")

    # Remove the '#' prefix
    body = body[1:]

    # Handle MIC sequence form: #MIC199,... or #MIC,199,...
    if body.startswith('MIC'):
        seq_str = 'MIC'
        fields_body = body[3:]
        if fields_body.startswith(','):
            fields_body = fields_body[1:]
        parts = [seq_str] + (fields_body.split(',', 6) if fields_body else [])
    else:
        # Split by comma - need at least sequence number
        # Some real-world packets are incomplete (missing analog values or digital I/O)
        parts = body.split(',', 7)

    if len(parts) < 1:
        raise ParseError("telemetry report must have at least a sequence number")

    seq_str = parts[0]
    # Extract analog values (up to 5, pad with empty strings if missing)
    analog_strs = parts[1:6] if len(parts) > 1 else []
    # Pad to 5 analog values if we have fewer
    while len(analog_strs) < 5:
        analog_strs.append('')

    # Digital I/O field (may be missing or in next position)
    digital_field = parts[6] if len(parts) > 6 else ''
    comment = ''

    # If digital field is empty, use default and treat remaining as comment
    if not digital_field or digital_field.strip() == '':
        digital_field = '00000000'
        comment = ','.join(parts[7:]) if len(parts) > 7 else ''
    else:
        # Collect all remaining parts as comment
        remaining_parts = []
        if len(parts) > 7:
            remaining_parts = list(parts[7:])
        comment = ','.join(remaining_parts) if remaining_parts else ''

    # Validate and parse sequence number (allow any positive integer or 'MIC')
    # APRS spec says 000-999 or MIC, but real-world packets use larger numbers
    if seq_str == 'MIC':
        seq = 'MIC'
    elif re.match(r'^\d+$', seq_str):
        seq = int(seq_str)
    else:
        raise ParseError("telemetry sequence number must be numeric or MIC")

    # Parse analog values (can be 000-999, allow decimals and negatives per APRS 1.2)
    # Empty values are allowed and treated as 0
    # Some packets have data extensions concatenated (e.g., "0>/A=9125")
    analog_vals = []
    for i, val_str in enumerate(analog_strs):
        # Allow empty values (treated as 0)
        if not val_str or val_str.strip() == '':
            analog_vals.append(0.0)
            continue

        # Extract numeric part if there are non-numeric characters (e.g., "0>/A=9125" -> "0")
        # This handles cases where data extensions are concatenated without proper separation
        original_val_str = val_str  # noqa: F841
        numeric_match = re.match(r'^-?(\d+\.?\d*|\.\d+)', val_str)
        if numeric_match:
            numeric_part = numeric_match.group(0)
            remaining = val_str[len(numeric_part):]
            val_str = numeric_part
            # If there's remaining content (like "/A=9125"), add it to comment
            if remaining and not comment:
                comment = remaining
        elif not re.match(r'^-?(\d+\.?\d*|\.\d+)$', val_str):
            raise ParseError("telemetry analog value %d has invalid format" % (i+1))

        try:
            val = float(val_str)
        except ValueError:
            raise ParseError("telemetry analog value %d is not a valid number" % (i+1))
        analog_vals.append(val)

    # Validate digital I/O (must be binary digits, pad to 8 if shorter)
    # Some packets have comment concatenated without comma separator
    # Some packets have shorter binary strings (pad with leading zeros)
    # Some packets have non-binary characters mixed in (extract leading binary digits)
    # Check if field starts with binary digits
    binary_match = re.match(r'^([01]+)', digital_field)
    if binary_match:
        binary_str = binary_match.group(1)

        # If there are non-binary characters after binary digits, require at least 4 binary digits
        # This prevents false positives like "123" (1 binary + 2 non-binary)
        if len(binary_str) < len(digital_field):
            # Has non-binary characters following
            if len(binary_str) < 4:
                # Too few binary digits before non-binary - likely invalid
                raise ParseError("telemetry digital I/O must be binary digits")

        # Extract leading binary digits
        if len(binary_str) < 8:
            # Pad shorter binary strings to 8 digits
            digital_str = binary_str.zfill(8)
        elif len(binary_str) == 8:
            digital_str = binary_str
        else:
            # Longer than 8, use first 8
            digital_str = binary_str[:8]

        # If there's non-binary content after the binary digits, treat as comment if no comment yet
        if len(binary_str) < len(digital_field) and not comment:
            remaining = digital_field[len(binary_str):]
            comment = remaining
    else:
        # No valid binary digits found - this is invalid
        raise ParseError("telemetry digital I/O must be binary digits")

    parsed.update({
        'format': 'telemetry',
        'telemetry': {
            'seq': seq,
            'vals': analog_vals,
            'bits': digital_str
        }
    })

    # Add comment if present
    if comment:
        parsed['comment'] = comment.strip(' ')

    # Return empty remaining body since we consumed everything
    return ('', parsed)

