"""이미지 한글화 단계: 지도 14장, 통짜 이미지, 메뉴 스프라이트(XCM).  images(rd) → {ISO 경로: 새 bytes}"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import xpf, lz, img_maps, img_misc, img_xcm

def _xpf_patch(data, fn):
    """XPF 의 항목들을 해제해 fn(dict) 로 바꾼 뒤 바뀐 항목만 재압축"""
    x = xpf.parse(data)
    ents = {n: lz.decompress(d)[0] for n, d, _ in x['ents']}
    new = fn(ents)
    for e in x['ents']:
        if new[e[0]] != ents[e[0]]: e[1] = lz.compress(new[e[0]])
    return xpf.build(x)

def images(rd, log=print):
    out = {}
    # 지도
    m1 = None
    for k in range(1, 15):
        p = '/DATACMN/MENU/MAP/MAP%02d.XPF' % k
        def fn(ents, k=k):
            nonlocal m1
            nm = 'map_%02d.xim' % k
            if m1 is None: m1 = lz.decompress([e for e in xpf.parse(rd('/DATACMN/MENU/MAP/MAP01.XPF'))['ents'] if e[0] == 'map_01.xim'][0][1])[0]
            ents = dict(ents); ents[nm] = img_maps.patch(k, ents[nm], m1)[0]; return ents
        out[p] = _xpf_patch(rd(p), fn)
    # 통짜 이미지
    by = {}
    for path, mem in img_misc.KEYS: by.setdefault(path, []).append(mem)
    for path, mems in by.items():
        src = out.get(path) or rd(path)
        if mems == [None]:
            out[path] = img_misc.patch((path, None), src)
        else:
            def fn(ents, path=path, mems=mems):
                ents = dict(ents)
                for m in mems: ents[m] = img_misc.patch((path, m), ents[m])
                return ents
            out[path] = _xpf_patch(src, fn)
    # 메뉴 스프라이트
    for name in img_xcm.EDITS:
        path = '/DATACMN/MENU/%s/%s.XPF' % (name, name)
        out[path] = _xpf_patch(rd(path), lambda ents, name=name: img_xcm.patch(name, ents)[0])
    log('이미지 %d개 파일' % len(out))
    return out
