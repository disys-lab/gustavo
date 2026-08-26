#!/usr/bin/env bash
# NASA HOME demo walkthrough - CU Boulder, June 2023.
#
# Live demo script for a habitat-simulation testbed: a Manager node plus one
# worker per habitat subsystem (device group), each running that subsystem's
# learning algorithm as a Gustavo-managed app. See ../docs/demos/nasa-home.md
# for the full write-up of what this demonstrates and why.
#
# This is a *presenter's script*, not an unattended pipeline: it pauses after
# each step so the commands and their output can be narrated live. Run it
# from this directory (demoapps/) so the relative config file paths resolve.
#
# Prerequisites:
#   - Manager and all workers (eclss, robotics, environment, eps) are already
#     up and reachable (see docs/cli/manager-setup.md / docs/cli/index.md).
#   - GUSTAVO_CONFIG_FILE points at your manager.env (see below).

set -euo pipefail

pause() {
    read -r -p "-- ${1:-Press Enter to continue...} " _
}

# Point the CLI at the manager node's config. Adjust this path, or export it
# yourself before running the script.
export GUSTAVO_CONFIG_FILE="${GUSTAVO_CONFIG_FILE:-./config_files/manager.env}"

echo "### Step 0 - Registry sanity check"
echo "Show the images available on the manager's registry."
pause
gustavo registry list

echo "### Step 1 - Confirm the edge nodes are clean"
echo "Nothing should be running yet on the ECLSS and Robotics edge devices."
pause "Run this on the ECLSS device, then press Enter..."
docker ps
pause "Run this on the Robotics device, then press Enter..."
docker ps

echo "### Step 2 - Deploy the habitat subsystem algorithms"
echo "One app per algorithm, each pinned to its habitat subsystem's device group:"
echo "  ECLSS (Environmental Control and Life Support) - 3 algorithms, one device group"
echo "  Robotics (Rotating Arm Equipment)"
echo "  ENV (Environment)"
echo "  EPS (Energy and Power)"
pause
gustavo apps createm -n eclss_algorithm1,eclss_algorithm2,eclss_algorithm3 -f algorithms.yml -d eclss
gustavo apps create -n robotics_algorithm1 -f algorithms.yml -d robotics
gustavo apps create -n environment_algorithm1 -f algorithms.yml -d environment
gustavo apps create -n eps_algorithm1 -f algorithms.yml -d eps

echo "### Step 3 - Confirm the algorithms are now running on each edge device"
echo "Repeat on each device: ECLSS, Robotics, Environment, EPS."
pause "Run this on each edge device in turn, then press Enter..."
docker ps

echo "### Step 4 - Bring up the comms relay"
echo "Routes data between the habitat subsystem nodes and the manager."
pause
docker-compose -f comms_manager_config.yaml up -d

echo "### Done."
echo "To add a worker for a new device group later:"
echo "    export GUSTAVO_CONFIG_FILE=/path/to/worker.env"
echo "    gustavo worker up -n worker -d eps"
echo "    gustavo worker up -n worker -d eclss"
