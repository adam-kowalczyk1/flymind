# Measurable properties of current VLA robot models (as of 3 Nov 2026) for comparison with a 424-neuron SNN controller on an SO-101 arm

Compiled 2026-11-03. Evidence tags used below:
- **[MEASURED]** = number from a paper/repo table produced by an experiment (hardware and date given where known).
- **[DOCS]** = vendor/repo documentation requirement or spec statement (not a benchmark).
- **[VENDOR CLAIM]** = marketing/blog statement without reproducible numbers, or chart-only values.
- **[THIRD-PARTY]** = secondary/aggregator source; lower reliability.

Reference side of the comparison (the user's SNN, not researched here): 424 neurons, ~0.4 ms per control tick on a laptop CPU, no training data. Useful derived yardsticks are in each "Inferences" block.

Quick-look table (all numbers detailed and sourced in sections below):

| Model | Params | Inference latency (hardware, date of source) | Chunk / control | Min GPU memory | Open weights |
|---|---|---|---|---|---|
| pi0 (Oct 2024; paper v4 Jan 2026) | 3.3B (3B PaliGemma + 300M action expert) | 73 ms on-board, RTX 4090, 3 cameras | 50-action chunk, 20-50 Hz | >8 GB inference, >22.5 GB LoRA, >70 GB full FT (openpi) | yes (openpi, Apache-2.0 code) |
| pi0-FAST (Jan-Feb 2025) | ~3B (autoregressive) | ~750 ms between chunks (as quoted by OFT paper, Feb 2025) | token-decoded chunk | same repo table | yes |
| pi0.5 (Apr 2025; openpi Sept 2025) | 300M action expert stated; total not stated by PI | 412.9 ms to 1.4 s on Jetson Orin (2026 papers) | 50 steps ~1 s | >8 GB inference | yes (flow head only) |
| pi*0.6 (Nov 2025) | 5B VLM (action expert size not stated) | not reported | 50 actions = 1 s at 50 Hz | not stated | not listed in openpi |
| pi0.7 (Apr 2026) | 4B Gemma-3 + 860M action expert (the-decoder, secondary) | not reported | not reported | not stated | apparently closed (single third-party source) |
| SmolVLA (Jun 2025) | 0.45B (~100M action expert) | 204.6 ms per 50-action chunk, PyTorch-MPS, Apple M5 Pro (project benchmark) | 30 fps, 50-action chunks | not stated | yes (HF/LeRobot) |
| OpenVLA (Jun 2024) | 7B | ~6 Hz on RTX 4090; 0.33 s per action step on A100 | 1 action per forward pass | 15 GB bf16 (7 GB int4) | yes |
| OpenVLA-OFT (Feb 2025) | 7B | 0.321 s per query (3 images) on A100 = 25 actions per query | 25 Hz ALOHA, chunk K=25 | needs 8x A100/H100 80GB to fine-tune (paper) | yes |
| GR00T N1 (Mar 2025) | 2.2B (1.34B VLM) | 63.9 ms per 16-action chunk, L40, bf16 | actions at up to 120 Hz | not stated | yes |
| GR00T N1.7 (2026) | 3B | ~28 Hz on Jetson AGX Thor with TensorRT (README) | - | >=16 GB inference, >=40 GB fine-tune | yes (license ambiguous) |
| Gemini Robotics On-Device (Jun 2025) | not disclosed | not disclosed ("low-latency") | not disclosed | not disclosed | no (trusted-tester SDK only) |

---

## Q1. Physical Intelligence models: pi0, pi0-FAST, pi0.5, and newer (pi*0.6, pi0.7)

### Takeaway
pi0 is a 3.3B-parameter flow-matching VLA whose measured on-board inference on an RTX 4090 is 73 ms per 50-action chunk (executed open-loop at 20-50 Hz, replanned every 0.5-0.8 s); openpi requires >8 GB GPU for inference, >22.5 GB for LoRA fine-tuning and >70 GB for full fine-tuning. The open-weights set is pi0, pi0-FAST and pi0.5 (Apache-2.0 code); newer pi*0.6 (Nov 2025) and pi0.7 (Apr 2026) are announced via papers/blogs and, since 13 Oct 2026, a hosted Pi API beta, not as downloadable weights as far as I could verify.

### Cited Findings

**Release timeline (PI blog list, accessed 2026-11-03)**
- Oct 31 2024 pi0; Jan 16 2025 FAST; Feb 4 2025 open-sourcing pi0 + pi0-FAST; Apr 22 2025 pi0.5; Jun 9 2025 Real-Time Action Chunking; Nov 17 2025 pi*0.6; Mar 19 2026 "Precise Manipulation with Efficient Online RL"; Apr 16 2026 pi0.7; Oct 13 2026 "Frontier Models for Every Robot" (Pi API beta: upload data, fine-tune, cloud inference). — [PI blog index](https://www.pi.website/blog)

**pi0 size, chunking, control rate, latency [MEASURED, paper v4 dated 8 Jan 2026]**
- 3B-parameter PaliGemma VLM + 300M-parameter action expert (initialized from scratch) = 3.3B total. — [pi0 paper, arXiv 2410.24164 (HTML v4)](https://arxiv.org/html/2410.24164v4)
- Action chunk H = 50 actions; "up to 50 Hz" control (laundry folding). Inference every 0.8 s (after 16 executed actions) for 20 Hz UR5e/Franka; every 0.5 s (after 25 actions) for 50 Hz robots. Chunks executed open-loop; temporal ensembling "hurt policy performance" and was not used. — [pi0 paper](https://arxiv.org/html/2410.24164v4)
- Latency table (NVIDIA RTX 4090, 3 camera images): image encoders 14 ms; observation forward pass 32 ms; 10 flow-matching steps 27 ms; network latency if off-board 13 ms; total on-board 73 ms; total off-board 86 ms. — [pi0 paper, Table I](https://arxiv.org/html/2410.24164v4)
- Independent measurement of pi0 on A100 (JAX): latency 0.086 s per query, throughput 291.6 actions/s (25-action chunk, 3 images) — [OFT paper Table III, arXiv 2502.19645](https://arxiv.org/html/2502.19645)
- Independent cross-hardware measurement of pi0 (LIBERO, BF16, 2026-04): RTX 4090 102.3 ms; Jetson Thor 246.0 ms; Jetson AGX Orin 920.6 ms. Accompanying LIBERO average 86.0% (hardware-independent). — [Zhou et al., arXiv 2604.24447 (27 Apr 2026), Table 1](https://arxiv.org/html/2604.24447)
- Profiling: VLM backbone is compute-bound, action expert is memory-bound; on Orin/Thor the action expert's arithmetic intensity (64.5 FLOPs/byte) is far below the ridge points (208 on Orin, 945 on Thor). — [arXiv 2604.24447](https://arxiv.org/html/2604.24447)

**pi0 data**
- Pretraining: ~10,000 hours of own dexterous data, 7 robot configurations, 68 tasks; plus OXE, Bridge v2, DROID (9.1% of mix); 903M timesteps of own data (106M single-arm, 797M dual-arm). Main model trained for 700k steps. — [pi0 paper](https://arxiv.org/html/2410.24164v4)
- Post-training data per task: "the simplest of the tasks necessitating only 5 hours and the most complex tasks using 100 or more hours of data". — [pi0 paper](https://arxiv.org/html/2410.24164v4)
- Paper concedes: "Not all tasks in our evaluation work reliably, and it remains unclear how to predict how much and what kind of data is needed to attain near-perfect performance." — [pi0 paper](https://arxiv.org/html/2410.24164v4)
- Fine-tuning eval: 10 trials per task, tasks scored with progress rubrics; pi0 compared against OpenVLA, Octo, ACT and Diffusion Policy; "the strongest prior models are the ones that are trained entirely from scratch on the target tasks" (i.e., ACT/DP). — [pi0 paper](https://arxiv.org/html/2410.24164v4)

**openpi repo (README on main, accessed 2026-11-03)**
- GPU memory (single NVIDIA GPU): inference >8 GB (e.g. RTX 4090); LoRA fine-tune >22.5 GB (RTX 4090); full fine-tune >70 GB (A100 80GB/H100). `fsdp_devices` can shard to reduce per-GPU memory. — [openpi README](https://github.com/Physical-Intelligence/openpi) / [raw](https://raw.githubusercontent.com/Physical-Intelligence/openpi/main/README.md) [DOCS]
- Supported: pi0 (flow), pi0-FAST (autoregressive, FAST tokenizer), pi0.5 (flow-matching head only for training and inference; released Sept 2025). PyTorch ports exist for pi0 and pi0.5 only (not pi0-FAST). Tested only on Ubuntu 22.04; NVIDIA GPU required; no mention of CPU or Apple Silicon. — [openpi README](https://github.com/Physical-Intelligence/openpi)
- Base pretrained checkpoints: >10k hours of robot data. Repo says no minimum demonstration count; fine-tuned "expert" checkpoints trained on "relatively small datasets"; "pi0 may or may not work for you". — [openpi README](https://raw.githubusercontent.com/Physical-Intelligence/openpi/main/README.md)
- License: repository is Apache-2.0; the repo also ships a separate `LICENSE_GEMMA.txt` (scope not explained on the page I read - likely Gemma terms for the Gemma-derived weights, unverified). LeRobot's pi0 doc also states Apache-2.0. — [openpi](https://github.com/Physical-Intelligence/openpi); [LeRobot pi0 docs](https://huggingface.co/docs/lerobot/pi0)
- pi0.5 fine-tuned on LIBERO (openpi LIBERO README): Spatial 98.8, Object 98.2, Goal 98.0, Long 92.4, average 96.85 (simulation, fine-tuned). — [openpi LIBERO README](https://raw.githubusercontent.com/Physical-Intelligence/openpi/main/examples/libero/README.md) [MEASURED]
- LeRobot fine-tune recipe example for pi0: batch 32, 3000 steps, bf16, gradient checkpointing; Apache-2.0. — [LeRobot pi0 docs](https://huggingface.co/docs/lerobot/pi0) [DOCS]

**pi0-FAST**
- FAST tokenizer (DCT-based compression of action trajectories); pi0-FAST "matches the performance of the state-of-the-art pi0 diffusion VLA ... while training 5x faster"; FAST+ universal tokenizer trained on 1M real-robot action trajectories; combined with pi0 backbone scales to 10k hours. — [FAST paper, arXiv 2501.09747](https://arxiv.org/html/2501.09747)
- Inference is slower than the flow model: openpi notes pi0-DROID has "faster inference than pi0-FAST-DROID"; the OFT paper quotes "significant latency between action chunks (e.g., 750 ms for the recent FAST approach)". — [openpi README](https://github.com/Physical-Intelligence/openpi); [OFT paper](https://arxiv.org/html/2502.19645)

**pi0.5 (Apr 2025 blog + later measurements)**
- Action expert 300M; total model size not stated on blog; 50-step action chunk (~1 s). Ablation table: in-distribution success 83%, out-of-distribution 94% (full pi0.5) vs 57% / 31% (no multi-environment data, "no ME"). Mobile-manipulator data in an ablation ~400 hours; performance approaches the test-environment baseline at ~100 training environments. — [pi0.5 blog](https://www.pi.website/blog/pi05) [MEASURED, vendor-run]
- pi0.5 on Jetson AGX Orin (third-party engines, 2026): Rust engine ApxInf: 165.67 ms (6.0 Hz) BF16 with 10-step generation, 119.05 ms (8.4 Hz) with one-step; Thor FP8 41.16 ms (24.3 Hz); settings = batch 1, two 224x224 views, action horizon 10; LIBERO-10 92.0% (Orin BF16), 94.0% (Thor FP8). — [ApxInf releases](https://github.com/infinigence/ApxInf/releases) [THIRD-PARTY, via search summary; not opened directly]
- Jetson-PI (arXiv 2607.12659, Jul 2026): pi0.5 baseline ~1.4 s per inference on Jetson Orin, reduced to 412.9 ms (6.06 Hz control) with asynchronous foresight-aligned correction and a llama.cpp-based engine. — [Jetson-PI](https://arxiv.org/pdf/2607.12659) [reported via search summary; abstract-level]
- Real-Time Chunking (RTC): inpainting-based asynchronous chunk generation for flow/diffusion VLAs; works with inference delays "in excess of 300 milliseconds" (>30% of horizon); same motion 20% faster than synchronous inference; applies without retraining. — [RTC paper, arXiv 2506.07339](https://arxiv.org/html/2506.07339)

**pi*0.6 (Nov 17 2025)**
- 5B-parameter VLM; trained with RL from experience ("Recap"); "over a 90% success rate" on espresso stages; throughput "more than doubles" on hardest tasks; failure rate down "2x or more"; espresso making ran ~18 h (5:30am-11:30pm); 59 boxes assembled in a factory; 50 novel laundry items in a new home. Exact per-task rates only on charts. — [pi*0.6 blog](https://www.pi.website/blog/pistar06) [VENDOR CLAIM / chart-only]
- In the RL-token paper pi0.6 is used with 50-action chunks (=1 s at 50 Hz), executing a prefix (e.g. first 20 steps) before re-planning; 14-D actions; up to 4 camera images. — [RLT paper, arXiv 2604.23073](https://arxiv.org/html/2604.23073)

**pi0.7 (Apr 16 2026)**
- Described as "steerable" (language + metadata such as speed/quality + visual subgoals). Backbone Gemma 3 4B, action expert 860M (the-decoder; a different aggregator claims 7B - conflicting, unresolved). Bimanual UR5e t-shirt folding 80% with no folding data on that robot; air-fryer task needs step-by-step coaching; latency and total data size not reported; PI itself concedes it cannot be certain which tasks are truly novel. — [the-decoder](https://the-decoder.com/physical-intelligence-shows-robot-model-with-llm-like-generalization-flaws-included/) [THIRD-PARTY]
- Primary blog URL for pi0.7 could not be fetched (404 at the URL I guessed); listing only: "pi0.7. A steerable robot foundation model with a large jump in generalization." — [PI blog index](https://www.pi.website/blog)
- Open-weights status: a model directory lists pi0.7 as closed-weights and pi0/pi0-FAST/pi0.5 as open (updated 19 Oct 2026). openpi README (main) lists only pi0, pi0-FAST, pi0.5. — [roboticscenter.ai directory](https://www.roboticscenter.ai/institutions/models/physical-intelligence) [THIRD-PARTY, single source]; [openpi README](https://github.com/Physical-Intelligence/openpi)

**Pi API beta (Oct 13 2026)**
- Hosted fine-tuning and cloud inference for "latest models" (PI blog index); secondary coverage says pi0 and pi0.5 fine-tuning via waitlist, no published pricing. — [PI blog index](https://www.pi.website/blog); [aiweekly](https://aiweekly.co/alerts/physical-intelligence-opens-pi-api-beta-for-0-05-fine-tuning); [unite.ai](https://unite.ai/physical-intelligence-opens-pi-api-beta-for-robot-foundation-models) [THIRD-PARTY]

**Real deployment data point for pi0.5 fine-tuning**
- Siemens factory case study (arXiv 2605.27461, 25 May 2026): pi0.5 iteratively fine-tuned on 2,535 episodes (~10 hours) for a bag-insertion packaging task; abstract reports "recurring failure modes", no success rate in the abstract. — [arXiv 2605.27461](https://arxiv.org/abs/2605.27461)

### Inferences
- Tick-rate gap: pi0's 73 ms (RTX 4090) is one inference per 25-50 actions, i.e. the policy "decides" ~2 times per second and replays a chunk open-loop in between; the SNN's 0.4 ms tick is ~180x shorter than the pi0 forward pass and is closed-loop at every tick. On an Orin-class edge board the same model needs ~0.17-0.9 s per chunk (sources disagree by 5x depending on engine/optimization).
- Fine-tuning minimum for pi0-class models is roughly 5 h of demos for the easiest tasks (paper), >=22.5 GB GPU for LoRA - versus 0 data and a CPU for the SNN. For an SO-101 the openpi path additionally needs Linux + NVIDIA GPU (README), so a MacBook-only setup cannot run the official pi0 stack.
- Chunk execution means pi0 reacts to disturbances only at replanning boundaries (0.5-0.8 s in the paper's configuration), unless RTC is used.

### Gaps
- pi0.5 total parameter count (blog only gives 300M action expert) and PI-measured pi0.5 latency not found in primary sources.
- pi0.7 primary blog/tech-report numbers (params, latency, data amounts) not retrieved; arXiv 2604.15483 mentioned by an aggregator was not verified.
- Whether pi*0.6 / pi0.7 weights are public: no primary statement found; only a third-party directory says pi0.7 is closed.
- The scope of `LICENSE_GEMMA.txt` in openpi (weights license) not confirmed.
- No official openpi latency table for Jetson/Apple Silicon; third-party Orin numbers disagree (165 ms vs 413 ms vs 920 ms for different model/versions/engines).

---

## Q2. SmolVLA (Hugging Face, Jun 2025)

### Takeaway
SmolVLA is 0.45B parameters (action expert ~100M), pretrained on ~22.9k community SO-100 episodes (10.6M frames, ~30k GPU hours); on a real SO-101 pick-place-Lego task it scored 90% in-distribution / 50% OOD (ACT: 70% / 40%), and on an SO-100 three-task suite 78.3% vs ACT 48.3% - but each real-world cell is a small sample and each SO-101 task was learned from 50 demonstrations. A PyTorch-MPS benchmark on an Apple M5 Pro gives ~205 ms per 50-action chunk; official latency tables for CPU/MPS are not given in the paper.

### Cited Findings
- Architecture: SmolVLM-2 backbone with half the layers kept (layer skipping), 64 visual tokens per frame (no image tiling), flow-matching action expert (hidden size 0.75x of VLM, interleaved cross- and self-attention, ~100M params); total "less than 0.5B"; paper variants 0.24B / 0.45B / 2.25B. — [SmolVLA paper, arXiv 2506.01844](https://arxiv.org/html/2506.01844); [HF blog](https://huggingface.co/blog/smolvla)
- Stated design goal: "trained on a single GPU and deployed on consumer-grade GPUs or even CPUs" [VENDOR CLAIM - paper gives no CPU timings]. — [arXiv 2506.01844](https://arxiv.org/html/2506.01844)
- Pretraining data: 481 community datasets (paper Table 1; the blog says 487), 22.9K episodes, 10.6M frames, all SO-100, 30 FPS; pretraining used 4 GPUs, "approximately 30k GPU hours" for the whole project. Limitations listed: single robot type in pretraining, ~23k trajectories vs ~1M for OpenVLA, short-horizon tasks only. — [arXiv 2506.01844](https://arxiv.org/html/2506.01844)
- Real-world fine-tuning data: three SO-100 datasets and one SO-101 dataset, each "10 trajectories for each of 5 distinct starting positions, resulting in a total of 50 demonstrations per dataset". SmolVLA was not pretrained on any SO-101 data. Simulation: MetaWorld dataset of 50 demos x 50 tasks; LIBERO/Meta-World eval = 10 trials per task. — [arXiv 2506.01844](https://arxiv.org/html/2506.01844)
- SO-100 real-world (Table 3): Pick-Place / Stacking / Sorting / Avg - ACT (single-task) 70/50/25/48.3; pi0 3.5B (multi-task) 100/40/45/61.7; SmolVLA 0.45B (multi-task) 75/90/70/78.3. — [arXiv 2506.01844](https://arxiv.org/html/2506.01844) [MEASURED, small n; number of real-world trials per cell not found]
- SO-101 real-world (Table 4, Pick-Place-Lego, single-task): ACT 70% in-distribution / 40% OOD; SmolVLA 90% / 50%. — [arXiv 2506.01844](https://arxiv.org/html/2506.01844) [MEASURED]
- Ablation (Table 5, SO-100): SmolVLA without robotics pretraining, single-task: 55/45/20 -> avg 40%; multi-task no pretraining 51.7%; with community pretraining 78.3% (+26.6 points). So the single-task un-pretrained SmolVLA (40%) is below ACT (48.3%). — [arXiv 2506.01844](https://arxiv.org/html/2506.01844); [HF blog](https://huggingface.co/blog/smolvla)
- Simulation (Table 2) LIBERO avg: Diffusion Policy 72.4; Octo 75.1; OpenVLA 7B 76.5; pi0 (PaliGemma, no robot pretraining) 71.8; pi0 3.3B (pretrained) 86.0; SmolVLA 0.24B 82.75, 0.45B 87.3, 2.25B 88.75. Meta-World avg: Diffusion Policy 10.5; TinyVLA 31.6; pi0 pretrained 47.9; SmolVLA 0.45B 57.3. — [arXiv 2506.01844](https://arxiv.org/html/2506.01844) [MEASURED; baseline numbers partly copied from other papers]
- Compared with pi0: "around 40% faster to train and consumes 6x less memory". — [arXiv 2506.01844](https://arxiv.org/html/2506.01844)
- Control: real-world frame rate 30 fps (control cycle 33 ms); asynchronous inference (policy server + RobotClient, queue threshold g=0.7) cut average task time 13.75 s -> 9.7 s (~30% faster) and raised cubes completed in a fixed 60 s window from 9 to 19, at comparable success. — [arXiv 2506.01844](https://arxiv.org/html/2506.01844); [HF blog](https://huggingface.co/blog/smolvla)
- Apple Silicon: `mlx-smolvla` (community package) benchmarks on an Apple M5 Pro: median 110.75 ms per 50-action chunk in MLX fp32 vs 204.58 ms PyTorch-MPS (1.85x); a 50-action chunk at 30 fps = 1.67 s (~15x real time); LoRA training bf16, effective batch 8: 0.873 updates/s, 2.27 GiB peak MLX memory. — [mlx-smolvla on PyPI](https://pypi.org/project/mlx-smolvla/) [THIRD-PARTY, project's own benchmark]
- Edge: vla.cpp (arXiv 2606.08094, Jun 2026) runtime covers 11 VLAs incl. SmolVLA/BitVLA on RTX 3060, AGX Orin and 8 GB Jetson Orin Nano; a search summary quotes 353-457 ms median latency on Orin Nano. — [vla.cpp](https://arxiv.org/abs/2606.08094) [abstract confirms hardware; latency figure only via search summary]
- Training time/energy of fine-tuning: ~9.55 h projected for 30,000 LoRA updates on M5 Pro (optimizer work only). — [mlx-smolvla](https://pypi.org/project/mlx-smolvla/)

### Inferences
- SmolVLA fine-tuning needs ~50 teleoperated demos per task and a GPU or a Mac for hours; the SNN needs neither. SmolVLA's per-chunk latency on a laptop (~0.1-0.2 s) is ~250-500x the SNN tick.
- Honest caveat for the student: SmolVLA's advantage over ACT in the paper is largest in multi-task/pretrained settings; on a single narrow task with no pretraining the paper's own ablation shows SmolVLA (40%) not beating ACT (48.3%).

### Gaps
- No official SmolVLA CPU or MPS latency table in the paper/blog; only the community MLX benchmark.
- Number of real-world evaluation trials per task not located (success percentages like 75/90/70 suggest 10-20 trials; unverified).
- No SO-101 absolute positioning accuracy in mm.

---

## Q3. OpenVLA / OpenVLA-OFT, NVIDIA GR00T N1/N1.5/N1.6/N1.7, Gemini Robotics (On-Device)

### Takeaway
OpenVLA (7B) runs at ~6 Hz on an RTX 4090 with 15 GB VRAM and one action per forward pass; OpenVLA-OFT makes it 26-43x faster via parallel decoding and 8-25-action chunks (25 Hz on ALOHA) but still needs 8x A100/H100 80 GB to fine-tune. GR00T N1 (2.2B) generates a 16-action chunk in 63.9 ms on an L40; the newest GR00T (N1.7, 3B) runs ~25-28 Hz on a Jetson AGX Thor with TensorRT. Gemini Robotics On-Device discloses no parameter count, latency or hardware.

### Cited Findings

**OpenVLA (Jun 2024) [MEASURED]**
- 7B parameters; trained on 64 A100 for 14 days = 21,500 A100-hours, batch 2048. Inference 15 GB in bf16, "approximately 6 Hz on one NVIDIA RTX 4090" without optimizations. — [OpenVLA paper, arXiv 2406.09246](https://arxiv.org/html/2406.09246)
- Quantization on BridgeData V2 (WidowX): bf16 71.3 +/- 4.8% at 16.8 GB; int8 58.1% at 10.2 GB; int4 71.9 +/- 4.7% at 7.0 GB. — [arXiv 2406.09246](https://arxiv.org/html/2406.09246)
- Outperforms RT-2-X (55B) by 16.5% absolute across 29 tasks; fine-tuned OpenVLA beats Diffusion Policy by 20.4% in multi-task, language-grounded settings; but "For narrower but highly dexterous tasks, Diffusion Policy still shows smoother and more precise trajectories". — [arXiv 2406.09246](https://arxiv.org/html/2406.09246)
- Single-action decoding takes 0.33 s on an A100 and action chunking is impractical for autoregressive decoding (K*D sequential passes). Measured later: 4.2 Hz / 0.2396 s (LIBERO query), 1.8 Hz / 0.543 s (ALOHA query with 3 images). — [OFT paper](https://arxiv.org/html/2502.19645)

**OpenVLA-OFT (Feb 2025; v2 Apr 2025) [MEASURED]**
- LIBERO average 76.5% -> 97.1% (four suites; pi0 fine-tuned 94.2%), with 26x faster action generation using 8-step chunks and parallel decoding; ALOHA bimanual at 25 Hz with chunk K=25, 43x faster throughput than base OpenVLA; OFT+ (with FiLM) beats pi0, RDT-1B, Diffusion Policy and ACT "by up to 15% (absolute) in average success rate". — [OFT paper, arXiv 2502.19645](https://arxiv.org/html/2502.19645)
- ALOHA inference table (A100, 3 images, K=25): OpenVLA 1.8 Hz / 0.543 s; OpenVLA-OFT+ 77.9 Hz / 0.321 s; RDT-1B 84.1 / 0.297; Diffusion Policy 267.4 / 0.090; pi0 291.6 / 0.086; ACT 432.8 / 0.058. — [OFT paper Table III](https://arxiv.org/html/2502.19645)
- Fine-tuning cost: LIBERO 50-150K gradient steps, batch 64-128, 8x A100/H100; ALOHA tasks e.g. 300 demonstrations (100 per object) for a language-conditioned task, 8x A100/H100-80GB, K=25. — [OFT paper](https://arxiv.org/html/2502.19645)
- Stated limitation: L1 regression may struggle with truly multimodal demonstrations. — [OFT paper, Limitations](https://arxiv.org/html/2502.19645)

**NVIDIA GR00T N1 (Mar 2025) [MEASURED, paper]**
- 2.2B total, 1.34B VLM; 63.9 ms to sample a 16-action chunk on an L40 (bf16); VLM runs at 10 Hz and the DiT action module produces actions at 120 Hz. Pretraining ~50,000 H100 GPU-hours (up to 1,024 H100s). — [GR00T N1 paper, arXiv 2503.14734](https://arxiv.org/html/2503.14734)
- Data: 88 h of real teleop expanded to 827 h with neural trajectories; 780k synthetic trajectories generated in 11 h. — [arXiv 2503.14734](https://arxiv.org/html/2503.14734)
- Real GR-1 humanoid post-training: average success Diffusion Policy 10.2% (10% data) / 46.4% (full data) vs GR00T-N1-2B 42.6% / 76.8%. Simulation with 100 demos/task: BC-Transformer 26.4%, Diffusion Policy 33.4%, GR00T-N1 45.0% averaged over RoboCasa, DexMG, GR-1. — [arXiv 2503.14734](https://arxiv.org/html/2503.14734)

**GR00T N1.6 / N1.7 (2025-2026)**
- NVIDIA repo says latest = GR00T N1.7 (GA), base `nvidia/GR00T-N1.7-3B`, 3B params. Code Apache-2.0; weights under the NVIDIA Open Model License (README also says "fully commercially licensable under Apache 2.0" - internally inconsistent). Inference needs >=16 GB (RTX 4090, L40, H100, Jetson Thor/Orin, DGX Spark); fine-tuning >=40 GB recommended. README speeds: ~40 Hz on RTX PRO 6000 Blackwell (TensorRT, batch 1, LIBERO), ~28 Hz on Jetson AGX Thor (TensorRT, MAXN). No minimum demo count; "a few thousand steps". SO100 example workflow exists (5-episode demo set for quick test); SO-101 not named. — [Isaac-GR00T repo](https://github.com/NVIDIA/Isaac-GR00T) [DOCS]
- NVIDIA Jetson AI Lab: GR00T N1.7 on Thor end-to-end 125 ms -> 39.9 ms with TensorRT mixed NVFP4 (3.1x; ~25 Hz; 4 denoising steps, one camera). — [Jetson AI Lab](https://www.jetson-ai-lab.com/tutorials/groot_n17_on_thor/) [vendor tutorial; via search summary]
- GR00T N1.6-3B on Thor PyTorch: 105 ms (9.5 Hz); ~22.8 Hz on RTX 4090 (third-party docs mirror of the repo FAQ). A Hugging Face mirror card lists 6.9 Hz (PyTorch eager) and 10.7 Hz (TensorRT) on Thor - conflicts with NVIDIA's numbers. — [mintlify mirror of FAQ](https://mintlify.wiki/NVIDIA/Isaac-GR00T/resources/faq); [HF mirror](https://huggingface.co/Rohith67/GR00T-N1.7-3B) [THIRD-PARTY]
- No GR00T "N2" release found in my searches (search summary: "I found no results for an N2 release").

**Gemini Robotics On-Device (DeepMind, Jun 24 2025)**
- Stated: runs locally on the robot, no network needed; adaptable with "as few as 50 to 100 demonstrations"; trained on ALOHA, adapted to bi-arm Franka FR3 and Apptronik Apollo humanoid; SDK via trusted-tester program only. Chart values (approx.): 9-task generalization benchmark ~0.52-0.74 vs ~0.60-0.75 for cloud Gemini Robotics and 0.11-0.36 for the previous best on-device model; 7-task fast adaptation avg ~0.68 (on-device) vs ~0.80 (cloud) vs ~0.53. — [DeepMind blog](https://deepmind.google/discover/blog/gemini-robotics-on-device-brings-ai-to-local-robotic-devices/) [VENDOR CLAIM; chart-only, no parameter count, hardware, or latency numbers]
- No 2026 successor ("Gemini Robotics 2.0") found. — search summary of [pureai](https://pureai.com/Articles/2025/06/24/Google-Unveils-On-Device-AI-Model-for-Robots.aspx) [THIRD-PARTY]

### Inferences
- "Hz" in several tables (OFT Table III, GR00T README) is actions/s or inference/s depending on source; OFT's 77.9 Hz = 25 actions / 0.321 s, i.e. ~3 decisions per second. Compare per-decision latency (0.06-0.54 s) against the SNN's 0.4 ms tick, not headline "Hz".
- Open, locally-runnable options for a laptop-class SO-101 setup are SmolVLA (0.45B) and, with an NVIDIA GPU, pi0/pi0.5 and GR00T; OpenVLA-OFT needs data-center GPUs to fine-tune.

### Gaps
- OpenVLA / OFT / GR00T license terms not verified here.
- GR00T N1.5 numbers (params, Hz) not retrieved separately; N1.6 numbers are third-party.
- Gemini Robotics On-Device: parameters, hardware, Hz, power not disclosed; no third-party measurements found.
- Jetson Orin (non-Thor) GR00T latency not found.

---

## Q4. Precision and failure modes; benchmark numbers

### Takeaway
Published evidence on VLA fine positioning is thin but unflattering: a fine-tuned pi0 on Mobile ALOHA showed up to 2.2 cm / 12.4 degrees placement error and ~60% success on simple grasping (10 trials), PI itself states VLAs "struggle in the last millimeter of execution" (screw insertion 20% -> 65% only after online RL), and LIBERO-Plus shows high benchmark scores collapse under camera or initial-state changes (pi0: 94.2% -> 15.8% camera, 6.6% robot init). I found no VLA paper reporting sub-millimetre repeatability on a low-cost arm.

### Cited Findings

**Positioning error**
- Fine-tuned pi0 on Mobile ALOHA (fine-tuned on one NVIDIA H20 96 GB for 10 h): ~60% success on simple pick-up; high-precision placing error "up to 2.2 cm and 12.4 degrees" (Table III average: 2.2 cm, 12.4 deg); 10 trials per condition; zero-shot VLAs completed none of the grasps. Same paper quotes classical visual servoing aligning a screwdriver to M4-M8 screws with average error 0.8-1.3 mm (cited from another work). — [Industrial VLA study, arXiv 2509.23121 (Sep 2025)](https://arxiv.org/html/2509.23121) [MEASURED, small n=10]
- PI's own RL-token paper (Mar-Apr 2026): VLAs "often struggle in the last millimeter of execution: motions can be slow, successful completion may require pauses and retries, and small errors at critical stages ... can compound into failure". Tasks needing "millimeter or sub-millimeter precision": screw installation, zip-tie fastening, charger and Ethernet insertion. With a small actor-critic added on top of pi0.6 (50 Hz, 14-D actions), critical-phase speed improved up to 3x and one screw-insertion task went from 20% to 65% success after minutes-to-hours of real-robot RL. — [RLT paper, arXiv 2604.23073](https://arxiv.org/html/2604.23073); [PI RLT page](https://pi.website/research/rlt) [MEASURED, vendor-run]
- pi*0.6 failure modes (PI): small execution errors (wrong gripper position, missed grasp, knocked-over objects) compound; bad grasp causes later portafilter insertion failure. — [pi*0.6 blog](https://www.pi.website/blog/pistar06) [VENDOR]
- OpenVLA vs deterministic controller (University of Washington Bothell MS thesis, Aug 2025; WidowX 250 6-DoF, RealSense D415, Jetson AGX Orin, ROS 2; ISO 9283-style accuracy, repeatability, cycle time): OpenVLA-7B "underperform[s] compared to deterministic control systems in terms of accuracy, repeatability, and cycle time". The catalogue abstract gives no numeric values. — [UW thesis record](https://digital.lib.washington.edu/researchworks/items/9ea676ab-f431-4c21-bc80-a1ac280b84f4/full) [MEASURED, numbers not retrieved]

**Robustness benchmark (LIBERO-Plus, arXiv 2510.13626; CVPR 2026)**
- Seven perturbation axes (layout, camera, robot initial state, language, light, background, noise), 10,030 tasks. Success (%) original -> camera / robot-init / language / light / background / noise / layout:
  - OpenVLA 76.5 -> 1.1 / 4.1 / 26.8 / 4.4 / 25.3 / 19.3 / 31.6
  - OpenVLA-OFT 97.1 -> 59.7 / 37.2 / 81.5 / 85.8 / 92.4 / 76.7 / 77.1
  - pi0 94.2 -> 15.8 / 6.6 / 61.0 / 79.6 / 78.5 / 79.4 / 70.4
  - pi0-FAST 85.5 -> 66.4 / 24.8 / 63.3 / 73.0 / 67.7 / 75.8 / 70.3
  — [LIBERO-Plus (HTML)](https://arxiv.org/html/2510.13626v1) [MEASURED, simulation]
- Authors: "performance dropping from 95% to below 30% under modest perturbations"; models largely insensitive to language changes and "tend to ignore language instructions completely". — [LIBERO-Plus](https://arxiv.org/html/2510.13626v1)

**Latency / smoothness / generalization**
- Autoregressive VLAs (OpenVLA, pi0-FAST) are too slow for chunked high-rate control (3-5 Hz for OpenVLA; 750 ms between chunks for FAST) — [OFT paper](https://arxiv.org/html/2502.19645). Diffusion-style action experts can be slower than their size suggests: Diffusion Policy with 100 denoising steps ran at a lower frequency than pi0 with 4 steps. — [arXiv 2604.24447](https://arxiv.org/html/2604.24447)
- Execution jerk: RTC paper shows naive synchronous chunking has pauses and discontinuities at chunk boundaries; RTC is "smoother than all competing methods, including temporal ensembling". — [RTC paper](https://arxiv.org/html/2506.07339)
- Embodiment transfer: SmolVLA authors say pretraining on one robot type (SO-100) limits cross-embodiment generalization (their stated limitation). OpenVLA "struggle[s] with novel robot setups and require[s] fine-tuning" (OFT abstract). pi0 repo: "may or may not work for you". Zero-shot VLAs failed all grasps on Mobile ALOHA in the industrial study. — [SmolVLA](https://arxiv.org/html/2506.01844); [OFT](https://arxiv.org/html/2502.19645); [openpi](https://github.com/Physical-Intelligence/openpi); [arXiv 2509.23121](https://arxiv.org/html/2509.23121)
- Benchmark inflation: LIBERO fine-tuned scores 96.85% (pi0.5 openpi), 97.1% (OFT), 87.3% (SmolVLA 0.45B), whereas pi0 under camera change falls to 15.8%. — sources above.

### Inferences
- Position-accuracy numbers for VLAs are reported as task success or cm/deg error on bigger arms, not as mm repeatability; the only quantitative contrast with classical control is 0.8-1.3 mm visual servoing vs 22 mm / 12.4 deg for fine-tuned pi0 - different robots/tasks, so only indicative. A student should measure the SNN and any VLA baseline with the same ISO 9283-style metrics (accuracy, repeatability, cycle time) as the UW thesis.
- A narrow, fixed-viewpoint task is the VLAs' most favourable regime; LIBERO-Plus suggests their weakness is viewpoint/initial-state shift, which the fixed SO-101 setup avoids, but also which the SNN presumably has no tolerance for either (untested).

### Gaps
- No numeric accuracy/repeatability for OpenVLA from the UW thesis (full PDF not read).
- No sub-millimetre VLA positioning study on SO-100/SO-101 hardware found.
- Joint-angle (degree) accuracy of SmolVLA/pi0 on SO-101 not found.
- Servo-level jerk/jitter metrics (e.g., jerk in rad/s^3) for VLAs not found.

---

## Q5. Energy and power

### Takeaway
Direct joule-per-inference measurements for VLAs are scarce: one 2026 paper reports 6.0-8.15 J per pi0.5 inference (device-edge plans, ~0.7-0.9 s), another measured full-task energy of pi0 on 4090/Thor/Orin as 2.4/1.3/1.9 kJ (units ambiguous), and board power ceilings are 450 W (RTX 4090), 15-60 W (AGX Orin), ~130 W (Thor). A laptop CPU running the SNN would sit below these, but I found no measured SNN-vs-VLA energy comparison.

### Cited Findings
- EcoVLA (Beihang, arXiv 2608.15502, 16 Aug 2026): testbed RTX 4090 server + Jetson AGX Orin 32 GB robot; NVML (4090) and tegrastats (Orin) integrated over inference windows. For pi0.5 under a 1 s SLO: EcoVLA-fast 712 ms, 8.15 J, 2.45 actions/J; EcoVLA-opt 902 ms, 6.0 J, 3.3 actions/J. These are device-edge co-inference plans, not a single-board figure. — [EcoVLA](https://arxiv.org/html/2608.15502) [MEASURED]
- Zhou et al. (arXiv 2604.24447, 27 Apr 2026) physical-power-meter energy for pi0: RTX 4090 2.398 kJ @ 102.3 ms; Jetson Thor 1.282 kJ @ 246.0 ms; AGX Orin 1.866 kJ @ 920.6 ms; Intel B60 6.363 kJ @ 306.5 ms; Ascend 310P 2.618 kJ @ 818.0 ms (the "Energy(kJ)" column's measurement window is not defined in the text I read; likely a whole task run). Among platforms reaching ~5 Hz with pi0.5 on a Franka arm, Thor had best end-to-end energy efficiency, RTX 4090 shortest task time. Hardware cost column: 4090 $3,500, Thor $3,400, Orin $1,999. — [arXiv 2604.24447](https://arxiv.org/html/2604.24447) [MEASURED]
- System-level framing: a Koch v1.1 arm's servos draw ~22 W under rated torque, similar to a Jetson Orin NX's 20 W budget; Franka arm + controller up to 430 W vs ~400 W for an H100 NVL; "improving inference efficiency alone does not guarantee better system-level embodied efficiency". — [arXiv 2603.19131](https://arxiv.org/html/2603.19131)
- Jetson-PI reports running on an RTX 4090 cuts robot battery life ~6x versus Jetson Orin including mechanical power (whole-robot figure). — [Jetson-PI](https://arxiv.org/pdf/2607.12659) [via search summary]
- Board power specs: AGX Orin 64 GB configurable 15-60 W (NVIDIA buy page; 32 GB variant 15-40 W or 15-50 W depending on source); AGX Thor 40-130 W (Japanese launch article); RTX 4090 TDP 450 W (blogs; not NVIDIA spec sheet). — [NVIDIA buy Jetson](https://developer.nvidia.com/buy-Jetson); [Monoist](https://monoist.itmedia.co.jp/mn/articles/2508/26/news058_2.html); [blackboxoperations blog](https://erp.blackboxoperations.com/blog/agx-orin-64gb-vs-rtx) [DOCS / THIRD-PARTY]
- Quadric press release (29 May 2026) claims pi0.5 runs "6-10x more efficiently" than on Jetson Thor. — [AI Infra Summit PR](https://www.ai-infra-summit.com/press-releases/quadric-runs-pi-0-5-6-10-more-efficiently-than-nvidia-s-jetson-thor) [VENDOR CLAIM]

### Inferences
- Rough upper bound for pi0 on a 4090: 450 W x 0.073 s ~ 33 J per chunk (my estimate from TDP x latency, not a measurement; EcoVLA's pi0.5 6-8 J is lower because it is not board TDP-bound). Per control step (25-50 actions per chunk) that is ~0.1-1 J/action.
- For a student: the like-for-like energy comparison is "watts at the wall for the compute that closes the loop" - VLA: a 20-450 W GPU board (Orin/Thor/4090); SNN: a laptop CPU core, typically single-digit watts above idle (not measured here). The arm's own servo power (~20 W class) can dominate system energy.

### Gaps
- No measured power for SmolVLA on CPU/MPS (watts, J/inference) found.
- No measured Apple Silicon power for any VLA.
- RTX 4090 450 W figure is from blogs, not NVIDIA's spec page.
- No published SNN-vs-VLA energy comparison on robot arms found.

---

## Q6. Published comparisons: VLAs vs simple/classical controllers or small specialized policies on narrow tasks

### Takeaway
Papers by VLA authors consistently show VLAs ahead of ACT/Diffusion Policy trained on small data (SmolVLA +30 pts SO-100 multitask, GR00T 42.6% vs DP 10.2% at 10% data, OFT up to +15 pts), but the baselines are often single-task and the margins collapse when pretraining/multitask is removed (SmolVLA single-task 40% < ACT 48.3%; OpenVLA paper concedes Diffusion Policy is smoother and more precise on narrow dexterous tasks; the pi0 paper finds that from-scratch models were the strongest prior baselines). I found no head-to-head of a VLA against a hand-scripted/classical controller with numbers, except a UW thesis whose abstract says the deterministic controller wins on accuracy, repeatability and cycle time.

### Cited Findings
- SmolVLA paper: ACT (single-task) 48.3% vs SmolVLA 78.3% vs pi0 61.7% on SO-100 (3 tasks); SO-101 Pick-Place-Lego ACT 70/40 (in/out of distribution) vs SmolVLA 90/50. Ablation: SmolVLA trained single-task without robotics pretraining = 40%, multi-task = 51.7%, multi-task + pretraining = 78.3%. — [arXiv 2506.01844](https://arxiv.org/html/2506.01844)
- pi0 paper: ACT and Diffusion Policy trained only on fine-tuning datasets "of similar size to the individual datasets used in the ACT and Diffusion Policy experiments"; pi0 "generally outperforms other methods"; from-scratch pi0 is often much worse than pretrained pi0 on small data. — [pi0 paper](https://arxiv.org/html/2410.24164v4)
- OpenVLA: "OpenVLA is the only approach that achieves at least 50% success rate across all tested tasks"; "For narrower but highly dexterous tasks, Diffusion Policy still shows smoother and more precise trajectories." — [OpenVLA paper](https://arxiv.org/html/2406.09246)
- OFT: OFT+ beats Diffusion Policy and ACT trained from scratch by up to 15 points on real ALOHA tasks; ACT latency 0.058 s vs OFT+ 0.321 s and pi0 0.086 s (A100). — [OFT paper](https://arxiv.org/html/2502.19645)
- GR00T N1: Diffusion Policy needs more data: 10.2% (10% of data) / 46.4% (full) vs GR00T 42.6% / 76.8% (real GR-1); sim 100 demos: DP 33.4% vs GR00T 45.0%. — [arXiv 2503.14734](https://arxiv.org/html/2503.14734)
- Small L1-regression heads can beat diffusion heads after fine-tuning (VLA-Adapter appendix, LIBERO-Long ~91.6% avg for L1; OFT cited as explanation). — [VLA-Adapter](https://arxiv.org/pdf/2509.09372) [via search summary]
- Deterministic-control comparison: UW thesis (Aug 2025) finds OpenVLA-7B behind a fine-tuned deterministic controller on accuracy, repeatability and cycle time (pick-and-place, WidowX 250 + Jetson AGX Orin); no numbers in the abstract. — [UW record](https://digital.lib.washington.edu/researchworks/items/9ea676ab-f431-4c21-bc80-a1ac280b84f4/full)
- Classical servoing reference point: average error 0.8-1.3 mm for visual servoing on M4-M8 screws (cited inside the industrial VLA paper). — [arXiv 2509.23121](https://arxiv.org/html/2509.23121)
- Meta-World avg success: Diffusion Policy 10.5%, SmolVLA 57.3% (note DP number copied from Chi et al. 2023, different training regime). — [arXiv 2506.01844](https://arxiv.org/html/2506.01844)
- Hardware-dependence: small policies need not be faster: Diffusion Policy at 100 denoising steps had lower inference frequency than pi0 with 4 steps on the same hardware class. — [arXiv 2604.24447](https://arxiv.org/html/2604.24447)

### Inferences
- Fair framing for the student: the SNN is not competing with VLAs on generality, language or novel objects (VLA strengths) but on one narrow, fixed task where ACT-type single-task policies are the proper "small policy" baseline; ACT's measured 0.058 s per 25-action chunk (A100) is already ~145x the SNN tick.
- The VLA literature tests with demonstrations (5-300 per task) and success rates from 10-trial evaluations; the SNN has 0 demos, so data-efficiency comparisons should be reported as "demos required" and "wall-clock to first working controller".
- Any claim "SNN beats VLA" must specify task, trial count, and VLA fine-tuning budget; the VLA numbers above have wide uncertainty (n=10 per cell gives +/- ~15-30 pp 95% intervals - my calculation).

### Gaps
- No 2026 SO-101 head-to-head of a VLA vs a scripted/inverse-kinematics baseline with numbers.
- The UW thesis PDF (numeric results) was not read.
- No published neuromorphic/SNN vs VLA robotic-arm comparison found.
- ACT / Diffusion Policy parameter counts not retrieved in this pass.
