import logging

from langchain.docstore.document import Document
from langchain_text_splitters import NLTKTextSplitter, RecursiveCharacterTextSplitter, SpacyTextSplitter

logger = logging.getLogger(__name__)


class TextSplitter:
    def __init__(self, llm_client, token_limit, text_splitter_name, **text_splitter_args):
        """
        - llm_client is used to get the number of tokens in a text
        - token_limit is the maximum number of tokens allowed by the embedding model
        """
        self.llm_client = llm_client
        self.token_limit = token_limit
        self.text_splitter = self.create_text_splitter(text_splitter_name, **text_splitter_args)

    def create_text_splitter(self, choice, **kwargs):
        logger.info("Creating %s", choice)
        if choice == "NLTKTextSplitter":
            logger.warning("  Not using arguments: %s", kwargs)
            splitter = NLTKTextSplitter()
        elif choice == "SpacyTextSplitter":
            logger.warning("  Not using arguments: %s", kwargs)
            splitter = SpacyTextSplitter()
        elif choice == "RecursiveCharacterTextSplitter":
            logger.info("  Using arguments: %s", kwargs)
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=kwargs["chunk_size"], chunk_overlap=kwargs["chunk_overlap"]
            )
        return splitter

    def split_into_chunks(self, title, text):
        """
        - title is the title to be used as the source of the text
        - text is the text to split
        """
        entire_text = title + "\n\n" + text
        texts = self.text_splitter.split_text(entire_text)

        logger.info("  Split into %s", len(texts))
        for t in texts:
            token_count = self.llm_client.get_num_tokens(t)
            assert token_count <= self.token_limit, "Exceeded token limit of {self.token_limit}: {token_count}"

        return [Document(page_content=t, metadata={"source": title.strip(), "entire_card": entire_text}) for t in texts]
