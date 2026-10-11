F12 - CORS misconfiguration check (evil Origin header)
Result: NOT VULNERABLE
Captured 2026-10-10

allow_origins in backend/main.py (~line 25-30) is a fixed allowlist:
  ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"]
allow_credentials=True, allow_methods=["*"], allow_headers=["*"]

1) Preflight (OPTIONS) from an evil origin - explicitly rejected:

$ curl -i -X OPTIONS "http://127.0.0.1:8000/login" \
  -H "Origin: https://evil.example" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type"

HTTP/1.1 400 Bad Request
vary: Origin
access-control-allow-methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
access-control-max-age: 600
access-control-allow-credentials: true
access-control-allow-headers: Content-Type
Disallowed CORS origin

No Access-Control-Allow-Origin header is present, and the body literally says
"Disallowed CORS origin" - Starlette's CORSMiddleware explicitly rejects a
preflight from an origin not in the allowlist.

2) Simple GET with an evil Origin header - the request itself is NOT blocked
server-side (this is expected/normal - the server has no way to stop the HTTP
request from happening at all; CORS is enforced by the BROWSER refusing to let
JS on evil.example read the response, which depends entirely on whether an
Access-Control-Allow-Origin header for that origin comes back):

$ curl -i "http://127.0.0.1:8000/assignments" -H "Origin: https://evil.example"

HTTP/1.1 200 OK
access-control-allow-credentials: true
[... full assignment data in body ...]

Critically: NO "Access-Control-Allow-Origin" header is present anywhere in this
response. Since the origin isn't in the allowlist, the middleware does not echo
it back. A real browser running JS on https://evil.example that issued this same
request would receive the data over the wire (same as any curl/server-to-server
call always can - that is not what CORS protects against) but would NOT be
allowed to read the response in JavaScript, because the browser enforces the
same-origin policy using the (missing) Access-Control-Allow-Origin header.

CONCLUSION: tested and safe. The origin allowlist is enforced correctly: evil.example
gets no Access-Control-Allow-Origin header on either a preflighted or simple
request, so a malicious website cannot use a victim's browser session to read
data from this API cross-origin. (Reminder, as noted in F01/F02: this protects
only against browser-mediated attacks from other websites - it does nothing to
stop direct API calls from curl, Postman, or a script, which is why F01/F02 are
rated Critical regardless of this control being correctly configured.)

==================== POST-FIX RETEST ====================
Re-run 2026-10-10 against http://127.0.0.1:8000 (bearer token for probe account f08probe where noted)

Result: STILL NOT VULNERABLE. CORSMiddleware config is unchanged (main.py:78-89): fixed four-origin localhost allowlist,
allow_credentials=True, allow_methods/allow_headers=["*"]. No Access-Control-Allow-Origin header is ever returned
for a non-allowlisted origin.

----- Raw output -----

$ OPTIONS /login  Origin: https://evil.example
HTTP/1.1 400 Bad Request
vary: Origin, Access-Control-Request-Method, Access-Control-Request-Headers, Access-Control-Request-Private-Network
access-control-allow-methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT, QUERY
access-control-max-age: 600
access-control-allow-credentials: true
access-control-allow-headers: Content-Type
content-type: text/plain; charset=utf-8

Disallowed CORS origin


$ OPTIONS /login  Origin: https://evil.example, Request-Headers: Authorization
HTTP/1.1 400 Bad Request
vary: Origin, Access-Control-Request-Method, Access-Control-Request-Headers, Access-Control-Request-Private-Network
access-control-allow-methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT, QUERY
access-control-max-age: 600
access-control-allow-credentials: true
access-control-allow-headers: Authorization
content-type: text/plain; charset=utf-8

Disallowed CORS origin


$ GET /assignments (Bearer token)  Origin: https://evil.example
HTTP/1.1 200 OK
content-type: application/json
access-control-allow-credentials: true
vary: Origin

[]


$ GET /assignments (no token)  Origin: https://evil.example
HTTP/1.1 401 Unauthorized
www-authenticate: Bearer
content-type: application/json
access-control-allow-credentials: true
vary: Origin

{"detail":"Not authenticated"}


$ GET /assignments (no token)  Origin: null
HTTP/1.1 401 Unauthorized
www-authenticate: Bearer
content-type: application/json
access-control-allow-credentials: true
vary: Origin

{"detail":"Not authenticated"}


$ OPTIONS /login  Origin: http://localhost:5173 (allowed origin, control)
HTTP/1.1 200 OK
vary: Origin, Access-Control-Request-Method, Access-Control-Request-Headers, Access-Control-Request-Private-Network
access-control-allow-methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT, QUERY
access-control-max-age: 600
access-control-allow-credentials: true
access-control-allow-origin: http://localhost:5173
access-control-allow-headers: Content-Type,Authorization
content-type: text/plain; charset=utf-8

OK


$ OPTIONS /login  Origin: http://localhost:5173.evil.example (suffix trick)
HTTP/1.1 400 Bad Request
vary: Origin, Access-Control-Request-Method, Access-Control-Request-Headers, Access-Control-Request-Private-Network
access-control-allow-methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT, QUERY
access-control-max-age: 600
access-control-allow-credentials: true
content-type: text/plain; charset=utf-8

Disallowed CORS origin


----- Findings -----
- Preflight from https://evil.example (Content-Type and Authorization requested): 400 "Disallowed CORS origin", no
  Access-Control-Allow-Origin. The browser will therefore refuse to send the Authorization-bearing request.
- Simple GET from evil origin, with token: 200 but no Access-Control-Allow-Origin, so JS on that site cannot read it.
  Without token (original test scenario): now 401 "Not authenticated" instead of full assignment data (F01 fix).
- Origin "null" gets no ACAO header. Suffix trick (http://localhost:5173.evil.example) is rejected: exact matching.
- Control: allowed origin http://localhost:5173 gets 200 and access-control-allow-origin: http://localhost:5173.
- allow_credentials=True remains; it is safe only while the allowlist stays exact. The auth now uses a bearer token
  header, not cookies, so ambient-credential CSRF via the browser is not a factor. Add production origins explicitly
  and never use "*" or a regex with credentials.
- Difference from original capture: allow-methods now also lists QUERY (newer Starlette); no security impact.
