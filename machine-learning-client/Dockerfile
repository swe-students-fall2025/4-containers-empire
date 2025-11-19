FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for TensorFlow/Keras
RUN apt-get update && apt-get install -y \
    libhdf5-dev \
    pkg-config \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/uploads

CMD ["python", "src/worker.py"]