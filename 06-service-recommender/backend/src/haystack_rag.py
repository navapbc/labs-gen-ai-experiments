# This file is for testing a Haystack pipeline before deploying it to Hayhooks
import os
import logging
from pprint import pprint
from dotenv import load_dotenv


from common import haystack_utils
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
os.environ["PHOENIX_PROJECT_NAME"] = "my-haystack-rag.py"

# Set up pipeline
pipeline_wrapper = pipeline_wrapper.PipelineWrapper()
pipeline_wrapper.setup()

DRAW_PIPELINE = False
if DRAW_PIPELINE:
    pipeline_wrapper.pipeline.draw(os.path.join(os.getcwd(), "pipeline.png"))

# Ask a question
question = "Who lives in Paris?"

RUN_RETRIEVER_ONLY = False
if RUN_RETRIEVER_ONLY:
    # Run any pipeline component directly
    retriever = pipeline_wrapper.pipeline.get_component("retriever")
    pprint(retriever)
    retriever_output = retriever.run(query=question)
    print("Retriever-only result:")
    pprint(retriever_output)
else:
    result = pipeline_wrapper.run_api(question)
    print("Pipeline result:", result)
