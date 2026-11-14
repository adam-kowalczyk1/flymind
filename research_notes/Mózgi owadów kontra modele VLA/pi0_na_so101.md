# Running a ready-made pi0-family VLA on a single SO-101 follower arm (no leader arm), student with Apple Silicon Mac, as of 2026-11-03

Scope note: research date 2026-11-03. Latest LeRobot on PyPI found: 0.6.1 (3 Aug 2026). Docs pages fetched are the "latest" docs. Items I could not verify are marked UNVERIFIED or placed under Gaps. Search tool summaries were treated cautiously; where a number came only from a search-engine summary (not from a page I read), I say so.

## 1. Does LeRobot support pi0 / pi0.5 / pi0-FAST for SO-100/SO-101? Official workflow and version

### Takeaway
Yes. LeRobot has three first-class policy types (`pi0`, `pi05`, `pi0_fast`) installed with the `[pi]` extra, trained with `lerobot-train` and deployed with `lerobot-rollout` (0.6.x). The official docs show fine-tuning on LIBERO, not on SO-101, but several community SO-101 pi0/pi0.5 checkpoints on the Hub show the exact same workflow works on SO-101 (all were trained on a leader-arm-teleoperated dataset).

### Cited Findings
- Latest LeRobot on PyPI: 0.6.1 (3 Aug 2026); 0.6.0 (6 Jul 2026); 0.5.1 (7 Apr 2026); 0.5.0 (9 Mar 2026). Requires Python >= 3.12. — [PyPI lerobot](https://pypi.org/project/lerobot/)
- Install: `pip install 'lerobot[pi]'` gives Pi0 / Pi0.5 / Pi0-FAST deps; Feetech motor extra `[feetech]` is needed for SO100/SO101. macOS/Windows get the PyPI default torch wheel (MPS/CPU on Mac). — [LeRobot installation docs](https://huggingface.co/docs/lerobot/installation)
- pi0: `--policy.type=pi0`, base checkpoints `lerobot/pi0_base` and `lerobot/pi0_libero`; pi0 predicts absolute actions by default, optional relative actions (`--policy.use_relative_actions=true`, gripper excluded). Docs example trains on `--policy.device=cuda`, `--policy.dtype=bfloat16`, `gradient_checkpointing=true`, `batch_size=32`, 3000 steps. `train_expert_only=true` freezes the VLM to save memory. — [LeRobot pi0 docs](https://huggingface.co/docs/lerobot/pi0)
- pi0.5: `--policy.type=pi05`, base `lerobot/pi05_base`; requires the gated `google/paligemma-3b-pt-224` tokenizer (accept licence on Hub, `hf auth login`); normalizes state/action with quantiles so `meta/stats.json` needs q01/q99 (older datasets fail with a ValueError until stats are recomputed via `lerobot-edit-dataset ... recompute_stats`). Docs example is "sized for a single 80 GB GPU" (batch 64). LeRobot pi0.5 LIBERO average 97.5% vs OpenPI reference 96.85%. — [LeRobot pi0.5 docs](https://huggingface.co/docs/lerobot/pi05)
- pi0-FAST: `--policy.type=pi0_fast`, base `lerobot/pi0fast-base`, FAST tokenizer `lerobot/fast-action-tokenizer` (can train own with `lerobot-train-tokenizer`); autoregressive with KV cache; docs claim up to 5x faster training than pi0. LeRobot's own LIBERO reproduction of pi0-FAST is weaker (average 82.5%). — [LeRobot pi0-FAST docs](https://huggingface.co/docs/lerobot/pi0fast)
- Loading nuance: `--policy.path` loads weights + checkpoint config (feature names from checkpoint, needs `--rename_map` if camera keys differ); `--policy.pretrained_path` loads weights only, takes features from your dataset and resets settings such as `n_action_steps` to defaults. — [LeRobot pi0.5 docs](https://huggingface.co/docs/lerobot/pi05)
- Deployment: `lerobot-rollout --strategy.type=base --policy.path=... --robot.type=so100_follower ...`; all strategies support `--inference.type=rtc` (real-time chunking) "for smooth execution with slow VLA models (Pi0, Pi0.5, SmolVLA)". — [LeRobot imitation learning on real robots](https://huggingface.co/docs/lerobot/il_robots)
- The `lerobot/pi0_base` model card says it is a "Base model to fine tune on your specific use case"; example inference uses `so100_follower`. License on card: gemma. — [lerobot/pi0_base](https://huggingface.co/lerobot/pi0_base)
- Real community SO-101 pi0 checkpoints exist (details in section 2), trained with LeRobot 0.5.2 and 0.6.1 respectively. — [Jingyi-Z/pi0_so101](https://huggingface.co/Jingyi-Z/pi0_so101); [hyf010124/pi0_so101_Pi0727](https://huggingface.co/hyf010124/pi0_so101_Pi0727)
- Reproducibility caution: LeRobot GitHub issues report that fine-tuned pi0/pi0.5 LIBERO success rates were lower than advertised for some users (one reports 41.8% on libero-goal vs 98.8% openpi; another ~10-20% below). These are simulation benchmark reports, not SO-101. — [Issue #2114](https://github.com/huggingface/lerobot/issues/2114); [Issue #952](https://github.com/huggingface/lerobot/issues/952) (from search-engine summary, issue bodies not read in full)
- Practical-blog note (single source, dated 23 Aug 2026): pi0.5 needs LeRobot v3.0-format datasets; 0.6.0 moved deployment to `lerobot-rollout`. — [ay-robots blog](https://www.ay-robots.com/blog/en/how-to-train-pi0-5-on-your-own-robot-data)

### Inferences
- The "official workflow" for a new robot like SO-101 is: record dataset (LeRobotDataset v3) -> `lerobot-train --policy.path=lerobot/pi05_base` (or pi0_base / pi0fast-base) on a big GPU -> `lerobot-rollout --policy.path=<your repo>`. SO-101 is not special-cased; it is a 6-dim state/6-dim action robot, padded to 32 internally (stated for LIBERO's 7-dim action: "padded to 32 internally").
- The documented robot type string changed across versions (`so100_follower`/`so101_follower` in docs, `so_follower` in two community cards). Check your installed version's `lerobot-rollout --help`.

### Gaps
- No official LeRobot doc page showing pi0/pi0.5 trained on an SO-101 end to end with success rates.
- I did not retrieve LeRobot release notes for 0.6.x to confirm which pi0 bugs were fixed when.

## 2. Zero-shot: can a pretrained pi0/pi0.5 base control an SO-101 without fine-tuning? Community checkpoints? SmolVLA?

### Takeaway
No credible evidence that a base pi0/pi0.5 checkpoint works zero-shot on SO-101; both Physical Intelligence and Hugging Face describe the base models as fine-tuning bases, and SO-101/SO-100 was not part of the pretraining embodiments. Public SO-101 fine-tuned pi0/pi0.5 checkpoints exist but none report quantitative results; SmolVLA (pretrained on community SO-100 data) is the realistic "ready-made" VLA for this arm but also needs fine-tuning (HF recommends ~50 episodes).

### Cited Findings
- openpi: base checkpoints (`pi0_base`, `pi0_fast_base`, `pi05_base`) are "for fine-tuning", pretrained on "10k+ hours of robot data"; fine-tuned "expert" checkpoints "may or may not work on your particular robot"; main use case is fine-tuning on your own platform with small/medium data. SO-100 is not mentioned. — [openpi README](https://github.com/Physical-Intelligence/openpi)
- Physical Intelligence's own statement (via search summary of their blog): pi0 is designed for fine-tuning although it can be used zero-shot for tasks in the pretraining data; checkpoints may be sensitive to overall robot setup. — [PI openpi blog](https://www.physicalintelligence.company/blog/openpi)
- pi0 was pretrained on 8 embodiments (UR5e, bimanual UR5e, Franka, bimanual Trossen, bimanual ARX, mobile Trossen, mobile Fibocom) — no SO-100/SO-101. — [LeRobot pi0 docs](https://huggingface.co/docs/lerobot/pi0)
- The zero-shot exceptions are robot-specific fine-tuned checkpoints (e.g., pi0-FAST-DROID "simple tabletop tasks zero-shot in new scenes on the DROID platform", pi0.5-DROID) — these are for the DROID Franka setup, not SO-101. — [openpi README](https://github.com/Physical-Intelligence/openpi)
- I found no GitHub issue, HF forum thread, or blog reporting successful zero-shot control of SO-100/SO-101 by `pi0_base`/`pi05_base`. Searches for such reports returned only model cards and generic docs. (Absence of evidence; see Gaps.)
- Community SO-101 pi0 checkpoints (all fine-tuned from `lerobot/pi0_base`, none with reported eval results):
  - `Jingyi-Z/pi0_so101`: 50 episodes / 33,687 frames @30 fps, task "Pick up the red ball and place it in the plastic bowl", cameras `wrist` + `top` at 640x480, 3,000 steps, batch size 4, LR 2.5e-5, LeRobot 0.5.2, robot type `so_follower`. Card states no eval results. — [Jingyi-Z/pi0_so101](https://huggingface.co/Jingyi-Z/pi0_so101)
  - `hyf010124/pi0_so101_Pi0727`: 80 episodes / 35,401 frames, task "Grab the cube into the grey box", three cameras (`front`, `right`, `up`) 480x640, 20,000 steps, batch 8, LeRobot 0.6.1. No eval results. — [hyf010124/pi0_so101_Pi0727](https://huggingface.co/hyf010124/pi0_so101_Pi0727)
- Community SO-101 pi0.5 checkpoint: `Cache-SCA/pi05_teleop_sort_block` from `lerobot/pi05_base`; dataset `CoRL2026-CSI/SO101-teleop_sort_blocks_100epi` (100 human teleop episodes, 94,568 frames, 30 fps); 18,500 steps, effective batch 256, 4 GPUs (model unspecified); cameras `base_0_rgb` (top), `left_wrist_0_rgb` (wrist) and an EMPTY `right_wrist_0_rgb` placeholder for the single-arm setup; 224x224; no quantitative success rate reported. Sibling: `Cache-SCA/pi05_teleop_close_pot`. — [Cache-SCA/pi05_teleop_sort_block](https://huggingface.co/Cache-SCA/pi05_teleop_sort_block)
- A GitHub project applies pi0.5 + RL-Token to a single SO-101 "cell" (follower + leader + two cameras `top`/`wrist`, 640x480@30), suggests 30-50 good demos for a single task; reports no success rates; leader arm used. — [Zhengsw03/RL-Token-Pi05-open](https://github.com/Zhengsw03/RL-Token-Pi05-open)
- A research paper (CARE, arXiv 2609.24118) reportedly tests pi0 on a dual-arm SO-101 on four tasks; baseline pi0 averaged ~30.8% success, CARE raised it to ~50.0% (100 trials/task). UNVERIFIED: this comes from a search-engine summary; the PDF text could not be extracted by my fetch tool. — [arXiv 2609.24118](https://arxiv.org/pdf/2609.24118)
- SmolVLA (450M params, ~100M action expert): pretrained on 487 community datasets for the SO100 arm, ~10M frames, <30k episodes, 30 FPS. "SmolVLA is a base model, so fine-tuning on your own data is required for optimal performance"; recommended ~50 episodes (SmolVLA paper dataset: 50 episodes, 5 cube positions x 10); a 25-episode attempt "was not enough". 20k steps ~4 h on a single A100. — [HF blog SmolVLA](https://huggingface.co/blog/smolvla); [LeRobot SmolVLA docs](https://huggingface.co/docs/lerobot/smolvla)
- Community SmolVLA SO-101 checkpoints exist (e.g., `sgzsh269/smolvla_so101_pickplace`, `phawitbinabik/smolvla_so101-pick-place`, `Harrysunshine/so101-smolvla-9task`, plus a pi0 counterpart `Harrysunshine/so101-pi0-9task` named but not directly fetched); dataset `lerobot/svla_so101_pickplace` is public. — [search result: pi0 so101 Hub listing](https://huggingface.co/Jingyi-Z/pi0_so101) ; [lerobot/svla_so101_pickplace](https://huggingface.co/datasets/lerobot/svla_so101_pickplace/tree/main)
- One model card notes a 100-episode SO-101 model is "sensitive to camera/lighting domain shift" (via search summary, card not fetched). UNVERIFIED.

### Inferences
- A community checkpoint is NOT zero-shot "for your arm": it is tied to its authors' camera positions, calibration, object, scene and task text. Re-using e.g. `Jingyi-Z/pi0_so101` on a different desk, different cameras or differently calibrated arm would likely fail or behave unpredictably; plan on it only as an initialization (`--policy.path=<community repo>` fine-tune) rather than a drop-in.
- Practical "ready-made" ladder: (a) try a community SO-101 pi0/SmolVLA checkpoint only if you can replicate its camera names/placement; (b) otherwise fine-tune `smolvla_base` (cheap) or `pi05_base`/`pi0_base` (expensive) on ~50 of your own episodes.

### Gaps
- No quantitative success rates for any public SO-101 pi0/pi0.5 checkpoint found.
- No GitHub issue/forum/Reddit/Discord post explicitly testing `pi0_base` zero-shot on SO-100/101 found (search tool coverage of Reddit/Discord is poor; Discord is not indexed).
- CARE paper numbers not verified against the PDF.

## 3. Compute: GPU memory, Apple Silicon (MPS/CPU), cloud and remote inference, costs

### Takeaway
Inference of pi0/pi0.5 needs a >8 GB NVIDIA GPU (RTX 4090 class recommended by openpi); full fine-tuning needs >70 GB (A100/H100 80 GB); openpi LoRA >22.5 GB. Nothing I found shows pi0/pi0.5 running at usable speed on Apple Silicon; the practical architecture is: arm + cameras on the Mac, policy on a remote CUDA GPU (LeRobot async inference server, or openpi websocket server). A fine-tune run costs on the order of a few to ~12 USD of rented GPU time.

### Cited Findings
- openpi memory requirements: inference > 8 GB (e.g. RTX 4090), LoRA fine-tuning > 22.5 GB (RTX 4090 class), full fine-tuning > 70 GB (A100 80 GB / H100); `fsdp_devices` can split memory across GPUs; tested on Ubuntu 22.04, "we do not currently support other operating systems"; no Mac/MPS support mentioned. — [openpi README](https://github.com/Physical-Intelligence/openpi)
- openpi supports remote inference: the model runs on a server and streams actions to the robot over a websocket (`docs/remote_inference.md`). — [openpi README](https://github.com/Physical-Intelligence/openpi)
- LeRobot async inference doc states "PI0 occupies 14GB of memory at inference time, while SmolVLA requires only ~2GB" (this statement may predate newer pi0 versions). — [LeRobot async inference docs](https://huggingface.co/docs/lerobot/async)
- LeRobot async inference: `python -m lerobot.async_inference.policy_server --host --port` on a separate machine and `python -m lerobot.async_inference.robot_client --robot.type=so100_follower ... --policy_type=... --pretrained_name_or_path=... --policy_device=cuda|mps|xpu|cpu --actions_per_chunk=50 --chunk_size_threshold=0.5`; works with all LeRobot policies; install with `[async]` extra. Docs example uses `policy_device=mps` on the server for SmolVLA. — [LeRobot async inference docs](https://huggingface.co/docs/lerobot/async)
- LeRobot training docs: `policy.device=mps` can train ACT on Apple silicon; lists Google Colab (ACT notebook) and Hugging Face Jobs (`--job.target=a10g-small`, pay per second) for cloud training. — [LeRobot il_robots docs](https://huggingface.co/docs/lerobot/il_robots)
- pi0.5 docs: first example "sized for a single 80 GB GPU"; second recipe freezes the VLM (`freeze_vision_encoder=true`, `train_expert_only=true`) for less memory "at some cost in success rate". — [LeRobot pi0.5 docs](https://huggingface.co/docs/lerobot/pi05)
- Blog (23 Aug 2026, single source): pi0.5 fine-tune 3-6 h on A100/H100 tier, 30,000 steps, ~4-12 USD per run at ~1.2-2.0 USD/h; inference 485 ms per action step with ACT 20 ms for comparison; advice to validate task learnability with a cheaper 24 GB policy first. — [ay-robots blog](https://www.ay-robots.com/blog/en/how-to-train-pi0-5-on-your-own-robot-data)
- Cloud price snapshots (aggregators, dates vary Mar-Sep 2026): RunPod H100 80GB from ~1.99 USD/h; A100 80GB ~1.19-1.49 USD/h; RTX 4090 ~0.34-0.74 USD/h; Lambda H100 ~3.3-4.3 USD/h. Verify live. — [RunPod pricing](https://www.runpod.io/gpu-cloud/pricing); [Jarvislabs A100 price](https://jarvislabs.ai/blog/a100-price)
- SmolVLA authors say it can run on CPU or a MacBook (no benchmark numbers). A third-party MLX port of SmolVLA reports 110.75 ms (MLX) vs 204.58 ms (PyTorch-MPS) per 50-action chunk on an Apple M5 Pro (single self-reported number, search summary). — [HF blog SmolVLA](https://huggingface.co/blog/smolvla); [HF discussion smolvla_base #24](https://huggingface.co/lerobot/smolvla_base/discussions/24)
- General MPS caveats: bfloat16 support on MPS has historically been unreliable (depends on PyTorch/macOS versions); fp32 roughly doubles memory vs half precision; memory pressure on unified memory causes swapping. — [HF discussions on bfloat16 MPS](https://huggingface.co/shenzhi-wang/Llama3-8B-Chinese-Chat/discussions/13)

### Inferences
- pi0 is ~3B-4B params (card shows ~4B in F32 safetensors). In fp32 that is ~14-16 GB of weights alone, so a 16 GB Mac is unlikely to run it; 32-64 GB Macs could load it, but latency for flow-matching denoising (10 steps by default, my knowledge) on MPS is probably seconds per chunk. I found NO measurement. Treat "pi0 on a MacBook" as unverified and probably impractical; use remote GPU.
- Recommended topology for a student: Mac (robot USB, cameras, `lerobot-rollout`/`robot_client`) <-> LAN/internet <-> rented 24-80 GB CUDA box (policy server). With chunk size 50 and ~0.5 threshold, ~0.3-0.5 s network+inference latency is tolerable because chunks are executed open-loop; RTC (`--inference.type=rtc`) is meant for exactly this.
- Cheapest viable path: fine-tune on RunPod/HF Jobs (A100 80 GB, few hours, roughly 5-15 USD incl. failed attempts) and serve inference from a 24 GB RTX 4090 pod (~0.3-0.7 USD/h) or from a local friend's NVIDIA PC; budget perhaps 20-60 USD total for a first experiment. This cost estimate is my extrapolation from the sources above.

### Gaps
- No measured pi0/pi0.5/pi0-FAST latency on Apple Silicon (MPS or CPU) found; LeRobot pi0 may also hard-require CUDA ops (not checked).
- No actual LeRobot-pi0 LoRA/PEFT VRAM number found (openpi's 22.5 GB is for its JAX path).
- No measured network-latency experience for LeRobot async with pi0 over the internet.

## 4. Demonstrations without a leader arm

### Takeaway
LeRobot officially supports keyboard, gamepad and phone (iOS/Android) teleoperation; phone teleop to SO-100/SO-101 is documented with end-effector IK. Kinesthetic teaching (torque off, hand-guide) is NOT an official workflow but is straightforward in principle. Simulation (MuJoCo Menagerie SO-101) exists but sim-to-real transfer of a pi0 policy is unproven. Scripted/classical-controller demos are the most reliable leader-free route for a simple reach/pick task. Typical need: 50 episodes (more if varied).

### Cited Findings
- LeRobot docs: during data collection "you'll use a teleoperation device, such as a leader arm or keyboard"; official teleoperators page lists keyboard, leader arm, gamepad, phone behind a common Teleoperator interface. — [LeRobot il_robots](https://huggingface.co/docs/lerobot/il_robots); [LeRobot teleoperators API](https://huggingface.co/docs/lerobot/main/api/teleoperators)
- Phone teleop: `pip install lerobot[phone]`; iOS via HEBI Mobile I/O app (ARKit pose), Android via `teleop` PyPI package (WebXR); phone pose -> end-effector deltas -> IK (Placo/Pinocchio) -> joint targets; example scripts `examples/phone_to_so100/{teleoperate,record,replay,evaluate}.py` work with SO100/SO101 URDF (`SO101/so101_new_calib.urdf` copied from SO-ARM100 repo); safety via `EEBoundsAndSafety` (workspace bounds, `max_ee_step_m`); gripper is velocity-controlled (buttons/analog). Recorded dataset stores absolute end-effector observations and actions (per docs). — [LeRobot phone teleop docs](https://huggingface.co/docs/lerobot/phone_teleop)
- Keyboard end-effector teleop (`KeyboardEndEffectorTeleop`, `keyboard_ee`) was added for `So100FollowerEndEffector` (code commit; docs not found). Third-party XLeRobot docs show an SO-100/SO-101 keyboard end-effector IK example. — [LeRobot commit #1289 (mirror)](https://gitea.d-robotics.cc/chao.wu/Lerobot/commit/6007a221f0d5e425e3c212e079688fa80f96a268); [XLeRobot SO101 docs](https://xlerobot.readthedocs.io/en/latest/_sources/software/getting_started/SO101.md.txt)
- macOS note: keyboard TELEOPERATION needs a global key backend; on macOS this requires Accessibility/Input Monitoring permission; recording control keys (n/r/q, arrows) fall back to terminal input. — [LeRobot il_robots](https://huggingface.co/docs/lerobot/il_robots)
- A Korean guide (via search summary) says keyboard/gamepad can replace the leader arm but "demonstration quality drops", so leader arm gives better imitation learning (UNVERIFIED, page not read). — [wikidocs LeRobot v0.6.1 guide](https://wikidocs.net/435287)
- Kinesthetic teaching: I found no documentation or community guide for recording LeRobot datasets by hand-guiding an SO-101. The SO-101 config has `disable_torque_on_disconnect` (default on), which is unrelated to teaching. — [LeRobot SO-101 docs summary (mintlify mirror)](https://www.mintlify.com/huggingface/lerobot/robots/so-101)
- Simulation: MuJoCo Menagerie has an SO-101 MJCF model (`robotstudio_so101`: `so101.xml`, `scene.xml`, `scene_box.xml`; derived from SO-ARM100 `so101_new_calib.xml`; Apache-2.0; needs MuJoCo >= 3.1.3). — [mujoco_menagerie robotstudio_so101](https://github.com/google-deepmind/mujoco_menagerie/tree/main/robotstudio_so101)
- LeRobot's `gym_hil` (Gymnasium + MuJoCo human-in-the-loop envs; keyboard and gamepad variants e.g. `PandaPickCubeGamepad-v0`, `PandaPickCubeKeyboard-v0`) is Franka Panda based; I found no evidence it ships an SO-101 env. — [gym-hil PyPI](https://pypi.org/project/gym-hil/); [LeRobot hilserl_sim docs](https://huggingface.co/docs/lerobot/hilserl_sim)
- A public simulated SO-101 pick-cube LeRobot dataset exists (`Cache-SCA/isaaclab-pickplacecube-so101-1000epis-no-randomize_10fps`, 1000 episodes Isaac Lab, 10 fps) and NVIDIA docs describe an SO-101 sim-to-real LeRobot workflow (Isaac Lab); not verified in detail. — [HF discussions page](https://huggingface.co/Cache-SCA/isaaclab-pickplacecube-so101-1000epis-no-randomize_10fps/discussions); [NVIDIA sim-to-real SO-101](https://docs.nvidia.com/learning/physical-ai/sim-to-real-so-101/latest/04-lerobot.html)
- Follower-only SO-100 kits are sold (Phospho) and VR headset control is mentioned for them (search summary). — [uofrobotics/SO-ARM101](https://github.com/uofrobotics/SO-ARM101)
- Amount of data: LeRobot recommends "at least 50 episodes, with 10 episodes per location", fixed cameras, consistent grasping, and the rule of thumb that you should be able to do the task from camera images alone. SmolVLA authors: 25 episodes insufficient, 50 (5 positions x 10) worked. Community pi0 cards used 50-100 episodes (30-35k to 95k frames). — [LeRobot il_robots](https://huggingface.co/docs/lerobot/il_robots); [LeRobot SmolVLA docs](https://huggingface.co/docs/lerobot/smolvla); model cards in section 2.

### Inferences (recommended options, ranked for a student with no leader arm)
1. Scripted/classical controller as the demonstrator (preferred if the task is a simple reach/touch/pick at varied positions): use the Mac to drive the SO-101 with an IK or hand-written controller (your other "controller" under comparison could generate it) while recording through `lerobot-record`-style loop (`robot.get_observation()` + `robot.send_action(action)` + dataset `add_frame`, following the Python API shown in the docs). Caveat: the VLA then imitates the scripted controller, so "VLA beats controller" cannot be concluded; at best it can match it; and dataset provenance must be disclosed in the comparison.
2. Phone teleop (documented, SO101 URDF provided): good for pick-and-place; expect lower smoothness than a leader arm; record at 30 fps; keep the same joint-space action format you will use at inference (the docs' phone dataset records end-effector actions; pi0 would then output EE actions, requiring an EE->joint IK step at deployment; alternatively convert to joint targets by logging IK output). Verify which action space is stored before training.
3. Kinesthetic teaching (UNVERIFIED, my design): disable torque on the follower (Feetech bus `disable_torque`), guide by hand, log joint positions as `observation.state`, and set `action[t] = state[t+k]` (small k, e.g. 1-3 frames). Risks: SO-101 gears are not backdrivable-friendly (STS3215) and a hand/arm appears in camera images (distribution shift versus autonomous execution) — use a wrist-camera-light setup or mask/crop; gripper force can't be demonstrated naturally.
4. Keyboard/gamepad EE teleop: works but slow and jerky; fine for reach tasks, poor for dexterous grasp.
5. Simulation: MuJoCo Menagerie SO-101 is available but you would have to build your own env, rendering and teleop wrapper; sim->real for a pi0 image-conditioned policy without real data is unlikely to work out-of-box (UNVERIFIED, no source). Use sim only for debugging the controller/IK pipeline.
- Plan on ~50 clean episodes per task variant as the minimum (consistent with LeRobot and SmolVLA guidance); for pi0/pi0.5 community cards used 50-100. A 'reach to a ball at N positions' task: 10 episodes per position.

### Gaps
- No tested guide for kinesthetic teaching with LeRobot found.
- No source on whether `gym_hil` or any LeRobot sim env natively supports SO-101 with gamepad.
- No quantitative comparison of dataset quality (keyboard/phone vs leader arm) found beyond one unverified qualitative remark.

## 5. Fair comparison design (VLA vs another controller on the same arm)

### Takeaway
No source gives a standard protocol for this; the following is my own design built on LeRobot's structure (`lerobot-rollout` with a policy, vs. your own controller loop calling the same `robot.send_action`). The key fairness rules: identical robot object, cameras, safety clamp, task, start states and trial randomization, with a single wrapper that gates every action.

### Cited Findings
- LeRobot's robot interface is `robot.get_observation()` / `robot.send_action(action)`; the policy and any teleoperator/controller only produce `action` dicts of joint targets (shown in the docs' API example). — [LeRobot il_robots](https://huggingface.co/docs/lerobot/il_robots)
- `lerobot-rollout` strategies: `base` (no recording), `sentry` (continuous recording with upload; "useful for large-scale evaluation"), `episodic`, `highlight`, `dagger`. — [LeRobot il_robots](https://huggingface.co/docs/lerobot/il_robots)
- Phone teleop pipeline provides `EEBoundsAndSafety` (workspace bounds, per-step limit) as a reusable processor pattern; LeRobot has a Processor pipeline guide ("Processors for Robots and Teleoperators"). — [LeRobot phone teleop docs](https://huggingface.co/docs/lerobot/phone_teleop)
- Latency reference points (single blog source): pi0.5 485 ms per action step vs ACT 20 ms. — [ay-robots blog](https://www.ay-robots.com/blog/en/how-to-train-pi0-5-on-your-own-robot-data)
- LIBERO reproduction discrepancies reported by LeRobot users show that headline success rates may not replicate; use your own repeated trials. — [Issue #2114](https://github.com/huggingface/lerobot/issues/2114)

### Inferences (proposed protocol; not from a source)
- Controller switch: write one `run_trial(controller, target)` harness. A `Controller` has `act(obs) -> joint_target_dict`. Implementations: `VLAController` (local `policy.select_action` or remote client with action queue) and `OtherController` (e.g., the connectome SNN or IK baseline). Everything downstream is shared: a single `SafetyFilter` (joint limits, max joint delta per step, max torque/current, workspace bounds, e-stop key) applied to the action BEFORE `robot.send_action`, the same control rate (30 Hz) and the same camera objects/frames. Log (timestamp, obs, raw action, filtered action, safety-clamp flag) for each step.
- Latency fairness: run the VLA with its natural chunking (async/RTC) but log inference latency separately; either (a) give both controllers the same observation timestamp budget, or (b) report two results: "as deployed" and "latency-matched" (hold the faster controller's actions with an artificial delay equal to VLA latency).
- Task and start states: fixed target set (e.g. 8-10 marked positions covering the workspace, including positions NOT in VLA training data and a held-out subset); fixed start pose via a "home" routine; the VLA is trained only on data that does not contain test-position episodes if you want to measure generalization, otherwise state clearly that test positions are within the training distribution.
- Randomization/blinding: pre-generate a randomized, balanced (blocked) schedule of (controller, target) pairs with a seeded RNG; the operator who places the object and scores success should not see which controller is running (controller label hidden in a sealed file; both controllers launched from the same command with a code letter); alternate in blocks to cancel drift (motor heating, lighting, battery/power-supply changes). Use fixed per-trial timeout (e.g. 30-60 s) and the same reset procedure.
- Metrics: success rate with Wilson (binomial) confidence intervals (>= 20-30 trials per controller for even coarse conclusions; paired design by target); final position error (mm) of the end-effector/gripper tip vs the target, measured by an independent method (e.g., overhead camera with fiducial marker, not the controller's own state); time-to-target; number of safety-filter interventions; collisions; path length/jerk; inference latency distribution (p50/p95) and control-loop jitter; compute (device, GPU model, power draw via nvidia-smi or wall meter, Wh per trial; parameters count); human effort (number of demos, collection time, training GPU-hours and cost) — the cost to get a VLA working is itself a result.
- Report the confound that the VLA's training demonstrations came from a particular demonstrator (scripted/phone) and report what the controller baseline had access to (e.g., the same cameras vs privileged state).

### Gaps
- No published protocol or paper specifically for comparing a VLA against a classical/bio-inspired controller on SO-101 found (I did not search the literature for this).

## 6. Camera requirements for pi0 on SO-101

### Takeaway
pi0/pi0.5 in LeRobot are multi-camera models that accept a few image views and tolerate a missing camera via "empty camera" placeholder; community SO-101 checkpoints use 2 cameras (wrist + top/front, 640x480 @30 fps) and one used 3. The model resizes to 224x224 internally. Camera names/keys at inference must match training.

### Cited Findings
- pi0.5 LIBERO setup uses two cameras (agentview + wrist), each resized to 224x224; `--policy.empty_cameras=1` pads a missing third camera; mismatched keys require `--rename_map` (or are taken from the dataset when using `pretrained_path`). — [LeRobot pi0.5 docs](https://huggingface.co/docs/lerobot/pi05)
- `Jingyi-Z/pi0_so101`: two cameras `wrist` and `top`, 3x480x640 each, `observation.state` (6,), `action` (6,); camera names must match training. — [Jingyi-Z/pi0_so101](https://huggingface.co/Jingyi-Z/pi0_so101)
- `hyf010124/pi0_so101_Pi0727`: three cameras `front`, `right`, `up`, 480x640. — [hyf010124/pi0_so101_Pi0727](https://huggingface.co/hyf010124/pi0_so101_Pi0727)
- `Cache-SCA/pi05_teleop_sort_block`: top + wrist at 224x224 plus one empty slot (`right_wrist_0_rgb`). — [Cache-SCA/pi05_teleop_sort_block](https://huggingface.co/Cache-SCA/pi05_teleop_sort_block)
- RL-Token pi0.5 project: two OpenCV cameras (`top`, `wrist`), 640x480@30, MJPG, 3 s warm-up because "a camera can open without delivering frames otherwise". — [Zhengsw03/RL-Token-Pi05-open](https://github.com/Zhengsw03/RL-Token-Pi05-open)
- LeRobot data-collection tip: keep cameras fixed; object must be visible to the camera; "you should be able to do the task yourself by only looking at the camera images". — [LeRobot il_robots](https://huggingface.co/docs/lerobot/il_robots)
- Blog example uses one overhead camera and says no required camera count is stated. — [ay-robots blog](https://www.ay-robots.com/blog/en/how-to-train-pi0-5-on-your-own-robot-data)
- SmolVLA camera mapping: image 1 top-down, image 2 wrist, 3+ additional. — [HF blog SmolVLA](https://huggingface.co/blog/smolvla)

### Inferences
- Minimum practical: one fixed front/top camera that sees both arm and target (the model can work with a single camera plus empty slots, but the wrist camera helps grasp/reach precision, as every community checkpoint used it). A good student setup: 1 wrist (USB, on gripper) + 1 top/front fixed, 640x480@30 fps; the cost of two cheap USB cameras is small.
- On macOS, two OpenCV USB cameras plus the Feetech serial adapter may hit USB bandwidth limits; use MJPG and lower resolution if frames drop (supported by the RL-Token README advice on MJPG, but macOS-specific behavior is untested by me).
- Per-camera and per-version naming matters: train and deploy with identical camera keys.

### Gaps
- Exact image keys that `pi0_base` expects out of the box (`base_0_rgb`, `left_wrist_0_rgb`, `right_wrist_0_rgb` is the openpi convention, seen on the Cache-SCA pi0.5 card) were not confirmed from pi0_base's config file.
- Effect of camera count on SO-101 pi0 success: no controlled study found.

## Quick feasibility summary (for the report writer)
- Works today: fine-tune `pi0_base`/`pi05_base` (or `smolvla_base`) with LeRobot 0.6.x on a rented CUDA GPU using ~50 episodes; deploy with `lerobot-rollout` (local CUDA) or async server/client (remote GPU; Mac keeps the robot and cameras). Several public SO-101 pi0/pi0.5 fine-tunes confirm the pipeline but publish no success numbers.
- Does not work (or no evidence): zero-shot base pi0/pi0.5 on SO-101; pi0 inference on a Mac at usable speed; official kinesthetic-teaching or SO-101 gym_hil support.
- Leader-free data options with real support: phone (iOS/Android) EE teleop, keyboard EE, gamepad, plus scripted controller (custom). Biggest risk: demonstration quality and then VLA performance, since reported single-task success for pi0-class models on SO-101 in the one paper found (UNVERIFIED) is ~31% baseline on multi-step dual-arm tasks.
