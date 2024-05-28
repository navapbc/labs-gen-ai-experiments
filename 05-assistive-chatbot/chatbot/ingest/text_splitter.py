import logging

from langchain_text_splitters import NLTKTextSplitter, RecursiveCharacterTextSplitter, SpacyTextSplitter

logger = logging.getLogger(__name__)


class TextSplitter:
    def __init__(self, embeddings_model, token_limit, text_splitter_name, **text_splitter_args):
        """
        - embeddings_model is used to get the number of tokens in a text
        - token_limit is the maximum number of tokens allowed by the embedding model
        """
        self.embeddings_model = embeddings_model
        self.token_limit = token_limit
        self.text_splitter = self.create_text_splitter(text_splitter_name, **text_splitter_args)

    def create_text_splitter(self, choice, **kwargs):
        logger.info("Creating %s", choice)
        if choice == "NLTKTextSplitter":
            logger.warning("  Not using arguments: %s", kwargs)
            return NLTKTextSplitter()
        elif choice == "SpacyTextSplitter":
            logger.warning("  Not using arguments: %s", kwargs)
            return SpacyTextSplitter()
        elif choice == "RecursiveCharacterTextSplitter":
            logger.info("  Using arguments: %s", kwargs)
            return RecursiveCharacterTextSplitter(
                chunk_size=kwargs["chunk_size"], chunk_overlap=kwargs["chunk_overlap"]
            )
        else:
            assert False, f"Unknown text splitter: {choice}"

    def split_into_chunks(self, text):
        chunks = self.text_splitter.split_text(text)

        logger.info("  Split into %s", len(chunks))
        for chunk in chunks:
            token_count = len(self.embeddings_model.embed_documents(chunk))
            assert token_count <= self.token_limit, "Exceeded token limit of {self.token_limit}: {token_count}"

        return chunks
