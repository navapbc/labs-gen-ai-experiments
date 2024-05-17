from langchain_core.prompts import PromptTemplate

from llm import claude_client, google_gemini_client, gpt_client, ollama_client
from chunking import chunking_ingest


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

CHUNKING_PROMPT = """
You are a helpful AI assistant tasked with summarizing transcripts, however we can only process the transcripts in pieces.
Fill out the fields with the text given {text}. If the following template already has the field filled out, do not overwrite this information.
Please fill out the data with the following template: {template}
"""

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

transcript = get_transcript()
llm = input() or "1"
prompt_template = PromptTemplate.from_template(PROMPT)
formatted_prompt = prompt_template.format(transcript=transcript)

if llm == "2":
    ollama = ollama_client(model_name="dolphin-mistral")
    response = ollama_client(client=ollama, prompt=formatted_prompt)
    print("""----------
        Dolphin
        """)
elif llm == "3":
    gemini = google_gemini_client()
    response = google_gemini_client(client=gemini, prompt=formatted_prompt)
    print("""----------
        Gemini Flash 1.5
        """)
elif llm == "4":
    print("""----------
      GPT 4
      """)
    gpt = gpt_client()
    response = gpt_client(client=gpt, model_choice="gpt4", prompt=formatted_prompt)
elif llm == "5":
    print("""----------
      GPT 4o
      """)
    gpt = gpt_client()
    response = gpt_client(client=gpt, model_choice="gpt4o", prompt=formatted_prompt)
elif llm == "6":
    print("""----------
        Claude 3
        """)
    claude = claude_client()
    response = claude_client(client=claude, prompt=formatted_prompt)
elif llm == "7":
    # print("""
    #     Openhermes
    #     """)
    # ollama_openhermes = ollama_client(model_name="openhermes")
    # ollama_openhermes_response = ollama_client(
    #     client=ollama_openhermes, prompt=formatted_prompt
    # )
    # print(ollama_openhermes_response)

    # print("""----------
    #     Dolphin
    #     """)
    # ollama_dolphin = ollama_client(model_name="dolphin-mistral")
    # dolphin_response = ollama_client(client=ollama_dolphin, prompt=formatted_prompt)
    # print(dolphin_response)

    # print("""----------
    #     Gemini Flash 1.5
    #     """)
    # gemini = google_gemini_client()
    # gemini_response = google_gemini_client(client=gemini, prompt=formatted_prompt)
    # print(gemini_response)

    # gpt = gpt_client()
    # print("""----------
    #   GPT 4
    #   """)
    # gpt_4_response = gpt_client(
    #     client=gpt, model_choice="gpt4", prompt=formatted_prompt
    # )
    # print(gpt_4_response)

    # print("""----------
    #   GPT 4o
    #   """)
    # gpt_4o_response = gpt_client(
    #     client=gpt, model_choice="gpt-4o", prompt=formatted_prompt
    # )
    # print(gpt_4o_response)

    print("""----------
        Claude 3
        """)
    claude = claude_client()
    claude_response = claude_client(client=claude, prompt=formatted_prompt)
    print(claude_response)
else:
    ollama = ollama_client(model_name="openhermes")
    response = ollama_client(client=ollama, prompt=formatted_prompt)
    print("""
        Openhermes
        """)
if response:
    print(response)
