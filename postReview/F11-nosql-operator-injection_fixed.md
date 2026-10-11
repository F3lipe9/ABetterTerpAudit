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

==================== POST-FIX RETEST ====================
Re-run 2026-10-10 against http://127.0.0.1:8000 (login/register unauthenticated; other routes as probe account f08probe)

Result: STILL NOT VULNERABLE. Operator objects are rejected with 422 on every body field tested, and query-string
operator tricks are ignored. LoginRequest (main.py) still types username/password as str, now with length caps
(username 1-64, password 1-128).

----- Raw output: login/register/body injection -----

$ POST /login {"username":{"$ne":""},"password":{"$ne":""}}
HTTP/1.1 422 Unprocessable Content

{"detail":[{"type":"string_type","loc":["body","username"],"msg":"Input should be a valid string","input":{"$ne":""}},{"type":"string_type","loc":["body","password"],"msg":"Input should be a valid string","input":{"$ne":""}}]}


$ POST /login {"username":{"$gt":""},"password":{"$gt":""}}
HTTP/1.1 422 Unprocessable Content

{"detail":[{"type":"string_type","loc":["body","username"],"msg":"Input should be a valid string","input":{"$gt":""}},{"type":"string_type","loc":["body","password"],"msg":"Input should be a valid string","input":{"$gt":""}}]}


$ POST /login {"username":"testUser1","password":{"$ne":""}}
HTTP/1.1 422 Unprocessable Content

{"detail":[{"type":"string_type","loc":["body","password"],"msg":"Input should be a valid string","input":{"$ne":""}}]}


$ POST /login {"username":{"$regex":".*"},"password":"x"}
HTTP/1.1 422 Unprocessable Content

{"detail":[{"type":"string_type","loc":["body","username"],"msg":"Input should be a valid string","input":{"$regex":".*"}}]}


$ POST /register {"username":{"$ne":""},"email":"a@b.com","password":"Abcdef1!xyz"}
HTTP/1.1 422 Unprocessable Content

{"detail":[{"type":"string_type","loc":["body","username"],"msg":"Input should be a valid string","input":{"$ne":""}}]}


$ GET /assignments/%7B%22$ne%22:%22%22%7D 
HTTP/1.1 400 Bad Request

{"detail":"Invalid id"}


$ GET /exercises?muscle[$ne]=x 


$ GET /habits?username[$ne]=x 


$ POST /habits {"name":{"$ne":""},"icon":"x"}
HTTP/1.1 422 Unprocessable Content

{"detail":[{"type":"missing","loc":["body","title"],"msg":"Field required","input":{"name":{"$ne":""},"icon":"x"}}]}


$ POST /water {"bottleName":{"$ne":""},"bottleOz":{"$gt":0},"dailyGoal":64}
HTTP/1.1 422 Unprocessable Content

{"detail":[{"type":"string_type","loc":["body","bottleName"],"msg":"Input should be a valid string","input":{"$ne":""}},{"type":"int_type","loc":["body","bottleOz"],"msg":"Input should be a valid integer","input":{"$gt":0}}]}



----- Raw output: query-string operator injection (curl -g) -----

$ GET /exercises?muscle[$ne]=x
HTTP/1.1 200 OK

[{"id":"bench","name":"Barbell Bench Press","muscle":"Chest","equipment":"Barbell","compound":true,"category":"Strength","createdByUser":false,"username":"f08probe"},{"id":"squat","name":"Back Squat","muscle":"Legs","equipment":"Barbell","compound":true,"category":"Strength","createdByUser":false,"username":"f08probe"},{"id":"deadlift","name":"Deadlift","muscle":"Legs","equipment":"Barbell","compo


$ GET /habits?username[$ne]=x
HTTP/1.1 200 OK

[]


$ GET /assignments?username[$ne]=x
HTTP/1.1 200 OK

[]


$ GET /exams?username[$ne]=x
HTTP/1.1 200 OK

[]


$ POST /habits {"title":{"$ne":""}}
HTTP/1.1 422 Unprocessable Content

{"detail":[{"type":"string_type","loc":["body","title"],"msg":"Input should be a valid string","input":{"$ne":""}}]}

----- Findings -----
- POST /login with {"$ne"}, {"$gt"} (both fields), {"$ne"} password only, and {"$regex"} username: all 422 string_type.
- POST /register, /habits, /water with operator objects in string/int fields: 422 type errors.
- GET /assignments/{"$ne":""} as path id: 400 "Invalid id" (parse_object_id).
- Query-string operators (?username[$ne]=x, ?muscle[$ne]=x) are ignored: handlers filter on the username from the
  JWT, so only the caller's own (f08probe's) records are returned (/habits, /assignments, /exams: [], /exercises:
  only f08probe's seeded rows). No other user's data appeared. Output above is truncated to 400 chars/line.
- The injection protection is still incidental to typed Pydantic models, but it now also has authentication
  scoping as a second layer.
