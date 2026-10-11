F01 retest - unauthenticated access to assignments (captured 2026-10-10, backend restarted on the fixed commit)
Users: testUser1 (token A), testUser2 (token B). Tokens redacted; they were not saved.

curl -i "http://127.0.0.1:8000/assignments/user/testUser1"   (no credentials)
HTTP/1.1 404 Not Found
{"detail":"Not Found"}

curl -i "http://127.0.0.1:8000/assignments/user/testUser2"   (no credentials)
HTTP/1.1 404 Not Found
{"detail":"Not Found"}
(The per-username route no longer exists; the old leak path is gone.)

curl -i "http://127.0.0.1:8000/assignments"   (no credentials, the old global dump)
HTTP/1.1 401 Unauthorized
www-authenticate: Bearer
{"detail":"Not authenticated"}

curl -i -H "Authorization: Bearer abc.def.ghi" "http://127.0.0.1:8000/assignments"   (garbage token)
HTTP/1.1 401 Unauthorized
{"detail":"Not authenticated"}

Controls (authenticated, scoped to the caller):
curl -H "Authorization: Bearer <TOKEN_A>" "http://127.0.0.1:8000/assignments"
HTTP/1.1 200 OK
[{"title":"testUser1 assignment","course":"CMSC131","dueDate":"2026-12-01","status":"pending","priority":"medium","type":"homework","points":"0","username":"testUser1","_id":"6acaccb28b14f499dd5307f5"}]

curl -H "Authorization: Bearer <TOKEN_B>" "http://127.0.0.1:8000/assignments"
[{"title":"testUser2 assignment","course":"CMSC131","dueDate":"2026-12-01","status":"pending","priority":"medium","type":"homework","points":"0","username":"testUser2","_id":"6acaccb28b14f499dd5307f9"}]
(Each user sees only their own records; no other user's data appears in either response.)

Cross-user check by id (B's assignment id = 6acaccb28b14f499dd5307f9):
GET /assignments/<B id>  no credentials  -> 401
GET /assignments/<B id>  token A         -> 404 {"detail":"Assignment not found"}
GET /assignments/<B id>  token B         -> 200

Also: GET /assignments/user/testUser2 with token A -> 404 (route removed).

Result: FIXED. Every original request now returns 401 or 404 without credentials, and an authenticated user cannot read another user's assignments by list or by id.
Note: these testUser1/2 records are fresh seed data, not the original records from the F01 capture; the emails used at registration were testuser1@abc.com and testuser2@abc.com.
