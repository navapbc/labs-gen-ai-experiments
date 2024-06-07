## Experiment 4: Call Notes

This prototype uses a Chainlit interface to upload transcripts for summarization.

To run it, set `GOOGLE_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` in a `.env` file and call

```
pip install -r requirements.txt

chainlit run chainlit-call-summaries-bot.py
```

Click on the Settings icon next to the message box to set the LLM and summarization method.

Then upload a transcript after clicking on the Upload transcript file for summarization button.
