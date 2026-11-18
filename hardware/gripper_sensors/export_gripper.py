"""Eksport chwytaka SO-101 (serwo nadgarstka + szczęka stała + ruchoma) w układzie ciała 'gripper', mm, do Blendera.
Szuka też powierzchni styku szczęk przy zamknięciu = miejsce na FSR402."""
import json, sys, numpy as np, mujoco
OPEN = float(sys.argv[1]) if len(sys.argv) > 1 else 0.6   # kąt szczęki do pokazania [rad]
xml = open("assets/so101_upstream.xml").read().replace('meshdir="assets"', 'meshdir="assets/so101_meshes"')
m = mujoco.MjModel.from_xml_string(xml); d = mujoco.MjData(m)
g = m.body("gripper").id; jaw = m.body("moving_jaw_so101_v1").id
def mesh_world(geom):
    mid = m.geom_dataid[geom]; a, n = m.mesh_vertadr[mid], m.mesh_vertnum[mid]
    fa, fn = m.mesh_faceadr[mid], m.mesh_facenum[mid]
    v = m.mesh_vert[a:a+n] @ d.geom_xmat[geom].reshape(3, 3).T + d.geom_xpos[geom]
    R = d.xmat[g].reshape(3, 3); v = (v - d.xpos[g]) @ R         # do układu 'gripper'
    return v * 1000, m.mesh_face[fa:fa+fn]
def vis_geoms(body):
    return [i for i in range(m.ngeom) if m.geom_bodyid[i] == body and m.geom_group[i] != 3
            and m.geom_type[i] == mujoco.mjtGeom.mjGEOM_MESH and m.geom_contype[i] == 0]
def at(q):
    d.qpos[:] = 0; d.qpos[m.joint("gripper").qposadr[0]] = q; mujoco.mj_forward(m, d)
    out = {}
    for gi in vis_geoms(g) + vis_geoms(jaw):
        name = m.mesh(m.geom_dataid[gi]).name; out[name] = mesh_world(gi)
    return out
closed = at(m.jnt_range[m.joint("gripper").id][0])
fixed, mov = closed["wrist_roll_follower_so101_v1"][0], closed["moving_jaw_so101_v1"][0]
from scipy.spatial import cKDTree
df, _ = cKDTree(mov).query(fixed); dm, _ = cKDTree(fixed).query(mov)
print("closed: min gap mm", df.min().round(2), "| verts within 3mm: fixed", (df < 3).sum(), "moving", (dm < 3).sum())
shown = at(OPEN)
json.dump({k: {"v": v.round(3).tolist(), "f": f.tolist()} for k, (v, f) in shown.items()},
          open("hardware/gripper_sensors/gripper_mm.json", "w"))
np.savez("/private/tmp/claude-501/-Users-admin--claude-spares-spare-6ruLld/a732218e-04d0-4a1c-96f8-40b2ecac8050/scratchpad/closed.npz",
         fixed=fixed, mov=mov, df=df, dm=dm, movo=shown["moving_jaw_so101_v1"][0])
for k, (v, f) in shown.items(): print(k, len(v), "verts, bbox mm", v.min(0).round(1), v.max(0).round(1))

# --- miejsca na FSR402: największa płaska ściana szczęki zwrócona do drugiej szczęki ---
def tri(v, f):
    T = v[f]; n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); a = np.linalg.norm(n, axis=1) / 2
    return T, n / (2 * a[:, None] + 1e-12), a
def flat_face(v, f, want, back_mm, bin_mm=1.0):
    """want = przybliżona normalna (do drugiej szczęki). Zwraca środek czujnika back_mm od czubka ściany."""
    T, n, a = tri(v, f); c = T.mean(1)
    sel = (n @ want > 0.95) & (c[:, 2] < -45)
    key = np.round(c[sel] @ want / bin_mm, 0)                                     # grupuj po odległości płaszczyzny
    big = [k for k in np.unique(key) if a[sel][key == k].sum() >= 200]   # ściana ≥ 2 cm², a z nich
    best = max(big)                                                      # ta najbliżej drugiej szczęki (dotyka pierwsza)
    ids = np.where(sel)[0][np.abs(c[sel] @ want - best * bin_mm) <= bin_mm];   # ściana może wpaść w 2 sąsiednie przedziały
    nn = (n[ids] * a[ids, None]).sum(0); nn /= np.linalg.norm(nn)
    P = T[ids].reshape(-1, 3); ax = np.cross(nn, [0, 1, 0]); ax /= np.linalg.norm(ax)
    if ax[2] < 0: ax = -ax                                               # oś szczęki: ku nadgarstkowi (+z)
    tip = P[np.argmin(P @ ax)]; c0 = tip + ax * back_mm
    d_ = (T[ids] - c0) @ ax; pts = []                                    # przekrój ściany w miejscu czujnika
    for i, j in ((0, 1), (1, 2), (2, 0)):
        m_ = d_[:, i] * d_[:, j] < 0; t_ = d_[m_, i] / (d_[m_, i] - d_[m_, j])
        pts.append(T[ids][m_, i] + t_[:, None] * (T[ids][m_, j] - T[ids][m_, i]))
    near = np.vstack(pts); c0[1] = (near[:, 1].min() + near[:, 1].max()) / 2
    return c0, nn, ax, float(near[:, 1].max() - near[:, 1].min()), float((P @ ax).max() - (P @ ax).min())
fv, ff = shown["wrist_roll_follower_so101_v1"]; mv, mf = shown["moving_jaw_so101_v1"]
sens = {}
for name, (v, f, want, back, bin_) in {"FSR1_A0_szczeka_stala": (fv, ff, np.array([1.0, 0, 0]), 10.0, 1.0),   # schodki co ~1,7 mm
                                 "FSR2_A1_szczeka_ruchoma": (mv, mf, None, 22.0, 4.0)}.items():  # ruchoma: jedna lekko krzywa ściana
    if want is None:   # normalna ruchomej: z siatki, ściana zwrócona do szczęki stałej
        T, n, a = tri(v, f); c = T.mean(1); s_ = (c[:, 2] < -45) & (n[:, 0] < -0.5)
        want = (n[s_] * a[s_, None]).sum(0); want /= np.linalg.norm(want)
    c0, nn, ax, h, L = flat_face(v, f, want, back, bin_)
    sens[name] = [c0.tolist(), nn.tolist(), ax.tolist()]
    print(name, "środek", c0.round(1), "normalna", nn.round(2), "wysokość ściany %.1f mm, długość %.1f mm" % (h, L))
J = json.load(open("hardware/gripper_sensors/gripper_mm.json")); J["_sensors"] = sens
json.dump(J, open("hardware/gripper_sensors/gripper_mm.json", "w"))
