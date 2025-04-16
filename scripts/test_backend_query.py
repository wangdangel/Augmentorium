import requests
import json

API_URL = "http://localhost:6655/api/query"
QUERY = "# Cline Rules/Instructions  ## Session Start & Task Initiation - At the start of a new session chec"
N_RESULTS = 3

payload = {
    "query": QUERY,
    "n_results": N_RESULTS
}

try:
    response = requests.post(API_URL, json=payload)
    response.raise_for_status()
    data = response.json()
    print("Backend query response:", json.dumps(data, indent=2))
except Exception as e:
    print("Error contacting backend API:", e)
