This experiment uses LangGraph to combine local resources to provide benefit referrals.

## Setup

You'll need the following to run this code:

- `.env` file with the 211 API key. You can request one [here](https://apiportal.211.org/)
- a csv file (optional, but necessary to run the spreadsheet query tool) `nyc_referral_csv.csv`, see `my_tools.py` file for instructions to download
- Ollama, installed [here](https://ollama.ai/)

To install dependencies

```
pip install -r requirements.txt
```

To run the llm

```
ollama run openhermes
```

To run the program

```
./langgraph-workflow.py
```
