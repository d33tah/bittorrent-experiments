#!/usr/bin/env python

import socket

s = socket.socket()
s.connect(('releases.ubuntu.com', 80))
s.send('GET /17.04/ubuntu-17.04-desktop-amd64.iso HTTP/1.1\r\n'
       'Host: releases.ubuntu.com\r\n\r\n')
print(repr(s.recv(4096)))
