Unauthenticated GET /exercises for two different users - no credentials supplied
Captured 2026-10-10

NOTE: this GET route seeds default exercises for a user as a side effect if that
user has none yet (ensure_default_exercises(username), called inside the route
handler before querying). testUser2 had no exercises before this test; the call
below seeded the full 17-item default library for testUser2 at request time.

$ curl "http://127.0.0.1:8000/exercises?username=testUser1"
HTTP/1.1 200 OK
[9 strength/cardio exercises for testUser1, e.g. id "latpull","tricep","bike",
"tread","row","rower","legpress","curl","stairs" - a subset, since testUser1 was
already seeded earlier in prior audit activity and some items had since been
removed]

$ curl "http://127.0.0.1:8000/exercises?username=testUser2"
HTTP/1.1 200 OK
[17 exercises - the full DEFAULT_EXERCISES set - seeded by THIS unauthenticated
GET request, including id "bench","squat","deadlift","ohp","row","pullup",
"latpull","legpress","curl","tricep","lateral","tread","bike","rower",
"elliptical","stairs","jumprope"]

FINDING: no credentials were sent for either call. The server trusts the
"username" query parameter completely for both reading data and for deciding
whether to write (seed) new data. An unauthenticated caller can read, and
cause database writes for, any username.
