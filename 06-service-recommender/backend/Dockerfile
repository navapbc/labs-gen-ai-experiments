# https://docs.haystack.deepset.ai/docs/docker
FROM deepset/haystack:base-v2.14.0

WORKDIR /app

COPY requirements.txt .

# "always pass --no-deps because Poetry has already resolved the dependencies so that all direct and transitive requirements are included"
# `find ...` removes about 400MB of space
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked pip install --no-cache-dir --no-deps -r requirements.txt; \
    find /usr/local/lib \( -type d -a -name test -o -name tests \) -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) -exec rm -rf {} \;

COPY *.py .
# https://github.com/deepset-ai/hayhooks/tree/main/examples/shared_code_between_wrappers#option-3-launch-hayhooks-with-the---additional-python-path-flag
# Documentation has a typo: https://github.com/deepset-ai/hayhooks/issues/124
COPY common/ ./common/
ENV HAYHOOKS_ADDITIONAL_PYTHON_PATH=.
COPY pipelines/ ./pipelines/

# CMD ["python", "/app/haystack_rag.py"]
# COPY entrypoint.sh .
# CMD ["/app/entrypoint.sh"]
ENV LOG=DEBUG
CMD ["hayhooks", "run", "--host", "0.0.0.0"]
