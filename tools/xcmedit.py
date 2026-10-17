"""XCM 스프라이트(뱅크) 편집: 조립 → 캔버스 편집 → 타일 재기록.
다른 곳과 공유되는 타일이나 같은 뱅크 안에서 내용이 갈라지는 타일은 텍스처의 미사용 영역에 새로 할당하고 uv 를 고친다."""
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import xim, xcm

class Pack:
    def __init__(s, ents):
        """ents: {항목명: 해제된 bytes} (XPF 하나)"""
        s.ents = ents
        s.xn = [n for n in ents if n.endswith('.xcm')][0]
        s.c = xcm.parse(ents[s.xn])
        s.X = {n: xim.parse(ents[n + '.xim']) for n in s.c['names']}
        s._used()

    def _used(s):
        s.used = {n: np.zeros((X['h'], X['w']), bool) for n, X in s.X.items()}
        s.refs = {}
        for bi, b in enumerate(s.c['banks']):
            for r in b['recs']:
                n = s.c['names'][r['t']]
                for (u, v) in r['uv']:
                    s.used[n][v:v + r['th'], u:u + r['tw']] = True
                    s.refs.setdefault((n, u, v, r['tw'], r['th']), set()).add(bi)

    def placements(s, bi):
        out = []
        for ri, r in enumerate(s.c['banks'][bi]['recs']):
            for i in range(r['n']):
                u, v = r['uv'][i]
                out.append(dict(r=r, i=i, x=r['x'] + i * r['tw'], y=r['y'], w=r['tw'], h=r['th'], n=s.c['names'][r['t']], u=u, v=v))
        return out

    def canvas(s, bi):
        """RGBA(알파 0..255) 캔버스, 원점"""
        P = s.placements(bi)
        x0 = min(p['x'] for p in P); y0 = min(p['y'] for p in P)
        x1 = max(p['x'] + p['w'] for p in P); y1 = max(p['y'] + p['h'] for p in P)
        cv = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
        for p in P:
            img = xim.rgba(s.X[p['n']])
            t = img[p['v']:p['v'] + p['h'], p['u']:p['u'] + p['w']].astype(np.int32)
            t[..., 3] = np.minimum(255, t[..., 3] * 2)
            m = t[..., 3] > 0
            reg = cv[p['y'] - y0:p['y'] - y0 + t.shape[0], p['x'] - x0:p['x'] - x0 + t.shape[1]]
            reg[m] = t[m]
        return cv, (x0, y0)

    def _quant(s, n, tile, err=False):
        X = s.X[n]; pal = xim.palette(X).astype(np.int32).copy(); pal[:, 3] = np.minimum(255, pal[:, 3] * 2)
        src = tile.reshape(-1, 4).astype(np.int32)
        best = np.zeros(len(src), np.int64); bd = np.full(len(src), 1 << 60, np.int64)
        for i in range(len(pal)):
            d = ((src - pal[i]) ** 2 * np.array([2, 3, 1, 4])).sum(1)
            d[(src[:, 3] < 8) & (pal[i, 3] >= 8)] += 1 << 40      # 투명은 투명으로
            m = d < bd; bd[m] = d[m]; best[m] = i
        if err: return best.reshape(tile.shape[:2]), bd.reshape(tile.shape[:2])
        return best.reshape(tile.shape[:2])

    def _alloc(s, n, w, h):
        U = s.used[n]; H, W = U.shape
        for v in range(0, H - h + 1, h):
            for u in range(0, W - w + 1, w):
                if not U[v:v + h, u:u + w].any():
                    U[v:v + h, u:u + w] = True; return u, v
        # 빈 곳이 없으면 텍스처 아래에 행을 덧붙임
        X = s.X[n]; add = max(h, 8)
        X['idx'] = np.vstack([X['idx'], np.zeros((add, W), X['idx'].dtype)]); X['h'] += add
        s.used[n] = np.vstack([U, np.zeros((add, W), bool)]); s.used[n][H:H + h, 0:w] = True
        return 0, H

    def write(s, bi, cv, org):
        """편집된 캔버스를 뱅크 bi 의 타일에 기록"""
        x0, y0 = org; P = s.placements(bi)
        # 겹친 층: 픽셀마다 오차가 가장 작은 층(같으면 위층)에만 그리고 나머지는 투명
        E = np.full(cv.shape[:2] + (len(P),), np.inf)
        for k, p in enumerate(P):
            t = cv[p['y'] - y0:p['y'] - y0 + p['h'], p['x'] - x0:p['x'] - x0 + p['w']]
            q, e = s._quant(p['n'], t, True)
            E[p['y'] - y0:p['y'] - y0 + t.shape[0], p['x'] - x0:p['x'] - x0 + t.shape[1], k] = e - k * 1e-3
        own = E.argmin(2)
        groups = {}
        for k, p in enumerate(P):
            t = cv[p['y'] - y0:p['y'] - y0 + p['h'], p['x'] - x0:p['x'] - x0 + p['w']].copy()
            mine = own[p['y'] - y0:p['y'] - y0 + p['h'], p['x'] - x0:p['x'] - x0 + p['w']] == k
            t[~mine] = 0
            q = s._quant(p['n'], t)
            groups.setdefault((p['n'], p['u'], p['v'], p['w'], p['h']), []).append((p, q))
        moved = 0
        for key, lst in groups.items():
            n, u, v, w, h = key; X = s.X[n]
            orig = X['idx'][v:v + h, u:u + w]
            shared = len(s.refs.get(key, ())) > 1
            variants = []
            for p, q in lst:
                for vq in variants:
                    if np.array_equal(vq[0], q): vq[1].append(p); break
                else: variants.append([q, [p]])
            for k, (q, ps) in enumerate(variants):
                if np.array_equal(q, orig): continue
                if k == 0 and not shared and len(variants) == 1:
                    X['idx'][v:v + h, u:u + w] = q; continue
                nu, nv = s._alloc(n, w, h); X['idx'][nv:nv + h, nu:nu + w] = q; moved += 1
                for p in ps: p['r']['uv'][p['i']] = [nu, nv]
        return moved

    def save(s):
        out = dict(s.ents)
        out[s.xn] = xcm.write_uv(s.c)
        for n, X in s.X.items(): out[n + '.xim'] = xim.build(X)
        return out
