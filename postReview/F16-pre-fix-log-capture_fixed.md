INFO:     127.0.0.1:58029 - "POST /login HTTP/1.1" 401 Unauthorized
INFO:     127.0.0.1:58031 - "GET /habits HTTP/1.1" 401 Unauthorized
INFO:     127.0.0.1:58033 - "POST /login HTTP/1.1" 200 OK
INFO:     127.0.0.1:58035 - "POST /login HTTP/1.1" 200 OK
INFO:     127.0.0.1:58037 - "POST /login HTTP/1.1" 200 OK
INFO:     127.0.0.1:58046 - "POST /login HTTP/1.1" 200 OK
INFO:     127.0.0.1:58048 - "POST /login HTTP/1.1" 200 OK
INFO:     127.0.0.1:58055 - "POST /login HTTP/1.1" 200 OK
INFO:     127.0.0.1:58057 - "POST /login HTTP/1.1" 200 OK
INFO:     127.0.0.1:58066 - "POST /login HTTP/1.1" 200 OK
INFO:     127.0.0.1:58068 - "POST /login HTTP/1.1" 200 OK
INFO:     127.0.0.1:58070 - "POST /login HTTP/1.1" 429 Too Many Requests
INFO:     127.0.0.1:58077 - "POST /login HTTP/1.1" 429 Too Many Requests

==================== POST-FIX RETEST ====================
Re-run 2026-10-10 of the SAME scenario as the original capture (failed login, unauthenticated GET /habits, 10 successful
logins, then 429s), against the current code. Server log captured from a second uvicorn instance on port 8001 (same
backend/main.py), as probe account f08probe.

Original gap: the log held only uvicorn access lines (no username, no reason, no marker; 401s indistinguishable).
Now (note the added SECURITY events):

WARNING:  SECURITY login_failed username='nobody' ip=127.0.0.1 consecutive_failures=1
INFO:     127.0.0.1:52567 - "POST /login HTTP/1.1" 401 Unauthorized
WARNING:  SECURITY auth_failed reason=missing_token ip=127.0.0.1 path='/habits'
INFO:     127.0.0.1:52568 - "GET /habits HTTP/1.1" 401 Unauthorized
INFO:     SECURITY login_success username='f08probe' ip=127.0.0.1
INFO:     127.0.0.1:55710 - "POST /login HTTP/1.1" 200 OK
INFO:     SECURITY login_success username='f08probe' ip=127.0.0.1
INFO:     127.0.0.1:55711 - "POST /login HTTP/1.1" 200 OK
INFO:     SECURITY login_success username='f08probe' ip=127.0.0.1
INFO:     127.0.0.1:55712 - "POST /login HTTP/1.1" 200 OK
INFO:     SECURITY login_success username='f08probe' ip=127.0.0.1
INFO:     127.0.0.1:55713 - "POST /login HTTP/1.1" 200 OK
INFO:     SECURITY login_success username='f08probe' ip=127.0.0.1
INFO:     127.0.0.1:55714 - "POST /login HTTP/1.1" 200 OK
INFO:     SECURITY login_success username='f08probe' ip=127.0.0.1
INFO:     127.0.0.1:55715 - "POST /login HTTP/1.1" 200 OK
INFO:     SECURITY login_success username='f08probe' ip=127.0.0.1
INFO:     127.0.0.1:55716 - "POST /login HTTP/1.1" 200 OK
INFO:     SECURITY login_success username='f08probe' ip=127.0.0.1
INFO:     127.0.0.1:55717 - "POST /login HTTP/1.1" 200 OK
INFO:     SECURITY login_success username='f08probe' ip=127.0.0.1
INFO:     127.0.0.1:55718 - "POST /login HTTP/1.1" 200 OK
INFO:     SECURITY login_success username='f08probe' ip=127.0.0.1
INFO:     127.0.0.1:55723 - "POST /login HTTP/1.1" 200 OK
WARNING:  SECURITY rate_limited ip=127.0.0.1 path='/login' limit=10 per 1 minute
INFO:     127.0.0.1:55724 - "POST /login HTTP/1.1" 429 Too Many Requests
WARNING:  SECURITY rate_limited ip=127.0.0.1 path='/login' limit=10 per 1 minute
INFO:     127.0.0.1:55725 - "POST /login HTTP/1.1" 429 Too Many Requests

Result: FIXED. Failed logins, auth failures and rate limiting now emit explicit SECURITY events with the username,
client IP and reason; successful logins are logged too. See F16-post-fix-log-capture_fixed.md for the full event set.
