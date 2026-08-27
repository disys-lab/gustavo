# DGX Spark vLLM recipes (Gustavo analogs)

Gustavo app config analogs of the recipes from
[eugr/spark-vllm-docker](https://github.com/eugr/spark-vllm-docker) (MIT licensed) — a
purpose-built vLLM Docker image and recipe collection for the NVIDIA DGX Spark's GB10
(Grace Blackwell) chip. Every file here is a plain `.yaml` app config, generated from that
repo's own `recipes/*.yaml`, converted into the `docker_image` / `command` / `shm_size` shape
Gustavo's Apps page expects (see [`docs/llm-deployments.md`](../../../../docs/llm-deployments.md)).

Only recipes that are **fully deployable through Gustavo today, as pure YAML, with nothing
else to fetch beyond the model weights**, are included. Nothing here depends on a file this
directory doesn't ship, an upstream source patch, or a private/unpublished image.

**Read the header comment at the top of each file before uploading it** — every file carries
its own numbered checklist (weights path, GPU_ENABLED, image, tensor-parallel assumptions).

## Two things every file assumes

1. **`docker_image: eugr/spark-vllm:latest`** — this is the upstream project's own real,
   public, arm64-only Docker Hub image (confirmed pullable, rebuilt nightly), built
   specifically for GB10 — not `vllm/vllm-openai`. It has no default entrypoint; the full
   `vllm serve ...` invocation is the `command` list in each file.
2. **`privileged: true`** — the upstream tooling runs these containers privileged by default
   (RDMA/InfiniBand, direct hardware access). Try `privileged: false` if your spark doesn't
   need it.

## Recipes with a second (draft/speculative) model

`nemotron-3.5-lightning.yaml` and `qwen3.8-27b-nvfp4-dflash2.yaml` reference a second
HuggingFace model ID directly inside a flag (a speculative-decoding draft model) that is
**not** redirected to a local mount like the main model — vLLM will try to download it over
the network at container start. Each file's header names the exact model ID.

## Not included

Twenty of the upstream repo's twenty-nine recipes were left out, for three different reasons:

**Needs multiple physical Spark nodes (`cluster_only: true`)** — Gustavo's worker starts one
container on one host with no cross-node Ray coordination, so there's no way to express these
as a single app config:
`deepseek-v4-flash.yaml`, `deepseek-v4-flash-0731.yaml`, `inkling-small-nvfp4.yaml`,
`minimax-m2-awq.yaml`, `minimax-m2.5-awq.yaml`, `minimax-m2.7-awq.yaml`,
`qwen3.5-122b-fp8.yaml`, `qwen3.5-397b-int4-autoround.yaml`, `step-3.7-flash-fp8.yaml`,
`step-3.7-flash-nvfp4.yaml` — plus the `recipes/3x-spark-cluster/`, `4x-spark-cluster/`, and
`8x-spark-cluster/` directories in the upstream repo (cluster-topology variants of the same
models).

**Needs a real vLLM source patch applied at container start, or an unpublished image** —
Gustavo can only pass a container command, not run a pre-step that patches files inside a
container before vLLM starts, and one recipe needs a custom image build with no public tag:
`diffusion-gemma-bf16.yaml`, `diffusion-gemma-bf16-thinking.yaml`, `diffusion-gemma-nvfp4.yaml`,
`diffusion-gemma-nvfp4-thinking.yaml` (need `mods/diffusiongemma` - the model architecture
doesn't exist in vLLM at all without it), `qwen3-coder-next-int4-autoround.yaml` (needs
`mods/fix-qwen3-next-autoround`), `qwen3.5-35b-a3b-fp8.yaml` (needs `mods/fix-qwen3-coder-next`),
`openai-gpt-oss-120b.yaml` (needs a `vllm-node-mxfp4` build - only the default build is
published to Docker Hub).

**Needs an extra file beyond model weights** (a chat-template `.jinja` or a reasoning-parser
`.py`) that this directory doesn't ship: `nemotron-3-nano-nvfp4.yaml`,
`qwen3.5-122b-int4-autoround.yaml`, `qwen3.6-35b-a3b-fp8.yaml`, `qwen3.6-35b-a3b-fp8-dflash.yaml`.
The app config itself is otherwise ordinary Gustavo YAML for these - see the upstream recipe
directly if you want to source that file yourself and adapt one of the included configs.

## Verify your hardware before deploying

Several recipes set `tensor_parallel: 2` even though they're marked solo-capable — this
assumes the target spark's worker has that many GPUs actually visible to Docker. This wasn't
guessed at or changed from the upstream recipe's own defaults; verify it against your own
hardware (`lower it to 1` if you're unsure) before deploying rather than assuming it's correct
for your setup.
