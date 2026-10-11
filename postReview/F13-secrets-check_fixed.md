$ git ls-files | grep -i "\.env"
[exit 1]

$ git log --all --oneline -- .env
[done]

$ git log --all --oneline -S "mongodb+srv"
[done]

$ grep -rn "mongodb+srv\|mongodb://" (py,md,json,ts*,js*) . --exclude-dir=node_modules
[exit 1]

$ cat .gitignore
cat: .gitignore: No such file or directory

# NOTE: no root .gitignore exists; .gitignore files are per-subdirectory

$ cat backend/.gitignore
.env
$ cat ABetterTerp/.gitignore
# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*

node_modules
dist
dist-ssr
*.local

# Editor directories and files
.vscode/*
!.vscode/extensions.json
.idea
.DS_Store
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?

$ git check-ignore -v backend/.env
backend/.gitignore:1:.env	backend/.env

$ grep -rn "getenv\|MONGO" --include=*.py backend (excluding venv)
backend/main.py:18:MONGO_URL = os.getenv("MONGO_URL")
backend/main.py:37:client = AsyncMongoClient(MONGO_URL)

==================================================================
SUMMARY OF FINDINGS - F13 (Secrets / credential exposure)
==================================================================
Result: NOT VULNERABLE

1. No .env file is tracked. `git ls-files | grep -i "\.env"` returned nothing.
2. No .env file was ever committed. `git log --all --oneline -- .env` is
   empty across all branches.
3. No MongoDB connection string appears in history. `git log --all
   --oneline -S "mongodb+srv"` is empty.
4. No hardcoded connection strings exist in the working tree. The grep for
   "mongodb+srv" / "mongodb://" across .py/.md/.json/.ts*/.js* files
   (excluding node_modules) returned no matches. The database URL is read
   from the environment only: backend/main.py:18
   `MONGO_URL = os.getenv("MONGO_URL")`, used at main.py:37.
5. .env is git-ignored where it lives. backend/.gitignore lists `.env`, and
   `git check-ignore -v backend/.env` confirms the rule applies.

Deviations from expected output:
- There is no root-level .gitignore, so `cat .gitignore` failed. Ignore
  rules are per-subdirectory (backend/.gitignore, ABetterTerp/.gitignore).
  The check was completed against the subdirectory files instead.
- The final grep returned no lines at all, rather than "only os.getenv"
  lines, because os.getenv calls do not contain the searched strings. A
  supplementary grep for getenv/MONGO confirms the only reference.

Residual observations (hardening, not vulnerabilities):
- ABetterTerp/.gitignore (frontend) does not ignore .env files. If env files
  are added there later they would be tracked. Recommend adding `.env*`.
- A root .gitignore ignoring `.env` would provide defense in depth.
- This check covers git history and source files only. It does not prove the
  credential itself was never exposed elsewhere (chat, logs, screenshots).
  If there is any doubt, rotate the MongoDB credential.

==================== POST-FIX RETEST ====================
Re-run 2026-10-10 on branch auditing. (backend/.env exists locally; its contents were deliberately not read or printed.)

Result: STILL NOT VULNERABLE. No credential or secret was found in tracked files or in git history.

----- Raw output -----

$ git ls-files | grep -i "\.env"
[exit 1]

$ git log --all --oneline -- .env backend/.env ABetterTerp/.env
[done]

$ git log --all --oneline -S "mongodb+srv"
ed0ef49 Before Changes Vuln. Findings
[done]

$ git log --all --oneline -S "JWT_SECRET" (history search for secret values below)
033c26b fix(F01): add jwt auth
[done]

$ grep -rn "mongodb+srv\|mongodb://" tracked files
[exit 1]

$ ls -a root; cat .gitignore
.
..
.git
ABetterTerp
backend
evidence
postReview
README.md
test.md
cat: .gitignore: No such file or directory

$ cat backend/.gitignore
.env
$ cat ABetterTerp/.gitignore (env-related lines)
13:*.local
27:.env
28:.env.*
29:!.env.example

$ git check-ignore -v backend/.env
backend/.gitignore:1:.env	backend/.env

$ git ls-files backend/__pycache__ (compiled files tracked?)
backend/__pycache__/main.cpython-313.pyc

$ grep getenv/SECRET/KEY in backend/main.py
21:import secrets
38:MONGO_URL = os.getenv("MONGO_URL")
40:JWT_SECRET = os.getenv("JWT_SECRET")
41:if not JWT_SECRET:
42:    # No configured secret: use a per-process one. Tokens stop working on restart.
43:    print("WARNING: JWT_SECRET not set; using a random per-process secret")
44:    JWT_SECRET = secrets.token_urlsafe(48)
46:JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
49:ADMIN_USERNAMES = {u.strip() for u in os.getenv("ADMIN_USERNAMES", "").split(",") if u.strip()}
53:IS_DEV = os.getenv("ENVIRONMENT", "production").lower() == "development"
412:    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
430:            JWT_SECRET,
450:DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(16))

$ git grep for hardcoded secrets/keys in tracked files
[exit 1]

----- Findings -----
1. No .env tracked, and none ever committed (history of .env, backend/.env, ABetterTerp/.env is empty).
2. No connection string in the working tree: `git grep "mongodb+srv|mongodb://"` finds nothing.
3. `git log -S "mongodb+srv"` now returns one commit (ed0ef49 "Before Changes Vuln. Findings"). This is a false positive:
   the only matches in that commit are the audit evidence files themselves (evidence/F13-secrets-check.md and
   findings text) quoting the search string. No actual connection string or host (mongodb.net) appears.
4. New since the original test: JWT_SECRET. `git log -S "JWT_SECRET"` hits only 033c26b (fix F01), the code that reads it.
   main.py:40 reads JWT_SECRET from the environment; no secret value is hardcoded, and a hardcoded-secret regex over
   tracked files found nothing. If unset, a random per-process secret is generated (main.py:41-44), so tokens
   invalidate on restart and there is no guessable default.
   Other config also comes from the environment: MONGO_URL, JWT_EXPIRE_MINUTES, ADMIN_USERNAMES, ENVIRONMENT.
5. backend/.env is still ignored (backend/.gitignore:1, confirmed with git check-ignore).
6. The compiled backend/__pycache__/main.cpython-313.pyc is tracked in git; its bytes contain no mongodb URL or host.

Changes versus the original residual observations:
- FIXED: ABetterTerp/.gitignore now ignores .env and .env.* (keeps !.env.example), lines 27-29.
- STILL OPEN: no root-level .gitignore (ls shows none); backend/__pycache__/*.pyc is committed and shows as modified in
  git status. Recommend a root .gitignore with .env*, __pycache__/, *.pyc, and `git rm --cached` the .pyc.
- STILL OPEN: set JWT_SECRET explicitly in backend/.env for any multi-process or persistent deployment.
- Unchanged caveat: this proves only git history and source files; if the MongoDB credential or JWT secret may have
  been exposed elsewhere (chat, logs, screenshots), rotate it.
