# syntax=docker/dockerfile:1.6

# Make VARIANT visible to all FROM statements
ARG VARIANT=3.11

# ---- Stage 0: We'll install Pulumi directly instead of copying ----------
# FROM pulumi/pulumi:latest AS pulumi_src

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

# --- Install Pulumi using multi-stage approach for complete plugin support ---

# Stage 1: Download and extract Pulumi
RUN case "${TARGETARCH}" in \
        "amd64") PULUMI_ARCH="x64" ;; \
        "arm64") PULUMI_ARCH="arm64" ;; \
        *) echo "Unsupported TARGETARCH: ${TARGETARCH}" && exit 1 ;; \
    esac && \
    PULUMI_VERSION="v3.196.0" && \
    curl -fsSL "https://github.com/pulumi/pulumi/releases/download/${PULUMI_VERSION}/pulumi-${PULUMI_VERSION}-linux-${PULUMI_ARCH}.tar.gz" -o "/tmp/pulumi.tar.gz" && \
    cd /tmp && \
    tar -xzf pulumi.tar.gz && \
    cp pulumi/* /usr/local/bin/ && \
    chmod +x /usr/local/bin/pulumi* && \
    rm -rf pulumi.tar.gz pulumi/

# Stage 2: Install critical Python dependencies for Pulumi
RUN pip install --no-cache-dir grpcio protobuf pulumi

# Stage 3: Create complete Pulumi runtime environment
# This ensures the Python language runtime is properly installed and linked
RUN mkdir -p /usr/local/lib/pulumi && \
    mkdir -p ~/.pulumi/plugins && \
    mkdir -p ~/.pulumi/bin

# Stage 4: Force Python language plugin initialization using pulumi new
RUN cd /tmp && \
    export PULUMI_SKIP_UPDATE_CHECK=true && \
    mkdir test-python-init && \
    cd test-python-init && \
    echo 'Creating test Python project to initialize language plugin...' && \
    yes | pulumi new python --name test-init --description "Plugin initialization test" --force || echo "Project creation completed with expected prompts" && \
    ls -la && \
    test -f __main__.py && echo "Python main file created successfully" || echo "Main file check failed" && \
    test -f Pulumi.yaml && echo "Pulumi config created successfully" || echo "Config file check failed" && \
    cd .. && \
    rm -rf test-python-init

# Stage 5: Final verification that Python language plugin is working
RUN pulumi version && echo "Pulumi version check passed" && \
    cd /tmp && \
    mkdir final-plugin-test && \
    cd final-plugin-test && \
    echo 'name: final-test' > Pulumi.yaml && \
    echo 'runtime: python' >> Pulumi.yaml && \
    echo 'description: Final plugin test' >> Pulumi.yaml && \
    echo 'import pulumi' > __main__.py && \
    echo 'pulumi.export("test", "working")' >> __main__.py && \
    pulumi stack init final-test --non-interactive || echo "Stack init completed" && \
    echo "Final test completed" && \
    cd .. && \
    rm -rf final-plugin-test

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
