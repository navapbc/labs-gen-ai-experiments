
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

1. Start the chatbot service: `./chatbot-chainlit.py` or `chainlit run ./chatbot-chainlit.py`
1. Open a browser to `http://localhost:8000/`

For development, run something like `chainlit run -w -h --port 9000 ./chatbot-chainlit.py`.

