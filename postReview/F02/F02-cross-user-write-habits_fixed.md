Cross-user write into testUser2's account - habits (retest)
Captured 2026-10-10

1) No credentials:
$ curl -i -X POST http://127.0.0.1:8000/habits -H "Content-Type: application/json" \
  -d '{"username":"testUser2","title":"F02-planted","description":""}'
HTTP/1.1 401 Unauthorized
{"detail":"Not authenticated"}

2) Authenticated as testUser1 (<TOKEN_A>), same body naming testUser2:
HTTP/1.1 201 Created
{"message":"Habit created successfully","habit":{"id":"636878e2-4da2-479c-aa49-2d920e4ace81","username":"testUser1","title":"F02-planted","description":"","_id":"6acacdf88b14f499dd5307fc"}}
The "username":"testUser2" in the body was ignored; the habit was stored under the token's user, testUser1.

3) Verification:
GET /habits with <TOKEN_B>: F02-planted absent.
GET /habits with <TOKEN_A>: F02-planted present (cleaned up afterwards with DELETE as testUser1 -> 204).

Result: FIXED. Unauthenticated writes are rejected, and a body username can no longer target another account.
