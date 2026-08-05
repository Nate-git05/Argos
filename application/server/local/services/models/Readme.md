# Model catalog

Every VLA architecture Argos knows about, sourced from the vla.cpp paper
(arXiv:2606.08094) plus each model's individual Hugging Face card. This is
generated from `models.yaml` in this directory -- edit that file, not this
one, if the catalog changes.

**Hardware target: Jetson Orin Nano, 8GB unified memory.** That budget is
the single biggest filter below -- two of the seven architectures
(GR00T-N1.6, GR00T-N1.7) simply don't fit; their ~6GB of weights alone
exhaust the pool. Both are still listed for reference (and are viable on
higher-tier hardware like AGX Orin), but `fits_orin_nano_8gb` is your
first filter when choosing a model.

Only `smolvla` is officially supported today (**V1**). Everything else is
a **V1.x candidate** -- reference data, still needs its launch command
verified against the real HF repo before being wired into `pull`/`run`.

## At a glance

| Model | Status | Params | Fits Orin Nano 8GB | LIBERO success (RTX 3060) |
|---|---|---|---|---|
| `smolvla` | V1 — officially supported | 450M | yes | 90.5% |
| `pi0` | V1.x candidate | 3B | yes | 87.5% |
| `bitvla` | V1.x candidate — strong second pick after smolvla | 2.4B | yes | 100.0% |
| `evo1` | V1.x candidate | 770M | yes | 94.5% |
| `gr00t-n1.5` | V1.x candidate — filename now confirmed, launch args verified | 3B | yes | 96.0% |
| `gr00t-n1.6` | NOT SUITABLE for Orin Nano 8GB — do not add to V1/V1.x catalog for this hardware target | 3B | no | — |
| `gr00t-n1.7` | NOT SUITABLE for Orin Nano 8GB — same memory issue as N1.6 | 3B | no | 98.0% |

## Details

### `smolvla`

**Status:** V1 — officially supported

vla.cpp's "golden reference" architecture — every other arch is validated against this recipe. Simplest setup: no gating, no extra stats files. Start here.

| | |
|---|---|
| Params | 450M |
| Vision backbone | SigLIP-So400m |
| Language backbone | SmolLM2-360M |
| Action head | flow-matching cross-attention expert |
| Action steps per chunk | 1 |
| Solver steps | 10 |
| Requires gated tokenizer | no |
| Camera views | 2 -- observation.images.image, observation.images.image2 |
| Fits Orin Nano 8GB | yes |
| Launch env | none required |

**Benchmark (RTX 3060):** 90.5% success, 28.16 ms/step, 54.8 ms inference, 1410 MiB VRAM

**Benchmark (Orin Nano 8GB):** 141.81 ms/step, 2031 MiB peak RSS

**Info confidence:** high -- Real invocation confirmed in README.md:135, eval/run_libero.sh:372-378, ci/lib/common.sh:87-88. Uses the client's generic/unsliced predict path (vla_cpp_client.py:518-547), so all of image_keys is sent. tokenizer_repo, max_state_dim, and image_size confirmed via vla_cpp_client.py's ARCH_PRESETS dict.

---

### `pi0`

**Status:** V1.x candidate

Needs `huggingface-cli login` + accepting the PaliGemma license before first use. Cheapest per-step compute of all 7 archs, but least accurate — long chunk replay lets the scene drift before replanning.

| | |
|---|---|
| Params | 3B |
| Vision backbone | SigLIP-So400m |
| Language backbone | Gemma-2B |
| Action head | flow-matching joint-attention expert |
| Action steps per chunk | 32 |
| Solver steps | 10 |
| Requires gated tokenizer | yes (google/paligemma-3b-pt-224) |
| Camera views | 2 -- observation.images.image, observation.images.image2 |
| Fits Orin Nano 8GB | yes -- split only — server+client+sim together exceed 8GB; benchmarked with sim offloaded to a second machine, so latency includes network hop |
| Launch env | none required |

**Launch notes:** Optional: VLA_PI0_F32_WEIGHTS=1 forces F32 weights (default bf16).

**Benchmark (RTX 3060):** 87.5% success, 9.74 ms/step, 207.2 ms inference, 5548 MiB VRAM

**Benchmark (Orin Nano 8GB (split, sim offloaded)):** 39.1 ms/step, 6068 MiB peak RSS

**Info confidence:** high -- Real invocation confirmed in eval/run_libero.sh:355-361, eval/run_libero_server.sh:129-133, ci/lib/common.sh:79-80. Same generic/unsliced predict path as smolvla.

---

### `bitvla`

**Status:** V1.x candidate — strong second pick after smolvla

1-bit/ternary weights, smallest footprint of any served model (1.3 GiB resident on Orin Nano) despite being 2.4B params. Highest success rate of all 7 archs (100% on LIBERO-Object, RTX 3060). No iterative solver loop — single forward pass emits the whole chunk. vla.cpp includes a custom tensor-core ternary GEMM kernel for this model specifically (4-4.6x additional speedup over the naive path).

| | |
|---|---|
| Params | 2.4B |
| Vision backbone | BitSigLIP-L (ternary) |
| Language backbone | BitNet-2B (ternary) |
| Action head | single-pass MLP regression (no solver loop) |
| Requires gated tokenizer | no |
| Camera views | 2 -- observation.images.image, observation.images.image2 |
| Fits Orin Nano 8GB | yes |
| Launch env | none required |

**Launch notes:** Optional: VLA_BITVLA_UNNORM_KEY selects stats suite key. VLA_BITVLA_BF16_WEIGHTS=1 opts into bf16 — NOTE opposite default polarity from every other arch: bitvla defaults to F32.

**Benchmark (RTX 3060):** 100.0% success, 37.85 ms/step, 235.9 ms inference, 1312 MiB VRAM

**Benchmark (Orin Nano 8GB):** 355.65 ms/step, 2199 MiB peak RSS

**Info confidence:** high -- Launch mechanics confirmed via eval/run_libero.sh:391-397, ci/lib/common.sh:91-93 (BITVLA_N_VIEWS=2, vla_cpp_client.py:61,832). BUT the filename above was corrected from the prior entry using the script's actual path ("libero_object/bitvla-libero-object.gguf" instead of "bitvla-libero.gguf") — verify this matches the real HF repo listing before first pull.

---

### `evo1`

**Status:** V1.x candidate

Second-highest success rate of the 7 (94.5% on LIBERO-Object, RTX 3060), fits comfortably on Orin Nano. No known gating requirement, but not yet individually verified against its HF model card the way smolvla/pi0/vla-jepa were — check before adding to catalog.

| | |
|---|---|
| Params | 770M |
| Vision backbone | InternViT-300M |
| Language backbone | Qwen2.5-0.5B |
| Action head | cross-attention DiT (flow-matching) |
| Action steps per chunk | 8 |
| Solver steps | 32 |
| Requires gated tokenizer | no |
| Camera views | 3 -- obs.pixels.image (real, front), obs.pixels.image2 (real, wrist), zero-filled pad slot |
| | *Server-side view count is flexible, but the real client (adapters.py:75-89) always sends 3 image slots with image_mask=[1,1,0] — 2 real camera views + 1 masked pad, not 2. Uses raw sim camera key names (obs.pixels.*), NOT the observation.images.* convention other archs use.* |
| Fits Orin Nano 8GB | yes |
| Launch env | none required |

**Launch notes:** Optional: VLA_EVO1_F32_WEIGHTS=1 forces F32 weights (default bf16).

**Benchmark (RTX 3060):** 94.5% success, 63.6 ms/step, 131.0 ms inference, 1564 MiB VRAM

**Benchmark (Orin Nano 8GB):** 458.84 ms/step, 2135 MiB peak RSS

**Info confidence:** high -- Real invocation confirmed in eval/run_libero.sh:381-387, ci/lib/common.sh:89-90.

---

### `gr00t-n1.5`

**Status:** V1.x candidate — filename now confirmed, launch args verified

| | |
|---|---|
| Params | 3B |
| Vision backbone | SigLIP2-400M (Eagle-2.5 VLM) |
| Language backbone | Qwen3-1.7B |
| Action head | AltVL DiT + self-attention (diffusion) |
| Action steps per chunk | 16 |
| Solver steps | 4 |
| Requires gated tokenizer | no |
| Camera views | 2 -- video.image, video.wrist_image |
| | *Hardcoded keys, different naming convention from observation.images.* used by other archs.* |
| Fits Orin Nano 8GB | yes -- split only — simulator offloaded to a second machine, benchmark includes network hop |
| Launch env | `VLA_GR00T_EMBODIMENT=new_embodiment`, `VLA_GR00T_BF16_WEIGHTS=1` |

**Launch notes:** VLA_GR00T_EMBODIMENT technically has a baked default (embodiment_id=24) but every real example sets it explicitly, so it's treated as required here. VLA_GR00T_BF16_WEIGHTS defaults to unset (F32) — required here specifically to fit the 8GB Orin Nano target.

**Benchmark (RTX 3060):** 96.0% success, 14.17 ms/step, 147.0 ms inference, 4866 MiB VRAM

**Benchmark (Orin Nano 8GB (split, sim offloaded)):** 84.76 ms/step

**Info confidence:** high -- Real invocation confirmed in eval/run_libero.sh:428-436, eval/run_libero_server.sh:135, ci/lib/common.sh:94-95, README.md:163. Filename/repo_id both match the script's path exactly — no correction needed.

---

### `gr00t-n1.6`

**Status:** NOT SUITABLE for Orin Nano 8GB — do not add to V1/V1.x catalog for this hardware target

~6GB resident weights exhaust the 8GB unified memory pool entirely — does not fit even with the simulator offloaded elsewhere. Only usable on higher-tier hardware (AGX Orin or better). Used in the paper's real-robot ALOHA stress test (87.5% success vs 40% for PyTorch baseline) — good architecture, wrong hardware tier for this product.

| | |
|---|---|
| Params | 3B |
| Vision backbone | SigLIP2-400M (Eagle3-VL) |
| Language backbone | Qwen3-1.7B |
| Action head | AltVL DiT (diffusion) |
| Action steps per chunk | 16 |
| Solver steps | 4 |
| Requires gated tokenizer | no |
| Camera views | ambiguous |
| | *3 mutually-incompatible real deployments exist in this repo: LIBERO (2 views: video.image, video.wrist_image), SimplerEnv-bridge (1 view: image_0), ALOHA (1 view, name unconfirmed).* |
| Fits Orin Nano 8GB | no |
| Launch env | *ambiguous -- see launch_notes* |

**Launch notes:** 3 mutually-incompatible real deployments exist, each with its own checkpoint/env/view-count: LIBERO (<gr00tn1d6-libero.gguf>, VLA_GR00T_EMBODIMENT=libero_panda), SimplerEnv-bridge (<gr00t-n1d6-bridge.gguf> --bind tcp://*:5566, requires the 252px vision build, VLA_GR00T_BF16_WEIGHTS=1 VLA_GR00T_EMBODIMENT=oxe_widowx), ALOHA (<gr00t-n1d6-aloha.gguf>, VLA_GR00T_EMBODIMENT=new_embodiment).

**Info confidence:** flag -- AMBIGUOUS — not suitable for Orin Nano anyway (fits_orin_nano_8gb: false), so lower priority, but this catalog key needs a decision on which of the 3 real deployments (LIBERO/SimplerEnv-bridge/ALOHA) it represents before it's usable — they use different checkpoints, embodiments, and view counts, confirmed via eval/run_libero.sh:450-454, eval/run_aloha_server.sh:19-47, README.md:171-176. Also: two conflicting filename spellings exist between eval/run_libero.sh/ci/lib/common.sh:97 ("gr00tn1d6-...") and eval/run_libero_server.sh:138 ("gr00t-n1d6-...") — verify against the actual HF repo before use.

---

### `gr00t-n1.7`

**Status:** NOT SUITABLE for Orin Nano 8GB — same memory issue as N1.6

Highest success rate of all 7 archs on LIBERO-Object (98.0%, RTX 3060), but same ~6GB footprint problem as N1.6 — does not fit the 8GB target hardware tier at all.

| | |
|---|---|
| Params | 3B |
| Vision backbone | Qwen3-VL ViT |
| Language backbone | Qwen3-VL |
| Action head | AltVL DiT + self-attention (diffusion) |
| Action steps per chunk | 16 |
| Solver steps | 4 |
| Requires gated tokenizer | no |
| Camera views | 2 -- video.image, video.wrist_image |
| Fits Orin Nano 8GB | no |
| Launch env | none required |

**Launch notes:** Do NOT set VLA_GR00T_EMBODIMENT — unlike n1.5/n1.6, n1.7 uses the GGUF's own baked default embodiment (libero_sim); explicitly omitted in the real CI invocation. Optional: VLA_GR00T_BF16_WEIGHTS (memory only), VLA_NUM_STEPS (overrides denoising step count).

**Benchmark (RTX 3060):** 98.0% success, 10.26 ms/step, 84.1 ms inference, 6302 MiB VRAM

**Info confidence:** high -- Launch mechanics confirmed via eval/run_libero.sh:465-469, ci/lib/common.sh:98-100. Filename corrected from the prior entry using the script's actual path; a second, conflicting hyphenation ("gr00t-n1d7-...") appears in eval/run_libero_server.sh:141 — verify against the actual HF repo before use.

---

## Dropped from the catalog

Kept here as a record, not as entries -- revisit once better attested
or upstream finetuning settles:

- **vla-jepa** -- low confidence, zero real invocations anywhere in vla.cpp.
- **vla-adapter** -- medium confidence, repo_id itself unverified.
- **pi05, openvla-oft** -- still being finetuned upstream by their devs,
  not stable enough to catalog yet.
