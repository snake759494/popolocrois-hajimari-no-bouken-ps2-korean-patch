"""지도 14장(MENU/MAP/MAPnn.XPF:map_nn.xim) 한글화 편집 생성"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import xim, imgpatch
NAMES = ['포포로크로이스 성', '포포로크로이스 성 아랫마을', '포포로크로이스 평원', '해안', '타키넨 계곡', '타키넨 마을', '플로네르 숲',
         '용의 사당', '바람의 성역', '화염의 성역', '빙해', '물의 성역', '어둠의 성 아랫마을', '어둠의 성역']
LABELS = [((300, 82, 415, 112), '타키넨 마을'), ((25, 122, 195, 152), '포포로크로이스 성'), ((340, 205, 508, 238), '플로네르 숲')]
_ref = {}
def refmasks(map01):
    if not _ref:
        rgb = np.ascontiguousarray(xim.rgba(xim.parse(map01))[..., :3])
        for box, _ in LABELS: _ref[box] = imgpatch.text_mask(rgb, box, 'white')
    return _ref
def patch(k, data, map01):
    rm = refmasks(map01)
    rgb = xim.rgba(xim.parse(data))[..., :3]
    dark = rgb.mean() / xim.rgba(xim.parse(map01))[..., :3].mean()
    OUT = tuple(int(v) for v in (np.array([70, 45, 25]) * dark).clip(0, 255))
    ed = [dict(box=b, refmask=rm[b], text=t, color='auto', outline=OUT, maxsize=19) for b, t in LABELS]
    ed += [dict(box=(118, 378, 184, 400), mode='gold', grow=2, text='현재지', color='auto', outline=(50, 30, 10), maxsize=16),
           dict(box=(195, 377, 410, 401), text=NAMES[k - 1], color='auto', outline=OUT, maxsize=17)]
    return imgpatch.apply(data, ed)
