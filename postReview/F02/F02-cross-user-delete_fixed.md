Cross-user deletion (retest)
Captured 2026-10-10
Targets: testUser2's habit id and assignment id 6acaccb28b14f499dd5307f9, read with <TOKEN_B>.

Habits
$ curl -i -X DELETE ".../habits/<B habit id>"                              (no credentials)
HTTP/1.1 401 {"detail":"Not authenticated"}
$ curl -i -X DELETE ".../habits/<B habit id>" -H "Authorization: Bearer <TOKEN_A>"
HTTP/1.1 404 {"detail":"Habit not found"}

Assignments
$ curl -i -X DELETE ".../assignments/<B assignment id>"                    (no credentials)
HTTP/1.1 401 {"detail":"Not authenticated"}
$ curl -i -X DELETE ".../assignments/<B assignment id>" -H "Authorization: Bearer <TOKEN_A>"
HTTP/1.1 404 {"detail":"Assignment not found"}

Verification: with <TOKEN_B>, both the habit and the assignment are still present.
Control: testUser1 deleting their own planted habit -> 204; own planted assignment -> 200 {"success":true,...}.

Result: FIXED. Deletes require a token and are scoped to the owner; another user's id returns 404 (does not confirm the record exists).
