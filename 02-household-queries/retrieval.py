from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

def retrieval_call(llm, vectordb):
    # Create the retrieval chain
    template = """
    You are a helpful AI assistant.
    Answer based on the context provided. 
    context: {context}
    """

    prompt = PromptTemplate.from_template(template)
    retriever = vectordb.as_retriever(search_kwargs={"k": 1})
    retrieval_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt},

    )

    print("Please state your question here: ")
    question = input()
    # Invoke the retrieval chain
    response=retrieval_chain.invoke({"query":question})
    print("RESULT: ", response["result"])
    print("SOURCE DOC: ",response["source_documents"])
