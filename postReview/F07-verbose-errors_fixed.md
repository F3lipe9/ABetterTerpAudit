F07 - Verbose server errors leak internal implementation details - POST-FIX RETEST
Re-run 2026-10-10 against http://127.0.0.1:8000 (authenticated as testUser1; routes now require a bearer token,
so the original unauthenticated calls would only return 401 "Not authenticated")

----- Raw output -----

$ curl -i -H "Authorization: Bearer <token>" http://127.0.0.1:8000/assignments/badid
HTTP/1.1 400 Bad Request
server: uvicorn
content-length: 23
content-type: application/json
x-content-type-options: nosniff
x-frame-options: DENY
referrer-policy: no-referrer
vary: Origin

{"detail":"Invalid id"}


$ curl -i -X PUT .../assignments/badid -d {"title":"x"}
HTTP/1.1 400 Bad Request
server: uvicorn
content-length: 23
content-type: application/json
x-content-type-options: nosniff
x-frame-options: DENY
referrer-policy: no-referrer
vary: Origin

{"detail":"Invalid id"}


$ curl -i -X DELETE .../assignments/badid
HTTP/1.1 400 Bad Request
server: uvicorn
content-length: 23
content-type: application/json
x-content-type-options: nosniff
x-frame-options: DENY
referrer-policy: no-referrer
vary: Origin

{"detail":"Invalid id"}


$ curl -i -X DELETE .../habits/badid
HTTP/1.1 404 Not Found
server: uvicorn
content-length: 28
content-type: application/json
x-content-type-options: nosniff
x-frame-options: DENY
referrer-policy: no-referrer
vary: Origin

{"detail":"Habit not found"}


$ curl -i -X DELETE .../exercises/badid
HTTP/1.1 404 Not Found
server: uvicorn
content-length: 31
content-type: application/json
x-content-type-options: nosniff
x-frame-options: DENY
referrer-policy: no-referrer
vary: Origin

{"detail":"Exercise not found"}


$ curl -i -X PUT .../exams/badid (full body)
HTTP/1.1 400 Bad Request
server: uvicorn
content-length: 23
content-type: application/json
x-content-type-options: nosniff
x-frame-options: DENY
referrer-policy: no-referrer
vary: Origin

{"detail":"Invalid id"}


----- Comparison with original -----
GET    /assignments/badid : 500 "Failed to fetch assignment: 'badid' is not a valid ObjectId..." -> 400 {"detail":"Invalid id"}
PUT    /assignments/badid : 422 (body rejected first)                                            -> 400 {"detail":"Invalid id"}
DELETE /assignments/badid : 500 "Failed to delete assignment: 'badid' is not a valid ObjectId..." -> 400 {"detail":"Invalid id"}
Additional routes checked (DELETE habits, DELETE exercises, PUT exams): generic 404/400, no leak.

CODE: every `except Exception` handler in backend/main.py now logs server-side and raises
HTTPException(500, "Internal server error"). Ids are validated by parse_object_id() (main.py:105), which
returns 400 before ObjectId construction can throw.

Note: the 500 path was not triggered by these tests (no DB failure induced); it was confirmed by code review only.

Result: FIXED. Malformed ids now return a generic 400 "Invalid id" (assignments, exams) or a generic 404
(habits, exercises). No bson/ObjectId text, 12-byte / 24-hex rule, or raw exception string is returned anywhere.
