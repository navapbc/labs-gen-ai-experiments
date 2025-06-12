# https://docs.haystack.deepset.ai/docs/docker
FROM deepset/haystack:base-v2.14.0

# Install wget for Docker Compose healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends wget && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
# Use --no-deps because transitive dependencies have already been included
# The `find ...` command removes unnecessary files to reduce the image size
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked pip install --no-cache-dir --no-deps -r requirements.txt; \
    find /usr/local/lib \( -type d -a -name test -o -name tests \) -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) -exec rm -rf {} \;

COPY *.py .
# https://github.com/deepset-ai/hayhooks/tree/main/examples/shared_code_between_wrappers
COPY common/ ./common/
ENV HAYHOOKS_ADDITIONAL_PYTHON_PATH=.

# Haystack pipelines defined under this folder is automatically deployed on Hayhooks startup
COPY pipelines/ ./pipelines/

ENV LOG=DEBUG
CMD ["hayhooks", "run", "--host", "0.0.0.0"]
