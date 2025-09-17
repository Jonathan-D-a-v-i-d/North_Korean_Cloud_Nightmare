# Base: official devcontainers Python image (keeps things small & reliable)
ARG VARIANT=3.11
FROM mcr.microsoft.com/devcontainers/python:${VARIANT}

ARG TARGETARCH
# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# System deps + helpful tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates apt-transport-https gnupg lsb-release \
    jq unzip zip make git bash-completion gnupg2 \
    # oathtool (TOTP)
    oathtool \
    # Node/npm in case you need small CLIs later
    nodejs npm \
    && rm -rf /var/lib/apt/lists/*

# --- AWS CLI v2 (multi-arch) ---
# Map devcontainers TARGETARCH -> AWS arch labels
RUN case "${TARGETARCH}" in \
      "amd64") AWS_ARCH="x86_64" ;; \
      "arm64") AWS_ARCH="aarch64" ;; \
      *) echo "Unsupported TARGETARCH: ${TARGETARCH}" && exit 1 ;; \
    esac \
 && curl -L "https://awscli.amazonaws.com/awscli-exe-linux-${AWS_ARCH}.zip" -o "/tmp/awscliv2.zip" \
 && unzip /tmp/awscliv2.zip -d /tmp \
 && /tmp/aws/install --bin-dir /usr/local/bin --install-dir /usr/local/aws-cli \
 && rm -rf /tmp/aws /tmp/awscliv2.zip

# Pulumi (latest stable)
RUN curl -fsSL https://get.pulumi.com | sh \
 && ln -s /root/.pulumi/bin/pulumi /usr/local/bin/pulumi

# Pre-install Python dependencies (cached by Docker layer)
WORKDIR /workspaces/nkcn
COPY requirements.txt /tmp/requirements.txt
RUN if [ -f /tmp/requirements.txt ]; then pip install --no-cache-dir -r /tmp/requirements.txt; fi


# Python deps (install your repo’s requirements if present)
# Copy just requirements first for better Docker layer caching
WORKDIR /workspaces/nkcn
COPY requirements.txt /tmp/requirements.txt
RUN if [ -f /tmp/requirements.txt ]; then pip install --no-cache-dir -r /tmp/requirements.txt; fi

# Optional: AWS helper completions
RUN echo "complete -C '/usr/local/bin/aws_completer' aws" >> /etc/bash.bashrc

# Default back to repo workspace when Codespace attaches
WORKDIR /workspaces/nkcn
