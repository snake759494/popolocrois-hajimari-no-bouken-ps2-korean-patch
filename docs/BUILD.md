# 재빌드

준비물: Python 3.11+ (numpy, Pillow, opencv-python, capstone), 원본 ISO, `NanumSquareNeo-dEb.ttf`, 번역 자료(`translation/pp3v.json`, `translation/ejt.json`, `translation/elf.json` — 저장소 미포함), xdelta3.

```
작업폴더/
  PoPoLoCrois - Hajimari no Bouken (Japan).iso
  NanumSquareNeo-dEb.ttf
  tools/          (이 저장소의 tools)
  translation/    pp3v.json · ejt.json · elf.json  (항목: id, jp, ko)
```

```powershell
python tools\extract.py      # 원본에서 번역 대상 추출 → translation\*.json (기존 ko 는 보존)
python tools\tcheck.py translation\pp3v.json translation\ejt.json translation\elf.json   # 줄 폭·바이트·제어 코드 검사
python tools\reflow.py       # 필드 대사 줄 재배치(한 줄 17칸·3줄·106바이트)
python tools\build.py        # -> PoPoLoCrois - Hajimari no Bouken (Korean).iso
xdelta3 -e -0 -S none -A -s "PoPoLoCrois - Hajimari no Bouken (Japan).iso" "PoPoLoCrois - Hajimari no Bouken (Korean).iso" PoPoLoCrois_Hajimari_KO_v1.0.xdelta
```

- `build.py`: 번역 로드 → 한글 음절을 SJIS 한자 코드에 배정 → PP3V 스크립트(라벨표 재계산)·EJT 자막(XPF 안 사본은 LZ 재압축)·ELF 문자열 → 글꼴 10종 재생성 → 그림 글자(`build_img.py`) → ISO 기록(커진 파일은 ISO 끝으로 옮기고 디렉터리 레코드 갱신).
- `tools/emu.py`: PCSX2 백그라운드 실행·PostMessage 키 입력·세이브스테이트 스크린샷 보조(자기 PID 만 다룸).
- xdelta 는 크기보다 생성 속도를 우선해 압축 없이(`-0`) 만듭니다.
