F09 - POST /water accepts out-of-range values the sibling model rejects
Captured 2026-10-10

WaterIntakeModel (backend/main.py ~line 95, NOT the model actually used by the
route) declares bounds:
    bottleOz: int = Field(..., ge=1)
    dailyGoal: int = Field(..., ge=1)
    currentOz: int = Field(default=0, ge=0)

But the /water route's actual input model, WaterIntakeUpsert (line ~103), has NO
bounds at all:
    bottleOz: int
    dailyGoal: int
    currentOz: int | None = 0

Test: POST negative bottle size, absurd daily goal, negative current ounces for a
fresh test user:

$ curl -i -X POST http://127.0.0.1:8000/water -H "Content-Type: application/json" \
  -d '{"username":"F09testUser","bottleName":"F09-test","bottleOz":-5,"dailyGoal":999999999,"currentOz":-1}'

HTTP/1.1 201 Created
{"message":"Water intake saved","water":{"username":"F09testUser","bottleName":"F09-test","bottleOz":-5,"dailyGoal":999999999,"currentOz":-1,"_id":"6aca7b457eaa1ecbf8527ef0"}}

Confirmed persisted on re-read:
$ curl "http://127.0.0.1:8000/water?username=F09testUser"
{"_id":"6aca7b457eaa1ecbf8527ef0","username":"F09testUser","bottleName":"F09-test","bottleOz":-5,"currentOz":-1,"dailyGoal":999999999}

FINDING: a negative bottle size, a negative current fill amount, and a
billion-ounce daily goal are all accepted and stored. The constraints that exist
on WaterIntakeModel (ge=1, ge=1, ge=0) are never enforced because the route uses a
different, unconstrained model for its input.

CLEANUP NOTE: this created a water_intake document for username "F09testUser"
(_id 6aca7b457eaa1ecbf8527ef0). There is no DELETE /water route, so it cannot be
removed via the API - delete it directly in Atlas/mongosh if you want the
collection clean.
