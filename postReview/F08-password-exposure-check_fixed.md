F08 - Check for password/hash exposure in API responses - POST-FIX RETEST
Re-run 2026-10-10 against http://127.0.0.1:8000 (authenticated as testUser1 where routes require a token)


Code review: users_collection is referenced only in index creation (main.py:391-392), register_user (:468, :479)
and login_user (:544). Both handlers build their own response dict; the user document is never returned.
login_user reads user["password"] only to verify the hash server-side.

New since original test: /login now also returns access_token + token_type (a signed JWT with sub, username,
iat, exp; no password data in the claims).

----- Raw output (token redacted) -----

$ curl -i -X POST /login (testUser1)
HTTP/1.1 200 OK
server: uvicorn
content-length: 347
content-type: application/json
x-content-type-options: nosniff
x-frame-options: DENY
referrer-policy: no-referrer
vary: Origin

{"message":"Login successful for testUser1","user_id":"6acaccaf8b14f499dd5307d0","username":"testUser1","access_token":"<token>","token_type":"bearer"}


$ curl -i /users
HTTP/1.1 404 Not Found
server: uvicorn
content-length: 22
content-type: application/json
x-content-type-options: nosniff
x-frame-options: DENY
referrer-policy: no-referrer
vary: Origin

{"detail":"Not Found"}


$ curl -i /users (authenticated)
HTTP/1.1 404 Not Found
server: uvicorn
content-length: 22
content-type: application/json
x-content-type-options: nosniff
x-frame-options: DENY
referrer-policy: no-referrer
vary: Origin

{"detail":"Not Found"}


$ curl -i /users/me
HTTP/1.1 404 Not Found
server: uvicorn
content-length: 22
content-type: application/json
x-content-type-options: nosniff
x-frame-options: DENY
referrer-policy: no-referrer
vary: Origin

{"detail":"Not Found"}


$ register duplicate-check response shape
HTTP/1.1 201 Created
server: uvicorn
content-length: 79
content-type: application/json
x-content-type-options: nosniff
x-frame-options: DENY
referrer-policy: no-referrer
vary: Origin

{"message":"User registered successfully","user_id":"6acad0828b14f499dd530810"}


$ grep -ic password in /habits /assignments /exams /courses /exercises /water responses
habits: 0
assignments: 0
exams: 0
courses: 0
exercises: 0
water: 0

----- Comparison with original -----
POST /login   : no password field; adds access_token/token_type (expected).
POST /register: only message + user_id.
/users        : 404 both unauthenticated and authenticated; /users/me also 404. No user listing endpoint.
Data routes   : 0 occurrences of "password" in habits, assignments, exams, courses, exercises, water responses.

Side effect of retest: created probe account "f08probe" (f08probe@abc.com) via POST /register; delete it from the DB if unwanted.

Result: STILL NOT VULNERABLE. No response includes a password or password hash. The fixes for F01/F03 (JWT auth, password hashing) did not introduce any new exposure.