# F02 retest - (a) per-user reads and (b) global dump
Captured 2026-10-10, backend restarted on the fixed commit. Tokens redacted (not saved).

## a. Per-user reads, no credentials
```
$ curl -i "http://127.0.0.1:8000/habits?username=testUser1"      -> 401 {"detail":"Not authenticated"}
$ curl -i "http://127.0.0.1:8000/habits?username=testUser2"      -> 401
$ curl -i "http://127.0.0.1:8000/water?username=testUser1"       -> 401
$ curl -i "http://127.0.0.1:8000/water?username=testUser2"       -> 401
$ curl -i "http://127.0.0.1:8000/exams?username=testUser1"       -> 401
$ curl -i "http://127.0.0.1:8000/exams?username=testUser2"       -> 401
$ curl -i "http://127.0.0.1:8000/exercises?username=testUser2"   -> 401
$ curl -i "http://127.0.0.1:8000/assignments/user/testUser1"     -> 404 {"detail":"Not Found"} (route removed)
$ curl -i "http://127.0.0.1:8000/assignments/user/testUser2"     -> 404 (route removed)
```

Authenticated as testUser1 (<TOKEN_A>), supplying `?username=testUser2`:
```
GET /habits?username=testUser2     -> 200, every record has username "testUser1"
GET /water?username=testUser2      -> 200, record is testUser1's
GET /exams?username=testUser2      -> 200, every record has username "testUser1"
GET /exercises?username=testUser2  -> 200, every record has username "testUser1"
```
The `username` parameter is now ignored; the server uses the identity in the token. Control (no parameter, token A) returns the same testUser1-only data for habits, water, exams, exercises and assignments.

## b. Global dump
```
$ curl -i "http://127.0.0.1:8000/assignments"                       -> 401 {"detail":"Not authenticated"}
$ curl -i -H "Authorization: Bearer <TOKEN_A>" .../assignments       -> 200, only testUser1's assignments
$ curl -i -H "Authorization: Bearer <TOKEN_B>" .../assignments       -> 200, only testUser2's assignments
```

Result: FIXED. No endpoint answers without credentials, and no authenticated caller can read another user's data by changing a username parameter.
