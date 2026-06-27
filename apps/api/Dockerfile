# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# Install compilation tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies in user local directory
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Final minimal production image
FROM python:3.11-slim AS runner

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a secure, restricted non-root system user
RUN groupadd -g 10001 rupeeradar && \
    useradd -u 10001 -g rupeeradar -s /bin/bash -m rupeeradar

# Copy dependency packages from builder
COPY --from=builder /root/.local /home/rupeeradar/.local
ENV PATH=/home/rupeeradar/.local/bin:$PATH

# Copy backend files and change owner to rupeeradar
COPY --chown=rupeeradar:rupeeradar . .

# Set container execution parameters
USER rupeeradar
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
