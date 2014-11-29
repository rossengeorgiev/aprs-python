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

logger = logging.getLogger(__name__)
logging.raiseExceptions = False
logging.addLevelName(11, "ParseError")


class GenericError(Exception):
    """
    Base exception class for the library. Logs information via logging module
    """
    def __init__(self, message):
        logger.debug("%s: %s", self.__class__.__name__, message)
        self.message = message

    def __str__(self):
        return self.message


class UnknownFormat(GenericError):
    """
    Raised when aprs.parse() encounters an unsupported packet format

    """
    def __init__(self, message, packet=''):
        logger.log(9, "%s\nPacket: %s", message, packet)
        self.message = message
        self.packet = packet


class ParseError(GenericError):
    """
    Raised when unexpected format of a supported packet format is encountered
    """
    def __init__(self, message, packet=''):
        logger.log(11, "%s\nPacket: %s", message, packet)
        self.message = message
        self.packet = packet


class LoginError(GenericError):
    """
    Raised when IS servers didn't respond correctly to our loging attempt
    """
    def __init__(self, message):
        logger.error("%s: %s", self.__class__.__name__, message)
        self.message = message


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
