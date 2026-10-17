"""XCM 스프라이트 정의.
헤더: u32 뱅크시작, u32, u32, u32 이름수, 이름(NUL 구분) — 이름 = 같은 XPF 안 XIM(확장자 제외)
뱅크시작: u32 뱅크수, 뱅크×[ u32 번호, u32 레코드수, 레코드×[ u32 텍스처번호, s16 x, s16 y, u16 타일폭, u16 타일높이,
u16 개수, u16 프레임수, (u16 u, u16 v)×(개수×프레임수) ] ]  (타일 i 는 x+i*타일폭 에 그림; 프레임은 개수 단위 반복)"""
import struct
def parse(d):
    o0, a, b, nn = struct.unpack_from('<4I', d, 0)
    names = [n.decode() for n in d[16:o0].split(b'\0')[:nn]]
    nb, = struct.unpack_from('<I', d, o0); o = o0 + 4; banks = []
    for _ in range(nb):
        bid, cnt = struct.unpack_from('<2I', d, o); ho = o; o += 8; recs = []
        for _ in range(cnt):
            t, x, y, tw, th, n, fr = struct.unpack_from('<IhhHHHH', d, o)
            m = n * max(1, fr)
            uv = [list(struct.unpack_from('<HH', d, o + 16 + 4 * i)) for i in range(m)]
            recs.append(dict(off=o, t=t, x=x, y=y, tw=tw, th=th, n=n, fr=fr, uv=uv)); o += 16 + 4 * m
        banks.append(dict(off=ho, id=bid, recs=recs))
    return dict(names=names, banks=banks, end=o, d=d)
def write_uv(c):
    d = bytearray(c['d'])
    for b in c['banks']:
        for r in b['recs']:
            for i, (u, v) in enumerate(r['uv']): struct.pack_into('<HH', d, r['off'] + 16 + 4 * i, u, v)
    return bytes(d)
