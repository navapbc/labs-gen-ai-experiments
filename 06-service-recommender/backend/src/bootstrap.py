# To run: uv run bootstrap.py

from phoenix.client.types import PromptVersion

from common.phoenix_utils import create_client

client = create_client()

# Use "mustache" syntax for placeholder variables
prompt = client.prompts.create(
    name="sample_rag",
    prompt_description="Sample RAG prompt",
    version=PromptVersion(
        [
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": (
                    "Given these documents, answer the question.\n"
                    "Documents:\n{% for doc in documents %}{{ doc.content }}{% endfor %}\n"
                    "Question: {{question}}\n"
                    "Answer:"
                ),
            },
        ],
        model_provider="OPENAI",
        model_name="gpt-4o-mini",
    ),
)
assert prompt.id is not None, "Prompt creation failed"
print(prompt.id)

# https://arize.com/docs/phoenix/prompt-engineering/how-to-prompts/tag-a-prompt#creating-and-managing-tags
client.prompts.tags.create(
    prompt_version_id=prompt.id,
    name="staging",
    description="Ready for staging environment",
)
