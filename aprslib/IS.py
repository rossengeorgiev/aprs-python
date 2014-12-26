# aprs - Python library for dealing with APRS
# Copyright (C) 2013-2014 Rossen Georgiev
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
IS class is used for connection to APRS-IS network
"""
import socket
import select
import time
import logging
import sys

from .version import __version__
from .parse import parse
from .exceptions import (
    GenericError,
    ConnectionDrop,
    ConnectionError,
    LoginError,
    )

__all__ = ['IS']


class IS(object):
    """
    The IS class is used to connect to aprs-is network and listen to the stream
    of packets. You can either run them through aprs.parse() or get them in raw
    form.

    Note: sending of packets is not supported yet

    """
    def __init__(self, callsign, passwd="-1", host="rotate.aprs.net", port=14580):
        """
        callsign        - used when login in
        passwd          - for verification, or "-1" if only listening
        Host & port     - aprs-is server
        """

        self.logger = logging.getLogger(__name__)

        self.set_server(host, port)
        self.set_login(callsign, passwd)

        self.sock = None
        self.filter = "t/poimqstunw"  # default filter, everything

        self._connected = False
        self.buf = ''

    def callsign_filter(self, callsigns):
        """
        Sets a filter for the specified callsigns.
        Only those will be sent to us by the server
        """

        if type(callsigns) is not list or len(callsigns) == 0:
            return False

        return self.set_filter("b/%s" % "/".join(callsigns))

    def set_filter(self, filter_text):
        """
        Set a specified aprs-is filter for this connection
        """
        self.filter = filter_text

        self.logger.info("Setting filter to: %s", self.filter)

        if self._connected:
            self.sock.sendall("#filter %s\r\n" % self.filter)

        return True

    def set_login(self, callsign, passwd):
        """
        Set callsign and password
        """
        self.callsign = callsign
        self.passwd = passwd

    def set_server(self, host, port):
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
                    self.logger.info("Attempting connection to %s:%s", self.server[0], self.server[1])
                    self._connect()

                    self.logger.info("Sending login information")
                    self._send_login()

                    self.logger.info("Filter set to: %s", self.filter)

                    if self.passwd == "-1":
                        self.logger.info("Login successful (receive only)")
                    else:
                        self.logger.info("Login successful")

                    break
                except:
                    if not blocking:
                        raise

                time.sleep(30)  # attempt to reconnect after 30 seconds

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

        immortal: When true, consumer will try to reconnect and stop propagation of Parse exceptions
                  if false (default), consumer will return

        raw: when true, raw packet is passed to callback, otherwise the result from aprs.parse()
        """

        if not self._connected:
            raise ConnectionError("not connected to a server")

        line = ''

        while True:
            try:
                for line in self._socket_readlines(blocking):
                    if line[0] != "#":
                        if raw:
                            callback(line)
                        else:
                            callback(parse(line))
            except (KeyboardInterrupt, SystemExit):
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
                self.logger.error("APRS Packet: %s", line)
                raise

            if not blocking:
                break

    def _connect(self):
        """
        Attemps to open a connection to the server
        """

        try:
            # 15 seconds connection timeout
            self.sock = socket.create_connection(self.server, 15)

            # 5 second timeout to receive server banner
            self.sock.setblocking(1)
            self.sock.settimeout(5)

            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

            if sys.platform not in ['cygwin', 'win32']:
                # these things don't exist in socket under Windows
                # pylint: disable=E1103
                self.sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 15)
                self.sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 3)
                self.sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 5)
                # pylint: enable=E1103

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
        login_str = "user {0} pass {1} vers aprslib {3} filter {2}\r\n"
        login_str = login_str.format(
            self.callsign,
            self.passwd,
            self.filter,
            __version__
            )

        try:
            self.sock.sendall(login_str)
            self.sock.settimeout(5)
            test = self.sock.recv(len(login_str) + 100)

            (x, x, callsign, status, x) = test.split(' ', 4)

            if callsign == "":
                raise LoginError("No callsign provided")
            if callsign != self.callsign:
                raise LoginError("Server: %s" % test[2:])
            if status != "verified," and self.passwd != "-1":
                raise LoginError("Password is incorrect")

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
            self.sock.setblocking(0)
        except socket.error, e:
            raise ConnectionDrop("connection dropped")

        while True:
            short_buf = ''

            select.select([self.sock], [], [], None if blocking else 0)

            try:
                short_buf = self.sock.recv(4096)

                # sock.recv returns empty if the connection drops
                if not short_buf:
                    raise ConnectionDrop("connection dropped")
            except socket.error, e:
                if "Resource temporarily unavailable" in e:
                    if not blocking:
                        if len(self.buf) == 0:
                            break
            except Exception:
                raise

            self.buf += short_buf

            while "\r\n" in self.buf:
                line, self.buf = self.buf.split("\r\n", 1)

                yield line
