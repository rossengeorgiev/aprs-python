"""
Contains exception definitions for the module
"""
import logging

__all__ = [
    "GenericError",
    "UnknownFormat",
    "ParseError",
    "LoginError",
    "ConnectionError",
    "ConnectionDrop",
    ]

logging.raiseExceptions = False
logging.addLevelName(11, "ParseError")
logging.addLevelName(9, "UnknownFormat")


class GenericError(Exception):
    """
    Base exception class for the library. Logs information via logging module
    """
    def __init__(self, message):
        super(GenericError, self).__init__(message)

        self.logger = logging.getLogger(__name__)


class UnknownFormat(GenericError):
    """
    Raised when aprs.parse() encounters an unsupported packet format

    """
    def __init__(self, message, packet=''):
        super(UnknownFormat, self).__init__(message)

        self.packet = packet
        self.logger.log(9, "%s\n    Packet: %s", message, packet)


class ParseError(GenericError):
    """
    Raised when unexpected format of a supported packet format is encountered
    """
    def __init__(self, message, packet=''):
        super(ParseError, self).__init__(message)

        self.packet = packet
        self.logger.log(11, "%s\n    Packet: %s", message, packet)


class LoginError(GenericError):
    """
    Raised when IS servers didn't respond correctly to our loging attempt
    """
    def __init__(self, message):
        super(LoginError, self).__init__(message)

        self.logger.error("%s: %s", self.__class__.__name__, message)


class ConnectionError(GenericError):
    """
    Riased when connection dies for some reason
    """
    pass


class ConnectionDrop(ConnectionError):
    """
    Raised when connetion drops or detected to be dead
    """
    pass
