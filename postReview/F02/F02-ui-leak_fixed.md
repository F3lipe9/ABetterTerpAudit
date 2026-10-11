UI leak - Assignments page (retest, code + API evidence)
Captured 2026-10-10

CODE: ABetterTerp/src/pages/Assignments.tsx still calls the same route as before:
  const response = await fetch(`${API_BASE_URL}/assignments`);
The page does not filter client-side. The change is on the server and in ABetterTerp/src/main.tsx, which wraps window.fetch to add "Authorization: Bearer <token from localStorage>" to requests.

API (what the page receives):
$ curl -i http://127.0.0.1:8000/assignments                                    -> 401 (no token: the page gets nothing)
$ curl -H "Authorization: Bearer <TOKEN_A>" http://127.0.0.1:8000/assignments  -> only testUser1's assignments
$ curl -H "Authorization: Bearer <TOKEN_B>" http://127.0.0.1:8000/assignments  -> only testUser2's assignments

CONCLUSION: logged in as testUser1, the page can only receive testUser1's assignments; testUser2's records are no longer sent. As in the original, this is code + API evidence; no live browser screenshot was taken.

Result: FIXED.
