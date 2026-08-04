# APRS Protocol Implementation Spec — Missing Features

This document specifies all missing APRS protocol features for `aprslib` to achieve
full APRS101 + APRS 1.1/1.2 protocol support. Each section is an independent unit
of work with exact format definitions, parsing rules, output schema, and test cases.

Reference documents:
- APRS101.PDF (APRS Protocol Reference, Version 1.0)
- APRS 1.1 Addendum (July 2004)
- APRS 1.2 Proposals (ongoing, aprs.org/aprs12/)
- Direwolf source (WB2OSZ) as reference implementation

---

## Table of Contents

1. [Query Packets (`?`)](#1-query-packets-)
2. [Area Objects](#2-area-objects)
3. [NWS Weather Alerts](#3-nws-weather-alerts)
4. [Signpost Objects](#4-signpost-objects)
5. [DF Reports (Direction Finding)](#5-df-reports-direction-finding)
6. [Peet Bros U-II Raw Weather (`#`)](#6-peet-bros-u-ii-raw-weather-)
7. [Telemetry Coefficient Application](#7-telemetry-coefficient-application)
8. [Frequency/Tone in Position Comment](#8-frequencytone-in-position-comment)
9. [Mic-E Device Type Detection](#9-mic-e-device-type-detection)
10. [Digipeater Path Analysis](#10-digipeater-path-analysis)
11. [Symbol Table Decoding](#11-symbol-table-decoding)
12. [Item-in-Message](#12-item-in-message)
13. [Weather Extensions (APRS 1.2)](#13-weather-extensions-aprs-12)
14. [Speed Extension (Above Mach 1)](#14-speed-extension-above-mach-1)

---

## 1. Query Packets (`?`)

**Priority:** HIGH  
**Spec Reference:** APRS101 Chapter 15  
**Current State:** Raises `UnknownFormat` — listed in `unsupported_formats`  
**File:** New `aprslib/parsing/query.py`

### 1.1 Format Definition

The `?` DTI identifies a general broadcast query. The information field format:

```
?TYPE?{optional qualifiers}
```

#### General Query Types

| Query String | Meaning | Expected Response |
|-------------|---------|-------------------|
| `?APRS?` | All-stations position query | Position report |
| `?APRS? lat/lon/range` | Area-qualified position query | Position (if in range) |
| `?IGATE?` | IGate status query | IGate statistics |
| `?WX?` | Weather station query | Weather report |

#### Directed Query Types (sent via `:` message format)

These arrive as messages (DTI `:`) with query text in the message body.
They are already routed through `parse_message` — we need to detect and flag them.

| Query Text | Meaning |
|------------|---------|
| `?APRS?` | Position query |
| `?APRSP` | Position query (synonym) |
| `?APRST` | Trace/path query |
| `?APRSS` | Status query |
| `?APRSO` | Objects query |
| `?APRSM` | Messages query |
| `?APRSD` | Stations heard direct |
| `?APRSH callsign` | Has station been heard? |

### 1.2 Parsing Rules

```python
def parse_query(body):
    """
    Parse general query format.
    
    Input: body after '?' DTI has been stripped
    Output: ('', parsed_dict)
    """
```

**Step 1:** Match the query type:
```
regex: ^([A-Z0-9]{2,10})\??(.*)$
```

**Step 2:** If query type is `APRS` and there's remaining body, parse area qualifier:
```
Area format: " ddmm.mmN/dddmm.mmW/rrrr"
regex: ^\s*(\d{4}\.\d{2}[NS])[/](\d{5}\.\d{2}[EW])[/](\d{4})$
```

- Latitude: standard APRS DDMM.MM format
- Longitude: standard APRS DDDMM.MM format  
- Range: 4-digit integer, miles

### 1.3 Output Schema

```python
{
    'format': 'query',
    'query_type': str,        # 'APRS', 'IGATE', 'WX'
    # If area-qualified:
    'latitude': float,        # decimal degrees (optional)
    'longitude': float,       # decimal degrees (optional)
    'range': float,           # km (converted from miles) (optional)
}
```

For directed queries detected in messages:

```python
{
    'format': 'directed-query',
    'addresse': str,
    'query_type': str,        # 'APRSP', 'APRST', 'APRSS', etc.
    'target_callsign': str,   # Only for ?APRSH (optional)
}
```

### 1.4 Integration Point

In `_try_toparse_body()`, remove `'?'` from `unsupported_formats` dict and add:

```python
elif packet_type == '?':
    logger.debug("Attempting to parse as query packet")
    body, result = parse_query(body)
```

In `parse_message()`, after detecting a valid addressee, check if the message body
starts with `?APRS` to classify it as `format: 'directed-query'` instead of a
regular message.

### 1.5 Test Cases

```python
# General query
"N0CALL>APRS:?APRS?"
# → format='query', query_type='APRS'

# Area-qualified query
"N0CALL>APRS:?APRS? 3400.00N/11800.00W/0050"
# → format='query', query_type='APRS', latitude=34.0, longitude=-118.0, range=80.467 (50mi)

# IGate query
"N0CALL>APRS:?IGATE?"
# → format='query', query_type='IGATE'

# Weather query
"N0CALL>APRS:?WX?"
# → format='query', query_type='WX'

# Directed query via message
"N0CALL>APRS::W1ABC    :?APRSD"
# → format='directed-query', addresse='W1ABC', query_type='APRSD'

# Directed query with target
"N0CALL>APRS::W1ABC    :?APRSH W2XYZ"
# → format='directed-query', addresse='W1ABC', query_type='APRSH', target_callsign='W2XYZ'
```

---

## 2. Area Objects

**Priority:** MEDIUM  
**Spec Reference:** APRS101 Chapter 7, pages 58-60  
**Current State:** Area objects are parsed as regular position reports — the area-specific
data in the CSE/SPD extension and the type/color encoding are not decoded.  
**File:** Enhance `aprslib/parsing/position.py` and `aprslib/parsing/common.py`

### 2.1 Format Definition

Area objects use the **line/area symbol** with symbol table `\` and symbol code `l`
(lowercase L). When this symbol is detected, the CSE/SPD data extension bytes carry
area type and dimensions instead of course/speed.

Position format is standard (uncompressed or compressed), but after position:

```
Data Extension (7 bytes): Tyy/Cxx
```

| Field | Width | Description |
|-------|-------|-------------|
| T | 1 char | Area type (0-9) |
| yy | 2 chars | Latitude offset in 1/60 degree (~1 nm) |
| / | 1 char | Separator |
| C | 1 char | Color code (0-9) |
| xx | 2 chars | Longitude offset in 1/60 degree |

### 2.2 Area Types

| Code | Shape | Description |
|------|-------|-------------|
| 0 | Open Circle | Unfilled circle |
| 1 | Line (down-right) | From NW corner to SE corner |
| 2 | Open Ellipse | Unfilled ellipse (rotated) |
| 3 | Open Triangle | Unfilled triangle |
| 4 | Open Rectangle | Unfilled rectangle |
| 5 | Filled Circle | Color-filled circle |
| 6 | Filled Line | Color-filled line corridor |
| 7 | Filled Ellipse | Color-filled ellipse |
| 8 | Filled Triangle | Color-filled triangle |
| 9 | Filled Rectangle | Color-filled rectangle |

### 2.3 Color Codes

| Code | Color |
|------|-------|
| 0 | Black |
| 1 | Blue |
| 2 | Green |
| 3 | Cyan |
| 4 | Red |
| 5 | Violet/Purple |
| 6 | Yellow |
| 7 | Grey |
| 8 | (reserved) |
| 9 | (reserved) |

### 2.4 Parsing Rules

Detection: After parsing position coordinates, check if `symbol_table == '\\' and symbol == 'l'`.

If area symbol detected, interpret the data extension differently:

```python
def parse_area_data_extension(body):
    """
    Parse area object data extension.
    Called when symbol is \\l (area object).
    
    Format: Tyy/Cxx
    T = area type (0-9)
    yy = latitude offset (00-90)
    C = color code (0-9) 
    xx = longitude offset (00-90)
    """
    match = re.match(r'^(\d)(\d{2})/(\d)(\d{2})', body)
    if match:
        area_type = int(match.group(1))
        lat_offset = int(match.group(2))
        color = int(match.group(3))
        lon_offset = int(match.group(4))
        body = body[7:]
        # ...
```

### 2.5 Dimension Interpretation

- **Circle** (types 0, 5): `lat_offset` = radius in 1/60 degree; `lon_offset` = 0
- **Line** (types 1, 6): offsets define the opposite corner relative to center
- **Ellipse** (types 2, 7): `lat_offset` = semi-minor, `lon_offset` = semi-major
- **Triangle** (types 3, 8): offsets define bounding box
- **Rectangle** (types 4, 9): `lat_offset` = half-height, `lon_offset` = half-width

### 2.6 Output Schema

```python
{
    'area_object': {
        'type': str,          # 'circle', 'line', 'ellipse', 'triangle', 'rectangle'
        'type_id': int,       # 0-9
        'filled': bool,       # True for types 5-9
        'color': str,         # 'black', 'blue', etc.
        'color_id': int,      # 0-9
        'lat_offset': float,  # degrees
        'lon_offset': float,  # degrees
    }
}
```

### 2.7 Test Cases

```python
# Circle area object
";PRIOR   *092345z4903.50N\\07201.75Wl088/036"
# → area_object.type='circle', type_id=0, lat_offset=88/60°, color_id=0, lon_offset=36/60°

# Filled rectangle
";ZONE1   *092345z4903.50N\\07201.75Wl910/420"
# → area_object.type='rectangle', type_id=9, filled=True, color_id=1, ...
```

---

## 3. NWS Weather Alerts

**Priority:** MEDIUM  
**Spec Reference:** APRS101 Chapter 16  
**Current State:** Parsed as regular objects — NWS-specific fields in comment not decoded  
**File:** New `aprslib/parsing/nws.py` or enhance weather.py

### 3.1 Format Definition

NWS alerts are APRS Objects (DTI `;`) with a specific naming convention and
comment format. They use the NWS symbol (`/W` for Weather Service Advisory or
`\W` for specific types).

#### Object Name Convention (9 chars)

```
Chars 1-3: Advisory type code
Chars 4-9: Zone/county ID + padding
```

#### Comment Field Format

```
{ADVISORY_TYPE}>DDHHMMz,{ZONE1},{ZONE2},...
```

Where:
- `ADVISORY_TYPE` = NWS advisory type (WIND, TORN, SVR, FLOOD, WINTER, etc.)
- `DDHHMMZ` = Expiration date/time in Zulu
- `ZONE1,ZONE2,...` = FIPS county or zone codes

### 3.2 Advisory Types

| Code | Alert Type |
|------|-----------|
| `WIND` | High Wind Warning/Advisory |
| `TORN` | Tornado Warning |
| `SVR` | Severe Thunderstorm Warning |
| `FLOOD` | Flood Warning/Advisory |
| `WINTER` | Winter Storm Warning |
| `HEAT` | Excessive Heat Warning |
| `FRZE` | Freeze Warning |
| `FIRE` | Fire Weather Watch/Warning |
| `HURR` | Hurricane Warning |
| `TSUN` | Tsunami Warning |

### 3.3 Zone Code Format

```
SS_ZXXX  or  SS_CXXX
```

Where:
- `SS` = 2-letter state code
- `Z` = zone indicator, `C` = county indicator
- `XXX` = 3-digit zone/county number

### 3.4 Parsing Rules

Detection: After parsing an object, check if:
1. Object name matches NWS pattern (3-letter type prefix + zone ID)
2. Comment contains `>` followed by expiration time and zone list

```python
def parse_nws_alert(object_name, comment):
    """
    Attempt to parse NWS alert data from an object's comment field.
    
    Returns None if not an NWS alert, otherwise returns parsed dict.
    """
    # Pattern: TYPE>DDHHMMz,ZONE,ZONE,...
    match = re.match(r'^([A-Z]+)>(\d{6})z,(.+)$', comment)
```

### 3.5 Output Schema

```python
{
    'nws_alert': {
        'advisory_type': str,     # 'TORN', 'SVR', etc.
        'expiration': str,        # 'DDHHMMz' raw timestamp
        'zones': list[str],       # ['MD_C025', 'MD_C027', ...]
    }
}
```

### 3.6 Test Cases

```python
# Tornado warning
";TORNC025*241800z3918.00N/07630.00W_000/000TORN>241800z,MD_C025,MD_C027"
# → nws_alert.advisory_type='TORN', zones=['MD_C025','MD_C027']

# Flood advisory
";FLOODC001*010000z4000.00N/08000.00W_000/000FLOOD>311200z,OH_C001,OH_C003"
# → nws_alert.advisory_type='FLOOD', zones=['OH_C001','OH_C003']
```

---

## 4. Signpost Objects

**Priority:** LOW  
**Spec Reference:** APRS101 Chapter 7 (Objects/Items section)  
**Current State:** Parsed as regular objects — signpost-specific comment not decoded  
**File:** Enhance `aprslib/parsing/position.py`

### 4.1 Format Definition

Signpost objects use symbol table `\` and symbol code `m`. The comment field
contains advisory speed and bearing information.

```
Comment format: SPD/DIR free-text
```

Where:
- `SPD` = Advisory speed (3 digits, mph)
- `DIR` = Bearing/direction the sign faces (3 digits, degrees)
- Remaining = free-text (sign message)

### 4.2 Parsing Rules

Detection: After position parsing, if `symbol_table == '\\' and symbol == 'm'`,
attempt signpost comment parsing.

```python
def parse_signpost_comment(body):
    """
    Parse signpost-specific comment format.
    Format: SSS/DDD text
    """
    match = re.match(r'^(\d{3})/(\d{3})\s*(.*)', body)
    if match:
        speed_mph = int(match.group(1))
        bearing = int(match.group(2))
        text = match.group(3)
        return {
            'signpost': {
                'speed': speed_mph * 1.609344,  # convert to km/h
                'speed_mph': speed_mph,
                'bearing': bearing,
                'text': text,
            }
        }
```

### 4.3 Output Schema

```python
{
    'signpost': {
        'speed': float,        # km/h (advisory speed)
        'speed_mph': int,      # original mph value
        'bearing': int,        # degrees (direction sign faces)
        'text': str,           # sign text content
    }
}
```

### 4.4 Test Cases

```python
# Speed limit sign
";SIGN-I95A*111111z3918.00N\\07630.00Wm055/180 Speed Limit 55"
# → signpost.speed_mph=55, bearing=180, text='Speed Limit 55'

# Curve advisory
";CURVE23  *111111z3920.00N\\07632.00Wm035/270 Sharp Curve Ahead"
# → signpost.speed_mph=35, bearing=270, text='Sharp Curve Ahead'
```

---

## 5. DF Reports (Direction Finding)

**Priority:** MEDIUM  
**Spec Reference:** APRS101 Chapter 18, pages 29-30  
**Current State:** `parse_data_extentions` in `common.py` handles CSE/SPD and
BRG/NRQ partially but does NOT parse the `DFS` data extension format.  
**File:** Enhance `aprslib/parsing/common.py`

### 5.1 Format Definition

DF reports use the `DFS` data extension (7 bytes) which replaces the normal
CSE/SPD data extension in a position report. The DF symbol is `\` table, `\` code.

```
DFSshgd
```

| Byte | Field | Values | Description |
|------|-------|--------|-------------|
| 1-3 | `DFS` | literal | DF report indicator |
| 4 | `s` | 0-9 | Signal strength (S-units) |
| 5 | `h` | 0-9 | Height above avg terrain (code) |
| 6 | `g` | 0-9 | Antenna gain (dBi) |
| 7 | `d` | 0-8 | Directivity code |

### 5.2 Field Decodings

**Signal Strength (s):**

| Code | Meaning |
|------|---------|
| 0 | Not detected |
| 1-8 | S1-S8 |
| 9 | Extremely strong (S9+) |

**Height HAAT (h):**

Formula: `height_feet = 10 * 2^h`

| Code | Height (feet) | Height (meters) |
|------|---------------|-----------------|
| 0 | 10 | 3.0 |
| 1 | 20 | 6.1 |
| 2 | 40 | 12.2 |
| 3 | 80 | 24.4 |
| 4 | 160 | 48.8 |
| 5 | 320 | 97.5 |
| 6 | 640 | 195.1 |
| 7 | 1280 | 390.1 |
| 8 | 2560 | 780.3 |
| 9 | 5120 | 1560.6 |

**Gain (g):** Direct dBi value (0-9)

**Directivity (d):**

| Code | Direction |
|------|-----------|
| 0 | Omni-directional |
| 1 | 45° (NE) |
| 2 | 90° (E) |
| 3 | 135° (SE) |
| 4 | 180° (S) |
| 5 | 225° (SW) |
| 6 | 270° (W) |
| 7 | 315° (NW) |
| 8 | 360° (N) |

### 5.3 BRG/NRQ (Bearing/Number/Range/Quality)

When a DF report includes a bearing, the CSE/SPD field becomes BRG/NRQ:

```
BRG/NRQ format: bbb/nrq
```

- `bbb` = bearing to signal source (000-360 degrees)
- `n` = Number of hits (0-9, 8=best)
- `r` = Range to signal (0-9, in miles)
- `q` = Quality/accuracy (0-9)

**Quality accuracy:**

| Q | Accuracy |
|---|----------|
| 0 | Useless |
| 1 | ±240° |
| 2 | ±120° |
| 3 | ±64° |
| 4 | ±32° |
| 5 | ±16° |
| 6 | ±8° |
| 7 | ±4° |
| 8 | ±2° |
| 9 | ±1° |

### 5.4 Parsing Rules

In `parse_data_extentions()`, add DFS detection before the existing PHG check:

```python
# DFS format: DFSshgd
match = re.findall(r"^DFS(\d)(\d)(\d)(\d)", body)
if match:
    s, h, g, d = match[0]
    body = body[7:]
    parsed.update({
        'df_report': {
            'signal_strength': int(s),
            'height': (10 * (2 ** int(h))) * 0.3048,  # meters
            'gain': int(g),
            'directivity': int(d) * 45 if int(d) > 0 else 'omni',
        }
    })
```

### 5.5 Output Schema

```python
{
    'df_report': {
        'signal_strength': int,    # 0-9 S-units
        'height': float,           # meters HAAT
        'gain': int,               # dBi
        'directivity': int|str,    # degrees or 'omni'
    },
    # If BRG/NRQ present:
    'bearing': int,                # degrees (already handled)
    'nrq': int,                    # Already handled but add detail:
    'df_quality': {
        'hits': int,               # 0-9
        'range': float,            # km (converted from miles)
        'accuracy': int,           # 0-9
    }
}
```

### 5.6 Test Cases

```python
# DF report with DFS extension
"N0CALL>APRS:!4903.50N/07201.75W\\DFS2260"
# → df_report.signal_strength=2, height=12.2m (40ft), gain=6, directivity='omni'

# DF report with BRG/NRQ
"N0CALL>APRS:!4903.50N/07201.75W\\088/036DFS2260"
# → bearing=88, df_quality.hits=0, df_quality.range=4.8km, df_quality.accuracy=6
#   df_report.signal_strength=2, height=12.2m, gain=6, directivity='omni'
```

---

## 6. Peet Bros U-II Raw Weather (`#`)

**Priority:** LOW  
**Spec Reference:** APRS101 Chapter 12  
**Current State:** Raises `UnknownFormat`  
**File:** New `aprslib/parsing/peetbros.py`

### 6.1 Format Definition

The `#` DTI indicates a raw Peet Bros Ultimeter 2000 data log packet. The body
is hex-encoded sensor data.

There are two sub-formats:
1. **Short data log** (`#` DTI): 8 fields × 4 hex chars = 32 hex chars
2. **Complete packet** (`!!` prefix, part of `$` DTI): 46 hex chars

### 6.2 Short Format (`#` DTI)

```
#WWWWDDDDSSSSGGGGTTTTLLLLRRRRPPPP
```

| Offset | Field (4 hex) | Description | Conversion |
|--------|---------------|-------------|------------|
| 0-3 | WWWW | Wind speed | val × 0.1 mph / 256 → km/h |
| 4-7 | DDDD | Wind direction | val × 360 / 256 degrees |
| 8-11 | SSSS | Reserved / Peak speed | Same as wind speed |
| 12-15 | GGGG | Wind gust | Same as wind speed |
| 16-19 | TTTT | Outdoor temperature | (val / 256) × 0.1 °F → °C |
| 20-23 | LLLL | Total rain count | Raw tip count |
| 24-27 | RRRR | Rain since reset | tips × 0.254 mm |
| 28-31 | PPPP | Barometric pressure | val / 256 × 0.1 mbar |

### 6.3 Ultimeter Complete Format (within `$` DTI)

The Ultimeter 2000 can also send complete packets via the `$ULTW` format
(already partially handled in `parse_raw_gps`). That format uses 52 hex chars.

### 6.4 Parsing Rules

```python
def parse_peetbros(body):
    """
    Parse Peet Bros U-II raw weather data.
    
    Input: body after '#' DTI stripped
    Output: ('', parsed_dict)
    """
    parsed = {'format': 'peet-bros-weather'}
    
    # Empty body returns raw_data as empty string (incomplete frame)
    hex_data = body.strip()
    if not hex_data:
        parsed['raw_data'] = ''
        return ('', parsed)

    # Must be complete 4-char hex groups or '----' for missing
    if not re.fullmatch(r'(?:[0-9A-Fa-f]{4}|----)+', hex_data):
        raise ParseError("invalid Peet Bros format: must be 4-char hex groups")
    
    if len(hex_data) < 32:
        # Incomplete data - store raw
        parsed['raw_data'] = hex_data
        return ('', parsed)
    
    # Parse 4-hex-char fields
    fields = [hex_data[i:i+4] for i in range(0, min(len(hex_data), 32), 4)]
    
    # All-zero frame: station online but no valid data yet
    if all(f == '0000' for f in fields):
        parsed['raw_data'] = hex_data
        parsed['weather'] = {}
        return ('', parsed)

    wind_speed_raw = int(fields[0], 16)
    wind_dir_raw = int(fields[1], 16)
    wind_gust_raw = int(fields[3], 16)
    temp_raw = int(fields[4], 16)
    rain_raw = int(fields[6], 16)
    pressure_raw = int(fields[7], 16)
    
    weather = {}
    
    # Wind speed: raw / 256 * 0.1 mph → km/h
    if wind_speed_raw != 0xFFFF:
        weather['wind_speed'] = (wind_speed_raw / 256.0) * 0.1 * 1.609344
    
    # Wind direction: raw * 360 / 256
    if wind_dir_raw != 0xFFFF:
        weather['wind_direction'] = int(wind_dir_raw * 360.0 / 256.0) % 360
    
    # Wind gust
    if wind_gust_raw != 0xFFFF:
        weather['wind_gust'] = (wind_gust_raw / 256.0) * 0.1 * 1.609344
    
    # Temperature: raw / 256 * 0.1 °F → °C
    if temp_raw != 0xFFFF:
        temp_f = temp_raw / 256.0 * 0.1
        # Handle negative (two's complement for 16-bit)
        if temp_raw > 0x7FFF:
            temp_f = -((0xFFFF - temp_raw + 1) / 256.0 * 0.1)
        weather['temperature'] = (temp_f - 32) / 1.8  # to Celsius
    
    # Rain
    if rain_raw != 0xFFFF:
        weather['rain'] = rain_raw * 0.254  # mm
    
    # Pressure: raw / 256 * 0.1 mbar
    if pressure_raw != 0xFFFF:
        weather['pressure'] = pressure_raw / 256.0 * 0.1
    
    parsed['weather'] = weather
    return ('', parsed)
```

### 6.5 Output Schema

```python
{
    'format': 'peet-bros-weather',
    'weather': {
        'wind_speed': float,      # km/h (optional)
        'wind_direction': int,    # degrees (optional)
        'wind_gust': float,       # km/h (optional)
        'temperature': float,     # °C (optional)
        'rain': float,            # mm (optional)
        'pressure': float,        # mbar/hPa (optional)
    }
}
```

### 6.6 Test Cases

```python
# Peet Bros raw data
"N0CALL>APRS:#0046004B006E001A00470000001800EB"
# → format='peet-bros-weather', weather contains decoded values

# All zeros (station not reporting)
"N0CALL>APRS:#00000000000000000000000000000000"
# → format='peet-bros-weather', weather={} (all zero = no data)
```

---

## 7. Telemetry Coefficient Application

**Priority:** MEDIUM  
**Spec Reference:** APRS101 Chapter 13  
**Current State:** `parse_telemetry_config` stores EQNS/PARM/UNIT/BITS but never
applies coefficients to telemetry data reports.  
**File:** New `aprslib/telemetry_store.py` or utility module

### 7.1 Overview

APRS Telemetry uses separate packets for configuration (names, units, equations)
and data. A station sends:
1. `:CALLSIGN :PARM.name1,name2,...` — parameter names
2. `:CALLSIGN :UNIT.unit1,unit2,...` — units
3. `:CALLSIGN :EQNS.a1,b1,c1,a2,b2,c2,...` — conversion equations
4. `:CALLSIGN :BITS.bbbbbbbb,title` — bit sense and project title
5. `T#seq,v1,v2,v3,v4,v5,bbbbbbbb` — data report

The equations convert raw values: `result = a * raw^2 + b * raw + c`

### 7.2 Proposed API

```python
class TelemetryStore:
    """
    Stores telemetry configuration per station and applies
    coefficients to raw telemetry data.
    """
    
    def __init__(self):
        self._configs = {}  # callsign -> config dict
    
    def update_config(self, callsign: str, config: dict):
        """
        Store telemetry config (from parse_telemetry_config result).
        Config keys: tPARM, tUNIT, tEQNS, tBITS, title
        """
        if callsign not in self._configs:
            self._configs[callsign] = {}
        self._configs[callsign].update(config)
    
    def apply(self, callsign: str, telemetry: dict) -> dict:
        """
        Apply stored coefficients to raw telemetry values.
        
        Input telemetry: {'seq': int, 'vals': [float,...], 'bits': str}
        Returns enhanced telemetry with named/converted values.
        """
        config = self._configs.get(callsign, {})
        result = {'seq': telemetry['seq'], 'channels': []}
        
        eqns = config.get('tEQNS', [[0,1,0]]*5)
        parms = config.get('tPARM', ['']*13)
        units = config.get('tUNIT', ['']*13)
        
        for i, raw_val in enumerate(telemetry.get('vals', [])):
            a, b, c = eqns[i] if i < len(eqns) else [0, 1, 0]
            converted = a * (raw_val ** 2) + b * raw_val + c
            
            result['channels'].append({
                'name': parms[i] if i < len(parms) else '',
                'unit': units[i] if i < len(units) else '',
                'raw': raw_val,
                'value': converted,
            })
        
        # Digital channels
        bits_sense = config.get('tBITS', '00000000')
        bits_data = telemetry.get('bits', '00000000')
        
        result['digital'] = []
        for i in range(8):
            sense = int(bits_sense[i]) if i < len(bits_sense) else 0
            value = int(bits_data[i]) if i < len(bits_data) else 0
            # XOR with sense bit for actual state
            result['digital'].append({
                'name': parms[5+i] if (5+i) < len(parms) else '',
                'active': bool(value ^ sense),
                'raw': value,
            })
        
        if 'title' in config:
            result['title'] = config['title']
        
        return result
```

### 7.3 Usage Pattern

```python
store = TelemetryStore()

# When config message arrives:
parsed = parse("N3MIM>APRS::N3MIM    :EQNS.0,2.6,0,0,.53,-32,3,4.39,49,-32,3,18,1,2,3")
store.update_config('N3MIM', parsed)

# When telemetry report arrives:
parsed = parse("N3MIM>APRS:T#123,100,200,150,075,025,11001100")
enhanced = store.apply('N3MIM', parsed['telemetry'])
# → channels[0] = {name:'Battery', unit:'Volts', raw:100, value:260.0}
```

### 7.4 Note

This is an application-layer feature, not a parsing feature. It could be:
- A standalone utility class (recommended)
- An optional post-processing step
- NOT integrated into the core `parse()` function (which is stateless)

---

## 8. Frequency/Tone in Position Comment

**Priority:** MEDIUM  
**Spec Reference:** APRS 1.2 Addendum (aprs.org/info/freqspec.txt)  
**Current State:** Frequency data in comments is not parsed — left as raw comment text  
**File:** Enhance `aprslib/parsing/common.py` `parse_comment()`

### 8.1 Format Definition

A fixed 10-byte frequency field can appear in position comments:

```
FFF.FFFMHz     (7 digits + "MHz" = 10 bytes)
FFF.FF MHz     (5 digits + space + "MHz" = 10 bytes with space-padding)
```

Additional optional fields (each with leading space):

| Format | Description |
|--------|-------------|
| `Tnnn` | PL Tone (nnn = tone × 10, drop tenths: T107 = 107.2 Hz) |
| `Cnnn` | CTCSS code |
| `Dnnn` | DCS code |
| `tnnn` | Narrow-band tone (lowercase = narrow) |
| `oXXX` | Offset in 10s of KHz (+060 = +600 KHz, -060 = -600 KHz) |
| `-000` | Forced simplex |
| `RXXm` | Range in miles |
| `RXXk` | Range in kilometers |

### 8.2 Parsing Rules

```python
def parse_comment_frequency(body):
    """
    Extract frequency/tone info from position comment.
    Returns (remaining_body, parsed_dict)
    """
    parsed = {}
    
    # Match frequency: FFF.FFFMHz or FFF.FF MHz
    freq_match = re.match(r'^(\d{3}\.\d{2,3})\s?MHz', body, re.IGNORECASE)
    if freq_match:
        parsed['frequency'] = float(freq_match.group(1))
        body = body[freq_match.end():]
        
        # Parse optional fields after frequency
        # PL Tone: Tnnn
        tone_match = re.match(r'^\s+[Tt](\d{3})', body)
        if tone_match:
            tone_val = int(tone_match.group(1))
            parsed['tone'] = tone_val  # actual Hz = tone_val + lookup
            body = body[tone_match.end():]
        
        # DCS: Dnnn
        dcs_match = re.match(r'^\s+D(\d{3})', body)
        if dcs_match:
            parsed['dcs'] = int(dcs_match.group(1))
            body = body[dcs_match.end():]
        
        # Offset: +/-nnn (in 10s of KHz)
        offset_match = re.match(r'^\s+([+-]\d{3})', body)
        if offset_match:
            offset_10khz = int(offset_match.group(1))
            parsed['offset'] = offset_10khz * 10  # KHz
            body = body[offset_match.end():]
        
        # Range: Rnnm or Rnnk
        range_match = re.match(r'^\s+R(\d{2})([mk])', body)
        if range_match:
            range_val = int(range_match.group(1))
            range_unit = range_match.group(2)
            if range_unit == 'm':
                parsed['range'] = range_val * 1.609344  # miles to km
            else:
                parsed['range'] = float(range_val)  # already km
            body = body[range_match.end():]
    
    return (body, parsed)
```

### 8.3 Output Schema

```python
{
    'frequency': float,     # MHz (e.g., 146.520)
    'tone': int,            # PL tone code (optional)
    'dcs': int,             # DCS code (optional)
    'offset': int,          # KHz offset (optional, +/-)
    'range': float,         # km (optional)
}
```

### 8.4 Integration Point

Call `parse_comment_frequency()` from `parse_comment()` in `common.py`, before
the general comment assignment. The function should be called after
`parse_data_extentions` and `parse_comment_altitude`.

### 8.5 Test Cases

```python
# Simple frequency
"N0CALL>APRS:!4903.50N/07201.75W-146.520MHz Enroute"
# → frequency=146.52, comment='Enroute'

# Repeater with tone and offset
"N0CALL>APRS:!4903.50N/07201.75Wr147.105MHz T107 +060 AARC Repeater"
# → frequency=147.105, tone=107, offset=600, comment='AARC Repeater'

# Frequency with range
"N0CALL>APRS:!4903.50N/07201.75W-446.000MHz R20m"
# → frequency=446.0, range=32.19 (20mi in km)
```

---

## 9. Mic-E Device Type Detection

**Priority:** LOW  
**Spec Reference:** APRS 1.2, Kenwood/Yaesu/Anytone extensions  
**Current State:** Mic-E status text stored as raw comment; device type not extracted  
**File:** Enhance `aprslib/parsing/mice.py`

### 9.1 Format Definition

The Mic-E status text field has a structured ending that identifies the device:

```
Text field: {status_text}{type_suffix}
```

The last 1-2 bytes identify the transmitting device.

### 9.2 Device Type Table

| Suffix Pattern | Device | Message Capable |
|---------------|--------|-----------------|
| `>` at end | Kenwood TH-D7A | Yes |
| `]` at end | Kenwood TM-D700 | Yes |
| `]=` at end (2 bytes) | Kenwood TM-D710 | Yes |
| `>=` at end | Kenwood TH-D72 | Yes |
| `>^` at end | Kenwood TH-D74 | Yes |
| `_b` at end (b=space) | Yaesu VX-8 | Yes |
| `_"` at end | Yaesu FTM-350 | Yes |
| `_#` at end | Yaesu VX-8G | Yes |
| `_$` at end | Yaesu FT1D | Yes |
| `_%` at end | Yaesu FTM-400DR | Yes |
| `_)` at end | Yaesu FTM-100D | Yes |
| `_(` at end | Yaesu FT2D | Yes |
| `_0` at end | Yaesu FT3D | Yes |
| `_3` at end | Yaesu FT5D | Yes |
| `_1` at end | Yaesu FTM-300D | Yes |
| `(5` at end | Anytone D578UV | Yes |
| `(8` at end | Anytone D878UV | No |
| `\|3` at end | Byonics TinyTrack3 | No |
| `\|4` at end | Byonics TinyTrack4 | No |
| `:4` at end | SCS P4dragon DR-7400 | No |

### 9.3 Parsing Rules

After extracting the Mic-E comment/status text, check the suffix:

```python
MICE_DEVICE_TABLE = {
    '>=': 'Kenwood TH-D72',
    '>^': 'Kenwood TH-D74',
    ']=': 'Kenwood TM-D710',
    '_b': 'Yaesu VX-8',       # b = space (0x20)
    '_"': 'Yaesu FTM-350',
    '_#': 'Yaesu VX-8G',
    '_$': 'Yaesu FT1D',
    '_%': 'Yaesu FTM-400DR',
    '_)': 'Yaesu FTM-100D',
    '_(': 'Yaesu FT2D',
    '_0': 'Yaesu FT3D',
    '_3': 'Yaesu FT5D',
    '_1': 'Yaesu FTM-300D',
    '(5': 'Anytone D578UV',
    '(8': 'Anytone D878UV',
    '|3': 'Byonics TinyTrack3',
    '|4': 'Byonics TinyTrack4',
    ':4': 'SCS P4dragon DR-7400',
    '>': 'Kenwood TH-D7A',     # 1-char (check AFTER 2-char)
    ']': 'Kenwood TM-D700',    # 1-char
}

def detect_mice_device(comment):
    """Detect Mic-E device type from comment suffix."""
    # Check 2-char suffixes first
    if len(comment) >= 2:
        suffix2 = comment[-2:]
        # Handle Yaesu space suffix
        if suffix2 == '_ ':
            return 'Yaesu VX-8', comment[:-2]
        if suffix2 in MICE_DEVICE_TABLE:
            return MICE_DEVICE_TABLE[suffix2], comment[:-2]
    
    # Check 1-char suffixes
    if len(comment) >= 1:
        suffix1 = comment[-1:]
        if suffix1 in ('>', ']'):
            return MICE_DEVICE_TABLE[suffix1], comment[:-1]
    
    return None, comment
```

### 9.4 Output Schema

```python
{
    'device': str,           # Device name (optional, if detected)
    'comment': str,          # Status text with device suffix removed
}
```

### 9.5 Test Cases

```python
# Kenwood TH-D72
"`lllc/s$/ Enroute>="
# → device='Kenwood TH-D72', comment='Enroute'

# Yaesu FT3D
"`lllc/s$/ Mobile_0"
# → device='Yaesu FT3D', comment='Mobile'
```

---

## 10. Digipeater Path Analysis

**Priority:** LOW  
**Spec Reference:** APRS101 Chapter 4, New-N Paradigm  
**Current State:** `parse_header` extracts the raw path list and the `via` field.
No analysis of hop count, WIDEn-N consumption, or has-been-digipeated markers.  
**File:** New `aprslib/parsing/path.py` or enhance `common.py`

### 10.1 Format Definition

The APRS path (digipeater addresses) has these conventions:

- `WIDE1-1,WIDE2-1` — standard 2-hop path (fill-in + wide)
- `WIDE2-2` — 2-hop wide only
- `*` suffix on a callsign = has been digipeated through that station
- `qXX` = APRS-IS q-construct (qAR, qAC, qAo, etc.)
- `RFONLY` / `NOGATE` = do not gate to APRS-IS

### 10.2 q-Construct Types

| Construct | Meaning |
|-----------|---------|
| `qAC` | Packet entered IS from client without messaging |
| `qAX` | Packet entered from server |
| `qAU` | Packet entered from server with message capability |
| `qAo` | Packet entered from RF via IGate (no messaging) |
| `qAO` | Packet entered from RF via IGate (with messaging) |
| `qAr` | Packet entered from RF, relayed to server |
| `qAR` | Packet entered from RF, directly heard by IGate |
| `qAS` | Packet from server-side source |
| `qAZ` | Packet from client at login |

### 10.3 Parsing Rules

```python
def analyze_path(path_list):
    """
    Analyze an APRS digipeater path.
    
    Input: list of path elements (already parsed from header)
    Returns: dict with path analysis
    """
    result = {
        'hops_consumed': 0,
        'hops_remaining': 0,
        'digipeaters': [],
        'is_internet': False,
        'q_construct': None,
        'igate': None,
        'no_gate': False,
    }
    
    for i, element in enumerate(path_list):
        # Check for q-construct
        if re.match(r'^q[A-Z]{2}$', element):
            result['q_construct'] = element
            result['is_internet'] = True
            # Next element after q-construct is the IGate
            if i + 1 < len(path_list):
                result['igate'] = path_list[i + 1]
            continue
        
        # Check for NOGATE/RFONLY
        if element.upper() in ('NOGATE', 'RFONLY'):
            result['no_gate'] = True
            continue
        
        # Check for has-been-digipeated marker
        used = element.endswith('*')
        call = element.rstrip('*')
        
        # Check for WIDEn-N pattern
        wide_match = re.match(r'^(WIDE|TRACE|RELAY)(\d)-(\d)$', call, re.I)
        if wide_match:
            n = int(wide_match.group(2))
            remaining = int(wide_match.group(3))
            consumed = n - remaining
            if used:
                consumed = n  # fully consumed
                remaining = 0
            result['hops_consumed'] += consumed
            result['hops_remaining'] += remaining
        elif used:
            result['hops_consumed'] += 1
            result['digipeaters'].append(call)
    
    result['total_hops'] = result['hops_consumed'] + result['hops_remaining']
    
    return result
```

### 10.4 Output Schema

```python
{
    'path_info': {
        'hops_consumed': int,     # Hops already used
        'hops_remaining': int,    # Hops remaining
        'total_hops': int,        # Total configured hops
        'digipeaters': list[str], # Callsigns that digipeated (with * removed)
        'is_internet': bool,      # True if q-construct present
        'q_construct': str|None,  # 'qAR', 'qAo', etc.
        'igate': str|None,        # IGate callsign
        'no_gate': bool,          # True if NOGATE/RFONLY in path
    }
}
```

### 10.5 Integration Point

Call `analyze_path()` after `parse_header()` in the main `parse()` function
and add results to `parsed` dict. This is optional/configurable since it adds
overhead for users who don't need path analysis.

### 10.6 Test Cases

```python
# RF packet digipeated once
"N0CALL>APRS,WIDE1*,WIDE2-1:!4903.50N/07201.75W-"
# → hops_consumed=1, hops_remaining=1, total_hops=2

# Packet from APRS-IS
"N0CALL>APRS,TCPIP*,qAR,IGATE1:!4903.50N/07201.75W-"
# → is_internet=True, q_construct='qAR', igate='IGATE1'

# NOGATE packet
"N0CALL>APRS,RFONLY,WIDE1-1:!4903.50N/07201.75W-"
# → no_gate=True, hops_remaining=1
```

---

## 11. Symbol Table Decoding

**Priority:** LOW  
**Spec Reference:** APRS101 Chapter 20, aprs.org/symbols/symbolsX.txt  
**Current State:** Symbol table character and code stored raw. No human-readable decoding.  
**File:** New `aprslib/symbols.py`

### 11.1 Overview

APRS uses two symbol tables (primary `/` and alternate `\`) with overlay characters
(0-9, A-Z) that can replace the alternate table character.

### 11.2 Implementation

A lookup table mapping `(table, code)` to description string:

```python
# Primary table (/) - 94 symbols (0x21-0x7E)
PRIMARY_SYMBOLS = {
    '!': 'Police Station',
    '"': 'reserved',
    '#': 'Digi (green star)',
    '$': 'Phone',
    '%': 'DX Cluster',
    '&': 'HF Gateway',
    "'": 'Aircraft (small)',
    '(': 'Mobile Satellite Station',
    ')': 'Wheelchair',
    '*': 'Snowmobile',
    '+': 'Red Cross',
    ',': 'Boy Scouts',
    '-': 'House QTH',
    '.': 'X',
    '/': 'Red Dot',
    # ... full table
    '_': 'Weather Station (Blue)',
    # ... etc
}

ALTERNATE_SYMBOLS = {
    '!': 'Emergency',
    '#': 'Digi (green star w/overlay)',
    # ... etc
}

def decode_symbol(symbol_table, symbol_code):
    """
    Decode APRS symbol to human-readable description.
    
    Returns: {'description': str, 'overlay': str|None}
    """
```

### 11.3 Output Schema

```python
{
    'symbol_description': str,  # 'Weather Station', 'Car', etc.
    'symbol_overlay': str|None, # Overlay character if present
}
```

### 11.4 Note

This is a large static lookup table (~188 entries). Consider loading from a
data file rather than embedding in code. The table should be optional/lazy-loaded.

---

## 12. Item-in-Message

**Priority:** LOW  
**Spec Reference:** APRS 1.2 Addendum  
**Current State:** Not detected — parsed as regular message  
**File:** Enhance `aprslib/parsing/message.py`

### 12.1 Format Definition

An APRS item can be embedded inside a message for reliable delivery:

```
:ADDRESSEE:)ITEMNAME!DDMM.mmN/DDDMM.mmW$comment{lineno
```

Where:
- Standard message wrapper (`:ADDRESSEE:`)
- Message body starts with `)` indicating item content
- Followed by standard item format (name + `!`/`_` + position)

### 12.2 Parsing Rules

In `parse_message()`, after extracting the addressee, check if the message body
starts with `)`:

```python
# Check for Item-in-Message
if body.startswith(')'):
    # Parse as item report
    _, item_result = parse_position(')', body[1:])
    parsed.update({
        'format': 'item-in-message',
        'item': item_result,
    })
    break
```

### 12.3 Output Schema

```python
{
    'format': 'item-in-message',
    'addresse': str,
    'msgNo': str,              # If present
    'item': {                  # Full item parse result
        'item_name': str,
        'alive': bool,
        'latitude': float,
        'longitude': float,
        'symbol': str,
        'symbol_table': str,
        'comment': str,
    }
}
```

### 12.4 Test Cases

```python
# Item-in-message
"N0CALL>APRS::W1ABC    :)FUEL!4903.50N/07201.75W-Gas Station{001"
# → format='item-in-message', addresse='W1ABC', item.item_name='FUEL'
```

---

## 13. Weather Extensions (APRS 1.2)

**Priority:** LOW  
**Spec Reference:** APRS 1.2.1 (March 2011)  
**Current State:** Standard weather fields parsed; new 1.2 fields ignored  
**File:** Enhance `aprslib/parsing/weather.py`

### 13.1 New Weather Fields

| Code | Field | Units | Description |
|------|-------|-------|-------------|
| `X` | Radiation | nSv/hr (resistor code) | Nuclear/radiation level |
| `F` | Water Level | tenths of foot | Flood stage (±999) |
| `V` | Battery | tenths of volt | Station battery voltage |
| `Z` | Device Type | integer | Weather station model ID |

### 13.2 Radiation Format (Resistor Code)

```
Xxxx
```

Where `xxx` uses resistor color code: first 2 digits are significand, 3rd is
power of 10.

Example: `X123` = 12 × 10³ nSv/hr = 12 µSv/hr

### 13.3 Water Level Format

```
Fxxxx
```

Where `xxxx` is signed integer in tenths of foot (-9999 to +9999).
Negative values use `-` as first character: `F-035` = -3.5 feet.

### 13.4 Parsing Rules

Add to `key_map` and `val_map` in `weather.py`:

```python
# Add to key_map
'X': 'radiation',
'F': 'water_level',
'V': 'battery',
'Z': 'device_type',

# Add to val_map  
'X': lambda x: _decode_radiation(x),  # resistor code to nSv/hr
'F': lambda x: float(x) * 0.03048,    # tenths of foot to meters
'V': lambda x: int(x) / 10.0,         # tenths to volts
'Z': lambda x: int(x),                # device type ID

def _decode_radiation(val_str):
    """Decode resistor-code radiation value to nSv/hr."""
    if len(val_str) == 3:
        significand = int(val_str[0:2])
        exponent = int(val_str[2])
        return significand * (10 ** exponent)
    return int(val_str)
```

### 13.5 Update Regex

The weather data regex in `parse_weather_data` needs to be extended:

```python
# Current:
r"^([cSgtrpPlLs#][0-9\-\. ]{3}|h[0-9\. ]{2}|b[0-9\. ]{5})+"

# Extended:
r"^([cSgtrpPlLs#XV][0-9\-\. ]{3}|h[0-9\. ]{2}|b[0-9\. ]{5}|F[\-0-9]{4}|Z\d{2})+"
```

### 13.6 Test Cases

```python
# Radiation reading
"...c180s005g010t077X123..."
# → weather.radiation = 12000 nSv/hr (12 µSv/hr)

# Water level
"...c000s000g000t050F-035..."
# → weather.water_level = -1.067 meters (-3.5 ft)

# Battery voltage
"...c090s010g015t065V128..."
# → weather.battery = 12.8 volts
```

---

## 14. Speed Extension (Above Mach 1)

**Priority:** LOW (niche: ISS, high-altitude balloons)  
**Spec Reference:** APRS 1.2  
**Current State:** Speed decoded normally; above-Mach extension not applied  
**File:** Enhance `aprslib/parsing/position.py`

### 14.1 Format Definition

For compressed position reports, when the encoded speed value exceeds 670 knots
(the normal max for the exponential encoding), a linear extension applies:

```
If encoded_speed > 670 knots:
    actual_speed = encoded_speed * 112 - 74370 knots
```

This allows encoding speeds up to ~89,000 knots (ISS orbital velocity).

### 14.2 Parsing Rules

In `parse_compressed()`, after computing speed:

```python
# Current code (line ~143):
parsed.update({'speed': (1.08 ** s1 - 1) * 1.852})

# Enhanced:
speed_knots = 1.08 ** s1 - 1
if speed_knots > 670:
    speed_knots = speed_knots * 112 - 74370
parsed.update({'speed': speed_knots * 1.852})
```

### 14.3 Test Cases

```python
# ISS-speed compressed packet (speed byte encoding for ~27600 km/h)
# This is rare; test with calculated values
```

---

## Implementation Order (Recommended)

1. **Query (`?`)** — New parser module, highest user impact
2. **Frequency/Tone** — Enhances existing comment parsing, common in real traffic
3. **DF Reports** — Small addition to existing data extensions parser
4. **Area Objects** — Enhancement to position parser
5. **NWS Weather Alerts** — Enhancement to object parser
6. **Telemetry Store** — New utility class (application-layer)
7. **Mic-E Device Type** — Small enhancement to Mic-E parser
8. **Weather Extensions** — Small addition to weather parser
9. **Peet Bros Raw (`#`)** — New parser module
10. **Digipeater Path** — New utility (optional feature)
11. **Item-in-Message** — Small enhancement to message parser
12. **Symbol Decoding** — Static lookup table (optional feature)
13. **Signpost Objects** — Small enhancement
14. **Speed Extension** — One-line fix

---

## Additional Considerations

### Not Implemented (and shouldn't be)

- **Reserved DTIs** (`&`, `(`, `+`, `-`, `.`, `\`, `]`, `^`): Not defined in spec
- **APRS Messaging responses**: Generating responses is a transmit-side concern
- **Query response timing**: Application-layer concern
- **Digipeater behavior**: Infrastructure concern, not a parser concern

### Backward Compatibility

All changes should be additive:
- New fields added to parsed dict (existing fields unchanged)
- New `format` values for new packet types
- `unsupported_formats` dict shrinks as features are implemented
- No breaking changes to existing parse output schema

### Testing Strategy

Each feature should include:
1. Unit tests with known-good packets from the spec
2. Real-world packet samples (from APRS-IS logs)
3. Edge cases (empty fields, maximum values, malformed data)
4. Regression tests ensuring existing parsing unchanged
