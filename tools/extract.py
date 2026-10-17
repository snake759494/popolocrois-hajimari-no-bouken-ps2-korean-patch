"""원본 ISO에서 번역 대상 텍스트를 뽑아 translation/*.json 생성(기존 ko 는 보존).
  pp3v.json : 고유 문자열 단위 {id, jp, ko, n(등장 수)}
  ejt.json  : 고유 자막 줄 단위 {id, jp, ko, n, ev}
  elf.json  : ELF 문자열 {id(va), jp, ko, max(바이트), refs}
"""
import sys, os, json, re, struct, collections, pickle
T = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(T)
sys.path.insert(0, T)
import iso, pp3v, xpf, lz
from mips import Elf
from coderefs import coderefs

ISO = os.path.join(R, 'PoPoLoCrois - Hajimari no Bouken (Japan).iso')
OUT = os.path.join(R, 'translation')

def read_all():
    f = open(ISO, 'rb'); ents = iso.walk(f); files = {}
    for e in ents:
        if e['dir']: continue
        n = e['name']
        if (n.startswith('/DATACMN/PP3V') or n.endswith('.EJT') or n == '/SCPS_150.28'
                or re.match(r'/DATAEVT/EV\d+/A\d+_M\.XPF$', n) or n.startswith('/DATAEVT/ENDING/')):
            f.seek(e['lba']*2048); files[n] = f.read(e['size'])
    return files

def ejt_lines(data):
    """(줄 인덱스, 텍스트 bytes) — 자막 레코드(\t17\t...) 3줄 뒤의 탭 줄"""
    L = data.split(b'\r\n'); out = []
    for i, l in enumerate(L):
        if i >= 3 and L[i-3].startswith(b'\t17\t') and l.startswith(b'\t'):
            out.append((i, l[1:]))
    return out

def merge(path, items, key='jp'):
    old = {}
    if os.path.exists(path):
        for it in json.load(open(path, encoding='utf-8')): old[it[key]] = it
    for it in items:
        o = old.get(it[key])
        if o:
            for k in ('ko', 'note'):
                if k in o: it[k] = o[k]
    json.dump(items, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(path, len(items), sum(1 for i in items if i.get('ko')))

def main():
    os.makedirs(OUT, exist_ok=True)
    files = read_all()
    # PP3V
    cnt = collections.Counter(); order = []
    for n in sorted(files):
        if not n.startswith('/DATACMN/PP3V'): continue
        for s in pp3v.strings(pp3v.parse(files[n])):
            t = s.decode('cp932')
            if t not in cnt: order.append(t)
            cnt[t] += 1
    merge(os.path.join(OUT, 'pp3v.json'), [dict(id=i, jp=t, ko='', n=cnt[t]) for i, t in enumerate(order)])
    # EJT
    cnt = collections.Counter(); order = []; ev = {}
    for n in sorted(files):
        if not n.endswith('.EJT'): continue
        for i, t in ejt_lines(files[n]):
            t = t.decode('cp932')
            if t not in cnt: order.append(t); ev[t] = n.split('/')[2]
            cnt[t] += 1
    # XPF 안의 a.ejt 도 같은 줄인지 확인
    for n in sorted(files):
        if n.endswith('_M.XPF'):
            for nm, d, _ in xpf.parse(files[n])['ents']:
                if nm == 'a.ejt':
                    u, _ = lz.decompress(d)
                    for i, t in ejt_lines(u):
                        t = t.decode('cp932')
                        if t not in cnt: order.append(t); ev[t] = n.split('/')[2]; cnt[t] += 1
    merge(os.path.join(OUT, 'ejt.json'), [dict(id=i, jp=t, ko='', n=cnt[t], ev=ev[t]) for i, t in enumerate(order)])
    # ELF
    e = Elf_from(files['/SCPS_150.28']); d = e.d
    refs = coderefs(e)
    W = collections.Counter(struct.unpack_from('<%dI' % (len(d)//4), d))
    pat = re.compile(rb'(?<=\x00)((?:[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]|[\x20-\x7e]|\x0a)+)\x00')
    items = []
    for m in pat.finditer(d):
        s = m.group(1); va = e.va(m.start(1))
        if va is None or va < 0x370000: continue
        if not re.search(rb'[\x81-\x9f\xe0-\xef]', s): continue
        try: t = s.decode('cp932')
        except UnicodeDecodeError: continue
        nref = W.get(va, 0) + len(refs.get(va, []))
        if not nref: continue
        if not re.fullmatch(r'[　-ヿ一-鿿！-ﾟ‐-♯ -ÿ -~\n]+', t): continue
        # 앞뒤 쓰레기 판정: 일본어 문자 2자 이상
        if sum(1 for c in t if '぀' <= c <= '鿿' or '０' <= c <= 'ｚ' or c in 'ー・') < 2 and len(t) < 3: continue
        o = m.start(1); end = m.end(1)
        while end < len(d) and d[end] == 0: end += 1
        items.append(dict(id='%06x' % va, jp=t, ko='', max=end - o - 1, refs=nref))
    merge(os.path.join(OUT, 'elf.json'), items, key='id')

def Elf_from(data):
    e = Elf.__new__(Elf); e.d = data
    phoff, = struct.unpack_from('<I', data, 0x1c); n, = struct.unpack_from('<H', data, 0x2c); e.seg = []
    for i in range(n):
        t, off, va, pa, fs, ms = struct.unpack_from('<6I', data, phoff + i*32)
        if t == 1: e.seg.append((va, off, fs, ms))
    return e

if __name__ == '__main__':
    main()
