exec(open("/private/tmp/claude-501/-Users-admin-so101-fly-project/6454b16d-a7f4-423a-a824-4d37dc6a0832/scratchpad/check_decoder_real.py").read().split("# ---------- skręt")[0])
G = [n for n in c["neurons"] if n["module"] == "grip"]
gids = [n["bodyId"] for n in G]; ge, rep = load_edges(W, bodies=gids); gpos = {b: i for i, b in enumerate(gids)}
mn = {k: [n["bodyId"] for n in G if n["type"] == t] for k, t in (("flex", "Ti flexor MN"), ("ext", "Ti extensor MN"), ("ltm", "ltm MN"))}
over = {b: ("glutamate", "założenie") for b in (800636, 815344)}
sens = [gpos[n["bodyId"]] for n in G if n.get("subclass") in ("campaniform sensilla", "leg")]
# ścieżki czucie → MN w danych obwodu
S = {gids[i] for i in sens}; M = set(sum(mn.values(), []))
print("bezpośrednie czucie→MN [syn]:", int(ge.weight[ge.body_pre.isin(S) & ge.body_post.isin(M)].sum()),
      " czucie→IN:", int(ge.weight[ge.body_pre.isin(S) & ~ge.body_post.isin(M | S)].sum()),
      " IN→MN:", int(ge.weight[~ge.body_pre.isin(M | S) & ge.body_post.isin(M)].sum()))
ins = [b for b in gids if b not in S and b not in M]
print("NT interneuronów:", build(ge, gids, nt, ModelParams(), nt_overrides=over).nt.set_index("bodyId").loc[ins].nt.value_counts().to_dict())
for J0 in (0.3, 1.0):
    gs = build(ge, gids, nt, ModelParams(J0=J0), nt_overrides=over)
    for amp in (20.0, 40.0):
        I = np.zeros(len(gids)); I[sens] = amp
        r = np.mean([ALIF(gs, P, s).run(I, 1000)[500:].mean(0) * 1000 for s in SEEDS], 0)
        print(f"J0={J0} czucie {amp} mV: czucie {r[sens].mean():.0f} Hz, IN {r[[gpos[b] for b in ins]].mean():.0f} Hz,",
              {k: r[[gpos[b] for b in mn[k]]].round(0).tolist() for k in mn})
