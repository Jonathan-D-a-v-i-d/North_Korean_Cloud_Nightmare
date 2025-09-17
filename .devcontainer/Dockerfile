# syntax=docker/dockerfile:1.6

# Make VARIANT visible to all FROM statements
ARG VARIANT=3.11

# ---- Stage 0: pull a Pulumi binary (multi-arch, no curl needed) ----------
FROM pulumi/pulumi:latest AS pulumi_src
# (Pulumi binary is present in this image; exact path varies by tag/arch)

# ---- Stage 1: your devcontainer base --------------------------------------
FROM mcr.microsoft.com/devcontainers/python:${VARIANT}

ARG TARGETARCH
ENV DEBIAN_FRONTEND=noninteractive
# Belt & suspenders: ensure curl uses the system CA bundle
ENV CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

# System deps & tools
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl ca-certificates apt-transport-https gnupg lsb-release \
      jq unzip zip make git bash-completion gnupg2 \
      oathtool nodejs npm \
 && update-ca-certificates || true \
 && rm -rf /var/lib/apt/lists/*

# --- AWS CLI v2 (multi-arch) ---
RUN case "${TARGETARCH}" in \
        "amd64") AWS_ARCH="x86_64" ;; \
        "arm64") AWS_ARCH="aarch64" ;; \
        *) echo "Unsupported TARGETARCH: ${TARGETARCH}" && exit 1 ;; \
    esac \
 && curl -fsSL --retry 5 --retry-connrefused --show-error \
      "https://awscli.amazonaws.com/awscli-exe-linux-${AWS_ARCH}.zip" -o "/tmp/awscliv2.zip" \
 && unzip /tmp/awscliv2.zip -d /tmp \
 && /tmp/aws/install --bin-dir /usr/local/bin --install-dir /usr/local/aws-cli \
 && rm -rf /tmp/aws /tmp/awscliv2.zip

# --- Pulumi (copy from pulumi/pulumi image; path-agnostic) ---
RUN --mount=from=pulumi_src,source=/,target=/pulumi_img \
    set -e; \
    for p in \
      /usr/local/bin/pulumi \
      /usr/bin/pulumi \
      /pulumi/bin/pulumi \
      /opt/pulumi/bin/pulumi \
    ; do \
      if [ -x "/pulumi_img${p}" ]; then \
        cp "/pulumi_img${p}" /usr/local/bin/pulumi; \
        chmod 0755 /usr/local/bin/pulumi; \
        exit 0; \
      fi; \
    done; \
    echo "Pulumi binary not found in pulumi_src image" >&2; \
    exit 1
# Smoke test to fail the build if pulumi isn't usable
RUN pulumi version

# Optional: AWS CLI tab completion
RUN if command -v aws_completer >/dev/null 2>&1; then \
      echo "complete -C '$(command -v aws_completer)' aws" >> /etc/bash.bashrc; \
    fi

# Pre-install Python deps for layer caching; post-create can re-run to refresh
WORKDIR /tmp
COPY requirements.txt /tmp/requirements.txt
RUN if [ -f /tmp/requirements.txt ]; then pip install --no-cache-dir -r /tmp/requirements.txt; fi

# Default workspace (matches how Dev Containers mounts your repo)
WORKDIR /workspaces/North_Korean_Cloud_Nightmare
