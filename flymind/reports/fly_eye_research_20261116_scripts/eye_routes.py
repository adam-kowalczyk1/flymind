import sys, json, numpy as np, pandas as pd
sys.path.insert(0, '/Users/admin/so101_fly_project/flymind/experiments/step3_wiring')
import nets
A = pd.read_feather(nets.visual_path.ANN, columns=["bodyId", "type", "superclass", "subclass", "somaSide", "rootSide"])
sc = dict(zip(A.bodyId, A.superclass)); ty = dict(zip(A.bodyId, A.type)); sub = dict(zip(A.bodyId, A.subclass)); side = dict(zip(A.bodyId, A.somaSide.fillna(A.rootSide)))
pre_bodies, m = nets.bodies_for("pre")
pre_set = set(int(b) for b in pre_bodies)
dn = set(A.bodyId[A.superclass == "descending_neuron"].astype(int))
vis = set(A.bodyId[A.superclass.isin(["visual_projection"])].astype(int))
W = pd.read_feather(nets.visual_path.WEIGHTS)
pre_, post_, w = W.body_pre.values, W.body_post.values, W.weight.values
# 1) input to every DN
mdn = np.isin(post_, list(dn))
d = pd.DataFrame(dict(pre=pre_[mdn], post=post_[mdn], w=w[mdn]))
d["sc"] = d.pre.map(sc)
tot = d.groupby("post").w.sum()
visin = d[d.sc == "visual_projection"].groupby("post").w.sum()
# 2) DN output to "pre" leg network (T1 L) and to fl-L motor neurons
mo = np.isin(pre_, list(dn)) & np.isin(post_, list(pre_set))
o = pd.DataFrame(dict(pre=pre_[mo], post=post_[mo], w=w[mo]))
o["mn"] = o.post.map(lambda b: sc.get(b) == "vnc_motor")
out_pre = o.groupby("pre").w.sum(); out_mn = o[o.mn].groupby("pre").w.sum()
R = pd.DataFrame(dict(type=[ty.get(b) for b in tot.index], side=[side.get(b) for b in tot.index], in_total=tot, in_visual=visin.reindex(tot.index).fillna(0),
                      out_preNet=out_pre.reindex(tot.index).fillna(0), out_flL_MN=out_mn.reindex(tot.index).fillna(0)))
R["vis_frac"] = R.in_visual / R.in_total
top = R[(R.in_visual >= 500)].sort_values("in_visual", ascending=False)
print("DN z największym wejściem z neuronów projekcyjnych oka (≥500 synaps):", len(top))
print(top.head(25).round(3).to_string())
both = R[(R.in_visual >= 300) & (R.out_preNet >= 50)].sort_values("out_preNet", ascending=False)
print("\nDN: wzrok ≥300 synaps ORAZ ≥50 synaps do sieci nogi „pre” (T1 L):", len(both))
print(both.head(25).round(3).to_string())
# 3) which VPN types feed the 'both' DNs
mv = np.isin(post_, list(both.index)) & np.isin(pre_, list(vis))
v = pd.DataFrame(dict(pre=pre_[mv], post=post_[mv], w=w[mv])); v["vt"] = v.pre.map(ty); v["dt"] = v.post.map(ty)
print("\nNajwiększe typy oka → te DN:")
print(v.groupby(["dt", "vt"]).w.sum().sort_values(ascending=False).head(30).to_string())
R.to_csv(sys.argv[1])
