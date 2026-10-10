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
