"""한글판 ISO 빌드.
  python build.py            → 'PoPoLoCrois - Hajimari no Bouken (Korean).iso' (원본과 같은 폴더)
  python build.py --merge    → translation/work/*.json 의 번역을 translation/*.json 에 병합한 뒤 빌드
"""
import sys, os, json, glob, struct, re, time
T = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(T)
sys.path.insert(0, T)
import iso, pp3v, xpf, lz, fnt, mkfont, isopatch, extract, build_img

SRC = os.path.join(R, 'PoPoLoCrois - Hajimari no Bouken (Japan).iso')
DST = os.path.join(R, 'PoPoLoCrois - Hajimari no Bouken (Korean).iso')
TR = os.path.join(R, 'translation')
B = chr(92)

def merge_work():
    for kind in ('pp3v', 'ejt', 'elf'):
        main = json.load(open(os.path.join(TR, kind + '.json'), encoding='utf-8'))
        idx = {str(it['id']): it for it in main}
        for p in sorted(glob.glob(os.path.join(TR, 'work', kind + '_*.json'))):
            for it in json.load(open(p, encoding='utf-8')):
                m = idx.get(str(it['id']))
                if m and m['jp'] == it['jp']:
                    for k in ('ko', 'note'):
                        if it.get(k): m[k] = it[k]
        json.dump(main, open(os.path.join(TR, kind + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(kind, sum(1 for i in main if i.get('ko')), '/', len(main))

# ---- 인코딩 ----
FW_FIX = {'〜': '～', '−': '－', '―': '―', '·': '・', '“': '"', '”': '"', '‘': "'", '’': "'"}
def kanji_codes():
    for lead in list(range(0x88, 0xa0)) + list(range(0xe0, 0xeb)):
        for tr in list(range(0x40, 0x7f)) + list(range(0x80, 0xfd)):
            if lead == 0x88 and tr < 0x9f: continue
            if tr in (0x5c, 0x7e): continue
            yield lead << 8 | tr
SPACE = '␠'   # 필드 엔진은 반각 공백(0x20)을 특수 처리 → 전용 좁은 공백 글리프로
class Enc:
    def __init__(s, korean_chars):
        s.map = {}
        for ch, code in zip(sorted(korean_chars) + [SPACE], kanji_codes()):
            s.map[ch] = code
    def enc(s, text, sp=False):
        out = bytearray()
        for ch in text:
            if sp and ch == ' ': ch = SPACE                   # 필드 창은 1바이트 문자를 특수 처리 → 2바이트 빈 글리프
            if ch in s.map:
                c = s.map[ch]; out += bytes([c >> 8, c & 255])
            else:
                ch = FW_FIX.get(ch, ch)
                out += ch.encode('cp932')
        return bytes(out)

def fullwidth(t):
    # 필드 대사: 줄바꿈/페이지 코드를 제외한 반각 ASCII -> 전각 (필드 창은 1바이트 문자를 특수 처리)
    out = []; i = 0
    while i < len(t):
        c = t[i]
        if c == B and i + 1 < len(t) and t[i+1].isalpha(): out.append(t[i:i+2]); i += 2; continue   # 제어 코드
        m = re.match(r'%[-+ 0-9.]*[a-zA-Z]', t[i:])
        if m: out.append(m.group()); i += len(m.group()); continue                            # 서식 지정자
        if '!' <= c <= '~' and c != B: out.append(chr(ord(c) + 0xfee0))
        else: out.append(c)
        i += 1
    return ''.join(out)

def is_ko(ch): return 0xac00 <= ord(ch) <= 0xd7a3

def codes_of(b):
    out = set(); i = 0
    while i < len(b):
        c = b[i]
        if 0x81 <= c <= 0x9f or 0xe0 <= c <= 0xfc: out.add(c << 8 | b[i+1]); i += 2
        else: out.add(c); i += 1
    return out

def main():
    t0 = time.time()
    if '--merge' in sys.argv: merge_work()
    P = json.load(open(os.path.join(TR, 'pp3v.json'), encoding='utf-8'))
    E = json.load(open(os.path.join(TR, 'ejt.json'), encoding='utf-8'))
    L = json.load(open(os.path.join(TR, 'elf.json'), encoding='utf-8'))
    allko = set()
    for it in P + E + L:
        allko |= {c for c in it.get('ko', '') if is_ko(c)}
    enc = Enc(allko); print('한글 글자', len(allko))
    json.dump({ch: '%04X' % c for ch, c in enc.map.items()}, open(os.path.join(TR, 'charmap.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    tp = {it['jp']: it['ko'] for it in P if it.get('ko')}
    te = {it['jp']: it['ko'] for it in E if it.get('ko')}

    files = extract.read_all()
    f = open(SRC, 'rb'); ents = {e['name']: e for e in iso.walk(f)}
    def rd(n):
        e = ents[n]; f.seek(e['lba'] * 2048); return f.read(e['size'])
    out = {}
    grpA = set(); grpB = set()        # A: 필드/시스템, B: 이벤트
    # PP3V
    for n in sorted(files):
        if not n.startswith('/DATACMN/PP3V'): continue
        p = pp3v.parse(files[n]); new = []
        for s in pp3v.strings(p):
            jp = s.decode('cp932'); ko = tp.get(jp)
            b = enc.enc(fullwidth(ko), True) if ko else s
            new.append(b); grpA |= codes_of(b)
        out[n] = pp3v.build(p, new)
    # EJT
    def ejt_patch(data):
        Ls = data.split(b'\r\n'); used = set()
        for i, t in extract.ejt_lines(data):
            jp = t.decode('cp932'); ko = te.get(jp)
            b = enc.enc(ko) if ko else t
            Ls[i] = b'\t' + b; used |= codes_of(b)
        return b'\r\n'.join(Ls), used
    for n in sorted(files):
        if n.endswith('.EJT'):
            out[n], u = ejt_patch(files[n]); grpB |= u
        elif n.endswith('_M.XPF'):
            x = xpf.parse(files[n]); ch = False
            for ent in x['ents']:
                if ent[0] == 'a.ejt':
                    u, _ = lz.decompress(ent[1]); nu, used = ejt_patch(u); grpB |= used
                    if nu != u: ent[1] = lz.compress(nu); ch = True
            if ch: out[n] = xpf.build(x)
    # ELF
    elf = bytearray(files['/SCPS_150.28']); e = extract.Elf_from(bytes(elf)); nel = 0
    for it in L:
        if not it.get('ko'): continue
        ko = it['ko']
        for cand in (fullwidth(ko), fullwidth(ko).replace(' ', ''), ko, ko.replace(' ', '')):
            b = enc.enc(cand, True)
            if len(b) <= it['max']: break
        va = int(it['id'], 16); o = e.off(va)
        old = it['jp'].encode('cp932')
        assert elf[o:o+len(old)] == old, it['id']
        assert len(b) <= it['max'], (it['id'], len(b), it['max'])
        elf[o:o+it['max']+1] = b + bytes(it['max'] + 1 - len(b)); nel += 1
        grpA |= codes_of(b)
    out['/SCPS_150.28'] = bytes(elf); print('ELF 문자열', nel)
    # 폰트
    korev = {v: k for k, v in enc.map.items()}
    for name, grp in (('FONT_EX', grpA), ('F_SYSMES', grpA), ('F_MAPMES', grpA), ('SYSFNT14', grpA), ('SYSFNT15', grpA),
                      ('SYSFNT16', grpA), ('SYSFNT18', grpA), ('SYSFNT20', grpA), ('F_EVENT', grpB), ('F_ENDING', grpB)):
        n = '/DATACMN/%s.FNT' % name; orig = rd(n); fo = fnt.parse(orig)
        oc = set(fo['codes'])
        need = {c for c in grp if c > 0x20}
        ko_map = {c: korev[c] for c in need if c in korev}
        # 원본에 없는 기호는 TTF 로 그림
        for c in need - oc - set(ko_map):
            try:
                ch = bytes([c >> 8, c & 255]).decode('cp932') if c > 255 else chr(c)
                ko_map[c] = ch
            except UnicodeDecodeError: pass
        keep = (oc & need) | {c for c in oc if c < 0x80} | {0x8140}
        data, info = mkfont.build(orig, ko_map, keep, width=fo['w'])
        out[n] = data; print('폰트', name, '원본 %dx%d %d자 → %dx%d %d자' % (fo['w'], fo['h'], len(oc), *info))
    out.update(build_img.images(rd))
    isopatch.patch(SRC, DST, out)
    print('완료 %.0f초 → %s' % (time.time() - t0, DST))

if __name__ == '__main__':
    main()
