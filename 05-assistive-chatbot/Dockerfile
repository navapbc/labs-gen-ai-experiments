# syntax=docker/dockerfile:1.2

#====== Create builder image
FROM python:3.11-slim as builder

# create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
# Use external cache to avoid fetching packages from the internet each time -- https://docs.docker.com/build/cache/#use-the-dedicated-run-cache
RUN --mount=type=cache,mode=0755,target=/root/.cache pip3 install -r requirements.txt

#====== Create final image
FROM python:3.11-slim as runner

# Set up a new user so we don't run as root
RUN useradd --create-home -u 1000 tron
RUN chown -R tron:tron /home/tron

USER tron
ENV HOME=/home/tron
WORKDIR $HOME/app

COPY --chown=tron --from=builder /opt/venv /opt/venv
# Activate virtual environment
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
# Ensure all messages always reach console
ENV PYTHONUNBUFFERED=1

# To prevent files from being copied into the image, update .dockerignore
COPY --chown=tron . .

# RUN ./ingest-guru-cards.py

EXPOSE 8000
HEALTHCHECK CMD curl http://localhost:8000 || exit 1
ENTRYPOINT ["chainlit", "run", "--port", "8000", "-h", "chatbot_api.py"]
