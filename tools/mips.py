"""ELF 로드·디스어셈블 도우미"""
import struct, capstone, sys
class Elf:
    def __init__(s, path):
        s.d = open(path, 'rb').read()
        phoff, = struct.unpack_from('<I', s.d, 0x1c); n, = struct.unpack_from('<H', s.d, 0x2c)
        s.seg = []
        for i in range(n):
            t, off, va, pa, fs, ms = struct.unpack_from('<6I', s.d, phoff + i*32)
            if t == 1: s.seg.append((va, off, fs, ms))
        s.entry, = struct.unpack_from('<I', s.d, 0x18)
    def off(s, va):
        for v, o, fs, ms in s.seg:
            if v <= va < v + fs: return o + va - v
    def va(s, off):
        for v, o, fs, ms in s.seg:
            if o <= off < o + fs: return v + off - o
    def u32(s, va): return struct.unpack_from('<I', s.d, s.off(va))[0]
    def dis(s, va, n=40):
        md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32 + capstone.CS_MODE_LITTLE_ENDIAN)
        o = s.off(va); out = []
        for k in range(n):
            w = s.d[o+4*k:o+4*k+4]
            ins = list(md.disasm(w, va+4*k))
            out.append('%08x: %s' % (va+4*k, ('%s %s' % (ins[0].mnemonic, ins[0].op_str)) if ins else '.word 0x%08x' % struct.unpack('<I', w)[0]))
        return '\n'.join(out)
    def refs(s, target):
        """lui/addiu(ori/lw..) 조합으로 target 주소를 만드는 위치 찾기"""
        hi = (target + 0x8000) >> 16; lo = target & 0xffff
        res = []
        for v, o, fs, ms in s.seg:
            for k in range(0, fs - 4, 4):
                w, = struct.unpack_from('<I', s.d, o + k)
                if (w >> 26) == 0xf and (w & 0xffff) == hi:
                    rt = (w >> 16) & 31
                    for j in range(1, 12):
                        if k + 4*j >= fs: break
                        w2, = struct.unpack_from('<I', s.d, o + k + 4*j)
                        if (w2 >> 21) & 31 == rt and (w2 & 0xffff) == lo and (w2 >> 26) in (9, 0xd, 0x23, 0x21, 0x25, 0x24, 0x2b, 0x29, 0x28, 0x37, 0x3f):
                            res.append(v + k); break
        return res
if __name__ == '__main__':
    e = Elf(sys.argv[1]); print(e.dis(int(sys.argv[2], 16), int(sys.argv[3]) if len(sys.argv) > 3 else 40))
