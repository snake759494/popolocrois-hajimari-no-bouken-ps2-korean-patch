"""XCM 뱅크 조립 렌더(프레임 0)"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import xim
def bank_canvas(c, IM, bank, frame=0):
    tl = []
    for r in bank['recs']:
        for i in range(r['n']):
            k = frame * r['n'] + i if r['fr'] > 1 else i
            u, v = r['uv'][min(k, len(r['uv']) - 1)]
            tl.append((r['x'] + i * r['tw'], r['y'], r['tw'], r['th'], r['t'], u, v))
    if not tl: return None, (0, 0)
    x0 = min(t[0] for t in tl); y0 = min(t[1] for t in tl)
    x1 = max(t[0] + t[2] for t in tl); y1 = max(t[1] + t[3] for t in tl)
    cv = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
    for X, Y, w, h, t, u, v in tl:
        img = IM[c['names'][t]]; p = img[v:v + h, u:u + w]
        m = p[..., 3] > 0; cv[Y - y0:Y - y0 + p.shape[0], X - x0:X - x0 + p.shape[1]][m] = p[m]
    return cv, (x0, y0)
