"""ISO9660 파일 교체: 원래 섹터에 들어가면 제자리, 아니면 ISO 끝에 덧붙이고 디렉터리 레코드 갱신."""
import os, struct, shutil, sys
sys.path.insert(0, os.path.dirname(__file__))
import iso

def patch(src, dst, files, log=print):
    """files: {'/DIR/NAME': bytes}"""
    if os.path.abspath(src) != os.path.abspath(dst):
        shutil.copyfile(src, dst)
    f = open(dst, 'r+b')
    ents = {e['name']: e for e in iso.walk(f)}
    f.seek(0, 2); end = f.tell(); end_lba = (end + 2047) // 2048
    moved = 0
    for name, data in sorted(files.items()):
        e = ents[name]
        cap = (e['size'] + 2047) // 2048 * 2048
        if len(data) <= cap:
            lba = e['lba']
            f.seek(lba * 2048); f.write(data + bytes(cap - len(data)))
        else:
            lba = end_lba; n = (len(data) + 2047) // 2048
            f.seek(lba * 2048); f.write(data + bytes(n * 2048 - len(data)))
            end_lba += n; moved += 1
        # 디렉터리 레코드: +2 LBA(LE,BE), +10 크기(LE,BE)
        f.seek(e['rec'] + 2); f.write(struct.pack('<I', lba) + struct.pack('>I', lba) + struct.pack('<I', len(data)) + struct.pack('>I', len(data)))
    # PVD 볼륨 크기
    f.seek(0, 2); total = (f.tell() + 2047) // 2048
    if f.tell() % 2048: f.write(bytes(total * 2048 - f.tell()))
    f.seek(16 * 2048 + 80); f.write(struct.pack('<I', total) + struct.pack('>I', total))
    f.close()
    log('ISO 패치: %d개 파일, %d개 재배치, %d 섹터' % (len(files), moved, total))
