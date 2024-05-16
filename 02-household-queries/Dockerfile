FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/navapbc/labs-gen-ai-experiments.git .
WORKDIR /app/02-household-queries
RUN pip3 install -r requirements.txt

# LABEL org.opencontainers.image.source https://github.com/navapbc/labs-gen-ai-experiments

EXPOSE 8000
HEALTHCHECK CMD curl http://localhost:8000 || exit 1
ENTRYPOINT ["chainlit", "run", "--port", "8000", "-h", "chainlit-household-bot.py"]
