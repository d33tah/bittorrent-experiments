#!/usr/bin/env python

from struct import unpack
from unittest import TestCase, main as unittest_main
from os import urandom
from io import BytesIO
from socket import error as socket_error
from logging import debug
from _01_bdecode import bdecode_str
import base64


class BaseBittorrentHandler():
    def __init__(self, sock, info_hash, reserved_extension_bytes=8 * b'\x00'):
        self.sock = sock
        self.info_hash = info_hash
        self.ext_b = reserved_extension_bytes

    def on_connect(self):
        handshake_msg = b''.join([b'\x13', b"BitTorrent protocol", self.ext_b,
                                  self.info_hash, urandom(20)])
        self.sock.send(handshake_msg)
        x = self._do_recv(1)
        if x != b'\x13':
            raise RuntimeError('Incorrect handshake: %s' % repr(x))
        # TODO: I might have left a bug here - do I still need minus one?
        expected_len = len(handshake_msg) - 1
        self._do_recv(expected_len)
        debug('Handshake complete.')

    def _do_recv(self, n):
        ret = b''
        while len(ret) < n:
            buf = self.sock.recv(n - len(ret))
            if buf == b'':
                raise socket_error('Connection closed by remote end.')
            ret += buf
        return ret

    def handle_packet(self):
        x = self._do_recv(4)
        if len(x) < 4:
            return False
        nbytes = unpack('>I', x)[0]
        if nbytes == 0:
            return True  # TODO: read up on keepalive?
        t = self._do_recv(1)
        if nbytes > 0:
            d = self._do_recv(nbytes - 1)
        else:
            d = b''
        {b'\x00': self.on_keepalive,
         b'\x01': self.on_unchoke,
         b'\x04': self.on_have,
         b'\x05': self.on_bitfield,
         b'\x07': self.on_piece,
         b'\x09': self.on_port,
         b'\x14': self.on_extended}.get(t, self.on_other)(d, t)
        return True

    def on_keepalive(self, d, t=None):
        debug('on_keepalive(d=%s)' % repr(d))

    def on_piece(self, d, t=None):
        debug('on_piece(d=%s)' % repr(d[:8]))

    def on_unchoke(self, d, t=None):
        debug('on_unchoke(d=%s)' % repr(d))

    def on_have(self, d, t=None):
        debug('on_have(d=%s)' % repr(d))

    def on_bitfield(self, d, t=None):
        debug('on_bitfield(d=%s)' % repr(d))

    def on_port(self, d, t=None):
        debug('on_port(d=%s)' % repr(d))

    def on_extended(self, d, t=None):
        if d[0] == b'\x00':
            debug('Sending extended handshake')
            self.sock.send(base64.b16decode('00000052140064313a6d6431313a75745f6d65746164617461693265363a75745f70657869316565313a7069343931363465343a72657171693230343865313a7631373a6c6962546f7272656e7420302e31332e3665'.upper()))
            self.sock.send(base64.b16decode('0000001b140264383a6d73675f74797065693065353a706965636569306565'.upper()))
        debug('on_extended(t=%r, d=%r, d2=%r)' % (d[0], d, bdecode_str(d[1:])))
        #raise NotImplementedError()

    def on_other(self, d, t):
        debug('on_other(d=%r, t=%r)' % (d, t))
        raise NotImplementedError()


class SocketMockIterated:

    def __init__(self, reply_list):
        self.h = BytesIO(reply_list)

    def send(self, *args, **kwargs):
        return None

    def recv(self, n):
        return self.h.read(n)


class BaseBittorrentHandlerTest(TestCase):

    def test_sample_conversation(self):
        import base64
        info_hash = base64.b64decode('tBXJE2Q+X/Sf430wS7tebhGtUQE=')
        handshake = b''.join([b'\x13', b"BitTorrent protocol",
                              8 * b'\x00', info_hash, urandom(20)])
        sock = SocketMockIterated(handshake)
        client = BaseBittorrentHandler(sock, info_hash)
        client.on_connect()


if __name__ == '__main__':
    unittest_main()
