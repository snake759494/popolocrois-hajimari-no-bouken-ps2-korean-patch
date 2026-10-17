"""R5900 범위 디스어셈블.  python rdis.py <elf> <시작hex> <개수>"""
import sys, struct, os
sys.path.insert(0, os.path.dirname(__file__))
from mips import Elf
from r5900 import dis1
e = Elf(sys.argv[1]); a = int(sys.argv[2], 16); n = int(sys.argv[3])
for k in range(n):
    x = e.u32(a + 4*k); print('%08x: %08x  %s' % (a + 4*k, x, dis1(a + 4*k, x)))
