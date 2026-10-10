curl "http://127.0.0.1:8000/assignments/user/testUser1"
[
    {"title":"Lab05","course":"CMSC216","dueDate":"2026-10-11","status":"pending","priority":"high","type":"lab","points":"10","username":"testUser1","_id":"6aca6e88c8f60271923c8a92"},
    {"title":"Proposal Draft","course":"ENGL393","dueDate":"2026-10-18","status":"pending","priority":"medium","type":"homework","points":"50","username":"testUser1","_id":"6aca6ebdc8f60271923c8a93"}
    ]

curl "http://127.0.0.1:8000/assignments/user/testUser2"
[
    {"title":"Read Phil Article","course":"PHIL364","dueDate":"2026-10-16","status":"pending","priority":"medium","type":"homework","points":"1","username":"testUser2","_id":"6aca70f0c8f60271923c8a98"},
    {"title":"Homework","course":"STAT400","dueDate":"2026-10-14","status":"pending","priority":"medium","type":"homework","points":"1","username":"testUser2","_id":"6aca7125c8f60271923c8a99"}
    ]


curl "http://127.0.0.1:8000/assignments"   (no credentials, global dump, captured 2026-10-10)
Returns every user's assignments in one response (testUser1 and testUser2 records together).
