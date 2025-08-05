# This file is for testing a Haystack pipeline before deploying it to Hayhooks

import contextlib
import logging
import os
from pprint import pprint
from time import sleep

import requests
from dotenv import load_dotenv

from common import haystack_utils
from common.app_config import config
from pipelines.first import pipeline_wrapper

logging.basicConfig(
    format="%(levelname)s - %(name)s -  %(message)s", level=logging.INFO
)


# https://docs.haystack.deepset.ai/v2.8/docs/tracing#opentelemetry
# To add traces to even deeper levels of your pipelines, we recommend you check out OpenTelemetry integrations, such as:
# - urllib3 instrumentation for tracing HTTP requests in your pipeline,
# - OpenAI instrumentation for tracing OpenAI requests.
haystack_utils.set_up_tracing()

# Load API keys
load_dotenv()

# Configure OTEL logging to specific Phoenix project
print("Configure Phoenix project name")
os.environ["PHOENIX_PROJECT_NAME"] = "ssl-my-haystack-rag.py"


old_merge_environment_settings = requests.Session.merge_environment_settings


@contextlib.contextmanager
def no_ssl_verification():
    # import warnings
    # from urllib3.exceptions import InsecureRequestWarning

    print("Disabling SSL verification for requests")
    opened_adapters = set()

    def merge_environment_settings(self, url, proxies, stream, verify, cert):
        # Verification happens only once per connection so we need to close
        # all the opened adapters once we're done. Otherwise, the effects of
        # verify=False persist beyond the end of this context manager.
        print("--- Opening adapter for URL: %s", url, verify, cert)
        opened_adapters.add(self.get_adapter(url))

        settings = old_merge_environment_settings(
            self, url, proxies, stream, verify, cert
        )
        settings["verify"] = False

        return settings

    requests.Session.merge_environment_settings = merge_environment_settings

    try:
        yield
        # with warnings.catch_warnings():
        #     warnings.simplefilter('ignore', InsecureRequestWarning)
        #     yield
    finally:
        requests.Session.merge_environment_settings = old_merge_environment_settings

        for adapter in opened_adapters:
            try:
                adapter.close()
            except Exception as e:
                print("Error closing adapter: %s", e)


def main():
    # Set up pipeline
    pipeline = pipeline_wrapper.PipelineWrapper()
    pipeline.setup()

    DRAW_PIPELINE = False
    if DRAW_PIPELINE:
        pipeline.pipeline.draw(os.path.join(os.getcwd(), "pipeline.png"))

    # Ask a question
    question = "Who lives in Paris?"

    RUN_RETRIEVER_ONLY = False
    if RUN_RETRIEVER_ONLY:
        # Run any pipeline component directly
        retriever = pipeline.pipeline.get_component("retriever")
        pprint(retriever)
        retriever_output = retriever.run(query=question)
        print("Retriever-only result:")
        pprint(retriever_output)
    else:
        result = pipeline.run_api(question)
        print("Pipeline result:", result)
    sleep(5)  # Allow time for traces to be sent
    print("Done running pipeline")


if __name__ == "__main__":
    import certifi
    import httpx

    # Python 3.6 does not rely on MacOS' openSSL anymore. It comes with its own openSSL bundled
    # and doesn't have access on MacOS' root certificates. https://stackoverflow.com/a/42107877
    print("certifi.where():", certifi.where())
    print("request.default:", requests.utils.DEFAULT_CA_BUNDLE_PATH)
    resp = httpx.get(config.phoenix_base_url)
    print("Phoenix service is alive:", resp.read().decode("utf-8"))

    if config.disable_ssl_verification:
        print("Running with SSL verification disabled")
        with no_ssl_verification():
            main()
    else:
        print("Running with SSL verification enabled")
        main()
