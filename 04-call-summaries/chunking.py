from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    NLTKTextSplitter,
    SpacyTextSplitter,
)
from langchain_core.prompts import PromptTemplate
from langchain.docstore.document import Document
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


CHUNKING_PROMPT = """
You are a helpful AI assistant tasked with summarizing transcripts, however we can only process the transcripts in pieces.
Fill out the fields with the text given {text}. If the following template already has the field filled out, do not overwrite this information.
Please fill out the data with the following template: {template}
"""

initial_temp = """
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
    text_chunks = get_text_chunks(
        transcript, chunk_size=750, chunk_overlap=300, text_splitter_choice="2"
    )
    prompt_template = PromptTemplate.from_template(prompt)
    template = initial_temp

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

    client.get_client()
    for text in text_chunks:
        formatted_prompt = prompt_template.format(
            text=text.page_content, template=template
        )
        print("Processing Text Chunk")
        template = client.generate_text(prompt=formatted_prompt)
    print("Complete")
    return template

if __name__ == "__main__":
    print(chunking_ingest(transcript=get_transcript(), prompt=CHUNKING_PROMPT))
