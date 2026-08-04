import re
from aprslib.exceptions import ParseError

__all__ = ['parse_query']


def parse_query(body):
    """
    Parse APRS general query format.

    Input: body after '?' DTI has been stripped
    Output: ('', parsed_dict)

    Format: TYPE?{optional area qualifier}
    """
    parsed = {'format': 'query'}

    # Match query type - ends with optional '?'
    match = re.match(r'^([A-Z0-9]{2,10})\??(.*)$', body, re.IGNORECASE)
    if not match:
        raise ParseError("invalid query format")

    query_type = match.group(1).upper()
    remainder = match.group(2).strip()

    parsed['query_type'] = query_type

    # Check for area qualifier (only for APRS queries)
    if query_type == 'APRS' and remainder:
        # Try DDMM.MM format first (APRS101 Chapter 14)
        area_match = re.match(
            r'^\s*(\d{4}\.\d{2})([NS])/(\d{5}\.\d{2})([EW])/(\d{4})$',
            remainder
        )
        if area_match:
            lat_str = area_match.group(1)
            lat_dir = area_match.group(2)
            lon_str = area_match.group(3)
            lon_dir = area_match.group(4)
            range_miles = int(area_match.group(5))

            # Convert DDMM.MM to decimal degrees
            lat_deg = int(lat_str[:2])
            lat_min = float(lat_str[2:])
            latitude = lat_deg + lat_min / 60.0
            if lat_dir == 'S':
                latitude = -latitude

            lon_deg = int(lon_str[:3])
            lon_min = float(lon_str[3:])
            longitude = lon_deg + lon_min / 60.0
            if lon_dir == 'W':
                longitude = -longitude

            parsed['latitude'] = latitude
            parsed['longitude'] = longitude
            parsed['range'] = range_miles * 1.609344  # miles to km
        else:
            # Try decimal-degree format: lat,lon,radius (e.g., "34.02,-117.15,0200")
            dec_match = re.match(
                r'^\s*(-?\d+\.?\d*),\s*(-?\d+\.?\d*),\s*(\d+)$',
                remainder
            )
            if dec_match:
                latitude = float(dec_match.group(1))
                longitude = float(dec_match.group(2))
                range_miles = int(dec_match.group(3))

                if -90 <= latitude <= 90 and -180 <= longitude <= 180:
                    parsed['latitude'] = latitude
                    parsed['longitude'] = longitude
                    parsed['range'] = range_miles * 1.609344  # miles to km

    return ('', parsed)
