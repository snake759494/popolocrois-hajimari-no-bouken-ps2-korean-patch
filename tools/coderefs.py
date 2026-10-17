"""ELF 코드에서 lui+addiu/ori 로 만들어지는 주소 → 참조 위치 목록"""
import struct, collections
def s16(x): return x - 0x10000 if x & 0x8000 else x
def coderefs(e):
    d = e.d; refs = collections.defaultdict(list)
    for v, o, fs, ms in e.seg:
        n = fs // 4; W = struct.unpack_from('<%dI' % n, d, o)
        for k in range(n):
            w = W[k]
            if (w >> 26) != 0xf: continue
            rt = (w >> 16) & 31; hi = (w & 0xffff) << 16
            for j in range(1, 10):
                if k + j >= n: break
                w2 = W[k+j]; op = w2 >> 26
                if op in (9, 0xd) and (w2 >> 21) & 31 == rt:
                    a = hi + (s16(w2 & 0xffff) if op == 9 else (w2 & 0xffff))
                    refs[a & 0xffffffff].append((v + 4*k, v + 4*(k+j)))
                    if (w2 >> 16) & 31 == rt: break
                if (w2 >> 16) & 31 == rt and op not in (0x2b, 0x29, 0x28, 0x3f, 0x1f, 4, 5): break
    return refs
