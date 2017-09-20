#!/usr/bin/env python

from unittest import main as unittest_main, TestCase
from io import BytesIO


def _read_from_file(f, n, infohash_obj, _is_info):
    ret = f.read(n)
    if _is_info and infohash_obj:
        infohash_obj.update(ret)
    return ret


def _read_number_until(f, c, infohash_obj, _is_info):
    ret = b""
    while True:
        v = _read_from_file(f, 1, infohash_obj, _is_info)
        if v.isdigit() or v == b'-':
            ret += v
        else:
            if v != c:
                err = "ERROR: Expected '%s', got '%s'." % (c, v)
                raise ValueError(err)
            return ret


def _bdecode_dict(f, infohash_obj, _is_info):
    ret = {}
    while True:
        key = bdecode_next_val(f, infohash_obj, _is_info)
        if key is None:
            return ret
        is_info_local = True if key == b'info' else _is_info
        value = bdecode_next_val(f, infohash_obj, is_info_local)
        ret[key] = value
    return ret


def _bdecode_list(f, infohash_obj, _is_info):
    ret = []
    while True:
        v = bdecode_next_val(f, infohash_obj, _is_info)
        if v is not None:
            ret += [v]
        else:
            return ret


def bdecode_next_val(f, infohash_obj=None, _is_info=False):
    t = _read_from_file(f, 1, infohash_obj, _is_info)
    if t == b'e':
        return None
    elif t == b'd':
        return _bdecode_dict(f, infohash_obj, _is_info)
    elif t.isdigit():
        t += _read_number_until(f, b":", infohash_obj, _is_info)
        ret = _read_from_file(f, int(t), infohash_obj, _is_info)
        return ret
    elif t == b'l':
        return _bdecode_list(f, infohash_obj, _is_info)
    elif t == b'i':
        return int(_read_number_until(f, b'e', infohash_obj, _is_info))
    else:
        raise ValueError("Unexpected type: %s" % repr(t))


def bdecode_str(s, infohash_obj=None):
    b = BytesIO(s)
    return bdecode_next_val(b, infohash_obj)


class BencodeTest(TestCase):
    def test_get_torrent_file(self):
        import zlib
        import base64
        import hashlib
        from io import BytesIO

        # I have no idea what this torrent contains, I just entered "txt" on
        # ThePirateBay and looked for something small.
        sample_torrent_compressed = b"""
        eJydlDuS1DAQhhMOYjIIVjO2/BjrAMQES0QAstUzVo2sdkky88hJNqGKM3AJ0g25BFdBM2
        MbP4aqLSKX7a///rvVarFhXGtsdQk0ZZVzDVutnOHlHgzRh8aSg2VpnuarHgvpEPGgpHVK
        vTAQFE3m4EHqneKSlFiPuazntoZSgTWpKHUXiFEarsfkpifhiKK1RIA96fKKzpP/dYnGgH
        ZkZ8BKpYCg2d3V7F12z608zo3GrBVjsnBnRAIt24xdxtmduoVFU4PjquDOgTnNpKO8kw7X
        xHBT7EgNU1XaE7L5EvceScWN11IzB76jU6NSycJcCl+0aV7SGbW4gpv7je+6+dDzph0w0l
        SNrz7u0ULutoguzOOIWNj7SHnPQryYpwKsT3BLZIkGtwgZcgy5e7wWd6dhXqbDPWhicFpm
        lHQYNv6vgBq1vE6rx7xINBMpsWnA2NZsL4r7KxSvF+NUQSMNd1Dw03z2wk4x7w79kirKpj
        Of/stTSGk2Bhf2ytLzs4NM5pNhHfo7Id3iwKdc0xZKloXrujE9jCl6MVpI19+7RcCLPdB5
        Kwfw/5wuN9eYHZdEO81uIQ237f5egoz5j7UvNg3Z463sQOBBK+QCRLA1WAddO4KSlxUE3A
        WdFTkMup+NcM1KA35WRFCc/OptO7VVmCVr/379KVEHwjMyDPMkz9LMz92GgS5R+P2asA+P
        7x42MZN6iyJlCvTOVTKhCcRM8xp8+98jqsCCV3M2eNOgL84FhV+Okhth3xJ3dGHEGgklBF
        18miQ0hfT20UZr9vHp28/Xv88/8NUn9vn7s3j+9fQV4A/z+0UM"""

        sample_torrent_bin = base64.b64decode(sample_torrent_compressed)
        sample_torrent = zlib.decompress(sample_torrent_bin)

        infohash_obj = hashlib.sha1()
        d = bdecode_next_val(BytesIO(sample_torrent), infohash_obj)

        self.assertEqual(d[b'info'][b'length'], 535)
        self.assertEqual(infohash_obj.hexdigest(),
                         "37d0c2c8ae3c1465f3d8761ac7029a58eda7fe42")


if __name__ == '__main__':
    unittest_main()
