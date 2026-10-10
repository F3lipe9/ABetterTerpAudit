Shared default exercise "id" across users - PUT by id with no ownership check
Captured 2026-10-10

Default exercises are seeded per-user but reuse the SAME "id" string (e.g.
"bench", "squat") across every user's copy - see DEFAULT_EXERCISES /
ensure_default_exercises in backend/main.py. PUT /exercises/{exercise_id}
updates by `{"id": exercise_id}` with find_one_and_update and NO username
filter (see update_exercise, backend/main.py ~line 511):

    updated = await exercises_collection.find_one_and_update(
        {"id": exercise_id},
        {"$set": update_doc},
        return_document=ReturnDocument.AFTER,
    )

Before this test: testUser2 had a "bench" exercise; testUser1 did not currently
have one (removed during earlier audit activity), so only one document in the
whole collection matched id "bench" at test time.

$ curl -i -X PUT "http://127.0.0.1:8000/exercises/bench" -H "Content-Type: application/json" -d '{"name":"F02-edited"}'
HTTP/1.1 200 OK
{"message":"Exercise updated","exercise":{"...,"id":"bench","name":"F02-edited",...,"username":"testUser2"}}

Verified: GET /exercises?username=testUser2 shows "bench" renamed to
"F02-edited"; GET /exercises?username=testUser1 still has no "bench" doc.
(Reverted back to "Barbell Bench Press" immediately after capture.)

FINDING: the route has no per-user scoping at all - it matches on the shared
"id" field alone. With the current single match, the request landed on
testUser2. But since every user's seeded defaults use the identical "id"
value, whenever two (or more) users both hold a document with the same id
(the normal, expected state right after seeding), this update will silently
hit whichever one of them Mongo's find_one_and_update happens to return,
not necessarily the caller's own copy, and not necessarily only one of them
if a user calls this repeatedly - any caller who knows a default id string
(a closed, guessable list: "bench", "squat", "deadlift", ...) can edit some
user's copy of that exercise with zero identity check of any kind, including
not supplying a username.
