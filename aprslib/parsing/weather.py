import re
from aprslib.exceptions import ParseError

__all__ = [
    'parse_weather',
    'parse_weather_data',
    ]

# constants
wind_multiplier = 0.44704
rain_multiplier = 0.254

key_map = {
    'g': 'wind_gust',
    'c': 'wind_direction',
    't': 'temperature',
    'S': 'wind_speed',
    'r': 'rain_1h',
    'p': 'rain_24h',
    'P': 'rain_since_midnight',
    'h': 'humidity',
    'b': 'pressure',
    'l': 'luminosity',
    'L': 'luminosity',
    's': 'snow',
    '#': 'rain_raw',
    'X': 'radiation',
    'F': 'water_level',
    'V': 'battery',
}
val_map = {
    'g': lambda x: int(x) * wind_multiplier,
    'c': lambda x: int(x),
    'S': lambda x: int(x) * wind_multiplier,
    't': lambda x: (float(x) - 32) / 1.8,
    'r': lambda x: int(x) * rain_multiplier,
    'p': lambda x: int(x) * rain_multiplier,
    'P': lambda x: int(x) * rain_multiplier,
    'h': lambda x: 100 if int(x) == 0 else int(x),
    'b': lambda x: float(x) / 10,
    'l': lambda x: int(x) + 1000,
    'L': lambda x: int(x),
    's': lambda x: float(x) * 25.4,
    '#': lambda x: int(x),
    'X': lambda x: int(x[0:2]) * (10 ** int(x[2])),  # resistor code to nSv/hr
    'F': lambda x: float(x) * 0.03048,  # tenths of foot to meters
    'V': lambda x: int(x) / 10.0,  # tenths to volts
}

def parse_weather_data(body):
    parsed = {}

    # parse weather data
    body = re.sub(r"^([0-9]{3})/([0-9]{3})", "c\\1s\\2", body)
    body = body.replace('s', 'S', 1)

    # match as many parameters from the start, rest is comment
    data = re.match(r"^([cSgtrpPlLs#XV][0-9\-\. ]{3}|h[0-9\. ]{2}|b[0-9\. ]{5}|F[\-0-9 ]{4})+", body)

    if data:
        data = data.group()
        # split out data from comment
        body = body[len(data):]
        # parse all weather parameters
        data = re.findall(r"([cSgtrpPlLs#XV]\d{3}|t-\d{2}|h\d{2}|b\d{5}|s\.\d{2}|s\d\.\d|F-?\d{3,4})", data)
        data = map(lambda x: (key_map[x[0]] , val_map[x[0]](x[1:])), data)
        parsed.update(dict(data))

    # Extract weather software identifier from remaining body
    # If remaining text is 3-5 alphanumeric chars, it's the software ID
    remaining = body.strip()
    if remaining and re.match(r'^[a-zA-Z0-9\-_]{3,5}$', remaining):
        parsed['wx_software'] = remaining
        body = ''

    return (body, parsed)

def parse_weather(body):
    match = re.match(r"^(\d{8})c[\. \d]{3}s[\. \d]{3}g[\. \d]{3}t[\. \d]{3}", body)
    if not match:
        raise ParseError("invalid positionless weather report format")

    comment, weather = parse_weather_data(body[8:])

    parsed = {
        'format': 'wx',
        'wx_raw_timestamp': match.group(1),
        'comment': comment.strip(' '),
        'weather': weather,
        }

    return ('', parsed)
