# https://docs.haystack.deepset.ai/docs/docker
FROM deepset/haystack:base-v2.14.0

RUN pip install chroma-haystack

COPY ./main.py /usr/src/myapp/main.py

ENTRYPOINT ["python", "/usr/src/myapp/main.py"]
