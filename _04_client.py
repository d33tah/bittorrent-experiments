#!/usr/bin/env python

from _02_dht import dht_query
from _03_conn import BaseBittorrentHandler
from select import select
from socket import socket, AF_INET, SOCK_DGRAM, gethostbyname, error as s_error
from logging import getLogger, DEBUG, debug, info, error as log_error


class BittorrentHandlerStub(BaseBittorrentHandler):
    def on_connect(self):
        BaseBittorrentHandler.on_connect(self)
        self.sock.send(b'\x00\x00\x00\x01\x02')  # "INTERESTED"


class BaseBittorrentClient:

    def __init__(self, info_hash, dht_ips):
        self.info_hash = info_hash
        self._dht_ips = dht_ips
        self._dht_sock = socket(AF_INET, SOCK_DGRAM)

    def _newHandler(self, sock):
        return BittorrentHandlerStub(sock, self.info_hash, b'\x00\x00\x00\x00\x00\x10\x00\x01')

    def _handle_peer(self, peer):
        sock = socket()
        sock.settimeout(1.0)
        client = self._newHandler(sock)
        debug("Connecting to %s:%d" % peer)
        sock.connect(peer)
        debug("Connected")
        try:
            client.on_connect()
            while True:
                got, _, _ = select([sock], [], [], 1.0)
                if not got:
                    continue
                if not client.handle_packet():
                    break
        except s_error as e:
            log_error(e)

    def main(self):

        while self._dht_ips:
            node = self._dht_ips.pop()
            ip, port = node[0], node[1]
            peers, nodes = dht_query(self._dht_sock, ip, port, self.info_hash)
            self._dht_ips += nodes
            debug(self._dht_ips)
            for peer in peers:
                try:
                    self._handle_peer(peer)
                except s_error as e:
                    log_error(e)
                except KeyboardInterrupt as e:
                    info(e)
                except Exception as e:
                    log_error(e)
                    raise

if __name__ == '__main__':

    getLogger().setLevel(DEBUG)

    import base64
    import sys
    import urlparse
    if True:
        # https://thepiratebay.org/torrent/11274073/Ubuntu_14.10_desktop__x64
        info_hash = b'\xb4\x15\xc9\x13d>_\xf4\x9f\xe3}0K\xbb^n\x11\xadQ\x01'
        parsed = urlparse.urlparse(sys.argv[1])
        if not parsed.query:
            info_hash = base64.b16decode(sys.argv[1].upper())
        else:
            info_hash = base64.b16decode(urlparse.parse_qs(parsed.query)['xt'][0].split(':')[2].upper())

        dht_ips = [(gethostbyname('router.bittorrent.com'), 6881)]
        BaseBittorrentClient(info_hash, dht_ips).main()
    if False:
        ip, port = sys.argv[1].split(':')
        port = int(port)
        BaseBittorrentClient(base64.b16decode('2f0b4ea9169689dbe2ff49407500c01575cd63a2'.upper()), [])._handle_peer((ip, port))
