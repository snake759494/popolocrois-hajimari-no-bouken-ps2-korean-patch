"""간이 R5900 디스어셈블러(분석용 주요 명령만)"""
RN = 'zero at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra'.split()
def s16(x): return x - 0x10000 if x & 0x8000 else x
I = {8:'addi',9:'addiu',10:'slti',11:'sltiu',12:'andi',13:'ori',14:'xori',0x18:'daddi',0x19:'daddiu'}
M = {0x20:'lb',0x21:'lh',0x23:'lw',0x24:'lbu',0x25:'lhu',0x27:'lwu',0x28:'sb',0x29:'sh',0x2b:'sw',0x37:'ld',0x3f:'sd',0x1e:'lq',0x1f:'sq',0x31:'lwc1',0x39:'swc1',0x22:'lwl',0x26:'lwr',0x2a:'swl',0x2e:'swr',0x1a:'ldl',0x1b:'ldr',0x2c:'sdl',0x2d:'sdr'}
R = {0x21:'addu',0x23:'subu',0x24:'and',0x25:'or',0x26:'xor',0x27:'nor',0x2a:'slt',0x2b:'sltu',0x2d:'daddu',0x2f:'dsubu',0x0a:'movz',0x0b:'movn',0x20:'add',0x22:'sub',0x14:'dsllv',0x16:'dsrlv',0x17:'dsrav',0x04:'sllv',0x06:'srlv',0x07:'srav'}
SH = {0:'sll',2:'srl',3:'sra',0x38:'dsll',0x3a:'dsrl',0x3b:'dsra',0x3c:'dsll32',0x3e:'dsrl32',0x3f:'dsra32'}
def dis1(a, x):
    op = x >> 26; rs = (x >> 21) & 31; rt = (x >> 16) & 31; rd = (x >> 11) & 31; sa = (x >> 6) & 31; fn = x & 63; imm = x & 0xffff
    br = lambda: hex(a + 4 + s16(imm) * 4)
    if x == 0: return 'nop'
    if op == 0:
        if fn in SH: return '%s %s,%s,%d' % (SH[fn], RN[rd], RN[rt], sa)
        if fn == 8: return 'jr %s' % RN[rs]
        if fn == 9: return 'jalr %s,%s' % (RN[rd], RN[rs])
        if fn == 0x2d and rt == 0: return 'move %s,%s' % (RN[rd], RN[rs])
        if fn in R: return '%s %s,%s,%s' % (R[fn], RN[rd], RN[rs], RN[rt])
        if fn == 0x18: return 'mult %s,%s,%s' % (RN[rd], RN[rs], RN[rt])
        if fn == 0x19: return 'multu %s,%s,%s' % (RN[rd], RN[rs], RN[rt])
        if fn == 0x1a: return 'div %s,%s' % (RN[rs], RN[rt])
        if fn == 0x1b: return 'divu %s,%s' % (RN[rs], RN[rt])
        if fn == 0x10: return 'mfhi %s' % RN[rd]
        if fn == 0x12: return 'mflo %s' % RN[rd]
        if fn == 0xc: return 'syscall'
        if fn == 0xf: return 'sync'
        return 'special.%x' % fn
    if op == 1: return '%s %s,%s' % ({0:'bltz',1:'bgez',2:'bltzl',3:'bgezl',0x11:'bgezal',0x10:'bltzal'}.get(rt, 'regimm%d' % rt), RN[rs], br())
    if op == 2: return 'j %x' % ((a & 0xf0000000) | ((x & 0x3ffffff) << 2))
    if op == 3: return 'jal %x' % ((a & 0xf0000000) | ((x & 0x3ffffff) << 2))
    if op in (4, 5, 0x14, 0x15):
        n = {4:'beq',5:'bne',0x14:'beql',0x15:'bnel'}[op]
        if rt == 0 and op in (4, 5): return '%s %s,%s' % ('beqz' if op == 4 else 'bnez', RN[rs], br())
        return '%s %s,%s,%s' % (n, RN[rs], RN[rt], br())
    if op in (6, 7, 0x16, 0x17): return '%s %s,%s' % ({6:'blez',7:'bgtz',0x16:'blezl',0x17:'bgtzl'}[op], RN[rs], br())
    if op == 0xf: return 'lui %s,0x%x' % (RN[rt], imm)
    if op in I: return '%s %s,%s,%s' % (I[op], RN[rt], RN[rs], s16(imm) if op in (8,9,10,11,0x18,0x19) else hex(imm))
    if op in M: return '%s %s,%d(%s)' % (M[op], ('f%d' % rt) if op in (0x31, 0x39) else RN[rt], s16(imm), RN[rs])
    if op == 0x11:
        return 'cop1 %08x' % x
    if op == 0x1c:
        if fn == 0x18: return 'mult1 ...'
        if fn == 0x28 and sa == 0x18 and rt == 0: return 'pmove %s,%s' % (RN[rd], RN[rs])
        if fn == 0x29 and sa == 0x12: return 'por %s,%s,%s' % (RN[rd], RN[rs], RN[rt])
        return 'mmi %08x' % x
    return '.word %08x' % x
