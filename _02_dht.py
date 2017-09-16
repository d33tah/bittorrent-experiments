#!/usr/bin/env python

from _01_bdecode import bdecode_str
from struct import unpack
from socket import AF_INET, inet_ntop, error as socket_error
from unittest import TestCase, main as unittest_main


def dht_query(s, ip, port, info_hash):
    a_bencoded = b''.join([b'd', b'2:id', b'20:', info_hash, b'9:info_hash',
                          b'20:', info_hash, b'e'])
    all_bencoded = b''.join([b'd', b'1:a', a_bencoded, b'1:q', b'9:get_peers',
                             b'1:t', b'2:0f', b'1:y', b'1:q', b'e'])
    s.sendto(all_bencoded, (ip, port))
    s.settimeout(0.5)
    try:
        response_raw = s.recvfrom(1024)[0]
    except socket_error:  # timed out?
        return [], []
    return interpret_dht_response(response_raw)


def id_to_ipport(node_id):
    ip = inet_ntop(AF_INET, node_id[-6:][:4])
    port = unpack(">H", node_id[-2:])[0]
    return ip, port


def interpret_dht_response(response_raw):
    response = bdecode_str(response_raw)
    if b'r' not in response:
        return [], []
    found_peers, found_nodes = [], []
    for node_id in response[b'r'].get(b'values', []):
        found_peers += [id_to_ipport(node_id)]
    list_of_peers = response[b'r'].get(b'nodes', '')
    for offset in range(0, len(list_of_peers), 26):
        node_id = response[b'r'].get(b'nodes', '')[offset:offset+26]
        found_nodes += [id_to_ipport(node_id)]
    return found_peers, found_nodes


class SocketMock:

    def __init__(self, reply):
        self.reply = reply

    def sendto(self, *args, **kwargs):
        return None

    def settimeout(self, *args, **kwargs):
        return None

    def recvfrom(self, *args, **kwargs):
        return self.reply, None


class DHTTest(TestCase):

    def testNodes(self):
        ihash = b'\x97\xb5\x80\xa4\xcd\xf5i\x9dbh\x19$\x1exh\xba\x8f\x96Q\x82'
        r = (b'd2:ip6:M\xed\x0b2\xb5\xca1:rd2:id20:2\xf5NisQ\xffJ\xec)\xcd\xba'
             b'\xab\xf2\xfb\xe3F|\xc2g5:nodes26:\xfb~\x1c\xef\x8au]\xd6:\xf2!'
             b'\xed\xaf\x11\xd6\xcf4o\x89\x02mn\x94\xa0\xd8\xb2e1:t2:0f1:y1:r'
             b'e')
        found_peers, found_nodes = dht_query(SocketMock(r), None, None, ihash)
        self.assertEqual(found_peers, [])
        self.assertEqual(found_nodes, [('109.110.148.160', 55474)])

    def testPeers(self):
        ihash = b'\x97\xb5\x80\xa4\xcd\xf5i\x9dbh\x19$\x1exh\xba\x8f\x96Q\x82'
        r = (b'd2:ip6:M\xed\x0b2\xb5\xca1:rd2:id20:2\xf5NisQ\xffJ\xec)\xcd\xba'
             b'\xab\xf2\xfb\xe3F|\xc2g6:valuesl6:mn\x94\xa0\xd8\xb2ee1:t2:0f1:'
             b'y1:re')
        found_peers, found_nodes = dht_query(SocketMock(r), None, None, ihash)
        self.assertEqual(found_peers, [('109.110.148.160', 55474)])
        self.assertEqual(found_nodes, [])


if __name__ == '__main__':
    unittest_main()
