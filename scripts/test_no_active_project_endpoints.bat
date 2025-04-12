@echo off
set API_URL=http://localhost:6655

echo 1. /api/health (should return status ok)
curl -s -X GET "%API_URL%/api/health"
echo.

echo 2. /api/projects (should return list, even if empty)
curl -s -X GET "%API_URL%/api/projects"
echo.

echo 3. /api/projects/active (should return project: null)
curl -s -X GET "%API_URL%/api/projects/active"
echo.

echo 4. /api/query (should return 400 and 'no active project' error)
curl -s -w "\nHTTP %%{http_code}\n" -X POST "%API_URL%/api/query" -H "Content-Type: application/json" -d "{\"query\":\"test\"}"
echo.

echo 5. /api/documents (should return 400 and 'no active project' error)
curl -s -w "\nHTTP %%{http_code}\n" -X GET "%API_URL%/api/documents"
echo.

echo 6. /api/graph (should return 400 and 'no active project' error)
curl -s -w "\nHTTP %%{http_code}\n" -X GET "%API_URL%/api/graph"
echo.

echo 7. /api/cache (should return 400 and 'no active project' error)
curl -s -w "\nHTTP %%{http_code}\n" -X DELETE "%API_URL%/api/cache"
echo.