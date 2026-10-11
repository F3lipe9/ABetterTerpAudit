F04 retest - destructive admin endpoints
Captured 2026-10-10, backend restarted on the fixed commit. Tokens redacted.

Code: no /admin/* route exists in backend/main.py any more; the delete_many({}) handlers were removed.

--- Requests (live) ---
DELETE /admin/clear-assignments   no credentials  -> 404 {"detail":"Not Found"}
DELETE /admin/clear-assignments   <TOKEN_A>       -> 404
GET    /admin/clear-assignments   <TOKEN_A>       -> 404
DELETE /admin/clear-courses       no credentials  -> 404
DELETE /admin/clear-courses       <TOKEN_A>       -> 404
GET    /admin/clear-courses       <TOKEN_A>       -> 404
DELETE /assignments (whole collection) <TOKEN_A>  -> 405 Method Not Allowed
DELETE /courses     (whole collection) <TOKEN_A>  -> 405 Method Not Allowed

--- Data ---
Assignments before: testUser1 = 1, testUser2 = 1. After: 1 and 1. Courses still list the existing CMSC216 record. Nothing was deleted.

--- Related checks: shared content writes ---
POST /courses       no credentials              -> 401 Not authenticated
POST /courses       <TOKEN_A> (not an admin)    -> 403 {"detail":"Forbidden"}
POST /affirmations  <TOKEN_A> (not an admin)    -> 403 {"detail":"Forbidden"}
(ADMIN_USERNAMES is not set in backend/.env, so nobody is an admin and these two POSTs return 403 for everyone. The frontend only reads these collections.)

Result: FIXED. There is no route that deletes a whole collection, with or without a token.
Remaining note: the only way to wipe data is now direct database access, which is outside the API.
