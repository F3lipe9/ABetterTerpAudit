GET /exercises without credentials (retest)
Captured 2026-10-10

$ curl -i "http://127.0.0.1:8000/exercises?username=testUser2"
HTTP/1.1 401 Unauthorized
{"detail":"Not authenticated"}

$ curl -i "http://127.0.0.1:8000/exercises?username=ghostUserX"      (a username that has never existed)
HTTP/1.1 401 Unauthorized
{"detail":"Not authenticated"}

Seeding side effect: GET /exercises no longer seeds anything. Default exercises are inserted once, at registration (seed_default_exercises in the /register handler). With a valid token the GET only reads: it returns the caller's own exercises.

Result: FIXED. Unauthenticated callers can neither read nor cause writes for any username.
