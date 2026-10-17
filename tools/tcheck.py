"""번역 검사.  python tcheck.py <json 파일들...>
규칙: 제어코드 보존, 줄 폭, 페이지 줄 수, ELF 바이트 상한, 허용 문자"""
import sys, json, re
B = chr(92)
ALLOWED_FW = set('、。・！？「」『』（）〜…ー―＋－×÷＝％：＆☆★○●◎◇◆□■△▲▽▼→←↑↓♪　＜＞／＃＊＠｛｝［］"＇“”‘’～·')
def width(s):
    return sum(0.5 if ord(c) < 0x80 else 1 for c in s)
def bad_chars(s):
    out = []
    for c in s:
        o = ord(c)
        if o < 0x80 or 0xac00 <= o <= 0xd7a3 or c in ALLOWED_FW or 0xff10 <= o <= 0xff5a: continue
        out.append(c)
    return out
def sjis_len(s):
    return sum(1 if ord(c) < 0x80 else 2 for c in s)
def check(kind, it):
    ko = it.get('ko', '')
    if not ko: return []
    jp = it['jp']; err = []
    bc = bad_chars(ko)
    if bc: err.append('허용 안 되는 문자 %r' % ''.join(sorted(set(bc))))
    if kind == 'pp3v':
        if ko.count(B + 'c') != jp.count(B + 'c'): err.append('\\c 개수 다름(원문 %d)' % jp.count(B + 'c'))
        for pi, page in enumerate(ko.split(B + 'c')):
            L = page.split(B + 'n')
            if len(L) > max(3, len(jp.split(B + 'c')[pi].split(B + 'n')) if pi < len(jp.split(B + 'c')) else 3): err.append('페이지 %d 줄 수 %d' % (pi, len(L)))
            for l in L:
                if width(l) > 18: err.append('줄 폭 %.1f > 18: %s' % (width(l), l))
        if B in ko.replace(B + 'n', '').replace(B + 'c', ''): err.append('알 수 없는 역슬래시')
    elif kind == 'ejt':
        L = ko.split('#N')
        if len(L) > 2: err.append('줄 수 %d > 2' % len(L))
        for l in L:
            if width(l) > 20: err.append('줄 폭 %.1f > 20: %s' % (width(l), l))
        if '\t' in ko or '\n' in ko: err.append('탭/개행 금지')
    elif kind == 'elf':
        n = sjis_len(ko)
        if n > it['max']: err.append('바이트 %d > max %d' % (n, it['max']))
        for fmt in re.findall(r'%[-0-9.]*[a-zA-Z]', jp):
            if fmt not in ko: err.append('서식 %s 누락' % fmt)
        if jp.count('\n') != ko.count('\n') and '\n' in jp: err.append('개행 수 다름')
    return err
if __name__ == '__main__':
    tot = 0
    for p in sys.argv[1:]:
        kind = 'pp3v' if 'pp3v' in p else 'ejt' if 'ejt' in p else 'elf'
        items = json.load(open(p, encoding='utf-8'))
        for it in items:
            e = check(kind, it)
            if e:
                tot += len(e); print('%s #%s: %s' % (p.split('/')[-1].split(chr(92))[-1], it['id'], ' / '.join(e)))
        done = sum(1 for i in items if i.get('ko') or i.get('note'))
        print('== %s: %d/%d 처리' % (p, done, len(items)))
    print('오류', tot)
