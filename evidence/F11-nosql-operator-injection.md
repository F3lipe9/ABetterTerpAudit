F11 - NoSQL operator injection attempt on POST /login
Result: NOT VULNERABLE
Captured 2026-10-10

$ curl -i -X POST http://127.0.0.1:8000/login -H "Content-Type: application/json" \
  -d '{"username":{"$ne":""},"password":{"$ne":""}}'

HTTP/1.1 422 Unprocessable Content
{"detail":[
  {"type":"string_type","loc":["body","username"],"msg":"Input should be a valid string","input":{"$ne":""}},
  {"type":"string_type","loc":["body","password"],"msg":"Input should be a valid string","input":{"$ne":""}}
]}

RESULT: as expected, 422. Pydantic's LoginRequest model (backend/main.py:65-67)
types `username` and `password` as plain `str`, so FastAPI rejects a JSON object
payload before it ever reaches the Mongo query - the classic `{"$ne": ""}` /
`{"$gt": ""}` style NoSQL operator-injection trick that works against
hand-rolled, untyped query builders does not work here, because Pydantic's type
coercion only accepts actual strings for these fields.

CONCLUSION: tested and safe. The protection is incidental (a side effect of using
Pydantic request models with str-typed fields) rather than deliberate input
sanitization, but the outcome holds for every route that types its request body
the same way.
