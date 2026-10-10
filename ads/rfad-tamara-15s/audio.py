# Synthesizes the 15s sound bed (pad + pulse + whooshes + chimes) -> build/audio.wav
import numpy as np, wave
SR=48000; D=15.0; n=int(SR*D); t=np.arange(n)/SR
out=np.zeros((n,2))
def env(a,d,length):
    e=np.ones(length); a=int(a*SR); d=int(d*SR)
    e[:a]=np.linspace(0,1,a); e[-d:]*=np.linspace(1,0,d); return e
def add(sig,start,gain=1.0,pan=0.0):
    i=int(start*SR); j=min(n,i+len(sig)); s=sig[:j-i]*gain
    out[i:j,0]+=s*(1-max(pan,0))
    out[i:j,1]+=s*(1+min(pan,0))
f=lambda m:440*2**((m-69)/12)
# pad: two chords, crossfade at 6s and 10s
chords=[(0,6.3,[45,52,57,60,64]),(6,10.3,[41,48,53,57,64]),(10,15,[43,50,55,59,62]),(13,15,[45,52,57,61,64])]
for a,b,notes in chords:
    L=int((b-a)*SR); tt=np.arange(L)/SR; s=np.zeros(L)
    for k,m in enumerate(notes):
        fr=f(m); s+=np.sin(2*np.pi*fr*tt+k)*(1+.3*np.sin(2*np.pi*.2*tt+k))/(1+k*.4)
        s+=.25*np.sin(2*np.pi*fr*2.003*tt)/(1+k)
    add(s*env(.8,.6,L),a,0.035,pan=0.0)
# soft pulse (sub thump) at 100bpm from 1.3s
for bt in np.arange(1.3,14.4,0.6):
    L=int(.35*SR); tt=np.arange(L)/SR
    s=np.sin(2*np.pi*(55+60*np.exp(-tt*30))*tt)*np.exp(-tt*9)
    add(s,bt,0.22)
# whooshes
rng=np.random.default_rng(3)
def whoosh(dur=.7):
    L=int(dur*SR); w=rng.standard_normal(L); tt=np.linspace(0,1,L)
    # moving one-pole lowpass
    y=np.zeros(L); a=0
    cut=.02+.25*np.sin(np.pi*tt)**2
    for i in range(L): a+= cut[i]*(w[i]-a); y[i]=a
    return y*np.sin(np.pi*tt)**2
for st in [0.15,2.7,5.55,9.9,12.8]:
    add(whoosh(),st,0.5,pan=0.3); add(whoosh(),st+.02,0.5,pan=-0.3)
# count-up ticks
for a,b in [(1.3,2.2),(3.75,4.6)]:
    for k,tk in enumerate(np.linspace(a,b,10)):
        L=int(.04*SR); tt=np.arange(L)/SR
        add(np.sin(2*np.pi*(2200+k*80)*tt)*np.exp(-tt*120),tk,0.06)
# chimes
def bell(base,dur=2.2):
    L=int(dur*SR); tt=np.arange(L)/SR; s=np.zeros(L)
    for r,g,dec in [(1,1,3),(2.0,.5,4),(2.76,.35,5),(4.07,.2,7),(5.4,.12,9)]:
        s+=g*np.sin(2*np.pi*base*r*tt)*np.exp(-tt*dec)
    return s*np.minimum(1,tt*400)
add(bell(f(81)),11.2,0.09,pan=.2); add(bell(f(88)),11.28,0.06,pan=-.2)
add(bell(f(76)),2.25,0.05)
add(bell(f(81)),13.6,0.08); add(bell(f(85)),13.68,0.06,pan=.3); add(bell(f(88)),13.76,0.06,pan=-.3)
# master fade + normalize
fo=int(.6*SR); out[-fo:]*=np.linspace(1,0,fo)[:,None]
out/=np.max(np.abs(out))/0.85
with wave.open('build/audio.wav','wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out*32767).astype('<i2').tobytes())
print('ok')
