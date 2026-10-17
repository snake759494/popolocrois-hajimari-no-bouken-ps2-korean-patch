"""XCM 뱅크를 이미지로 조립: 텍스처 1 = 4bpp XIM(앞 두 개 제외) 세로 합성, 2 = 8bpp XIM 세로 합성"""
import sys, os, struct, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import xim, xcm
def stacks(E, names, skip=2):
    s4 = []; s8 = []
    for i, n in enumerate(names):
        X = xim.parse(E[n + '.xim'])
        if X['bpp'] == 4:
            if i >= skip: s4.append((n, X))
        else: s8.append((n, X))
    out = {}
    for t, lst in ((1, s4), (2, s8)):
        y = 0; m = []
        for n, X in lst: m.append((n, y, X)); y += X['h']
        out[t] = m
    return out
def locate(st, tex, u, v):
    for n, y0, X in st[tex]:
        if y0 <= v < y0 + X['h']: return n, X, u, v - y0
    return None
def render(c, st, bank, W=512, H=256, ox=256, oy=96):
    canvas = np.zeros((H, W, 4), np.uint8)
    for r in bank['recs']:
        for i, (u, v) in enumerate(r['uv']):
            L = locate(st, r['tex'], u, v)
            if not L: continue
            n, X, uu, vv = L; img = xim.rgba(X)
            X0 = r['x'] + ox + i * r['tw']; Y0 = r['y'] + oy
            t = img[vv:vv + r['th'], uu:uu + r['tw']]
            if 0 <= X0 and X0 + t.shape[1] <= W and 0 <= Y0 and Y0 + t.shape[0] <= H:
                m = t[..., 3] > 0; canvas[Y0:Y0 + t.shape[0], X0:X0 + t.shape[1]][m] = t[m]
    return canvas
