import base64
import hmac
import json
import time
from functools import wraps

import openai
import streamlit as st

st.set_page_config(layout="wide")



def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], "gates"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

if not check_password():
    st.stop()


@st.cache_resource
def get_client():
    return openai.OpenAI()

PROMPT = (
"""Please review the attached document and respond with a JSON object matching the DocumentAnalysis type definition provided below. Do not respond with anything else besides the DocumentAnalysis JSON object.
Note that the `identity` documents must include a photo of the person, and that a document can provide multiple kinds of evidence.

interface Evidence {
 evidence_type: "residency" | "identity" | "income" | "expenses" | "disability" | "immigration"; // what type of evidence the document corresponds to
 reason: string; // the justification for the document providing this type of evidence
}

interface DocumentAnalysis {
 evidence: Evidence[]; // a list of the various evidences that the document provides
 legible: boolean; // if the document is legible, e.g., false if the document is blurry
 address: string | null; // the  person's residence if the document contains an address
}

Remember, do not respond with anything other than valid JSON.
"""
)

def timed(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()  # Record the start time
        result = func(*args, **kwargs)  # Call the function
        end_time = time.time()  # Record the end time
        execution_time = end_time - start_time  # Calculate execution time
        return result, execution_time  # Append the execution time to the original result
    return wrapper

def main():
    st.title("Classify documents")

    with st.form("upload-files", clear_on_submit=True):
        files = st.file_uploader("Upload documents",
            accept_multiple_files=True,
        )

        if st.form_submit_button("Process documents", type="primary") and files:
            process_files(files)
            files = None

def process_files(files):
    results = []
    for file in files:
        with st.spinner(f"Processing {file.name}..."):
            results.append(process_file(file))
    display_results(results)

@timed
def process_file(file):
    base64_image = base64.b64encode(file.read()).decode('utf-8')
    client = get_client()
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {
            "role": "user",
            "content": [
                {
                "type": "text",
                "text": PROMPT,
                },
                {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                },
                },
            ],
            }
        ],
        max_tokens=300,
        )
    tokens = response.usage.total_tokens
    response_string = response.choices[0].message.content
    try:
        response_content = json.loads(response_string)
    except:
        # GPT4-turbo sometimes likes to wrap it with ```json {content here}```
        if response_string.startswith("```json"):
            response_content = json.loads(response_string[7:-3])
        else:
            st.write("Error processing response:")
            st.code(response_string)
            st.stop()
    return file.name, response_content, tokens

def display_results(results):
    display_classification(results)
    display_legibility(results)
    display_timing_and_cost(results)

def display_classification(results):
    classification_table = []
    for result in results:
        classification_result = result[0][1]
        if classification_result["legible"]:
            for evidence in classification_result["evidence"]:
                classification_table.append(
                    {
                        "Evidence": evidence["evidence_type"],
                        "Document": result[0][0],
                        "Reason": evidence["reason"],
                        "Caveats": "n/a" if evidence["evidence_type"] != "residency" else f"If current address is {classification_result['address']}"
                    }
                )
    st.subheader("Evidence provided")
    st.table(classification_table)

def display_legibility(results):
    legibility_table = []
    for result in results:
        legibility_table.append(
            {
                "Document": result[0][0],
                "Legibility": result[0][1]["legible"],
            }
        )
    st.subheader("Legibility results")
    st.table(legibility_table)

def display_timing_and_cost(results):
    timing_and_cost_table = []
    total_cost = 0
    total_time = 0
    for result in results:
        # Super rough, not at all accurate cost estimate
        # See https://help.openai.com/en/articles/7127956-how-much-does-gpt-4-cost
        est_cost = result[0][2] * .001 * .01
        total_cost += est_cost
        total_time += result[1]
        timing_and_cost_table.append(
            {
                "Document": result[0][0],
                "Tokens": result[0][2],
                "Cost (estimated)": f"${est_cost:.2f}",
                "Time (seconds)": f"{result[1]:.2f}",
            }
        )
    st.subheader("Timing and costs")
    st.table(timing_and_cost_table)
    st.write(f"Total cost (estimated): ${total_cost:.2f}")
    st.write(f"Total time (seconds): {total_time:.2f}")

main()