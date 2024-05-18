FROM python:3.11-slim

WORKDIR /app

# RUN apt-get update && apt-get install -y \
#     build-essential \
#     curl \
#     software-properties-common \
#     git \
#     && rm -rf /var/lib/apt/lists/*

COPY . .
RUN pip3 install -r requirements.txt

# Associate GHCR package with GitHub repo; otherwise, it's associated with the navapbc GitHub organization
# See https://github.com/orgs/navapbc/packages?repo_name=labs-gen-ai-experiments
# LABEL org.opencontainers.image.source https://github.com/navapbc/labs-gen-ai-experiments

EXPOSE 8000
HEALTHCHECK CMD curl http://localhost:8000 || exit 1
ENTRYPOINT ["chainlit", "run", "--port", "8000", "-h", "chainlit-household-bot.py"]

# To test:
# docker build -t chainlit1 .
# docker run --rm -p 8000:8000 chainlit1
