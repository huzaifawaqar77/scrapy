FROM python:3.11-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
# Tell Playwright to store browsers in a shared folder so our non-root user can access them
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright OS dependencies as root
RUN playwright install-deps chromium

# Create a non-root user and group for enterprise-grade security
RUN addgroup --system appgroup && \
    adduser --system --group appuser && \
    mkdir -p /ms-playwright && \
    chown -R appuser:appgroup /ms-playwright /app

# Switch to the non-root user
USER appuser

# Install the Chromium browser binaries under the non-root user's environment
RUN playwright install chromium

# Copy the rest of the application code
COPY . .

# Expose port (Coolify automatic port detection)
EXPOSE 8000

# Start the Flask web application using Gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "app:app"]
