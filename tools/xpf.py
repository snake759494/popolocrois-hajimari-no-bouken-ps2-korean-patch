"""XPF 아카이브: 'XPFX', u32 헤더크기, u32 개수, u32 0, 항목 32B(이름24, u32 오프셋(데이터 기준), u32 크기)"""
import struct
def parse(d):
    assert d[:4] == b'XPFX', d[:4]
    hs, n = struct.unpack_from('<II', d, 4)
    ents = []
    for i in range(n):
        e = d[16+i*32:48+i*32]
        name = e[:24].split(b'\0')[0].decode('ascii'); off, sz = struct.unpack_from('<II', e, 24)
        ents.append([name, d[hs+off:hs+off+sz], e[:24]])
    return dict(hs=hs, head=d[:hs], ents=ents, tail=d[hs+sum(len(e[1]) for e in ents):])
def build(x):
    hs = x['hs']; head = bytearray(x['head']); off = 0; body = bytearray()
    for i, (name, data, raw) in enumerate(x['ents']):
        struct.pack_into('<II', head, 16+i*32+24, off, len(data)); body += data; off += len(data)
    return bytes(head) + bytes(body) + x['tail']
