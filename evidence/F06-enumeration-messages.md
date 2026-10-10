User enumeration via distinct register error messages
Captured 2026-10-10

$ curl -i -X POST http://127.0.0.1:8000/register -H "Content-Type: application/json" \
  -d '{"username":"testUser1","email":"newemail@abc.com","password":"whatever"}'

HTTP/1.1 400 Bad Request
{"detail":"Username already exists"}

$ curl -i -X POST http://127.0.0.1:8000/register -H "Content-Type: application/json" \
  -d '{"username":"brandNewUser","email":"test1@abc.com","password":"whatever"}'

HTTP/1.1 400 Bad Request
{"detail":"Email already registered"}

FINDING: the two collision checks in register_user (backend/main.py ~line 269-276)
return distinct, explicit messages:
  - "Username already exists"  -> confirms a specific username is registered
  - "Email already registered" -> confirms a specific email is registered
An attacker can script registration attempts to enumerate valid usernames or emails
in the system (e.g. to target a phishing or credential-stuffing list), one HTTP
request per candidate, with no rate limiting observed.
