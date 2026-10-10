F04 - Destructive, unauthenticated admin endpoints
Captured 2026-10-10

Routes (backend/main.py:732-751), no auth/Depends on either:
  DELETE /admin/clear-assignments  -> assignments_collection.delete_many({})
  DELETE /admin/clear-courses      -> courses_collection.delete_many({})

Both delete EVERY document in the respective collection, for every user,
in one unauthenticated request.

--- 1. BEFORE state ---
See F04-before-courses.txt, F04-before-assignments.txt.
courses: already empty at test time (0 documents) - not something this test
  put at risk, but still demonstrates the endpoint is reachable with no auth.
assignments: 5 live documents across both test users (testUser1 x2, testUser2 x3).

--- 2. The destructive calls (no credentials sent for either) ---
See F04-admin-clear-courses-call.txt, F04-admin-clear-assignments-call.txt.

$ curl -X DELETE http://127.0.0.1:8000/admin/clear-courses
{"message":"Deleted 0 courses"}

$ curl -X DELETE http://127.0.0.1:8000/admin/clear-assignments
{"message":"Deleted 5 assignments"}

--- 3. AFTER state ---
See F04-after-courses.txt, F04-after-assignments.txt.
Both GET /courses and GET /assignments returned [] - confirmed empty,
all 5 assignments (belonging to both testUser1 and testUser2) gone in one call.

--- 4. Reseed ---
Re-created the 5 assignments via 5x POST /assignments, matching the captured
before-state field-for-field (title/course/dueDate/status/priority/type/points/
username). New Mongo _ids were assigned on insert (expected - cannot force a
specific _id through the API), but the content is otherwise identical to the
original. Verified via GET /assignments afterward (F04-reseeded-assignments.txt) -
same 5 records, same usernames, same field values.
courses was already empty before and after, so nothing needed reseeding there.

FINDING: both /admin/clear-* routes are fully unauthenticated mass-delete
operations that destroy an entire collection - every user's data for that
resource type - in a single request, with no confirmation, no soft-delete, no
backup, and no audit trail. This is the most severe class of finding in this
audit: not just reading or editing one record cross-user (F02), but permanently
destroying all records of a type for all users at once.
