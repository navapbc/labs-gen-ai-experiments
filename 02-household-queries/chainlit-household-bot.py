#!/usr/bin/env chainlit run

from datetime import date
import pprint
import shutil

import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider

import chromadb
from chromadb.config import Settings

from langchain.chains import ConversationalRetrievalChain
from langchain_community.embeddings import SentenceTransformerEmbeddings, HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.memory import ChatMessageHistory, ConversationBufferMemory
from langchain_google_genai import GoogleGenerativeAIEmbeddings

import os

from ingest import add_json_html_data_to_vector_db, add_pdf_to_vector_db, ingest_call
from llm import google_gemini_client, gpt4all_client, ollama_client
from retrieval import retrieval_call

OLLAMA_LLMS = ["openhermes", "llama2", "mistral"]
GOOGLE_LLMS = ["gemini-pro"]
# GPT4ALL_LLMS = ["gpt4all"]

GOOGLE_EMBEDDINGS=["Google::models/embedding-001"]
OPEN_SOURCE_EMBEDDINGS=["all-MiniLM-L6-v2"]
HUGGING_FACE_EMBEDDINGS=["HuggingFace::all-MiniLM-L6-v2", "HuggingFace::all-mpnet-base-v2"]

@cl.on_chat_start
async def init_chat():
    await cl.Message(
        content="Hi! Ask me about Michigan household policies for benefit applications.",
        actions=[
            cl.Action(name="todayAct", value="current_date", label="Today's date"),
            cl.Action(name="settingsAct", value="chat_settings", label="Show settings"),
            cl.Action(name="stepsDemoAct", value="stepsDemo", label="Demo steps"),
            cl.Action(
                name="chooseBetterAct",
                value="chooseBetter",
                label="Demo choosing better response",
            ),
            cl.Action(name="uploadDefaultFiles", value="upload_default_files", label="Upload default files"),
            cl.Action(name="uploadFilesToVectorAct", value="upload_files_to_vector", label="Upload files to vector"),
            cl.Action(name="resetDB", value="reset_db", label="Reset DB"),
        ],
    ).send()

    settings = await cl.ChatSettings(
        [
            Select(
                id="model",
                label="LLM Model",
                values=OLLAMA_LLMS + GOOGLE_LLMS,
                # values=OLLAMA_LLMS + GOOGLE_LLMS + GPT4ALL_LLMS,
                initial_index=0,
            ),
            Select(
                id="embedding",
                label="Embeddings",
                values= GOOGLE_EMBEDDINGS + OPEN_SOURCE_EMBEDDINGS + HUGGING_FACE_EMBEDDINGS,
                initial_index=0,
            ),
            Switch(id="use_vector_db", label="Use vector db sources", initial=os.environ.get("USE_VECTOR_DB", False)),
            Slider(
                id="temperature",
                label="LLM Temperature",
                initial=0.1,
                min=0,
                max=1,
                step=0.1,
            ),
            Switch(id="streaming", label="Stream response tokens", initial=True),
        ]
    ).send()
    cl.user_session.set("settings", settings)


@cl.action_callback("todayAct")
async def on_click_today(action: cl.Action):
    today = date.today()
    await cl.Message(content=f"{action.value}: Today is {today}").send()


@cl.action_callback("settingsAct")
async def on_click_settings(action: cl.Action):
    settings = cl.user_session.get("settings")
    settings_str = pprint.pformat(settings, indent=4)
    await cl.Message(content=f"{action.value}:\n`{settings_str}`").send()


contentA = """This is text A.
    This is multi-line text.
    It can be used to display longer messages.
    And it can also include markdown formatting.
    E.g. **bold**, *italic*, `code`, [links](https://www.example.com), etc.
"""

@cl.action_callback("resetDB")
async def on_click_resetDB(action: cl.Action):
    persistent_client = cl.user_session.get("persistent_client")
    if persistent_client is None:
        persistent_client = chromadb.PersistentClient(settings=Settings(allow_reset=True))
    persistent_client.reset()

@cl.action_callback("stepsDemoAct")
async def on_click_stepsDemo(action: cl.Action):
    async with cl.Step(name="Child step A", disable_feedback=False) as child_step:
        child_step.output = contentA

    async with cl.Step(name="Child step B", disable_feedback=False) as child_step:
        child_step.output = "Hello, this is a text element B."


# Alternative to https://docs.chainlit.io/data-persistence/feedback
@cl.action_callback("chooseBetterAct")
async def on_click_chooseBetter(action: cl.Action):
    await cl.Message(
        content=contentA,
        disable_feedback=True,
        actions=[
            cl.Action(name="choose_response", value="optionA", label="This is better")
        ],
    ).send()
    await cl.Message(
        content="Hello, this is a text B.",
        disable_feedback=True,
        actions=[
            cl.Action(name="choose_response", value="optionB", label="This is better")
        ],
    ).send()


@cl.action_callback("choose_response")
async def on_choose_response(action: cl.Action):
    await cl.Message(
        content=f"User chose: {action.value}", disable_feedback=True
    ).send()


@cl.on_settings_update
async def update_settings(settings):
    print("Settings updated:", pprint.pformat(settings, indent=4))
    cl.user_session.set("settings", settings)
    await set_llm_model()
    await set_embeddings()
    if settings["use_vector_db"]:
        await set_vector_db()


async def set_llm_model():
    settings = cl.user_session.get("settings")
    llm_name = settings["model"]
    llm_settings = dict((k, settings[k]) for k in ["temperature"] if k in settings)
    msg = cl.Message(
        author="backend",
        content=f"Setting up LLM: {llm_name} with `{llm_settings}`...\n",
    )
    client = None
    if llm_name in OLLAMA_LLMS:
        client = ollama_client(llm_name, settings=llm_settings)
    elif llm_name in GOOGLE_LLMS:
        client = google_gemini_client(llm_name, settings=llm_settings)
    # elif llm_name in GPT4ALL_LLMS:
    #     client = gpt4all_client()
    else:
        await cl.Message(content=f"Could not initialize model: {llm_name}").send()
        return

    cl.user_session.set("client", client)
    await msg.stream_token(f"Done setting up {llm_name} LLM")
    await msg.send()

async def set_embeddings():
    settings = cl.user_session.get("settings")
    embeddings = settings["embedding"]
    msg = cl.Message(
        author="backend",
        content=f"Setting up embedding: `{embeddings}`...\n",
    )
    embedding = None
    if embeddings in GOOGLE_EMBEDDINGS:
        GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
        model_name= embeddings.split('::')[1]
        embedding =  GoogleGenerativeAIEmbeddings(model=model_name, google_api_key=GOOGLE_API_KEY)
    elif embeddings in OPEN_SOURCE_EMBEDDINGS:
        embedding = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    elif embeddings in HUGGING_FACE_EMBEDDINGS:
        model_name= embeddings.split('::')[1]
        embeddings = HuggingFaceEmbeddings(model_name=model_name)
    else:
        await cl.Message(content=f"Could not initialize embedding: {embeddings}").send()
        return
    cl.user_session.set("embedding", embedding)
    await msg.stream_token(f"Done setting up {embeddings} embedding")
    await msg.send()

async def set_vector_db():
    await init_embedding_function_if_needed()
    embeddings = cl.user_session.get("embedding")
    msg = cl.Message(
        author="backend",
        content=f"Setting up Chroma DB with `{embeddings}`...\n",
    )
    
    # clean up db when setting embedding for embedding dimension does not match collection dimensionality
    persistent_client = chromadb.PersistentClient(settings=Settings(allow_reset=True))
    cl.user_session.set("chromadb_client", persistent_client)
    vectordb=Chroma(
        client=persistent_client,
        collection_name="resources", 
        persist_directory="./chroma_db",
        embedding_function=embeddings
    )

    cl.user_session.set("vectordb", vectordb)
    await msg.stream_token(f"Done setting up vector db")
    await msg.send()

async def init_llm_client_if_needed():
    client = cl.user_session.get("client")
    if not client:
        await set_llm_model()
async def init_embedding_function_if_needed():
    embedding = cl.user_session.get("embedding")
    if not embedding:
        await set_embeddings()
async def init_vector_db_if_needed():
    vectordb=cl.user_session.get("vectordb")
    if vectordb is None:
        await set_vector_db()


@cl.on_message
async def message_submitted(message: cl.Message):
    await init_llm_client_if_needed()
    await init_embedding_function_if_needed()
    settings = cl.user_session.get("settings")
    client=cl.user_session.get("client")
    vectordb=cl.user_session.get("vectordb")
    # 3 ways to manage history for LLM:
    # 1. Use Chainlit
    # message_history = cl.user_session.get("message_history")
    # message_history.append({"role": "user", "content": message.content})
    # 2. Use LangChain's ConversationBufferMemory
    # 3. Use LlmPrompts lp.register_answer

    # Reminder to use make_async for long running tasks: https://docs.chainlit.io/guides/sync-async#long-running-synchronous-tasks
    # If options `streaming` and `use_vector_db` are set the RAG chain will not be called 
    if settings["streaming"]:
        await call_llm_async(message)
    else:
        if settings["use_vector_db"] and vectordb:
            await retrieval_function(vectordb=vectordb, llm=client)
            response = retrieval_call(client, vectordb, message.content)
            answer = f"Result: {response['result']} \nSources: {response['source_documents'][0].metadata}"
            await cl.Message(content=answer).send()
        else:
            response = call_llm(message)
            await cl.Message(content=f"*Response*: {response}").send()

@cl.step(type="llm", show_input=True)
async def call_llm_async(message: cl.Message):
    client = cl.user_session.get("client")

    botMsg = cl.Message(content="", disable_feedback=False)
    async for chunk in client.astream(message.content):
        await botMsg.stream_token(chunk)
    await botMsg.send()

    response = botMsg.content
    return response


def call_llm(message: cl.Message):
    client = cl.user_session.get("client")
    response = client.invoke(message.content)
    return response


@cl.action_callback("uploadDefaultFiles")
async def on_click_upload_default_files(action: cl.Action):
    await set_vector_db()
    vectordb= cl.user_session.get("vectordb")
    msg = cl.Message(content=f"Processing files...", disable_feedback=True)
    await msg.send()

    ingest_call(vectordb)
    msg.content = f"Processing default files done. You can now ask questions!"
    await msg.update()

@cl.action_callback("uploadFilesToVectorAct")
async def on_click_upload_file_query(action: cl.Action):
    files = None
    # Wait for the user to upload a file
    while files == None:
        files = await cl.AskFileMessage(
            content="Please upload a pdf or json file to begin!",
            accept=["text/plain", "application/pdf", "application/json"],
            max_size_mb=20,
            timeout=180,
        ).send()
    file = files[0]
    
    # initialize db
    await set_vector_db()
    vectordb=cl.user_session.get("vectordb")
    if(file.type == "application/pdf"):
        add_pdf_to_vector_db(vectordb=vectordb, file_path=file.path)
    elif(file.type == "application/json"):
        add_json_html_data_to_vector_db(vectordb=vectordb, file_path=file.path, content_key="content", index_key="preferredPhrase")
    msg = cl.Message(content=f"Processing `{file.name}`...", disable_feedback=True)
    await msg.send()
    msg.content = f"Processing `{file.name}` done. You can now ask questions!"
    await msg.update()

async def retrieval_function(vectordb, llm):    
    retriever = vectordb.as_retriever(search_kwargs={"k": 1})
    message_history = ChatMessageHistory()

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        output_key="answer",
        chat_memory=message_history,
        return_messages=True,
    )

    # Create a chain that uses the Chroma vector store
    chain = ConversationalRetrievalChain.from_llm(
        llm,
        chain_type="stuff",
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
    )
    
    # Let the user know that the system is ready
    cl.user_session.set("chain", chain)
