"""포포로크로이스 FNT 폰트 파서/빌더.
구조: 'G'|'K', 셀폭, 셀높이, 0, 개수(BE16), 0, 0 [+K는 0x20 이름]
레코드 20B: [0]폭 [1..5]메트릭 [6:8]SJIS코드(LE) [8]u0 [9]v0 [14:16]v페이지 [16]u페이지 [18]u1 [19]v1 (G는 [12]=u1,[17]=v1 중복)
코드표 u16×n (+n 홀수면 2바이트 패딩), 비트맵: u16 높이, u16 폭, 선형 PSMT4(하위 니블=왼쪽)"""
import struct, numpy as np
def parse(d):
    kind = chr(d[0]); n = d[4] << 8 | d[5]
    rb = 0x28 if kind == 'K' else 8
    recs = [bytearray(d[rb+i*20:rb+i*20+20]) for i in range(n)]
    ct = rb + n*20
    codes = list(struct.unpack_from('<%dH' % n, d, ct))
    bm = ct + n*2 + (2 if n & 1 else 0)
    h, w = struct.unpack_from('<HH', d, bm)
    raw = d[bm+4:bm+4+w*h//2]; short = w*h//2 - len(raw)
    a = np.frombuffer(raw + bytes(short), np.uint8)
    px = np.empty(w*h, np.uint8); px[0::2] = a & 15; px[1::2] = a >> 4
    return dict(kind=kind, head=bytes(d[:rb]), recs=recs, codes=codes, w=w, h=h, pix=px.reshape(h, w), tail=d[bm+4+w*h//2:], short=short)
def rect(r, kind='G'):
    if kind == 'K':
        x0 = r[8] | r[12] << 8; y0 = r[9] | r[13] << 8; x1 = r[18] | r[16] << 8; y1 = r[19] | r[17] << 8
        return x0, y0, x1, y1
    vp = struct.unpack_from('<H', r, 14)[0] * 256
    x0 = r[16]*256 + r[8]; y0 = vp + r[9]
    x1 = r[16]*256 + r[18] + (256 if r[18] < r[8] else 0); y1 = vp + r[19] + (256 if r[19] < r[9] else 0)
    return x0, y0, x1, y1
def set_rect(r, kind, x0, y0, x1, y1):
    if kind == 'K':
        r[8] = x0 & 255; r[9] = y0 & 255; r[12] = x0 >> 8; r[13] = y0 >> 8
        r[16] = x1 >> 8; r[17] = y1 >> 8; r[18] = x1 & 255; r[19] = y1 & 255
    else:
        r[8] = x0 & 255; r[9] = y0 & 255; r[12] = x1 & 255; r[13] = y0 & 255
        struct.pack_into('<H', r, 14, y0 >> 8); r[16] = x0 >> 8; r[17] = y1 & 255; r[18] = x1 & 255; r[19] = y1 & 255
def build(f):
    n = len(f['recs']); head = bytearray(f['head']); head[4] = n >> 8; head[5] = n & 255
    out = bytearray(head)
    for r in f['recs']: out += r
    out += struct.pack('<%dH' % n, *f['codes'])
    if n & 1: out += b'\0\0'
    h, w = f['pix'].shape
    out += struct.pack('<HH', h, w)
    p = f['pix'].reshape(-1).astype(np.uint8)
    out += (p[0::2] | (p[1::2] << 4)).tobytes()
    out = bytes(out + f['tail'])
    return out[:len(out)-f.get('short', 0)] if not f.get('keep') else out
