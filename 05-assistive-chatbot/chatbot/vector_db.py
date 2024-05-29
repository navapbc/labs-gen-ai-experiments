import logging
from dataclasses import dataclass
from functools import cached_property
from typing import Callable

from langchain_community.embeddings import HuggingFaceEmbeddings, SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma

from chatbot import utils

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingsModel:
    name: str
    token_limit: int
    create: Callable


_EMBEDDINGS_MODEL_LIST = [
    EmbeddingsModel("all-MiniLM-L6-v2", 256, lambda: SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")),
    EmbeddingsModel("HuggingFace::all-MiniLM-L6-v2", 256, lambda: HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")),
    EmbeddingsModel(
        "BAAI/bge-small-en-v1.5", 512, lambda: SentenceTransformerEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    ),
    EmbeddingsModel(
        "mixedbread-ai/mxbai-embed-large-v1",
        1024,
        lambda: SentenceTransformerEmbeddings(model_name="mixedbread-ai/mxbai-embed-large-v1"),
    ),
    # EmbeddingsModel("Google::embedding-001", 2048, lambda: GoogleGenerativeAIEmbeddings(model="models/embedding-001")),
    # EmbeddingsModel("Google::text-embedding-004", 768, lambda: GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")),
]

EMBEDDING_MODELS = {model.name: model for model in _EMBEDDINGS_MODEL_LIST}


class LocalLangchainChromaVectorDb:
    def __init__(self, embedding_name="all-MiniLM-L6-v2", folder="./chroma_db"):
        self.embedding_name = embedding_name
        self.folder = folder

    @cached_property
    @utils.timer
    def embeddings_model(self):
        logger.info("Creating embeddings model: %s", self.embedding_name)
        return EMBEDDING_MODELS[self.embedding_name].create()

    @cached_property
    @utils.timer
    def vectordb(self):
        logger.info("Creating Vector DB: %s", self.folder)
        return Chroma(
            embedding_function=self.embeddings_model,
            persist_directory=self.folder,
            # Must use collection_name="langchain" -- https://github.com/langchain-ai/langchain/issues/10864#issuecomment-1730303411
            collection_name="langchain",
        )


ingest_vectordb_wrapper = LocalLangchainChromaVectorDb()
