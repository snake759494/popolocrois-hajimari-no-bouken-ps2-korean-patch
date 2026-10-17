"""한글판을 부팅해 첫 필드(피논 방)까지 진행 → 슬롯1 저장, 흔들목마 조사 화면 캡처"""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__)); import emu
iso = sys.argv[1] if len(sys.argv) > 1 else 'PoPoLoCrois - Hajimari no Bouken (Korean).iso'
emu.stop(); time.sleep(1); emu.start(iso); time.sleep(22)
emu.post('start'); time.sleep(4); emu.post('start'); time.sleep(4)
for _ in range(3): emu.post('o'); time.sleep(3)
time.sleep(10)
for _ in range(150): emu.post('o'); time.sleep(2.5)
emu.savestate(1); time.sleep(2)
for d, ms in [('left', 1500), ('left', 400)]: emu.post(d, ms); time.sleep(0.4)
time.sleep(0.5); emu.post('o', 200); time.sleep(3)
emu.snap('work/field.png')
