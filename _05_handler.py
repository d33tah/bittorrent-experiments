#!/usr/bin/env python

from sys import exit
from struct import pack, unpack
from logging import getLogger, DEBUG, debug
from _03_conn import BaseBittorrentHandler
from _04_client import BaseBittorrentClient
from socket import gethostbyname, error as socket_error
from threading import Lock


class BittorrentHandler(BaseBittorrentHandler):
    def __init__(self, sock, info_hash, piece_length, total_length, num_pieces,
                 f, f_lock):
        self.total_length = total_length
        self.num_pieces = num_pieces
        self.piece_length = piece_length
        self.f = f
        self.f_lock = f_lock
        self.sent_interested = False
        self.have = []
        BaseBittorrentHandler.__init__(self, sock, info_hash)

    def on_piece(self, d):
        piece_idx, piece_offset = unpack('>II', d[:8])
        debug('found a piece! idx=%d, offset=%d, len=%d' %
              (piece_idx, piece_offset, len(d) - 8))
        with self.f_lock:
            self.f.seek(piece_idx * self.piece_length)
            self.f.write(d[8:])  # first 8 bytes = piece & offset within piece
            self.f.flush()

    def _handle_interested(self):
        if not self.sent_interested:
            self.sock.send(b'\x00\x00\x00\x01\x02')  # "INTERESTED"
            self.sent_interested = True

    def _send_want(self, piece, offset):
        if piece < self.num_pieces:
            length = self.piece_length
        else:
            length = self.total_length - (num_pieces * self.piece_length)
        length = min(0x4000, length)

        debug('_send_want(piece=%d, o=%d, len=%d' % (piece, offset, length))
        buf = (b'\x00\x00\x00\x0D\x06' + pack('>III', piece, offset, length))
        self.sock.send(buf)

    def on_unchoke(self, d):
        self._handle_interested()
        for piece in self.have:
            self._send_want(piece, 0)

    def on_have(self, d):
        piece = unpack('>I', d)[0]
        debug('Got a HAVE: %d' % piece)
        self._handle_interested()
        self.have += [piece]
        self._send_want(piece, 0)

    def on_other(self, t, d):
        exit('Unsupported type: %s' % repr(t))


class BittorrentClient(BaseBittorrentClient):
    def __init__(self, info_hash, dht_ips, info_bdecoded, f, f_lock):
        BaseBittorrentClient.__init__(self, info_hash, dht_ips)
        self.info_bdecoded = info_bdecoded
        self.piece_length = info_bdecoded['piece length']
        self.num_pieces = len(info_bdecoded['pieces']) / 20
        self.total_length = info_bdecoded['length']
        self.f = f
        self.f_lock = f_lock

    def _newHandler(self, sock):
        return BittorrentHandler(sock, self.info_hash, self.piece_length,
                                 self.total_length, self.num_pieces, self.f,
                                 self.f_lock)

if __name__ == '__main__':

    from sys import argv
    from hashlib import sha1
    from _01_bdecode import bdecode_next_val
    getLogger().setLevel(DEBUG)
    infohash_obj = sha1()
    torrent_bdecoded = bdecode_next_val(open(argv[1]), infohash_obj)
    if 'info' in torrent_bdecoded:
        info_bdecoded = torrent_bdecoded['info']
    else:
        info_bdecoded = torrent_bdecoded

    f_lock = Lock()
    f = open(info_bdecoded['name'], 'ab')
    f.truncate(info_bdecoded['length'])

    dht_ips = [(gethostbyname('router.bittorrent.com'), 6881)]
    BittorrentClient(infohash_obj.digest(), dht_ips, info_bdecoded,
                     f, f_lock).main()
