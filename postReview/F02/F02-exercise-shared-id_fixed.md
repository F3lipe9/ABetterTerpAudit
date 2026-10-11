Shared default exercise "id" across users - PUT by id (retest)
Captured 2026-10-10

Both testUser1 and testUser2 hold exercises with id "bench".
Before: testUser1 bench = "Barbell Bench Press"; testUser2 bench = "Barbell Bench Press" (two docs, see note).

$ curl -i -X PUT ".../exercises/bench" -H "Content-Type: application/json" -d '{"name":"F02-edited"}'     (no credentials)
HTTP/1.1 401 {"detail":"Not authenticated"}

$ curl -i -X PUT ".../exercises/bench" -H "Authorization: Bearer <TOKEN_A>" -H "Content-Type: application/json" -d '{"name":"F02-edited"}'
HTTP/1.1 200 {"message":"Exercise updated","exercise":{"id":"bench","name":"F02-edited",...,"username":"testUser1"}}

After: testUser1 bench = "F02-edited"; testUser2 bench unchanged ("Barbell Bench Press"). Reverted testUser1's afterwards.
The update filter is now {"id": ..., "username": <token user>}, so a shared id can only hit the caller's own copy.

NOTE (not part of F02): testUser1 and testUser2 each have duplicate default exercises (testUser2: every default id twice, 35 docs). These look like leftover documents from the earlier audit that were never removed when the old test accounts were deleted; re-registering the same username picked them up and registration then seeded 17 more. This was inferred from the counts, not confirmed. It suggests deleting a user does not delete their exercises, and it is unrelated to the access-control fix.

Result: FIXED.
