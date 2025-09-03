# Base: official devcontainers Python image (keeps things small & reliable)
ARG VARIANT=3.11
FROM mcr.microsoft.com/devcontainers/python:${VARIANT}

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

# AWS CLI v2 (official)
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip" \
 && unzip /tmp/awscliv2.zip -d /tmp \
 && /tmp/aws/install \
 && rm -rf /tmp/aws /tmp/awscliv2.zip

# Pulumi (latest stable)
RUN curl -fsSL https://get.pulumi.com | sh \
 && ln -s /root/.pulumi/bin/pulumi /usr/local/bin/pulumi

# Python deps (install your repo’s requirements if present)
# Copy just requirements first for better Docker layer caching
WORKDIR /workspaces/nkcn
COPY requirements.txt /tmp/requirements.txt
RUN if [ -f /tmp/requirements.txt ]; then pip install --no-cache-dir -r /tmp/requirements.txt; fi

# Optional: AWS helper completions
RUN echo "complete -C '/usr/local/bin/aws_completer' aws" >> /etc/bash.bashrc

# Default back to repo workspace when Codespace attaches
WORKDIR /workspaces/nkcn
