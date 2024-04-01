import dotenv
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.llms import GPT4All
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
import os

from ingest import ingest_call
from retrieval import retrieval_call

dotenv.load_dotenv()

print("""
Which embedding function would you like to use?
1. Google Gen AI (default)
2. all-MiniLM-L6-v2
      """)
embedding_choice = input()
# Set embedding function
if embedding_choice == 2 or embedding_choice == "all-MiniLM-L6-v2":
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
else:
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

print("""
Which LLM would you like to use? 
1. Gemini (default)
2. Mistral
      """)

llm_choice = input()
# Load the models
if llm_choice == 2 or llm_choice == "Mistral":
    # Open source option
    # download Mistral at https://mistral.ai/news/announcing-mistral-7b/
    gpt4all_path= "./mistral-7b-instruct-v0.1.Q4_0.gguf"
    llm = GPT4All(model=gpt4all_path,max_tokens=1000, verbose=True,repeat_last_n=0)
else:
    # Get a Google API key by following the steps after clicking on Get an API key button 
    # at https://ai.google.dev/tutorials/setup
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    llm = ChatGoogleGenerativeAI(model="gemini-pro",
                                verbose = True,google_api_key=GOOGLE_API_KEY,
                                convert_system_message_to_human=True)
        
# initialize chroma db
vectordb=Chroma(embedding_function=embeddings, collection_name="resources", persist_directory="./chroma_db")

ingest_call(vectordb=vectordb)
retrieval_call(llm=llm, vectordb=vectordb)