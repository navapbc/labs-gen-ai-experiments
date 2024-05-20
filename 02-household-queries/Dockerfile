FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Associate GHCR package with GitHub repo; otherwise, it's associated with the navapbc GitHub organization
# See https://github.com/orgs/navapbc/packages?repo_name=labs-gen-ai-experiments
# LABEL org.opencontainers.image.source https://github.com/navapbc/labs-gen-ai-experiments

RUN apt-get update && apt-get install -y \
    curl unzip \
    && rm -rf /var/lib/apt/lists/*

COPY . .
ARG GURU_CARDS_URL
RUN echo "Downloading from ${GURU_CARDS_URL}" \
    && curl -L "${GURU_CARDS_URL}" > download.zip \
    && unzip -o download.zip \
    && rm download.zip \
    && mv guru_cards_for_nava--Multi-benefit.json guru_cards_for_nava.json

RUN ./decompose-questions.py 0

EXPOSE 8000
HEALTHCHECK CMD curl http://localhost:8000 || exit 1
ENTRYPOINT ["chainlit", "run", "--port", "8000", "-h", "chainlit-summaries.py"]

# To test:
# docker build -t chainlit1 .
# docker run --rm -p 8000:8000 chainlit1
