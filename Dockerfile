
# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /app

# Install the Python project and its dependencies
COPY pyproject.toml .
COPY src/ ./src/

RUN pip install --no-cache-dir .

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages and executables
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create a non-root user
RUN useradd --create-home appuser

USER appuser

EXPOSE 8000

CMD ["python", "-m", "youtube_mcp.server"]
