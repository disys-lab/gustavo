# Changelog

All notable changes to Gustavo are documented here. Dates are commit
dates (`YYYY-MM-DD`), not release/publish dates. Gustavo doesn't cut
GitHub Releases — versions are Git tags, bumped automatically by CI
(`#bump #patch|#minor` commit-message catchphrases in
`.github/workflows/multi-build.yml`), so a single day can span several
version numbers. Sections below group commits by real development era
rather than by exact tag, which is more useful than one entry per
auto-bump.

## [Unreleased]

- Added numpydoc-style docstrings across `gustavo/src/{NebulaBase,
  Manager,Composer,Cache}.py` and all nine `gustavo/api/routers/*.py`
  modules, rendered on the docs site via the existing `mkdocstrings`
  setup.
- Replaced `docs/ui/dashboard.md`'s ASCII mockup with a real
  screenshot.
- Fixed the README's license badge/text — it claimed MIT, but
  `LICENSE` is GPL-3.0.
- Added this CHANGELOG and README badges.

## 2026-03-05 – 2026-09-03 — Next.js + FastAPI rewrite (spans `v0.4.0-beta.1`–`v0.7.1`)

The platform's UI and backend were rewritten from a Streamlit app
into a Next.js frontend and FastAPI backend; the legacy Streamlit
pages were kept side-by-side during the migration and removed once
the rewrite reached parity.

**Core rewrite**

- Introduced the Next.js + FastAPI architecture (2026-03-05).
- Removed the Streamlit UI in favor of Next.js/FastAPI; added a
  version display (2026-08-24).

**Access control & multi-user support**

- Added Nebula-backed local accounts and user/group admin management.
- Let admins grant/revoke group access to apps and device groups; let
  non-admins create and manage their own device groups.
- Hid admin-only UI from non-admin users; showed who's logged in;
  showed service status to non-admins with per-service checks.
- Fixed a db-user login spoofing issue; split the login form.
- Included Nebula group memberships in the login response.

**Worker & registry tooling**

- Added worker config downloads (`worker.env`) for device groups,
  including HTTP Basic auth for one-request script access and
  `REGISTRY_HOST`/`REGISTRY_PORT` in the generated file.
- Added GPU_ENABLED support to worker config generation and the CLI;
  the worker now warns (not crashes) on a GPU mismatch at startup.
- Added Nebula-backed registry auth checks and a localhost-bind
  toggle; added `REGISTRY_CONTAINER_PORT` so Gustavo's own registry
  calls survive a proxy (replacing an earlier `REGISTRY_INTERNAL_PORT`
  attempt that collided with the registry launch).
- Let downloaded `worker.env` carry registry-proxy login credentials.

**Backups & credentials**

- Added Mongo backup/restore, matching the existing Redis/Registry
  pattern.
- Added Mongo credential rotation.

**Fixes & cleanup**

- Fixed a raw JSON-parse error leaking on invalid per-user Nebula
  tokens.
- Fixed copy-to-clipboard silently failing on non-localhost HTTP.
- Fixed app-create defaults to use the caller's own Nebula identity;
  reverted an earlier per-user-token approach and dropped
  `NEBULA_AUTH_TOKEN`/`MANAGER_AUTH` from app defaults.
- Removed the dead `gustavo/Builder/` directory.
- Fixed the remaining Dependabot CVEs across npm and pip dependencies.
- Added `command`/`shm_size` fields to the app form; made YAML upload
  prefill the full app config, not just `docker_image`.

**Docs & examples**

- Added a real 2-command quickstart ahead of the full manual setup.
- Documented the worker-download endpoint, group grants, and the
  registry proxy setup.
- Documented the NASA HOME demo (`examples/nasa_home_demoapps/`,
  renamed from `demoapps/`); consolidated sample config files.
- Added an LLM deployment tutorial (vLLM) and DGX Spark recipe
  examples.

## 2025 — Streamlit UI hardening

- Added Firebase authentication as a login option.
- Added Redis and Registry backup/restore; later added Mongo
  parity in the rewrite above.
- Added manager service status, monitoring, and styling
  improvements; added loaders for creation/update status refresh.
- Strengthened the app-creation environment-variable editor UI and
  fixed several related bugs (missing `APP_ID`, form value bugs).
- Updated mkdocs documentation support.

## 2023–2024 — Early prototype

- Initial CLI and manager/worker communication ("comms") layer.
- Added the original Streamlit GUI.
- Reorganized the codebase into an installable `src`-layout package.
