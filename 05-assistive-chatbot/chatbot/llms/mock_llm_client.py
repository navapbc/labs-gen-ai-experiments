import logging

logger = logging.getLogger(__name__)

CLIENT_NAME = "mock"
MODEL_NAMES = ["llm"]


def init_client(model_name, settings):
    return MockLlmClient(model_name, settings)


class MockLlmClient:
    "Mock client that returns the mock_responses or the message itself."

    sample_qa_pairs = {
        "test Q1": {
            "errorMsg": "Some error message",
            "systemMsg": "Some system message",
            "content": "Some content",
        },
        "test Q2": {
            "errorMsg": "Some error message",
            "systemMsg": {"content": "Some system message", "metadata": {"errorObj": 123}},
            "content": "Some content",
            "metadata": {"key1": "value1", "key2": "value2"},
        },
    }

    def __init__(self, model_name, settings):
        logger.info("Creating Mock LLM client '%s' with %s", model_name, settings)

        self.mock_responses = self.sample_qa_pairs | settings

    def generate_reponse(self, message):
        return self.mock_responses.get(message, f"Mock LLM> Your query was: {message}")


if __name__ == "__main__":
    # An LLM client can be used in any arbitrary program
    def client_example_usage():
        settings = {"temperature": 1}
        client = init_client("llm", settings)
        while True:
            message = input("You> ")
            response = client.generate_reponse(message)
            print(f"Mock LLM> {response}")

    client_example_usage()
