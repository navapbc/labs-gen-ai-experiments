from langchain_core.prompts import PromptTemplate

from llm import claude, google_gemini_client, gpt3_5, gpt_4_turbo, ollama_client


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

print("""
      Select an llm
      1. openhermes (default)
      2. dolphin
      3. gemini
      4. gpt 3.5
      5. gpt 4
      6. claude 3
      7. all
      """)


transcript = get_transcript()
llm = input() or "1"
prompt_template = PromptTemplate.from_template(PROMPT)
formatted_prompt = prompt_template.format(transcript=transcript)

if llm == "2":
    test = ollama_client(model_name="dolphin-mistral", prompt=formatted_prompt)
    print("""----------
        Dolphin
        """)
elif llm == "3":
    test = google_gemini_client(prompt=formatted_prompt).text
    print("""----------
        Gemini
        """)
elif llm == "4":
    print("""----------
      GPT 3.5
      """)
    test = gpt3_5(prompt=formatted_prompt)
elif llm == "5":
    print("""----------
        GPT 4
        """)
    test = gpt_4_turbo(prompt=formatted_prompt)
elif llm == "6":
    print("""----------
        Claude 3
        """)
    test = claude(prompt=formatted_prompt)
elif llm == "7":
    test_open_hermes = ollama_client(model_name="openhermes", prompt=formatted_prompt)
    print("""
        Openhermes
        """)
    print(test_open_hermes)

    test_dolphin = ollama_client(model_name="dolphin-mistral", prompt=formatted_prompt)
    print("""----------
        Dolphin
        """)
    print(test_dolphin)

    test_gemini = google_gemini_client(prompt=formatted_prompt).text
    print("""----------
        Gemini
        """)
    print(test_gemini)

    print("""----------
      GPT 3.5
      """)
    test_gpt3_5 = gpt3_5(prompt=formatted_prompt)
    print(test_gpt3_5)

    print("""----------
        GPT 4
        """)
    test_gpt4 = gpt_4_turbo(prompt=formatted_prompt)
    print(test_gpt4)

    print("""----------
        Claude 3
        """)
    test_claude = claude(prompt=formatted_prompt)
    print(test_claude)
else:
    test = ollama_client(model_name="openhermes", prompt=formatted_prompt)
    print("""
        Openhermes
        """)
if test:
    print(test)
