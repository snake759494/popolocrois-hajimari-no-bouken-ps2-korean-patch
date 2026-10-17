"""필드 대사(pp3v.json) 자동 줄 재배치.
필드 창: 2바이트 고정 폭 → 한 줄 ≤ 17칸(공백·기호 포함 모두 1칸), 페이지 ≤ 3줄, 페이지 ≤ 106바이트.
넘치는 페이지만 단어 단위로 다시 감싼다. 그래도 안 되면 목록 출력(수동 수정)."""
import json, os, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = chr(92); W = 17; MAXL = 3; MAXB = 106

def pbytes(lines):
    return sum(2 * len(l) for l in lines) + 2 * (len(lines) - 1)

def ok(lines):
    return all(len(l) <= W for l in lines) and len(lines) <= MAXL and pbytes(lines) <= MAXB

def wrap(text):
    words = text.split(' '); lines = ['']
    for w in words:
        if not w: continue
        cand = (lines[-1] + ' ' + w) if lines[-1] else w
        if len(cand) <= W: lines[-1] = cand
        else:
            if len(w) > W:   # 긴 단어는 강제로 자름
                if lines[-1]: lines.append('')
                while len(w) > W: lines[-1] = w[:W]; w = w[W:]; lines.append('')
                lines[-1] = w
            else: lines.append(w)
    return lines

def fix_page(pg):
    lines = pg.split(B + 'n')
    if ok(lines): return pg, True
    lead = ''
    if lines and lines[0] == '': lead = B + 'n'; lines = lines[1:]   # 앞의 빈 줄 유지
    nl = wrap(' '.join(l.strip() for l in lines if l.strip()))
    if not ok(nl) and pbytes(nl) > MAXB:
        nl = wrap(' '.join(l.strip() for l in lines if l.strip()).replace(' ', ''))   # 공백 제거 후 재시도
    return lead + (B + 'n').join(nl), ok(nl)

def main():
    p = os.path.join(R, 'translation', 'pp3v.json')
    P = json.load(open(p, encoding='utf-8')); changed = 0; bad = []
    for x in P:
        ko = x.get('ko')
        if not ko: continue
        pages = ko.split(B + 'c'); out = []; good = True
        for pg in pages:
            np_, g = fix_page(pg); out.append(np_); good &= g
        nk = (B + 'c').join(out)
        if nk != ko: x['ko'] = nk; changed += 1
        if not good: bad.append(x['id'])
    json.dump(P, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('재배치', changed, '실패', bad)

if __name__ == '__main__':
    main()
