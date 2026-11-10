"""Porównanie powtórzonych prób z zapisanymi: wszystko poza polami czasu zegarowego musi być identyczne."""
import json, sys
R = sys.argv[1]
def strip(x):
    if isinstance(x, dict): return {k: strip(v) for k, v in x.items() if "wall" not in k and k != "lat"}
    if isinstance(x, list): return [strip(v) for v in x]
    return x
def key(r): o = r["objects"][0]; return (o["shape"], o["material"], o["spawn"]["x"], o["spawn"]["y"])
for new, old in (("sensory_manipulation/repro_check_B_fly_search_v1.json", "sensory_manipulation/B_fly_search_glu-1_v1.json"),
                 ("sensory_manipulation/repro_check_C_fly_feco_search_v1.json", "sensory_manipulation/C_fly_feco_search_v1.json"),
                 ("object_handling/repro_check_B_base_v2.json", "object_handling/B_base_v2.json")):
    a, b = json.load(open(R + new)), json.load(open(R + old))
    B = {key(r): strip(r) for r in b["runs"]}
    same = sum(B.get(key(r)) == strip(r) for r in a["runs"])
    print(f"{new}: prób {len(a['runs'])}, identycznych z {old} (poza czasem zegarowym): {same}")
