import json
from pprint import pprint

with open("api_endpoint_responses.json", encoding="utf-8") as f:
    results = json.load(f)

for entry in results:
    print(f"\n--- {entry['method']} {entry['endpoint']} ---")
    print(f"Status: {entry.get('status_code', entry.get('error', 'N/A'))}")
    print("Response:")
    pprint(entry.get('response', entry.get('error', 'No response')))
