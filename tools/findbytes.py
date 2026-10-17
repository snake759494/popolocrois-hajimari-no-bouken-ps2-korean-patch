"""ISO 전체에서 바이트열을 찾아 파일명으로 매핑.  python findbytes.py <iso> <sjis문자열>"""
import sys, mmap, bisect
sys.path.insert(0, __import__('os').path.dirname(__file__))
from iso import walk
iso, s = sys.argv[1], sys.argv[2]
pat = s.encode('cp932')
f = open(iso, 'rb'); ents = sorted([e for e in walk(f) if not e['dir']], key=lambda e: e['lba'])
starts = [e['lba']*2048 for e in ents]
m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
cnt = {}
i = m.find(pat)
while i != -1:
    k = bisect.bisect_right(starts, i) - 1
    e = ents[k]; nm = e['name'] if i < starts[k] + e['size'] else '?'
    cnt[nm] = cnt.get(nm, 0) + 1
    i = m.find(pat, i+1)
for k, v in sorted(cnt.items()): print(v, k)
