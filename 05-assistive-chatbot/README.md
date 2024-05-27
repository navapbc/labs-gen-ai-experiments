
## Setup

### Python
* Use Python 3.11.x (higher versions cause library version problems).
* Install Python libraries: `pip install -r requirements.txt`

### (Optional) Enable Chatbot feedback
To enable the [feedback mechanism](https://docs.chainlit.io/data-persistence/feedback):
* Get an API key: https://docs.chainlit.io/data-persistence/overview
* Create or update `.env` with `LITERAL_API_KEY` set to the API key

After running the chatbot and providing feedback in the UI, review the feedback at https://cloud.getliteral.ai/projects/YOUR_PROJECT_NAME/feedback.

* To use a custom feedback storage instead of `getliteral.ai`, see https://docs.chainlit.io/data-persistence/custom.


## Run

All apps use configurations set in `.env`, which can be overridden by environment variables, like `CHAT_ENGINE` and `LLM_MODEL_NAME`.  See `_init_settings()` in `chatbot/__init__.py` for other variables.

### Run web chatbot app

1. Start the Chainlit-based chatbot service: `./chatbot-chainlit.py` or `chainlit run ./chatbot-chainlit.py`
1. Open a browser to `http://localhost:8000/`

For development, run something like `chainlit run -w -h --port 9000 ./chatbot-chainlit.py`.

Running the chatbot app will also run the API, which is defined in `chatbot_api.py`.

### Run only the API

1. Run `./chatbot_api.py`
1. Open a browser to the `/query` endpoint followed by a question, such as `http://localhost:8001/query/tell me a joke`

### Run commandline app

1. Run `./cmdline.py`

To quickly set variables and run the app on a single line: 
`CHATBOT_LOG_LEVEL=INFO CHAT_ENGINE=Direct LLM_MODEL_NAME='langchain.ollama :: openhermes' ./cmdline.py`

To see more logs, adjust the log level like `CHATBOT_LOG_LEVEL=DEBUG`.


## Development

- The chatbot package `chatbot/__init__.py` is run for all apps because they `import chatbot`.
- It initializes settings (`_init_settings()`) and creates a specified chat engine (`create_chat_engine(settings)`).

### Adding a chat engine

A chat engine specifies a process that interfaces with an LLM (or multiple LLMs) and ultimately produces a response.
To create a chat engine, add a new Python file under `chatbot/engines` with:
- a constant `ENGINE_NAME` set to a unique chat engine name; this name is used as a value for the `CHAT_ENGINE` setting or environment variable.
- an `init_engine(settings)` function to instantiate a chat engine class
- a chat engine class that:
    - creates a client to an LLM (`create_llm_client(settings)`), then
    - uses the LLM client to generate a response to specified query (`gen_response(self, query)`)

The `chat_engine.gen_response(query)` function is called by the apps when a user submits a query.

### Adding an LLM client

An LLM client enables interacting with a specified language model via some LLM API. To add a new LLM model to an existing LLM client, add the model's name to `MODEL_NAMES` of the corresponding `*_client.py` file.

To create a new LLM client, add a new Python file under `chatbot/llms` with:
- a constant `CLIENT_NAME` set to a unique LLM provider name; this name is used as a value for the `LLM_MODEL_NAME` setting or environment variable;
- a constant `MODEL_NAMES` set to a list of language model names recognized by the LLM provider;
- an `init_client(model_name, settings)` function to instantiate an LLM client class;
- an LLM client class that:
    - sets `self.client` based on the provided `settings`, and
    - implements a `submit(self, message)` function that uses `self.client` to generate a response, which may need to be parsed so that a string is returned to `chat_engine.gen_response(self, query)`.

An LLM client can be used in any arbitrary program by:
- setting `client = init_client(model_name, settings)`
- then calling `client.submit(message)`
See `client_example_usage()` in `chatbot/llms/mock_llm_client.py`.
