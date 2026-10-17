"""PCSX2 백그라운드 제어: 시작/키 입력(PostMessage)/화면 캡처(PrintWindow)/PINE 메모리 읽기"""
import ctypes,ctypes.wintypes as W,subprocess,socket,struct,time,os,sys
PCSX2=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'work','emu','pcsx2-qt.exe')
HERE=os.path.dirname(os.path.abspath(__file__));PIDF=os.path.join(os.path.dirname(HERE),"work","emu.pid")
u32=ctypes.windll.user32;g32=ctypes.windll.gdi32
VK=dict(up=0x26,down=0x28,left=0x25,right=0x27,x=0x4B,o=0x4C,tri=0x49,sq=0x4A,start=0x0D,select=0x08,l1=0x51,r1=0x45,l2=0x31,r2=0x33,
        lu=0x57,ld=0x53,ll=0x41,lr=0x44,f12=0x7B,tab=0x09)
def start(iso):
    si=subprocess.STARTUPINFO();si.dwFlags=1;si.wShowWindow=4   # SW_SHOWNOACTIVATE
    p=subprocess.Popen([PCSX2,'-batch','-nogui','--',os.path.abspath(iso)],cwd=os.path.dirname(PCSX2),startupinfo=si)
    open(PIDF,'w').write(str(p.pid))
    for _ in range(100):
        time.sleep(0.2)
        try:
            h=main_hwnd()
            if h:
                time.sleep(0.5);u32.SetWindowPos(h,1,0,0,0,0,0x13)   # HWND_BOTTOM, NOSIZE|NOMOVE|NOACTIVATE
                break
        except Exception: pass
    return p.pid
def stop():
    if os.path.exists(PIDF):
        subprocess.run(['taskkill','/F','/PID',open(PIDF).read().strip()],capture_output=True);os.remove(PIDF)
def hwnds():
    pid=int(open(PIDF).read());res=[]
    @ctypes.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
    def cb(h,l):
        p=W.DWORD();u32.GetWindowThreadProcessId(h,ctypes.byref(p))
        if p.value==pid and u32.IsWindowVisible(h):
            b=ctypes.create_unicode_buffer(256);u32.GetWindowTextW(h,b,256);res.append((h,b.value))
        return True
    u32.EnumWindows(cb,0);return res
def main_hwnd():
    best=None;ba=0
    for h,t in hwnds():
        r=W.RECT();u32.GetWindowRect(h,ctypes.byref(r));a=(r.right-r.left)*(r.bottom-r.top)
        if a>ba: best,ba=h,a
    return best
def children(h):
    res=[]
    @ctypes.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
    def cb(c,l): res.append(c);return True
    u32.EnumChildWindows(h,cb,0);return res
def post(key,ms=120,h=None):
    h=h or main_hwnd();vk=VK.get(key,key) if isinstance(key,str) else key
    sc=u32.MapVirtualKeyW(vk,0);ext=1<<24 if vk in(0x25,0x26,0x27,0x28) else 0
    targets=[h]+children(h)
    for t in targets: u32.PostMessageW(t,0x100,vk,1|(sc<<16)|ext)
    time.sleep(ms/1000)
    for t in targets: u32.PostMessageW(t,0x101,vk,1|(sc<<16)|ext|0xC0000000)
    time.sleep(0.05)
def shot(path,h=None):
    from PIL import Image
    h=h or main_hwnd();r=W.RECT();u32.GetWindowRect(h,ctypes.byref(r));w,hh=r.right-r.left,r.bottom-r.top
    hdc=u32.GetDC(h);mdc=g32.CreateCompatibleDC(hdc);bmp=g32.CreateCompatibleBitmap(hdc,w,hh);g32.SelectObject(mdc,bmp)
    u32.PrintWindow(h,mdc,3)
    class BIH(ctypes.Structure):_fields_=[('a',W.DWORD),('w',W.LONG),('h',W.LONG),('p',W.WORD),('b',W.WORD),('c',W.DWORD),('s',W.DWORD),('x',W.LONG),('y',W.LONG),('u',W.DWORD),('i',W.DWORD)]
    bi=BIH(40,w,-hh,1,32,0,0,0,0,0,0);buf=ctypes.create_string_buffer(w*hh*4)
    g32.GetDIBits(mdc,bmp,0,hh,buf,ctypes.byref(bi),0)
    g32.DeleteObject(bmp);g32.DeleteDC(mdc);u32.ReleaseDC(h,hdc)
    im=Image.frombuffer('RGBA',(w,hh),buf,'raw','BGRA',0,1).convert('RGB');im.save(path);return im
class Pine:
    def __init__(s,port=28241):
        s.s=socket.create_connection(('127.0.0.1',port));s.s.settimeout(20)
    def _cmd(s,payload,nret):
        s.s.sendall(struct.pack('<I',len(payload)+4)+payload)
        hdr=s._recv(4);n=struct.unpack('<I',hdr)[0];d=s._recv(n-4)
        if d[0]!=0: raise RuntimeError('pine fail')
        return d[1:]
    def _recv(s,n):
        b=b''
        while len(b)<n:
            c=s.s.recv(n-len(b))
            if not c: raise EOFError
            b+=c
        return b
    def read(s,addr,size):
        out=bytearray()
        for base in range(addr,addr+size,8*4096):
            cnt=min(4096,(addr+size-base+7)//8)
            pl=b''.join(struct.pack('<BI',3,base+i*8) for i in range(cnt))
            out+=s._cmd(pl,cnt*8)
        return bytes(out[:size])
    def write(s,addr,data):
        for i in range(0,len(data),4096):
            ch=data[i:i+4096];pl=b''.join(struct.pack('<BIB',4,addr+i+j,ch[j]) for j in range(len(ch)));s._cmd(pl,0)
    def status(s): return s._cmd(b'\x0f',4)
    def title(s): return s._cmd(b'\x0b',0)
if __name__=='__main__':
    c=sys.argv[1]
    if c=='start': print(start(sys.argv[2]))
    elif c=='stop': stop()
    elif c=='shot': shot(sys.argv[2]);print('ok')
    elif c=='key':
        for k in sys.argv[2:]: post(k);time.sleep(0.3)
    elif c=='dump':
        p=Pine();open(sys.argv[2],'wb').write(p.read(0,32*1024*1024));print('dumped')
def savestate(slot):
    p=Pine();p._cmd(bytes([9,slot]),0)
def loadstate(slot):
    p=Pine();p._cmd(bytes([10,slot]),0)
def seq(keys,shotpath=None,wait=1.0):
    for k in keys.split():
        if k.startswith('w'): time.sleep(float(k[1:]));continue
        post(k);time.sleep(wait)
    if shotpath: shot(shotpath)
def combo(mods,key,ms=150):
    """mods: VK 리스트(예 [0x11,0x10]), key: VK"""
    h=main_hwnd();ts=[h]+children(h)
    for m in mods:
        for t in ts: u32.PostMessageW(t,0x100,m,1|(u32.MapVirtualKeyW(m,0)<<16))
    for t in ts: u32.PostMessageW(t,0x100,key,1|(u32.MapVirtualKeyW(key,0)<<16))
    time.sleep(ms/1000)
    for t in ts: u32.PostMessageW(t,0x101,key,1|(u32.MapVirtualKeyW(key,0)<<16)|0xC0000000)
    for m in mods[::-1]:
        for t in ts: u32.PostMessageW(t,0x101,m,1|(u32.MapVirtualKeyW(m,0)<<16)|0xC0000000)
SST=os.path.join(os.path.dirname(HERE),'work','emu','sstates')
def _member(p,name):
    import zipfile
    with zipfile.ZipFile(p) as z: i=z.getinfo(name)
    with open(p,'rb') as f:
        f.seek(i.header_offset);h=f.read(30);n,e=struct.unpack_from('<HH',h,26);f.seek(n+e,1);raw=f.read(i.compress_size)
    if i.compress_type==0: return raw
    if i.compress_type==93:
        from backports import zstd
        return zstd.decompress(raw)
    with zipfile.ZipFile(p) as z: return z.read(name)
def _latest():
    import glob
    best=None;bt=-1
    for q in glob.glob(os.path.join(SST,'*.p2s')):
        try: t=os.path.getmtime(q)
        except OSError: continue
        if t>bt: best,bt=q,t
    return best
def snap(out,ram=None,slot=9):
    """상태 저장(PINE) → Screenshot.png(+eeMemory) 추출"""
    old=_latest()
    try: t=os.path.getmtime(old) if old else 0
    except OSError: t=0
    Pine()._cmd(bytes([9,slot]),0)
    for _ in range(300):
        p=_latest()
        try:
            if p and os.path.getmtime(p)>t: time.sleep(1.0);break
        except OSError: pass
        time.sleep(0.1)
    open(out,'wb').write(_member(p,'Screenshot.png'))
    if ram: open(ram,'wb').write(_member(p,'eeMemory.bin'))
    return p
if __name__=='__main__' and sys.argv[1]=='snap':
    snap(sys.argv[2],sys.argv[3] if len(sys.argv)>3 else None);print('ok')
if __name__=='__main__' and sys.argv[1]=='seq':
    seq(' '.join(sys.argv[2:]))
