"""ISO 내 모든 XPF의 항목 이름 확장자 통계"""
import sys, os, collections, struct
sys.path.insert(0, os.path.dirname(__file__))
from iso import walk
f = open(sys.argv[1], 'rb'); c = collections.Counter(); ex = collections.defaultdict(list)
for e in walk(f):
    if e['dir'] or not e['name'].endswith('.XPF'): continue
    f.seek(e['lba']*2048); h = f.read(16)
    if h[:4] != b'XPFX': c['!bad'] += 1; continue
    hs, n = struct.unpack_from('<II', h, 4); f.seek(e['lba']*2048 + 16); t = f.read(n*32)
    for i in range(n):
        nm = t[i*32:i*32+24].split(b'\0')[0].decode('ascii', 'replace'); x = nm.rsplit('.', 1)[-1].lower()
        c[x] += 1
        if len(ex[x]) < 3: ex[x].append(e['name'] + ':' + nm)
for k, v in c.most_common(): print(v, k, ex[k])
