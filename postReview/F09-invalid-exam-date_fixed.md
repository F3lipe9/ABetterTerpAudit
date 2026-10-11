F09 - Free-string date field accepts invalid/nonsensical dates
Captured 2026-10-10

ExamCreate (backend/main.py ~line 135) declares `date: str` with no format
validation at all (no date type, no regex, no range check).

$ curl "http://127.0.0.1:8000/exams?username=testUser1"
[{"_id":"6aca6ed7c8f60271923c8a94","username":"testUser1","course":"CMSC216","date":"0206-10-23","planned_hours":40,"score":1},
 {"_id":"6aca6ef1c8f60271923c8a95","username":"testUser1","course":"ENGL393","date":"2026-10-15","planned_hours":15}]

testUser1's CMSC216 exam is stored with date "0206-10-23" - year 0206, almost
certainly a typo for 2026 made while testing, but accepted and persisted without
any validation. This is low severity on its own (a free-text date typo, not a
security boundary), but demonstrates the backend performs no server-side input
validation on this field - it will accept, store, and later render any string.

==================== POST-FIX RETEST ====================
Re-run 2026-10-10 against http://127.0.0.1:8000 (authenticated as testUser1; POST /exams now requires a bearer token)

Result: FIXED. ExamCreate.date is validated by validate_iso_date (main.py:225): it must match \d{4}-\d{2}-\d{2},
be a real calendar date, and fall within the allowed year range (2000-2100). Invalid values return 422 and are not stored.

----- Raw output -----

$ GET /exams (existing data)
[{"_id":"6acaccb28b14f499dd5307f6","course":"CMSC131","date":"2026-12-10","planned_hours":5,"username":"testUser1"}]

$ POST /exams date=0206-10-23
HTTP/1.1 422 Unprocessable Content

{"detail":[{"type":"value_error","loc":["body","date"],"msg":"Value error, Date must be YYYY-MM-DD with a year between 2000 and 2100","input":"0206-10-23","ctx":{"error":{}}}]}


$ POST /exams date=abc
HTTP/1.1 422 Unprocessable Content

{"detail":[{"type":"value_error","loc":["body","date"],"msg":"Value error, Date must be a valid YYYY-MM-DD date","input":"abc","ctx":{"error":{}}}]}


$ POST /exams date=2026-13-45
HTTP/1.1 422 Unprocessable Content

{"detail":[{"type":"value_error","loc":["body","date"],"msg":"Value error, Date must be a valid YYYY-MM-DD date","input":"2026-13-45","ctx":{"error":{}}}]}


$ POST /exams date=2026-02-30
HTTP/1.1 422 Unprocessable Content

{"detail":[{"type":"value_error","loc":["body","date"],"msg":"Value error, Date must be a valid YYYY-MM-DD date","input":"2026-02-30","ctx":{"error":{}}}]}


$ POST /exams date=
HTTP/1.1 422 Unprocessable Content

{"detail":[{"type":"value_error","loc":["body","date"],"msg":"Value error, Date must be a valid YYYY-MM-DD date","input":"","ctx":{"error":{}}}]}


$ POST /exams date=99999-01-01
HTTP/1.1 422 Unprocessable Content

{"detail":[{"type":"value_error","loc":["body","date"],"msg":"Value error, Date must be a valid YYYY-MM-DD date","input":"99999-01-01","ctx":{"error":{}}}]}


$ POST /exams date=2026-10-15
HTTP/1.1 201 Created

{"id":"6acad0c28b14f499dd530822","message":"Exam created"}


$ POST /exams date=<script>alert(1)</script>
HTTP/1.1 422 Unprocessable Content

{"detail":[{"type":"value_error","loc":["body","date"],"msg":"Value error, Date must be a valid YYYY-MM-DD date","input":"<script>alert(1)</script>","ctx":{"error":{}}}]}


$ GET /exams (after)
[{"_id":"6acaccb28b14f499dd5307f6","course":"CMSC131","date":"2026-12-10","planned_hours":5,"username":"testUser1"},{"_id":"6acad0c28b14f499dd530822","course":"F09TEST","date":"2026-10-15","planned_hours":5,"username":"testUser1"}]

----- Comparison with original -----
0206-10-23 (original bug) : accepted and stored -> 422 "year between 2000 and 2100"
abc / empty / <script>    : accepted (any string) -> 422 "valid YYYY-MM-DD date"
2026-13-45, 2026-02-30    : accepted -> 422
99999-01-01               : accepted -> 422
2026-10-15 (valid)        : 201 Created, stored (control case)

Note: the old "0206-10-23" record is no longer in testUser1's exams (the DB data has since been reset), so
stored legacy bad data was not re-checked; validation applies to new writes only.
Side effect: the valid control exam (course F09TEST, id 6acad0c28b14f499dd530822) remains in testUser1's exams; there is no DELETE /exams route to remove it.
