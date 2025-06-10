

# To run: uv run bootstrap.py

from phoenix.client import Client
from phoenix.client.types import PromptVersion

content = """\
You are a {{grade_level}} teacher responding to questions from your students.\
Answer your student's question below."""

# TODO: Use environment variable for base_url
base_url = None # defaults to "http://localhost:6006"
client = Client(base_url=base_url)

prompt_name = "teacher"
# TODO: Add authentication to the client -- https://arize.com/docs/phoenix/sdk-api-reference/python/overview#authentication-if-applicable
prompt = client.prompts.create(
    name=prompt_name,
    version=PromptVersion(
        [{"role": "system", "content": content}],
        model_name="gpt-4o-mini",
    ),
)

assert prompt.id is not None, "Prompt creation failed"
# https://arize.com/docs/phoenix/prompt-engineering/how-to-prompts/tag-a-prompt#creating-and-managing-tags
Client().prompts.tags.create(
    prompt_version_id=prompt.id,
    name="staging",
    description="Ready for staging environment"
)
