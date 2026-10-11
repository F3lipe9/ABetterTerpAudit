Input validation on /register (retest)
Captured 2026-10-10

RegisterRequest now enforces: username 3-32 chars, letters/digits/underscore/dot/hyphen only; a valid email (max 254); password 8-72 bytes, not blank. Whitespace around the username is trimmed and emails are lowercased. The runs were spaced to stay under the 5/min register limit.

1) All-empty fields:
$ curl -i -X POST http://127.0.0.1:8000/register -H "Content-Type: application/json" -d '{"username":"","email":"","password":""}'
HTTP/1.1 422 -- username "String should have at least 3 characters"; email "An email address must have an @-sign."; password too short.

2) Whitespace-only fields:
-d '{"username":"   ","email":"   ","password":"   "}'
HTTP/1.1 422 -- same errors (the username is trimmed to empty first).

3) Malformed email ("notanemail"), password "x":
HTTP/1.1 422 -- email: "An email address must have an @-sign."; password: too short.

4) Short password only (username and email valid, password "x"):
HTTP/1.1 422 -- "String should have at least 8 characters"

5) Username with disallowed characters ("<b>x y</b>"):
HTTP/1.1 422 -- "String should match pattern '^[A-Za-z0-9_.-]+$'"

6) 100-character password:
HTTP/1.1 422 -- "Password must be at most 72 bytes" (bcrypt input limit)

7) 100-character username:
HTTP/1.1 422 -- "String should have at most 32 characters"

8) Login with empty credentials (original: an empty-name account could log in):
$ curl -i -X POST http://127.0.0.1:8000/login -H "Content-Type: application/json" -d '{"username":"","password":""}'
HTTP/1.1 422 -- both fields "String should have at least 1 character"

No account was created by any of the requests above. A database query for usernames outside the allowed pattern or emails without a valid shape returned no accounts, so the three junk accounts from the original test (empty, whitespace, "notanemailuser") are no longer in the users collection.

Observation: the 422 bodies echo the submitted value in an "input" field, including the password (e.g. "input":"x"). This is FastAPI's default error format. It only reflects what the client itself sent, but a password could end up in proxy or client logs; it can be removed with a custom RequestValidationError handler if you want.

Result: FIXED.
