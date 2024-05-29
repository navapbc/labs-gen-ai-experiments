import logging
import os

from anthopic import Anthropic

logger = logging.getLogger(__name__)

CLIENT_NAME = "anthropic"
# These names will be associated with this Python module
MODEL_NAMES = ["claude-3-opus-20240229"]


def init_client(model_name, settings):
    return AnthropicLlmClient(model_name, settings)


class AnthropicLlmClient:
    def __init__(self, model_name, settings):
        self.model_name = model_name
        self.settings = {
            # MAX TOKENS for response
            "max_tokens": int(os.environ.get("MAX_TOKENS", 1024)),
        } | settings

        logger.info("Creating LLM client '%s' with %s", model_name, self.settings)
        # ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
        self.client = Anthropic(
            # api_key=ANTHROPIC_API_KEY,
        )

    def generate_reponse(self, message):
        generated_response = self.client.messages.create(
            model=self.model_name,
            max_tokens=self.settings["max_tokens"],
            messages=[{"role": "user", "content": message}],
        )
        text_response = "\n".join([text_block.text for text_block in generated_response.content])

        return text_response
