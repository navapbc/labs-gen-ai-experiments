# This file is for testing a Haystack pipeline before deploying it to Hayhooks

import contextlib
import logging
import os
import socket
import ssl
from pprint import pprint
from time import sleep

import certifi
import httpx
import requests
from common import haystack_utils
from common.app_config import config
from dotenv import load_dotenv
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


def get_certificate_hostnames(hostname, port):
    # Establish a connection to the server
    sock = socket.create_connection((hostname, port))
    ctx = ssl.create_default_context()
    # ctx.check_hostname = False
    sslsock = ctx.wrap_socket(sock, server_hostname=hostname)

    pprint(sslsock.getpeercert())
    common_name = next(
        s[0][1] for s in sslsock.getpeercert()["subject"] if s[0][0] == "commonName"
    )
    san_list = list(s[1] for s in sslsock.getpeercert()["subjectAltName"])
    sslsock.close()
    sock.close()
    return common_name, san_list


def check_ssl_certificate():
    domain_and_port = config.phoenix_base_url.split("://")[-1].split(":")
    target_hostname = domain_and_port[0]
    port = domain_and_port[1]
    cn, sans = get_certificate_hostnames(target_hostname, port)

    print(f"Connected to: {target_hostname}")
    print(f"Certificate Common Name (CN): {cn}")
    print(f"Certificate Subject Alternative Names (SANs): {sans}")

    # Compare with the target hostname
    if target_hostname != cn and target_hostname not in sans:
        print(f"Hostname mismatch: '{target_hostname}' != '{cn}' or any SANs.")
    else:
        print(f"Hostname '{target_hostname}' matches the certificate.")


def test_basic_https_request():
    # Python 3.6 does not rely on MacOS' openSSL anymore. It comes with its own openSSL bundled
    # and doesn't have access on MacOS' root certificates. https://stackoverflow.com/a/42107877
    print("certifi.where():", certifi.where())
    assert certifi.where() == requests.utils.DEFAULT_CA_BUNDLE_PATH
    check_ssl_certificate()

    resp = httpx.get(config.phoenix_base_url)
    print("Phoenix service is alive:", resp.read().decode("utf-8"))


# Usage: PHOENIX_COLLECTOR_ENDPOINT=https://localhost:6006 uv run src/haystack_rag.py
if __name__ == "__main__":
    if config.disable_ssl_verification:
        print("Running with SSL verification disabled")
        with no_ssl_verification():
            main()
    else:
        try:
            test_basic_https_request()
            print("Running with SSL verification enabled")
            main()
        except ssl.SSLCertVerificationError as e:
            print(
                "Please ensure the self-signed root CA certificate is appended to ",
                certifi.where(),
                "as done in the Dockerfile",
            )
            raise e
