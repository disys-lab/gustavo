# ─────────────────────────────────────────────────────────────────────────────
#  Gustavo — Docker image build
# ─────────────────────────────────────────────────────────────────────────────
#  Usage:
#    make build                        # build with defaults
#    make build VERSION=0.3.15         # specify gustavo package version
#    make build AUTH=false             # bake NEXT_PUBLIC_AUTH_ENABLED=false
#    make push  VERSION=0.3.15         # push to registry after building
#    make run                          # run locally on port 3000
#    make stop                         # stop the local container
#    make logs                         # tail logs of running container
#    make clean                        # remove local image
# ─────────────────────────────────────────────────────────────────────────────

REGISTRY   ?= ghcr.io/disys-lab
IMAGE      ?= gustavo
GUSTAVO_DOCKER_VERSION    ?= 0.4.0b3
GUSTAVO_VERSION    ?= v0.4.0-beta.3
PY_VERSION ?= python3.11
NODE_VERSION ?= 20
AUTH       ?= true

FULL_IMAGE  = $(REGISTRY)/$(IMAGE):$(GUSTAVO_DOCKER_VERSION)
LATEST_TAG  = $(REGISTRY)/$(IMAGE):latest

# ── Build ─────────────────────────────────────────────────────────────────────
.PHONY: build
build:
	docker buildx build \
		--platform linux/amd64 \
		--no-cache \
		--pull \
		--build-arg gustavo_version=$(GUSTAVO_VERSION) \
		--build-arg py_version=$(PY_VERSION) \
		--build-arg node_version=$(NODE_VERSION) \
		--build-arg NEXT_PUBLIC_AUTH_ENABLED=$(AUTH) \
		-t $(FULL_IMAGE) \
		-t $(LATEST_TAG) \
		--load \
		.

# ── Push ──────────────────────────────────────────────────────────────────────
.PHONY: push
push:
	docker push $(FULL_IMAGE)
	docker push $(LATEST_TAG)

# ── Build + Push in one step ──────────────────────────────────────────────────
.PHONY: release
release:
	docker buildx build \
		--platform linux/amd64 \
		--no-cache \
		--pull \
		--build-arg gustavo_version=$(GUSTAVO_VERSION) \
		--build-arg py_version=$(PY_VERSION) \
		--build-arg node_version=$(NODE_VERSION) \
		--build-arg NEXT_PUBLIC_AUTH_ENABLED=$(AUTH) \
		-t $(FULL_IMAGE) \
		-t $(LATEST_TAG) \
		--push \
		.

# ── Run locally ───────────────────────────────────────────────────────────────
.PHONY: run
run:
	docker run -d \
		--name gustavo \
		-p 3000:3000 \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v /tmp/:/tmp/ \
		-e AUTH_ENABLED=$(AUTH) \
		$(FULL_IMAGE) \
		gustavo-next -p 3000

# ── Stop & remove local container ────────────────────────────────────────────
.PHONY: stop
stop:
	docker stop gustavo && docker rm gustavo

# ── Logs ──────────────────────────────────────────────────────────────────────
.PHONY: logs
logs:
	docker logs -f gustavo

# ── Remove local image ────────────────────────────────────────────────────────
.PHONY: clean
clean:
	docker rmi $(FULL_IMAGE) $(LATEST_TAG) || true

# ── Print resolved variables ──────────────────────────────────────────────────
.PHONY: info
info:
	@echo "Image:    $(FULL_IMAGE)"
	@echo "Latest:   $(LATEST_TAG)"
	@echo "Auth:     NEXT_PUBLIC_AUTH_ENABLED=$(AUTH)"
	@echo "Python:   $(PY_VERSION)"
	@echo "Node:     $(NODE_VERSION)"
