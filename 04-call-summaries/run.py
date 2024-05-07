from llm import google_gemini_client, ollama_client, gpt3_5, gpt_4_turbo
from langchain_core.prompts import PromptTemplate


# download transcripts from https://drive.google.com/drive/folders/19r6x3Zep4N9Rl_x4n4H6RpWkXviwbxyw?usp=sharing
def get_transcript(file_path="./transcript.txt"):
    file = open(file_path)
    content = file.read()
    file.close()
    return content


prompt = """
You are a helpful AI assistant who will summarize this transcript {transcript}, using the following template:
---------------------
Caller Information (Name, contact information, availability, household information)

Reason/Type of Call (Applying for benefits, Follow-Ups)

Previous Benefits History (Applied for, Receives, Denied, etc)

Put # in front of the benefit discussed (i.e. #SNAP, LIHEAP)

Discussion Points (Key information points)

Documents Needed (Income, Housing, etc)

Next Steps for Client

Next Steps for Agent
---------------------

"""

print("""
      Select an llm
      1. openhermes (default)
      2. dolphin
      3. gemini
      4. gpt 3.5
      5. gpt 4
      """)


transcript = get_transcript()
llm = input() or "1"
prompt_template = PromptTemplate.from_template(prompt)
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
else:
    test = ollama_client(model_name="openhermes", prompt=formatted_prompt)
    print("""
        Openhermes
        """)

print(test)
