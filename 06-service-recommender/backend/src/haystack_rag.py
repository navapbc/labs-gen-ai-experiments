# This file is for testing a Haystack pipeline before deploying it to Hayhooks

import truststore
truststore.inject_into_ssl()

import os
import logging
from pprint import pprint
from time import sleep
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

# endpoint = os.environ.get("PHOENIX_COLLECTOR_ENDPOINT", "https://localhost:6006")
# print("Using Phoenix endpoint: %s", endpoint)
# if config.phoenix_base_url is None:
#     config.phoenix_base_url = endpoint


import contextlib
import requests

old_merge_environment_settings = requests.Session.merge_environment_settings

@contextlib.contextmanager
def no_ssl_verification():
    import warnings
    from urllib3.exceptions import InsecureRequestWarning

    print("Disabling SSL verification for requests")
    opened_adapters = set()

    def merge_environment_settings(self, url, proxies, stream, verify, cert):
        # Verification happens only once per connection so we need to close
        # all the opened adapters once we're done. Otherwise, the effects of
        # verify=False persist beyond the end of this context manager.
        print("--- Opening adapter for URL: %s", url, verify, cert)
        opened_adapters.add(self.get_adapter(url))

        settings = old_merge_environment_settings(self, url, proxies, stream, verify, cert)
        settings['verify'] = False

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
                pass # adapter.close()
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
    # import ssl
    # ssl._create_default_https_context = ssl._create_unverified_context

    import httpx
    import certifi
    # cert_chain = "/Users/yoom/Downloads/otel_phoenix/certs/certificate_chain.txt"
    # print(certifi.contents())

    # Python 3.6 does not rely on MacOS' openSSL anymore. It comes with its own openSSL bundled
    # and doesn't have access on MacOS' root certificates. https://stackoverflow.com/a/42107877
    pem_file = certifi.where()
    # pem_file = os.environ['REQUESTS_CA_BUNDLE']
    print("pem_file:", pem_file)

    from requests.utils import DEFAULT_CA_BUNDLE_PATH
    print("         ", DEFAULT_CA_BUNDLE_PATH)
    # os.environ['SSL_CERT_FILE'] = pem_file
    # pem_file = "amazon_m04.pem"
    # with open(pem_file, 'r') as f:
    #     azn_m04 = f.read()
    # print("Certificate chain:", azn_m04)
    # # Append to certifi.where() file
    # with open(certifi.where(), 'a') as f:
    #     f.write(azn_m04)

    # pem_file = "amazon_certs.pem" # full chain works
    # pem_file = "amazon_m04.pem" # does not work
    # resp = httpx.get(config.phoenix_base_url, verify=pem_file)
    resp = httpx.get(config.phoenix_base_url)
    print("Phoenix service is alive:", resp.read().decode('utf-8'))
    import pdb; pdb.set_trace()


    if config.disable_ssl_verification:
        print("Running with SSL verification disabled")
        with no_ssl_verification():
            main()
    else:
        print("Running with SSL verification enabled")
        main()
