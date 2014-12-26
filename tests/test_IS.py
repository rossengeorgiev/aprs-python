import unittest
import mox
import aprslib
import logging
import socket
import sys
import os


class TestCase_IS(unittest.TestCase):
    def setUp(self):
        self.ais = aprslib.IS("LZ1DEV-99", "testpwd", "127.0.0.1", "11111")
        self.m = mox.Mox()

    def tearDown(self):
        self.m.UnsetStubs()

    def test_initilization(self):
        self.assertFalse(self.ais._connected)
        self.assertEqual(self.ais.buf, '')
        self.assertIsNone(self.ais.sock)
        self.assertEqual(self.ais.callsign, "LZ1DEV-99")
        self.assertEqual(self.ais.passwd, "testpwd")
        self.assertEqual(self.ais.server, ("127.0.0.1", "11111"))

    def test_close(self):
        self.ais._connected = True
        s = mox.MockAnything()
        s.close()
        self.ais.sock = s
        mox.Replay(s)

        self.ais.close()

        mox.Verify(s)
        self.assertFalse(self.ais._connected)
        self.assertEqual(self.ais.buf, '')

    def test_open_socket(self):
        with self.assertRaises(socket.error):
            self.ais._open_socket()

    def test_socket_readlines(self):
        fdr, fdw = os.pipe()
        f = os.fdopen(fdw,'w')
        f.write("something")
        f.close()

        self.m.ReplayAll()
        self.ais.sock = mox.MockAnything()
        # part 1 - conn drop before setblocking
        self.ais.sock.setblocking(0).AndRaise(socket.error)
        # part 2 - conn drop trying to recv
        self.ais.sock.setblocking(0)
        self.ais.sock.fileno().AndReturn(fdr)
        self.ais.sock.recv(mox.IgnoreArg()).AndReturn('')
        # part 3 - nothing to read
        self.ais.sock.setblocking(0)
        self.ais.sock.fileno().AndReturn(fdr)
        self.ais.sock.recv(mox.IgnoreArg()).AndRaise(socket.error(""
                "Resource temporarily unavailable"))
        # part 4 - yield 3 lines (blocking False)
        self.ais.sock.setblocking(0)
        self.ais.sock.fileno().AndReturn(fdr)
        self.ais.sock.recv(mox.IgnoreArg()).AndReturn("a\r\n"*3)
        self.ais.sock.fileno().AndReturn(fdr)
        self.ais.sock.recv(mox.IgnoreArg()).AndRaise(socket.error(""
                "Resource temporarily unavailable"))
        # part 5 - yield 3 lines 2 times (blocking True)
        self.ais.sock.setblocking(0)
        self.ais.sock.fileno().AndReturn(fdr)
        self.ais.sock.recv(mox.IgnoreArg()).AndReturn("b\r\n"*3)
        self.ais.sock.fileno().AndReturn(fdr)
        self.ais.sock.recv(mox.IgnoreArg()).AndReturn("b\r\n"*3)
        self.ais.sock.fileno().AndReturn(fdr)
        self.ais.sock.recv(mox.IgnoreArg()).AndRaise(StopIteration)
        mox.Replay(self.ais.sock)

        # part 1
        with self.assertRaises(aprslib.exceptions.ConnectionDrop):
            self.ais._socket_readlines().next()
        # part 2
        with self.assertRaises(aprslib.exceptions.ConnectionDrop):
            self.ais._socket_readlines().next()
        # part 3
        with self.assertRaises(StopIteration):
            self.ais._socket_readlines().next()
        # part 4
        for line in self.ais._socket_readlines():
            self.assertEqual(line, 'a')
        # part 5
        for line in self.ais._socket_readlines(blocking=True):
            self.assertEqual(line, 'b')

        mox.Verify(self.ais.sock)

    def test_send_login(self):
        self.ais.sock = mox.MockAnything()
        self.m.StubOutWithMock(self.ais, "close")
        # part 1 - raises
        self.ais.sock.sendall(mox.IgnoreArg())
        self.ais.sock.settimeout(mox.IgnoreArg())
        self.ais.sock.recv(mox.IgnoreArg()).AndReturn("invalidreply")
        self.ais.close()
        # part 2 - raises (empty callsign)
        self.ais.sock.sendall(mox.IgnoreArg())
        self.ais.sock.settimeout(mox.IgnoreArg())
        self.ais.sock.recv(mox.IgnoreArg()).AndReturn("# logresp  verified, xx")
        self.ais.close()
        # part 3 - raises (callsign doesn't match
        self.ais.sock.sendall(mox.IgnoreArg())
        self.ais.sock.settimeout(mox.IgnoreArg())
        self.ais.sock.recv(mox.IgnoreArg()).AndReturn("# logresp NOMATCH verified, xx")
        self.ais.close()
        # part 4 - raises (unverified, but pass is not -1)
        self.ais.sock.sendall(mox.IgnoreArg())
        self.ais.sock.settimeout(mox.IgnoreArg())
        self.ais.sock.recv(mox.IgnoreArg()).AndReturn("# logresp CALL unverified, xx")
        self.ais.close()
        # part 5 - normal, receive only
        self.ais.sock.sendall(mox.IgnoreArg())
        self.ais.sock.settimeout(mox.IgnoreArg())
        self.ais.sock.recv(mox.IgnoreArg()).AndReturn("# logresp CALL unverified, xx")
        # part 6 - normal, correct pass
        self.ais.sock.sendall(mox.IgnoreArg())
        self.ais.sock.settimeout(mox.IgnoreArg())
        self.ais.sock.recv(mox.IgnoreArg()).AndReturn("# logresp CALL verified, xx")
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
        if sys.platform not in ['cygwin', 'win32']:
            self.ais.sock.setsockopt(mox.IgnoreArg(), mox.IgnoreArg(), mox.IgnoreArg())
            self.ais.sock.setsockopt(mox.IgnoreArg(), mox.IgnoreArg(), mox.IgnoreArg())
            self.ais.sock.setsockopt(mox.IgnoreArg(), mox.IgnoreArg(), mox.IgnoreArg())
        self.ais.sock.recv(mox.IgnoreArg()).AndReturn("junk")
        self.ais.close()
        # part 3 - everything going well
        self.ais._open_socket()
        self.ais.sock.getpeername().AndReturn((1, 2))
        self.ais.sock.setblocking(mox.IgnoreArg())
        self.ais.sock.settimeout(mox.IgnoreArg())
        self.ais.sock.setsockopt(mox.IgnoreArg(), mox.IgnoreArg(), mox.IgnoreArg())
        if sys.platform not in ['cygwin', 'win32']:
            self.ais.sock.setsockopt(mox.IgnoreArg(), mox.IgnoreArg(), mox.IgnoreArg())
            self.ais.sock.setsockopt(mox.IgnoreArg(), mox.IgnoreArg(), mox.IgnoreArg())
            self.ais.sock.setsockopt(mox.IgnoreArg(), mox.IgnoreArg(), mox.IgnoreArg())
        self.ais.sock.recv(mox.IgnoreArg()).AndReturn("# server banner")
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
        testFilter = "x/CALLSIGN"

        self.ais._connected = True
        s = mox.MockAnything()
        s.sendall("#filter %s\r\n" % testFilter)
        self.ais.sock = s
        mox.Replay(s)

        self.ais.set_filter(testFilter)
        self.assertEqual(self.ais.filter, testFilter)

        mox.Verify(s)

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
        self.ais._connect().AndRaise(Exception("first"))
        self.ais._connect()
        self.ais._send_login().AndRaise(Exception("second"))
        self.ais._connect()
        self.ais._send_login()
        self.m.ReplayAll()

        self.ais.connect(blocking=True, retry=0)

        self.m.VerifyAll()


class TestCase_IS_consumer(unittest.TestCase):
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

    def test_consumer_exptions(self):
        self.ais._socket_readlines(False).AndRaise(SystemExit)
        self.ais._socket_readlines(False).AndRaise(KeyboardInterrupt)
        self.ais._socket_readlines(False).AndRaise(Exception("random"))
        self.ais._socket_readlines(False).AndRaise(StopIteration)
        self.ais._socket_readlines(False).AndRaise(aprslib.exceptions.GenericError('x'))
        self.m.ReplayAll()

        def testcallback(line):
            pass

        for e in [SystemExit, KeyboardInterrupt, Exception]:
            with self.assertRaises(e):
                self.ais.consumer(callback=testcallback, blocking=False, raw=False)

        # StopIteration
        self.ais.consumer(callback=testcallback, blocking=False, raw=False)
        # GenericError
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
