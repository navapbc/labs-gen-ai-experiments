FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y \
    curl unzip \
    && rm -rf /var/lib/apt/lists/*

ARG GURU_CARDS_URL
RUN echo "Downloading from ${GURU_CARDS_URL}" \
    && curl -L "${GURU_CARDS_URL}" > download.zip \
    && unzip -o download.zip \
    && rm download.zip \
    && mv guru_cards_for_nava--Multi-benefit.json guru_cards_for_nava.json

# Update .dockerignore to prevent files from being copied into the image
COPY . .

RUN ./ingest-guru-cards.py

EXPOSE 8000
HEALTHCHECK CMD curl http://localhost:8000 || exit 1
ENTRYPOINT ["chainlit", "run", "--port", "8000", "-h", "chatbot-chainlit.py"]
