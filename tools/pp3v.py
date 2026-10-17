"""PP3V 필드 스크립트: 헤더(0x10, 시작라벨, 라벨수, 라벨표오프셋), 워드 코드, 라벨표(워드 인덱스, 코드시작 0x10 기준), 디버그 이름.
FFFD <id> = 라벨 정의, FB52 <SJIS문자열 NUL, 4바이트 정렬> = 메시지 정의."""
import struct
MSG = 0xfb52
def parse(d):
    hs, entry, n, tab = struct.unpack_from('<4I', d, 0)
    code = d[hs:tab]
    items = []   # ('w', word) | ('s', bytes)
    i = 0
    while i < len(code):
        w, = struct.unpack_from('<I', code, i); items.append(('w', w)); i += 4
        if w == MSG:
            j = code.index(b'\0', i); s = code[i:j]; items.append(('s', s)); i = (j + 4) & ~3
    labels = struct.unpack_from('<%dI' % n, d, tab)
    return dict(hs=hs, entry=entry, items=items, labels=labels, rest=d[tab+4*n:])
def strings(p):
    return [it[1] for it in p['items'] if it[0] == 's']
def build(p, new):
    """new: 문자열 목록(순서대로). 라벨 위치를 FFFD 정의로 재계산"""
    out = bytearray(); k = 0; lab = {}
    its = p['items']
    for idx, (t, v) in enumerate(its):
        if t == 'w':
            if v == 0xfffd and idx + 1 < len(its) and its[idx+1][0] == 'w':
                lab.setdefault(its[idx+1][1], len(out)//4)
            out += struct.pack('<I', v)
        else:
            s = new[k]; k += 1
            b = s + b'\0'; b += b'\0' * (-len(b) % 4); out += b
    labels = []
    for i, w in enumerate(p['labels']):
        labels.append(lab[i])
    hs = p['hs']; tab = hs + len(out)
    entry = labels[0] if p['entry'] == p['labels'][0] else p['entry']
    head = struct.pack('<4I', hs, entry, len(labels), tab)
    return head + bytes(out) + struct.pack('<%dI' % len(labels), *labels) + p['rest']
