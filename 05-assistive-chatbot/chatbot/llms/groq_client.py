from groq import Groq

CLIENT_NAME = "groq"
MODEL_NAMES = ["llama3-70b-8192", "mixtral-8x7b-32768"]


def init_client(model_name, settings):
    return GroqClient(model_name, settings)


class GroqClient:
    def __init__(self, model_name, settings):
        self.model_name = model_name
        self.client = Groq()

    def submit(self, message):
        chat_completion = self.client.chat.completions.create(
            messages=[{"role": "user", "content": message}],
            model=self.model_name,
        )

        return chat_completion.choices[0].message.content
