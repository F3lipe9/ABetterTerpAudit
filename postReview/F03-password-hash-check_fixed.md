F03 retest - password storage (read-only database check)
Captured 2026-10-10. A read-only pymongo query (connection string from backend/.env, not printed) on the users collection.
Only the first 7 characters of each stored value are shown; no full hash is recorded.
The placeholder screenshot postReview/F03_plaintext_password_fixed.png is an empty file, so this text replaces it.

users: 8 | passwords matching bcrypt hash format: 8 | not matching: 0
testUser1 -> stored password prefix: $2b$12$... length: 60 | equals plaintext: False
testUser2 -> stored password prefix: $2b$12$... length: 60 | equals plaintext: False

Result: FIXED. All 8 stored passwords are 60-character bcrypt hashes ($2b$, cost 12), and none equal the plaintext password.
Code: register_user hashes with bcrypt before insert; login_user verifies with checkpw (and checks a dummy hash for unknown users).
