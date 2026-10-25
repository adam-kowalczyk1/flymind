"""AUDYT WERYFIKACYJNY KONEKTOMU MaleCNS v1.0

Skrypt wyodrębniający surowe dane anatomiczne (bodyId, liczba synaps EM)
oraz predykcje chemiczne (consensus_nt, confidence) dla neuronów zstępujących,
interneuronów i motoneuronów T1 w MaleCNS v1.0.
"""

import os
import sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, ".."))

ANNOT_PATH = os.path.join(PROJECT_ROOT, "data/malecns/body-annotations-male-cns-v1.0-minconf-0.5.feather")
NT_PATH = os.path.join(PROJECT_ROOT, "data/malecns/body-neurotransmitters-male-cns-v1.0.feather")
WEIGHTS_PATH = os.path.join(PROJECT_ROOT, "data/malecns/connectome-weights-male-cns-v1.0-minconf-0.5.feather")

def run_audit():
    print("=== 1. ŁADOWANIE SUROWYCH PLIKÓW DANYCH MALECNS v1.0 ===")
    annot = pd.read_feather(ANNOT_PATH)
    nt = pd.read_feather(NT_PATH)
    weights = pd.read_feather(WEIGHTS_PATH)

    print(f"Załadowano adnotacje: {len(annot):,} ciał (komórek)")
    print(f"Załadowano neuroprzekaźniki: {len(nt):,} ciał")
    print(f"Załadowano krawędzie synaptyczne: {len(weights):,} połączeń\n")

    # Ujednolicenie klucza ID
    id_col_annot = "bodyId" if "bodyId" in annot.columns else annot.columns[0]
    id_col_nt = "body" if "body" in nt.columns else "bodyId"

    # Łączenie metadanych
    meta = pd.merge(
        annot[[id_col_annot, "type", "instance", "class", "subclass", "somaNeuromere", "somaSide"]],
        nt[[id_col_nt, "consensus_nt", "predicted_nt_confidence"]],
        left_on=id_col_annot,
        right_on=id_col_nt,
        how="left"
    ).rename(columns={id_col_annot: "bodyId"})

    meta_dict = meta.set_index("bodyId").to_dict(orient="index")

    # Weryfikacja targetów
    target_dns = ["DNp07", "DNp10", "DNa02", "DNp47", "DNg79", "DNg13"]
    target_ins = ["IN12B018", "IN12A001", "IN13A014", "IN08A006", "IN21A007", "IN13A009", "IN12A003", "IN03B019", "IN07B009"]

    print("=== 2. WERYFIKACJA IDENTYFIKATORÓW I NEUROPRZEKAŹNIKÓW ===")
    dn_bodies = meta[meta["type"].isin(target_dns)].copy()
    in_bodies = meta[meta["type"].isin(target_ins)].copy()

    print("\n--- Neurony zstępujące (Descending Neurons) ---")
    cols_dn = ["bodyId", "type", "instance", "somaSide", "consensus_nt", "predicted_nt_confidence"]
    print(dn_bodies[cols_dn].to_string(index=False))

    print("\n--- Weryfikowane Interneurony (IN) ---")
    cols_in = ["bodyId", "type", "instance", "somaNeuromere", "somaSide", "consensus_nt", "predicted_nt_confidence"]
    print(in_bodies[cols_in].to_string(index=False))

    # Motoneurony T1
    mn_types = ["Ti flexor MN", "Ti extensor MN", "ltm MN"]
    mn_bodies = meta[meta["type"].isin(mn_types)].copy()
    print(f"\n--- Motoneurony piszczeli/stopy (znaleziono: {len(mn_bodies)}) ---")
    print(mn_bodies[["bodyId", "type", "instance", "somaNeuromere", "consensus_nt"]].head(20).to_string(index=False))

    # Ekstrakcja krawędzi synaptycznych
    print("\n=== 3. SUROWE POŁĄCZENIA SYNAPTYCZNE (1-SKOKOWE I 2-SKOKOWE) ===")
    
    # 1. Krok DN -> IN
    dn_ids = set(dn_bodies["bodyId"])
    in_ids = set(in_bodies["bodyId"])
    mn_ids = set(mn_bodies["bodyId"])

    edges_dn_in = weights[weights["body_pre"].isin(dn_ids) & weights["body_post"].isin(in_ids)].copy()
    edges_dn_in["DN_type"] = edges_dn_in["body_pre"].map(lambda x: meta_dict.get(x, {}).get("type"))
    edges_dn_in["DN_instance"] = edges_dn_in["body_pre"].map(lambda x: meta_dict.get(x, {}).get("instance"))
    edges_dn_in["DN_nt"] = edges_dn_in["body_pre"].map(lambda x: meta_dict.get(x, {}).get("consensus_nt"))
    edges_dn_in["IN_type"] = edges_dn_in["body_post"].map(lambda x: meta_dict.get(x, {}).get("type"))
    edges_dn_in["IN_instance"] = edges_dn_in["body_post"].map(lambda x: meta_dict.get(x, {}).get("instance"))
    edges_dn_in["IN_nt"] = edges_dn_in["body_post"].map(lambda x: meta_dict.get(x, {}).get("consensus_nt"))
    edges_dn_in = edges_dn_in.sort_values(by="weight", ascending=False)

    print("\n--- Krawędzie synaptyczne DN -> IN (surowa liczba styków T-bars): ---")
    print(edges_dn_in[["body_pre", "DN_type", "DN_nt", "body_post", "IN_type", "IN_nt", "weight"]].to_string(index=False))

    # 2. Krok IN -> MN
    edges_in_mn = weights[weights["body_pre"].isin(in_ids) & weights["body_post"].isin(mn_ids)].copy()
    edges_in_mn["IN_type"] = edges_in_mn["body_pre"].map(lambda x: meta_dict.get(x, {}).get("type"))
    edges_in_mn["IN_nt"] = edges_in_mn["body_pre"].map(lambda x: meta_dict.get(x, {}).get("consensus_nt"))
    edges_in_mn["MN_type"] = edges_in_mn["body_post"].map(lambda x: meta_dict.get(x, {}).get("type"))
    edges_in_mn["MN_instance"] = edges_in_mn["body_post"].map(lambda x: meta_dict.get(x, {}).get("instance"))
    edges_in_mn["MN_neuromere"] = edges_in_mn["body_post"].map(lambda x: meta_dict.get(x, {}).get("somaNeuromere"))
    edges_in_mn = edges_in_mn.sort_values(by="weight", ascending=False)

    print("\n--- Krawędzie synaptyczne IN -> MN (surowa liczba styków T-bars): ---")
    print(edges_in_mn[["body_pre", "IN_type", "IN_nt", "body_post", "MN_type", "MN_instance", "MN_neuromere", "weight"]].to_string(index=False))

    # Zapis do plików CSV
    out_dir = os.path.join(HERE, "results")
    os.makedirs(out_dir, exist_ok=True)
    
    csv_dn_in = os.path.join(out_dir, "malecns_audit_DN_to_IN.csv")
    csv_in_mn = os.path.join(out_dir, "malecns_audit_IN_to_MN.csv")
    
    edges_dn_in.to_csv(csv_dn_in, index=False)
    edges_in_mn.to_csv(csv_in_mn, index=False)
    print(f"\nZapisano wyniki audytu do:\n  {csv_dn_in}\n  {csv_in_mn}")

if __name__ == "__main__":
    run_audit()
