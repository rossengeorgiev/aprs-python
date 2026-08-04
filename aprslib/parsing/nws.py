import re

__all__ = ['parse_nws_alert']


def parse_nws_alert(comment):
    """
    Attempt to parse NWS alert data from an object's comment field.
    Returns dict if NWS alert detected, None otherwise.

    Format: TYPE>DDHHMMz,ZONE,ZONE,...
    """
    match = re.match(r'^([A-Z]{3,10})>(\d{6})z,(.+)$', comment)
    if not match:
        return None

    advisory_type = match.group(1)
    expiration = match.group(2) + 'z'
    zones_str = match.group(3)

    # Split zones by comma, strip whitespace
    zones = [z.strip() for z in zones_str.split(',') if z.strip()]

    return {
        'advisory_type': advisory_type,
        'expiration': expiration,
        'zones': zones,
    }
