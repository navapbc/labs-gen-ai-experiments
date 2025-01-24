# Experiment 3: Document classification

This prototype uses a multimodal LLM (GPT-4o) to automatically:
 - Determine whether a document is legible (e.g., not too blurry)
 - Determine what kind of document it is (e.g., driver's license, student ID, etc.)
 - Determine what kind of evidence the document provides (e.g., proof of identity, residence, expenses, etc.)
 - Extract arbitrary key/value pairs from the document

## Prerequisites

- An OpenAI API key with access to GPT-4o

## Setup Instructions

1. Clone this repository and navigate to the project directory:
```bash
cd 03-document-classification
```

2. Create and activate a Python virtual environment:
```bash
# Create the virtual environment
python -m venv venv

# Activate it on macOS
source venv/bin/activate
```

3. Install the required packages:
```bash
pip install python-dotenv streamlit openai
```

4. Create a `.env` file in the project directory and add your OpenAI API key:
```bash
echo "OPENAI_API_KEY=your-api-key-here" > .env
```
Replace `your-api-key-here` with your actual OpenAI API key.

5. Run the Streamlit app:
```bash
streamlit run app.py
```

The app should now be running and accessible at http://localhost:8501 (or another port if 8501 is in use).

## Using the App

1. Open the app in your web browser
2. Use the file uploader to upload one or more document images
3. Click "Process documents" to analyze them

## Troubleshooting

If you encounter any issues:

1. Make sure your virtual environment is activated (you should see `(venv)` in your terminal)
2. Verify your OpenAI API key is correct and has access to GPT-4o
3. Check that all required packages are installed by running:
   ```bash
   pip install -r requirements.txt
   ```