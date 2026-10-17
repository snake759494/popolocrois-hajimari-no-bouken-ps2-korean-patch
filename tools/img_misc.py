"""통짜 이미지(지도 외) 한글화 편집 명세.  키: (ISO 경로, XPF 항목명 또는 None)"""
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import imgpatch

W = (255, 255, 255); OUTD = (30, 25, 20)

def _cont(box):   # 「つづく…」 → 계속……
    return [dict(box=box, mode='dark', grow=3, text='계속……', color=(20, 20, 20), outline=None, maxsize=34)]

EDITS = {
    # 엔딩 메시지
    ('/DATACMN/LOGO_T03.XIM', None): [
        dict(box=(50, 76, 300, 104), text='이렇게……', color='auto', outline=OUTD, align='l', maxsize=19),
        dict(box=(50, 133, 480, 166), text='피논 왕자의 첫 모험은 막을 올렸습니다', color='auto', outline=OUTD, align='l', maxsize=19),
        dict(box=(50, 194, 480, 280), text='앞으로는 분명\n동료들과의 만남과 여러 가지 일들이\n기다리고 있겠지요', color='auto', outline=OUTD, align='l', maxsize=19, spacing=4),
        dict(box=(50, 309, 490, 341), text='첫 모험에서 피논 왕자는 무엇을 보게 될까――', color='auto', outline=OUTD, align='l', maxsize=19),
        dict(box=(50, 366, 300, 396), text='부디 기대해 주세요', color='auto', outline=OUTD, align='l', maxsize=19)],
    # 공식 사이트 안내
    ('/DATACMN/LOGO_T02.XIM', None): [
        dict(box=(30, 292, 485, 358), bg=(255, 255, 255), fill=True, text='『포포로크로이스 ~시작의 모험~』의\n최신 정보는 여기에서', color=(15, 15, 15), outline=None, maxsize=19, spacing=4)],
    ('/DATACMN/LOGO_T01.XIM', None): _cont((285, 370, 508, 432)),
    ('/DATACMN/TITLE/EX.XPF', 'ex_c01.xim'): _cont((285, 370, 508, 432)),
    ('/DATACMN/TITLE/EX.XPF', 'ex_c02.xim'): _cont((285, 370, 508, 432)),
    # 튜토리얼 창
    ('/DATACMN/USEFIRE.XIM', None): [
        dict(box=(70, 308, 466, 337), mode='light', text='불의 정령님 힘도 쓸 수 있게 됐어', color='auto', outline=(20, 12, 8), align='l', maxsize=18),
        dict(box=(150, 337, 300, 359), mode='light', text='버튼으로', color='auto', outline=(20, 12, 8), align='l', maxsize=18),
        dict(box=(70, 359, 420, 385), mode='light', text='정령님을 바꿀 수 있어', color='auto', outline=(20, 12, 8), align='l', maxsize=18)],
    ('/DATACMN/USEWIND.XIM', None): [
        dict(box=(78, 308, 450, 337), mode='light', text='바람의 정령님이 도와준대', color='auto', outline=(20, 12, 8), align='l', maxsize=18),
        dict(box=(120, 337, 430, 359), mode='light', text='버튼으로 정령님 힘을 쓸 수 있어', color='auto', outline=(20, 12, 8), align='l', maxsize=18),
        dict(box=(78, 359, 420, 385), mode='light', text='수상한 곳에서 써 보자', color='auto', outline=(20, 12, 8), align='l', maxsize=18)],
    # 타이틀 로고 부제
    ('/DATACMN/MENU/XIM/XIM.XPF', 'title_logo.xim'): [
        dict(box=(62, 108, 242, 145), mode='white', grow=2, text='시작의 모험', color=(255, 255, 255), outline=(80, 30, 110), maxsize=20)],
}
DEV = '이 소프트웨어는 현재 개발 중이라 정상적으로\n작동하지 않는 등 예기치 못한 문제가\n발견될 수 있습니다.\n만일 오작동이 생기더라도 디스크\n교환은 불가하오니 양해 바랍니다.'
for k in (('/DATACMN/TITLE/EX.XPF', 'ex_02.xim'), ('/DATACMN/TITLE/LOGO.XPF', 'logoex2.xim')):
    EDITS[k] = [dict(box=(20, 100, 505, 330), bg='clear', text=DEV, color=(170, 230, 40), outline=(20, 60, 10), maxsize=19, spacing=10)]

# 전투 상태 라벨(투명 아틀라스, 단어 위치 고정)
CLEAR = {('/DATACMN/EFFECT/CMNEFF.XPF', 'eff-num-font.xim'): [
    dict(box=(2, 1, 103, 23), text='크리티컬'), dict(box=(105, 1, 144, 23), text='수면'), dict(box=(146, 1, 191, 23), text='마비'),
    dict(box=(194, 1, 239, 23), text='혼란'),
    dict(box=(1, 25, 95, 47), text='공격력UP'), dict(box=(97, 25, 223, 47), text='공격력DOWN'), dict(box=(225, 25, 248, 47), text='독'),
    dict(box=(2, 49, 96, 71), text='방어력UP'), dict(box=(97, 49, 223, 71), text='방어력DOWN'),
    dict(box=(2, 73, 96, 95), text='민첩UP'), dict(box=(97, 73, 223, 95), text='민첩DOWN')]}

def patch(key, data):
    if key in CLEAR:
        return imgpatch.apply_clear(data, [dict(e, outline=(20, 15, 40), ow=2) for e in CLEAR[key]])
    eds = []
    import xim
    rgb = xim.rgba(xim.parse(data))[..., :3]
    for e in EDITS[key]:
        if e.get('bg') == 'sample':
            x0, y0 = e['box'][:2]; e = dict(e, bg=tuple(int(v) for v in rgb[y0 - 5, x0 - 5]))
        eds.append(e)
    return imgpatch.apply(data, eds)[0]

KEYS = list(EDITS) + list(CLEAR)
