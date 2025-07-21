# This file is for testing a Haystack pipeline before deploying it to Hayhooks
import logging
import os
from pprint import pprint
from typing import Generator

from dotenv import load_dotenv
from haystack.dataclasses.chat_message import ChatMessage

from common import haystack_utils
from pipelines.ask_until_answered.pipeline_wrapper import PipelineWrapper

logging.basicConfig(
    format="%(levelname)s - %(name)s -  %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

haystack_utils.set_up_tracing()

# Load API keys
load_dotenv()

# Configure OTEL logging to specific Phoenix project
print("Configure Phoenix project name")
os.environ["PHOENIX_PROJECT_NAME"] = "haystack_chat_memory.py"


pipeline_wrapper = PipelineWrapper()
pipeline_wrapper.setup()

DRAW_PIPELINE = False
if DRAW_PIPELINE and not os.path.exists("pipeline.png"):
    pipeline_wrapper.pipeline.draw(os.path.join(os.getcwd(), "pipeline.png"))

msg_history = [
    ChatMessage.from_system(
        "Use the provided information to answer the question.\n"
        "My name is Jean and I live in Paris.\n"
        "My name is Mark and I live in Berlin.\n"
        "My name is Giorgio and I live in Rome.\n"
    ),
    ChatMessage.from_user("Who lives in Paris?"),
    ChatMessage.from_assistant("Jean lives in Paris."),
    ChatMessage.from_user("Harold's location is Berlin."),
]

last_question = "Which country does Harold live in?"
messages = msg_history + [{"role": "user", "content": last_question}]
result: Generator = pipeline_wrapper.run_chat_completion(
    "doesn't matter", messages, body={}
)
result_chunks = [chunk for chunk in result]
print("Result from the pipeline:")
pprint(result_chunks)
