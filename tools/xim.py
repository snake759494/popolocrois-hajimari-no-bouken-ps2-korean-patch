"""XIM 텍스처: 0x10 헤더([2]=0x40 4bpp / 0x30 8bpp), 팔레트 블록(u32 크기, ..., RGBA×n),
픽셀 블록(u32 크기, u32, u32 높이, u32 폭, 선형 데이터). 8bpp 팔레트는 PS2 CSM1 순서."""
import struct, numpy as np

def _perm():
    i = np.arange(256); return (i & 0xe7) | ((i & 8) << 1) | ((i & 16) >> 1)

def parse(d):
    bpp = 4 if d[2] == 0x40 else 8
    cs, = struct.unpack_from('<I', d, 0x10); n = 16 if bpp == 4 else 256
    co = 0x10 + cs - n * 4
    clut = np.frombuffer(d, np.uint8, n * 4, co).reshape(n, 4).copy()
    po = 0x10 + cs
    ps, z, h, w = struct.unpack_from('<4I', d, po)
    raw = np.frombuffer(d, np.uint8, ps - 16, po + 16)
    if bpp == 4:
        px = np.empty(raw.size * 2, np.uint8); px[0::2] = raw & 15; px[1::2] = raw >> 4
    else:
        px = raw.copy()
    H = px.size // w
    return dict(d=bytearray(d), bpp=bpp, co=co, clut=clut, po=po, w=w, h=H, idx=px[:w * H].reshape(H, w))

def palette(x):
    """표시 순서 팔레트 RGBA (인덱스 → 색)"""
    c = x['clut']
    return c[_perm()] if x['bpp'] == 8 else c

def rgba(x):
    return palette(x)[x['idx']]

def build(x):
    d = bytearray(x['d']); p = x['idx'].reshape(-1).astype(np.uint8)
    if x['bpp'] == 4: raw = (p[0::2] | (p[1::2] << 4)).tobytes()
    else: raw = p.tobytes()
    po = x['po']; ps, z, h, w = struct.unpack_from('<4I', d, po)
    if len(raw) != ps - 16:                      # 높이를 늘린 경우: 픽셀 블록 크기·높이 갱신
        tail = d[po + ps:]
        d = d[:po + 16] + bytearray(raw) + tail
        struct.pack_into('<4I', d, po, 16 + len(raw), z, x['idx'].shape[0], w)
    else:
        d[po + 16:po + 16 + len(raw)] = raw
    return bytes(d)

def quantize(x, img, mask):
    """img(H,W,4 RGBA) 의 mask 영역을 팔레트 최근접 색 인덱스로 x['idx'] 에 기록"""
    pal = palette(x).astype(np.int32)
    ys, xs = np.nonzero(mask)
    src = img[ys, xs].astype(np.int32)
    best = np.zeros(len(ys), np.int64); bd = np.full(len(ys), 1 << 60, np.int64)
    for i in range(len(pal)):
        dd = ((src - pal[i]) ** 2 * np.array([3, 4, 2, 2])).sum(1)
        m = dd < bd; bd[m] = dd[m]; best[m] = i
    z = src[:, 3] == 0                      # 완전 투명은 투명 팔레트 항목으로
    tr = np.nonzero(pal[:, 3] == 0)[0]
    if len(tr): best[z] = tr[0]
    x['idx'][ys, xs] = best
