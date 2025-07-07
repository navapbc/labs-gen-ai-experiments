# This file is for testing a Haystack pipeline before deploying it to Hayhooks
import logging
import os
from pprint import pprint
from typing import Generator, List

import hayhooks
from dotenv import load_dotenv
from hayhooks import BasePipelineWrapper
from haystack import Pipeline, component
from haystack.components.builders.chat_prompt_builder import ChatPromptBuilder
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses.chat_message import ChatMessage

from common import haystack_utils, phoenix_utils

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


@component
class ChatHistoryPrepender:
    "A component to prepend chat history"

    @component.output_types(full_prompt=List[ChatMessage])
    def run(self, prompt: List[ChatMessage], history: List[ChatMessage]) -> dict:
        print("ChatHistoryPrepender.run called")
        full_prompt = history + prompt
        print("Full prompt:")
        pprint(full_prompt)
        return {"full_prompt": full_prompt}


class PipelineWrapper(BasePipelineWrapper):
    def setup(self) -> None:
        phoenix_utils.configure_phoenix()
        self.pipeline = self._create_pipeline(llm=OpenAIChatGenerator())

    def _create_pipeline(self, llm) -> Pipeline:
        pipeline = Pipeline()

        chat_template: list[ChatMessage] = [ChatMessage.from_user("{{question}}")]

        # https://nava.slack.com/archives/C06ETE82UHM/p1751562152543639
        # Option 1: a single “user” message containing the entire chat history
        #   - Example: https://haystack.deepset.ai/cookbook/conversational_rag_using_memory
        # Option 2: a list of dicts of previous messages
        # See https://community.openai.com/t/how-to-pass-conversation-history-back-to-the-api/697083
        prompt_builder = ChatPromptBuilder(
            template=chat_template, required_variables="*"
        )
        pipeline.add_component("prompt_builder", prompt_builder)

        # Add custom component that outputs list[ChatMessage] to llm.messages
        pipeline.add_component("chat_history_prepender", ChatHistoryPrepender())

        pipeline.add_component("llm", llm)

        pipeline.connect("prompt_builder.prompt", "chat_history_prepender.prompt")
        pipeline.connect("chat_history_prepender.full_prompt", "llm.messages")

        return pipeline

    def run_chat_completion(self, model: str, messages: list, body: dict):
        logger.info(
            "Running chat completion with model: %s, messages: %s", model, messages
        )
        question = hayhooks.get_last_user_message(messages)
        logger.info("Question: %s", question)
        return hayhooks.streaming_generator(
            pipeline=self.pipeline,
            pipeline_run_args={
                "chat_history_prepender": {"history": messages[:-1]},
                "prompt_builder": {"question": question},
            },
        )


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
]

last_question = "Which country is that?"
messages = msg_history + [{"role": "user", "content": last_question}]
result: Generator = pipeline_wrapper.run_chat_completion(
    "model not used", messages, body={}
)
result_chunks = [chunk for chunk in result]
print("Result from the pipeline:")
pprint(result_chunks)


# print("Pipeline result:", result)
# import pdb; pdb.set_trace()
