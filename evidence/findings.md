# Audit Findings

Target: ABetterTerp (`backend/main.py` - FastAPI + MongoDB; `ABetterTerp/` - React/Vite frontend). Test accounts: `testUser1` / `testUser2` (see `users.md`). All backend calls were made against `http://127.0.0.1:8000` unless noted. Mapping edition: OWASP Top 10:2025 (category mapping to be added after confirming names on owasp.org).

IDs follow the audit checklist's numbering. F00 is setup evidence (the register request capture used to create the test accounts), not a standalone finding - it is referenced as supporting evidence under F03.

## Threat model and severity method

- **Threat model for all ratings:** the API is assumed reachable by an untrusted network client with no credentials. (Today it runs only on localhost against a personal Atlas cluster holding test data; a deployed version would be exposed as rated.)
- **Scoring:** CVSS 3.1 base score and vector for each confirmed finding, plus a qualitative label. Where I override the mechanical score, the finding says so and why.
- **Counting:** findings are grouped by root cause. Several IDs below are consequences of the same missing control and are not counted as independent problems.

## Results at a glance

**9 confirmed findings from 3 root causes, 1 unverified dependency item, 5 tested-and-clean checks.**

| Root cause | Findings |
|---|---|
| RC1: No authentication or authorization enforcement | F01, F02, F04, F10 |
| RC2: Weak credential and login handling | F03, F05, F06 |
| RC3: Missing input validation and unsafe error handling | F07, F09 |
| Unverified (scanner result, reachability not yet checked) | F14 |
| Tested, no issue found | F08, F11, F12, F13, F15 |

## Summary

| ID | Title | Endpoint(s) | Status | Severity (CVSS 3.1) |
|----|-------|-------------|--------|----------|
| F01 | No authentication or authorization | all tested data routes (see F01) | Confirmed | Critical (9.1) |
| F02 | Broken access control (read/write/delete, UI leak, shared IDs) | `/habits`, `/water`, `/exams`, `/assignments*`, `/exercises*` | Confirmed (two sub-items pending capture) | Critical (9.1), same root cause as F01 |
| F03 | Passwords stored in plaintext | `/register`, `/login` | Confirmed | Medium (5.9) |
| F04 | Destructive, unauthenticated admin mass-delete | `DELETE /admin/clear-assignments`, `DELETE /admin/clear-courses` | Confirmed | Critical (9.1) |
| F05 | No brute-force protection on login | `POST /login` | Confirmed | High (7.4) |
| F06 | User enumeration + missing register validation | `POST /register` | Confirmed | Medium (5.3) |
| F07 | Verbose server errors leak internals | `GET/DELETE /assignments/{id}` (and siblings) | Confirmed | Low (judgment, see F07) |
| F08 | Password/hash exposure in responses | `/register`, `/login` | Not vulnerable | N/A |
| F09 | Missing input validation (exam date, water bounds) | `POST /exams`, `POST /water` | Confirmed | Low (adjusted from 5.3, see F09) |
| F10 | State-changing GET (unauthenticated writes via read) | `GET /exercises` | Confirmed | Medium (6.5) |
| F11 | NoSQL operator injection | `POST /login` | Not vulnerable | N/A |
| F12 | CORS misconfiguration | all routes (CORS middleware) | Not vulnerable | N/A |
| F13 | Secrets in source/history | repo-wide (git history, source) | Not vulnerable | N/A |
| F14 | Known-vulnerable dependencies (exploitability not yet verified) | backend (pip), frontend (npm) | Unverified | Unrated |
| F15 | Static analysis (bandit) of backend | `backend/main.py` | No findings from the tool | N/A |

## Coverage and limitations (read first)

**Live-tested (request and response captured):**
- Reads, no credentials: `GET /habits`, `/water`, `/exams`, `/exercises`, `/assignments/user/{username}`, `/assignments` (global)
- Writes, no credentials: `POST /habits`, `POST /assignments`, `PUT /exercises/bench`
- Delete, no credentials: `DELETE /habits/{id}` (planted record)
- Admin: both `DELETE /admin/clear-*` routes
- Auth: `/register`, `/login` (brute force, enumeration, validation, operator injection)
- Other: CORS preflight, verbose error, water and exam validation, `GET /exercises` side effect

**Reviewed in code or observed in the UI only (no unauthenticated live capture yet):**
- `PUT/DELETE /assignments/{id}`, `GET /assignments/{id}`, `DELETE /exercises/{id}`
- `GET/POST /courses`, `GET /courses/{code}`, `GET/POST /affirmations`
- UI leak (F02-e): seen in the app and traced in source, not captured in Burp

**Not run (listed so nothing is implied):**
- Mass assignment: `PUT /assignments/{id}` with `username` changed to another user
- Stored-XSS probe through `POST /affirmations` (frontend rendering is teammates' code)
- Brute force or rate-limit testing on `/register`

**Environment and scope limits:**
- Self-audit of code I wrote; the frontend is teammates' code and was examined only from the browser side and by reading source.
- App ran locally, but against a personal Atlas cluster (test data only, sole access), not an isolated local database.
- No automated business-logic testing. All findings are from manual testing and tool output saved in `evidence/`.

---

## F01 - No authentication or authorization on API endpoints

**Endpoint:** tested data routes: `/assignments*`, `/habits`, `/water`, `/exercises`, `/exams` (live); `/courses`, `/affirmations` (code only); and `POST /login`
**Severity:** Critical - CVSS 3.1 **9.1** `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N`
**Status:** Confirmed
**Evidence:** `evidence/F01-No-Auth.md`, `evidence/F01-login.png`

### Description
The backend never verifies who is calling. `POST /login` checks the username and password but returns only `{message, user_id, username}`. It issues no token, session or cookie, and no route uses `Depends` or checks a credential. Every data endpoint trusts a caller-supplied `username` or ID, so logging in has no effect on what the server allows.

### Reproduction (no credentials sent)
1. `curl http://127.0.0.1:8000/assignments/user/testUser1` returns testUser1's assignments.
2. `curl http://127.0.0.1:8000/assignments/user/testUser2` returns testUser2's assignments.
3. `curl http://127.0.0.1:8000/assignments` returns the global dump of every user's assignments.
4. Write routes for assignments, habits and exercises have the same gap in code. Live unauthenticated writes and deletes are in F02.

### Impact
Anyone who can reach the API can read all users' data, enumerate usernames and assignment IDs, and modify or delete records. No exploit skill is needed, only HTTP requests. Because the server does no per-user filtering, the app UI also shows both users' assignments to whichever user is logged in (F02-e).

### Severity reasoning
- **Likelihood: high.** No credentials, tooling or prior knowledge needed; endpoints are guessable.
- **Impact: high** for confidentiality and integrity (full read, write and delete). Availability impact is not scored here; F04 covers it.
- Rated under the threat model above. CORS is a browser control and does not stop curl or any non-browser client (confirmed in F12).

### Recommendation
Issue a signed token (e.g. JWT) or server-side session at `/login`. Require it on every data route through a FastAPI dependency. Derive the user from the token instead of the `username` parameter, check ownership on ID-based routes, and remove or restrict the global `GET /assignments`.

---

## F02 - Broken access control (no ownership checks on read, write, or delete)

**Endpoint:** `GET/POST /habits`, `DELETE /habits/{id}`, `GET/POST /water`, `GET /exams`, `GET /assignments`, `GET /assignments/user/{username}`, `POST/DELETE /assignments/{id}`, `GET/PUT /exercises`, `PUT/DELETE /exercises/{id}`
**Severity:** Critical - CVSS 3.1 **9.1** `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N` (same root cause as F01; not counted as an independent problem)
**Status:** Confirmed. Two sub-items are pending a live capture (marked below).
**Evidence:** `evidence/F02.md`, `evidence/F02-cross-user-write-habits.txt`, `evidence/F02-cross-user-write-assignments.txt`, `evidence/F02-cross-user-delete.txt`, `evidence/F02-ui-leak.txt`, `evidence/F02-exercises-no-auth.txt`, `evidence/F02-exercise-shared-id.txt`

### Description
This is F01's root cause expressed at the data layer: nothing on the backend checks that the caller owns the record it is reading, writing, or deleting. Every route takes a `username` (or a bare record id) straight from the request and trusts it. The database separates users' data correctly by `username` field - the bug is entirely in the API layer not enforcing who may supply that field or act on that id.

### Reproduction

**a. Read other users' data.** `GET /habits`, `/water`, `/exams`, and `/assignments/user/{username}` for both testUser1 and testUser2 returned full data with no credentials sent.

**b. Global dump.** `GET /assignments` returns every user's assignments in one unauthenticated response. It ignores any `username` query parameter (a call with `?username=testUser1` still returned all four rows). The database rows are correctly tagged per user; the endpoint does not filter by caller.

**c. Write into another user's account.** Unauthenticated `POST /habits` with `{"username":"testUser2", "title":"F02-planted", ...}` returned 201 and the record appeared in testUser2's habit list. Same result for `POST /assignments`. See `F02-cross-user-write-habits.txt` / `F02-cross-user-write-assignments.txt`.

**d. Delete another user's data.**
- Habits (live): a planted habit was deleted via `DELETE /habits/{id}` with no credentials and confirmed gone on re-read.
- Assignments (UI-observed): `DELETE /assignments/{assignment_id}` carries only a Mongo ObjectId in the URL - no username, header, cookie, or token - and returns `{"success": true, "id": ...}`. IDs are returned in cleartext by the unauthenticated global dump (b).
- **[PENDING capture]** an unauthenticated `curl -X DELETE` of a planted testUser2 assignment, to confirm the assignment case outside the UI.
- See `F02-cross-user-delete.txt`.

**e. UI leak.** Observed in the app: logged in as one test user, the Assignments page shows both users' assignments. Traced in source: `ABetterTerp/src/pages/Assignments.tsx:159` calls the global `GET /assignments` with no filtering; `username` from `localStorage` only gates the "please log in" alert on add/edit, never what is displayed. Combined with (b), any logged-in user's page renders every user's assignments. **[PENDING capture]** the Burp request the page makes and a screenshot of the page; no live capture was taken yet. See `F02-ui-leak.txt`.

**f. Exercises.** `GET /exercises?username=X` for both test users succeeded with no credentials. This route also seeds default exercise documents as a side effect when a user has none (see F10). See `F02-exercises-no-auth.txt`.

**g. Shared default-ID edit.** Default exercises reuse the same `id` string (e.g. `"bench"`) across every user's seeded copy. `PUT /exercises/{exercise_id}` matches on that shared `id` alone, with no username scoping (`exercises_collection.find_one_and_update({"id": exercise_id}, ...)`). An unauthenticated `PUT /exercises/bench` edited testUser2's "Barbell Bench Press" to "F02-edited" (then reverted). Because the id is shared and guessable (a closed list of default exercise names), any caller can edit some user's copy with zero identity check, and which document is hit depends on Mongo's ordering, not on who is asking. See `F02-exercise-shared-id.txt`.

### Impact
Full read, write, and delete access to every user's habits, water settings, exams, exercises, and assignments, with no credentials required. The frontend compounds this by rendering the global, unfiltered assignment dump regardless of who is logged in.

### Severity reasoning
- **Likelihood: high.** No tooling beyond curl; IDs needed for targeted deletes are handed out in cleartext by the app's own unauthenticated endpoints.
- **Impact: high.** Confidentiality and integrity are broken for all users' data across every resource type.
- Same CORS caveat as F01.

### Recommendation
Same root fix as F01: require an authenticated identity on every route, derive the acting user from it server-side, and filter or check ownership using that identity. Specifically:
- Scope `GET /assignments` to the caller, or remove it; the frontend should call the per-user endpoint.
- Add an ownership check (`{"id": exercise_id, "username": caller}`) to `PUT/DELETE /exercises/{id}`, and the same pattern to `DELETE /habits/{id}` and the `/assignments/{id}` routes.
- Do not let an unauthenticated read cause a write (see F10).

---

## F03 - Passwords stored in plaintext

**Endpoint:** `POST /register`, `POST /login`
**Severity:** Medium - CVSS 3.1 **5.9** `AV:N/AC:H/PR:H/UI:N/S:U/C:H/I:H/A:N`
**Status:** Confirmed
**Evidence:** `evidence/F03_plaintext_password.png`, `evidence/F00-register.png` (supporting - shows the plaintext password in the register request body)

### Description
User passwords are stored and compared in plaintext, with no hashing anywhere in the password lifecycle.

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
`F00-register.png` (Burp capture of `POST /register` for testUser1) shows the password traveling in cleartext in the request body. `F03_plaintext_password.png` (Atlas document browse) shows the same password stored in cleartext in the `users` collection. The comments show this was a known shortcut; there is no hashing library, salt, or digest in the auth path.

### Impact
Anyone who obtains read access to the database (an admin, a backup, an export, or an attacker who reaches the database through another flaw) gets every user's password immediately, with no cracking. Because people reuse passwords, this also threatens accounts on other services.

### Severity reasoning
- **The API does not expose the passwords.** F08 confirmed no response returns them, and F13 confirmed the database credential has not leaked, so exploitation needs a separate way to read the database. That precondition is why the vector uses `AC:H` and `PR:H`, and why this scores below the authentication findings.
- **Impact: high once the precondition is met.** Account takeover for every user, with spillover through reuse.
- **Rating would rise to High** if the database were reachable by anyone other than its owner, or if another flaw (e.g. injection) gave read access.

### Recommendation
Hash passwords with a slow, salted algorithm (bcrypt, scrypt, or Argon2) before insert in `register_user`, and verify with the library's `verify`/`checkpw` in `login_user` instead of an exact-match query. Never store or log the plaintext password. Treat existing plaintext passwords as compromised and require resets.

---

## F04 - Destructive, unauthenticated admin mass-delete endpoints

**Endpoint:** `DELETE /admin/clear-assignments`, `DELETE /admin/clear-courses`
**Severity:** Critical - CVSS 3.1 **9.1** `AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:H/A:H`
**Status:** Confirmed
**Evidence:** `evidence/F04-admin-clear-summary.txt`, `evidence/F04-before-courses.txt`, `evidence/F04-before-assignments.txt`, `evidence/F04-admin-clear-courses-call.txt`, `evidence/F04-admin-clear-assignments-call.txt`, `evidence/F04-after-courses.txt`, `evidence/F04-after-assignments.txt`, `evidence/F04-reseeded-assignments.txt`

### Description
Two admin-style routes delete an entire collection outright, with no authentication, no confirmation, and no scoping to any user (backend/main.py:732-751):
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
Neither route checks a credential, an admin role, or any identity - the `/admin/` prefix is cosmetic.

### Reproduction
1. **Before:** `GET /courses` returned `[]` (already empty, so no course data was at risk, but the route is still reachable with no auth). `GET /assignments` returned 5 documents across both test users (testUser1 x2, testUser2 x3).
2. **The calls**, no credentials sent:
   ```
   $ curl -X DELETE http://127.0.0.1:8000/admin/clear-courses
   {"message":"Deleted 0 courses"}

   $ curl -X DELETE http://127.0.0.1:8000/admin/clear-assignments
   {"message":"Deleted 5 assignments"}
   ```
3. **After:** `GET /courses` and `GET /assignments` both returned `[]`. All 5 assignments, belonging to both test users, were gone in one unauthenticated request.
4. **Reseed:** re-created the 5 assignments via `POST /assignments`, matching the before-state field for field. New Mongo `_id`s were assigned (the API cannot reuse a specific `_id`); content is otherwise identical.

### Impact
An unauthenticated caller can permanently destroy every assignment or course belonging to every user in one request, with no soft-delete, backup, or audit trail. A scanner probing common `/admin/*` paths could wipe these collections.

### Severity reasoning
- **Likelihood: high.** No credentials; the path follows an obvious convention (`/admin/clear-{collection}`).
- **Impact: critical.** Irreversible at the API level, across the whole user base for that resource type, with no targeting needed. Scored with `C:N` because the endpoint discloses nothing.

### Recommendation
Remove these routes if they are leftover dev utilities. If an admin "clear all" is genuinely needed, put it behind authentication and an admin-role check, require explicit confirmation, and log who triggered it. Do not expose collection-wide destructive operations under a predictable unauthenticated path.

---

## F05 - No brute-force protection on login

**Endpoint:** `POST /login`
**Severity:** High - CVSS 3.1 **7.4** `AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:N` (`AC:H` because success depends on the target password's strength)
**Status:** Confirmed
**Evidence:** `evidence/F05-bruteforce.txt` (script + full output)

### Description
`POST /login` has no rate limiting, account lockout, CAPTCHA, or increasing delay.

### Reproduction
A Python script (in the evidence file) sent 120 consecutive wrong-password attempts for `testUser1`; every one returned `401 Invalid username or password` in 4.76 seconds total (~40ms/request), with no change in behavior. The correct password was then accepted immediately on the next request (`200 OK`), with no cooldown.

### Impact
An attacker can brute-force or credential-stuff any username at full network speed with no defense in the auth layer. At ~40ms/request (unthrottled, single-threaded, localhost), a weak or short password is crackable in minutes. This compounds with F06 (which confirms which usernames exist).

### Severity reasoning
- **Likelihood: high.** A basic standard-library script was enough.
- **Impact: high.** Successful brute force is a full account takeover, with possible reuse spillover.

### Recommendation
Add account lockout or exponential backoff after a small number of failures per username, rate-limit `/login` by IP, and consider a CAPTCHA after repeated failures. Hashing passwords (F03) does not fix this; throttling must happen at the login endpoint.

---

## F06 - User enumeration and missing register input validation

**Endpoint:** `POST /register`, `POST /login`
**Severity:** Medium - CVSS 3.1 **5.3** `AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N`
**Status:** Confirmed
**Evidence:** `evidence/F06-enumeration-messages.txt`, `evidence/F06-weak-validation.txt`

### Description
`POST /register` has two problems.

**Enumeration oracle.** The uniqueness checks return distinct messages (backend/main.py:269-276):
```python
existing_user = await users_collection.find_one({"username": data.username})
if existing_user:
    raise HTTPException(status_code=400, detail="Username already exists")

existing_email = await users_collection.find_one({"email": data.email})
if existing_email:
    raise HTTPException(status_code=400, detail="Email already registered")
```

**No input validation.** `RegisterRequest` (backend/main.py:69-72) declares `username`, `email`, `password` as plain `str` with no constraints - no minimum length, no whitespace trimming, no email format check (the `min_length=1` on the unrelated `UserModel` is never applied here).

### Reproduction
- A known username returns `400 {"detail":"Username already exists"}`; a known email returns `400 {"detail":"Email already registered"}` - two distinguishable responses, no rate limiting observed.
- Empty strings for all three fields are accepted (`201 Created`). Whitespace-only strings are accepted. A string with no "@" is accepted as an email.
- The resulting empty-username/empty-password account logs in successfully (`POST /login {"username":"","password":""}` returns `200 OK`).

### Impact
- Enumeration lets an attacker build a verified list of real usernames/emails for phishing or credential-stuffing.
- The validation gap lets anyone create junk or colliding accounts (including one with no username), which can break assumptions elsewhere in the app.

### Severity reasoning
- **Likelihood: high.** Both issues need only unauthenticated HTTP requests.
- **Impact: low to medium.** Confidentiality impact is limited to account existence; neither issue by itself grants access to data or credentials (that is F01/F02).

### Recommendation
- Return the same generic message ("Registration failed") for both collision cases, and rate-limit `/register` by IP.
- Add length/format validation on `RegisterRequest` (e.g. `Field(min_length=1)` with trimming, and `EmailStr` for email); reject whitespace-only input server-side.
- Cleanup: no API route deletes a user, so three junk accounts from this test (empty username, whitespace username, malformed-email username "notanemailuser") remain in `users`; remove them directly in Atlas/mongosh.

---

## F07 - Verbose server errors leak internal implementation details

**Endpoint:** `GET /assignments/{id}`, `DELETE /assignments/{id}` (and the same `except Exception` pattern across the habits/exercises/exams/courses handlers)
**Severity:** Low (qualitative judgment; CVSS does not model fingerprint-only leaks well)
**Status:** Confirmed
**Evidence:** `evidence/F07-verbose-errors.txt`

### Description
Handlers follow a blanket `except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to ...: {str(e)}")` pattern, forwarding the raw Python exception string to the client.

### Reproduction
```
$ curl "http://127.0.0.1:8000/assignments/badid"
HTTP/1.1 500 Internal Server Error
{"detail":"Failed to fetch assignment: 'badid' is not a valid ObjectId, it must be a 12-byte input or a 24-character hex string"}
```
Same on `DELETE /assignments/badid`.

### Impact
Reveals backend internals (MongoDB/bson, ObjectId validation rules) that help fingerprint the stack. Any future unexpected error would be echoed the same way.

### Severity reasoning
- **Likelihood: high** that some exception fires on bad input.
- **Impact: low.** The leaked text is library error wording, not user data or credentials; it is a reconnaissance aid. Rated Low by judgment.

### Recommendation
Return a generic client-facing message and log `str(e)`/the traceback server-side only. Validate ids before constructing an `ObjectId` and return `400` for malformed input. Re-raise `HTTPException` before the blanket handler (as `update_exercise` and `update_exam` already do).

---

## F08 - Password/hash exposure in API responses

**Endpoint:** `POST /register`, `POST /login`
**Severity:** N/A
**Status:** NOT VULNERABLE
**Evidence:** `evidence/F08-password-exposure-check.txt`

### Test
Checked whether any response returns a password or password hash. Reviewed every code path touching `users_collection` (`register_user`, `login_user` - the only two call sites) and confirmed both build their own response dict (`{"message", "user_id", "username"}`) rather than returning the raw user document. No `/users` listing endpoint exists.

### Result
Not vulnerable; a live `/login` call confirmed the response contains no password field. The real risk is plaintext storage (F03), not API re-exposure.

---

## F09 - Missing input validation on exam dates and water intake values

**Endpoint:** `POST /exams`, `POST /water`
**Severity:** Low (CVSS mechanically 5.3 for `I:L`; adjusted to Low because this is data-quality only and crosses no security boundary beyond what F01/F02 already cover)
**Status:** Confirmed
**Evidence:** `evidence/F09-invalid-exam-date.txt`, `evidence/F09-water-invalid-values.txt`

### Description
**Exam date.** `ExamCreate` (backend/main.py:135) declares `date: str` with no format or range check.

**Water intake.** `WaterIntakeModel` (backend/main.py:95) declares bounds (`bottleOz: Field(..., ge=1)`, `dailyGoal: Field(..., ge=1)`, `currentOz: Field(default=0, ge=0)`), but `upsert_water` takes `WaterIntakeUpsert` (backend/main.py:103), which has no bounds.

### Reproduction
- testUser1's CMSC216 exam is stored with `"date":"0206-10-23"` (year 0206), accepted and served back unmodified.
- `POST /water` with `{"username":"F09testUser","bottleOz":-5,"dailyGoal":999999999,"currentOz":-1}` returned `201 Created` and the values persisted on re-read.

### Impact
Nonsensical UI states and stored data. It also shows validation models defined (`WaterIntakeModel`) but never wired to the route that needed them; other routes may have the same mismatch.

### Severity reasoning
- **Likelihood: high.** Any client can trigger it.
- **Impact: low.** Bad stored data, no cross-user access or credential exposure.

### Recommendation
Use `WaterIntakeUpsert` with the same `ge` bounds as `WaterIntakeModel` (or use `WaterIntakeModel` as the input type), and give `ExamCreate.date` real validation (a `date` type or range check).

**Cleanup:** testing created a `water_intake` document for "F09testUser" (`_id` 6aca7b457eaa1ecbf8527ef0). There is no `DELETE /water` route; remove it in Atlas/mongosh.

---

## F10 - State-changing GET (unauthenticated reads trigger database writes)

**Endpoint:** `GET /exercises`
**Severity:** Medium - CVSS 3.1 **6.5** `AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:L/A:L`
**Status:** Confirmed
**Evidence:** `evidence/F10-state-changing-get.txt`, `evidence/F10-ghost1-response.json`, `evidence/F10-ghost2-response.json`, `evidence/F10-ghost3-response.json`

### Description
`GET /exercises?username={username}` should be a read. `get_exercises` first calls `ensure_default_exercises(username)` (backend/main.py ~466-479), which inserts the full 17-item default library for that username if none exists - a write performed by a GET, with no credentials and no check that the username is real.

### Reproduction
Three unauthenticated calls for never-seen usernames (`ghost1`, `ghost2`, `ghost3`) each returned exactly 17 documents and created 51 new rows in `exercises`.

### Impact
Anyone can inflate the database by GETting unique usernames - no registration, login, or write-looking request. This is a resource-exhaustion / data-pollution vector, and it breaks the expectation that GET is safe and idempotent, which can surprise caches, monitoring, and log replays.

### Severity reasoning
- **Likelihood: high.** One ordinary GET.
- **Impact: medium.** Unbounded, attacker-controlled growth with no auth, rated `I:L/A:L` because no existing data is read or destroyed.

### Cleanup note
Deleting the 51 ghost documents through `DELETE /exercises/{id}` would risk deleting a real user's exercise, because that route matches only on the shared `id` (F02-g). Clean up directly in the database: `db.exercises.deleteMany({ username: { $in: ["ghost1","ghost2","ghost3"] } })`.

### Recommendation
Do not write inside a GET handler. Seed defaults at `/register` for the new user, or via an explicit POST. Fix `DELETE /exercises/{id}` to scope by the authenticated user (F02).

---

## F11 - NoSQL operator injection on /login

**Endpoint:** `POST /login`
**Severity:** N/A
**Status:** NOT VULNERABLE (tested and safe)
**Evidence:** `evidence/F11-nosql-operator-injection.txt`

### Test
`POST /login` with `{"username":{"$ne":""},"password":{"$ne":""}}`, a classic operator-injection payload that would make an untyped Mongo query always-true.

### Result
`422 Unprocessable Content`. `LoginRequest` (backend/main.py:65-67) types both fields as plain `str`, so Pydantic rejects the object payload before it reaches the query.

---

## F12 - CORS misconfiguration (cross-origin credentialed requests)

**Endpoint:** all routes (CORS middleware, backend/main.py:22-33)
**Severity:** N/A
**Status:** NOT VULNERABLE (tested and safe)
**Evidence:** `evidence/F12-cors-evil-origin.txt`

### Test
Replayed requests with `Origin: https://evil.example`: a preflight (`OPTIONS /login`) and a simple `GET /assignments`, checking whether the origin is echoed in `Access-Control-Allow-Origin`.

### Result
The preflight was rejected ("Disallowed CORS origin", `400`, no ACAO header). The simple GET still returns `200` with data in the body (expected - CORS limits only a browser's JS from reading the response), but no `Access-Control-Allow-Origin` for `evil.example` is present. `allow_origins` (backend/main.py:25-30) is a fixed localhost-only allowlist, correctly enforced.

This protects only against browser-mediated attacks from other sites. It does not stop direct API calls, which is why F01/F02 stay Critical independently.

---

## F13 - Secrets in source control / git history

**Endpoint:** N/A - repo-wide check
**Severity:** N/A
**Status:** NOT VULNERABLE
**Evidence:** `evidence/F13-secrets-check.md`

### Test
Checked for a committed `.env`, a Mongo connection string anywhere in git history or tracked source, and that `.env` is git-ignored: `git ls-files | grep -i "\.env"`, `git log --all --oneline -- .env`, `git log --all --oneline -S "mongodb+srv"`, a repo-wide grep for `mongodb+srv|mongodb://`, and `git check-ignore -v backend/.env`.

### Result
No `.env` is or was ever tracked, no connection string appears in history or source, and `backend/.gitignore` ignores `.env`. The only reference to the database URL in source is `MONGO_URL = os.getenv("MONGO_URL")` (backend/main.py:18).

### Hardening items (tracked for the fix phase, not vulnerabilities)
- No root-level `.gitignore`; rules are per-subdirectory. `ABetterTerp/.gitignore` does not ignore `.env` files. Add the rule now.
- This check covers git history and source only; it cannot prove the credential was never exposed elsewhere (chat, logs, screenshots). Before publishing, scan every file in `evidence/` for the connection string or credentials.

---

## F14 - Known-vulnerable dependencies (exploitability not yet verified)

**Endpoint:** N/A - backend (pip) and frontend (npm) dependency trees
**Severity:** Unrated. A scanner match is not a confirmed vulnerability; severity will be assigned after the reachability check below.
**Status:** Unverified
**Evidence:** `evidence/F14-dependency-audit.txt`

### Test
Ran `pip-audit` against the backend's installed environment (no `requirements.txt` exists; versions reflect the dev environment: fastapi 0.115.0, pydantic 2.13.3, pymongo 4.15.3, python-dotenv 1.0.1, uvicorn 0.32.0) and `npm audit` against `ABetterTerp/`.

### Scanner output
**Backend:** `pymongo` 4.15.3 has 4 listed CVEs (fixed in 4.18.1/4.18.2); `python-dotenv` 1.0.1 has 1 listed advisory (fixed in 1.2.2).

**Frontend:** `npm audit` reports 26 advisories (1 low, 3 moderate, 22 high). Per `ABetterTerp/package.json`, only `react`, `react-dom`, and `react-router-dom` are production dependencies. Everything else flagged (`vite`, `rollup`, `postcss`, `typescript-eslint`, `braces`, `minimatch`, etc.) is a devDependency or build-tool transitive package, relevant to developer-machine risk rather than the shipped bundle. The production-relevant entry is **`react-router`** (via `react-router-dom`, affected range up to 7.17.0), whose listed advisories include XSS via open redirects and CSRF/RCE-class issues in server-side or framework modes.

### Reachability check (to do before rating)
1. Open each `react-router` advisory (GHSA link) and record the affected component. Server-side and framework-mode features may not apply to a client-only Vite SPA; state whether this app uses the affected API.
2. Open each of the four `pymongo` CVEs and record which code path or feature is affected, and whether `main.py` calls it (it uses `AsyncMongoClient`, `find`, `insert_one`, `update_one`, `delete_one/many`, `find_one_and_update`).
3. Same for the `python-dotenv` advisory (used once: `load_dotenv()`).
4. Rate each advisory as **reachable / not reachable / unknown**, then assign a severity to the reachable ones only. Until then, nothing here is claimed as exploitable.

### Recommendation
Backend: add a pinned `requirements.txt` (none exists), upgrade `pymongo` to >=4.18.2 and `python-dotenv` to >=1.2.2. Frontend: upgrade `react-router-dom` past 7.17.0, run `npm audit fix`, and re-run `npm audit` to confirm the devDependency findings are cleared.

---

## F15 - Static analysis (bandit) of backend source

**Endpoint:** N/A - static analysis of `backend/main.py`
**Severity:** N/A
**Status:** NO FINDINGS FROM THE TOOL (not a statement that the code is secure)
**Evidence:** `evidence/F15-bandit-static-analysis.txt`

### Test
Ran `bandit` against the backend source (636 lines scanned, 0 skipped).

### Result
0 issues at any severity or confidence level. This does not contradict the findings above: bandit looks for specific unsafe code patterns (`eval`, hardcoded secrets, weak crypto, shell injection) and does not evaluate missing authentication or authorization, which is this app's architectural weakness. Bandit missed nine confirmed issues in this report, which is itself worth noting in the methodology section.

---

## Non-security observations (not counted)

1. **`PUT /assignments/{id}` does not persist updates.** (a) The body model is `AssignmentCreate`, so every field is required and a partial `{"status": ...}` gets a 422 before the handler runs; (b) when submitted values equal stored ones, `modified_count == 0` raises 404, which the blanket `except Exception` re-raises as 500. `get_assignment` and `delete_assignment` share the flaw. **[PENDING]** confirm with the status code and body from Burp.
2. **Exam `done` toggle loses state.** The backend saves both `true` and `false` correctly (`v is not None`), so the frontend most likely sends `false` both times. **[PENDING]** confirm from the request body in Burp.
3. **`POST /exercises` sends no request** from the UI (frontend wiring); the endpoint itself was tested directly.
