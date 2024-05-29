import datetime

from langchain.docstore.document import Document
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    NLTKTextSplitter,
    SpacyTextSplitter,
)

from llm import LLM
from run import get_transcript


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


MAP_TEMPLATE = """
You are a helpful AI assistant tasked with summarizing transcripts. The following is a set of transcript pieces:
{transcript_chunk}
Please summarize the sections, include key details.
"""

REDUCE_TEMPLATE = """The following is set of summaries:
{summaries}
Take these fill out this template:
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


def select_client():
    print("""
    Select an llm
    1. openhermes (default)
    2. dolphin
    3. gemini
    4. gpt 4
    5. gpt 4o
    6. claude 3
    """)

    llm = input() or "1"

    if llm == "2":
        client = LLM(client_name="ollama", model_name="dolphin-mistral")
        print("""----------
            Dolphin
            """)

    elif llm == "3":
        client = LLM(client_name="gemini")
        print("""----------
            Gemini Flash 1.5
            """)
    elif llm == "4":
        print("""----------
        GPT 4
        """)
        client = LLM(client_name="gpt", model_name="gpt4")
    elif llm == "5":
        print("""----------
        GPT 4o
        """)
        client = LLM(client_name="gpt", model_name="gpt-4o")
    elif llm == "6":
        print("""----------
            Claude 3
            """)
        client = LLM(client_name="claude")
    else:
        print("""
            Openhermes
            """)
        client = LLM(client_name="ollama", model_name="openhermes")
    return client


def chunking_ingest(transcript):
    text_chunks = get_text_chunks(
        transcript, chunk_size=750, chunk_overlap=300, text_splitter_choice="2"
    )
    client = select_client()
    client.init_client()
    ct = datetime.datetime.now()
    print(ct)
    summaries = []
    for text_chunk in text_chunks:
        summary_template = PromptTemplate.from_template(template=MAP_TEMPLATE)
        formatted_prompt = summary_template.format(transcript_chunk=text_chunk)
        summary = client.generate_text(formatted_prompt)
        summaries.append(summary)

    collected_summaries_template = PromptTemplate.from_template(
        template=REDUCE_TEMPLATE
    )

    text_summary = "\n".join(summaries)
    prompt_with_all_summaries = collected_summaries_template.format(
        summaries=text_summary
    )
    filled_out_template = client.generate_text(prompt_with_all_summaries)
    print(filled_out_template)


if __name__ == "__main__":
    print(
        chunking_ingest(
            transcript=get_transcript("./multi_benefit_transcript.txt"),
        )
    )
    ct = datetime.datetime.now()
    print(ct)
