import llms
import utils


@utils.timer
def create_llm_client(settings):
    llm_name = settings["model"]
    llm_settings = dict((k, settings[k]) for k in ["temperature"] if k in settings)
    client = llms.init_client(llm_name, llm_settings)
    return client
