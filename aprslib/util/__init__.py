from math import floor


def degrees_to_ddm(dd):
    degrees = int(floor(dd))
    minutes = (dd - degrees) * 60
    return (degrees, minutes)


def latitude_to_ddm(dd):
    direction = "S" if dd < 0 else "N"
    degrees, minutes = degrees_to_ddm(abs(dd))

    return "{0:02d}{1:05.2f}{2}".format(
        degrees,
        minutes,
        direction,
        )

def longitude_to_ddm(dd):
    direction = "W" if dd < 0 else "E"
    degrees, minutes = degrees_to_ddm(abs(dd))

    return "{0:03d}{1:05.2f}{2}".format(
        degrees,
        minutes,
        direction,
        )

def comment_altitude(altitude):
    altitude /= 0.3048  # to feet
    altitude = min(999999, altitude)
    altitude = max(-99999, altitude)
    return "/A={0:06.0f}".format(altitude)


def remove_WIDEn_N(path):
    """
    Remove WIDEn-N entries and asterisks from path, leaving only digi names
    path: path of parsed packet (list of strings)
    returns: list of digipeaters that digipeated packet, in order
    """
    path = map(lambda x: re.sub('*$', '', x), path) # Remove asterisks
    return(path = list(filter(lambda x: not re.match(r'WIDE[0-9\-\*]+$', x), path)))
