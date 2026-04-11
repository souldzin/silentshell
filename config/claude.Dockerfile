# Dockerfile for claude coding agent
FROM node:20-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# Install mise (polyglot tool version manager)
RUN curl https://mise.run | MISE_INSTALL_PATH=/usr/local/bin/mise sh

# Create a non-root user
RUN useradd -m -s /bin/bash mary && \
    mkdir -p /home/mary/.claude && \
    chown -R mary:mary /home/mary

# Switch to non-root user
USER mary

# Install claude code
RUN curl -fsSL https://claude.ai/install.sh | bash
ENV PATH="/home/mary/.local/bin:$PATH"

# Set up the project mount point
WORKDIR /project

# Default command - run pi in interactive mode
CMD ["claude"]
