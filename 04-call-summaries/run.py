from langchain_core.prompts import PromptTemplate

from llm import select_client


# download transcripts from https://drive.google.com/drive/folders/19r6x3Zep4N9Rl_x4n4H6RpWkXviwbxyw?usp=sharing
def get_transcript(file_path="./transcript.txt"):
    file = open(file_path, encoding="utf-8")
    content = file.read()
    file.close()
    return content


PROMPT = """
You are a helpful AI assistant tasked with summarizing transcripts, only use the data in the transcript fill out the fields.
Please summarize the transcript, {transcript}, with the following template:
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


def stuffing_summary(transcript, client):
    prompt_template = PromptTemplate.from_template(PROMPT)
    formatted_prompt = prompt_template.format(transcript=transcript)
    response = client.generate_text(prompt=formatted_prompt)
    return response


if __name__ == "__main__":
    transcript = get_transcript()
    client = select_client()
    client.init_client()
    stuffing_summary(transcript=transcript, client=client)
