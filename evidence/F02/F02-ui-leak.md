UI leak - confirmed by code + API evidence (no Burp capture; see decision log)
Captured 2026-10-10

CODE EVIDENCE: ABetterTerp/src/pages/Assignments.tsx

Line 159 - the only call the Assignments page makes to load assignment data:
  async fetchAssignments(): Promise<Assignment[]> {
    const response = await fetch(`${API_BASE_URL}/assignments`);
    ...
  }

Line ~206 - loadData(), run once on mount via useEffect:
  const [assignmentsData, coursesData] = await Promise.all([
    API.fetchAssignments(),
    API.fetchCourses()
  ]);
  const mappedAssignments = assignmentsData.map((a: any) => ({ ...a, id: a._id }));
  setAssignments(mappedAssignments);

`username` is read from localStorage (line ~202, `const u =
localStorage.getItem('username')`) only to decide whether to show the "please
log in" alert on add/edit. It is never passed to fetchAssignments(), and the
response from GET /assignments is rendered unfiltered as-is.

API EVIDENCE: GET /assignments (same call the page makes, no credentials)

$ curl http://127.0.0.1:8000/assignments
[{"title":"Lab05", ..., "username":"testUser1", ...},
 {"title":"Proposal Draft", ..., "username":"testUser1", ...},
 {"title":"Read Phil Article", ..., "username":"testUser2", ...},
 {"title":"Homework", ..., "username":"testUser2", ...}, ...]

CONCLUSION: whichever user is logged in (or no user at all - the page works
unauthenticated), the Assignments page renders the full global dump,
including every other user's assignments. This matches the prediction in
F02.md/checklist item (e): the page calls the global GET /assignments
with no per-user filtering, client or server side.

NOTE: this entry is code + API evidence only. A live screenshot (Burp browser,
logged in as testUser1, showing testUser2's assignments on screen) was not
captured in this pass - see team decision to skip the manual Burp capture for
this item. The code path leaves no room for a different outcome: there is no
filtering logic anywhere between the fetch and the render.
