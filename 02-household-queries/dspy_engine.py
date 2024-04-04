import os
import json
from typing import Optional

import dotenv
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


def run_basic_predictor(query):
    # Define the predictor.
    generate_answer = dspy.Predict(BasicQA)

    # Call the predictor on a particular input.
    pred = generate_answer(question=query)

    # Print the input and the prediction.
    print(f"Query: {query}")
    print(f"Answer: {pred.answer}")
    return pred


def run_cot_predictor(query):
    generate_answer_with_chain_of_thought = dspy.ChainOfThought(BasicQA)

    # Call the predictor on the same input.
    pred = generate_answer_with_chain_of_thought(question=query)
    print(f"\nQUERY    : {query}")
    print(f"\nRATIONALE: {pred.rationale.split(':', 1)[1].strip()}")
    print(f"\nANSWER   : {pred.answer}")
    # debugging.debug_here(locals())


class GenerateAnswer(dspy.Signature):
    """Answer the question with a short factoid answer."""

    context = dspy.InputField(
        desc="may contain relevant facts used to answer the question"
    )
    question = dspy.InputField()
    answer = dspy.OutputField(
        desc="Start with one of these words: Yes, No, Maybe. Between 1 and 5 words"
    )


class RAG(dspy.Module):
    def __init__(self, num_passages):
        super().__init__()

        self.retrieve = dspy.Retrieve(k=num_passages)
        self.generate_answer = dspy.ChainOfThought(GenerateAnswer)

    def forward(self, query):
        context = self.retrieve(query).passages
        prediction = self.generate_answer(context=context, question=query)
        return dspy.Prediction(context=context, answer=prediction.answer)


@debugging.timer
def run_retrieval(query, retrieve_k):
    retrieve = dspy.Retrieve(k=retrieve_k)
    retrieval = retrieve(query)
    topK_passages = retrieval.passages

    print(f"Top {retrieve.k} passages for query: {query} \n", "-" * 30, "\n")
    for i, passage in enumerate(topK_passages):
        print(f"[{i+1}]", passage, "\n")
    return retrieval


def run_rag(query, retrieve_k):
    rag = RAG(retrieve_k)
    pred = rag(query=query)
    print(f"\nRATIONALE: {pred.get('rationale')}")
    print(f"\nANSWER   : {pred.answer}")
    print(f"\nCONTEXT: {len(pred.context)}")
    for i, d in enumerate(pred.context):
        print(i + 1, d, "\n")
    # debugging.debug_here(locals())


# https://dspy-docs.vercel.app/docs/deep-dive/retrieval_models_clients/custom-rm-client
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


def main(query):
    retrieve_k = int(os.environ.get("RETRIEVE_K", "2"))

    # run_basic_predictor(query)
    # run_cot_predictor(query)
    # run_retrieval(query, retrieve_k)
    run_rag(query, retrieve_k)


if __name__ == "__main__":
    qa = load_training_json()
    for qa_dict in qa:
        orig_question = qa_dict["orig_question"]
        question = qa_dict.get("question", orig_question)
        print(f"\nQUESTION {qa_dict['id']}: {question}")
        answer = qa_dict["answer"]
        short_answer = qa_dict.get("short_answer", answer)
        print(f"  SHORT   ANSWER : {short_answer}")
        print(f"  Desired ANSWER : {answer}")
    print()

    llm_model = create_llm_model()
    dspy.settings.configure(lm=llm_model, rm=create_retriever_model())

    main(question)

    print("----- llm_model.inspect_history ------------------")
    llm_model.inspect_history(n=10)
