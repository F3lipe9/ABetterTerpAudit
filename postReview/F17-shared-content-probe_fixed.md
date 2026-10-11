F17 - Shared collections writable by any authenticated user (pre-fix probe)

Setup: ordinary user postTest2 (not an admin; no admin role existed). Backend before the fix.

1) POST /affirmations  {"text":"<img src=x onerror=alert(document.domain)><script>alert(1)</script>"}
   -> 201 Created. GET /affirmations (as another user) returned it among 11 affirmations, Content-Type: application/json.

2) POST /courses  {"code":"<svg onload=alert(1)>","name":"A"*1,000,000,"professor":"x"}
   -> 201 Created, 1 MB name stored and returned. No length limit on any field.

3) XSS render check (source + render test):
   - grep of ABetterTerp/src for dangerouslySetInnerHTML / innerHTML / insertAdjacentHTML / eval( : no matches.
   - home.tsx:151 renders the value as a JSX child: <p className="affirmation">{todaysAffirmation}</p>
   - react-dom/server renderToString of that element with the payload above produced:
       <p class="affirmation">&lt;img src=x onerror=alert(1)&gt;&lt;script&gt;alert(1)&lt;/script&gt;</p>
   Result: payload is inert in the current frontend. NOT tested in a live browser session.

Cleanup: the probe affirmation and course were deleted from Atlas afterwards.

Post-fix (ADMIN_USERNAMES=postTest1): postTest2 POST /affirmations -> 403, POST /courses -> 403;
admin writes accepted; affirmation >280 chars, course name >200 chars -> 422.

==================== POST-FIX RETEST ====================
Re-run 2026-10-10. Tested on a second uvicorn instance (port 8001, same backend/main.py) started with
ADMIN_USERNAMES=f08probe so an admin path could be exercised. Non-admin user: testUser1. Long inputs are truncated to
300 chars/line in the output below.

Result: FIXED. Shared collections are writable only by users listed in ADMIN_USERNAMES (main.py:48-49, require_admin at
:442), and shared-content fields are length-bounded. Nothing was written to the database by this retest.

----- Raw output -----

== non-admin (testUser1) ==
$ POST /affirmations XSS payload
HTTP/1.1 403 Forbidden
content-type: application/json

{"detail":"Forbidden"}


$ POST /courses XSS code + 1,000,000-char name
HTTP/1.1 403 Forbidden
content-type: application/json

{"detail":"Forbidden"}


$ POST /affirmations no token
HTTP/1.1 401 Unauthorized
www-authenticate: Bearer
content-type: application/json

{"detail":"Not authenticated"}


== admin (f08probe via ADMIN_USERNAMES) - rejection paths only ==
$ POST /affirmations 281 chars
HTTP/1.1 422 Unprocessable Content
content-type: application/json

{"detail":[{"type":"string_too_long","loc":["body","text"],"msg":"String should have at most 280 characters","input":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA


$ POST /courses name 201 chars
HTTP/1.1 422 Unprocessable Content
content-type: application/json

{"detail":[{"type":"string_too_long","loc":["body","name"],"msg":"String should have at most 200 characters","input":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA


$ POST /courses 1 MB name
HTTP/1.1 422 Unprocessable Content
content-type: application/json

{"detail":[{"type":"string_too_long","loc":["body","name"],"msg":"String should have at most 200 characters","input":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA


== GET shared content sanity ==
affirmations containing "<img" or "<script": 0
courses containing "<svg": 0
content-type: application/json

----- Frontend render check (re-run) -----

$ grep -rnE "dangerouslySetInnerHTML|innerHTML|insertAdjacentHTML|eval\(" ABetterTerp/src
[exit 1]

$ react-dom/server renderToString of <p className="affirmation">{payload}</p>
<p class="affirmation">&lt;img src=x onerror=alert(1)&gt;&lt;script&gt;alert(1)&lt;/script&gt;</p>

(home.tsx still renders the value as a JSX child: <p className="affirmation" aria-live="polite">{todaysAffirmation}</p>.)

----- Findings -----
1) POST /affirmations with the XSS payload as an ordinary user: 201 -> 403 Forbidden. Without a token: 401.
2) POST /courses with the <svg onload> code and a 1,000,000-char name as an ordinary user: 201 -> 403 Forbidden.
3) Length limits (admin): affirmation 281 chars -> 422 (max 280); course name 201 chars -> 422 (max 200);
   the 1 MB course name -> 422. A 1 MB body no longer gets stored (the original stored and returned it).
4) GET /affirmations and /courses contain no <img/<script/<svg payloads (the earlier probe records had been deleted).
5) Frontend: still no dangerouslySetInnerHTML/innerHTML/insertAdjacentHTML/eval in ABetterTerp/src, and the server-side
   render escapes the payload. Defense in depth is now in place: only admins can write, and the UI escapes on output.
   Not tested in a live browser session (same caveat as the original).
Not tested: an admin write that succeeds (valid payload), because there is no DELETE route for affirmations/courses and
I did not want to leave records behind; admin acceptance was shown in the original post-fix note (postTest1).
Side effect: none (only rejected requests; second server instance stopped afterward).
