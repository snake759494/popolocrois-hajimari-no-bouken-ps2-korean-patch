"""메뉴 스프라이트(XCM 뱅크) 한글화 명세와 적용.  EDITS[XPF][뱅크] = [(상자(캔버스 좌표), 한국어, 방식)]
방식: 'clear' = 상자를 투명하게 비우고 원래 글자색·외곽선색으로 새로 씀, 'inpaint' = 배경을 복원하고 씀"""
import os, sys, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
import imgpatch, xcmedit
FONT = imgpatch.FONT

EDITS = {
    'MEMORY': {13: [((0, 0, 128, 32), '책갈피에 기록', 'clear')],
               14: [((0, 0, 128, 32), '책갈피 열기', 'clear')],
               2: [((26, 0, 82, 22), '피논', 'clear', dict(keep=(0, 8, 52, 88)))],
               3: [((26, 0, 82, 22), '루나', 'clear', dict(keep=(0, 8, 52, 88)))],
               4: [((26, 0, 82, 22), '마르코', 'clear', dict(keep=(0, 8, 52, 88)))]},
    'SYSTEM': {19: [((0, 0, 14, 18), '소', 'clear'), ((147, 0, 161, 18), '대', 'clear')],
               26: [((8, 6, 152, 34), '원작 만화 읽는 법', 'inpaint', dict(text_color=(40, 160, 60), outline=(20, 40, 10), flat=True))],
               27: [((8, 6, 152, 34), '설치 중지', 'inpaint', dict(text_color=(40, 160, 60), outline=(20, 40, 10), flat=True))],
               39: [((195, 0, 270, 25), '도망', 'clear'), ((7, 28, 100, 56), '작전 변경', 'clear'),
                    ((330, 27, 392, 54), '공격', 'clear'), ((330, 78, 392, 105), '특기', 'clear'),
                    ((1, 102, 106, 129), '도움말', 'clear'), ((330, 125, 392, 152), '도구', 'clear'),
                    ((0, 172, 113, 196), '커서 이동', 'clear'), ((311, 171, 417, 196), '취소', 'clear')],
               44: [((4, 12, 110, 38), '카메라 조작', 'clear'), ((184, 0, 272, 23), '카메라 초기화', 'clear'),
                    ((313, 12, 419, 38), '카메라 조작', 'clear'), ((319, 51, 411, 78), '정령 변경', 'clear'),
                    ((12, 63, 104, 90), '정령 변경', 'clear'), ((303, 95, 420, 115), '상태 메뉴', 'clear'),
                    ((3, 116, 109, 143), '지도', 'clear'), ((320, 132, 411, 159), '정령 사용', 'clear'),
                    ((0, 171, 114, 194), '시스템 메뉴', 'clear'), ((304, 173, 415, 198), '결정', 'clear'),
                    ((24, 219, 76, 245), '이동', 'clear'), ((304, 219, 414, 246), '취소', 'clear')]},
    'FIELD': {34: [((0, 2, 16, 22), '풍', 'clear')], 35: [((0, 2, 16, 22), '염', 'clear')], 36: [((0, 2, 16, 22), '수', 'clear')]},
    'BATTLE': {69: [((0, 0, 24, 32), '공', 'clear')], 70: [((0, 0, 24, 32), '특', 'clear')], 71: [((0, 0, 24, 32), '도', 'clear')],
               72: [((10, 12, 40, 36), '도망', 'inpaint')]},
    'TTITLE': {7: [((286, 78, 452, 120), '시작의 모험', 'clear')]},
}

def _colors(cv, box):
    x0, y0, x1, y1 = box; sub = cv[y0:y1, x0:x1].reshape(-1, 4).astype(int)
    op = sub[sub[:, 3] > 200]
    if len(op) == 0: op = sub[sub[:, 3] > 0]
    if len(op) == 0: return (255, 255, 255), (0, 0, 0)
    lum = op[:, :3].mean(1)
    hi = op[lum >= np.percentile(lum, 70)][:, :3].mean(0); lo = op[lum <= np.percentile(lum, 20)][:, :3].mean(0)
    return tuple(int(v) for v in hi), tuple(int(v) for v in lo)

def _text_layer(W, H, text, color, outline, ow, maxsize):
    size = imgpatch.fit_size(text, W, H, maxsize, ow=ow); ss = 4
    f = ImageFont.truetype(FONT, size * ss); big = Image.new('RGBA', (W * ss, H * ss), (0, 0, 0, 0)); d = ImageDraw.Draw(big)
    b = f.getbbox(text); x = (W * ss - (b[2] - b[0])) // 2 - b[0]; y = (H * ss - (b[3] - b[1])) // 2 - b[1]
    if outline is not None and ow:
        d.text((x, y), text, font=f, fill=tuple(outline) + (255,), stroke_width=ow * ss, stroke_fill=tuple(outline) + (255,))
    d.text((x, y), text, font=f, fill=tuple(color) + (255,))
    return np.asarray(big.resize((W, H), Image.LANCZOS))

_col = {}
def apply_edit(cv, box, text, mode, opt={}):
    x0, y0, x1, y1 = box; x1 = min(x1, cv.shape[1]); y1 = min(y1, cv.shape[0]); box = (x0, y0, x1, y1)
    W, H = x1 - x0, y1 - y0
    if mode == 'draw' and id(text) in _col: hi, lo = _col.pop(id(text))
    else: hi, lo = _colors(cv, box)
    if mode == 'erase':
        _col[id(text)] = (hi, lo); out = cv.copy(); kp = opt.get('keep')
        if kp:   # 겹친 그림 영역: 글자색(흰/검) 픽셀만 주변으로 복원
            sub = out[y0:y1, x0:x1, :3].astype(int); lum = sub.mean(2); sat = sub.max(2) - sub.min(2)
            tm = ((lum > 150) & (sat < 70)) | (lum < 85)
            m = np.zeros(out.shape[:2], np.uint8); m[y0:y1, x0:x1] = tm * 255
            k0, k1, k2, k3 = kp; inside = np.zeros_like(m); inside[k1:k3, k0:k2] = 255
            rgb = cv2.inpaint(np.ascontiguousarray(out[..., :3]), cv2.dilate(m, np.ones((5, 5), np.uint8)) & inside, 4, cv2.INPAINT_TELEA)
            out[..., :3] = rgb
            clr = np.zeros(out.shape[:2], bool); clr[y0:y1, x0:x1] = True; clr[k1:k3, k0:k2] = False
            out[clr] = 0
        else:
            out[y0:y1, x0:x1] = 0
        return out
    # 외곽선 유무: 밝기 차가 크면 외곽선 있음
    has_ol = abs(sum(hi) - sum(lo)) > 150
    fg, ol = (hi, lo) if has_ol else (hi, None)
    if not has_ol and sum(hi) < 200: fg = hi       # 어두운 단색 글자
    ow = 2 if has_ol and H >= 20 else (1 if has_ol else 0)
    lay = _text_layer(W, H, text, fg, ol, ow, H)
    out = cv.copy()
    if mode == 'draw':
        a = lay[..., 3:4].astype(np.float32) / 255; reg = out[y0:y1, x0:x1].astype(np.float32)
        ra = reg[..., 3:4] / 255; na = a + ra * (1 - a)
        rgb = (lay[..., :3] * a + reg[..., :3] * ra * (1 - a)) / np.maximum(na, 1e-6)
        out[y0:y1, x0:x1, :3] = rgb.astype(np.uint8); out[y0:y1, x0:x1, 3] = (na[..., 0] * 255).astype(np.uint8)
    else:
        rgb = np.ascontiguousarray(out[..., :3])
        sub = rgb[y0:y1, x0:x1].astype(int); al = out[y0:y1, x0:x1, 3]
        # 글자 = 배경 대표색과 색 거리가 큰 픽셀
        bgc = np.median(sub[al > 200].reshape(-1, 3), 0) if (al > 200).any() else np.median(sub.reshape(-1, 3), 0)
        dist = np.sqrt(((sub - bgc) ** 2).sum(2)); m = np.zeros(rgb.shape[:2], np.uint8)
        m[y0:y1, x0:x1] = ((dist > 70) & (al > 0)).astype(np.uint8) * 255
        m = cv2.dilate(m, np.ones((3, 3), np.uint8))
        if opt.get('flat'):
            o = sub[(al > 200) & (sub[..., 0] > 190) & (sub[..., 1] < 170) & (sub[..., 2] < 90)]
            if len(o): bgc = np.median(o, 0)
            band = rgb[y0:y1, x0:x1]; band[al > 0] = bgc.astype(np.uint8); rgb[y0:y1, x0:x1] = band
        else:
            rgb = cv2.inpaint(rgb, m, 5, cv2.INPAINT_TELEA)
        if opt.get('text_color'): hi, lo = opt['text_color'], opt.get('outline', lo); lay = _text_layer(W, H, text, hi, lo, 1, H)
        a = lay[..., 3:4].astype(np.float32) / 255
        rgb[y0:y1, x0:x1] = (rgb[y0:y1, x0:x1] * (1 - a) + lay[..., :3] * a).astype(np.uint8)
        out[..., :3] = rgb
    return out

def coverage(P, bi, org, shape):
    C = np.zeros(shape[:2], bool); x0, y0 = org
    for p in P.placements(bi): C[p['y'] - y0:p['y'] - y0 + p['h'], p['x'] - x0:p['x'] - x0 + p['w']] = True
    return C

def fit_box(C, box):
    x0, y0, x1, y1 = box; x1 = min(x1, C.shape[1]); y1 = min(y1, C.shape[0])
    if C[y0:y1, x0:x1].all(): return (x0, y0, x1, y1)
    best = None; H = y1 - y0
    for t in range(y0, y1):
        for b in range(y1, t + max(8, int(H * 0.6)) - 1, -1):
            cols = C[t:b, x0:x1].all(0); run = 0; bs = 0; be = 0; st = 0
            for i, c in enumerate(cols):
                if c:
                    if run == 0: st = i
                    run += 1
                    if run > be - bs: bs, be = st, i + 1
                else: run = 0
            area = (be - bs) * (b - t)
            if best is None or area > best[0]: best = (area, (x0 + bs, t, x0 + be, b))
    return best[1] if best else box

def patch(name, ents):
    """name: 'MEMORY' 등, ents: {항목: bytes} → 새 ents"""
    P = xcmedit.Pack(ents); moved = 0
    for bi, lst in EDITS[name].items():
        cv, org = P.canvas(bi); C = coverage(P, bi, org, cv.shape)
        for e in lst:
            box, text, mode = e[:3]; opt = e[3] if len(e) > 3 else {}
            if mode == 'clear': cv = apply_edit(cv, box, text, 'erase', opt); box = fit_box(C, box); cv = apply_edit(cv, box, text, 'draw', opt)
            else: cv = apply_edit(cv, box, text, mode, opt)
        moved += P.write(bi, cv, org)
    return P.save(), moved
