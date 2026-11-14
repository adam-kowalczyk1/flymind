"""flymind/connectome.py — moduł A: loader i walidator MaleCNS v1.0 flat-connectome.

Izolacja od Stage 1: nie importuje bio2 ani mujoco, niczego nie zapisuje (tylko czyta pliki).

Fakty o danych (nagłówek Arrow, sprawdzone 2026-10-28):
  connectome-weights-male-cns-v1.0-minconf-0.5.feather: body_pre:int64, body_post:int64, weight:int64,
  151 856 684 wierszy, BRAK kolumny confidence. Próg minconf=0.5 (pewność pojedynczej synapsy) zastosował
  dostawca przed agregacją — znamy go tylko z nazwy pliku i nie da się go tu zmienić (do tego potrzebny
  syn-partners-*.feather z pewnością per synapsa). weight = liczba synaps pre→post (research_notes/
  .../malecns_data_access.md), NIE siła fizjologiczna. Kierunek wynika z nazw kolumn; direction() pozwala
  sprawdzić go na połączeniu znanym jako asymetryczne.
"""
import hashlib
import os
import re

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds

EDGE_COLS = ("body_pre", "body_post", "weight")


class ConnectomeError(ValueError):
    pass


def provenance(path, sha256=False):
    """Pochodzenie pliku: ścieżka, rozmiar, mtime, minconf z nazwy, opcjonalnie sha256 (1 GB ≈ kilka s)."""
    st = os.stat(path)
    m = re.search(r"minconf-(\d+(?:\.\d+)?)", os.path.basename(path))
    p = dict(path=os.path.abspath(path), bytes=st.st_size, mtime=st.st_mtime, minconf=float(m.group(1)) if m else None)
    if sha256:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 24), b""):
                h.update(chunk)
        p["sha256"] = h.hexdigest()
    return p


def validate_edges(df):
    """Twarde błędy: brak kolumn, typy nie-całkowite, pusto, null, id ≤ 0, weight ≤ 0, zduplikowane pary.
    Autapsy (pre == post) są dozwolone, ale liczone w raporcie. Zwraca raport."""
    missing = [c for c in EDGE_COLS if c not in df.columns]
    if missing:
        raise ConnectomeError(f"brak kolumn: {missing}")
    for c in EDGE_COLS:
        if not pd.api.types.is_integer_dtype(df[c]):
            raise ConnectomeError(f"kolumna {c} nie jest całkowita: {df[c].dtype}")
    if df.empty:
        raise ConnectomeError("brak krawędzi")
    if df[list(EDGE_COLS)].isna().any().any():
        raise ConnectomeError("wartości null w krawędziach")
    if (df.body_pre <= 0).any() or (df.body_post <= 0).any():
        raise ConnectomeError("bodyId ≤ 0")
    if (df.weight <= 0).any():
        raise ConnectomeError("weight ≤ 0 (liczba synaps musi być dodatnia)")
    dup = int(df.duplicated(["body_pre", "body_post"]).sum())
    if dup:
        raise ConnectomeError(f"{dup} zduplikowanych par (pre, post) — niejednoznaczna waga")
    return dict(edges=len(df), synapses=int(df.weight.sum()), self_loops=int((df.body_pre == df.body_post).sum()),
                bodies=int(pd.concat([df.body_pre, df.body_post]).nunique()))


def load_edges(path, bodies=None, minconf=0.5, min_weight=1, sha256=False):
    """Krawędzie z pliku feather. bodies: podgraf indukowany (strumieniowo, bez ładowania całego grafu).
    minconf musi zgadzać się z progiem zaszytym w pliku — inaczej odmowa (nie udajemy refiltracji).
    min_weight: jawny próg liczby synaps, raportowany przed i po. Zwraca (DataFrame, raport)."""
    prov = provenance(path, sha256)
    if prov["minconf"] is None:
        raise ConnectomeError(f"nieznany próg confidence (brak 'minconf-X' w nazwie): {path}")
    if prov["minconf"] != minconf:
        raise ConnectomeError(f"plik ma minconf={prov['minconf']}, żądano {minconf}; plik wag nie ma kolumny "
                              "confidence, więc progu nie da się zmienić bez syn-partners-*.feather")
    d = ds.dataset(path, format="ipc")
    missing = [c for c in EDGE_COLS if c not in d.schema.names]
    if missing:
        raise ConnectomeError(f"brak kolumn: {missing}")
    filt = None
    if bodies is not None:
        ids = pa.array(sorted({int(b) for b in bodies}), pa.int64())
        filt = pc.field("body_pre").isin(ids) & pc.field("body_post").isin(ids)
    df = d.to_table(columns=list(EDGE_COLS), filter=filt).to_pandas()
    rep = dict(provenance=prov, rows_in_file=d.count_rows(), loaded=validate_edges(df), min_weight=min_weight)
    if bodies is not None:
        seen = set(df.body_pre) | set(df.body_post)
        rep["bodies_requested"] = len(ids)
        rep["bodies_without_edges"] = sorted(int(b) for b in ids.to_pylist() if b not in seen)
    if min_weight > 1:
        df = df[df.weight >= min_weight].reset_index(drop=True)
    rep["after_min_weight"] = dict(edges=len(df), synapses=int(df.weight.sum()))
    return df, rep


def map_populations(ann, spec, strict=True):
    """ann: adnotacje z kolumną bodyId; spec: {populacja: {kolumna: wartość | lista}} (AND kolumn).
    Pusta populacja → błąd (strict) lub wpis w raporcie; ciało w dwóch populacjach → zawsze błąd.
    Zwraca ({populacja: tablica bodyId}, raport z kryteriami)."""
    pops, empty = {}, []
    for name, crit in spec.items():
        mask = np.ones(len(ann), bool)
        for col, val in crit.items():
            if col not in ann.columns:
                raise ConnectomeError(f"{name}: brak kolumny adnotacji {col!r}")
            mask &= ann[col].isin(val if isinstance(val, (list, tuple, set)) else [val]).to_numpy()
        pops[name] = np.sort(ann.bodyId.to_numpy()[mask])
        if not len(pops[name]):
            empty.append(name)
    if empty and strict:
        raise ConnectomeError(f"puste populacje (brak neuronów w danych): {empty}")
    allids = np.concatenate(list(pops.values())) if pops else np.array([], int)
    uniq, cnt = np.unique(allids, return_counts=True)
    if (cnt > 1).any():
        raise ConnectomeError(f"ciała w wielu populacjach: {uniq[cnt > 1][:10].tolist()}")
    return pops, dict(criteria=spec, sizes={k: len(v) for k, v in pops.items()}, empty=empty)


def direction(df, pre, post):
    """(synapsy pre→post, synapsy post→pre) — test kierunku na połączeniu znanym jako asymetryczne."""
    pre, post = list(pre), list(post)
    fwd = df.weight[df.body_pre.isin(pre) & df.body_post.isin(post)].sum()
    rev = df.weight[df.body_pre.isin(post) & df.body_post.isin(pre)].sum()
    return int(fwd), int(rev)
