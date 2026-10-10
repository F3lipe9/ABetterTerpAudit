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
