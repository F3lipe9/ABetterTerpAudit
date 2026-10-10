# Audit Findings

Target: ABetterTerp (backend/main.py - FastAPI + MongoDB; ABetterTerp/ - React/Vite
frontend). Test accounts: `testUser1` / `testUser2` (see `users.md`). All backend
calls were made against `http://127.0.0.1:8000` unless noted.

IDs follow the audit checklist's numbering. F00 is setup evidence (the register
request capture used to create the test accounts), not a standalone finding - it
is referenced as supporting evidence under F03 below.

## Summary

| ID | Title | Endpoint(s) | Status | Severity |
|----|-------|-------------|--------|----------|
| F01 | No authentication or authorization | all data routes | Confirmed | Critical |
| F02 | Broken access control (read/write/delete, UI leak, shared IDs) | `/habits`, `/water`, `/exams`, `/assignments*`, `/exercises*` | Confirmed | Critical |
| F03 | Passwords stored in plaintext | `/register`, `/login` | Confirmed | Critical |
| F04 | Destructive, unauthenticated admin mass-delete | `DELETE /admin/clear-assignments`, `DELETE /admin/clear-courses` | Confirmed | Critical |
| F05 | No brute-force protection on login | `POST /login` | Confirmed | High |
| F06 | User enumeration + missing register validation | `POST /register` | Confirmed | Medium |
| F07 | Verbose server errors leak internals | `GET/DELETE /assignments/{id}` (and siblings) | Confirmed | Low |
| F08 | Password/hash exposure in responses | `/register`, `/login` | Not vulnerable | N/A |
| F09 | Missing input validation (exam date, water bounds) | `POST /exams`, `POST /water` | Confirmed | Low |
| F10 | State-changing GET (unauthenticated writes via read) | `GET /exercises` | Confirmed | Medium |
| F11 | NoSQL operator injection | `POST /login` | Not vulnerable | N/A |
| F12 | CORS misconfiguration | all routes (CORS middleware) | Not vulnerable | N/A |
| F13 | Secrets in source/history | repo-wide (git history, source) | Not vulnerable | N/A |
| F14 | Outdated dependencies with known CVEs | backend (pip), frontend (npm) | Confirmed | High |
| F15 | Static analysis (bandit) of backend | `backend/main.py` | Not vulnerable | N/A |

---

## F01 - No authentication or authorization on API endpoints

**Endpoint:** all data routes (`/assignments*`, `/habits`, `/water`, `/exercises*`, `/exams`, `/courses`) and `POST /login`
**Severity:** Critical
**Status:** Confirmed
**Evidence:** `evidence/F01-No-Auth.md`, `evidence/F01-login.png`

### Description
The backend never verifies who is calling. `POST /login` checks the username and
password but returns only `{message, user_id, username}`. It issues no token, session
or cookie, and no route uses `Depends` or checks a credential. Every data endpoint
(`/assignments`, `/habits`, `/water`, `/exercises`, `/exams`, `/courses`) trusts a
caller-supplied `username` or ID, so logging in has no effect on what the server allows.

### Reproduction (no credentials sent)
1. `curl http://127.0.0.1:8000/assignments/user/testUser1` returns testUser1's assignments.
2. `curl http://127.0.0.1:8000/assignments/user/testUser2` returns testUser2's assignments.
3. `curl http://127.0.0.1:8000/assignments` returns the global dump of every user's assignments.
4. Write routes (`POST/PUT/DELETE /assignments`, `DELETE /habits/{id}`, `DELETE /exercises/{id}`)
   have the same gap, so any caller can modify or delete other users' data
   (checked in code; destructive calls not executed here - see F02 for live writes/deletes).

### Impact
Anyone who can reach the API can read all users' data, enumerate usernames and assignment
IDs, and modify or delete records. No exploit skill is needed, only HTTP requests.
The app UI also shows both users' assignments to whichever user is logged in, which
confirms the server does no per-user filtering.

### Severity reasoning
- **Likelihood: high.** No credentials, tooling or prior knowledge are needed, and the
  endpoints are guessable.
- **Impact: high.** Full read, write and delete access to all user data.
- **Mitigating factor:** CORS allows only localhost origins, but CORS is a browser
  control and does not stop curl or any other non-browser client (confirmed directly
  in F12). The API currently appears to run only locally; a deployed version would be
  fully exposed. That keeps this at Critical for a production-bound app rather than
  lowering it.

### Recommendation
Issue a signed token (e.g. JWT) or server-side session at `/login`. Require it on every
data route through a FastAPI dependency. Derive the user from the token instead of the
`username` parameter, check ownership on ID-based routes, and remove or restrict the
global `GET /assignments`.

---

## F02 - Broken access control (no ownership checks on read, write, or delete)

**Endpoint:** `GET/POST /habits`, `DELETE /habits/{id}`, `GET/POST /water`, `GET /exams`,
`GET /assignments`, `GET /assignments/user/{username}`, `POST/DELETE /assignments/{id}`,
`GET/PUT /exercises`, `PUT/DELETE /exercises/{id}`
**Severity:** Critical
**Status:** Confirmed
**Evidence:** `evidence/F02.md`, `evidence/F02-cross-user-write-habits.txt`,
`evidence/F02-cross-user-write-assignments.txt`, `evidence/F02-cross-user-delete.txt`,
`evidence/F02-ui-leak.txt`, `evidence/F02-exercises-no-auth.txt`,
`evidence/F02-exercise-shared-id.txt`

### Description
This is F01's root cause expressed at the data layer: nothing on the backend checks
that the caller owns the record it is reading, writing, or deleting. Every route takes
a `username` (or a bare record id) straight from the request and trusts it. The database
itself separates users' data correctly by `username` field - the bug is entirely in the
API layer not enforcing who is allowed to supply that field or act on that id.

### Reproduction

**a. Read other users' data.** `GET /habits`, `/water`, `/exams`, and
`/assignments/user/{username}` for both testUser1 and testUser2 returned full data with
no credentials sent.

**b. Global dump.** `GET /assignments` returns every user's assignments in one
unauthenticated response. The database rows are correctly tagged per user; the endpoint
just doesn't filter by caller.

**c. Write into another user's account.** Unauthenticated `POST /habits` with
`{"username":"testUser2", "title":"F02-planted", ...}` returned 201 and the record
appeared in testUser2's habit list. Same result for `POST /assignments`. See
`F02-cross-user-write-habits.txt` / `F02-cross-user-write-assignments.txt`.

**d. Delete another user's data.** A planted habit was deleted via
`DELETE /habits/{id}` with no credentials and confirmed gone on re-read. The assignment
case is worse: `DELETE /assignments/{assignment_id}` carries only a Mongo ObjectId in
the URL - no username, header, cookie, or token of any kind. Any caller who can see or
guess an assignment id (ids are returned in cleartext by the unauthenticated global
dump in b) can delete any user's assignment. See `F02-cross-user-delete.txt`.

**e. UI leak.** Confirmed by code, not a live Burp capture (team decision - see
`F02-ui-leak.txt`). `ABetterTerp/src/pages/Assignments.tsx:159` calls the global
`GET /assignments` with no filtering; `username` from `localStorage` is only used to
gate the "please log in" alert on add/edit, never to scope what's displayed. Combined
with (b), any logged-in user's Assignments page renders every user's assignments.

**f. Exercises.** `GET /exercises?username=X` for both test users succeeded with no
credentials. This route also seeds default exercise documents as a side effect when a
user has none yet - meaning an unauthenticated read can trigger a database write for an
arbitrary username (expanded on separately in F10). See `F02-exercises-no-auth.txt`.

**g. Shared default-ID edit.** Default exercises reuse the same `id` string (e.g.
`"bench"`) across every user's seeded copy. `PUT /exercises/{exercise_id}` matches by
that shared `id` field alone, with no username scoping
(`exercises_collection.find_one_and_update({"id": exercise_id}, ...)`). An
unauthenticated `PUT /exercises/bench` edited testUser2's "Barbell Bench Press" to
"F02-edited" (then reverted). Because the id is shared and guessable (a closed list of
default exercise names), any caller can edit some user's copy of a default exercise
with zero identity check - and whenever more than one user holds a document with that
id, which document gets hit depends on Mongo's internal ordering, not on who is asking.
See `F02-exercise-shared-id.txt`.

### Impact
Full read, write, and delete access to every user's habits, water settings, exams,
exercises, and assignments, with no credentials required anywhere. The frontend compounds
this by rendering the global, unfiltered assignment dump regardless of who is logged in.

### Severity reasoning
- **Likelihood: high.** No tooling beyond curl is needed; ids needed for targeted
  deletes are handed out in cleartext by the app's own unauthenticated endpoints.
- **Impact: high.** Confidentiality and integrity are both broken for all users' data
  across every resource type in the app.
- Same CORS caveat as F01: it blocks browser-origin abuse from other sites (confirmed in
  F12), not direct API calls.

### Recommendation
Same root fix as F01: require an authenticated identity (token/session) on every route,
derive the acting user from it server-side, and filter or check ownership using that
identity instead of trusting a client-supplied `username` or bare id. Specifically:
- Scope `GET /assignments` to the caller, or remove it; the frontend should call the
  per-user endpoint.
- Add an ownership check (`{"id": exercise_id, "username": caller}`) to
  `PUT /exercises/{id}` and `DELETE /exercises/{id}`, and the same pattern for
  `DELETE /habits/{id}` and the `/assignments/{id}` routes.
- Do not let an unauthenticated read cause a write (`ensure_default_exercises` should
  only fire for the authenticated caller's own username; see F10).

---

## F03 - Passwords stored in plaintext

**Endpoint:** `POST /register`, `POST /login`
**Severity:** Critical
**Status:** Confirmed
**Evidence:** `evidence/F03_plaintext_password.png`, `evidence/F00-register.png` (supporting - shows the plaintext password in the register request body itself)

### Description
User passwords are stored and compared in plaintext, with no hashing at any point in
the password lifecycle.

`register_user` writes the raw password straight into the `users` collection:
```python
new_user = {
    "username": data.username,
    "email": data.email,
    "password": data.password  # In production, hash this password!
}
```
(backend/main.py:283)

`login_user` authenticates by querying for an exact plaintext match:
```python
user = await users_collection.find_one({
    "username": data.username,
    "password": data.password  # In production, compare hashed passwords!
})
```
(backend/main.py:299)

### Reproduction
`F00-register.png` (Burp capture of `POST /register` for testUser1) shows the
password traveling in cleartext in the request body. `F03_plaintext_password.png`
(Atlas/mongosh document browse) shows the same password stored in cleartext in the
`users` collection. The comments ("In production, hash this password!" / "In
production, compare hashed passwords!") show this was a known shortcut, not an
oversight - confirming there is no hashing library, salt, or digest anywhere in the
auth path.

### Impact
Anyone with read access to the database (a DB admin, a backup, an export, or an
attacker who reaches the database through any other vulnerability - e.g. if F13's
"not vulnerable" connection-string finding ever regressed, or any future
injection/SSRF) gets every user's password in cleartext immediately, with no
cracking required. Because people commonly reuse passwords, this also threatens
accounts on other, unrelated services.

### Severity reasoning
- **Likelihood: high.** Any database access (legitimate admin, misconfigured backup,
  or a future compromise) yields full credentials instantly - no cracking, no
  rainbow tables, no time cost.
- **Impact: high.** Full account takeover for every user, plus likely spillover to
  other services via password reuse.

### Recommendation
Hash passwords with a slow, salted algorithm (bcrypt, scrypt, or Argon2) before
insert in `register_user`, and verify with the library's `verify`/`checkpw` function
in `login_user` instead of an exact-match query. Never store or log the plaintext
password. Existing plaintext passwords in the database should be treated as
compromised and all users should be required to reset.

---

## F04 - Destructive, unauthenticated admin mass-delete endpoints

**Endpoint:** `DELETE /admin/clear-assignments`, `DELETE /admin/clear-courses`
**Severity:** Critical
**Status:** Confirmed
**Evidence:** `evidence/F04-admin-clear-summary.txt`, `evidence/F04-before-courses.txt`,
`evidence/F04-before-assignments.txt`, `evidence/F04-admin-clear-courses-call.txt`,
`evidence/F04-admin-clear-assignments-call.txt`, `evidence/F04-after-courses.txt`,
`evidence/F04-after-assignments.txt`, `evidence/F04-reseeded-assignments.txt`

### Description
Two admin-style routes delete an entire collection outright, with no
authentication, no confirmation, and no scoping to any particular user
(backend/main.py:732-751):
```python
@app.delete("/admin/clear-assignments", response_description="Clear all assignments")
async def clear_all_assignments():
    result = await assignments_collection.delete_many({})
    return {"message": f"Deleted {result.deleted_count} assignments"}

@app.delete("/admin/clear-courses", response_description="Clear all courses")
async def clear_all_courses():
    result = await courses_collection.delete_many({})
    return {"message": f"Deleted {result.deleted_count} courses"}
```
Neither route checks a credential, an admin role, or any identity at all - the
`/admin/` path prefix is purely cosmetic, not an access boundary.

### Reproduction
1. **Before:** `GET /courses` returned `[]` (already empty at test time - not
   data this test put at risk, but it still confirms the route is reachable with
   no auth). `GET /assignments` returned 5 live documents across both test users
   (testUser1 x2, testUser2 x3).
2. **The calls**, no credentials sent for either:
   ```
   $ curl -X DELETE http://127.0.0.1:8000/admin/clear-courses
   {"message":"Deleted 0 courses"}

   $ curl -X DELETE http://127.0.0.1:8000/admin/clear-assignments
   {"message":"Deleted 5 assignments"}
   ```
3. **After:** `GET /courses` and `GET /assignments` both returned `[]` - all 5
   assignments, belonging to both test users, were gone in a single
   unauthenticated request.
4. **Reseed:** re-created the 5 assignments via `POST /assignments`, matching the
   captured before-state field-for-field (title/course/dueDate/status/priority/
   type/points/username). New Mongo `_id`s were assigned on insert (unavoidable -
   the API cannot be told to reuse a specific `_id`), but the content is
   otherwise identical to the original, confirmed via a final `GET /assignments`.
   `courses` was already empty before and after, so nothing needed reseeding
   there.

### Impact
This is the most severe class of finding in this audit. F01/F02 let an
unauthenticated caller read, edit, or delete individual records; this lets an
unauthenticated caller permanently destroy **every** assignment or course
belonging to **every** user in one request, with no soft-delete, no backup, and
no audit trail. A single curl command (or an automated scanner probing common
`/admin/*` paths) can wipe these collections for the entire application.

### Severity reasoning
- **Likelihood: high.** No credentials or special knowledge needed - just
  knowing or guessing the path, which follows an obvious naming convention
  (`/admin/clear-{collection}`) an attacker could enumerate.
- **Impact: critical.** Full, irreversible (at the API level - no undo, no
  trash) data loss across the entire user base for that resource type, not
  scoped to a single account. This is strictly worse than F02's per-record
  write/delete findings because it requires no targeting at all.

### Recommendation
Remove these routes entirely if they're leftover dev/testing utilities, or if an
admin "clear all" feature is genuinely needed, put it behind real
authentication and an admin-role check, require explicit confirmation (e.g. a
typed confirmation string or a second request), and log who triggered it. At
minimum, do not expose destructive, collection-wide operations under a
predictable unauthenticated path.

---

## F05 - No brute-force protection on login

**Endpoint:** `POST /login`
**Severity:** High
**Status:** Confirmed
**Evidence:** `evidence/F05-bruteforce.txt` (script + full output)

### Description
`POST /login` has no rate limiting, account lockout, CAPTCHA, or increasing delay of
any kind.

### Reproduction
A Python script (saved in the evidence file) sent 120 consecutive wrong-password
attempts for `testUser1`; every single one returned `401 Invalid username or
password` in 4.76 seconds total (~40ms/request), with no change in behavior across
the run. The correct password was then accepted immediately on the very next
request (`200 OK`), with no cooldown or extra verification triggered by the
preceding 120 failures.

### Impact
An attacker can brute-force or credential-stuff any username at full network speed
with a plaintext-password backend (see F03) and no defense in the auth layer
itself. At ~40ms/request observed here (unthrottled, single-threaded, over
localhost), a weak or short password is crackable in minutes; with parallel
requests it would be faster still. This compounds directly with F06 (which lets an
attacker first confirm which usernames exist) and F03 (plaintext passwords mean a
successful guess yields the real password, not a hash to crack further).

### Severity reasoning
- **Likelihood: high.** No tooling beyond a basic script is needed; the test above
  used only Python's standard library.
- **Impact: high.** Successful brute force is a full account takeover, and with
  password reuse, potentially other services too.

### Recommendation
Add account lockout or exponential backoff after a small number of failed attempts
per username, rate-limit `/login` by IP, and consider a CAPTCHA after repeated
failures. Hashing passwords (F03) does not fix this - throttling has to happen at
the login endpoint itself regardless of how passwords are stored.

---

## F06 - User enumeration and missing register input validation

**Endpoint:** `POST /register`, `POST /login`
**Severity:** Medium
**Status:** Confirmed
**Evidence:** `evidence/F06-enumeration-messages.txt`, `evidence/F06-weak-validation.txt`

### Description
`POST /register` has two separate problems.

**Enumeration oracle.** The uniqueness checks each return a distinct, specific
message (backend/main.py:269-276):
```python
existing_user = await users_collection.find_one({"username": data.username})
if existing_user:
    raise HTTPException(status_code=400, detail="Username already exists")

existing_email = await users_collection.find_one({"email": data.email})
if existing_email:
    raise HTTPException(status_code=400, detail="Email already registered")
```

**No input validation.** `RegisterRequest` (backend/main.py:69-72) declares
`username`, `email`, `password` as plain `str` with no constraints - no minimum
length, no whitespace trimming, no email format check (the `min_length=1`
constraint that exists on the unrelated `UserModel` is never applied here).

### Reproduction
- Submitting a known username returns `400 {"detail":"Username already exists"}`;
  submitting a known email returns `400 {"detail":"Email already registered"}` -
  two distinguishable responses, no rate limiting observed.
- Empty strings for all three register fields are accepted (`201 Created`).
- Whitespace-only strings are accepted.
- A malformed, non-"@"-containing string is accepted as an email.
- The resulting empty-username/empty-password account can log in successfully
  (confirmed: `POST /login {"username":"","password":""}` → `200 OK`).

### Impact
- Enumeration lets an attacker build a verified list of real usernames/emails for
  phishing or credential-stuffing, without needing any other access.
- The validation gap lets anyone create junk or colliding-looking accounts
  (including one with no identifying username at all), which can pollute the user
  base, break assumptions elsewhere in the app that expect a non-empty username, or
  be used to probe the app's behavior under edge-case identities.

### Severity reasoning
- **Likelihood: high.** Both issues require only unauthenticated HTTP requests.
- **Impact: medium.** Enumeration and bad data are a real risk but don't by
  themselves grant access to other users' data or credentials (that's F01/F02/F03).

### Recommendation
- Return the same generic message ("Registration failed") for both the username and
  email collision cases, and consider rate-limiting /register by IP.
- Add length/format validation on `RegisterRequest` (e.g. Pydantic `Field(min_length=1)`
  with `.strip()`, plus an `EmailStr` type for `email`), and reject whitespace-only
  input server-side (don't rely on the frontend).
- Separately: there is no API route to delete a user, so three junk accounts created
  during this test (empty username, whitespace username, malformed-email username
  "notanemailuser") remain in the `users` collection - clean up directly in
  Atlas/mongosh.

---

## F07 - Verbose server errors leak internal implementation details

**Endpoint:** `GET /assignments/{id}`, `DELETE /assignments/{id}` (and the same
`except Exception` pattern across the habits/exercises/exams/courses handlers)
**Severity:** Low
**Status:** Confirmed
**Evidence:** `evidence/F07-verbose-errors.txt`

### Description
Route handlers across the backend follow a blanket `except Exception as e: raise
HTTPException(status_code=500, detail=f"Failed to ...: {str(e)}")` pattern, which
forwards the raw Python exception string to the client instead of a generic
message.

### Reproduction
```
$ curl "http://127.0.0.1:8000/assignments/badid"
HTTP/1.1 500 Internal Server Error
{"detail":"Failed to fetch assignment: 'badid' is not a valid ObjectId, it must be a 12-byte input or a 24-character hex string"}
```
Same on `DELETE /assignments/badid`.

### Impact
Reveals backend internals (MongoDB/bson, exact ObjectId validation rules) that help
an attacker fingerprint the stack and refine further requests. The blanket
`except Exception` means any future unexpected error (library internals, future DB
errors) would be echoed back the same way, not just this one case.

### Severity reasoning
- **Likelihood: high** that some exception eventually fires on bad input.
- **Impact: low on its own** - it's an information-disclosure/fingerprinting aid
  rather than a direct path to data or access, which is why it's rated below
  F01-F06.

### Recommendation
Return a generic client-facing message (e.g. "Invalid id" / "Internal server
error") and log `str(e)` / the traceback server-side only. Validate ids before
constructing an `ObjectId` from them and return a `400` for malformed input instead
of letting the constructor throw into the generic handler.

---

## F08 - Password/hash exposure in API responses

**Endpoint:** `POST /register`, `POST /login`
**Severity:** N/A
**Status:** NOT VULNERABLE
**Evidence:** `evidence/F08-password-exposure-check.txt`

### Test
Checked whether any response returns a password or password hash. Reviewed every
code path touching `users_collection` (`register_user`, `login_user` - the only two
call sites) and confirmed both build their own response dict
(`{"message", "user_id", "username"}`) rather than returning the raw user document.
No `/users` listing endpoint exists.

### Result
Not vulnerable, confirmed with a live `/login` call that the response contains no
password field. Flagging alongside F03: the real risk is that passwords are stored
in plaintext in the database (F03), not that the API re-exposes them in responses -
no evidence of the latter was found.

---

## F09 - Missing input validation on exam dates and water intake values

**Endpoint:** `POST /exams`, `POST /water`
**Severity:** Low
**Status:** Confirmed
**Evidence:** `evidence/F09-invalid-exam-date.txt`, `evidence/F09-water-invalid-values.txt`

### Description
Two data fields accept and persist values with no server-side validation.

**Exam date.** `ExamCreate` (backend/main.py:135) declares `date: str` with no
format or range check.

**Water intake.** `WaterIntakeModel` (backend/main.py:95) declares bounds
(`bottleOz: Field(..., ge=1)`, `dailyGoal: Field(..., ge=1)`,
`currentOz: Field(default=0, ge=0)`), but `upsert_water` (the actual `/water`
route) takes `WaterIntakeUpsert` (backend/main.py:103) instead, which has no
bounds at all.

### Reproduction
- testUser1's CMSC216 exam is stored with `"date":"0206-10-23"` - a clear typo
  (year 0206) that the backend happily accepted and still serves back unmodified.
- A test POST with `{"username":"F09testUser","bottleOz":-5,"dailyGoal":999999999,
  "currentOz":-1}` returned `201 Created` and the values persisted on re-read.

### Impact
Low on its own - this is data-integrity noise rather than an access or
confidentiality issue. It can produce nonsensical UI states (negative water
levels, a billion-ounce goal, an exam "due" in the year 206) and indicates the
project has validation models defined (`WaterIntakeModel`) that were never wired
up to the route that needed them - worth checking other routes for the same
model/route mismatch.

### Severity reasoning
- **Likelihood: high** - any client, malicious or just buggy, can trigger this.
- **Impact: low** - no cross-user access or credential exposure, just bad stored
  data that could confuse the UI or downstream logic.

### Recommendation
Use `WaterIntakeUpsert` with the same `Field(..., ge=1)` / `ge=0` bounds as
`WaterIntakeModel` (or just use `WaterIntakeModel` as the input type), and give
`ExamCreate.date` real validation - either a `date`/`datetime` type or a regex/
range check rejecting implausible years.

CLEANUP NOTE: testing created a `water_intake` document for username
"F09testUser" (`_id` 6aca7b457eaa1ecbf8527ef0). There is no `DELETE /water`
route, so remove it directly in Atlas/mongosh if a clean collection is wanted for
the demo.

---

## F10 - State-changing GET (unauthenticated reads trigger database writes)

**Endpoint:** `GET /exercises`
**Severity:** Medium
**Status:** Confirmed
**Evidence:** `evidence/F10-state-changing-get.txt`,
`evidence/F10-ghost1-response.json`, `evidence/F10-ghost2-response.json`,
`evidence/F10-ghost3-response.json`

### Description
`GET /exercises?username={username}` is supposed to be a read. Instead,
`get_exercises` calls `ensure_default_exercises(username)` first (backend/main.py
~466-479), which inserts the full 17-item default exercise library for that
username if none exists yet - a write, performed by a GET, with no credentials
required and no check that the username is real.

### Reproduction
Three unauthenticated calls for usernames that had never been seen before
(`ghost1`, `ghost2`, `ghost3`) each returned exactly 17 documents and created 51
new rows in the `exercises` collection in total.

### Impact
Combined with F02's lack of authentication, this means anyone can inflate the
database arbitrarily just by GETting unique usernames - no registration, no
login, no write-looking request. This is a resource-exhaustion / data-pollution
vector (automated scanning or a crawler hitting this endpoint with random
usernames would silently grow the collection), and it also breaks the normal
expectation that GET requests are safe/idempotent, which can surprise caching
layers, monitoring, or anyone replaying requests from logs.

### Severity reasoning
- **Likelihood: high** - triggered by a single ordinary GET request.
- **Impact: medium** - not a data breach by itself, but unbounded,
  attacker-controlled database growth with no registration or auth required, and
  it compounds the cleanup difficulty described below.

### Severity note: cleanup could not be done safely via the API
Attempting to delete the 51 ghost documents through the app's own
`DELETE /exercises/{id}` route would risk deleting a real user's exercise
instead, because that route matches only on the shared `id` field with no
username scoping (the same defect as F02-g) - multiple usernames (including real
test users) hold documents with the same `id` value (e.g. "bench"), so
`delete_one({"id": "bench"})` could hit any one of them. Cleanup was intentionally
left to be done directly in the database:
`db.exercises.deleteMany({ username: { $in: ["ghost1","ghost2","ghost3"] } })`.

### Recommendation
Do not perform writes inside a GET handler - move the seeding logic to the
`/register` flow (seed once, at account creation, for the authenticated new
user) or to an explicit POST. Separately, fix `DELETE /exercises/{id}` to scope
by the authenticated user (see F02 recommendation) so cleanup like this can be
done safely through the API in the future.

---

## F11 - NoSQL operator injection on /login

**Endpoint:** `POST /login`
**Severity:** N/A
**Status:** NOT VULNERABLE (tested and safe)
**Evidence:** `evidence/F11-nosql-operator-injection.txt`

### Test
`POST /login` with `{"username":{"$ne":""},"password":{"$ne":""}}` - a classic
NoSQL operator-injection payload that, against an untyped/hand-built Mongo query,
would make the comparison always-true and bypass authentication.

### Result
`422 Unprocessable Content`. `LoginRequest` (backend/main.py:65-67) types both
fields as plain `str`, so FastAPI/Pydantic rejects the object payload before it
reaches the database query. Confirmed safe - operator injection does not work
against this endpoint.

---

## F12 - CORS misconfiguration (cross-origin credentialed requests)

**Endpoint:** all routes (CORS middleware, backend/main.py:22-33)
**Severity:** N/A
**Status:** NOT VULNERABLE (tested and safe)
**Evidence:** `evidence/F12-cors-evil-origin.txt`

### Test
Replayed requests with `Origin: https://evil.example` - both a CORS preflight
(`OPTIONS /login`) and a simple `GET /assignments` - to check whether the server
echoes that origin back in `Access-Control-Allow-Origin`.

### Result
Confirmed safe. The preflight was explicitly rejected ("Disallowed CORS origin",
`400`, no ACAO header). The simple GET still returns `200` with data in the body
(expected - CORS does not block the HTTP request itself, only a browser's JS
from reading the response), but no `Access-Control-Allow-Origin` header for
`evil.example` is ever present, so a browser enforcing same-origin policy would
block script access to the response. `allow_origins` (backend/main.py:25-30) is a
fixed localhost-only allowlist, correctly enforced.

Note: this only protects against browser-mediated attacks from other websites. It
does not stop direct API calls (curl, Postman, scripts) from any origin, which is
why F01/F02 remain Critical independently of this control being configured
correctly.

---

## F13 - Secrets in source control / git history

**Endpoint:** N/A - repo-wide check (git history, tracked files)
**Severity:** N/A
**Status:** NOT VULNERABLE
**Evidence:** `evidence/F13-secrets-check.md`

### Test
Checked for a committed `.env` file, a Mongo connection string anywhere in git
history or tracked source, and confirmed `.env` is git-ignored where it lives:
`git ls-files | grep -i "\.env"`, `git log --all --oneline -- .env`,
`git log --all --oneline -S "mongodb+srv"`, a repo-wide grep for
`mongodb+srv|mongodb://`, and `git check-ignore -v backend/.env`.

### Result
Not vulnerable. No `.env` file is or was ever tracked, no connection string
appears anywhere in git history or source, and `backend/.gitignore` correctly
ignores `.env` (confirmed via `git check-ignore`). The only reference to the
database URL in source is `MONGO_URL = os.getenv("MONGO_URL")`
(backend/main.py:18).

### Residual hardening notes (not vulnerabilities)
- There is no root-level `.gitignore`; ignore rules are per-subdirectory
  (`backend/.gitignore`, `ABetterTerp/.gitignore`). `ABetterTerp/.gitignore` does
  not ignore `.env` files - if one is ever added there, it would be tracked.
- This check covers git history and source files only; it cannot prove the
  credential was never exposed elsewhere (chat, logs, screenshots). If there is
  any doubt, rotate the MongoDB credential.

---

## F14 - Outdated dependencies with known CVEs

**Endpoint:** N/A - backend (pip) and frontend (npm) dependency trees
**Severity:** High
**Status:** Confirmed
**Evidence:** `evidence/F14-dependency-audit.txt`

### Test
Ran `pip-audit` against the backend's installed environment (no `requirements.txt`
exists in the repo - versions reflect the dev environment: fastapi 0.115.0,
pydantic 2.13.3, pymongo 4.15.3, python-dotenv 1.0.1, uvicorn 0.32.0) and
`npm audit` against `ABetterTerp/`.

### Result
**Backend (production-relevant):** `pymongo` 4.15.3 has 4 known CVEs (fixed in
4.18.1/4.18.2); `python-dotenv` 1.0.1 has 1 known advisory (fixed in 1.2.2). Both
are runtime dependencies actually used by the app (pymongo drives every database
call).

**Frontend:** `npm audit` reports 26 advisories (1 low, 3 moderate, 22 high).
Checked `ABetterTerp/package.json`: only `react`, `react-dom`, and
`react-router-dom` are production `dependencies`; everything else flagged
(`vite`, `rollup`, `postcss`, `typescript-eslint`, `braces`, `minimatch`, etc.) is
a devDependency / build-tool transitive package, relevant to developer-machine
risk rather than the shipped production bundle. The one production-relevant
advisory is **`react-router`** (pulled in by `react-router-dom`, versions
6.0.0-7.17.0), which includes several high-severity issues: XSS via open
redirects, CSRF in action/server-action request processing, and an "unauthenticated
RCE" advisory via its vendored turbo-stream deserialization - this is the one
that matters for a deployed build.

### Impact
Known, patched CVEs in a runtime database driver (pymongo) and a routing library
actually shipped to users (react-router) mean the app is running code with public,
documented weaknesses that newer versions have already fixed - no novel exploit
development needed, just matching a known CVE to the installed version.

### Severity reasoning
- **Likelihood: medium-high** - exploitability varies per CVE, but these are public,
  indexed vulnerabilities, not hypothetical ones.
- **Impact: high** - react-router's listed advisories include XSS and RCE-class
  issues in a production dependency; pymongo CVEs affect the database driver every
  request passes through.
- The bulk of the 26 npm advisories are devDependency-only and were excluded from
  the high-impact framing above for that reason - they're worth fixing too but
  don't carry the same production risk.

### Recommendation
Backend: pin dependencies in a `requirements.txt` (none currently exists in the
repo) and upgrade `pymongo` to >=4.18.2 and `python-dotenv` to >=1.2.2. Frontend:
run `npm audit fix` and specifically prioritize upgrading `react-router-dom` past
7.17.0 given the XSS/CSRF/RCE-class advisories on the installed range; re-run
`npm audit` after to confirm the devDependency-only findings are addressed too
(lower priority, but still worth clearing before shipping tooling to other
contributors).

---

## F15 - Static analysis (bandit) of backend source

**Endpoint:** N/A - static analysis of `backend/main.py`
**Severity:** N/A
**Status:** NOT VULNERABLE
**Evidence:** `evidence/F15-bandit-static-analysis.txt`

### Test
Ran `bandit` (Python static security analyzer) against the backend source (636
lines scanned, 0 lines skipped).

### Result
Not vulnerable by this tool's checks: 0 issues identified at any severity (Low/
Medium/High) or confidence level. This is a useful cross-check but does not
contradict F01-F03/F05-F07/F09/F10 above - bandit looks for specific unsafe
code patterns (e.g. `eval`, hardcoded secrets, insecure crypto calls, shell
injection) and does not evaluate missing authentication/authorization, which is
this app's primary weakness and is architectural rather than a flagged unsafe
call.
