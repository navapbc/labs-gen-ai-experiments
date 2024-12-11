# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "openai==1.52.2",
#     "streamlit==1.34.0",
# ]
# ///
import base64
import json
import time
from functools import wraps

import openai
import streamlit as st

if __name__ == "__main__":
    if "__streamlitmagic__" not in locals():
        import streamlit.web.bootstrap

        streamlit.web.bootstrap.run(__file__, False, [], {})


st.set_page_config(layout="wide")


@st.cache_resource
def get_client():
    return openai.OpenAI()


PROMPT = """Please review the attached document and respond with a JSON object matching the DocumentAnalysis type definition provided below. Do not respond with anything else besides the DocumentAnalysis JSON object.
Note that the `identity` documents MUST include a photo of the person, and that a document can provide multiple kinds of evidence.
Do not mark a document as evidence of identity unless it includes a photo!
If you can't CLEARLY and ACCURATELY read text from the image, mark the document as not legible.

interface Evidence {
 reason: string; // the justification for why the document provides this type of evidence
 evidence_type: "residency" | "identity" | "income" | "expenses" | "disability" | "immigration"; // what type of evidence the document corresponds to
}

interface KeyValue {
    key: string; // the key of the key-value pair
    value: string; // the value of the key-value pair
    explanation: string; // what this key-value pair represents or is
}

interface DocumentAnalysis {
 evidence: Evidence[]; // a list of the various evidences that the document provides
 document_type: string | null; // the type of document, e.g., "driver's license", "utility bill", "student id", etc.
 legible: boolean; // if the document is legible, e.g., false if the document is blurry
 contains_photo; // if the document contains a photo of the person to whom the document belongs
 address: string | null; // the  person's residence if the document contains an address
 name: string | null; // the person's name if the document mentions a name
 extracted_information: KeyValue[]; // a list of key-value pairs extracted from the document, based on your judgement of what you think is important
}

Remember, do not respond with anything other than valid JSON.
"""


def timed(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()  # Record the start time
        result = func(*args, **kwargs)  # Call the function
        end_time = time.time()  # Record the end time
        execution_time = end_time - start_time  # Calculate execution time
        return (
            result,
            execution_time,
        )  # Append the execution time to the original result

    return wrapper


def main():
    st.title("Categorize documents")

    with st.form("upload-files", clear_on_submit=True):
        files = st.file_uploader(
            "Upload documents",
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
    base64_image = base64.b64encode(file.read()).decode("utf-8")
    client = get_client()
    response = client.chat.completions.create(
        model="gpt-4o",
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
        max_tokens=4_096,
    )
    response_string = response.choices[0].message.content
    try:
        response_content = json.loads(response_string)
    except Exception:
        # GPT4-turbo sometimes likes to wrap it with ```json {content here}```
        if response_string.startswith("```json"):
            try:
                response_content = json.loads(response_string[7:-3])
            except Exception:
                st.write("Error processing response:")
                st.code(response_string)
                st.stop()
        else:
            st.write("Error processing response:")
            st.code(response_string)
            st.stop()
    return (
        file.name,
        response_content,
        response.usage.prompt_tokens,
        response.usage.completion_tokens,
    )


def display_results(results):
    # Legibility
    legibility_table = []
    for result in results:
        legibility_table.append(
            {
                "Document": result[0][0],
                "Document type": result[0][1]["document_type"],
                "Legibility": "✅" if result[0][1]["legible"] else "❌",
            }
        )
    st.subheader("Legibility results")
    st.table(legibility_table)

    # Document classification and key/value pair extraction
    classification_table = []
    key_value_table = []
    for result in results:
        classification_result = result[0][1]
        if classification_result["legible"]:
            for evidence in classification_result["evidence"]:
                classification_table.append(
                    {
                        "Document": result[0][0],
                        "Evidence": evidence["evidence_type"],
                        "Reason": evidence["reason"],
                        "Caveats": (
                            "n/a"
                            if evidence["evidence_type"] != "residency"
                            else f"If current address is {classification_result['address']}"
                        ),
                        "Contains photo": (
                            "✅" if result[0][1]["contains_photo"] else "❌"
                        ),
                    }
                )
            for key_value in classification_result["extracted_information"]:
                key_value_table.append(
                    {
                        "Document": result[0][0],
                        "Key": key_value["key"],
                        "Value": key_value["value"],
                        "Explanation": key_value["explanation"],
                    }
                )

    st.subheader("Evidence provided")
    st.table(classification_table)

    with st.expander("Key value pairs extracted from documents"):
        st.subheader("Key value pairs extracted from documents")
        st.table(key_value_table)

    # Collected household information
    household_names = set()
    proved_names = set()
    for result in results:
        classification_result = result[0][1]
        if classification_result["legible"] and classification_result["name"]:
            for evidence in classification_result["evidence"]:
                if evidence["evidence_type"] in ["identity"]:
                    proved_names.add(classification_result["name"])
                household_names.add(classification_result["name"])
    st.subheader("Household information")
    household_table = [
        {"Name": name, "Identity verified": "✅" if name in proved_names else "❌"}
        for name in household_names
    ]
    st.table(household_table)

    # Timing and costs
    timing_and_cost_table = []
    total_cost_dollars = 0
    total_time = 0
    for result in results:
        # Only valid for gpt-4o, pricing as of May 2024
        # See https://help.openai.com/en/articles/7127956-how-much-does-gpt-4-cost
        # Input: $5/M tokens, Output: $15/M tokens
        est_cost_dollars = (result[0][2] / 1_000_000 * 5) + (
            result[0][3] / 1_000_000 * 15
        )
        total_cost_dollars += est_cost_dollars
        total_time += result[1]
        timing_and_cost_table.append(
            {
                "Document": result[0][0],
                "Tokens": result[0][2],
                "Cost (estimated)": f"${est_cost_dollars:.3f}",
                "Time (seconds)": f"{result[1]:.2f}",
            }
        )
    st.subheader("Timing and costs")
    st.table(timing_and_cost_table)
    st.write(f"Total cost (estimated): ${total_cost_dollars:.3f}")
    st.write(f"Total time (seconds): {total_time:.2f}")


main()
