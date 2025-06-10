import os
import logging

from common import hs_utils
from dotenv import load_dotenv
from hayhooks_pipelines.first import pipeline_wrapper

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
logger = logging.getLogger(f"my_haystack_rag.{__name__}")

# https://docs.haystack.deepset.ai/v2.8/docs/tracing#opentelemetry
# To add traces to even deeper levels of your pipelines, we recommend you check out OpenTelemetry integrations, such as:
# - urllib3 instrumentation for tracing HTTP requests in your pipeline,
# - OpenAI instrumentation for tracing OpenAI requests.


if __name__ == "__main__":
    logging.basicConfig(
        format="%(levelname)s - %(name)s -  %(message)s", level=logging.INFO
    )
    logging.getLogger("haystack").setLevel(logging.INFO)
    load_dotenv()

    hs_utils.configure_phoenix("my-haystack-rag")

    pipeline_wrapper = pipeline_wrapper.PipelineWrapper()
    pipeline_wrapper.setup()

    # Ask a question
    question = "Who lives in Paris?"
    result = pipeline_wrapper.run_api(question)
    logger.info("Result: %s", result)

    # if False:
    #     pprint(retriever)
    #     # run() any component directly
    #     retriever_out = retriever.run(query=question)

    pipeline_wrapper.pipeline.draw(os.path.join(os.getcwd(), "pipeline.png"))
