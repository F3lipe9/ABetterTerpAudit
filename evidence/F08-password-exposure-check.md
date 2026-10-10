F08 - Check for password/hash exposure in API responses
Captured 2026-10-10

Reviewed every response-building path that touches users_collection in
backend/main.py:

1. register_user (POST /register): inserts {username, email, password} but the
   response is a hand-built dict: {"message": ..., "user_id": str(result.inserted_id)}
   - no password field returned.

2. login_user (POST /login): queries by {"username":..., "password":...} but the
   response is a hand-built dict: {"message": ..., "user_id": ..., "username": ...}
   - no password field returned.

$ curl -i -X POST http://127.0.0.1:8000/login -H "Content-Type: application/json" \
  -d '{"username":"testUser1","password":"testUser1"}'
HTTP/1.1 200 OK
{"message":"Login successful for testUser1","user_id":"6ac17329310ec3274894717b","username":"testUser1"}

3. No route returns the raw user document; grep confirms `users_collection` is only
   referenced in register_user and login_user, both of which construct their own
   response dict rather than returning `user` or `new_user` directly.

4. No /users (or similar) listing endpoint exists:
$ curl -i "http://127.0.0.1:8000/users"
HTTP/1.1 404 Not Found

RESULT: NOT VULNERABLE. No response observed during this audit includes a
password or password hash. This is worth keeping in mind alongside F03 (passwords
are plaintext in the DB) - the plaintext storage is the real risk; the API layer
itself does not re-expose it in responses.
