# Base: official devcontainers Python image (multi-arch)
ARG VARIANT=3.11
FROM mcr.microsoft.com/devcontainers/python:${VARIANT}

ARG TARGETARCH
ENV DEBIAN_FRONTEND=noninteractive

# System deps + tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates apt-transport-https gnupg lsb-release \
    jq unzip zip make git bash-completion gnupg2 \
    oathtool \
    nodejs npm \
    && rm -rf /var/lib/apt/lists/*

# --- AWS CLI v2 (multi-arch) ---
RUN case "${TARGETARCH}" in \
      "amd64") AWS_ARCH="x86_64" ;; \
      "arm64") AWS_ARCH="aarch64" ;; \
      *) echo "Unsupported TARGETARCH: ${TARGETARCH}" && exit 1 ;; \
    esac \
 && curl -L "https://awscli.amazonaws.com/awscli-exe-linux-${AWS_ARCH}.zip" -o "/tmp/awscliv2.zip" \
 && unzip /tmp/awscliv2.zip -d /tmp \
 && /tmp/aws/install --bin-dir /usr/local/bin --install-dir /usr/local/aws-cli \
 && rm -rf /tmp/aws /tmp/awscliv2.zip

# Make sure any extra certs provided by Dev Containers are activated before we curl anything.
# (Harmless if none are present.)
RUN update-ca-certificates || true

# --- Pulumi (APT first; fallback to tarball; system-wide) ---
# APT repo (multi-arch)
RUN curl -fsSL https://get.pulumi.com/apt/pubkey.gpg | gpg --dearmor -o /usr/share/keyrings/pulumi-archive-keyring.gpg \
 && echo "deb [signed-by=/usr/share/keyrings/pulumi-archive-keyring.gpg] https://get.pulumi.com/apt stable main" > /etc/apt/sources.list.d/pulumi.list \
 && apt-get update && apt-get install -y pulumi || true

# Fallback if apt didn’t land (handles SSL hiccups / repo issues)
ARG TARGETARCH
RUN if ! command -v pulumi >/dev/null 2>&1; then \
      case "${TARGETARCH}" in \
        "amd64") P_ARCH="x64" ;; \
        "arm64") P_ARCH="arm64" ;; \
        *) echo "Unsupported TARGETARCH: ${TARGETARCH}" && exit 1 ;; \
      esac ; \
      P_VER="$(curl -fsSL https://www.pulumi.com/latest-version)"; \
      curl -fsSL --retry 5 --retry-connrefused --show-error \
        "https://get.pulumi.com/releases/sdk/pulumi-v${P_VER}-linux-${P_ARCH}.tar.gz" -o /tmp/pulumi.tgz; \
      tar -xzf /tmp/pulumi.tgz -C /opt; \
      ln -sf /opt/pulumi/pulumi /usr/local/bin/pulumi; \
      rm -f /tmp/pulumi.tgz; \
    fi \
 && pulumi version




# Optional: make aws completion resilient (v2 path can vary)
RUN if command -v aws_completer >/dev/null 2>&1; then \
      echo "complete -C '$(command -v aws_completer)' aws" >> /etc/bash.bashrc; \
    fi

# Pre-install Python deps for layer caching (copy only requirements to leverage cache)
WORKDIR /tmp
COPY requirements.txt /tmp/requirements.txt
RUN if [ -f /tmp/requirements.txt ]; then pip install --no-cache-dir -r /tmp/requirements.txt; fi

# Default workspace matches how Dev Containers mounts your repo
WORKDIR /workspaces/North_Korean_Cloud_Nightmare
