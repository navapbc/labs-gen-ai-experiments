import llms


def validate_settings(settings):
    model_name = settings["model"]
    if model_name not in llms.llm_modules:
        return f"Unknown model: '{model_name}'"

    # PLACEHOLDER: Validate other settings

    return None
