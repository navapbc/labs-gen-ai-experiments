#!/usr/bin/env python
import os
import time
import json
from typing import Optional

import dotenv
import dsp
from dsp.utils import dotdict
import dspy
from dspy.evaluate import Evaluate
from dspy.teleprompt import COPRO, LabeledFewShot, BootstrapFewShot

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

import debugging


class BasicQA(dspy.Signature):
    """Answer questions with short answers."""

    question = dspy.InputField()
    answer = dspy.OutputField(desc="Respond with only one of these words: Yes, No, Maybe")


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
    # Manual ChatGPT general RAG prompt:
    #     """Given the input query and context of the most relevant information, generate a response that clearly addresses the query based on the context. \
    # Your response should be concise, relevant, and directly answer the question or address the topic at hand."""
    # Manual ChatGPT suggestion given my initial prompt:
    #     """When provided with a question, analyze its content and the context carefully to determine the most accurate and concise response. \
    # Your answer should begin with one of the following words: "Yes", "No", or "Maybe." \
    # Ensure that the response directly addresses the question posed, is clear, and provides a definitive stance where possible. \
    # If the question involves uncertainty or lacks sufficient information, use "Maybe" to reflect this ambiguity. \
    # Aim for precision and brevity in your answer to succinctly convey your assessment of the situation or fact."""
    # Automatic COPRO using openhermes:
    #     """Please provide an improved instruction to the task as follows: Given a question in English, generate a concise and precise answer using appropriate grammar and punctuation."""
    # Automatic COPRO using OpenAI gpt-3.5-turbo:
    """Given a question, promptly discern its context and components. \
Provide a direct response with either \"Yes\", \"No\", or \"Maybe\" based on the content and certainty of the query. \
Focus on clarity and decisiveness, being concise in conveying your evaluation while catering to the specifics of the question.
"""

    context = dspy.InputField(desc="may contain relevant facts used to answer the question")
    question = dspy.InputField()
    answer = dspy.OutputField(
        desc="Start with one of these words: Yes, No, Maybe",
        prefix="Response:",
        # prefix="Your concise and accurate response to the question is:",
        # json_schema_extra=...
    )


class RAG(dspy.Module):
    def __init__(self, num_passages):
        super().__init__()
        self.retrieve = dspy.Retrieve(k=num_passages)
        self.generate_answer = dspy.ChainOfThought(
            GenerateAnswer,
            # rationale_type=dspy.OutputField(
            #     prefix="Reasoning: Let's think step by step in order to",
            #     desc="${produce the " + "answer" + "}. We ...",
            # ),
        )

    def forward(self, question):
        retrievals = self.retrieve(question)
        # print(retrievals)
        context = retrievals.passages
        prediction = self.generate_answer(context=context, question=question)
        return dspy.Prediction(context=context, answer=prediction.answer)


@debugging.timer
def run_retrieval(query, retrieve_k):
    retrieve = dspy.Retrieve(k=retrieve_k)
    retrieval = retrieve(query)
    topK_passages = retrieval.passages

    print(f"Top {retrieve.k} passages for query: {query} \n", "-" * 30, "\n")
    for i, passage in enumerate(topK_passages):
        print(f"[{i + 1}]", passage, "\n")
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
        # k parameter is specific to Chroma retriever
        # See other parameters in .../site-packages/langchain_core/vectorstores.py
        retriever = self.vectordb.as_retriever(search_kwargs={"k": k})
        retrievals = retriever.invoke(query)
        dedup_retrievals = []
        retrieval_sources = set()
        for d in retrievals:
            if d.metadata["source"] not in retrieval_sources:
                retrieval_sources.add(d.metadata["source"])
                dedup_retrievals.append(d)
        # print("Retrieved (dedup)")
        # for d in dedup_retrievals:
        #     print(type(d))
        #     print(d.metadata)
        #     print()

        # DSPy expects a `long_text` attribute for each retrieved item
        retrievals_as_text = [
            dotdict(
                {
                    "long_text": doc.metadata["entire_card"],
                    "page_content": doc.page_content,
                    "source": doc.metadata["source"],
                }
            )
            for doc in dedup_retrievals
        ]
        return retrievals_as_text


@debugging.timer
def create_retriever_model():
    # "The all-mpnet-base-v2 model provides the best quality, while all-MiniLM-L6-v2 is 5 times faster and still offers good quality."
    _embeddings_model_name = os.environ.get("EMBEDDINGS_MODEL_NAME", "all-MiniLM-L6-v2")
    embeddings = HuggingFaceEmbeddings(model_name=_embeddings_model_name)
    vectordb = Chroma(
        embedding_function=embeddings,
        # Must use collection_name="langchain" -- https://github.com/langchain-ai/langchain/issues/10864#issuecomment-1730303411
        collection_name="langchain",
        persist_directory="./chroma_db",
    )
    print(embeddings)

    # https://dspy-docs.vercel.app/docs/deep-dive/retrieval_models_clients/ChromadbRM
    # return ChromadbRM(collection_name="resources", persist_directory="./chroma_db", embedding_function=embedding_function)

    return RetrievalModelWrapper(vectordb)


@debugging.timer
def create_llm_model(llm_name="openhermes", respond_with_json=False):
    # print("LLM model name:", llm_name)
    dspy_llm_kwargs = {
        "temperature": 0.1,
        # The default DSPy max_tokens is only 150, which caused issues due to incomplete JSON string output
        "max_tokens": 1000,
    }
    if llm_name in ["openhermes", "llama2", "llama2:chat", "llama3", "mistral", "mistral:instruct"]:
        # Alternative using OpenAI-compatible API: https://gist.github.com/jrknox1977/78c17e492b5a75ee5bbaf9673aee4641
        return dspy.OllamaLocal(model=llm_name, **dspy_llm_kwargs)
    elif llm_name in [
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-instruct",
        "gpt-4",
        "gpt-4-turbo",
    ]:
        if respond_with_json:
            return dspy.OpenAI(model=llm_name, **dspy_llm_kwargs, response_format={"type": "json_object"})
        else:
            return dspy.OpenAI(model=llm_name, **dspy_llm_kwargs)
    elif llm_name in ["gemini-1.0-pro"]:
        return dspy.Google(model=f"models/{llm_name}", **dspy_llm_kwargs)
    elif llm_name in ["llama3-70b-8192", "mixtral-8x7b-32768"]:
        api_key = os.environ.get("GROQ_API_KEY")
        return dspy.GROQ(api_key, model=llm_name, **dspy_llm_kwargs)
    else:
        assert False, f"Unknown LLM model: {llm_name}"


def main_baseline(query):
    retrieve_k = int(os.environ.get("RETRIEVE_K", "2"))

    dspy.settings.configure(lm=create_llm_model(), rm=create_retriever_model())

    # run_basic_predictor(query)
    # run_cot_predictor(query)
    # run_retrieval(query, retrieve_k)
    run_rag(query, retrieve_k)


def main_train(qa_pairs):
    training = [qa.with_inputs("question") for qa in qa_pairs]
    print_training_data(training)

    retrieve_k = int(os.environ.get("RETRIEVE_K", "10"))
    print("Using retrieve_k =", retrieve_k)
    module: dspy.Module = RAG(retrieve_k)

    filename = input("Specify compiled_module file to load optimized module or press Enter to start from scratch: ")
    if filename:
        module.load(filename)
        compiled_module = module

    # Options: validate_answer, validate_context_and_answer
    eval_metric = validate_context_and_answer

    if not filename:
        optimizer_choice = input(f"""Which optimizer?
        1. COPRO(metric={eval_metric.__name__})
        2. LabeledFewShot(3)
        3. BootstrapFewShot(metric={eval_metric.__name__})
    """)
        eval_kwargs = None
        if optimizer_choice == "1":
            # Can specify prompt_model to use different LLM for prompt candidate generation
            # By default, it uses the same LLM as dspy.settings.lm
            optimizer = COPRO(metric=eval_metric, verbose=True)
            eval_kwargs = dict(num_threads=64, display_progress=True, display_table=0)
        elif optimizer_choice == "2":
            optimizer = LabeledFewShot(3)
        elif optimizer_choice == "3":
            optimizer = BootstrapFewShot(metric=eval_metric)

    llm_choice = input("""Which LLM?
        openhermes (default), llama2, mistral,
        gpt-3.5-turbo, gpt-3.5-turbo-instruct, gpt-4, gpt-4-turbo, gpt-4-turbo-instruct
    """)
    if not llm_choice:
        llm_choice = "openhermes"
    dspy.settings.configure(lm=create_llm_model(llm_choice), rm=create_retriever_model())

    if not filename:
        file_suffix = f"optimizer{optimizer_choice}_{retrieve_k}_{llm_choice}_{time.strftime('%Y-%m-%d-%H%M%S')}"
        compiled_module = optimize_module(optimizer, module, training, eval_kwargs, file_suffix)
    print_optimization(compiled_module)

    evaluate_module(compiled_module, eval_metric, training)


# Custom validator for training
# Built-in alternatives:
# - dspy.evaluate.metrics.answer_exact_match
# - dspy.evaluate.metrics.answer_passage_match
def validate_answer(example, pred, trace=None):
    return pred.answer.lower().startswith(example.answer.lower())


def validate_context_and_answer(example, pred, trace=None):
    # check the gold label and the predicted answer are the same
    answer_match = validate_answer(example, pred, trace)

    # Check if context contains guru card questions
    context_match = dsp.passage_match(pred.context, example.guru_cards)

    # print("match scores:", answer_match, context_match)
    if trace is None:  # if we're doing evaluation or optimization
        return (answer_match + context_match) / 2.0
    else:  # if we're doing bootstrapping, i.e. self-generating good demonstrations of each step
        return answer_match and context_match


def print_training_data(training):
    print("----- training data ------------------")
    for i, t in enumerate(training):
        print(i, t.inputs())
    print("--------------------------------------")


def print_optimization(compiled_module):
    print("----- optimization ------------------")
    for name, parameter in compiled_module.named_predictors():
        print(name)
        print(parameter)
        print(len(parameter.demos), "demos")
        {print(d) for d in parameter.demos}
        print()
    print("--------------------------------------")


def print_eval_table(eval_score, results):
    print("----- evalation results ------------------")
    correct_count = 0
    for ex, pred, score in results:
        if score == 1:
            correct_count += 1
        print(score, "|", ex.q_id, "|", ex.answer, "|", pred.get("answer", "")[:20])
    print()
    print("score:", eval_score)
    print(f"{correct_count} ({int(correct_count / len(results) * 100)}%) correct")
    print("--------------------------------------")


@debugging.timer
def manual_evaluation(program, dataset):
    scores = []
    for i, ex in enumerate(dataset):
        print(i, ex)
        pred = program(**ex.inputs())
        print(pred)
        score = validate_answer(ex, pred)
        scores.append(score)
    print(scores)


def print_last_llm_history(n=1):
    print("----- DSPy history  ------------------")
    dspy.settings.lm.inspect_history(n=n)
    print("--------------------------------------")


@debugging.timer
def sanity_check(training, module, eval_metric):
    print("----- Sanity check ------------------")
    index = 3
    print(training[index])
    pred = module(training[index].question)
    print(pred)
    print(eval_metric(training[index], pred))
    print_last_llm_history()
    print("--------------------------------------")


@debugging.timer
def optimize_module(optimizer, module, training, eval_kwargs, file_suffix):
    print("----- optimizing ------------------")
    if eval_kwargs:
        # COPRO requires eval_kwargs whereas other optimizers don't
        compiled_module = optimizer.compile(module, trainset=training, eval_kwargs=eval_kwargs)
    else:
        compiled_module = optimizer.compile(module, trainset=training)
    compiled_module.save(f"compiled_module-{file_suffix}.json")
    print("--------------------------------------")
    return compiled_module


@debugging.timer
def evaluate_module(compiled_module, eval_metric, devset):
    print(f"----- evaluating against {len(devset)} items ------------------")
    # manual_evaluation(compiled_module, devset)
    evaluator = Evaluate(
        devset=devset,
        num_threads=1,
        display_progress=True,
        display_table=0,
        return_outputs=True,
    )
    score, results = evaluator(compiled_module, metric=eval_metric)
    print("--------------------------------------")
    # print_last_llm_history()
    print_eval_table(score, results)


def load_training_json():
    with open("question_answer_citations.json", encoding="utf-8") as data_file:
        json_data = json.load(data_file)
        # print(json.dumps(json_data, indent=2))
        return json_data


def examples_from(qa):
    examples = []
    answers = set()
    for qa_dict in qa:
        orig_question = qa_dict["orig_question"]
        question = qa_dict.get("easy_question", qa_dict.get("question", orig_question))
        # print(f"\nQUESTION {qa_dict['id']}: {question}")

        answer = qa_dict.get("short_answer", qa_dict["answer"])
        # print(f"  Desired ANSWER : {answer}")

        qa_pair = dspy.Example(
            q_id=qa_dict["id"],
            question=question,
            answer=answer,
            orig_answer=qa_dict["orig_answer"],
            guru_cards=qa_dict["guru_cards"],
        )
        examples.append(qa_pair)
        answers.add(qa_pair.answer)
    print()
    print("Possible answers: ", answers)
    print()
    return examples


if __name__ == "__main__":
    dotenv.load_dotenv()
    examples_qa = examples_from(load_training_json())

    # main_baseline(examples_qa[0].question)
    main_train(examples_qa)
