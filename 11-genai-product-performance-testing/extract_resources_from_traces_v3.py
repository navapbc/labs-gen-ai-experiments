#!/usr/bin/env python3
"""
Extract full system prompt with resources from production Phoenix traces v3
Focus on generate_referrals spans and their child LLM spans
"""
import httpx
import json
import os
import re
import sys

# Never hardcode credentials or internal URLs — load from environment.
# Copy .env.example to .env and fill in values before running.
PHOENIX_URL = os.environ.get("PHOENIX_URL")
PHOENIX_PROJECT_NAME = os.environ.get("PHOENIX_PROJECT_NAME", "pilot-prod")
PHOENIX_API_KEY = os.environ.get("PHOENIX_API_KEY")

if not PHOENIX_URL or not PHOENIX_API_KEY:
    sys.exit("ERROR: PHOENIX_URL and PHOENIX_API_KEY must be set in the environment.\n"
             "Copy .env.example to .env and fill in your values.")

headers = {"Authorization": f"Bearer {PHOENIX_API_KEY}"}

print("="*80)
print("EXTRACTING RESOURCES FROM PRODUCTION TRACES (V3)")
print("="*80)
print(f"Phoenix URL: {PHOENIX_URL}")
print(f"Project: {PHOENIX_PROJECT_NAME}")
print("Strategy: Look for generate_referrals CHAIN spans and their child LLM spans")
print("="*80)

# Fetch spans
print("\nFetching spans...")
all_spans = []
cursor = None
max_pages = 10  # Get more pages to find referral spans

for page in range(max_pages):
    url = f"{PHOENIX_URL}/v1/projects/{PHOENIX_PROJECT_NAME}/spans"
    if cursor:
        url += f"?cursor={cursor}"

    try:
        response = httpx.get(url, headers=headers, verify=False, timeout=60.0)
        data = response.json()
        spans = data.get('data', [])

        all_spans.extend(spans)
        print(f"  Page {page+1}: {len(spans)} spans (total: {len(all_spans)})")

        cursor = data.get('next_cursor')
        if not cursor or len(spans) == 0:
            break
    except Exception as e:
        print(f"  Error fetching page {page+1}: {e}")
        break

print(f"\n✅ Total spans fetched: {len(all_spans)}\n")

# Build a map of spans by ID for parent-child relationships
spans_by_id = {span['id']: span for span in all_spans}

# Find generate_referrals CHAIN spans
print(f"{'='*80}")
print("LOOKING FOR generate_referrals SPANS")
print(f"{'='*80}")

referral_chain_spans = []
for span in all_spans:
    name = span.get('name', '').lower()
    if 'generate' in name and 'referral' in name:
        print(f"Found: {span.get('name')} (kind: {span.get('span_kind')}, id: {span.get('id')})")
        referral_chain_spans.append(span)

print(f"\nFound {len(referral_chain_spans)} generate_referrals spans")

# For each CHAIN span, find its child LLM spans
resource_texts = []
largest_resource_section = ""

for chain_span in referral_chain_spans:
    chain_id = chain_span['id']
    print(f"\n{'='*80}")
    print(f"Examining children of CHAIN span: {chain_span.get('name')}")
    print(f"{'='*80}")

    # Find child spans
    child_llm_spans = []
    for span in all_spans:
        if span.get('parent_id') == chain_id and span.get('span_kind') == 'LLM':
            child_llm_spans.append(span)

    print(f"  Found {len(child_llm_spans)} child LLM spans")

    # Look for llm.input_messages in child LLM spans
    for llm_span in child_llm_spans:
        attrs = llm_span.get('attributes', {})

        # Check for llm.input_messages
        llm_input = attrs.get('llm.input_messages')

        if llm_input:
            try:
                # Parse if it's a JSON string
                if isinstance(llm_input, str):
                    messages = json.loads(llm_input)
                else:
                    messages = llm_input

                if isinstance(messages, list):
                    for msg in messages:
                        if not isinstance(msg, dict):
                            continue

                        role = msg.get('role', '')
                        content = msg.get('content', '')

                        # Look for system messages with resources
                        if role == 'system' and isinstance(content, str) and '## Resources' in content:
                            print(f"\n  {'='*40}")
                            print(f"  FOUND SYSTEM MESSAGE WITH RESOURCES!")
                            print(f"  {'='*40}")
                            print(f"  LLM Span: {llm_span.get('name')}")
                            print(f"  System message length: {len(content)} chars")

                            # Try to extract the resources section
                            # Look for text between "{% for s in supports %}" and "Career Advancement Training"
                            # Or between "## Resources" and "Career Advancement Training"
                            match = re.search(
                                r'## Resources.*?In addition to.*?choose from following list of resources:(.*?)(?:Career Advancement Training|Additional resources:)',
                                content,
                                re.DOTALL | re.IGNORECASE
                            )

                            if match:
                                resources = match.group(1).strip()
                                print(f"  Extracted {len(resources)} characters of injected resources")
                                print(f"\n  First 500 characters:")
                                print(f"  {resources[:500]}")

                                if len(resources) > len(largest_resource_section):
                                    largest_resource_section = resources

                                resource_texts.append({
                                    'chain_span_name': chain_span.get('name'),
                                    'llm_span_name': llm_span.get('name'),
                                    'resources': resources,
                                    'full_system_message': content
                                })
                            else:
                                # Just save full prompt if it's substantial
                                if len(content) > 10000:  # Large prompt likely has resources
                                    print(f"  Saving full system message (no regex match, but {len(content)} chars)")
                                    resource_texts.append({
                                        'chain_span_name': chain_span.get('name'),
                                        'llm_span_name': llm_span.get('name'),
                                        'resources': "FULL_PROMPT",
                                        'full_system_message': content
                                    })

            except json.JSONDecodeError as e:
                print(f"  Error parsing JSON: {e}")
            except Exception as e:
                print(f"  Error processing span: {e}")

print(f"\n{'='*80}")
print("EXTRACTION RESULTS")
print(f"{'='*80}")
print(f"Found {len(resource_texts)} system messages with resources")

if largest_resource_section:
    print(f"Largest resource section: {len(largest_resource_section)} characters")

if resource_texts:
    # Save the one with the most comprehensive prompt
    best = max(resource_texts, key=lambda x: len(x['full_system_message']))

    print(f"\nSaving largest prompt: {len(best['full_system_message'])} characters")
    print(f"  CHAIN span: {best['chain_span_name']}")
    print(f"  LLM span: {best['llm_span_name']}")

    with open('extracted_production_resources.txt', 'w') as f:
        f.write("# Extracted from Production Phoenix Trace\n")
        f.write(f"# CHAIN Span: {best['chain_span_name']}\n")
        f.write(f"# LLM Span: {best['llm_span_name']}\n")
        f.write(f"# Full system message length: {len(best['full_system_message'])} chars\n")
        f.write("=" * 80 + "\n\n")
        f.write(best['full_system_message'])

    print(f"✅ Saved to: extracted_production_resources.txt")

    # Also save just the resources section if we found one
    if best['resources'] != "FULL_PROMPT" and best['resources']:
        with open('extracted_resources_only.txt', 'w') as f:
            f.write("# Just the Resources Section (Database-Injected)\n")
            f.write("=" * 80 + "\n\n")
            f.write(best['resources'])
        print(f"✅ Also saved resources-only to: extracted_resources_only.txt")
else:
    print("\n⚠️  No system messages with resources found in traces")
    print("Note: Possible reasons:")
    print("  - Production might not be logging full prompts to Phoenix")
    print("  - Resources might be injected at a different layer")
    print("  - Need to check application source code for how prompts are constructed")

print("\n" + "=" * 80)
