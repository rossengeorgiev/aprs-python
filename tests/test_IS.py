import unittest2 as unittest
import socket
import sys
import os

import aprslib
from mox3 import mox


# byte shim for testing in both py2 and py3

class TC_IS(unittest.TestCase):
    def setUp(self):
        self.ais = aprslib.IS("LZ1DEV-99", "testpwd", "127.0.0.1", "11111")
        self.m = mox.Mox()

    def tearDown(self):
        self.m.UnsetStubs()

    def test_initilization(self):
        self.assertFalse(self.ais._connected)
        self.assertEqual(self.ais.buf, b'')
        self.assertIsNone(self.ais.sock)
        self.assertEqual(self.ais.callsign, "LZ1DEV-99")
        self.assertEqual(self.ais.passwd, "testpwd")
        self.assertEqual(self.ais.server, ("127.0.0.1", "11111"))

    def test_close(self):
        self.ais._connected = True
        self.ais.sock = mox.MockAnything()
        self.ais.sock.close()
        mox.Replay(self.ais.sock)

        self.ais.close()

        mox.Verify(self.ais.sock)
        self.assertFalse(self.ais._connected)
        self.assertEqual(self.ais.buf, b'')

    def test_open_socket(self):
        with self.assertRaises(socket.error):
            self.ais._open_socket()

    def test_socket_readlines(self):
        fdr, fdw = os.pipe()
        f = os.fdopen(fdw, 'w')
        f.write("something")
        f.close()

        self.m.ReplayAll()
        self.ais.sock = mox.MockAnything()
        # part 1 - conn drop before setblocking
        self.ais.sock.setblocking(0).AndRaise(socket.error)
        # part 2 - conn drop trying to recv
        self.ais.sock.setblocking(0)
        self.ais.sock.fileno().AndReturn(fdr)
        self.ais.sock.recv(mox.IgnoreArg()).AndReturn(b'')
        # part 3 - nothing to read
        self.ais.sock.setblocking(0)
        self.ais.sock.fileno().AndReturn(fdr)
        self.ais.sock.recv(mox.IgnoreArg()).AndRaise(
            socket.error("Resource temporarily unavailable"))
        # part 4 - yield 3 lines (blocking False)
        self.ais.sock.setblocking(0)
        self.ais.sock.fileno().AndReturn(fdr)
        self.ais.sock.recv(mox.IgnoreArg()).AndReturn(b"a\r\n"*3)
        self.ais.sock.fileno().AndReturn(fdr)
        self.ais.sock.recv(mox.IgnoreArg()).AndRaise(
            socket.error("Resource temporarily unavailable"))
        # part 5 - yield 3 lines 2 times (blocking True)
        self.ais.sock.setblocking(0)
        self.ais.sock.fileno().AndReturn(fdr)
        self.ais.sock.recv(mox.IgnoreArg()).AndReturn(b"b\r\n"*3)
        self.ais.sock.fileno().AndReturn(fdr)
        self.ais.sock.recv(mox.IgnoreArg()).AndReturn(b"b\r\n"*3)
        self.ais.sock.fileno().AndReturn(fdr)
        self.ais.sock.recv(mox.IgnoreArg()).AndRaise(StopIteration)
        mox.Replay(self.ais.sock)

        next_method = '__next__' if sys.version_info[0] >= 3 else 'next'

        # part 1
        with self.assertRaises(aprslib.exceptions.ConnectionDrop):
            getattr(self.ais._socket_readlines(), next_method)()
        # part 2
        with self.assertRaises(aprslib.exceptions.ConnectionDrop):
            getattr(self.ais._socket_readlines(), next_method)()
        # part 3
        with self.assertRaises(StopIteration):
            getattr(self.ais._socket_readlines(), next_method)()
        # part 4
        for line in self.ais._socket_readlines():
            self.assertEqual(line, b'a')
        # part 5
        for line in self.ais._socket_readlines(blocking=True):
            self.assertEqual(line, b'b')

        mox.Verify(self.ais.sock)

    def test_send_login(self):
        self.ais.sock = mox.MockAnything()
        self.m.StubOutWithMock(self.ais, "close")
        self.m.StubOutWithMock(self.ais, "_sendall")
        # part 1 - raises
        self.ais._sendall(mox.IgnoreArg())
        self.ais.sock.settimeout(mox.IgnoreArg())
        self.ais.sock.recv(mox.IgnoreArg()).AndReturn(b"invalidreply")
        self.ais.close()
        # part 2 - raises (empty callsign)
        self.ais._sendall(mox.IgnoreArg())
        self.ais.sock.settimeout(mox.IgnoreArg())
        self.ais.sock.recv(mox.IgnoreArg()).AndReturn(b"# logresp  verified, xx")
        self.ais.close()
        # part 3 - raises (callsign doesn't match
        self.ais._sendall(mox.IgnoreArg())
        self.ais.sock.settimeout(mox.IgnoreArg())
        self.ais.sock.recv(mox.IgnoreArg()).AndReturn(b"# logresp NOMATCH verified, xx")
        self.ais.close()
        # part 4 - raises (unverified, but pass is not -1)
        self.ais._sendall(mox.IgnoreArg())
        self.ais.sock.settimeout(mox.IgnoreArg())
        self.ais.sock.recv(mox.IgnoreArg()).AndReturn(b"# logresp CALL unverified, xx")
        self.ais.close()
        # part 5 - normal, receive only
        self.ais._sendall(mox.IgnoreArg())
        self.ais.sock.settimeout(mox.IgnoreArg())
        self.ais.sock.recv(mox.IgnoreArg()).AndReturn(b"# logresp CALL unverified, xx")
        # part 6 - normal, correct pass
        self.ais._sendall(mox.IgnoreArg())
        self.ais.sock.settimeout(mox.IgnoreArg())
        self.ais.sock.recv(mox.IgnoreArg()).AndReturn(b"# logresp CALL verified, xx")
        mox.Replay(self.ais.sock)
        self.m.ReplayAll()

        # part 1
        self.ais.set_login("CALL", "-1")
        self.assertRaises(aprslib.exceptions.LoginError, self.ais._send_login)
        # part 2
        self.ais.set_login("CALL", "-1")
        self.assertRaises(aprslib.exceptions.LoginError, self.ais._send_login)
        # part 3
        self.ais.set_login("CALL", "-1")
        self.assertRaises(aprslib.exceptions.LoginError, self.ais._send_login)
        # part 4
        self.ais.set_login("CALL", "99999")
        self.assertRaises(aprslib.exceptions.LoginError, self.ais._send_login)
        # part 5
        self.ais.set_login("CALL", "-1")
        self.ais._send_login()
        # part 6
        self.ais.set_login("CALL", "99999")
        self.ais._send_login()

        mox.Verify(self.ais.sock)
        self.m.VerifyAll()

    def test_connect(self):
        self.ais.sock = mox.MockAnything()
        self.m.StubOutWithMock(self.ais, "_open_socket")
        self.m.StubOutWithMock(self.ais, "close")
        # part 1 - socket creation errors
        self.ais._open_socket().AndRaise(socket.timeout("timed out"))
        self.ais.close()
        self.ais._open_socket().AndRaise(socket.error('any'))
        self.ais.close()
        # part 2 - invalid banner from server
        self.ais._open_socket()
        self.ais.sock.getpeername().AndReturn((1, 2))
        self.ais.sock.setblocking(mox.IgnoreArg())
        self.ais.sock.settimeout(mox.IgnoreArg())
        self.ais.sock.setsockopt(mox.IgnoreArg(), mox.IgnoreArg(), mox.IgnoreArg())
        self.ais.sock.recv(mox.IgnoreArg()).AndReturn(b"junk")
        self.ais.close()
        # part 3 - everything going well
        self.ais._open_socket()
        self.ais.sock.getpeername().AndReturn((1, 2))
        self.ais.sock.setblocking(mox.IgnoreArg())
        self.ais.sock.settimeout(mox.IgnoreArg())
        self.ais.sock.setsockopt(mox.IgnoreArg(), mox.IgnoreArg(), mox.IgnoreArg())
        self.ais.sock.recv(mox.IgnoreArg()).AndReturn(b"# server banner")
        mox.Replay(self.ais.sock)
        self.m.ReplayAll()

        # part 1
        self.assertRaises(aprslib.exceptions.ConnectionError, self.ais._connect)
        self.assertFalse(self.ais._connected)
        self.assertRaises(aprslib.exceptions.ConnectionError, self.ais._connect)
        self.assertFalse(self.ais._connected)
        # part 2
        self.assertRaises(aprslib.exceptions.ConnectionError, self.ais._connect)
        self.assertFalse(self.ais._connected)
        # part 3
        self.ais._connect()
        self.assertTrue(self.ais._connected)

        mox.Verify(self.ais.sock)
        self.m.VerifyAll()

    def test_filter(self):
        testFilter = 'x/CALLSIGN'

        self.ais._connected = True
        self.ais.sock = mox.MockAnything()
        self.ais.sock.sendall(b'#filter ' + testFilter.encode('ascii') + b'\r\n')
        mox.Replay(self.ais.sock)

        self.ais.set_filter(testFilter)
        self.assertEqual(self.ais.filter, testFilter)

        mox.Verify(self.ais.sock)

    def test_connect_from_notconnected(self):
        self.m.StubOutWithMock(self.ais, "_connect")
        self.m.StubOutWithMock(self.ais, "_send_login")
        self.ais._connect()
        self.ais._send_login()
        self.m.ReplayAll()

        self.ais.connect()

        self.m.VerifyAll()

    def test_connect_from_connected(self):
        self.m.StubOutWithMock(self.ais, "_connect")
        self.m.StubOutWithMock(self.ais, "_send_login")
        self.ais._connect()
        self.ais._send_login()
        self.m.ReplayAll()

        self.ais._connected = True
        self.ais.connect()

        self.assertRaises(mox.ExpectedMethodCallsError, self.m.VerifyAll)

    def test_connect_raising_exception(self):
        self.m.StubOutWithMock(self.ais, "_connect")
        self.ais._connect().AndRaise(Exception("anything"))
        self.m.ReplayAll()

        self.assertRaises(Exception, self.ais.connect)

        self.m.VerifyAll()

    def test_connect_raising_exceptions(self):
        self.m.StubOutWithMock(self.ais, "_connect")
        self.m.StubOutWithMock(self.ais, "_send_login")
        self.ais._connect().AndRaise(aprslib.exceptions.ConnectionError("first"))
        self.ais._connect()
        self.ais._send_login().AndRaise(aprslib.exceptions.LoginError("second"))
        self.ais._connect()
        self.ais._send_login()
        self.m.ReplayAll()

        self.ais.connect(blocking=True, retry=0)

        self.m.VerifyAll()

    def test_sendall_type_exception(self):
        for testType in [5, 0.5, dict, list]:
            with self.assertRaises(TypeError):
                self.ais.sendall(testType)

    def test_sendall_not_connected(self):
        self.ais._connected = False
        with self.assertRaises(aprslib.ConnectionError):
            self.ais.sendall("test")

    def test_sendall_socketerror(self):
        self.ais.sock = mox.MockAnything()
        self.m.StubOutWithMock(self.ais, "close")

        # setup
        self.ais.sock.setblocking(mox.IgnoreArg())
        self.ais.sock.settimeout(mox.IgnoreArg())
        self.ais.sock.sendall(mox.IgnoreArg()).AndRaise(socket.error)
        self.ais.close()

        mox.Replay(self.ais.sock)
        self.m.ReplayAll()

        # test
        self.ais._connected = True
        with self.assertRaises(aprslib.ConnectionError):
            self.ais.sendall("test")

        # verify
        mox.Verify(self.ais.sock)
        self.m.VerifyAll()

    def test_sendall_empty_input(self):
        self.ais._connected = True
        self.ais.sendall("")

    def test_sendall_passing_to_socket(self):
        self.ais.sock = mox.MockAnything()
        self.m.StubOutWithMock(self.ais, "close")
        self.m.StubOutWithMock(self.ais, "_sendall")

        # rest
        _unicode = str if sys.version_info[0] >= 3 else unicode

        self.ais._connected = True
        for line in [
                "test",
                "test\r\n",
                _unicode("test"),
                _unicode("test\r\n"),
                ]:
            # setup
            self.ais.sock = mox.MockAnything()
            self.ais.sock.setblocking(mox.IgnoreArg())
            self.ais.sock.settimeout(mox.IgnoreArg())
            self.ais._sendall(b"%c" + line.rstrip('\r\n').encode('ascii') + b'\r\n').AndReturn(None)
            mox.Replay(self.ais.sock)

            self.ais.sendall(line)

            mox.Verify(self.ais.sock)


class TC_IS_consumer(unittest.TestCase):
    def setUp(self):
        self.ais = aprslib.IS("LZ1DEV-99")
        self.ais._connected = True
        self.m = mox.Mox()
        self.m.StubOutWithMock(self.ais, "_socket_readlines")
        self.m.StubOutWithMock(self.ais, "_parse")
        self.m.StubOutWithMock(self.ais, "connect")
        self.m.StubOutWithMock(self.ais, "close")

    def tearDown(self):
        self.m.UnsetStubs()

    def test_consumer_notconnected(self):
        self.ais._connected = False

        with self.assertRaises(aprslib.exceptions.ConnectionError):
            self.ais.consumer(callback=lambda: None, blocking=False)

    def test_consumer_raw(self):
        self.ais._socket_readlines(False).AndReturn(["line1"])
        self.m.ReplayAll()

        def testcallback(line):
            self.assertEqual(line, "line1")

        self.ais.consumer(callback=testcallback, blocking=False, raw=True)

        self.m.VerifyAll()

    def test_consumer_blocking(self):
        self.ais._socket_readlines(True).AndReturn(["line1"])
        self.ais._socket_readlines(True).AndReturn(["line1"] * 5)
        self.ais._socket_readlines(True).AndRaise(StopIteration)
        self.m.ReplayAll()

        def testcallback(line):
            self.assertEqual(line, "line1")

        self.ais.consumer(callback=testcallback, blocking=True, raw=True)

        self.m.VerifyAll()

    def test_consumer_parsed(self):
        self.ais._socket_readlines(False).AndReturn(["line1"])
        self.ais._parse("line1").AndReturn([])
        self.m.ReplayAll()

        def testcallback(line):
            self.assertEqual(line, [])

        self.ais.consumer(callback=testcallback, blocking=False, raw=False)

        self.m.VerifyAll()

    def test_consumer_serverline(self):
        self.ais._socket_readlines(False).AndReturn(["# serverline"])
        self.m.ReplayAll()

        def testcallback(line):
            self.fail("callback shouldn't be called")

        self.ais.consumer(callback=testcallback, blocking=False, raw=False)

        self.m.VerifyAll()

    def test_consumer_exceptions(self):
        self.ais._socket_readlines(False).AndRaise(SystemExit)
        self.ais._socket_readlines(False).AndRaise(KeyboardInterrupt)
        self.ais._socket_readlines(False).AndRaise(Exception("random"))
        self.ais._socket_readlines(False).AndRaise(aprslib.exceptions.ParseError('x'))
        self.ais._socket_readlines(False).AndRaise(aprslib.exceptions.UnknownFormat('x'))
        self.ais._socket_readlines(False).AndRaise(aprslib.exceptions.LoginError('x'))
        self.ais._socket_readlines(False).AndRaise(aprslib.exceptions.GenericError('x'))
        self.ais._socket_readlines(False).AndRaise(StopIteration)
        self.m.ReplayAll()

        def testcallback(line):
            pass

        # should raise
        for e in [
                SystemExit,
                KeyboardInterrupt,
                Exception
                ]:
            with self.assertRaises(e):
                self.ais.consumer(callback=testcallback, blocking=False, raw=False)

        # non raising
        for e in [
                aprslib.exceptions.ParseError,
                aprslib.exceptions.UnknownFormat,
                aprslib.exceptions.LoginError,
                aprslib.exceptions.GenericError,
                StopIteration
                ]:
            self.ais.consumer(callback=testcallback, blocking=False, raw=False)

        self.m.VerifyAll()

    def test_consumer_close(self):
        # importal = False
        self.ais._socket_readlines(False).AndRaise(aprslib.exceptions.ConnectionDrop(''))
        self.ais.close()
        self.ais._socket_readlines(False).AndRaise(aprslib.exceptions.ConnectionError(''))
        self.ais.close()
        # importal = True
        self.ais._socket_readlines(False).AndRaise(aprslib.exceptions.ConnectionDrop(''))
        self.ais.close()
        self.ais.connect(blocking=False)
        self.ais._socket_readlines(False).AndRaise(aprslib.exceptions.ConnectionError(''))
        self.ais.close()
        self.ais.connect(blocking=False)
        self.ais._socket_readlines(False).AndRaise(StopIteration)
        self.m.ReplayAll()

        with self.assertRaises(aprslib.exceptions.ConnectionDrop):
            self.ais.consumer(callback=lambda: None, blocking=False, raw=False)
        with self.assertRaises(aprslib.exceptions.ConnectionError):
            self.ais.consumer(callback=lambda: None, blocking=False, raw=False)

        self.ais.consumer(callback=lambda: None, blocking=False, raw=False, immortal=True)

        self.m.VerifyAll()
