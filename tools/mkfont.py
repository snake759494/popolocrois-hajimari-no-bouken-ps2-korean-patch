"""한글 FNT 생성: 원본 폰트에서 유지할 코드의 글리프는 그대로, 한글은 나눔스퀘어 네오로 렌더해 새 아틀라스에 배치."""
import os, sys, struct, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
import fnt
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TTF = os.path.join(R, 'NanumSquareNeo-dEb.ttf')

def style(f):
    """원본 폰트의 외곽선 인덱스(가장 흔한 큰 값), 몸체=1"""
    h = np.bincount(f['pix'].ravel(), minlength=16)
    O = int(np.argmax(h[8:]) + 8)
    return O

def kanji_metrics(f):
    """원본 한자 레코드에서 가장 흔한 메트릭(바이트1~5)과 글리프 높이"""
    import collections
    c = collections.Counter()
    for r, code in zip(f['recs'], f['codes']):
        if 0x889f <= code < 0xeb00: c[bytes(r[1:6])] += 1
    m = c.most_common(1)[0][0]
    return m

_cache = {}
def render(ch, asc, desc, O, outline, ttf=TTF):
    """글리프 픽셀(높이 asc+desc, 폭 자동) 반환. asc/desc 는 기준선 위/아래 픽셀"""
    H = asc + desc
    if ch == '␠': return np.zeros((H, max(4, H // 3)), np.uint8)
    key = (ch, asc, desc, O, outline, ttf)
    if key in _cache: return _cache[key]
    body_h = H - 2*outline                    # 몸체 높이
    SS = 4                                    # 초과표본
    size = _fit_size(body_h, ttf)
    font = ImageFont.truetype(ttf, size * SS)
    W = H * 2
    im = Image.new('L', (W*SS, H*SS), 0); d = ImageDraw.Draw(im)
    # '한' 기준 세로 위치 맞춤
    top = _ref_top(size, ttf)
    d.text((outline*SS*2, (outline - top) * SS), ch, font=font, fill=255)
    a = np.asarray(im.resize((W, H), Image.LANCZOS), np.float32) / 255.0
    a = np.clip(a * 1.15, 0, 1)
    body = a > 0.5
    # 외곽선: 몸체 커버리지를 outline 픽셀만큼 팽창
    m = Image.fromarray((a > 0.25).astype(np.uint8) * 255)
    m = m.filter(ImageFilter.MaxFilter(2*outline + 1))
    om = np.asarray(m) > 0
    idx = np.zeros((H, W), np.uint8)
    idx[om] = O
    t = a                                      # 1 → 몸체(1), 0 → 외곽선(O)
    inner = om & (a > 0.08)
    idx[inner] = np.clip(np.round(O - t[inner] * (O - 1)), 1, O).astype(np.uint8)
    cols = np.where(om.any(0))[0]
    if len(cols) == 0:
        g = np.zeros((H, 0), np.uint8)
    else:
        g = idx[:, cols[0]:cols[-1] + 1]
    _cache[key] = g
    return g

_fs = {}
def _fit_size(body_h, ttf):
    k = (body_h, ttf)
    if k in _fs: return _fs[k]
    best = 8
    for s in range(6, 64):
        f = ImageFont.truetype(ttf, s)
        x0, y0, x1, y1 = f.getbbox('뷁햏곩갂')
        if y1 - y0 <= body_h: best = s
        else: break
    _fs[k] = best; return best
def _ref_top(size, ttf):
    f = ImageFont.truetype(ttf, size)
    return f.getbbox('뷁햏곩갂')[1]

def build(orig, ko_map, keep, extra=None, width=None, ttf=TTF, outline=None):
    """orig: 원본 FNT bytes, ko_map: {코드: 문자}(새로 그릴 것), keep: 유지할 원본 코드 집합.
    반환: 새 FNT bytes"""
    f = fnt.parse(orig); kind = f['kind']; O = style(f)
    m = kanji_metrics(f)                      # [줄높이, asc, desc, left, 0]
    asc, desc = m[1], (m[2] - 256 if m[2] > 127 else m[2])
    if outline is None: outline = 2 if f['head'][2] >= 21 else 1
    glyphs = []                                # (code, rec(bytearray), pix)
    for r, code in zip(f['recs'], f['codes']):
        if code in keep and code not in ko_map:
            x0, y0, x1, y1 = fnt.rect(r, kind)
            if not r[0]: g = None
            elif y1 - y0 > 2 * f['head'][2]: g = np.zeros((asc + desc, r[0]), np.uint8)   # 전각 공백 등 이상 높이 → 빈칸
            else: g = f['pix'][y0:y1, x0:x1].copy()
            glyphs.append((code, bytearray(r), g))
    sp = None
    for r, code in zip(f['recs'], f['codes']):
        if code == 0x20: sp = bytearray(r)
    for code, ch in ko_map.items():
        if ch == '␠':                         # 전용 공백: 폭 작은 빈 글리프
            sw = max(4, (asc + desc) // 4)
            r = bytearray(20); r[0] = sw; r[1:6] = m; r[1] = sw; r[4] = 0; struct.pack_into('<H', r, 6, code)
            glyphs.append((code, r, np.zeros((asc + desc, sw), np.uint8))); continue
        g = render(ch, asc, desc, O, outline, ttf)
        r = bytearray(20); r[0] = g.shape[1]; r[1:6] = m; struct.pack_into('<H', r, 6, code)
        glyphs.append((code, r, g))
    glyphs.sort(key=lambda x: x[0])
    # 배치
    W = width or 1024
    rowh = max((g.shape[0] for _, _, g in glyphs if g is not None), default=1) + 1
    x = y = 0; place = []
    for code, r, g in glyphs:
        if g is None or g.shape[1] == 0: place.append(None); continue
        w = g.shape[1]
        if x + w > W: x = 0; y += rowh
        place.append((x, y)); x += w + 1
    H = y + rowh
    H = (H + 7) // 8 * 8
    assert H <= 1024, ('아틀라스 높이 초과', H)
    pix = np.zeros((H, W), np.uint8)
    recs = []; codes = []
    for (code, r, g), p in zip(glyphs, place):
        if p is not None:
            px, py = p; h, w = g.shape
            pix[py:py+h, px:px+w] = g
            fnt.set_rect(r, kind, px, py, px + w, py + h)
        recs.append(r); codes.append(code)
    nf = dict(kind=kind, head=f['head'], recs=recs, codes=codes, pix=pix, tail=b'', short=0)
    return fnt.build(nf), (W, H, len(recs))
