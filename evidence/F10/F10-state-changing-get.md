F10 - Unauthenticated GET causes database writes (state-changing GET)
Captured 2026-10-10

Route: GET /exercises?username={username}
Handler calls ensure_default_exercises(username) BEFORE querying (backend/main.py
~line 467-479). That helper does:
    count = await exercises_collection.count_documents({"username": username})
    if count > 0:
        return
    docs = [{**ex, "username": username} for ex in DEFAULT_EXERCISES]
    await exercises_collection.insert_many(docs)

So a plain, unauthenticated GET request for any never-before-seen username
inserts the full 17-item default exercise library for that username.

$ curl "http://127.0.0.1:8000/exercises?username=ghost1"   -> 200 OK, 17 docs returned
$ curl "http://127.0.0.1:8000/exercises?username=ghost2"   -> 200 OK, 17 docs returned
$ curl "http://127.0.0.1:8000/exercises?username=ghost3"   -> 200 OK, 17 docs returned

Each response contained exactly 17 documents (ids: bench, squat, deadlift, ohp,
row, pullup, latpull, legpress, curl, tricep, lateral, tread, bike, rower,
elliptical, stairs, jumprope) - full raw responses saved as
F10-ghost1-response.json / F10-ghost2-response.json / F10-ghost3-response.json.
No credentials were sent for any of the three requests. This is 51 new database
documents created by three GET requests with usernames that were never
registered or authenticated in any way - an attacker (or a crawler, or a cache
warmer, or anyone probing usernames) can grow this collection arbitrarily just by
GETting unique, never-before-seen usernames.

CLEANUP - NOT PERFORMED VIA THE API, BY DESIGN:
The only delete route for exercises is `DELETE /exercises/{exercise_id}`, which
matches on the shared "id" field with NO username filter
(exercises_collection.delete_one({"id": exercise_id}) - see F02-exercise-shared-id
for the same defect). Right now at least 4 usernames (testUser2, ghost1, ghost2,
ghost3) each hold a document with id "bench" (and the same for every other
default id). Calling DELETE /exercises/bench right now would delete whichever ONE
of those four documents MongoDB's delete_one happens to match first - it could
just as easily delete testUser2's real seeded exercise as a ghost document, with
no way to control which. Using the API to clean up this test would itself risk
destroying real seeded data, so it was deliberately NOT done this way.

RECOMMENDATION FOR CLEANUP: delete directly in Atlas/mongosh, scoped by username:
    db.exercises.deleteMany({ username: { $in: ["ghost1", "ghost2", "ghost3"] } })
This is the only safe way to remove exactly the 51 ghost documents without risking
any real user's data, and it doubles as a live demonstration of why the
DELETE /exercises/{id} route (F02-g) is unsafe for exactly this reason.
