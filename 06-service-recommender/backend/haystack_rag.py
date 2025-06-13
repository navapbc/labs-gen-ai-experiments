# This file is for testing a Haystack pipeline before deploying it to Hayhooks
import os
import logging
from pprint import pprint
from dotenv import load_dotenv

from pipelines.first import rag_pipeline_openai
from common import phoenix_utils

logging.basicConfig(
    format="%(levelname)s - %(name)s -  %(message)s", level=logging.INFO
)
# Show haystack logs
logging.getLogger("haystack").setLevel(logging.INFO)

# https://docs.haystack.deepset.ai/v2.8/docs/tracing#opentelemetry
# To add traces to even deeper levels of your pipelines, we recommend you check out OpenTelemetry integrations, such as:
# - urllib3 instrumentation for tracing HTTP requests in your pipeline,
# - OpenAI instrumentation for tracing OpenAI requests.

# Load API keys
load_dotenv()

# Configure OTEL logging to specific Phoenix project
print("Configuring Phoenix project")
os.environ["PHOENIX_PROJECT_NAME"]="my-haystack-rag.py"

# Set up pipeline
rag_pipeline_openai = rag_pipeline_openai.OpenAiRagPipeline()
rag_pipeline_openai.setup()

DRAW_PIPELINE = False
if DRAW_PIPELINE:
    rag_pipeline_openai.pipeline.draw(os.path.join(os.getcwd(), "pipeline.png"))

# Ask a question
question = "Who lives in Paris?"

RUN_RETRIEVER_ONLY = False
if RUN_RETRIEVER_ONLY:
    # Run any pipeline component directly
    retriever = rag_pipeline_openai.pipeline.get_component("retriever")
    pprint(retriever)
    retriever_output = retriever.run(query=question)
    print("Retriever-only result:")
    pprint(retriever_output)
else:
    result = rag_pipeline_openai.run_api(question)
    print("Pipeline result:", result)
