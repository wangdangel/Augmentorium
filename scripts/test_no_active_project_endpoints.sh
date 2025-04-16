#!/bin/bash
# Test Augmentorium API endpoints with NO active project set

API_URL="http://localhost:6655"

echo "1. /api/health (should return status ok)"
curl -s -X GET "$API_URL/api/health" | jq

echo "2. /api/projects (should return list, even if empty)"
curl -s -X GET "$API_URL/api/projects" | jq

echo "3. /api/projects/active (should return project: null)"
curl -s -X GET "$API_URL/api/projects/active" | jq

echo "4. /api/query (should return 400 and 'no active project' error)"
curl -s -o /dev/stderr -w "\nHTTP %{http_code}\n" -X POST "$API_URL/api/query" -H "Content-Type: application/json" -d '{"query":"test"}'

echo "5. /api/documents (should return 400 and 'no active project' error)"
curl -s -o /dev/stderr -w "\nHTTP %{http_code}\n" -X GET "$API_URL/api/documents"

echo "6. /api/graph (should return 400 and 'no active project' error)"
curl -s -o /dev/stderr -w "\nHTTP %{http_code}\n" -X GET "$API_URL/api/graph"

echo "7. /api/cache (should return 400 and 'no active project' error)"
curl -s -o /dev/stderr -w "\nHTTP %{http_code}\n" -X DELETE "$API_URL/api/cache"