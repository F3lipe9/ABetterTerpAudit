# ABetterTerp Security Audit

**Target:** ABetterTerp, a FastAPI + MongoDB backend (`backend/main.py`) with a React/Vite frontend (`ABetterTerp/`).
**Auditor:** the backend's author (a self-audit). **Date:** 2026-10-10. **Branch:** `auditing`.
**Mapping edition:** OWASP Top 10:2025 (category names confirmed against owasp.org/Top10/2025 on 2026-10-10).

---

## 1. Threat model and severity method

- **Threat model for every rating:** the API is reachable by an untrusted network client who has no credentials. Today it runs only on localhost, against a personal MongoDB Atlas cluster holding test data. A deployed copy would be exposed as rated.
- **Severity:** CVSS 3.1 base score and vector, plus a qualitative label. Where I override the mechanical score, the finding says so and why. F07, F16 and F17 are rated by judgment only (no CVSS vector computed).
- **Counting:** findings are grouped by root cause. Several IDs are consequences of the same missing control, so this report quotes root causes rather than raw ID counts.

## 2. Scope and methodology

- **Environment:** the app ran on my machine against a **personal Atlas cluster** (sole access, test data only). It was *not* an isolated local database.
- **Scope:** the backend I wrote. The frontend belongs to teammates and was examined only from the browser side and by reading its source.
- **Test accounts:** `testUser1`, `testUser2`. Retests also used throwaway accounts (`f08probe`, `lockTest`, and similar).
- **Tools actually used:**
  - FastAPI's `/openapi.json` for the endpoint inventory (27 routes)
  - Burp Suite Community (Proxy to capture the app's traffic, Repeater to replay and tamper with requests)
  - `curl` and small Python scripts (brute-force timing, read-only MongoDB document counts)
  - `pip-audit`, `npm audit`, `bandit`, and `git` history searches
- **Method:** manual testing against the unmodified code, saving each request/response to `evidence/`. Fixes were then committed, mostly one commit per finding; three commits each cover two related findings (`2ce4d51`: F06 and F07; `af0b9d8`: F10 and F14; `b25b0e4`: F16 and F17). Each fix was verified by re-running the original test against the fixed code, with results in `postReview/`.
- **Evidence naming:** before-fix evidence is `evidence/F##-*.md`; after-fix evidence is `postReview/F##-*_fixed.md`. The `_fixed` files for F09-exam, F10, F11, F12, F13, F14, F15, F16 and F17 contain the original capture followed by the retest.

## 3. Summary

**Original audit: 9 confirmed findings from 3 root causes, 1 unverified dependency item (F14), and 5 clean checks. Remediation work found 2 more (F16, F17), for a final total of 11 confirmed findings from 4 root causes.** All 11 are fixed and re-tested.

Final severity count of the 11 confirmed findings: **3 Critical** (F01, F02, F04), **1 High** (F05), **4 Medium** (F03, F06, F10, F17), **3 Low** (F07, F09, F16).

| Root cause | Findings |
|---|---|
| RC1: No authentication or authorization enforcement | F01, F02, F04, F10, and F17 (found during remediation) |
| RC2: Weak credential and login handling | F03, F05, F06 |
| RC3: Missing input validation and unsafe error handling | F07, F09 |
| RC4: No security event logging (found during remediation) | F16 |
| Dependency scan, reachability not verified | F14 |
| Tested, no issue found | F08, F11, F12, F13, F15 |

| ID | Title | Severity | Status after fix |
|---|---|---|---|
| F01 | No authentication on API endpoints | Critical, 9.1 | Fixed, re-tested |
| F02 | Broken access control (read, write, delete, UI leak, shared ids) | Critical, 9.1 (same root cause as F01) | Fixed, re-tested |
| F03 | Plaintext passwords | Medium, 5.9 | Fixed, verified by database check |
| F04 | Unauthenticated admin mass-delete | Critical, 9.1 | Fixed, re-tested |
| F05 | No brute-force protection on login | High, 7.4 | Fixed, re-tested |
| F06 | User enumeration and weak register validation | Medium, 5.3 | Fixed, re-tested |
| F07 | Verbose errors leak internals | Low (judgment) | Fixed, re-tested |
| F08 | Password/hash exposure in responses | Not vulnerable | Re-tested, still clean |
| F09 | Missing input validation (exam date, water bounds) | Low (adjusted from 5.3) | Fixed, re-tested |
| F10 | State-changing GET | Medium, 6.5 | Fixed, re-tested |
| F11 | NoSQL operator injection | Not vulnerable | Re-tested, still clean |
| F12 | CORS | Not vulnerable | Re-tested, still clean |
| F13 | Secrets in repo/history | Not vulnerable | Re-tested, still clean |
| F14 | Known-vulnerable dependencies | Unrated (scanner result) | Upgraded; scanners now clean |
| F15 | bandit static analysis | No findings from the tool | 1 Low false positive after the fixes |
| F16 | No security event logging | Low (judgment) | Fixed, re-tested |
| F17 | Shared collections writable by any user; no field length limits | Medium (judgment) | Fixed, re-tested |

Additional hardening that is not tied to a finding is described in section 5.

---

## 4. Findings

Each finding lists: what was wrong, how to reproduce, evidence, impact, the fix, how it was verified, and what the fix does **not** cover.

### F01: No authentication on API endpoints (Critical, CVSS 9.1 `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N`)

- **Description:** `POST /login` checked the password but returned only `{message, user_id, username}`: no token, session or cookie. No route used `Depends`, and every data route trusted a caller-supplied `username` or id.
- **Reproduction (no credentials):** `curl http://127.0.0.1:8000/assignments/user/testUser1` and `.../testUser2` returned each user's data; `curl .../assignments` returned every user's assignments in one response.
- **Evidence:** `evidence/F01-No-Auth.md`, `evidence/F01-login.png`.
- **Impact:** anyone who can reach the API can read, enumerate, modify and delete all users' data with plain HTTP requests.
- **Severity reasoning:** likelihood high (no credentials, guessable routes); impact high on confidentiality and integrity. CORS does not help because it only constrains browsers (F12).
- **Fix:** JWT issued at login (`PyJWT`, HS256 pinned, `exp` and `sub` required, `JWT_SECRET` from the environment), a `get_current_user` dependency on every data route, and the acting user derived from the token. The per-username assignments route was removed. Commit `033c26b`. The frontend change (`ABetterTerp/src/main.tsx` wraps `fetch` to send `Authorization: Bearer`) touches teammates' code.
- **Verification:** `postReview/F01-No-Auth_fixed.md`. Unauthenticated and garbage-token requests return 401; the removed route returns 404; each authenticated user sees only their own assignments; reading another user's assignment by id returns 404.
- **What it does not cover:**
  - The token is stored in the browser's `localStorage`, so any XSS in the frontend could steal it (no HTML sinks were found in `ABetterTerp/src`; see F17).
  - There is no token revocation or refresh. Tokens last until they expire (default 60 minutes), including after a user is deleted.
  - `JWT_SECRET` is optional. If it is unset, the app only prints a warning and generates a random per-process secret, so tokens die on restart and multiple workers would not accept each other's tokens.

### F02: Broken access control (Critical, CVSS 9.1, same root cause as F01)

- **Description:** F01's missing control shown at the data layer: no route checked that the caller owned the record. The database itself separated users correctly; the API did not enforce who may supply the `username` field or act on an id.
- **Reproduction (no credentials):**
  - (a) read other users' habits, water, exams and assignments
  - (b) global dump of every user's assignments from `GET /assignments`
  - (c) planted records in another user's account with `POST /habits` and `POST /assignments`
  - (d) deleted a planted habit via `DELETE /habits/{id}`
  - (e) the Assignments page showed both users' assignments
  - (f) `GET /exercises?username=X` worked unauthenticated
  - (g) `PUT /exercises/bench` edited another user's copy, because default exercise ids are shared across users
- **Evidence:** `evidence/F02/` (`F02.md`, `F02-cross-user-write-habits.md`, `F02-cross-user-write-assignments.md`, `F02-cross-user-delete.md`, `F02-ui-leak.md`, `F02-exercises-no-auth.md`, `F02-exercise-shared-id.md`).
- **Impact:** full read, write and delete across every resource type for every user.
- **Fix:** the username comes from the token and is never accepted from the request; every query filters on it; `GET /assignments` returns only the caller's records; exercise, habit and assignment updates and deletes match on `{id, username}`. Commit `8386d25`.
- **Verification:** `postReview/F02/`. Every sub-item was re-run on 2026-10-10:
  - (a), (b) reads: without credentials every read returns 401, and the removed per-user route returns 404. With testUser1's token, a `?username=testUser2` parameter is ignored and only testUser1's records come back.
  - (c) writes: an unauthenticated `POST /habits` or `POST /assignments` returns 401. With testUser1's token and `"username":"testUser2"` in the body, the record is created under testUser1 (the body field is ignored), and it does not appear in testUser2's list.
  - (d) deletes: deleting testUser2's habit or assignment returns 401 without a token and 404 with testUser1's token; both records are still present when read with testUser2's token. Control: testUser1 deleting their own planted habit returns 204 and their own planted assignment returns 200.
  - (e) UI leak: `Assignments.tsx` still calls `GET /assignments`, but the server now answers 401 without a token and returns only the caller's records with one, so the page can no longer receive another user's assignments (code and API evidence; no browser screenshot).
  - (f) exercises: `GET /exercises?username=...` returns 401 without a token, including for a username that never existed, and no longer creates documents.
  - (g) shared id: an unauthenticated `PUT /exercises/bench` returns 401. With testUser1's token it changed only testUser1's copy; testUser2's `bench` was unchanged (testUser1's was reverted afterward).
  - Planted test records were deleted by their owner afterward. A 404 for another user's id does not reveal whether that record exists.
- **What it does not cover:**
  - The UI leak (e) rests on code and API evidence; I did not capture the Burp request or take a screenshot of the page, either before or after the fix.
  - Deleting a user does not appear to delete their exercises. During the retest, testUser1 and testUser2 each held duplicate default exercises (testUser2 had every default id twice, 35 documents), most likely left over from the earlier, deleted test accounts with the same usernames and then seeded again at re-registration. This is inferred from the counts, not confirmed. Because a user can hold two documents with the same id, `PUT /exercises/bench` updates only one of the caller's own copies. That is a data-cleanup issue, not a cross-user one.

### F03: Plaintext passwords (Medium, CVSS 5.9 `AV:N/AC:H/PR:H/UI:N/S:U/C:H/I:H/A:N`)

- **Description:** `register_user` stored the raw password and `login_user` matched it with an exact-match query.
- **Evidence:** `evidence/F03_plaintext_password.png` (Atlas document browse), `evidence/F00-register.png` (password in the register request body).
- **Impact:** anyone with database read access (admin, backup, export, another flaw) gets every password without cracking; password reuse spreads the damage.
- **Severity reasoning:** the API never exposed the passwords (F08) and the database credential had not leaked (F13), so exploitation needs a separate way to read the database. That is why the vector uses `AC:H` and `PR:H`. It would rise to High if the database were reachable by others.
- **Fix:** bcrypt hashing at registration and `checkpw` at login, run in a threadpool; a dummy hash is checked for unknown users so timing does not reveal them. Commit `152a725`. Because plaintext users cannot be verified against hashes, the test accounts were wiped and re-registered.
- **Verification:** `postReview/F03-password-hash-check_fixed.md`. A read-only database query shows all 8 stored passwords are 60-character bcrypt hashes (`$2b$`, cost 12) and none equal the plaintext. No screenshot exists; the empty placeholder `F03_plaintext_password_fixed.png` should be deleted.
- **What it does not cover:** bcrypt only protects stored passwords. It does nothing for password strength beyond the registration length rule, or for passwords sent over plain HTTP in a deployment without TLS. The 72-byte bcrypt input limit is enforced by rejecting longer passwords.

### F04: Unauthenticated admin mass-delete (Critical, CVSS 9.1 `AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:H/A:H`)

- **Description:** `DELETE /admin/clear-assignments` and `DELETE /admin/clear-courses` ran `delete_many({})` with no authentication; the `/admin/` prefix was cosmetic.
- **Reproduction:** with no credentials, one request deleted all 5 assignments belonging to both test users (re-created afterward from the saved before-state).
- **Evidence:** `evidence/F04/` (before, call, after and reseed captures, plus `F04-admin-clear-summary.md`).
- **Impact:** one unauthenticated request can permanently destroy a whole collection for all users.
- **Fix:** the routes were removed rather than protected, because they were leftover developer utilities. Commit `53b3b18`.
- **Verification:** `postReview/F04/`. The routes return 404 with or without a token, collection-wide `DELETE` returns 405, and no data was deleted.
- **What it does not cover:** anyone with database access can still wipe data. That is outside the API.

### F05: No brute-force protection on login (High, CVSS 7.4 `AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:N`)

- **Description:** `POST /login` had no rate limit, lockout or delay.
- **Reproduction:** a script sent 120 wrong passwords for `testUser1`; all returned 401 in 4.76 s (about 40 ms each), and the correct password was then accepted immediately.
- **Evidence:** `evidence/F05-bruteforce.md`.
- **Impact:** online guessing and credential stuffing at full speed; this compounds with the user enumeration in F06.
- **Fix:** a per-IP limit (`slowapi`, 10 login requests per minute) plus per-username backoff (30 s after 5 consecutive failures, doubling to a 15-minute cap, also applied to unknown usernames). Commit `3ce900a`.
- **Verification:** `postReview/F05-bruteforce_fixed.md`. The same 120-attempt script against a throwaway account ended with 5 evaluated guesses and 115 rejected before any password check (attempts 6 to 10 by the account lockout, 11 onward by the IP limit), in 1.25 s. The correct password worked after a 65-second wait.
- **What it does not cover:** the lockout counter is in memory, so it resets on restart and is per-process. The IP limit is keyed on the client address, so behind a proxy all users could share one IP unless forwarded addresses are configured. Basic rate limiting does not stop a distributed attack, and the lockout lets someone deliberately lock out a known username for up to 15 minutes. `/register` has its own limit (5 per minute), which was not load-tested.

### F06: User enumeration and weak registration validation (Medium, CVSS 5.3 `AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N`)

- **Description:** `POST /register` returned distinct messages ("Username already exists" and "Email already registered"), and `RegisterRequest` accepted empty, whitespace-only and malformed values. An account with an empty username and password could log in.
- **Evidence:** `evidence/F06-enumeration-messages.md`, `evidence/F06-weak-validation.md`.
- **Impact:** a verified list of real usernames and emails, plus junk accounts that break assumptions elsewhere.
- **Fix:** one generic "Registration failed" message for both collisions, with the real reason logged server-side; username 3 to 32 characters from a restricted set, a validated email, and a password of 8 to 72 bytes; unique database indexes on username and email (startup fails if they cannot be created); a registration rate limit; length caps on login fields. Commit `2ce4d51`.
- **Verification:** `postReview/F06-enumeration-messages_fixed.md`, `postReview/F06-weak-validation_fixed.md`. The two collision cases give the same response; empty, whitespace-only, malformed and over-long values return 422; an empty login returns 422. A database query found none of the three junk accounts left.
- **What it does not cover:** timing equality was reasoned from the code, not measured. FastAPI's 422 responses echo back the submitted value, including a password a client sent, which could end up in proxy or client logs (it can be removed with a custom handler).

### F07: Verbose errors leak internals (Low, judgment)

- **Description:** handlers wrapped everything in `except Exception as e: raise HTTPException(500, f"...{str(e)}")`, so `GET /assignments/badid` returned "'badid' is not a valid ObjectId, it must be a 12-byte input or a 24-character hex string".
- **Evidence:** `evidence/F07-verbose-errors.md`.
- **Impact:** reveals the MongoDB/bson stack and its id rules; any future exception would be echoed the same way.
- **Fix:** generic "Internal server error" responses with the real exception logged server-side, `HTTPException` re-raised before the blanket handler, and a `parse_object_id` helper that returns 400 "Invalid id" for malformed ids. Commit `2ce4d51`.
- **Verification:** `postReview/F07-verbose-errors_fixed.md`. Malformed ids now return 400 "Invalid id" (assignments, exams) or a generic 404 (habits, exercises), with no exception text.
- **What it does not cover:** the generic 500 path was confirmed by reading the code; I did not force a database failure to see it live.

### F09: Missing input validation on exam dates and water values (Low, adjusted from mechanical 5.3)

- **Description:** `ExamCreate.date` was an unchecked string (an exam was stored with year 0206). `POST /water` used `WaterIntakeUpsert`, which had none of the bounds that `WaterIntakeModel` declared, so `bottleOz: -5`, `dailyGoal: 999999999` and `currentOz: -1` were stored.
- **Evidence:** `evidence/F09-invalid-exam-date.md`, `evidence/F09-water-invalid-values.md`.
- **Impact:** nonsensical stored data and UI states; no cross-user access. I lowered the score to Low because it crosses no security boundary beyond F01/F02.
- **Fix:** exam and assignment dates must match `YYYY-MM-DD` exactly, be a real calendar date and fall within 2000 to 2100; water fields are bounded (bottle 1 to 256 oz, daily goal 1 to 1000, current 0 to 10000, bottle name 1 to 50 characters); exam updates bound `course`, `planned_hours` and `score`. Commit `01b0513`.
- **Verification:** `postReview/F09-invalid-exam-date_fixed.md`, `postReview/F09-water-invalid-values_fixed.md`. The original bad date, `abc`, an empty string, `2026-13-45`, `2026-02-30`, `99999-01-01` and a script tag all return 422; a valid control date is stored.
- **What it does not cover:** the check applies to new writes only; old bad records are not migrated. Retest data remains in the database (an F09TEST exam and an `f08probe` water document) because no delete route exists for them.

### F10: State-changing GET (Medium, CVSS 6.5 `AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:L/A:L`)

- **Description:** `GET /exercises?username=X` inserted a 17-item default library for any username it had not seen, with no authentication.
- **Reproduction:** three unauthenticated GETs for `ghost1`, `ghost2`, `ghost3` created 51 documents.
- **Evidence:** `evidence/F10/` (`F10-state-changing-get.md` and the three response files).
- **Impact:** an anonymous caller can grow the collection without limit, and a GET is no longer safe or idempotent.
- **Fix:** `GET /exercises` requires a token and only reads. Default exercises are copied in at registration instead. Commit `af0b9d8`.
- **Verification:** `postReview/F10/`. Unauthenticated requests for the ghost names return 401; a read-only count showed the exercises collection unchanged (130 before and after) with no `ghost*` documents.
- **What it does not cover:** every user still gets the same default `id` strings, which is safe only because updates and deletes filter on both id and username.

### F14: Known-vulnerable dependencies (unrated; scanner result)

- **Description:** `pip-audit` found advisories in `pymongo` 4.15.3 (4) and `python-dotenv` 1.0.1 (1, listed twice); `npm audit` reported 26 (1 low, 3 moderate, 22 high), mostly in development tooling. The production-relevant one was `react-router`.
- **Evidence:** `evidence/F14-dependency-audit.md`.
- **What I did not do:** I did not run the per-advisory **reachability check** the audit plan called for (whether the vulnerable code path is used by this app). No severity is claimed, and I make no statement about whether any of these were exploitable here.
- **Fix:** a pinned `backend/requirements.txt` was added (none existed before) and dependencies were upgraded (`pymongo` 4.18.3, `python-dotenv` 1.2.4, `react-router-dom` 7.18.4, `vite` 7.3.7, among others). Commit `af0b9d8`.
- **Verification:** `postReview/F14-dependency-audit_fixed.md`. `pip-audit` on the pinned requirements (including the full dependency tree) and `npm audit` both report no known vulnerabilities as of 2026-10-10.
- **What it does not cover:** a clean scan reflects today's advisory databases and will drift; pins are not hash-locked; I audited the frontend for vulnerabilities only and did not rebuild it or run its tests. A scanner result proves a version match, not exploitability, and a clean result does not prove the code is safe.

### F16: No security event logging (Low, judgment; found during remediation)

- **Description:** the only trace of a failed login, rejected token or rate-limit hit was uvicorn's access line, with no username, reason or event name.
- **Evidence:** `evidence/F16-pre-fix-log-capture.md`.
- **Impact:** brute-force and token probing left no usable audit trail.
- **Fix:** `SECURITY` log events for `login_failed` (with a failure count and lockout), `login_locked`, `auth_failed` (missing, invalid or expired token), `forbidden`, `rate_limited`, `register_failed` (with the collision reason, never the email) and `register_success`, plus `login_success`. User-supplied values and request paths are logged with `repr()` and truncated to 64 characters. Commit `b25b0e4`.
- **Verification:** `evidence/F16-post-fix-log-capture.md` and the retest in `postReview/F16-*_fixed.md`. A username containing a newline appears on one line, paths are quoted, and no passwords or tokens appear in the log.
- **What it does not cover:** the logs go to the process's standard output only, with no retention, shipping or alerting.

### F17: Shared collections writable by any authenticated user; no field length limits (Medium, judgment; found during remediation)

- **Description:** affirmations and courses are shown to every user, but any logged-in user could create entries, and text fields had no length limits (a 1 MB course name was stored).
- **Evidence:** `evidence/F17-shared-content-probe.md`.
- **Impact:** one user could put misleading content in front of everyone or bloat the database. A stored-XSS probe stored the payload verbatim, but the React frontend renders it as inert text.
- **Fix:** writes to `/affirmations` and `/courses` require a username listed in `ADMIN_USERNAMES` (empty means nobody); all user-supplied text has length limits; assignment `status`, `priority`, `type` and exercise `category` are enums. Response models for assignments and courses use plain types, so older stored documents cannot break a list response. Commit `b25b0e4`.
- **Verification:** `postReview/F17-shared-content-probe_fixed.md`. A non-admin gets 403 on both routes, an unauthenticated caller gets 401, and over-long values get 422.
- **What it does not cover:**
  - The XSS result is from reading the source and a server-side render test, not a live browser session, and the rendering code is teammates'.
  - A successful admin write was not re-tested, because there is no delete route to clean up afterward.
  - Admin rights are granted by username, and registration is open. Anyone can register a name listed in `ADMIN_USERNAMES` before the real owner does. The admin account must be registered before the variable is set; keying admin on the user id would remove this risk.

---

## 5. Additional hardening (not tied to a finding)

| Change | Evidence | Status |
|---|---|---|
| Response headers `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`; HSTS only when the request arrived over HTTPS | Visible on every response in `postReview/F07-verbose-errors_fixed.md` and `postReview/F08-*_fixed.md` | Verified |
| `/docs`, `/redoc` and `/openapi.json` disabled unless `ENVIRONMENT=development` (default is production). Before the fixes, `/openapi.json` was public and was used to inventory every route. | `postReview/HARDEN-docs-hidden.md`: 404 with `ENVIRONMENT` unset, 200 with `ENVIRONMENT=development` | Verified |
| `PUT /assignments/{id}` accepts partial updates (`AssignmentUpdate`) and treats an unchanged update as success (`matched_count`) | `postReview/NONSEC-put-assignments.md` (see section 8) | Verified |

## 6. Areas tested with no vulnerability found

| ID | Test | Result |
|---|---|---|
| F08 | Whether any response returns a password or hash | Not vulnerable. Re-tested after the fixes: no change, and the new login token carries no password data. The real risk was plaintext storage (F03). |
| F11 | NoSQL operator injection (`{"$ne": ""}` and similar) on login and other bodies | Not vulnerable. Pydantic's string types reject objects. The protection is incidental to the typed models; it now has authentication scoping as a second layer. |
| F12 | CORS with an `evil.example` origin | Not vulnerable. A fixed localhost allowlist is enforced, including against `Origin: null` and a suffix trick. CORS only constrains browsers and never protected against direct API calls. |
| F13 | Secrets in source and git history | Not vulnerable. No `.env` was ever tracked and no connection string is in history. `ABetterTerp/.gitignore` now ignores `.env`. Still open as hardening: no root `.gitignore`, and a compiled `backend/__pycache__/*.pyc` file is committed. If the credential may have been exposed elsewhere (chat, logs, screenshots), rotate it. |
| F15 | `bandit` static analysis of `backend/main.py` | **No findings from the tool**, which is not a statement that the code is secure. Bandit missed every architectural issue in this report because it looks for unsafe code patterns, not missing authorization. After the fixes it reports one Low false positive (B105 on the string `"bearer"` in the login response). |

## 7. Limitations

- **Self-audit:** I wrote the code and audited it, so I may share its blind spots. The audit was not independent.
- **Environment:** a personal Atlas cluster with test data only; not an isolated database and not production.
- **Frontend:** teammates' code, reviewed from the browser side and by reading source; the UI leak and XSS results were not captured in a live browser session. I did not confirm that the frontend's dropdown values match the new backend enums.
- **Evidence gaps from before the fixes:** a live unauthenticated delete of an assignment (F02-d) and the Burp capture of the UI leak (F02-e) were not taken; mass assignment (changing `username` in a `PUT /assignments/{id}` body), several rarely used routes (`GET/POST /courses`, `GET/POST /affirmations`, `PUT/DELETE /exercises/{id}` unauthenticated) and `/register` rate-limit testing were not run against the original code. After the fixes these routes require a token and ignore any client-supplied `username`.
- **F14:** reachability was not checked; see above.
- **Retests:** most retests were run once, on 2026-10-10, against the fixed code; nothing here proves the absence of other flaws. No automated business-logic testing was done.
- **Retest side effects:** the retests left throwaway test data in the database (the `f08probe` account and its seeded exercises, a water document, an F09TEST exam), which should be removed directly in Atlas.

## 8. Non-security observations (not counted)

1. **`PUT /assignments/{id}` did not persist partial updates.** The original body model required every field, so a partial update got a 422; and when submitted values equaled the stored ones, `modified_count == 0` raised 404, which the old blanket handler re-raised as 500. The current code fixes both (`AssignmentUpdate` with optional fields, and `matched_count`), and the retest in `postReview/NONSEC-put-assignments.md` confirms partial and unchanged updates now succeed. Fixed.
2. **Exam `done` toggle loses state.** The backend stores both `true` and `false`, so the frontend most likely sends `false` both times. Not confirmed from a request capture; not fixed.
3. **`POST /exercises` sends no request** from the UI (frontend wiring); the endpoint itself was tested directly.

## 9. Mapping to OWASP Top 10:2025 and NIST SP 800-53

Category names are taken from owasp.org/Top10/2025 (checked 2026-10-10). The mapping is by category description; I did not check each finding against OWASP's per-category CWE lists, so treat it as best fit. The NIST identifiers are SP 800-53 Rev. 5 controls.

| Findings | OWASP Top 10:2025 | NIST SP 800-53 |
|---|---|---|
| F01 | A07:2025 Authentication Failures; A01:2025 Broken Access Control | IA-2 Identification and Authentication; AC-3 Access Enforcement |
| F02, F04, F17 | A01:2025 Broken Access Control | AC-3 Access Enforcement (F17 also AC-6 Least Privilege) |
| F10 | A01:2025 Broken Access Control; A06:2025 Insecure Design | AC-3 Access Enforcement |
| F03 | A04:2025 Cryptographic Failures | IA-5 Authenticator Management |
| F05 | A07:2025 Authentication Failures | AC-7 Unsuccessful Logon Attempts |
| F06 | A07:2025 Authentication Failures | IA-5 Authenticator Management; SI-10 Information Input Validation |
| F07 | A10:2025 Mishandling of Exceptional Conditions | SI-11 Error Handling |
| F09 | A06:2025 Insecure Design (a bounded model existed but was not used) | SI-10 Information Input Validation |
| F14 | A03:2025 Software Supply Chain Failures | SI-2 Flaw Remediation |
| F16 | A09:2025 Security Logging and Alerting Failures | AU-2 Event Logging |
| Hardening (headers, docs disabled) | A02:2025 Security Misconfiguration | CM-7 Least Functionality |

## 10. Evidence index and final check

Every claim above points to a saved file: before-fix evidence in `evidence/` (plus `evidence/findings.md`, the original working notes), after-fix evidence in `postReview/`.

Checks made for this report:
- A search of `evidence/`, `postReview/` and `AuditPlan.md` for JWT-shaped strings, `mongodb://`/`mongodb+srv://` connection strings and `mongodb.net` hosts found only the search strings themselves quoted in the F13 notes. No connection string, token or real personal data was found.
- No value from `backend/.env` was printed or saved in any evidence file. The F03 database check loaded the connection string from `backend/.env` at runtime without printing it.
- Empty placeholder files in `postReview/` (`findings_fixed.md`, `users_fixed.md`, `F00-register_fixed.png`, `F01-login_fixed.png`, `F03_plaintext_password_fixed.png`) are to be deleted before publishing.
- `evidence/findings.md` refers to some evidence as `.txt` files; on disk they are `.md`.

## 11. Credits

The frontend (`ABetterTerp/`) is teammates' work. This audit cites it (for example `ABetterTerp/src/pages/Assignments.tsx:159` for the UI leak, and the `fetch` wrapper in `src/main.tsx` that was added for authentication). The authentication change touched five of their files (`main.tsx`, `Assignments.tsx`, `Exams.tsx`, `LoginPage.tsx`, `Register.tsx`).