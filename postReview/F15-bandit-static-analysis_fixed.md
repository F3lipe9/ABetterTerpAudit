[main]	INFO	profile include tests: None
[main]	INFO	profile exclude tests: None
[main]	INFO	cli include tests: None
[main]	INFO	cli exclude tests: None
[main]	INFO	running on Python 3.13.7
Run started:2026-10-10 18:00:15.303595+00:00

Test results:
	No issues identified.

Code scanned:
	Total lines of code: 636
	Total lines skipped (#nosec): 0
	Total potential issues skipped due to specifically being disabled (e.g., #nosec BXXX): 0

Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 0
Files skipped (0):

==================== POST-FIX RETEST ====================
Re-run 2026-10-10 on branch auditing: python -m bandit backend/main.py (bandit 1.9.4, Python 3.13.7)

Result: 1 Low-severity / Medium-confidence finding, a FALSE POSITIVE. No Medium or High findings.

----- Raw output -----

[main]	INFO	profile include tests: None
[main]	INFO	profile exclude tests: None
[main]	INFO	cli include tests: None
[main]	INFO	cli exclude tests: None
[main]	INFO	running on Python 3.13.7
Run started:2026-10-11 00:02:06.851921+00:00

Test results:
>> Issue: [B105:hardcoded_password_string] Possible hardcoded password: 'bearer'
   Severity: Low   Confidence: Medium
   CWE: CWE-259 (https://cwe.mitre.org/data/definitions/259.html)
   More Info: https://bandit.readthedocs.io/en/1.9.4/plugins/b105_hardcoded_password_string.html
   Location: .\backend/main.py:564:8
563	        "access_token": create_access_token(str(user["_id"]), user["username"]),
564	        "token_type": "bearer",
565	    }
566	
567	# HABITS endpoints
568	@app.get("/habits", response_description="Get user habits")
569	async def get_habits(current_user: str = Depends(get_current_user)):
570	    """
571	    Get all habits for a specific user.

--------------------------------------------------

Code scanned:
	Total lines of code: 849
	Total lines skipped (#nosec): 0
	Total potential issues skipped due to specifically being disabled (e.g., #nosec BXXX): 0

Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 1
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 1
		High: 0
Files skipped (0):

----- Analysis -----
B105 (hardcoded_password_string) at backend/main.py:564 flags the literal "bearer" in the login response
`"token_type": "bearer"`. That is the OAuth2 token-type label (RFC 6750), not a credential; nothing secret is hardcoded.
JWT_SECRET and MONGO_URL come from the environment (see F13). Optionally silence it with `# nosec B105`.

Comparison with original: lines of code scanned grew 636 -> 849 (auth, rate limiting, validation, logging were added).
Issues: 0 -> 1 Low, caused only by the new token_type response field. The new code introduced no real findings
(no unsafe deserialization, shell/exec calls, weak hashes, or bare try/except/pass flagged).
Scope: bandit covers Python only, and only backend/main.py was scanned; it does not assess logic flaws such as
authorization, which are covered by the other F-tests.
