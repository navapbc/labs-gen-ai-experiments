
## Setup

### Python
* Use Python 3.11.x (higher versions cause library version problems).
* Install Python libraries: `pip install -r requirements.txt`

### Ollama
1. Install Ollama from https://ollama.ai/
2. Run `ollama run openhermes` to run the OpenHermes LLM, downloading it if needed.

### (Optional) Enable Chatbot feedback
To enable the [feedback mechanism](https://docs.chainlit.io/data-persistence/feedback):
* Get an API key: https://docs.chainlit.io/data-persistence/overview
* Create `.env` with the API key

After running the chatbot and providing feedback in the UI, review the feedback at https://cloud.getliteral.ai/projects/YOUR_PROJECT_NAME/feedback.

* To use a custom feedback storage instead of `getliteral.ai`, see https://docs.chainlit.io/data-persistence/custom.


## Run

1. Start the chatbot service: `./chainlit-household-bot.py` or `chainlit run chainlit-household-bot.py`
1. Open a browser to `http://localhost:8000/`

For development, run something like `chainlit run -w -h --port 9000 chainlit-household-bot.py`.

