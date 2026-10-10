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
