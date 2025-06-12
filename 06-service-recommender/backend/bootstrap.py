# To run: uv run bootstrap.py

from phoenix.client import Client
from phoenix.client.types import PromptVersion

content = """You are a {{grade_level}} teacher responding to questions from your student. \
Answer your student's question below."""

base_url = None # defaults to "http://localhost:6006"
client = Client(base_url=base_url)

prompt = client.prompts.create(
    name="teacher",
    prompt_description="Sample teacher-student prompt",
    version=PromptVersion(
        [{"role": "system", "content": content}],
        model_name="gpt-4o-mini",
    ),
)
assert prompt.id is not None, "Prompt creation failed"
print(prompt.id)

# https://arize.com/docs/phoenix/prompt-engineering/how-to-prompts/tag-a-prompt#creating-and-managing-tags
Client().prompts.tags.create(
    prompt_version_id=prompt.id,
    name="staging",
    description="Ready for staging environment"
)
