# Dockerfile for the realbot project
# Uses uv's 3.13 slim image
# installs the project's runtime dependencies explicitly (avoids relying on a build-backend
# in pyproject.toml), copies source, and runs main.py.

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Create a non-root user and use it
# if you use podman rootless, you may need to adjust permissions on the host
# or comment out lines below to run as "root"
RUN useradd --shell /bin/bash appuser && chown -R appuser:appuser /app

USER appuser

# Default command: run the main script
CMD ["uv", "run","main.py"]
