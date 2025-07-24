# This file is for testing a Haystack pipeline before deploying it to Hayhooks
import os
import logging
from pprint import pprint
from dotenv import load_dotenv


from common import haystack_utils
from pipelines.crawler import pipeline_wrapper

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
os.environ["PHOENIX_PROJECT_NAME"] = "haystack-crawler.py"

# Set up pipeline
pipeline_wrapper = pipeline_wrapper.PipelineWrapper()
pipeline_wrapper.setup()

DRAW_PIPELINE = False
if DRAW_PIPELINE:
    pipeline_wrapper.pipeline.draw(os.path.join(os.getcwd(), "pipeline.png"))

# Submit query
# url = "https://www.goodwillcentraltexas.org/programs-and-services/career-opportunities-for-young-adults/"
url = "https://excelcenterhighschool.org/ and https://excelcenterhighschool.org/contact/general-faqs/"
result = pipeline_wrapper.run_api(url)
print("Pipeline result:", result)
