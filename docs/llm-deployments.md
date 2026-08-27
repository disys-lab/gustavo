# Deploying LLMs (vLLM)

This tutorial walks through deploying a GPU-backed LLM inference server — [vLLM](https://docs.vllm.ai/)'s OpenAI-compatible API — as a Gustavo app. It builds on the [End-to-End Tutorial](tutorial.md); read that first if you haven't set up a device group and worker yet.

Two ready-to-use example configs ship in [`examples/llm_deployments/vllm/`](https://github.com/disys-lab/gustavo/tree/main/examples/llm_deployments/vllm):

| File | Model |
|------|-------|
| `qwen3-coder-next.yaml` | Qwen3 Coder (tool-calling, code-focused) |
| `qwen3.6-35b-a3b-fp8.yaml` | Qwen3.6 35B (reasoning/thinking model) |

Both were converted from a plain `docker run --gpus all --ipc=host ...` command into a Gustavo app config — see [Converting a `docker run` command](#converting-a-docker-run-command-to-an-app-config) below if you're adapting a different model.

A larger set of ready-made configs for real production models lives in
[`examples/llm_deployments/vllm/dgx-spark/`](https://github.com/disys-lab/gustavo/tree/main/examples/llm_deployments/vllm/dgx-spark)
— analogs of the single-node recipes from
[eugr/spark-vllm-docker](https://github.com/eugr/spark-vllm-docker), converted for Gustavo. Its
[README](https://github.com/disys-lab/gustavo/blob/main/examples/llm_deployments/vllm/dgx-spark/README.md)
explains a few that ship with `running: false` (they need something Gustavo can't yet automate
— a runtime patch to vLLM itself, or a custom image build) and which upstream recipes were left
out entirely because they require a multi-node Spark cluster, which Gustavo doesn't support.

---

## The one thing this tutorial can't skip: model weights are your responsibility

**Gustavo does not fetch, download, or manage model weights.** The `volumes` entry in the app config is a bind mount — it tells the container "make this host directory available inside the container at `/model`." Nothing in Gustavo, the Manager, or the worker downloads a model into that directory for you.

Before you deploy, you must:

1. **Download the model weights yourself** (e.g. `huggingface-cli download`, `git lfs`, or however you normally fetch them) directly onto the target spark — not onto your laptop, not onto the manager node. The worker mounts a path on **its own local disk**.
2. **Put them at the exact absolute path** that appears on the host side of `volumes:` in the YAML. If the YAML says:
   ```yaml
   volumes:
     - /home/ubuntu/cypress-ai/models/qwen3-coder-next-fp8:/model
   ```
   then `/home/ubuntu/cypress-ai/models/qwen3-coder-next-fp8` must exist on that spark, with the model files directly inside it, *before* you start the app. If the path is wrong or empty, the container will still start (Docker creates an empty directory rather than failing), but vLLM will fail immediately trying to load a model from an empty `/model`.
3. **Match the path per-spark.** If you deploy the same app config to a device group with multiple workers, every worker in that group needs the weights at that identical path — Gustavo doesn't stage or sync files between workers, it just tells each worker's Docker daemon to mount whatever's at that path locally.

This is the single most common way a first LLM deployment fails — the container comes up, looks healthy in `docker ps`, and then immediately crash-loops because `/model` is empty or has the wrong path underneath it. Always check the target spark's filesystem yourself before assigning the app to a device group:

```bash
ssh <spark-host>
ls -la /home/ubuntu/cypress-ai/models/qwen3-coder-next-fp8
# should show config.json, *.safetensors, tokenizer files, etc. — not an empty directory
```

---

## Prerequisites

Beyond the weights being staged correctly, confirm:

- **GPU access on the target worker.** GPU access is a *per-worker* setting in Gustavo, not a per-app one — there is no per-app "use GPU" toggle. The worker that will run this app must already be started with `GPU_ENABLED=true` in its config; every container that worker runs gets GPU device access, not just this one. If you're not sure, check the worker's config/env on that spark, or ask whoever set it up. Deploying a GPU app to a worker without `GPU_ENABLED=true` will start the container, but vLLM will fail to find a GPU.
- **A vLLM API key.** Both example configs pass `--api-key` as a command argument to vLLM itself — replace the placeholder with a real key before deploying, or requests to the server will be rejected (or worse, left open if you drop the flag instead of replacing it).
- **Free host port.** Both example configs bind host port `8000`. If you're deploying more than one LLM to the *same* spark, give each a distinct host port in `starting_ports` — two apps both trying to bind `8000` on one worker will conflict.
- **Enough `/dev/shm`.** See [shm_size vs `--ipc=host`](#shm_size-vs-ipchost) below.

---

## Step 1 — Customize the example config

Open the example closest to your model (or your own converted config — see below) and edit:

```yaml
docker_image: vllm/vllm-openai:latest   # or a pinned tag instead of :latest

volumes:
  - /ABSOLUTE/PATH/ON/THE/SPARK:/model   # must match where you staged the weights

command:
  - "--model"
  - "/model"
  - "--served-model-name"
  - "your-model-name"                    # what clients will request via the OpenAI API
  # ...other vLLM flags...
  - "--api-key"
  - "your-real-api-key"                  # replace the placeholder

shm_size: "16g"                          # see the note below on sizing this
```

Everything else (`running`, `privileged`, `network_mode`, `starting_ports`, `env_vars`) can usually be left as-is unless you have a specific reason to change it.

---

## Step 2 — Upload and create the app

1. Go to **Apps → New App**.
2. Click **Upload YAML** and select your edited config file.
3. This prefills the entire form — Docker image, port mapping, volume, and the **Command & Shared Memory** section (the `command` arguments and `shm_size`).
4. Review every field, especially the volume path and API key you just edited — the form doesn't re-validate that the path actually exists on any worker, that's on you (see [above](#the-one-thing-this-tutorial-cant-skip-model-weights-are-your-responsibility)).
5. Under **Device Groups**, select the group whose worker(s) already have the weights staged and `GPU_ENABLED=true`.
6. Click **Create App**.

If you'd rather not use YAML upload, every field can be filled in by hand the same way — the **Command & Shared Memory** card has an "Add Argument" button for building up the `command` list one flag at a time, and a plain text field for `shm_size`.

---

## Step 3 — Verify it's running

On the target spark:

```bash
docker ps --filter name=your-app-name
docker logs your-app-name-1
```

vLLM takes a while to load a large model into GPU memory — watch the logs until you see it report the server is up, then hit the OpenAI-compatible endpoint directly from the spark (or from anywhere with network access to it):

```bash
curl http://localhost:8000/v1/models \
  -H "Authorization: Bearer your-real-api-key"
```

A working deployment returns your `served-model-name` in the response. If the container is repeatedly restarting instead, check `docker logs` first — an empty or wrong `/model` mount (see above) and a missing GPU are the two most common causes.

---

## Notes specific to LLM deployments

### `shm_size` vs `--ipc=host`

If you were previously running vLLM manually with `--ipc=host`, note that Gustavo has no equivalent setting yet — there's no `ipc_mode` field. This isn't a gap specific to LLMs: `--ipc=host` and a generous `shm_size` are [documented alternatives](https://docs.vllm.ai/) for vLLM specifically, not two different features — `--ipc=host` just gives the container the host's real (effectively unbounded) `/dev/shm`, sidestepping the need to guess a size. Setting `shm_size` to something generous (both examples use `16g`; scale it to what your spark can spare and your model's parallelism needs) achieves the same practical effect for vLLM.

Leaving `shm_size` unset defaults to Docker's normal 64m, which is usually too small for vLLM's inter-process communication — an unset or too-small `shm_size` tends to show up as vLLM crashing or hanging during startup rather than a clear error message, so if a deployment misbehaves and the logs look GPU/model-loading-related, check this next.

### GPU is worker-wide, not per-app

Worth repeating: there is no per-app GPU flag in Gustavo. `GPU_ENABLED` is set once, on the worker itself, and applies to every container that worker starts — GPU or not. You can't have one GPU app and one non-GPU app pinned differently on the same worker; the setting is host-wide.

### Restart behavior

Every app Gustavo starts (LLM or otherwise) already runs with Docker's `unless-stopped` restart policy — this is hardcoded worker behavior, not something you configure per app. You don't need (and currently can't set) an equivalent to `--restart unless-stopped` in the YAML; it's already the default.

---

## Converting a `docker run` command to an app config

If you're adapting a different model, the mapping from a manual `docker run` invocation to a Gustavo app config is direct:

| `docker run` flag | App config field |
|---|---|
| the image reference | `docker_image` |
| `-p HOST:CONTAINER` | `starting_ports: [{HOST: CONTAINER}]` |
| `-v HOST:CONTAINER` | `volumes: ["HOST:CONTAINER"]` |
| `-e KEY=VALUE` | `env_vars: {KEY: VALUE}` |
| `--privileged` | `privileged: true` |
| everything after the image name | `command: [...]`, one array element per token |
| `--shm-size` / `--ipc=host` | `shm_size` (see [above](#shm_size-vs-ipchost)) |
| `--gpus all` | not part of the app config — see [GPU is worker-wide](#gpu-is-worker-wide-not-per-app) |
| `--restart` | not configurable — see [Restart behavior](#restart-behavior) |
| `--name` | the app's `name` (set at creation, not part of `config`) |

The two example files in `examples/llm_deployments/vllm/` show this conversion end-to-end, including the comments explaining each field — they're a good starting template even for a non-vLLM GPU workload.

---

## Next steps

- [End-to-End Tutorial](tutorial.md) — device groups, worker setup, and the rest of the app lifecycle
- [Apps (Web UI)](ui/apps.md) — full reference for every AppForm field
- [Monitoring](ui/monitoring.md) — watch GPU host resource usage once the app is live
