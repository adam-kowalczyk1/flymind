import sys; sys.path.insert(0,'/Users/admin/so101_fly_project/flymind')
import numpy as np, pandas as pd
import sensory_manipulation as sm
from leg_circuit import select
from visual_path import ANN
fc=sm.FlyCfg(trigger="search")
d=sm.LegJaw(fc,touch=True,proprio=True)
print("receptory FeCO w obwodzie:",{k:len(v) for k,v in d.feco.items()}, "| szczecinki", sum(map(len,d.pad_in)), "| MN zamykające/otwierające", len(d.press), len(d.release))
# adnotacje typów: co mówią dane o tych typach
a=pd.read_feather(ANN); cols=[c for c in a.columns if c in("type","subclass","synonyms","class","description","flywireType","modality")]
for k,t in sm.FECO.items():
    r=a[a.type==t]; print(k,t,"n w MaleCNS",len(r),{c:r[c].dropna().astype(str).value_counts().head(2).to_dict() for c in cols if c!="type"})
# bezpośrednie i 2-skokowe wejście znakowane do puli zamykającej (Ti extensor) i otwierającej (Ti flexor)
W=d.spec.toarray() if hasattr(d.spec,"toarray") else np.asarray(d.spec)
def infl(src):
    v=np.zeros(d.N); v[src]=1.0/len(src); h1=W@v; h2=W@np.maximum(h1,0)*0+W@h1
    return (h1[d.press].mean(),h1[d.release].mean(),h2[d.press].mean(),h2[d.release].mean())
print("wpływ znakowany [mV na jednostkę aktywności]: (1 skok→zamyk., 1 skok→otw., 2 skoki→zamyk., 2 skoki→otw.)")
for k,ix in list(d.feco.items())+[("bristle",list(d.pad_in[0])+list(d.pad_in[1]))]:
    print(f"  {k:10s}", np.round(infl(ix),3))
# odpowiedź dynamiczna: każdy kanał osobno, z dotykiem i bez
def run(q,qd,touch,only=None,n=120):
    d.reset(); orig=dict(d.feco)
    if only: d.feco={k:(v if k==only else []) for k,v in orig.items()}
    t=[d.step(np.array([touch,touch,0.0]),q,qd) for _ in range(n)]; d.feco=orig
    return round(float(np.mean(t[60:])),3)
print("moment szczęki [N·m] (+ = zamykanie), ustalony:")
print("  sam dotyk 0,5 N (bez FeCO):", sm.LegJaw(fc).__class__ and (lambda L:(L.reset(), round(float(np.mean([L.step(np.array([.5,.5,0]),0.5,0.0) for _ in range(120)][60:])),3))[1])(sm.LegJaw(fc)))
for name,q,qd in (("szczęka rozwarta q=1,6, bez ruchu",1.6,0.0),("szczęka środek q=0,8",0.8,0.0),("szczęka zamknięta q=0,0",0.0,0.0),("ruch zamykania qd=−0,5",0.8,-0.5),("ruch otwierania qd=+0,5",0.8,0.5)):
    print(f"  {name:36s} bez dotyku {run(q,qd,0.0):+.3f} | z dotykiem 0,5 N {run(q,qd,0.5):+.3f}")
