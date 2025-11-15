# Use Python 3.8 as base image
FROM python:3.8-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT=8000

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories first
RUN mkdir -p /app/templates/Meetup \
    && mkdir -p /app/staticfiles \
    && mkdir -p /app/static

# Create a non-root user
RUN useradd -m appuser

# Copy project files with correct ownership
COPY --chown=appuser:appuser . .

# Set permissions
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE ${PORT}

# Start Daphne server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"] 