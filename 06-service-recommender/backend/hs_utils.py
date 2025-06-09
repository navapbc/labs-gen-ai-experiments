from haystack import Document, Pipeline
from haystack.components.builders import PromptBuilder
from haystack.components.builders.chat_prompt_builder import ChatPromptBuilder
from haystack.components.converters import OutputAdapter
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
from haystack.dataclasses import ChatMessage
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.utils import Secret


def create_in_memory_doc_store():
    # Write documents to InMemoryDocumentStore
    document_store = InMemoryDocumentStore()
    document_store.write_documents(
        [
            Document(content="My name is Jean and I live in Paris."),
            Document(content="My name is Mark and I live in Berlin."),
            Document(content="My name is Giorgio and I live in Rome."),
        ]
    )
    return document_store


def create_retriever(document_store: InMemoryDocumentStore):
    return InMemoryBM25Retriever(document_store=document_store)


def create_chat_template():
    return [
        ChatMessage.from_system("You are a helpful assistant."),
        ChatMessage.from_user(
            "Given these documents, answer the question.\n"
            "Documents:\n{% for doc in documents %}{{ doc.content }}{% endfor %}\n"
            "Question: {{question}}\n"
            "Answer:"
        ),
    ]


def create_llm_openai():
    return OpenAIChatGenerator(api_key=Secret.from_env_var("OPENAI_API_KEY"))


def connect_to_openai(rag_pipeline: Pipeline):
    llm = create_llm_openai()
    rag_pipeline.add_component("llm", llm)

    template = create_chat_template()
    # Define required variables explicitly
    prompt_builder = ChatPromptBuilder(
        template=template, required_variables=["question", "documents"]
    )
    # Alternatively, you can use a wildcard to include all variables:
    # prompt_builder = ChatPromptBuilder(template=template, required_variables="*")

    rag_pipeline.add_component("prompt_builder", prompt_builder)
    rag_pipeline.connect("retriever.documents", "prompt_builder.documents")
    rag_pipeline.connect("prompt_builder.prompt", "llm.messages")

