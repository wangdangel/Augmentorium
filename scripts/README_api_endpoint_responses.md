# API Endpoint Response Dumper

This script (`api_endpoint_responses.py`) systematically calls all major backend endpoints and saves their responses to `api_endpoint_responses.json` for review.

## Usage
1. Make sure your backend server is running at `http://localhost:6655`.
2. Activate your Python virtual environment (if needed).
3. Run the script:
   ```sh
   python scripts/api_endpoint_responses.py
   ```
4. Open `api_endpoint_responses.json` to review all endpoint responses, status codes, and payloads.

## Endpoints Covered
- `/api/health/` (GET)
- `/api/indexer/` (GET)
- `/api/indexer/status` (GET, POST)
- `/api/graph/` (GET)
- `/api/cache/` (GET, DELETE)
- `/api/query/` (POST)
- `/api/query/cache` (DELETE)
- `/api/projects/` (GET, POST)
- `/api/projects/active` (GET)

You can easily expand the script to add more endpoints or payloads as needed.
