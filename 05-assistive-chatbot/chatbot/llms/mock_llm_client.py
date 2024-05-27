CLIENT_NAME = "mock"
MODEL_NAMES = ["llm"]


def init_client(model_name, settings):
    return MockLlmClient(model_name, settings)


class MockLlmClient:
    "Mock client that returns the mock_responses or the message itself."

    def __init__(self, model_name, settings):
        self.model_name = model_name
        self.mock_responses = settings

    def submit(self, message):
        return self.mock_responses.get(message, f"Mock LLM> Your query was: {message}")


if __name__ == "__main__":
    # An LLM client can be used in any arbitrary program
    def client_example_usage():
        settings = {"temperature": 1}
        client = init_client("llm", settings)
        while True:
            message = input("You> ")
            response = client.submit(message)
            print(f"Mock LLM> {response}")

    client_example_usage()
