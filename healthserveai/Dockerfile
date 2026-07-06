# Use a lightweight Debian-slim base image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy only dependency files first to leverage caching
COPY pyproject.toml uv.lock ./

# Install dependencies without installing the project itself
RUN uv sync --frozen --no-install-project --no-dev

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Copy the virtual environment from the builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy project files
COPY app ./app
COPY frontend ./frontend

# Start server reading $PORT, defaulting to 8000
CMD uvicorn app.server:app --host 0.0.0.0 --port ${PORT:-8000}
