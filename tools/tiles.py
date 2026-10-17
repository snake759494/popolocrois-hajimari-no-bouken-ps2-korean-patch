"""8×8 타일 스트림 유틸: XIM(폭 256) 을 타일 번호 순서(행 우선, 32타일/행)로 다룸"""
import numpy as np
def to_tiles(idx):
    H, W = idx.shape; th, tw = H // 8, W // 8
    return idx[:th * 8].reshape(th, 8, tw, 8).transpose(0, 2, 1, 3).reshape(th * tw, 8, 8)
def from_tiles(t, W):
    tw = W // 8; th = len(t) // tw
    return t.reshape(th, tw, 8, 8).transpose(0, 2, 1, 3).reshape(th * 8, W)
def layout(t, start, cols, rows):
    """타일 start 부터 cols×rows 를 이미지로"""
    out = np.zeros((rows * 8, cols * 8), t.dtype)
    for k in range(cols * rows):
        if start + k >= len(t): break
        r, c = divmod(k, cols); out[r*8:r*8+8, c*8:c*8+8] = t[start + k]
    return out

def to_strip(t, rows=2, cols=16):
    """타일 → 띠(높이 rows*8): 아틀라스 32타일 행 = (윗줄 cols, 아랫줄 cols …) 128px 조각"""
    per = rows * cols; n = len(t) // per
    segs = []
    for s in range(n):
        seg = np.zeros((rows * 8, cols * 8), t.dtype)
        for r in range(rows):
            for c in range(cols):
                seg[r*8:r*8+8, c*8:c*8+8] = t[s * per + r * cols + c]
        segs.append(seg)
    return np.hstack(segs) if segs else np.zeros((rows * 8, 0), t.dtype)

def from_strip(t, strip, rows=2, cols=16):
    per = rows * cols; t = t.copy()
    for s in range(strip.shape[1] // (cols * 8)):
        seg = strip[:, s * cols * 8:(s + 1) * cols * 8]
        for r in range(rows):
            for c in range(cols):
                t[s * per + r * cols + c] = seg[r*8:r*8+8, c*8:c*8+8]
    return t
