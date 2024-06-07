# Experiment 3: Document classification

This prototype uses a multimodal LLM (GPT-4o) to automatically:
 - Determine whether a document is legible (e.g., not too blurry)
 - Determine what kind of document it is (e.g., driver's license, student ID, etc.)
 - Determine what kind of evidence the document provides (e.g., proof of identity, residence, expenses, etc.)
 - Extract arbitrary key/value pairs from the document

To run it, set OPENAI_API_KEY in your environment and then `streamlit run app.py`.