"""ISO 각 파일에서 SJIS 문자열(히라가나/가타카나 포함 3자 이상) 개수 집계"""
import sys, re, os
sys.path.insert(0, os.path.dirname(__file__))
from iso import walk
pat = re.compile(rb'(?:[\x81-\x9f\xe0-\xea][\x40-\x7e\x80-\xfc]){3,}')
kana = re.compile(rb'\x82[\x9f-\xf1]|\x83[\x40-\x96]')
f = open(sys.argv[1], 'rb'); res = []
for e in walk(f):
    if e['dir'] or e['name'].endswith(('.PSS', '.XV', '.XWB')): continue
    f.seek(e['lba']*2048); d = f.read(e['size'])
    c = sum(1 for m in pat.finditer(d) if len(kana.findall(m.group())) >= 2)
    if c: res.append((c, e['name'], e['size']))
for c, n, s in sorted(res, key=lambda x: x[1]): print(c, s, n)
