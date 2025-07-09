import logging
from pprint import pformat
from textwrap import dedent

import hayhooks
from hayhooks import BasePipelineWrapper
from haystack import Pipeline
from haystack.components.builders.chat_prompt_builder import ChatPromptBuilder
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses.chat_message import ChatMessage

# https://github.com/deepset-ai/hayhooks?tab=readme-ov-file#sharing-code-between-pipeline-wrappers
from common import haystack_utils, phoenix_utils

logger = logging.getLogger(__name__)


class PipelineWrapper(BasePipelineWrapper):
    def setup(self) -> None:
        phoenix_utils.configure_phoenix()
        self.pipeline = self._create_pipeline(llm=OpenAIChatGenerator())

    def _create_pipeline(self, llm) -> Pipeline:
        pipeline = Pipeline()

        system_prompt = "If Harold's location is mentioned in the conversation history, then state Harold's location and answer the question, else ask for Harold's location."
        msg_history_prompt = dedent(
            """
                Conversation history:
                {% for msg in history %}
                {{ msg.role.value }}: {{ msg.text }}
                {% endfor %}
            """
        )

        chat_template: list[ChatMessage] = [
            ChatMessage.from_system(system_prompt),
            ChatMessage.from_user(msg_history_prompt),
            ChatMessage.from_user("Question: {{question}}"),
        ]

        # https://nava.slack.com/archives/C06ETE82UHM/p1751562152543639
        # Option 1: a single “user” message containing the entire chat history
        #   - Example: https://haystack.deepset.ai/cookbook/conversational_rag_using_memory
        # Option 2: a list of dicts of previous messages
        # See https://community.openai.com/t/how-to-pass-conversation-history-back-to-the-api/697083
        # Option 1 is implemented here using ChatPromptBuilder
        prompt_builder = ChatPromptBuilder(
            template=chat_template, required_variables="*"
        )
        pipeline.add_component("prompt_builder", prompt_builder)

        pipeline.add_component("llm", llm)

        pipeline.connect("prompt_builder.prompt", "llm.messages")

        return pipeline

    # Called for the `{pipeline_name}/run` endpoint
    def run_api(self, question: str) -> str:
        results = self.pipeline.run(
            {
                "prompt_builder": {"question": question},
            }
        )
        logger.info("Results: %s", pformat(results))
        replies = results.get("llm", {}).get("replies", [])
        if not replies:
            logger.warning("No replies found in the results.")
            return "No replies found."
        else:
            logger.info("Replies: %s", replies)
            if hasattr(replies[0], "text"):
                return replies[0].text
            else:
                return replies[0]

    def run_chat_completion(self, model: str, messages: list, body: dict):
        logger.info(
            "Running chat completion with model: %s, messages: %s", model, messages
        )
        question = hayhooks.get_last_user_message(messages)
        # prev_user_messages = [
        #     ChatMessage.from_user(msg["content"]) for msg in messages[:-1] if msg["role"] == "user"
        # ]
        logger.info("Question: %s", question)
        return hayhooks.streaming_generator(
            pipeline=self.pipeline,
            pipeline_run_args={
                "prompt_builder": {
                    "history": haystack_utils.to_chat_messages(messages[:-1]),
                    "question": question,
                },
            },
        )
