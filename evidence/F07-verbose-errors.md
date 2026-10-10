F07 - Verbose server errors leak internal implementation details
Captured 2026-10-10

$ curl -i "http://127.0.0.1:8000/assignments/badid"
HTTP/1.1 500 Internal Server Error
{"detail":"Failed to fetch assignment: 'badid' is not a valid ObjectId, it must be a 12-byte input or a 24-character hex string"}

Same pattern on other routes that build an ObjectId from a path/body parameter
without validating it first:

$ curl -i -X PUT "http://127.0.0.1:8000/assignments/badid" -H "Content-Type: application/json" -d '{"title":"x"}'
HTTP/1.1 422 Unprocessable Content   (Pydantic rejects the incomplete body first here,
                                       so the ObjectId bug doesn't trigger on this call)

$ curl -i -X DELETE "http://127.0.0.1:8000/assignments/badid"
HTTP/1.1 500 Internal Server Error
{"detail":"Failed to delete assignment: 'badid' is not a valid ObjectId, it must be a 12-byte input or a 24-character hex string"}

CODE: every route handler wraps its body in `except Exception as e: raise
HTTPException(status_code=500, detail=f"Failed to ...: {str(e)}")` (see
get_assignment, update_assignment, delete_assignment, and the same pattern in
habits/exercises/exams/courses handlers in backend/main.py). This forwards the raw
Python exception string straight to the client.

IMPACT: this specific message reveals the backend uses MongoDB's bson ObjectId
type and exact validation rules (12-byte / 24-hex-char), which helps an attacker
understand the stack and craft further requests (e.g. for NoSQL injection probing
or to distinguish "malformed id" from "not found" when enumerating real ids). More
generally, any future exception (auth errors, unexpected DB errors, library stack
traces) would be echoed back to the client in the same way, since this is a
blanket `except Exception` pattern applied throughout the file, not a one-off bug
on this route.

RECOMMENDATION: return a generic message to the client (e.g. "Invalid assignment
id" / "Internal server error") and log the real exception (str(e), traceback)
server-side only. Validate path/body ids before using them to build an ObjectId,
returning a 400 for a malformed id rather than letting construction throw into the
generic except Exception handler.
