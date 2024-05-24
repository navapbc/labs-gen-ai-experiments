import os
import dotenv
import llms

dotenv.load_dotenv()
initial_settings = {"model": os.environ.get("LLM_MODEL_NAME", "mock :: llm")}


def validate_settings(settings):
    model_name = settings["model"]
    if model_name not in llms.available_llms():
        return f"Unknown model: '{model_name}'"

    # PLACEHOLDER: Validate other settings

    return None


def create_llm_client(settings):
    llm_name = settings["model"]
    llm_settings = dict((k, settings[k]) for k in ["temperature"] if k in settings)
    client = llms.init_client(llm_name, llm_settings)
    return client
