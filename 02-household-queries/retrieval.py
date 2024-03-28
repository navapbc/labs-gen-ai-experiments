from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Chroma

import os
from pprint import pprint
import dotenv

dotenv.load_dotenv()

# Load the models
# Get a Google API key by following the steps after clicking on Get an API key button 
# at https://ai.google.dev/tutorials/setup
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
llm = ChatGoogleGenerativeAI(model="gemini-pro",
                             verbose = True,google_api_key=GOOGLE_API_KEY,
                             convert_system_message_to_human=True)
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# Create the retrieval chain
template = """
You are a helpful AI assistant.
Answer based on the context provided. 
context: {context}
"""

# Open source option
# gpt4all_path= "./mistral-7b-instruct-v0.1.Q4_0.gguf"
# llm = GPT4All(model=gpt4all_path,max_tokens=1000, verbose=True,repeat_last_n=0)
# embeddings = SentenceTransformerEmbeddings(model_name="BAAI/bge-small-en-v1.5")
prompt = PromptTemplate.from_template(template)
vectordb=Chroma(embedding_function=embeddings, collection_name="resources", persist_directory="./chroma_db")
retriever = vectordb.as_retriever(search_kwargs={"k": 1})
retrieval_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True,
    chain_type_kwargs={"prompt": prompt},

)

# Invoke the retrieval chain
response=retrieval_chain.invoke({"query":"Should all household members be listed even if they are not in the food stamp household?"})
print("RESULT: ", response["result"])
print("SOURCE DOC: ",response["source_documents"])