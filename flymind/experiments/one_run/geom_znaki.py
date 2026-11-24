import sys; sys.dont_write_bytecode=True
sys.path.insert(0,'.')
import one_run as O, numpy as np, mujoco
cam=O.Cam(); m=cam.m; k=cam.k
print([m.joint(i).name for i in range(m.njnt)][:8],'zakresy',m.jnt_range[:6].round(3).tolist())
print([m.site(i).name for i in range(m.nsite)]); print([m.body(i).name for i in range(m.nbody)])
for i in range(6):
    j=i; print(m.joint(j).name,'oś świat',k.xaxis[j].round(3),'kotwica',k.xanchor[j].round(3))
home=cam.home
def pose(q):
    k.qpos[:]=cam.sim.d.qpos; k.qpos[cam.sim.qadr]=q; mujoco.mj_forward(m,k)
    return k.site('cs_fixed').xpos.copy(), k.cam_xpos[cam.cid].copy(), -k.cam_xmat[cam.cid].reshape(3,3)[:,2].copy()
p0,e0,f0=pose(home); print('home grip',p0.round(4),'kam',e0.round(4),'osk kamery',f0.round(3))
R0=k.cam_xmat[cam.cid].reshape(3,3).copy(); print('kamera prawo',R0[:,0].round(3),'góra',R0[:,1].round(3))
for j in (0,1,2,3):
    for s in (.05,-.05):
        q=home.copy(); q[j]+=s; p,e,f=pose(q); print('staw',j,'dq',s,'Δchwytak mm',((p-p0)*1e3).round(2),'Δkam mm',((e-e0)*1e3).round(2), 'promień',round(float(np.hypot(*p[:2])),4))
