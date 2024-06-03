#!/usr/bin/env python
import logging

import dotenv
from langchain.docstore.document import Document

import chatbot
from chatbot import guru_cards, vector_db
from chatbot.ingest.text_splitter import TextSplitter

logger = logging.getLogger(f"chatbot.{__name__}")

dotenv.load_dotenv()
chatbot.configure_logging()

vectordb_wrapper = vector_db.ingest_vectordb_wrapper

text_splitter = TextSplitter(
    embeddings_model=vectordb_wrapper.embeddings_model,
    token_limit=vector_db.EMBEDDING_MODELS[vectordb_wrapper.embedding_name].token_limit,
    text_splitter_name="RecursiveCharacterTextSplitter",
    # Use smaller chunks for shorter-length quotes
    chunk_size=250,
    chunk_overlap=100,
)

guru_cards_processor = guru_cards.GuruCardsProcessor()
guru_question_answers = guru_cards_processor.extract_qa_text_from_guru()
# Chunk the json data and load into vector db
for question, answer in guru_question_answers.items():
    logger.info("Processing document: %s", question)
    entire_text = question + "\n\n" + answer
    chunks = text_splitter.split_into_chunks(entire_text)
    docs = [Document(page_content=t, metadata={"source": question.strip(), "entire_card": entire_text}) for t in chunks]
    vectordb_wrapper.vectordb.add_documents(documents=docs)
