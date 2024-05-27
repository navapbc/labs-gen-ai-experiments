#!/usr/bin/env python
import logging
from dataclasses import dataclass
from functools import cached_property
from typing import Callable

import dotenv
from langchain_community.embeddings import (HuggingFaceEmbeddings,
                                            SentenceTransformerEmbeddings)
from langchain_community.vectorstores import Chroma

import chatbot
from chatbot import guru_cards, llms, utils
from chatbot.ingest.text_splitter import TextSplitter

logger = logging.getLogger(f"chatbot.{__name__}")


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


class AppState:
    def __init__(self, llm_model, embedding_name):
        self.llm_model = llm_model
        self.embedding_name = embedding_name

    @cached_property
    @utils.timer
    def llm(self):
        logger.info("Creating LLM")
        return llms.init_client(("langchain.ollama", self.llm_model))

    @cached_property
    @utils.timer
    def vectordb(self):
        logger.info("Creating Vector DB")
        embeddings_model = EMBEDDING_MODELS[self.embedding_name].create()
        logger.info("Embeddings model created: %s", embeddings_model)
        return Chroma(
            embedding_function=embeddings_model,
            # Must use collection_name="langchain" -- https://github.com/langchain-ai/langchain/issues/10864#issuecomment-1730303411
            collection_name="langchain",
            persist_directory="./chroma_db",
        )


if __name__ == "__main__":
    dotenv.load_dotenv()
    chatbot.configure_logging()

    app_state = AppState("mistral", "all-MiniLM-L6-v2")

    text_splitter = TextSplitter(
        llm_client=app_state.llm.client,
        token_limit=EMBEDDING_MODELS[app_state.embedding_name].token_limit,
        text_splitter_name="RecursiveCharacterTextSplitter",
        # Use smaller chunks for shorter-length quotes
        chunk_size=250,
        chunk_overlap=100,
    )

    guru_question_answers = guru_cards.GuruCardsProcessor().extract_qa_text_from_guru()
    # Chunk the json data and load into vector db
    for question, answer in guru_question_answers.items():
        logger.info("Processing document: %s", question)
        chunks = text_splitter.split_into_chunks(question, answer)
        app_state.vectordb.add_documents(documents=chunks)
