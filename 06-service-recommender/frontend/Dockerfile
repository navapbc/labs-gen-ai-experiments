FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt /app

# Use --no-deps because transitive dependencies have already been included
# The `find ...` command removes unnecessary files to reduce the image size
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked pip install --no-cache-dir --no-deps -r requirements.txt; \
    find /usr/local/lib \( -type d -a -name test -o -name tests \) -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) -exec rm -rf {} \;

COPY .env .
COPY .streamlit /app/.streamlit
COPY src /app/src

EXPOSE 8501
CMD ["streamlit", "run", "src/main.py", "--server.port=8501", "--server.enableCORS=false"]
# May be needed later: "--server.address=0.0.0.0"
