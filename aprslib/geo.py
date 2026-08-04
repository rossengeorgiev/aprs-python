"""
Geographic utility functions for APRS.

Provides:
- distance(): Great circle distance between two points (km)
- direction(): Initial bearing between two points (degrees)
- position_resolution(): Position uncertainty in meters based on coordinate precision
"""

import math

__all__ = ['distance', 'direction', 'position_resolution']


def distance(lat0, lon0, lat1, lon1):
    """
    Calculate great-circle distance between two points using the Haversine formula.

    Args:
        lat0, lon0: First point (decimal degrees)
        lat1, lon1: Second point (decimal degrees)

    Returns:
        Distance in kilometers.
    """
    R = 6371.0  # Earth mean radius in km

    lat0_r = math.radians(lat0)
    lat1_r = math.radians(lat1)
    dlat = math.radians(lat1 - lat0)
    dlon = math.radians(lon1 - lon0)

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat0_r) * math.cos(lat1_r) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def direction(lat0, lon0, lat1, lon1):
    """
    Calculate initial bearing (forward azimuth) from point 0 to point 1.

    Args:
        lat0, lon0: Start point (decimal degrees)
        lat1, lon1: End point (decimal degrees)

    Returns:
        Bearing in degrees (0-360, where 0=North, 90=East, etc.)
    """
    lat0_r = math.radians(lat0)
    lat1_r = math.radians(lat1)
    dlon_r = math.radians(lon1 - lon0)

    x = math.sin(dlon_r) * math.cos(lat1_r)
    y = (math.cos(lat0_r) * math.sin(lat1_r) -
         math.sin(lat0_r) * math.cos(lat1_r) * math.cos(dlon_r))

    bearing = math.degrees(math.atan2(x, y))
    return bearing % 360


def position_resolution(lat_str):
    """
    Calculate position resolution (uncertainty) based on the number of
    decimal digits in the latitude string.

    APRS uses DDMM.MM format. The resolution depends on how many digits
    after the decimal point are present (vs space-filled for ambiguity).

    According to APRS101 Chapter 6:
    - Full precision (MM.MM): ~18.5 meters
    - 1 digit ambiguous (MM.M_): ~185 meters
    - 2 digits ambiguous (MM.__): ~1.85 km
    - 3 digits ambiguous (M_.__ ): ~18.5 km
    - 4 digits ambiguous (__.__): ~185 km (1 degree)

    Args:
        lat_str: Latitude string in DDMM.MM format (may have spaces for ambiguity)

    Returns:
        Position resolution in meters (worst-case uncertainty).
    """
    if not lat_str or '.' not in lat_str:
        return None

    # Count space characters (ambiguity level)
    # In APRS, spaces replace digits from right-to-left for position ambiguity
    # Each space represents one less digit of precision
    spaces = lat_str.count(' ')

    # Resolution table (meters per ambiguity level)
    # Based on 1/100th of a minute = ~18.52m at equator
    # Level 0: full precision = 1/100 minute = ~18.52m
    # Level 1: 1/10 minute = ~185.2m
    # Level 2: 1 minute = ~1852m
    # Level 3: 10 minutes = ~18520m
    # Level 4: 1 degree = ~111120m
    resolution_table = [
        18.52,      # 0 spaces: 1/100 minute
        185.2,      # 1 space: 1/10 minute
        1852.0,     # 2 spaces: 1 minute
        18520.0,    # 3 spaces: 10 minutes
        111120.0,   # 4 spaces: 1 degree
    ]

    if spaces < len(resolution_table):
        return resolution_table[spaces]
    return resolution_table[-1]
