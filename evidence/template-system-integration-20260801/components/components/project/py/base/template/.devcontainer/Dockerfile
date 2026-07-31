# syntax=docker/dockerfile:1

ARG VARIANT="3.13"
FROM mcr.microsoft.com/devcontainers/python:${VARIANT}

ENV DEBIAN_FRONTEND=noninteractive

# Install compilation tooling and system tools needed by the baseline hooks.
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    curl \
    git \
    shellcheck \
    && rm -rf /var/lib/apt/lists/*

# Install hadolint for local pre-commit parity across architectures.
RUN set -eux; \
    arch="$(dpkg --print-architecture)"; \
    case "${arch}" in \
      amd64) asset="hadolint-Linux-x86_64" ;; \
      arm64) asset="hadolint-Linux-arm64" ;; \
      *) echo "Unsupported architecture for hadolint: ${arch}" >&2; exit 2 ;; \
    esac; \
    curl -fsSL -o /usr/local/bin/hadolint \
      "https://github.com/hadolint/hadolint/releases/latest/download/${asset}"; \
    chmod +x /usr/local/bin/hadolint

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv && \
    mv /root/.local/bin/uvx /usr/local/bin/uvx

ENV UV_PROJECT_ENVIRONMENT=.venv
ENV UV_LINK_MODE=copy
ENV PATH="/home/vscode/.venv/bin:${PATH}"
