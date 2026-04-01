# syntax=docker/dockerfile:1.4

# --- Stage 1: Builder ---
# Use a base Python image
FROM python:3.12-slim AS builder

# Install uv from its GitHub registry image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory
WORKDIR /app

# Copy project files and install dependencies using the lock file
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Copy the application source code
COPY app ./app

# --- Stage 2: Production Runtime ---
# Start from a clean, slim Python image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy the installed application and its virtual environment from the builder stage
COPY --from=builder /app /app

# Place the virtual environment binaries on the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose the port the FastAPI app will run on
EXPOSE 8000

# Command to run the application using the installed `fastapi` command
# Ensure the host is 0.0.0.0 to be accessible outside the container
CMD ["/app/.venv/bin/fastapi", "run", "app/main.py", "--port", "8000", "--host", "0.0.0.0"]
