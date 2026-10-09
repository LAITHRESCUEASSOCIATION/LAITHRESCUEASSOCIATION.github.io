import numpy as np, soundfile as sf, sys
SR=44100; T=60.0; N=int(SR*T); t=np.arange(N)/SR
rng=np.random.default_rng(7)
L=np.zeros(N); R=np.zeros(N)
def env(n,a,r):  # attack/release (samples)
    e=np.ones(n); a=min(a,n); r=min(r,n)
    e[:a]=np.linspace(0,1,a); e[n-r:]*=np.linspace(1,0,r); return e
def add(sig,start,pan=0.0,g=1.0):
    i=int(start*SR); j=min(N,i+len(sig)); s=sig[:j-i]*g
    L[i:j]+=s*np.sqrt((1-pan)/2); R[i:j]+=s*np.sqrt((1+pan)/2)
def hz(m): return 440*2**((m-69)/12)
def lp(x,a):  # one-pole lowpass
    y=np.empty_like(x); acc=0.0; a=np.broadcast_to(a,x.shape)
    for k in range(len(x)): acc+=a[k]*(x[k]-acc); y[k]=acc
    return y
# --- pad: D drone + hijaz-coloured chords, slow swells
chords=[(0,[50,57,62,66]),(7,[50,57,62,65]),(16,[48,55,60,63]),(25,[46,53,58,62]),(33.3,[50,57,62,66]),(44.3,[51,58,63,67]),(52,[50,57,62,66,69])]
ends=[c[0] for c in chords[1:]]+[T]
for (st,notes),en in zip(chords,ends):
    d=en-st+1.5; n=int(d*SR); tt=np.arange(n)/SR
    s=np.zeros(n)
    for m in notes:
        f=hz(m)
        for det in (-0.12,0.0,0.12):
            s+=np.sin(2*np.pi*f*(1+det/100)*tt+rng.uniform(0,6))*0.5+0.18*np.sin(2*np.pi*2*f*tt)
    s*=env(n,int(1.2*SR),int(1.5*SR))*(1+0.15*np.sin(2*np.pi*0.2*tt))
    add(s/len(notes)*0.10,st,pan=rng.uniform(-.3,.3))
# --- sub drone
add(np.sin(2*np.pi*hz(38)*t)*0.06*np.clip(t/4,0,1)*np.clip((T-t)/3,0,1),0)
# --- frame drum (daf) dum / tak
def dum():
    n=int(0.45*SR); tt=np.arange(n)/SR; f=95*np.exp(-tt*6)+55
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*9)
def tak():
    n=int(0.12*SR); tt=np.arange(n)/SR; nz=rng.standard_normal(n)
    nz=nz-lp(nz,0.25)
    return (nz*0.5+np.sin(2*np.pi*420*tt)*0.4)*np.exp(-tt*45)
D,K=dum(),tak()
bpm=96; beat=60/bpm
# maqsum-like pattern in 8th notes: D T . T D . T .
pat=[('D',0),('T',0.5),('T',1.5),('D',2),('T',3)]
def intensity(x):
    if x<7: return 0
    if x<33.3: return 0.55
    if x<52: return 0.9
    return 0.0
b=7.0
while b<52:
    g=intensity(b)
    for k,off in pat:
        tm=b+off*beat
        if tm>=52: break
        add(D if k=='D' else K, tm, pan=(0 if k=='D' else 0.25), g=(0.55 if k=='D' else 0.22)*g)
    if b>=33.3:  # extra ghost taks
        for off in (2.5,3.5): add(K,b+off*beat,pan=-0.3,g=0.10)
    b+=4*beat
# --- oud-like plucks (Karplus-Strong) hijaz motif
def pluck(f,d=1.6):
    n=int(d*SR); p=int(SR/f); buf=rng.uniform(-1,1,p); out=np.empty(n)
    for k in range(n):
        out[k]=buf[k%p]; buf[k%p]=0.996*0.5*(buf[k%p]+buf[(k+1)%p])
    return out*np.exp(-np.arange(n)/SR*1.5)
scale=[62,63,66,67,69,70,72,74]  # D Eb F# G A Bb C D
motifs=[[0,1,2,1,0],[4,5,4,2,3,2,1,0],[2,3,4,5,6,5,4],[7,6,5,4,3,2,1,0]]
cache={}
def P(m):
    if m not in cache: cache[m]=pluck(hz(m))
    return cache[m]
for st,mi,step in [(1.0,0,0.55),(9.5,1,0.42),(18.5,2,0.42),(27,3,0.38),(36,1,0.36),(40,2,0.36),(46,3,0.36),(54,0,0.6)]:
    for i,deg in enumerate(motifs[mi]):
        add(P(scale[deg]),st+i*step,pan=-0.2,g=0.16)
# --- risers & impacts on transitions
for x in [7,16,25,33.3,44.3,52]:
    n=int(1.6*SR); tt=np.arange(n)/SR; nz=rng.standard_normal(n)
    sw=lp(nz,0.02+0.25*(tt/1.6)**2)*(tt/1.6)**2*0.25
    add(sw,x-1.6,pan=0)
    imp=dum()*1.0; add(imp,x,g=0.45 if x!=52 else 0.8)
# --- final shimmer
n=int(7*SR); tt=np.arange(n)/SR
sh=sum(np.sin(2*np.pi*hz(m)*tt) for m in (74,78,81,86))*np.exp(-tt*0.5)*0.025
add(sh,52.2)
mix=np.stack([L,R],1)
fade=np.clip((T-t)/2.5,0,1)[:,None]*np.clip(t/0.3,0,1)[:,None]
mix*=fade
mix/=np.abs(mix).max()/0.89
sf.write(sys.argv[1],mix.astype(np.float32),SR)
print('ok')
