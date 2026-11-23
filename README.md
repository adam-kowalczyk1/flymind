# FlyMind — a fly-connectome spiking network controlling an SO-101 arm (simulation)

Research project: a spiking neural network built from the male fly central nervous system connectome (MaleCNS)
controls a SO-101 robot arm in MuJoCo simulation. **Simulation only; no claims about real flies or real hardware.**
Negative results and control tests (shuffled networks, placebo tests) are reported openly, e.g.
`flymind/experiments/step3_wiring/WYNIK_PLACEBO.md` (results/notes are mostly in Polish).

- `flymind/` — code, experiments (each with a pre-registered plan and result report), results
- `hardware/` — SO-101 mounts and sensor designs; `assets/` — meshes; `reports/`, `research_notes/` — literature notes

## Data not included (download separately)
- MaleCNS connectome (v1.0, Janelia/FlyEM) → `data/malecns/*.feather`
- flyvis models and Sintel dataset → `data/flyvis/`

Large generated result files (`*.feather`, `*.npz`) are not tracked. License: MIT (see `LICENSE`).
