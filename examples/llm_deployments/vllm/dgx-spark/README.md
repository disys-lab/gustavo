# DGX Spark vLLM recipes (Gustavo analogs)

Gustavo app config analogs of the single-spark-deployable recipes from
[eugr/spark-vllm-docker](https://github.com/eugr/spark-vllm-docker) (MIT licensed) — a
purpose-built vLLM Docker image and recipe collection for the NVIDIA DGX Spark's GB10
(Grace Blackwell) chip. Every file here is generated from that repo's own `recipes/*.yaml`,
converted into the `docker_image` / `command` / `shm_size` shape Gustavo's Apps page expects
(see [`docs/llm-deployments.md`](../../../../docs/llm-deployments.md)).

**Read the header comment at the top of each file before uploading it** — every file carries
its own numbered checklist (weights path, GPU_ENABLED, image, tensor-parallel assumptions).
This README covers what's common across all of them and what didn't make the cut.

## Two things every file assumes

1. **`docker_image: eugr/spark-vllm:latest`** — this is the upstream project's own real,
   public, arm64-only Docker Hub image (confirmed pullable, rebuilt nightly), built
   specifically for GB10 — not `vllm/vllm-openai`. It has no default entrypoint; the full
   `vllm serve ...` invocation is the `command` list in each file.
2. **`privileged: true`** — the upstream tooling runs these containers privileged by default
   (RDMA/InfiniBand, direct hardware access). Try `privileged: false` if your spark doesn't
   need it.

## Files with `running: false`

Six of the twenty files are set to `running: false` on purpose — they need something Gustavo
can't currently automate. Flip it once you've handled the caveat in that file's own header:

| File | Why it's off |
|---|---|
| `diffusion-gemma-bf16.yaml`, `diffusion-gemma-bf16-thinking.yaml`, `diffusion-gemma-nvfp4.yaml`, `diffusion-gemma-nvfp4-thinking.yaml` | Depend on `mods/diffusiongemma` - real `git apply` patches to the *installed* vLLM package that add DiffusionGemma model support. Without them the model architecture doesn't exist in vLLM at all; it will fail to load, not just run worse. |
| `qwen3-coder-next-int4-autoround.yaml` | Depends on `mods/fix-qwen3-next-autoround`, which reverts an upstream vLLM PR by fetching and applying a patch to the installed package at container start. |
| `qwen3.5-35b-a3b-fp8.yaml` | Depends on `mods/fix-qwen3-coder-next` (crash/slowness/allocator patches to installed vLLM files). |
| `openai-gpt-oss-120b.yaml` | Needs a custom `vllm-node-mxfp4` build (`build-and-copy.sh --exp-mxfp4`) - there's no public image for it, only the default build is published to Docker Hub. `docker_image` in that file is a `REPLACE-ME` placeholder. |

Gustavo's worker only ever gets a plain container `command` - there's no mechanism to run a
pre-step that patches files inside a container before the main process starts. Some mods are
just a file copy (see below), which *is* fully replicated; source patches are not.

## Files needing an extra staged file

Three files need one more file staged on the spark beyond the model weights - each says so in
its own header, with the exact host path to use. The files themselves are shipped in
[`support-files/`](support-files/):

| Recipe file | Needs | From upstream mod |
|---|---|---|
| `qwen3.6-35b-a3b-fp8.yaml`, `qwen3.6-35b-a3b-fp8-dflash.yaml` | `support-files/qwen3.6-fixed_chat_template.jinja` | `mods/fix-qwen3.6-chat-template` |
| `qwen3.5-122b-int4-autoround.yaml` | `support-files/qwen3.5-unsloth.jinja` | `mods/fix-qwen3.5-chat-template` |
| `nemotron-3-nano-nvfp4.yaml` | `support-files/nano_v3_reasoning_parser.py` | `mods/nemotron-nano` (a plain `wget` of a public file, not a patch) |

(`qwen3.5-35b-a3b-fp8.yaml` also needs `qwen3.5-unsloth.jinja` — its header covers this, but
it's `running: false` regardless for the reason above.)

## Recipes with a second (draft/speculative) model

`gemma4-26b-a4b-nvfp4.yaml`, `nemotron-3.5-lightning.yaml`, `qwen3.6-35b-a3b-fp8-dflash.yaml`,
and `qwen3.8-27b-nvfp4-dflash2.yaml` reference a second HuggingFace model ID directly inside a
flag (a speculative-decoding draft model) that is **not** redirected to a local mount like the
main model — vLLM will try to download it over the network at container start. Each file's
header names the exact model ID.

## Not included: cluster-only recipes

Ten of the upstream repo's recipes are marked `cluster_only: true` — the model genuinely
doesn't fit in one spark's GPU memory and requires Ray spanning multiple physical DGX Spark
nodes (see the upstream repo's `--discover`/`launch-cluster.sh` workflow). Gustavo's worker
starts one container on one host with no cross-node coordination, so there is no way to
express these as a single app config - fabricating one would just produce a config that OOMs
on startup. Not converted:

- `deepseek-v4-flash.yaml`, `deepseek-v4-flash-0731.yaml`
- `inkling-small-nvfp4.yaml`
- `minimax-m2-awq.yaml`, `minimax-m2.5-awq.yaml`, `minimax-m2.7-awq.yaml`
- `qwen3.5-122b-fp8.yaml`, `qwen3.5-397b-int4-autoround.yaml`
- `step-3.7-flash-fp8.yaml`, `step-3.7-flash-nvfp4.yaml`

Also not included: the `recipes/3x-spark-cluster/`, `4x-spark-cluster/`, and
`8x-spark-cluster/` directories in the upstream repo — cluster-topology variants of the same
models, for the same reason.

## Verify your hardware before deploying

Several recipes set `tensor_parallel: 2` even though they're marked solo-capable — this
assumes the target spark's worker has that many GPUs actually visible to Docker. This wasn't
guessed at or changed from the upstream recipe's own defaults; verify it against your own
hardware (`lower it to 1` if you're unsure) before deploying rather than assuming it's correct
for your setup.
