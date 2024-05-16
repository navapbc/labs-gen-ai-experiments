from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    NLTKTextSplitter,
    SpacyTextSplitter,
)
from llm import ollama_client

# from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate

from langchain_community.vectorstores.faiss import FAISS
from langchain.docstore.document import Document


# split text into chunks
def get_text_chunks(text, chunk_size, chunk_overlap, text_splitter_choice):
    if text_splitter_choice == "2":
        text_splitter = NLTKTextSplitter()
    elif text_splitter_choice == "3":
        text_splitter = SpacyTextSplitter()
    else:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

    texts = text_splitter.split_text(text)

    docs = [
        Document(
            page_content=t,
        )
        for t in texts
    ]

    return docs


CHUNKING_PROMPT = """
You are a helpful AI assistant tasked with summarizing transcripts, however we can only process the transcripts in pieces.
Fill out the fields with the text given {text}. If the template {template} already has the field filled out, do not overwrite this information.
Please fill out the data with the following template:
1. Caller Information:
- Name
- Contact Information
- Availability
- Household Information
2. Reason/Type of Call: e.g., Applying for benefits, Follow-ups
3. Previous Benefits History:
- Applied for
- Receives
- Denied
4. Benefits Discussion: Prefix the discussed benefit with a hashtag (e.g., #SNAP, #LIHEAP)
5. Discussion Points:
- Key information points
6. Documents Needed: e.g., Income verification, Housing documentation
7. Next Steps for Client
8. Next Steps for Agent
"""


def chunking_ingest(transcript, prompt):
    # text_splitter_choice= input() or "2"
    text_chunks = get_text_chunks(
        transcript, chunk_size=750, chunk_overlap=300, text_splitter_choice="2"
    )

    finalized_template = ""
    prompt_template = PromptTemplate.from_template(prompt)

    print("TEXT CHUNK")
    for text in text_chunks:
        formatted_prompt = prompt_template.format(
            text=text.page_content, template=finalized_template
        )
        print("formatted_prompt", formatted_prompt)
        answer = ollama_client(model_name="openhermes", prompt=formatted_prompt)
        print("answer______________________")
        print(answer)
        finalized_template += "\n" + answer
    print(finalized_template)

