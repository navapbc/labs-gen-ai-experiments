import os
import dotenv
import json
from typing import List, Union, Optional

import dspy
from dsp.utils import dotdict

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

import debugging


dotenv.load_dotenv()


class BasicQA(dspy.Signature):
    """Answer questions with short factoid answers."""

    question = dspy.InputField()
    answer = dspy.OutputField(desc="often between 1 and 5 words")


def run_basic_predictor(question):
    # Define the predictor.
    generate_answer = dspy.Predict(BasicQA)

    # Call the predictor on a particular input.
    pred = generate_answer(question=question)

    # Print the input and the prediction.
    print(f"Question: {question}")
    print(f"Predicted Answer: {pred.answer}")
    return pred


def run_cot_predictor(question):
    generate_answer_with_chain_of_thought = dspy.ChainOfThought(BasicQA)

    # Call the predictor on the same input.
    pred = generate_answer_with_chain_of_thought(question=question)
    print(f"\nQUESTION : {question}")
    print(f"\nRATIONALE: {pred.rationale.split(':', 1)[1].strip()}")
    print(f"\nANSWER   : {pred.answer}")
    # debugging.debug_here(locals())


class GenerateAnswer(dspy.Signature):
    """Answer the question with a short factoid answer."""

    context = dspy.InputField(desc="may contain relevant facts")
    question = dspy.InputField()
    answer = dspy.OutputField(desc="often between 1 and 5 words")


class RAG(dspy.Module):
    def __init__(self, num_passages):
        super().__init__()

        self.retrieve = dspy.Retrieve(k=num_passages)
        self.generate_answer = dspy.ChainOfThought(GenerateAnswer)

    def forward(self, question):
        context = self.retrieve(question).passages
        prediction = self.generate_answer(context=context, question=question)
        return dspy.Prediction(context=context, answer=prediction.answer)


@debugging.timer
def run_retrieval(question, retrieve_k):
    retrieve = dspy.Retrieve(k=retrieve_k)
    retrieval = retrieve(question)
    topK_passages = retrieval.passages

    print(f"Top {retrieve.k} passages for question: {question} \n", "-" * 30, "\n")
    for i, passage in enumerate(topK_passages):
        print(f"[{i+1}]", passage, "\n")
    return retrieval


def run_rag(question, retrieve_k):
    print(f"\nQUESTION : {question}")
    rag = RAG(retrieve_k)
    pred = rag(question=question)
    print(f"\nRATIONALE: {pred.get('rationale')}")
    print(f"\nANSWER   : {pred.answer}")
    print(f"\nCONTEXT: {len(pred.context)}")
    for i, d in enumerate(pred.context):
        print(i + 1, d, "\n")
    # debugging.debug_here(locals())


class RetrievalModelWrapper(dspy.Retrieve):
    def __init__(self, vectordb):
        super().__init__()
        self.vectordb = vectordb

    def forward(self, query: str, k: Optional[int]) -> dspy.Prediction:
        k = self.k if k is None else k
        # print("k=", k)
        # k parameter is specific to Chroma retriever
        # See other parameters in .../site-packages/langchain_core/vectorstores.py
        retriever = self.vectordb.as_retriever(search_kwargs={"k": k})
        retrievals = retriever.invoke(query)
        # print("Retrieved")
        # for d in retrievals:
        #     print(d)
        #     print()

        # DSPy expects a `long_text` attribute for each retrieved item
        retrievals_as_text = [
            dotdict({"long_text": doc.page_content}) for doc in retrievals
        ]
        return retrievals_as_text


@debugging.timer
def create_retriever_model():
    # "The all-mpnet-base-v2 model provides the best quality, while all-MiniLM-L6-v2 is 5 times faster and still offers good quality."
    _embeddings_model_name = os.environ.get("EMBEDDINGS_MODEL_NAME", "all-MiniLM-L6-v2")
    embeddings = HuggingFaceEmbeddings(model_name=_embeddings_model_name)
    vectordb = Chroma(
        embedding_function=embeddings,
        collection_name="resources",
        persist_directory="./chroma_db",
    )

    # https://dspy-docs.vercel.app/docs/deep-dive/retrieval_models_clients/ChromadbRM
    # return ChromadbRM(collection_name="resources", persist_directory="./chroma_db", embedding_function=embedding_function)

    return RetrievalModelWrapper(vectordb)


@debugging.timer
def create_llm_model():
    llm_name = "openhermes"  # "openhermes", "llama2", "mistral"
    return dspy.OllamaLocal(model=llm_name, temperature=0.1)


def load_training_json():
    with open("question_answer_citations.json", encoding="utf-8") as data_file:
        json_data = json.load(data_file)
        # print(json.dumps(json_data, indent=2))
        return json_data


def main():
    retrieve_k = int(os.environ.get("RETRIEVE_K", "2"))

    qa = load_training_json()
    question = qa[2]["question"]

    # run_basic_predictor(question)
    # run_cot_predictor(question)
    # run_retrieval(question, retrieve_k)
    run_rag(question, retrieve_k)

    print("----- llm_model.inspect_history ------------------")
    llm_model.inspect_history(n=10)


if __name__ == "__main__":
    llm_model = create_llm_model()
    dspy.settings.configure(lm=llm_model, rm=create_retriever_model())

    main()
