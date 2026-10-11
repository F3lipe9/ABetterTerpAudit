DELETE /admin/clear-assignments (retest, captured 2026-10-10)

$ curl -i -X DELETE http://127.0.0.1:8000/admin/clear-assignments        (no credentials)
HTTP/1.1 404 Not Found
{"detail":"Not Found"}

$ curl -i -X DELETE http://127.0.0.1:8000/admin/clear-assignments -H "Authorization: Bearer <TOKEN_A>"
HTTP/1.1 404 Not Found
{"detail":"Not Found"}

$ curl -i http://127.0.0.1:8000/admin/clear-assignments -H "Authorization: Bearer <TOKEN_A>"      (GET)
HTTP/1.1 404 Not Found
