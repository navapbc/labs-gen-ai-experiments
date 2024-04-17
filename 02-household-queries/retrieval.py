import os
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA


def create_retriever(vectordb):
    retrieve_k = int(os.environ.get("RETRIEVE_K", "10"))
    return vectordb.as_retriever(search_kwargs={"k": retrieve_k})


def retrieval_call(llm, vectordb, question):
    # Create the retrieval chain
    template = """
    You are a helpful AI assistant.
    Answer based on the context provided. 
    context: {context}
    """
    llm_prompt = os.environ.get("LLM_PROMPT", template)
    print("\n## PROMPT TEMPLATE: ", llm_prompt)

    prompt = PromptTemplate.from_template(llm_prompt)
    retriever = create_retriever(vectordb)
    retrieval_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt},
    )

    # question = os.environ.get("USER_QUERY")
    if question is None:
        print("Please state your question here: ")
        question = input()
    # Invoke the retrieval chain
    response = retrieval_chain.invoke({"query": question})
    print("\n## QUERY: ", question)
    print("\n## RESULT: ", response["result"])
    print("\n## SOURCE DOC: ")
    for d in response["source_documents"]:
        print(d)
        print()
    return response
