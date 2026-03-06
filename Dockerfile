FROM ubuntu:24.04

ARG py_version=python3.11
ARG gustavo_version=v0.4.0-beta.3
ARG node_version=20
ARG NEXT_PUBLIC_AUTH_ENABLED=true

LABEL version=${gustavo_version}
LABEL maintainer="paritosh.ramanan@okstate.edu"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ── Python base (mirrors Dockerfile.streamlit exactly) ───────────────────────
# All apt steps in one layer so apt lists are always fresh and then cleaned up,
# preventing stale GPG signatures from being cached across builds.
RUN apt-get -y update && apt-get -y upgrade && \
    apt-get -y install build-essential supervisor software-properties-common curl && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get -y update && \
    apt-get -y install python3-pip ${py_version} ${py_version}-venv ${py_version}-dev && \
    apt-get purge -y build-essential && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# ── Node.js ──────────────────────────────────────────────────────────────────
RUN curl -fsSL https://deb.nodesource.com/setup_${node_version}.x | bash - && \
    apt-get -y install nodejs && \
    rm -rf /var/lib/apt/lists/*

RUN ${py_version} -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

RUN pip3 install --no-cache-dir --extra-index-url https://pypi.fury.io/osu-home-stri/ gustavo==${gustavo_version}

# ── FastAPI requirements ─────────────────────────────────────────────────────
COPY gustavo/api/requirements-api.txt /tmp/requirements-api.txt
RUN pip install --no-cache-dir -r /tmp/requirements-api.txt && \
    rm -f /tmp/requirements-api.txt

WORKDIR /app
COPY . .

# Install local gustavo package (adds gustavo/api/ submodule not in PyPI release).
# PACKAGE_VERSION must be set so setup.py doesn't fall through to sys.argv[-1],
# which pip sets to 'egg_info' during editable installs — an invalid version string.
RUN PACKAGE_VERSION=${gustavo_version} pip install --no-cache-dir -e . --no-deps

# ── Next.js UI build ─────────────────────────────────────────────────────────
# NEXT_PUBLIC_AUTH_ENABLED is baked in at build time (Next.js requirement for client vars)
# Default: true (production). Override with --build-arg NEXT_PUBLIC_AUTH_ENABLED=false
ENV NEXT_PUBLIC_AUTH_ENABLED=${NEXT_PUBLIC_AUTH_ENABLED}

WORKDIR /app/gustavo-ui
# Ensure all gustavo images are available to Next.js at build time
# regardless of which public/ files were committed to git.
RUN cp /app/gustavo/images/*.png /app/gustavo-ui/public/

RUN npm ci --prefer-offline --no-audit --no-fund && \
    npm run build && \
    cp -r .next/static .next/standalone/.next/static && \
    cp -r public .next/standalone/public && \
    rm -rf node_modules && \
    npm cache clean --force

# ── Runtime configuration ────────────────────────────────────────────────────
WORKDIR /app

# Supervisor config at /etc/supervisord.conf (separate from /etc/gustavo platform config)
COPY gustavo/api/supervisord.conf /etc/supervisord.conf

# gustavo-next: one-stop startup command (mirrors "gustavo gui -p PORT" pattern)
COPY gustavo/api/entrypoint.sh /usr/local/bin/gustavo-next
RUN chmod +x /usr/local/bin/gustavo-next

RUN mkdir -p /etc/gustavo

# Only port 3000 (Next.js) is the public interface.
# FastAPI (:8000) binds to 127.0.0.1 only — not reachable from outside the container.
EXPOSE 3000

CMD ["gustavo-next", "-p", "3000"]
