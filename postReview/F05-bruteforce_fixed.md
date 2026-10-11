F05 retest - brute force / lockout against POST /login
Captured 2026-10-10, backend restarted on the fixed commit.

Target: a dedicated throwaway account, lockTest (registered for this test), so the real test users were not locked out. Same shape as the original script: 120 consecutive wrong-password attempts, then the correct password. The script waited 61s first so the per-IP rate-limit window was fresh.

=== Output (first 12 attempts, then 60 and 120) ===
attempt   1: HTTP 401 {"detail":"Invalid username or password"}
attempt   2: HTTP 401 {"detail":"Invalid username or password"}
attempt   3: HTTP 401 {"detail":"Invalid username or password"}
attempt   4: HTTP 401 {"detail":"Invalid username or password"}
attempt   5: HTTP 401 {"detail":"Invalid username or password"}
attempt   6: HTTP 429 {"detail":"Too many failed attempts. Try again later."}  Retry-After=30
attempt   7: HTTP 429 {"detail":"Too many failed attempts. Try again later."}  Retry-After=30
attempt   8: HTTP 429 {"detail":"Too many failed attempts. Try again later."}  Retry-After=30
attempt   9: HTTP 429 {"detail":"Too many failed attempts. Try again later."}  Retry-After=30
attempt  10: HTTP 429 {"detail":"Too many failed attempts. Try again later."}  Retry-After=30
attempt  11: HTTP 429 {"error":"Rate limit exceeded: 10 per 1 minute"}
attempt  12: HTTP 429 {"error":"Rate limit exceeded: 10 per 1 minute"}
attempt  60: HTTP 429 {"error":"Rate limit exceeded: 10 per 1 minute"}
attempt 120: HTTP 429 {"error":"Rate limit exceeded: 10 per 1 minute"}

--- 120 wrong-password attempts in 1.25s; status counts: {401: 5, 429: 115}
(Original run: 120 x 401 in 4.76s, nothing throttled.)

Correct password immediately after the burst -> HTTP 429 {"error":"Rate limit exceeded: 10 per 1 minute"} (blocked by the per-IP limiter)
Waited 65s (30s account lockout and the 1-minute window both expire).
Correct password after the wait -> HTTP 200, access token issued.

=== Two separate controls observed ===
1. Per-username backoff: after 5 consecutive failures the account locks for 30s (the lock doubles with each further failure, capped at 15 min). Attempts 6-10 returned 429 with a Retry-After: 30 header. The lock applies to unknown usernames as well, so it does not reveal which accounts exist.
2. Per-IP rate limit: 10 requests per minute on /login. From attempt 11 on, 429 {"error":"Rate limit exceeded: 10 per 1 minute"}.
Only 5 of the 120 guesses were evaluated; the other 115 were rejected before any password check.

=== Server log lines for this run (excerpt) ===
SECURITY login_failed username='lockTest' ip=127.0.0.1 consecutive_failures=1
... (2, 3, 4)
SECURITY login_failed username='lockTest' ip=127.0.0.1 consecutive_failures=5 lockout=30s
SECURITY login_locked username='lockTest' ip=127.0.0.1 retry_after=30s   (repeated)
SECURITY rate_limited ... path='/login' ... (rate-limit rejections)

Result: FIXED. Brute force is throttled by both an account backoff and an IP rate limit, and a legitimate user can log in again once the lock expires.
Limitations: the lockout counter is in memory (per process, reset on restart; multiple workers each keep their own), and the rate limit is keyed on the client IP, so behind a proxy all users could share one IP unless forwarded addresses are configured. The lockout can also be used to temporarily lock out a known username (capped at 15 minutes).
