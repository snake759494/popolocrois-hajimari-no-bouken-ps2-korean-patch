"""PS2 4bpp/8bpp 텍스처 스위즐(Rainbow 방식) 위치 계산"""
import numpy as np
def idx4(W, H):
    """선형 (y,x) → 원본 니블 인덱스 배열[H,W] (바이트*2 + 상위여부)"""
    y, x = np.mgrid[0:H, 0:W]
    pageX = x & ~0x7f; pageY = y & ~0x7f
    ph = (W + 127) // 128; pv = (H + 127) // 128
    pn = (pageY // 128) * ph + (pageX // 128)
    p32Y = (pn // pv) * 32; p32X = (pn % pv) * 64
    ploc = p32Y * H * 2 + p32X * 4
    locX = x & 0x7f; locY = y & 0x7f
    bloc = ((locX & ~0x1f) >> 1) * H + (locY & ~0xf) * 2
    sw = (((y + 2) >> 2) & 1) * 4
    posY = (((y & ~3) >> 1) + (y & 1)) & 7
    cloc = posY * H * 2 + ((x + sw) & 7) * 4
    bn = (x >> 3) & 3
    bits = (y >> 1) & 1
    pos = ploc + bloc + cloc + bn
    return pos * 2 + bits
def idx8(W, H):
    y, x = np.mgrid[0:H, 0:W]
    bloc = (y & ~0xf) * W + (x & ~0xf) * 2
    sw = (((y + 2) >> 2) & 1) * 4
    posY = (((y & ~3) >> 1) + (y & 1)) & 7
    cloc = posY * W * 2 + ((x + sw) & 7) * 4
    bn = ((y >> 1) & 1) + ((x >> 2) & 2)
    return bloc + cloc + bn
