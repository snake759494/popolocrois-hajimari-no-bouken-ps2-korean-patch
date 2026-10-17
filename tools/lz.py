"""XPF 항목 압축(ELF 0x130800 해제 루틴 기준).
BE u32 원본크기, 이후 플래그 바이트(MSB 우선, 필요할 때 그 자리에서 읽음).
0 = 리터럴 1바이트.  1,0,b = 짧은 거리 b-256 (b==0 이면 끝).  1,1,b,4비트 = 긴 거리 ((b-256)<<4|bits)-255.
길이: n=1; 다음 비트가 1인 동안 n = n*2 + 비트; 복사 길이 n+1."""
import struct
def decompress(src):
    size, = struct.unpack_from('>I', src, 0)
    out = bytearray(); pos = 5; flag = src[4]; mask = 0x80
    def bit():
        nonlocal flag, mask, pos
        if mask == 0: flag = src[pos]; pos += 1; mask = 0x80
        b = 1 if flag & mask else 0; mask >>= 1; return b
    while True:
        if bit() == 0:
            out.append(src[pos]); pos += 1; continue
        b2 = bit(); off = src[pos]; pos += 1
        if b2 == 0:
            if off == 0: break
            off -= 256
        else:
            o = off - 256
            for _ in range(4): o = o*2 + bit()
            off = o - 255
        n = 1
        while bit(): n = n*2 + bit()
        s = len(out) + off
        for k in range(n + 1): out.append(out[s + k])
    return bytes(out), size

class _W:
    def __init__(s): s.out = bytearray(); s.fpos = None; s.mask = 0
    def bit(s, b):
        if s.mask == 0:
            s.fpos = len(s.out); s.out.append(0); s.mask = 0x80
        if b: s.out[s.fpos] |= s.mask
        s.mask >>= 1
    def byte(s, v): s.out.append(v)

def _lenbits(n):
    """복사길이 L=n+1 의 n(>=1) 을 n=1; while 1: n=n*2+b 형식 비트로"""
    bits = bin(n)[3:]   # 맨 앞 1 제외
    out = []
    for c in bits: out += [1, int(c)]
    out.append(0); return out

def compress(data, level=1):
    """해시 체인 기반 탐욕적 LZ. 거리: 짧음 1..255(바이트 1..255), 긴 거리 256..4095+? """
    w = _W(); w.out += struct.pack('>I', len(data))
    n = len(data); i = 0
    MAXD_S = 255; MAXD_L = 4096 + 255 - 16   # 긴 거리: o=((b-256)<<4|bits)-255, b 1..255 → 여유 있게
    head = {}; prev = [-1] * n
    def ins(p):
        if p + 2 < n:
            k = data[p:p+3]; prev[p] = head.get(k, -1); head[k] = p
    MAXL = 0x10000
    while i < n:
        best_l = 0; best_d = 0
        if i + 2 < n:
            p = head.get(data[i:i+3], -1); cnt = 0
            while p >= 0 and i - p <= MAXD_L and cnt < 64:
                l = 0
                while i + l < n and l < MAXL and data[p + l] == data[i + l]: l += 1
                if l > best_l: best_l, best_d = l, i - p
                p = prev[p]; cnt += 1
        if i >= 1 and best_l < 2:
            # 거리 1~짧은 범위의 2바이트 일치도 허용
            for d in range(1, min(i, MAXD_S) + 1):
                if data[i-d:i-d+2] == data[i:i+2] and i + 1 < n:
                    l = 0
                    while i + l < n and data[i-d+l] == data[i+l]: l += 1
                    best_l, best_d = l, d; break
        if best_l >= 2:
            d = best_d; L = best_l
            if d <= MAXD_S:
                w.bit(1); w.bit(0); w.byte(256 - d)
            else:
                o = 255 - d                  # o = off + 255 (음수)
                # o = (b-256)*16 + bits, b in 1..255
                b = (o >> 4) + 256; bits = o & 15
                assert 1 <= b <= 255, (d, b)
                w.bit(1); w.bit(1); w.byte(b)
                for k in (3, 2, 1, 0): w.bit((bits >> k) & 1)
            for b_ in _lenbits(L - 1): w.bit(b_)
            for k in range(L): ins(i + k)
            i += L
        else:
            w.bit(0); w.byte(data[i]); ins(i); i += 1
    w.bit(1); w.bit(0); w.byte(0)
    return bytes(w.out)
