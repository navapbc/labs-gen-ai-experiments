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
os.environ["PHOENIX_PROJECT_NAME"] = "haystack_chat_memory.py"

# Set up pipeline
pipeline_wrapper = pipeline_wrapper.PipelineWrapper()
pipeline_wrapper.setup()


from haystack import component
from typing import List, Generator
from haystack.dataclasses.chat_message import ChatMessage

@component
class ChatHistoryPrepender:
    """
    A component to prepend chat history
    """

    @component.output_types(full_prompt=List[ChatMessage])
    def run(self, prompt: List[ChatMessage], history: List[ChatMessage]) -> dict:
        print("ChatHistoryPrepender.run called")
        full_prompt = history + prompt
        print("Full prompt:")
        pprint(full_prompt)
        return {"full_prompt": full_prompt}

# Add custom component
pipeline = pipeline_wrapper.pipeline
pipeline.add_component("chat_history_prepender", ChatHistoryPrepender())
# Remove connection
# pipeline.remove_connection("prompt_builder.prompt", "llm.messages")
# Add connection to the custom component
pipeline.connect("prompt_builder.prompt", "chat_history_prepender.prompt")
pipeline.connect("chat_history_prepender.full_prompt", "llm.messages")


DRAW_PIPELINE = not False
if DRAW_PIPELINE and not os.path.exists("pipeline.png"):
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
    msg_history = [
        ChatMessage.from_system("You are a RAG-capable bot."),
        ChatMessage.from_system("Use the provided information to answer the question. Respond with the country name only."),
        ]
    messages = msg_history + [{"role": "user", "content": question}]
    result: Generator = pipeline_wrapper.run_chat_completion("model not used", messages, question)
    result_chunks = [chunk for chunk in result]
    print("Result from the pipeline:")
    pprint(result_chunks)


    # print("Pipeline result:", result)
    # import pdb; pdb.set_trace()
