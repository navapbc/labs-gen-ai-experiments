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

# Update files based on current folder
COPY . .

EXPOSE 8000

# HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["chainlit", "run", "--port", "8000", "-h", "chainlit-household-bot.py"]

# docker build -t chainlit1 .
# docker run --rm -p 8000:8000 chainlit1
