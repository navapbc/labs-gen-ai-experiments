
## Setup

### Python
* Use Python 3.11.x (higher versions cause library version problems).
* Install Python libraries: `pip install -r requirements.txt`

### (Optional) Enable Chatbot Feedback
To enable the [feedback mechanism](https://docs.chainlit.io/data-persistence/feedback):
* Get an API key: https://docs.chainlit.io/data-persistence/overview
* Create or update `.env` with `LITERAL_API_KEY` set to the API key

After running the chatbot and providing feedback in the UI, review the feedback at https://cloud.getliteral.ai/projects/YOUR_PROJECT_NAME/feedback.

* To use custom feedback storage instead of `getliteral.ai`, see https://docs.chainlit.io/data-persistence/custom.


## Running an application

There are several ways to run the chatbot application, offering different ways to interact with the chatbot.
All apps use configurations set in `.env`, which is *not* checked into git. These configurations (like `CHAT_ENGINE` and `LLM_MODEL_NAME`) can be overridden by environment variables set on the commandline.  See `_init_settings()` in `chatbot/__init__.py` for other variables.

### Run commandline app

This commandline application entrypoint is useful for quickly or repeatedly running, testing, or debugging without having to click through or type in a UI. Set the configuration in `.env` or as environment variables, then run `./cmdline.py`.

To quickly set variables and run the app on a single line: 
`CHATBOT_LOG_LEVEL=INFO CHAT_ENGINE=Direct LLM_MODEL_NAME='langchain.ollama :: openhermes' ./cmdline.py`

To see more logs, adjust the log level, like `CHATBOT_LOG_LEVEL=DEBUG`.

### Run chatbot web app

This application provides a chatbot web app that users typically interact with.

1. Start the Chainlit-based chatbot service: `./chatbot-chainlit.py` or `chainlit run ./chatbot-chainlit.py`
1. Open a browser to `http://localhost:8000/`

For development, run something like `chainlit run -w -h --port 9000 ./chatbot-chainlit.py` to watch for changed files and automatically update the running application without having to restart chainlit.

Chainlit UI configurations are in the `.chainlit/config.toml` file.

Running the chatbot app will also run the API (described in the next section), which is defined in `chatbot_api.py`.

### Run only the API

This application runs the chatbot API for other applications to make requests to the chatbot.

1. Run `./chatbot_api.py`
1. Test a query: `curl -X POST "http://localhost:8001/query" -d 'message="tell me a joke"'`

## Development Notes

- Application entrypoints are in the root folder of the repo. Other Python files are under the `chatbot` folder.
- The chatbot package `chatbot/__init__.py` is run for all apps because they `import chatbot`.
- It initializes settings (`_init_settings()`) and creates a specified chat engine (`create_chat_engine(settings)`).

### Adding a chat engine

A chat engine specifies a process that interfaces with an LLM (or multiple LLMs) and ultimately produces a response.
To create a chat engine, add a new Python file under `chatbot/engines` with:
- a constant `ENGINE_NAME` set to a unique chat engine name; this name is used as a value for the `CHAT_ENGINE` setting or environment variable.
- an `init_engine(settings)` function to instantiate a chat engine class
- a chat engine class that:
    - creates a client to an LLM (`create_llm_client(settings)`), then
    - uses the LLM client to generate a response to a specified query (`gen_response(self, query)`)
The new Python file will be automatically discovered and registered for display in the Chainlit settings web UI.

The `chat_engine.gen_response(query)` function is called by the apps when a user submits a query.

### Adding an LLM client

An LLM client enables interacting with a specified language model via some LLM API. To add a new LLM model to an existing LLM client, add the model's name to `MODEL_NAMES` of the corresponding `*_client.py` file.

To create a new LLM client, add a new Python file under `chatbot/llms` with:
- a constant `CLIENT_NAME` set to a unique LLM provider name; this name is used as a value for the `LLM_MODEL_NAME` setting or environment variable;
- a constant `MODEL_NAMES` set to a list of language model names recognized by the LLM provider;
- an `init_client(model_name, settings)` function to instantiate an LLM client class;
- an LLM client class that:
    - sets `self.client` based on the provided `settings`, and
    - implements a `generate_reponse(self, message)` function that uses `self.client` to generate a response, which may need to be parsed so that a string is returned to `chat_engine.gen_response(self, query)`.
- (optional) a `requirements_satisfied()` function that checks if necessary environment variable(s) and other LLM client preconditions are satisfied;
The new Python file will be automatically discovered and registered for display in the Chainlit settings web UI.

An LLM client can be used in any arbitrary program by:
- setting `client = init_client(model_name, settings)`
- then calling `client.generate_reponse(message)`
See `client_example_usage()` in `chatbot/llms/mock_llm_client.py`.

### Python formatting

Install and run `ruff format .` and `isort .` to consistently format Python files.

### Docker

A Docker image is built for deployments (by GitHub Action `push-image.yml`). To verify that the image builds and runs correctly, run:
```
GURU_CARDS_URL_ID='1fO-ABCD1234...' # Google Drive document id
docker build -t dst-chatbot . --build-arg GURU_CARDS_URL="https://docs.google.com/uc?export=download&id=$GURU_CARDS_URL_ID"
docker run --rm -p 8000:8000 dst-chatbot
```
Then, open a browser to `http://localhost:8000/` for testing.
