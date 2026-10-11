WARNING:  SECURITY login_failed username='victimUser\nFAKE LOG LINE' ip=127.0.0.1 consecutive_failures=1
WARNING:  SECURITY auth_failed reason=missing_token ip=127.0.0.1 path=/habits
WARNING:  SECURITY auth_failed reason=invalid_token ip=127.0.0.1 path=/habits
WARNING:  SECURITY auth_failed reason=invalid_token ip=127.0.0.1 path=/habits
INFO:     SECURITY login_success username='postTest2' ip=127.0.0.1
WARNING:  SECURITY forbidden user='postTest2' ip=127.0.0.1 path=/affirmations
INFO:     127.0.0.1:57184 - "POST /affirmations HTTP/1.1" 403 Forbidden
WARNING:  SECURITY login_failed username='lockme' ip=127.0.0.1 consecutive_failures=1
WARNING:  SECURITY login_failed username='lockme' ip=127.0.0.1 consecutive_failures=2
WARNING:  SECURITY login_failed username='lockme' ip=127.0.0.1 consecutive_failures=3
WARNING:  SECURITY login_failed username='lockme' ip=127.0.0.1 consecutive_failures=4
WARNING:  SECURITY login_failed username='lockme' ip=127.0.0.1 consecutive_failures=5 lockout=30s
WARNING:  SECURITY login_locked username='lockme' ip=127.0.0.1 retry_after=30s
INFO:     127.0.0.1:57213 - "POST /login HTTP/1.1" 429 Too Many Requests
WARNING:  SECURITY login_locked username='lockme' ip=127.0.0.1 retry_after=30s
INFO:     127.0.0.1:57215 - "POST /login HTTP/1.1" 429 Too Many Requests
WARNING:  SECURITY login_locked username='lockme' ip=127.0.0.1 retry_after=30s
INFO:     127.0.0.1:57224 - "POST /login HTTP/1.1" 429 Too Many Requests
WARNING:  SECURITY login_locked username='lockme' ip=127.0.0.1 retry_after=30s
INFO:     127.0.0.1:57226 - "POST /login HTTP/1.1" 429 Too Many Requests
WARNING:  SECURITY login_locked username='lockme' ip=127.0.0.1 retry_after=29s
INFO:     127.0.0.1:57228 - "POST /login HTTP/1.1" 429 Too Many Requests
WARNING:  SECURITY rate_limited ip=127.0.0.1 path=/login limit=10 per 1 minute
WARNING:  SECURITY rate_limited ip=127.0.0.1 path=/login limit=10 per 1 minute
WARNING:  SECURITY rate_limited ip=127.0.0.1 path=/login limit=10 per 1 minute

==================== POST-FIX RETEST ====================
Re-run 2026-10-10 of the post-fix scenario against the current backend/main.py (second uvicorn instance on port 8001).
Scenario: log-injection username, missing token, two bad tokens, successful login, non-admin POST /affirmations (403),
5 bad logins to trigger lockout + 2 locked attempts, then a burst of logins to trip the rate limiter.
(The probe uses f08probe as the non-admin user; the original used postTest2.)

----- Raw server log -----

WARNING:  SECURITY login_failed username='victimUser\nFAKE LOG LINE' ip=127.0.0.1 consecutive_failures=1
INFO:     127.0.0.1:58347 - "POST /login HTTP/1.1" 401 Unauthorized
WARNING:  SECURITY auth_failed reason=missing_token ip=127.0.0.1 path='/habits'
INFO:     127.0.0.1:58348 - "GET /habits HTTP/1.1" 401 Unauthorized
WARNING:  SECURITY auth_failed reason=invalid_token ip=127.0.0.1 path='/habits'
INFO:     127.0.0.1:58349 - "GET /habits HTTP/1.1" 401 Unauthorized
WARNING:  SECURITY auth_failed reason=invalid_token ip=127.0.0.1 path='/habits'
INFO:     127.0.0.1:58350 - "GET /habits HTTP/1.1" 401 Unauthorized
INFO:     SECURITY login_success username='f08probe' ip=127.0.0.1
INFO:     127.0.0.1:58351 - "POST /login HTTP/1.1" 200 OK
WARNING:  SECURITY forbidden user='f08probe' ip=127.0.0.1 path='/affirmations'
INFO:     127.0.0.1:58352 - "POST /affirmations HTTP/1.1" 403 Forbidden
WARNING:  SECURITY login_failed username='lockme' ip=127.0.0.1 consecutive_failures=1
INFO:     127.0.0.1:61292 - "POST /login HTTP/1.1" 401 Unauthorized
WARNING:  SECURITY login_failed username='lockme' ip=127.0.0.1 consecutive_failures=2
INFO:     127.0.0.1:61293 - "POST /login HTTP/1.1" 401 Unauthorized
WARNING:  SECURITY login_failed username='lockme' ip=127.0.0.1 consecutive_failures=3
INFO:     127.0.0.1:61294 - "POST /login HTTP/1.1" 401 Unauthorized
WARNING:  SECURITY login_failed username='lockme' ip=127.0.0.1 consecutive_failures=4
INFO:     127.0.0.1:61295 - "POST /login HTTP/1.1" 401 Unauthorized
WARNING:  SECURITY login_failed username='lockme' ip=127.0.0.1 consecutive_failures=5 lockout=30s
INFO:     127.0.0.1:61296 - "POST /login HTTP/1.1" 401 Unauthorized
WARNING:  SECURITY login_locked username='lockme' ip=127.0.0.1 retry_after=30s
INFO:     127.0.0.1:61297 - "POST /login HTTP/1.1" 429 Too Many Requests
WARNING:  SECURITY login_locked username='lockme' ip=127.0.0.1 retry_after=30s
INFO:     127.0.0.1:61298 - "POST /login HTTP/1.1" 429 Too Many Requests
WARNING:  SECURITY login_failed username='rl1' ip=127.0.0.1 consecutive_failures=1
INFO:     127.0.0.1:61299 - "POST /login HTTP/1.1" 401 Unauthorized
WARNING:  SECURITY login_failed username='rl2' ip=127.0.0.1 consecutive_failures=1
INFO:     127.0.0.1:61300 - "POST /login HTTP/1.1" 401 Unauthorized
WARNING:  SECURITY login_failed username='rl3' ip=127.0.0.1 consecutive_failures=1
INFO:     127.0.0.1:61301 - "POST /login HTTP/1.1" 401 Unauthorized
WARNING:  SECURITY rate_limited ip=127.0.0.1 path='/login' limit=10 per 1 minute
INFO:     127.0.0.1:61307 - "POST /login HTTP/1.1" 429 Too Many Requests
WARNING:  SECURITY rate_limited ip=127.0.0.1 path='/login' limit=10 per 1 minute
INFO:     127.0.0.1:61308 - "POST /login HTTP/1.1" 429 Too Many Requests
WARNING:  SECURITY rate_limited ip=127.0.0.1 path='/login' limit=10 per 1 minute
INFO:     127.0.0.1:61309 - "POST /login HTTP/1.1" 429 Too Many Requests
WARNING:  SECURITY rate_limited ip=127.0.0.1 path='/login' limit=10 per 1 minute
INFO:     127.0.0.1:61310 - "POST /login HTTP/1.1" 429 Too Many Requests
WARNING:  SECURITY rate_limited ip=127.0.0.1 path='/login' limit=10 per 1 minute
INFO:     127.0.0.1:61311 - "POST /login HTTP/1.1" 429 Too Many Requests
WARNING:  SECURITY rate_limited ip=127.0.0.1 path='/login' limit=10 per 1 minute
INFO:     127.0.0.1:61312 - "POST /login HTTP/1.1" 429 Too Many Requests
WARNING:  SECURITY rate_limited ip=127.0.0.1 path='/login' limit=10 per 1 minute
INFO:     127.0.0.1:61313 - "POST /login HTTP/1.1" 429 Too Many Requests
WARNING:  SECURITY rate_limited ip=127.0.0.1 path='/login' limit=10 per 1 minute
INFO:     127.0.0.1:61314 - "POST /login HTTP/1.1" 429 Too Many Requests
WARNING:  SECURITY rate_limited ip=127.0.0.1 path='/login' limit=10 per 1 minute
INFO:     127.0.0.1:61315 - "POST /login HTTP/1.1" 429 Too Many Requests

----- Findings -----
Result: FIXED / behaves as designed. Every event in the original capture is reproduced:
- login_failed with username, ip, consecutive_failures count; lockout=30s appears on the 5th failure.
- login_locked (429) while locked out, with retry_after.
- auth_failed reason=missing_token / invalid_token with ip and path.
- login_success (INFO) and forbidden (403 for non-admin on /affirmations).
- rate_limited with ip, path and limit once the 10/min login limit is hit.
- Log injection is neutralized: the username 'victimUser\nFAKE LOG LINE' was logged on ONE line with the newline
  escaped (repr-quoted), so an attacker cannot forge a separate log entry.
- No passwords, tokens or token fragments are written to the log.
Differences from the original: values are now repr-quoted (path='/habits'). The 7 lockme attempts count toward the per-IP
10/min limit, so only 3 of the 12 burst logins (rl1-rl3) were processed before 429s began.
Also: lockout is tracked per username, independent of the per-IP rate limit.
Side effects: the retest repeatedly logged in as f08probe and attempted logins for 'lockme' and 'rl1'-'rl12'
(non-existent accounts; no records created).
