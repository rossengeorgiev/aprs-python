# Copyright 2013-2014 (C) Rossen Georgiev

import socket
import time
import datetime
import re
import math
import logging
import sys


logger = logging.getLogger(__name__)
logging.addLevelName(11, "ParseError")

__all__ = ['IS', 'GenericError', 'ParseError', 'UnknownFormat',
           'LoginError', 'ConnectionError', 'ConnectionDrop', 'parse']

# IS class is used to connect to aprs-is servers and listen to the feed

class IS(object):
    def __init__(self, host, port, callsign, passwd):
        """
        APRS module that listens and parses sentences passed by aprs.net servers
        """

        self.set_server(host, port)
        self.set_login(callsign, passwd)

        self.sock = None
        self.filter = "b/" # empty bud filter

        self._connected = False
        self.buf = ''

    def callsign_filter(self, callsigns):
        """
        Sets a filter for the specified callsigns. Only those will be sent to us by the server
        """

        if type(callsigns) is not list or len(callsigns) == 0:
            return False

        return self.set_filter("b/%s" % "/".join(callsigns))

    def set_filter(self, filter):
        self.filter = filter

        logger.info("Setting filter to: %s" % self.filter)

        if self._connected:
            self.sock.sendall("#filter %s\r\n" % self.filter)

        return True

    def set_login(self, callsign, passwd):
        """
        Set callsign and password
        """
        self.callsign = callsign
        self.passwd = passwd

    def set_server(self, host, port=14850):
        """
        Set server ip/host and port to use
        """
        self.server = (host, port)

    def connect(self, blocking=False):
        """
        Initiate connection to APRS server and attempt to login
        """

        if not self._connected:
            while True:
                try:
                    logger.info("Attempting connection to %s:%s" % (self.server[0], self.server[1]))
                    self._connect()

                    logger.info("Sending login information")
                    self._send_login()

                    logger.info("Filter set to: %s" % self.filter)

                    if self.passwd == "-1":
                        logger.info("Login successful (receive only)")
                    else:
                        logger.info("Login successful")

                    break
                except:
                    if not blocking:
                        raise

                time.sleep(30) # attempt to reconnect after 30 seconds

    def close(self):
        """
        Closes the socket
        Called internally when Exceptions are raised
        """

        self._connected = False
        self.buf = ''

        if self.sock is not None:
            self.sock.close()

    def consumer(self, callback, blocking=True, immortal=False, raw=False):
        """
        When a position sentence is received, it will be passed to the callback function

        blocking: if true (default), runs forever, otherwise will return after one sentence
                  You can still exit the loop, by raising StopIteration in the callback function

        immortal: When true, consumer will try to reconnect and stop propagation of Parse exceptions.
                  if false (default), consumer will return

        raw: when true, raw aprs sentence is passed to the callback, otherwise parsed data as dict
        """

        if not self._connected:
            raise ConnectionError("not connected to a server")

        while True:
            try:
                for line in self._socket_readlines(blocking):
                    if line[0] != "#":
                        if raw:
                            callback(line)
                        else:
                            callback(parse(line))
            except KeyboardInterrupt:
                raise
            except (ConnectionDrop, ConnectionError):
                self.close()

                if not immortal:
                    raise
                else:
                    self.connect(blocking=blocking)
                    continue
            except GenericError:
                continue
            except StopIteration:
                break
            except:
                #if not immortal:
                #    raise
                #logger.exception(e)
                #continue
                logger.error("APRS Packet: " + line)
                raise

            if not blocking:
                break

    def _connect(self):
        """
        Attemps to open a connection to the server, retries if it fails
        """

        try:
            self.sock = socket.create_connection(self.server, 15) # 15 seconds connection timeout

            self.sock.settimeout(5) # 5 second timeout to receive server banner
            self.sock.setblocking(True)

            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

            if sys.platform not in ['cygwin','win32']:
                self.sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 15)
                self.sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 3)
                self.sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 5)

            if self.sock.recv(512)[0] != "#":
                raise ConnectionError("invalid banner from server")


        except Exception, e:
            self.close()

            if e == "timed out":
                raise ConnectionError("no banner from server")
            else:
                raise ConnectionError(e)

        self._connected = True

    def _send_login(self):
        """
        Sends login string to server
        """
        login_str = "user {0} pass {1} vers pytinyaprs 0.2 filter {2}\r\n".format(self.callsign, self.passwd, self.filter)

        try:
            self.sock.sendall(login_str)
            self.sock.settimeout(5)
            test = self.sock.recv(len(login_str) + 100)
            self.sock.setblocking(True)

            (x, x, callsign, status, x) =  test.split(' ',4)

            if callsign != self.callsign:
                raise LoginError("login callsign does not match")
            if status != "verified," and self.passwd != "-1":
                raise LoginError("callsign is not 'verified'")

        except LoginError, e:
            self.close()
            raise LoginError("failed to login: %s" % e)
        except:
            self.close()
            raise LoginError("failed to login")

    def _socket_readlines(self, blocking=False):
        """
        Generator for complete lines, received from the server
        """
        try:
            self.sock.setblocking(False)
        except socket.error, e:
            raise ConnectionDrop("connection dropped")

        while True:
            short_buf = ''

            try:
                short_buf = self.sock.recv(1024)

                # sock.recv returns empty if the connection drops
                if not short_buf:
                    raise ConnectionDrop("connection dropped")
            except socket.error, e:
                if "Resource temporarily unavailable" in e:
                    if not blocking:
                        if len(self.buf) == 0:
                            break;
            except Exception:
                raise

            self.buf += short_buf

            while "\r\n" in self.buf:
                line, self.buf = self.buf.split("\r\n", 1)

                yield line

                if not blocking:
                    raise StopIteration

            # in blocking mode this will fast if there is no data
            # so we should sleep and not hog the CPU
            if blocking:
                time.sleep(0.5)


# Mic-e message type table

MTYPE_TABLE_STD = {
    "111": "M0: Off Duty",
    "110": "M1: En Route",
    "101": "M2: In Service",
    "100": "M3: Returning",
    "011": "M4: Committed",
    "010": "M5: Special",
    "001": "M6: Priority",
    "000": "Emergency",
    }
MTYPE_TABLE_CUSTOM = {
    "111": "C0: Custom-0",
    "110": "C1: Custom-1",
    "101": "C2: Custom-2",
    "100": "C3: Custom-3",
    "011": "C4: Custom-4",
    "010": "C5: Custom-5",
    "001": "C6: Custom-6",
    "000": "Emergency",
    }

# routine for decoding base91 values of arbitrary length

def base91(text):
    decimal = 0
    length = len(text);
    for i in range(length):
        decimal += (ord(text[i]) - 33) * (91.0 ** (length-1-i))

    return decimal if text != '' else ''

# parse a single packet
# throws expcetions

def parse(raw_sentence):
    """
    Parses position sentences and returns a dict with the useful data
    All attributes are in meteric units
    """

    raw_sentence = raw_sentence.rstrip("\r\n")
    logger.debug("Parsing: %s" % raw_sentence)

    if len(raw_sentence) == 0:
        raise ParseError("packet is empty", raw_sentence)

    try:
        (header, body) = raw_sentence.split(':',1)
    except:
        raise ParseError("packet has no body", raw_sentence)

    if len(body) == 0:
        raise ParseError("packet body is empty", raw_sentence)

    if not re.match(r"^[ -~]+$", header):
        raise ParseError("packet header contains non-ascii characters ", raw_sentence)

    try:
        (fromcall, path) = header.split('>',1)
    except:
        raise ParseError("invalid packet header", raw_sentence)

    # TODO: validate callsigns??

    path = path.split(',')

    if len(path) < 1 or len(path[0]) == 0:
        raise ParseError("no tocallsign", raw_sentence)

    tocall  = path[0]
    path = path[1:]

    parsed = {
                'raw': raw_sentence,
                'from': fromcall,
                'to': tocall,
                'path': path,
             }

    try:
        viacall = path[-1] if re.match(r"^qA[CXUoOSrRRZI]$", path[-2]) else ""
        parsed.update({ 'via': viacall })
    except:
        pass

    packet_type = body[0]
    body = body[1:]

    if len(body) == 0 and packet_type != '>':
        raise ParseError("packet body is empty after packet type character", raw_sentence)

    # attempt to parse the body
    # ------------------------------------------------------------------------------

    # try and parse timestamp first for status and position reports
    if packet_type in '>/@':
        # try to parse timestamp
        match = re.findall(r"^((\d{6})(.))$", body[0:7])
        if match:
            rawts,ts,form = match[0]
            utc = datetime.datetime.utcnow()

            if packet_type == '>' and form != 'z':
                raise ParseError("Time format for status reports should be zulu", raw_sentence)

            parsed.update({ 'raw_timestamp': rawts })

            try:
                if form == 'h': # zulu hhmmss format
                    timestamp = time.mktime(utc.strptime("%s %s %s %s" % (utc.year, utc.month, utc.day, ts), "%Y %m %d %H%M%S").timetuple())
                elif form == 'z': # zulu ddhhss format
                    timestamp = time.mktime(utc.strptime("%s %s %s" % (utc.year, utc.month, ts), "%Y %m %d%M%S").timetuple())
                elif form == '/': # '/' local ddhhss format
                    timestamp = time.mktime(utc.strptime("%s %s %s" % (utc.year, utc.month, ts), "%Y %m %d%M%S").timetuple())
                else:
                    timestamp = 0
            except:
                timestamp = 0

            parsed.update({ 'timestamp': int(timestamp) })

            # remove datetime from the body for further parsing
            body = body[7:]

    # Mic-encoded packet
    #
    # 'lllc/s$/.........         Mic-E no message capability
    # 'lllc/s$/>........         Mic-E message capability
    # `lllc/s$/>........         Mic-E old posit

    if packet_type in "`'":
        logger.debug("Attempting to parse as mic-e packet")
        parsed.update({'format': 'mic-e'})

        dstcall = tocall.split('-')[0]

        # verify mic-e format
        if len(dstcall) != 6:
            raise ParseError("dstcall has to be 6 characters", raw_sentence)
        if len(body) < 8:
            raise ParseError("packet data field is too short", raw_sentence)
        if not re.match(r"^[0-9A-Z]{3}[0-9L-Z]{3}$", dstcall):
            raise ParseError("invalid dstcall", raw_sentence)
        if not re.match(r"^[&-\x7f][&-a][\x1c-\x7f]{2}[\x1c-\x7d][\x1c-\x7f][\x21-\x7e][\/\\0-9A-Z]", body):
            raise ParseError("invalid data format", raw_sentence)

        # get symbol table and symbol
        parsed.update({ 'symbol': body[6], 'symbol_table': body[7] })

        # parse latitude
        # the routine translates each characters into a lat digit as described in
        # 'Mic-E Destination Address Field Encoding' table
        tmpdstcall = ""
        for i in dstcall:
            if i in "KLZ": # spaces
                tmpdstcall += " "
            elif ord(i) > 76: # P-Y
                tmpdstcall += chr(ord(i) - 32)
            elif ord(i) > 57: # A-J
                tmpdstcall += chr(ord(i) - 16)
            else: # 0-9
                tmpdstcall += i

        # determine position ambiguity
        match = re.findall(r"^\d+( *)$", tmpdstcall)
        if not match:
            raise ParseError("invalid latitude ambiguity", raw_sentence)

        posambiguity = len(match[0])
        parsed.update({ 'posambiguity': posambiguity })

        # adjust the coordinates be in center of ambiguity box
        tmpdstcall = list(tmpdstcall)
        if posambiguity > 0:
            if posambiguity >= 4:
                tmpdstcall[2] = '3'
            else:
                tmpdstcall[6 - posambiguity] = '5'

        tmpdstcall = "".join(tmpdstcall)

        latminutes = float( ("%s.%s" % (tmpdstcall[2:4], tmpdstcall[4:6])).replace(" ", "0") )

        if latminutes >= 60:
            raise ParseError("Latitude minutes >= 60", raw_sentence)

        latitude = int(tmpdstcall[0:2]) + (latminutes / 60.0)

        # determine the sign N/S
        latitude = -latitude if ord(dstcall[3]) <= 0x4c else latitude

        parsed.update({ 'latitude': latitude })

        # parse message bits

        mbits = re.sub(r"[0-9L]","0", dstcall[0:3])
        mbits = re.sub(r"[P-Z]","1", mbits)
        mbits = re.sub(r"[A-K]","2", mbits)

        parsed.update({ 'mbits': mbits })

        # resolve message type

        if mbits.find("2") > -1:
            parsed.update({ 'mtype': MTYPE_TABLE_CUSTOM[mbits.replace("2","1")] })
        else:
            parsed.update({ 'mtype': MTYPE_TABLE_STD[mbits] })

        # parse longitude

        longitude = ord(body[0]) - 28 # decimal part of longitude
        longitude += 100 if ord(dstcall[4]) >= 0x50 else 0 # apply lng offset
        longitude += -80 if longitude >= 180 and longitude <= 189 else 0
        longitude += -190 if longitude >= 190 and longitude <= 199 else 0

        # long minutes
        lngminutes = ord(body[1]) - 28.0
        lngminutes += -60 if lngminutes >= 60 else 0

        # + (long hundredths of minutes)
        lngminutes += ((ord(body[2]) - 28.0) / 100.0)

        # apply position ambiguity
        # routines adjust longitude to center of the ambiguity box
        if posambiguity is 4:
            lngminutes = 30
        elif posambiguity is 3:
            lngminutes = (math.floor(lngminutes/10) + 0.5) * 10
        elif posambiguity is 2:
            lngminutes = math.floor(lngminutes) + 0.5
        elif posambiguity is 1:
            lngminutes = (math.floor(lngminutes*10) + 0.5) / 10.0
        elif posambiguity is not 0:
            raise ParseError("Unsupported position ambiguity: %d" % posambiguity, raw_sentence)

        longitude += lngminutes / 60.0

        # apply E/W sign
        longitude = 0 - longitude if ord(dstcall[5]) >= 0x50 else longitude

        parsed.update({ 'longitude': longitude })

        # parse speed and course
        speed = (ord(body[3]) - 28) * 10
        course = ord(body[4]) - 28
        quotient = int(course / 10.0)
        course += -(quotient * 10)
        course = course*100 + ord(body[5]) - 28
        speed += quotient

        speed += -800 if speed >= 800 else 0
        course += -400 if course >= 400 else 0

        speed *= 1.852 # knots * 1.852 = kmph
        parsed.update({'speed': speed, 'course': course })

        # the rest of the packet can contain telemetry and comment

        if len(body) > 8:
            body = body[8:]

            # check for optional 2 or 5 channel telemetry
            match = re.findall(r"^('[0-9a-f]{10}|`[0-9-af]{4})(.*)$", body)
            if match:
                hexdata, body = match[0]

                hexdata = hexdata[1:]           # remove telemtry flag
                channels = len(hexdata) / 2     # determine number of channels
                hexdata = int(hexdata, 16)      # convert hex to int

                telemetry = []
                for i in range(channels):
                    telemetry.insert(0, int(hexdata >> 8*i & 255))

                parsed.update({'telemetry': telemetry})

            # check for optional altitude
            match = re.findall(r"^(.*)([!-{]{3})\}(.*)$", body)
            if match:
                body,altitude,extra = match[0]

                altitude = base91(altitude) - 10000
                parsed.update({'altitude': altitude})

                body = body + extra

            # rest is a comment
            parsed.update({'comment': body})

    # STATUS PACKET
    #
    # >DDHHMMzComments
    # >Comments

    elif packet_type == '>':
        logger.debug("Packet is just a status message")
        parsed.update({'format': 'status', 'comment': body })

    # MESSAGE PACKET
    #
    # :ADDRESSEE:Message text ........{XXXXX    Up to 5 char line number
    # :ADDRESSEE:ackXXXXX                       Ack for same line number
    # :ADDRESSEE:Message text ........{MM}AA    Line# with REPLY ACK
    #
    # TELEMETRY MESSAGES
    #
    # :N3MIM:PARM.Battery,BTemp,AirTemp,Pres,Altude,Camra,Chute,Sun,10m,ATV
    # :N3MIM:UNIT.Volts,deg.F,deg.F,Mbar,Kfeet,Clik,OPEN!,on,on,high
    # :N3MIM:EQNS.0,2.6,0,0,.53,-32,3,4.39,49,-32,3,18,1,2,3
    # :N3MIM:BITS.10110101,PROJECT TITLE...

    elif packet_type == ':':
        # the while loop is used to easily break out once a match is found
        while True:
            # try to match bulletin
            match  = re.findall(r"^BLN([0-9])([a-zA-Z0-9 \-]{5}):(.{0,67})", body)
            if match:
                bid, identifier, text = match[0]
                identifier = identifier.rstrip(' ')

                mformat = 'bulletin' if identifier == "" else 'group-bulletin'

                parsed.update({'format':mformat, 'message_text':text, 'bid':bid, 'identifier': identifier})
                break

            # try to match announcement
            match  = re.findall(r"^BLN([A-Z])([a-zA-Z0-9 \-]{5}):(.{0,67})", body)
            if match:
                aid, identifier, text = match[0]
                identifier = identifier.rstrip(' ')

                parsed.update({'format':'announcement', 'message_text':text, 'aid':aid, 'identifier': identifier})
                break

            # validate addresse
            match  = re.findall(r"^([a-zA-Z0-9 \-]{9}):(.*)$", body)
            if not match:
                raise ParseError("invalid addresse in message", raw_sentance)

            addresse,body = match[0]

            parsed.update({'addresse': addresse.rstrip(' ')})

            # check if it's a telemetry configuration message
            match  = re.findall(r"^(PARM|UNIT|EQNS|BITS)\.(.*)$", body)
            if match:
                logger.debug("Attempting to parse telemetry-message packet")
                form,body = match[0]

                parsed.update({'format': 'telemetry-message'})

                if form in ["PARM", "UNIT"]:
                    vals = body.split(',')[:13]

                    for val in vals:
                        if not re.match(r"^(.{1,20}|)$", val):
                            raise ParseError("incorrect format of %s (name too long?)" % form, raw_sentence)

                    defvals = [''] * 13
                    defvals[:len(vals)] = vals

                    parsed.update({ 't%s' % form : defvals })
                elif form == "EQNS":
                    eqns = body.split(',')[:15]
                    teqns = [0,1,0] * 5

                    for idx,val in zip(range(len(eqns)), eqns):
                        if not re.match("^([-]?\d*\.?\d+|)$", val):
                            raise ParseError("value at %d is not a number in %s" % (idx+1,form), raw_sentence)
                        else:
                            try:
                                val = int(val)
                            except:
                                val = float(val) if val != "" else 0

                            teqns[idx] = val

                    # group values in 5 list of 3
                    teqns = [teqns[i*3:(i+1)*3] for i in range(5)]

                    parsed.update({ 't%s' % form : teqns })
                elif form == "BITS":
                    match = re.findall(r"^([01]{8}),(.{0,23})$", body)
                    if not match:
                        raise ParseError("incorrect format of %s (title too long?)" % form, raw_sentence)

                    bits, title = match[0]

                    parsed.update({ 't%s' % form : bits, 'title': title })

            # regular message
            else:
                logger.debug("Packet is just a regular message")
                parsed.update({'format': 'message'})

                print body
                match  = re.findall(r"^(ack|rej)\{([0-9]{1,5})$", body)
                if match:
                    response, number = match[0]

                    parsed.update({'response': response, 'msgNo': number })
                else:
                    body = body[0:70]

                    match  = re.findall(r"\{([0-9]{1,5})$", body)
                    if match:
                        msgid = match[0]
                        body = body[:len(body) - 1 - len(msgid)]

                        parsed.update( {'msgNo': int(msgid)} )

                    parsed.update({'message_text': body })

            break

    # postion report (regular or compressed)
    #
    # !DDMM.hhN/DDDMM.hhW$...                           POSIT ( no APRS)
    # =DDMM.hhN/DDDMM.hhW$...                           POSIT (APRS message capable)
    # /DDHHMM/DDMM.hhN/DDDMM.hhW$...                    Time of last fix (No APRS)
    # @DDHHMM/DDMM.hhN/DDDMM.hhW$CSE/SPD/...            Moving (with APRS)
    # @DDHHMM/DDMM.hhN/DDDMM.hhW\CSE/SPD/BRG/NRQ/....   DF report
    # ./YYYYXXXX$csT                                    Compressed (Used in any !=/@ format)

    elif packet_type in '!=/@':
        parsed.update({ "messagecapable": packet_type in '@=' })

        if len(body) == 0 and 'timestamp' in parsed:
            raise ParseError("invalid position report format", raw_sentence)

        # comprossed packets start with /
        if re.match(r"^[\/\\A-Za-j][!-|]{8}[!-{}][ -|]{3}", body):
            logger.debug("Attempting to parse as compressed position report")

            if len(body) < 13:
                raise ParseError("Invalid compressed packet (less than 13 characters)", raw_sentence)

            parsed.update({ 'format': 'compressed' })

            packet = body[:13]
            extra = body[13:]

            symbol_table = packet[0]
            symbol = packet[9]

            latitude = 90 - (base91(packet[1:5]) / 380926)
            longitude = -180 + (base91(packet[5:9]) / 190463)

            # parse csT

            # converts the relevant characters from base91
            c1,s1,ctype = [ord(x) - 33 for x in packet[10:13]]

            if c1 == -1:
                parsed.update({'gpsfixstatus': 1 if ctype & 0x20 == 0x20 else 0})

            if -1 in [c1, s1]:
                pass
            elif ctype & 0x18 == 0x10:
                parsed.update({'altitude': (1.002 ** (c1 * 91 + s1)) * 0.3048})
            elif c1 >= 0 and c1 <= 89:
                parsed.update({'course': 360 if c1 == 0 else c1 * 4 })
                parsed.update({'speed': (1.08 ** s1 - 1) * 1.852 }) # mul = convert knts to kmh
            elif c1 == 90:
                parsed.update({'radiorange': (2 * 1.08 ** s1) * 1.609344 }) # mul = convert mph to kmh


        # normal position report
        else:
            logger.debug("Attempting to parse as normal position report")
            parsed.update({ 'format': 'uncompressed' })

            try:
                (
                lat_deg,
                lat_min,
                lat_dir,
                symbol_table,
                lon_deg,
                lon_min,
                lon_dir,
                symbol,
                extra
                ) = re.match(r"^(\d{2})([0-9 ]{2}\.[0-9 ]{2})([NnSs])([\/\\0-9A-Z])(\d{3})([0-9 ]{2}\.[0-9 ]{2})([EeWw])([\x21-\x7e])(.*)$", body).groups()

                # TODO: position ambiguity

                # validate longitude and latitude

                if int(lat_deg) > 89 or int(lat_deg) < 0:
                    raise ParseError("latitude is out of range (0-90 degrees)", raw_sentence)
                if int(lon_deg) > 179 or int(lon_deg) < 0:
                    raise ParseError("longitutde is out of range (0-180 degrees)", raw_sentence)
                #if float(lat_min) >= 60:
                #    raise ParseError("latitude minutes are out of range (0-60)", raw_sentence)
                #if float(lon_min) >= 60:
                #    raise ParseError("longitude minutes are out of range (0-60)", raw_sentence)
                # the above is commented out intentionally
                # apperantly aprs.fi doesn't bound check minutes
                # and there are actual packets that have >60min
                # i don't even know why that's the case

                # convert coordinates from DDMM.MM to decimal

                latitude = int(lat_deg) + ( float(lat_min) / 60.0 )
                longitude = int(lon_deg) + ( float(lon_min) / 60.0 )

                latitude *= -1 if lat_dir in 'Ss' else 1
                longitude *= -1 if lon_dir in 'Ww' else 1

            except:
                # failed to match normal sentence sentence
                raise ParseError("invalid format", raw_sentence)

        # include symbol in the result

        parsed.update({ 'symbol': symbol, 'symbol_table': symbol_table })

        # include longitude and latitude in the result

        parsed.update({'latitude': latitude, 'longitude': longitude})

        # attempt to parse remaining part of the packet (comment field)

        # try CRS/SPD/

        match  = re.findall(r"^([0-9]{3})/([0-9]{3})", extra)
        if match:
            cse, spd = match[0]
            extra = extra[7:]
            parsed.update({'course': int(cse), 'speed': int(spd)*1.852}) # knots to kms

            # try BRG/NRQ/
            match  = re.findall(r"^([0-9]{3})/([0-9]{3})", extra)
            if match:
                brg, nrq = match[0]
                extra = extra[7:]
                parsed.update({'bearing': int(brg), 'nrq': int(nrq)})

        #TODO parse PHG

        # try find altitude in comment /A=dddddd
        match = re.findall(r"^(.*?)/A=(\-\d{5}|\d{6})(.*)$", extra)

        if match:
            extra,altitude,post = match[0]
            extra += post # glue front and back part together, DONT ASK

            parsed.update({ 'altitude': int(altitude)*0.3048 })

        # try parse comment telemetry
        match = re.findall(r"^(.*?)\|([!-{]{2,14})\|(.*)$", extra)
        if match and len(match[0][2]) % 2 == 0:
            extra,telemetry,post = match[0]
            extra += post

            temp = []
            for i in range(7):
                temp.append('')

                try:
                    temp[i] = base91(telemetry[i*2:i*2+2])
                    temp[i] = int(temp[i]) if temp[i].is_integer() else temp[i]
                except:
                    continue

            parsed.update({'telemetry': {'seq': temp[0], 'vals': temp[1:6]}})

            if temp[6] != '':
                parsed['telemetry'].update({'bits': "{0:08b}".format(int(temp[6]))})

        if len(extra) > 0 and extra[0] == "/":
            extra = extra[1:]

        parsed.update({'comment': extra})
    else:
        raise UnknownFormat("format is not supported", raw_sentence)

    logger.debug("Parsed ok.")
    return parsed


# Exceptions
class GenericError(Exception):
    def __init__(self, message):
        logger.debug("%s: %s" % (self.__class__.__name__, message))
        self.message = message

    def __str__(self):
        return self.message

class UnknownFormat(GenericError):
    def __init__(self, message, packet=''):
        logger.log(9, "%s\nPacket: %s" % (message, packet))
        self.message = message
        self.packet = packet

class ParseError(GenericError):
    def __init__(self, message, packet=''):
        logger.log(11, "%s\nPacket: %s" % (message, packet))
        self.message = message
        self.packet = packet

class LoginError(GenericError):
    def __init__(self, message):
        logger.error("%s: %s" % (self.__class__.__name__, message))
        self.message = message

class ConnectionError(GenericError):
    pass

class ConnectionDrop(ConnectionError):
    pass
