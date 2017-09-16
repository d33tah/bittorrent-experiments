#!/usr/bin/env python

import hashlib
hashobj = hashlib.sha1()
is_info = False


def file_read(f, n):
    global is_info, hashobj
    # TODO: if global is_info is True, feed read data into hashlib.sha1()
    ret = f.read(n)
    if is_info:
        hashobj.update(ret)
    return ret


def read_number_until(f, c):
    ret = ""
    while True:
        v = file_read(f, 1).decode('ascii')
        if v.isdigit() or v == '-':
            ret += v
        else:
            if v != c:
                err = "ERROR: Expected '%s', got '%s'." % (c, v)
                raise ValueError(err)
            return ret


def get_val(f):
    global is_info
    t = file_read(f, 1).decode('ascii')
    if t == 'e':
        return None
    elif t == 'i':
        return int(read_number_until(f, 'e'))
    elif t.isdigit():
        t += read_number_until(f, ":")
        ret = file_read(f, int(t))
        return ret
    elif t == 'l':
        ret = []
        while True:
            v = get_val(f)
            if v is not None:
                ret += [v]
            else:
                return ret
    elif t == 'd':
        ret = {}
        while True:
            key = get_val(f)
            if key is None:
                return ret
            is_info = True if key == 'info' else is_info
            value = get_val(f)
            is_info = False if key == 'info' else is_info
            ret[key] = value
    else:
        raise ValueError("Unexpected type: %s" % repr(t))


if __name__ == '__main__':
    import pprint
    d = get_val(open('_00_sample.torrent', 'rb'))
    # Let's shorten it so that demo doesn't take whole screen...
    d['info']['pieces'] = d['info']['pieces'][:16] + '(and so on)'
    pprint.pprint(d)
    pprint.pprint(hashobj.hexdigest())
