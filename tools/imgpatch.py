"""이미지 속 일본어 → 한국어: 글자 픽셀을 지우고(인페인팅) 나눔스퀘어 네오로 다시 그린 뒤 원래 팔레트로 양자화."""
import os, sys, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
import xim
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(R, 'NanumSquareNeo-dEb.ttf')

def text_mask(rgb, box, mode):
    x0, y0, x1, y1 = box
    sub = rgb[y0:y1, x0:x1].astype(int)
    mx = sub.max(2); mn = sub.min(2)
    lum = sub.mean(2)
    if mode == 'white':          # 흰 글자 + 어두운 외곽선 (어두운 지도는 상대 기준)
        thr = min(175, np.percentile(mn, 93))
        core = (mn > thr) & (mx - mn < 70)
    elif mode == 'gold':         # 금색 글자
        thr = np.percentile(lum, 85)
        core = (lum > thr) & (sub[..., 0] > sub[..., 2] + 40)
    elif mode == 'dark':         # 어두운 글자(밝은 배경)
        core = mx < 110
    elif mode == 'light':        # 밝은 글자(어두운 배경)
        core = mn > 120
    else:
        core = np.ones(sub.shape[:2], bool)
    m = np.zeros(rgb.shape[:2], np.uint8); m[y0:y1, x0:x1] = core.astype(np.uint8) * 255
    return m

def erase(rgb, box, mode, grow=3):
    m = text_mask(rgb, box, mode)
    if grow: m = cv2.dilate(m, np.ones((2 * grow + 1, 2 * grow + 1), np.uint8))
    x0, y0, x1, y1 = box; clip = np.zeros_like(m); clip[y0:y1, x0:x1] = 255; m &= clip
    return cv2.inpaint(np.ascontiguousarray(rgb), m, 4, cv2.INPAINT_TELEA), m

def fill_box(rgb, box, color):
    x0, y0, x1, y1 = box; out = rgb.copy(); out[y0:y1, x0:x1] = color; return out

def draw(rgb, box, text, size, fill, outline=None, ow=2, align='c', font=FONT, spacing=2, ss=4):
    """box 안에 text(줄바꿈 \\n 가능) 를 그림. 초과표본 후 축소해 부드럽게."""
    x0, y0, x1, y1 = box; W, H = x1 - x0, y1 - y0
    f = ImageFont.truetype(font, size * ss)
    lines = text.split('\n')
    lh = [f.getbbox(l or ' ') for l in lines]
    big = Image.new('RGBA', (W * ss, H * ss), (0, 0, 0, 0)); d = ImageDraw.Draw(big)
    hs = [b[3] - b[1] for b in lh]; tot = sum(hs) + spacing * ss * (len(lines) - 1)
    y = (H * ss - tot) // 2
    for l, b, h in zip(lines, lh, hs):
        tw = b[2] - b[0]
        x = (W * ss - tw) // 2 if align == 'c' else (ow * ss if align == 'l' else W * ss - tw - ow * ss)
        if outline is not None:
            d.text((x - b[0], y - b[1]), l, font=f, fill=tuple(outline) + (255,), stroke_width=ow * ss, stroke_fill=tuple(outline) + (255,))
        d.text((x - b[0], y - b[1]), l, font=f, fill=tuple(fill) + (255,))
        y += h + spacing * ss
    sm = np.asarray(big.resize((W, H), Image.LANCZOS)).astype(np.float32)
    a = sm[..., 3:4] / 255.0
    out = rgb.copy().astype(np.float32)
    out[y0:y1, x0:x1] = out[y0:y1, x0:x1] * (1 - a) + sm[..., :3] * a
    draw.last_alpha = sm[..., 3]
    return np.clip(out, 0, 255).astype(np.uint8)

def fit_size(text, maxw, maxh, start, font=FONT, ow=2):
    s = start
    while s > 6:
        f = ImageFont.truetype(font, s)
        ws = [f.getbbox(l or ' ')[2] - f.getbbox(l or ' ')[0] for l in text.split('\n')]
        hs = sum(f.getbbox(l or ' ')[3] - f.getbbox(l or ' ')[1] + 2 for l in text.split('\n'))
        if max(ws) + 2 * ow <= maxw and hs + 2 * ow <= maxh: return s
        s -= 1
    return s

def apply(xdata, edits):
    """xdata: XIM bytes, edits: [{box, mode, text, size, fill, outline, ow, align, erase:True|'fill'(color)}]"""
    X = xim.parse(xdata)
    img = xim.rgba(X); rgb = np.ascontiguousarray(img[..., :3]); alpha = img[..., 3]
    changed = np.zeros(rgb.shape[:2], bool)
    for e in edits:
        box = tuple(e['box'])
        if e.get('bg') == 'clear':                   # 투명 배경: 상자를 투명으로
            x0, y0, x1, y1 = box; alpha = alpha.copy(); alpha[y0:y1, x0:x1] = 0
        elif e.get('fill') is not None and e.get('bg') is not None:
            rgb = fill_box(rgb, box, e['bg'])
        elif e.get('refmask') is not None:          # 다른 이미지에서 구한 글자 마스크 사용
            core = e['refmask'] > 0
            if e.get('color') == 'auto': e = dict(e, color=tuple(int(v) for v in rgb[core].mean(0)))
            g = e.get('grow', 3); m = cv2.dilate(core.astype(np.uint8) * 255, np.ones((2 * g + 1, 2 * g + 1), np.uint8))
            rgb = cv2.inpaint(np.ascontiguousarray(rgb), m, 4, cv2.INPAINT_TELEA)
        elif e.get('mode', 'white') != 'none':
            core = text_mask(rgb, box, e.get('mode', 'white')) > 0
            if e.get('color') == 'auto': e = dict(e, color=tuple(int(v) for v in rgb[core].mean(0)) if core.any() else (255, 255, 255))
            rgb, m = erase(rgb, box, e.get('mode', 'white'), e.get('grow', 3))
        if e.get('text'):
            x0, y0, x1, y1 = box
            size = e.get('size') or fit_size(e['text'], x1 - x0, y1 - y0 - e.get('spacing', 2) * e['text'].count(chr(10)), 40, ow=e.get('ow', 2))
            if e.get('maxsize'): size = min(size, e['maxsize'])
            rgb = draw(rgb, box, e['text'], size, e.get('color', (255, 255, 255)), e.get('outline'), e.get('ow', 2), e.get('align', 'c'), spacing=e.get('spacing', 2))
            if e.get('bg') == 'clear':
                x0, y0, x1, y1 = box; ta = draw.last_alpha
                alpha[y0:y1, x0:x1] = np.where(ta > 110, e.get('alpha', 128), 0).astype(alpha.dtype)
        x0, y0, x1, y1 = box; changed[y0:y1, x0:x1] = True
    out = np.dstack([rgb, alpha])
    xim.quantize(X, out, changed)
    return xim.build(X), out

def apply_clear(xdata, edits):
    """투명 배경 글자 아틀라스용: 상자를 인덱스 0(투명)으로 비우고, 글자만 불투명 픽셀로 양자화"""
    X = xim.parse(xdata); pal = xim.palette(X).astype(np.int32)
    usable = [i for i in range(len(pal)) if pal[i, 3] > 0x40]
    for e in edits:
        x0, y0, x1, y1 = e['box']; W, H = x1 - x0, y1 - y0
        X['idx'][y0:y1, x0:x1] = 0
        size = e.get('size') or fit_size(e['text'], W, H, 40, ow=e.get('ow', 2))
        canvas = np.zeros((H, W, 3), np.uint8)
        f = ImageFont.truetype(FONT, size * 4); big = Image.new('RGBA', (W * 4, H * 4), (0, 0, 0, 0)); d = ImageDraw.Draw(big)
        b = f.getbbox(e['text']); tw, th = b[2] - b[0], b[3] - b[1]
        x = (W * 4 - tw) // 2 - b[0]; y = (H * 4 - th) // 2 - b[1]
        ow = e.get('ow', 2) * 4
        d.text((x, y), e['text'], font=f, fill=tuple(e.get('color', (255, 255, 255))) + (255,), stroke_width=ow, stroke_fill=tuple(e.get('outline', (30, 20, 40))) + (255,))
        d.text((x, y), e['text'], font=f, fill=tuple(e.get('color', (255, 255, 255))) + (255,))
        sm = np.asarray(big.resize((W, H), Image.LANCZOS)).astype(np.int32)
        ys, xs = np.nonzero(sm[..., 3] > 110)
        src = sm[ys, xs]; src[:, 3] = 255
        best = np.zeros(len(ys), np.int64); bd = np.full(len(ys), 1 << 60, np.int64)
        for i in usable:
            dd = ((src - pal[i]) ** 2 * np.array([3, 4, 2, 1])).sum(1); m = dd < bd; bd[m] = dd[m]; best[m] = i
        X['idx'][y0 + ys, x0 + xs] = best
    return xim.build(X)
