F09 - POST /water accepts out-of-range values the sibling model rejects - POST-FIX RETEST
Re-run 2026-10-10 against http://127.0.0.1:8000 (authenticated as the probe account f08probe, so testUser1's water
settings were not touched; POST /water now requires a bearer token and takes the username from it)

Result: FIXED. WaterIntakeUpsert (main.py:193) now enforces the same bounds as WaterIntakeModel, with upper limits added:
    bottleName: 1-50 chars | bottleOz: 1-256 | dailyGoal: 1-1000 | currentOz: 0-10000
Out-of-range and non-integer values return 422 and nothing is stored.

----- Raw output -----

$ POST /water {"bottleName":"F09-test","bottleOz":-5,"dailyGoal":999999999,"currentOz":-1}
HTTP/1.1 422 Unprocessable Content

{"detail":[{"type":"greater_than_equal","loc":["body","bottleOz"],"msg":"Input should be greater than or equal to 1","input":-5,"ctx":{"ge":1}},{"type":"less_than_equal","loc":["body","dailyGoal"],"msg":"Input should be less than or equal to 1000","input":999999999,"ctx":{"le":1000}},{"type":"greater_than_equal","loc":["body","currentOz"],"msg":"Input should be greater than or equal to 0","input":-1,"ctx":{"ge":0}}]}


$ POST /water {"bottleName":"F09-test","bottleOz":-5,"dailyGoal":64,"currentOz":0}
HTTP/1.1 422 Unprocessable Content

{"detail":[{"type":"greater_than_equal","loc":["body","bottleOz"],"msg":"Input should be greater than or equal to 1","input":-5,"ctx":{"ge":1}}]}


$ POST /water {"bottleName":"F09-test","bottleOz":20,"dailyGoal":999999999,"currentOz":0}
HTTP/1.1 422 Unprocessable Content

{"detail":[{"type":"less_than_equal","loc":["body","dailyGoal"],"msg":"Input should be less than or equal to 1000","input":999999999,"ctx":{"le":1000}}]}


$ POST /water {"bottleName":"F09-test","bottleOz":20,"dailyGoal":64,"currentOz":-1}
HTTP/1.1 422 Unprocessable Content

{"detail":[{"type":"greater_than_equal","loc":["body","currentOz"],"msg":"Input should be greater than or equal to 0","input":-1,"ctx":{"ge":0}}]}


$ POST /water {"bottleName":"F09-test","bottleOz":0,"dailyGoal":0,"currentOz":0}
HTTP/1.1 422 Unprocessable Content

{"detail":[{"type":"greater_than_equal","loc":["body","bottleOz"],"msg":"Input should be greater than or equal to 1","input":0,"ctx":{"ge":1}},{"type":"greater_than_equal","loc":["body","dailyGoal"],"msg":"Input should be greater than or equal to 1","input":0,"ctx":{"ge":1}}]}


$ POST /water {"bottleName":"","bottleOz":20,"dailyGoal":64,"currentOz":0}
HTTP/1.1 422 Unprocessable Content

{"detail":[{"type":"string_too_short","loc":["body","bottleName"],"msg":"String should have at least 1 character","input":"","ctx":{"min_length":1}}]}


$ POST /water {"bottleName":"F09-test","bottleOz":"abc","dailyGoal":64}
HTTP/1.1 422 Unprocessable Content

{"detail":[{"type":"int_parsing","loc":["body","bottleOz"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"abc"}]}


$ POST /water {"username":"testUser1","bottleName":"F09-test","bottleOz":20,"dailyGoal":64,"currentOz":0}
HTTP/1.1 201 Created

{"message":"Water intake saved","water":{"username":"f08probe","bottleName":"F09-test","bottleOz":20,"dailyGoal":64,"currentOz":0,"_id":"6acad1017eaa1ecbf852b4a2"}}


$ GET /water (after, f08probe)
{"_id":"6acad1017eaa1ecbf852b4a2","username":"f08probe","bottleName":"F09-test","bottleOz":20,"currentOz":0,"dailyGoal":64}

----- Comparison with original -----
bottleOz -5            : accepted and stored -> 422 (ge 1)
dailyGoal 999999999    : accepted and stored -> 422 (le 1000)
currentOz -1           : accepted and stored -> 422 (ge 0)
bottleOz 0 / dailyGoal 0 : accepted            -> 422 (ge 1)
empty bottleName, "abc" bottleOz : -> 422
Valid values (20 / 64 / 0) : 201 Created, stored (control case)

Bonus: a client-supplied "username":"testUser1" in the body is ignored; the record was saved under the
authenticated user (f08probe), so the old trick of writing under an arbitrary username no longer works.

Cleanup note: the retest left a water document for f08probe (_id 6acad1017eaa1ecbf852b4a2). There is still no
DELETE /water route; the original F09testUser document (_id 6aca7b457eaa1ecbf8527ef0) was not re-checked.
