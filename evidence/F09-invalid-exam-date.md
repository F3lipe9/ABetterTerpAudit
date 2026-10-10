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
