# DSPy version of v2_household_engine.py

import json
import logging
import os
from functools import cached_property

import dspy  # type: ignore[import-untyped]
from dspy.signatures.signature import signature_to_template  # type: ignore[import-untyped]

from chatbot import engines
from chatbot.engines.v2_household_engine import SummariesChatEngine

logger = logging.getLogger(__name__)

ENGINE_NAME = "Summaries-DSPy"


def init_engine(settings):
    return SummariesDspyChatEngine(settings)


## LLM Client classes for (Question) Decomposer and (Guru Card) Summarizer used by the chat engine.
##   DSPy LLM clients require different handling than non-DSPy clients.
##   Also non-DSPy clients are using the prompt generated (but not yet optimized) by DSPy.


class DecomposerDspyClient:
    def __init__(self, prompts, settings):
        self.prompts = prompts

        if os.environ.get("DSP_CACHEBOOL").lower() != "false":
            logger.warning("DSP_CACHEBOOL should be set to True to get different responses for retry attempts")

        if "predictor" not in settings:
            settings["predictor"] = self.decomposer_predictor
        self.decomposer_client = engines.create_llm_client(settings)

    def decomposer_predictor(self, message):
        prediction = self.prompts.decomposer(question=message)
        derived_questions = json.loads(prediction.answer)
        if "Answer" in derived_questions:
            # For OpenAI 'gpt-4-turbo' in json mode
            derived_questions = derived_questions["Answer"]
        return derived_questions

    def generate_derived_questions(self, query):
        # generate_reponse() indirectly calls decomposer_predictor()
        return self.decomposer_client.generate_reponse(query)


class DecomposerLlmClient:
    def __init__(self, prompts, settings):
        self.prompts = prompts
        self.decomposer_client = engines.create_llm_client(settings)

    def generate_derived_questions(self, query):
        response = call_llm_with_dspy_prompt(self.decomposer_client, self.prompts.decomposer, question=query)
        return json.loads(response)


class SummarizerDspyClient:
    def __init__(self, prompts, settings):
        self.prompts = prompts

        settings["predictor"] = None
        self.summarizer_client = engines.create_llm_client(settings)

    def summarizer(self, **kwargs):
        with dspy.context(lm=self.summarizer_client.llm):
            return self.prompts.summarizer(**kwargs).answer


class SummarizerLlmClient:
    def __init__(self, prompts, settings):
        self.prompts = prompts

        self.summarizer_client = engines.create_llm_client(settings)

    def summarizer(self, **kwargs):
        return call_llm_with_dspy_prompt(self.summarizer_client, self.prompts.summarizer, **kwargs)


def call_llm_with_dspy_prompt(llm_client, dspy_predict_obj: dspy.Predict, **template_inputs):
    template = signature_to_template(dspy_predict_obj.signature)
    # demos are for in-context learning
    dspy_prompt = template({"demos": []} | template_inputs)
    logger.debug("Prompt: %s", dspy_prompt)
    response = llm_client.generate_reponse(dspy_prompt)
    logger.debug("Response object: %s", response)
    return response


class DSPyPrompts:
    @cached_property
    def decomposer(self):
        class DecomposeQuestion(dspy.Signature):
            """Rephrase and decompose into multiple questions so that we can search for relevant public benefits eligibility requirements. \
    Be concise -- only respond with JSON. Only output the questions as a JSON list: ["question1", "question2", ...]. \
    The question is: {question}"""

            # TODO: Incorporate https://gist.github.com/hugodutka/6ef19e197feec9e4ce42c3b6994a919d

            question = dspy.InputField()
            answer = dspy.OutputField(desc='["question1", "question2", ...]')

        return dspy.Predict(DecomposeQuestion)

    @cached_property
    def summarizer(self):
        class SummarizeCardGivenQuestion(dspy.Signature):
            """Summarize the following context into 1 sentence without explicitly answering the question(s): {context_question}

            Context: {context}
            """

            context_question = dspy.InputField()
            context = dspy.InputField()
            answer = dspy.OutputField()

        return dspy.Predict(SummarizeCardGivenQuestion)


## Summaries (using DSPy) Chat Engine


class SummariesDspyChatEngine(SummariesChatEngine):
    def _init_llms(self, settings):
        prompts = DSPyPrompts()

        if settings["model"].startswith("dspy ::"):
            decomposer_client = DecomposerDspyClient(prompts, settings.copy())
        else:
            decomposer_client = DecomposerLlmClient(prompts, settings.copy())
        self.decomposer = decomposer_client.generate_derived_questions

        if "model2" in settings:
            settings["model"] = settings.pop("model2")
        if "temperature2" in settings:
            settings["temperature"] = settings.pop("temperature2")
        if settings["model"].startswith("dspy ::"):
            summarizer_client = SummarizerDspyClient(prompts, settings.copy())
        else:
            summarizer_client = SummarizerLlmClient(prompts, settings.copy())
        self.summarizer = summarizer_client.summarizer
