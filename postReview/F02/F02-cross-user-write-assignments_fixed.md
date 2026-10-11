Cross-user write into testUser2's account - assignments (retest)
Captured 2026-10-10

1) No credentials:
$ curl -i -X POST http://127.0.0.1:8000/assignments -H "Content-Type: application/json" \
  -d '{"title":"F02-planted","course":"TEST101","dueDate":"2026-12-01","username":"testUser2"}'
HTTP/1.1 401 Unauthorized
{"detail":"Not authenticated"}

2) Authenticated as testUser1 (<TOKEN_A>), same body naming testUser2:
HTTP/1.1 201 Created
{"title":"F02-planted","course":"TEST101","dueDate":"2026-12-01","status":"pending","priority":"medium","type":"homework","points":"0","username":"testUser1","_id":"6acacdf88b14f499dd5307fd"}
The body "username" was ignored; the record belongs to testUser1.

3) Verification: GET /assignments with <TOKEN_B> does not contain F02-planted; with <TOKEN_A> it does (removed afterwards by testUser1, 200).

Result: FIXED.
