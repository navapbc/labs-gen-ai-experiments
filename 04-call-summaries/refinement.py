import datetime

from langchain_core.prompts import PromptTemplate

from chunking import get_text_chunks
from llm import select_client
from run import get_transcript


CHUNKING_PROMPT = """
You are a helpful AI assistant tasked with summarizing transcripts, however we can only process the transcripts in pieces.
Please fill out and return the following template: {template} with data in the text: {text}
If the following template already has the field filled out, do not overwrite this information.
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


def refinement_ingest(transcript, prompt):
    text_chunks = get_text_chunks(
        transcript, chunk_size=750, chunk_overlap=300, text_splitter_choice="2"
    )
    prompt_template = PromptTemplate.from_template(prompt)
    template = initial_temp

    client = select_client()
    client.init_client()
    ct = datetime.datetime.now()
    print("current time:-", ct)
    for text in text_chunks:
        formatted_prompt = prompt_template.format(
            text=text.page_content, template=template
        )
        print("Processing Text Chunk")
        template = client.generate_text(prompt=formatted_prompt)
    print("Complete")
    return template


if __name__ == "__main__":
    print(
        refinement_ingest(
            transcript=get_transcript("./multi_benefit_transcript.txt"),
            prompt=CHUNKING_PROMPT,
        )
    )
    ct = datetime.datetime.now()
    print(ct)
