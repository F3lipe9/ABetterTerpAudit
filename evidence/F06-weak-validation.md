Missing input validation on /register
Captured 2026-10-10

RegisterRequest (backend/main.py ~line 251) declares username/email/password as
plain `str` with no length or format constraint (unlike UserModel, which does have
min_length=1 - that constraint is never applied to the actual input model used by
the /register route).

1) All-empty fields - accepted:
$ curl -i -X POST http://127.0.0.1:8000/register -H "Content-Type: application/json" \
  -d '{"username":"","email":"","password":""}'
HTTP/1.1 201 Created
{"message":"User registered successfully","user_id":"6aca79d5c8f60271923c8ab3"}

2) Whitespace-only fields - accepted:
$ curl -i -X POST http://127.0.0.1:8000/register -H "Content-Type: application/json" \
  -d '{"username":"   ","email":"   ","password":"   "}'
HTTP/1.1 201 Created
{"message":"User registered successfully","user_id":"6aca79d5c8f60271923c8ab4"}

3) Malformed, non-empty email ("notanemail", no @ sign) - accepted, no format check:
$ curl -i -X POST http://127.0.0.1:8000/register -H "Content-Type: application/json" \
  -d '{"username":"notanemailuser","email":"notanemail","password":"x"}'
HTTP/1.1 201 Created
{"message":"User registered successfully","user_id":"6aca79d5c8f60271923c8ab5"}

4) The empty-username/empty-password account from (1) can log in successfully:
$ curl -i -X POST http://127.0.0.1:8000/login -H "Content-Type: application/json" \
  -d '{"username":"","password":""}'
HTTP/1.1 200 OK
{"message":"Login successful for ","user_id":"6aca79d5c8f60271923c8ab3","username":""}

FINDING: there is no server-side validation at all on register inputs - not length,
not whitespace-trimming, not email format. A fully functional account can be created
(and logged into) with an empty username and empty password.

CLEANUP NOTE: this created three junk accounts in the `users` collection (_ids
6aca79d5c8f60271923c8ab3, ...ab4, ...ab5). No /register-adjacent delete-user endpoint
exists in the API, so these cannot be cleaned up via the app itself. Delete them
directly in Atlas / mongosh if you want the users collection clean for the demo.
