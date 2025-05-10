FROM python:3.12

# Install system dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg libportaudio2 && \
    rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Install Python dependencies first for cache
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose Flask port
EXPOSE 5000

# Default command (can be overridden by docker compose)
CMD ["python", "dream_recorder.py"]

ENV PYTHONPATH=/app 