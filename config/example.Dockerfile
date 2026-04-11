# =============================================================================
# silentshell example Dockerfile
# =============================================================================
# This is a minimal starting point. Customise it for your project before
# running 'silentshell start --build'.
#
# Steps to get started:
#   1. Choose a base image that suits your stack (e.g. node:22-slim, python:3.12-slim)
#   2. Install your project's system dependencies
#   3. Install your coding agent (run 'silentshell dockerfile claude' or
#      'silentshell dockerfile pi' for working examples)
#   4. Set CMD to your agent's entrypoint command
# =============================================================================

FROM alpine:3.21

# TODO: install system dependencies your project needs, e.g.:
# RUN apk add --no-cache git curl bash

# =============================================================================
# IMPORTANT: silentshell expects a non-root user matching image_user in your
# .silentshell.toml (default: "mary"). The UID/GID are used for tmpfs mounts
# and volume ownership — keep this in sync with your toml.
# =============================================================================
RUN adduser -D -s /bin/sh mary

# TODO: install your coding agent here

# Switch to the non-root user before setting WORKDIR
USER mary

# =============================================================================
# IMPORTANT: silentshell mounts your project at /project. Do not change this.
# =============================================================================
WORKDIR /project

# TODO: replace this with your agent's entrypoint, e.g. CMD ["claude"]
CMD ["sh", "-c", "echo 'Please configure your silentshell Dockerfile with a CMD for your agent and rebuild with: silentshell start --build'"]
