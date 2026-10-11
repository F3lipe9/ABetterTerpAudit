User enumeration via distinct register error messages (retest)
Captured 2026-10-10

$ curl -i -X POST http://127.0.0.1:8000/register -H "Content-Type: application/json" \
  -d '{"username":"testUser1","email":"newemail@abc.com","password":"whatever12"}'

HTTP/1.1 400 Bad Request
{"detail":"Registration failed"}

$ curl -i -X POST http://127.0.0.1:8000/register -H "Content-Type: application/json" \
  -d '{"username":"brandNewUser","email":"testuser1@abc.com","password":"whatever12"}'

HTTP/1.1 400 Bad Request
{"detail":"Registration failed"}

Both collisions (username taken, email taken) now return the identical status and body. The handler also computes the bcrypt hash before the lookup, so a collision does not answer measurably faster than a success.

The reason is recorded only in the server log (the response stays generic):
SECURITY register_failed reason=username_taken username='testUser1' ip=127.0.0.1
SECURITY register_failed reason=email_taken username='brandNewUser' ip=127.0.0.1

Rate limit: /register is limited to 5 requests per minute per IP, so scripted enumeration is slowed as well (the original finding noted no rate limiting).

Result: FIXED for the message difference. Limitations: the timing equality was reasoned from the code, not measured here; and /login still returns "Invalid username or password" for both unknown users and wrong passwords (unchanged, and not part of this finding).
