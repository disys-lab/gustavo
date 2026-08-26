# Case Study: NASA HOME — CU Boulder, June 2023

Gustavo was built for the [NASA HOME (Habitats Optimized for Missions of Exploration)
project](https://homestri.sf.ucdavis.edu/), a NASA STRI-funded effort to design
long-duration deep-space habitats. In June 2023, at CU Boulder, Gustavo served as
the primary orchestration workhorse for a live habitat-simulation demo presented
in front of NASA engineers.

## The scenario

A habitat is broken into subsystems, each with its own continually-learning
control algorithm running on its own compute hardware — modeling how a real
deep-space habitat would distribute intelligence across independent onboard
edge nodes rather than one central computer:

| Device group | Subsystem | Role |
|---|---|---|
| `eclss` | **E**nvironmental **C**ontrol and **L**ife **S**upport **S**ystem | Air, water, temperature — keeping the crew alive |
| `environment` | **Env**ironment | Modeling/responding to the surrounding habitat environment |
| `robotics` | Rotating Arm Equipment | Robotic manipulation hardware |
| `eps` | **E**nergy and **P**ower **S**ystem | Habitat power generation/distribution |

Each subsystem ran as a separate Gustavo **worker** node — its own device group,
with its own algorithm container(s) deployed and managed independently. A single
Gustavo **Manager** node coordinated all of them: distributing algorithm images
through its registry, deploying/updating apps per device group, and relaying
data between subsystems via a comms container.

This is exactly the problem Gustavo is designed to solve in production edge
deployments too — just demonstrated here on a habitat-simulation testbed instead
of an industrial site.

## The walkthrough

The commands below are what was actually run live during the demo. A ready-to-run
version lives at [`examples/nasa_home_demoapps/orchestration_test.sh`](https://github.com/disys-lab/gustavo/blob/main/examples/nasa_home_demoapps/orchestration_test.sh)
in the repo, alongside the config files it references
([`algorithms.yml`](https://github.com/disys-lab/gustavo/blob/main/examples/nasa_home_demoapps/config_files/algorithms.yml),
[`comms_manager_config.yaml`](https://github.com/disys-lab/gustavo/blob/main/examples/nasa_home_demoapps/config_files/comms_manager_config.yaml),
[`mappings_list.yml`](https://github.com/disys-lab/gustavo/blob/main/examples/nasa_home_demoapps/config_files/mappings_list.yml)).

Prerequisite: the Manager and all four workers (`eclss`, `robotics`, `environment`,
`eps`) are already up — see [Manager Node Setup](../cli/manager-setup.md) and
[Worker node setup](../cli/index.md#worker-node-setup).

### Step 0 — Registry sanity check

Confirm the algorithm images have already been synced into the manager's local
registry (via the syncer/`dregsy_conf.yml` — see [Syncer Setup](../cli/manager-setup.md#step-3-create-syncer-config-files)):

```bash
gustavo registry list
```

### Step 1 — Confirm the edge nodes start clean

Nothing should be running yet on any habitat subsystem's edge device:

```bash
docker ps
```

Run on the ECLSS and Robotics devices to show a clean slate before deployment.

### Step 2 — Deploy an algorithm to each subsystem

One app per algorithm, each created against
[`algorithms.yml`](https://github.com/disys-lab/gustavo/blob/main/examples/nasa_home_demoapps/config_files/algorithms.yml)
and pinned to its subsystem's device group. ECLSS runs three algorithms at once
via [`createm`](../cli/apps.md#createm) (create-multiple); the rest use a single
[`create`](../cli/apps.md#create):

```bash
gustavo apps createm -n eclss_algorithm1,eclss_algorithm2,eclss_algorithm3 -f config_files/algorithms.yml -d eclss
gustavo apps create -n robotics_algorithm1 -f config_files/algorithms.yml -d robotics
gustavo apps create -n environment_algorithm1 -f config_files/algorithms.yml -d environment
gustavo apps create -n eps_algorithm1 -f config_files/algorithms.yml -d eps
```

### Step 3 — Confirm the algorithms are running at the edge

Repeated on each of the four edge devices to show the containers landed and
started:

```bash
docker ps
```

### Step 4 — Bring up inter-subsystem comms

A comms relay container ties the subsystems together, using
[`comms_manager_config.yaml`](https://github.com/disys-lab/gustavo/blob/main/examples/nasa_home_demoapps/config_files/comms_manager_config.yaml):

```bash
docker-compose -f config_files/comms_manager_config.yaml up -d
```

### Adding a worker for a new device group

Shown separately, to demonstrate onboarding a new habitat subsystem after the
fact rather than only at initial bring-up:

```bash
export GUSTAVO_CONFIG_FILE=/path/to/worker.env

gustavo worker up -n worker -d eps
gustavo worker up -n worker -d eclss
```

See [`worker.env`](../cli/index.md#workerenv) for the config file format.

---

*Command syntax above reflects the CLI as of June 2023; see [CLI Reference](../cli/index.md)
for the current, authoritative command set.*
