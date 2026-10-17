"""ISO9660 목록/추출 도구.  python iso.py list|extract <iso> [패턴] [출력폴더]"""
import struct, sys, os, fnmatch

def walk(f):
    f.seek(16*2048); pvd = f.read(2048)
    lba, = struct.unpack('<I', pvd[158:162]); sz, = struct.unpack('<I', pvd[166:170])
    out = []
    def rec(lba, sz, p, dirent_pos):
        f.seek(lba*2048); d = f.read(sz); i = 0
        while i < len(d):
            l = d[i]
            if l == 0:
                i = (i//2048+1)*2048; continue
            e = d[i:i+l]
            el, = struct.unpack('<I', e[2:6]); es, = struct.unpack('<I', e[10:14])
            n = e[33:33+e[32]]
            if n not in (b'\0', b'\1'):
                nm = p + '/' + n.decode().split(';')[0]
                isdir = bool(e[25] & 2)
                out.append(dict(name=nm, lba=el, size=es, dir=isdir, rec=lba*2048+i))
                if isdir: rec(el, es, nm, None)
            i += l
    rec(lba, sz, '', None)
    return out

if __name__ == '__main__':
    cmd, iso = sys.argv[1], sys.argv[2]
    pat = sys.argv[3] if len(sys.argv) > 3 else '*'
    f = open(iso, 'rb')
    for e in walk(f):
        if e['dir'] or not fnmatch.fnmatch(e['name'], pat): continue
        if cmd == 'list':
            print(e['lba'], e['size'], e['name'])
        else:
            dst = os.path.join(sys.argv[4], e['name'].lstrip('/'))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            f.seek(e['lba']*2048); open(dst, 'wb').write(f.read(e['size']))
