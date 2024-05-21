from langchain_core.prompts import PromptTemplate

from llm import LLM


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


transcript = get_transcript()
prompt_template = PromptTemplate.from_template(PROMPT)
formatted_prompt = prompt_template.format(transcript=transcript)


def stuffing_summary(prompt=None):
    print("""
        Select an llm
        1. openhermes (default)
        2. dolphin
        3. gemini
        4. gpt 4
        5. gpt 4o
        6. claude 3
        7. all
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
        client = LLM(client_name="gpt", model_name="gpt4o")
    elif llm == "6":
        print("""----------
            Claude 3
            """)
        client = LLM(client_name="claude")
    elif llm == "7":
        print("""
            Openhermes
            """)
        ollama_openhermes = LLM(client_name="ollama", model_name="openhermes")
        ollama_openhermes.get_client()
        ollama_openhermes_response = ollama_openhermes.generate_text(prompt=prompt)
        print(ollama_openhermes_response)

        print("""----------
            Dolphin
            """)
        ollama_dolphin = LLM(client_name="ollama", model_name="dolphin-mistral")
        ollama_dolphin.get_client()
        dolphin_response = ollama_dolphin.generate_text(prompt=prompt)
        print(dolphin_response)

        print("""----------
            Gemini Flash 1.5
            """)
        gemini = LLM(client_name="gemini")
        gemini.get_client()
        gemini_response = gemini.generate_text(prompt=prompt)
        print(gemini_response)

        print("""----------
        GPT 4
        """)
        gpt_4 = LLM(client_name="gpt", model_name="gpt4")
        gpt_4.get_client()
        gpt_4_response = gpt_4.generate_text(prompt=prompt)
        print(gpt_4_response)

        print("""----------
        GPT 4o
        """)
        gpt_4o = LLM(client_name="_4o", model_name="gpt4o")
        gpt_4o.get_client()
        gpt_4o_response = gpt_4o.generate_text(prompt=prompt)
        print(gpt_4o_response)

        print("""----------
            Claude 3
            """)
        claude = LLM(client_name="claude")
        claude.get_client()
        claude_response = claude.generate_text(prompt=prompt)
        print(claude_response)
    else:
        client = LLM(client_name="ollama", model_name="openhermes")
        print("""
            Openhermes
            """)
    client.get_client()
    response = client.generate_text(prompt=prompt)
    if response:
        print(response)

if __name__ == "__main__":
    stuffing_summary(prompt=formatted_prompt)
