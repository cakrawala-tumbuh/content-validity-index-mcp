# Makefile — satu-satunya pintu untuk automated test (linter + unit).
# Developer di lokal maupun GitHub Actions menjalankan target yang SAMA: `make test`.
# Semua test berjalan di dalam Docker (Dockerfile.test), tanpa bind-mount, sehingga
# tidak ada artefak yang bocor ke folder project.

# Nama image diturunkan dari nama folder agar tidak bentrok antar project.
IMAGE_NAME ?= $(shell basename $(CURDIR))-test
DOCKER_RUN  = docker run --rm $(IMAGE_NAME)

.DEFAULT_GOAL := test
.PHONY: build lint unit test clean help

build: ## Bangun image test (deps + tooling + source)
	docker build -f Dockerfile.test -t $(IMAGE_NAME) .

lint: build ## Jalankan linter (Ruff check + format check) di dalam container
	$(DOCKER_RUN) sh -c "ruff check . && ruff format --check ."

unit: build ## Jalankan unit test (pytest) di dalam container
	$(DOCKER_RUN) python -m pytest tests/ -v

test: lint unit ## Gate lengkap = lint + unit (dipakai lokal & CI)

clean: ## Hapus image test
	-docker rmi $(IMAGE_NAME)

help: ## Tampilkan daftar target
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-8s\033[0m %s\n", $$1, $$2}'
