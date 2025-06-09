FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt /app

# Created using: poetry export -f requirements.txt --output requirements.txt
# "always pass --no-deps because Poetry has already resolved the dependencies so that all direct and transitive requirements are included"
# `find ...` removes about 400MB of space
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked pip install --no-cache-dir --no-deps -r requirements.txt; \
    find /usr/local/lib \( -type d -a -name test -o -name tests \) -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) -exec rm -rf {} \;

COPY .env .
COPY .streamlit /app/.streamlit
COPY src /app/src

EXPOSE 8501

CMD ["streamlit", "run", "src/main.py", "--server.port=8501", "--server.enableCORS=false"]
# streamlit run src/main.py --server.port=8501 --server.enableCORS=false
# May be needed later: "--server.address=0.0.0.0"
