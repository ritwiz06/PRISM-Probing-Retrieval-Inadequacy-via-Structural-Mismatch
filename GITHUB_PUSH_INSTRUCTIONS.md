# GitHub Push Instructions

## Current Local Git State

- Local repo path: `/Users/ritik/Documents/Projects/LLMRouter`
- Branch: `main`
- Initial project commit: `ad54d09 Initial PRISM project state`
- Push status: pushed successfully with HTTPS after SSH authentication failed.
- Current local `main` tracks `origin/main`.
- Git remote `origin` is configured.
- The repo was initialized locally because this directory was not previously a git repository.
- `.gitignore` is present and ignores local virtualenvs, caches, bytecode, local model/vector caches, and Python build artifacts.

## Configured Remote

```bash
origin  https://github.com/ritwiz06/PRISM-Probing-Retrieval-Inadequacy-via-Structural-Mismatch.git (fetch)
origin  https://github.com/ritwiz06/PRISM-Probing-Retrieval-Inadequacy-via-Structural-Mismatch.git (push)
```

## Push Attempt Result

Final result: push succeeded with HTTPS.

Successful push output:

```text
To https://github.com/ritwiz06/PRISM-Probing-Retrieval-Inadequacy-via-Structural-Mismatch.git
 * [new branch]      main -> main
branch 'main' set up to track 'origin/main'.
```

Earlier SSH attempts failed before switching to HTTPS.

First attempt:

```text
ssh: Could not resolve hostname github.com: -65563
fatal: Could not read from remote repository.
```

Escalated/network attempt:

```text
Host key verification failed.
fatal: Could not read from remote repository.
```

Final retry after committing this helper file produced the same SSH host-key failure.

This means SSH auth is still not configured, but HTTPS auth through the local credential helper worked.

## Useful Commands

Run these from the repo root:

```bash
cd /Users/ritik/Documents/Projects/LLMRouter
git status
git remote -v
git push
```

## SSH Optional Fix

If you prefer SSH later, add a GitHub SSH key and then switch back:

```bash
cd /Users/ritik/Documents/Projects/LLMRouter
git remote set-url origin git@github.com:ritwiz06/PRISM-Probing-Retrieval-Inadequacy-via-Structural-Mismatch.git
git remote -v
ssh -T git@github.com
```

## Safety Notes

- Do not run `git reset --hard`.
- Do not rewrite history.
- The local project is committed and ready to push.
- Local virtualenv and cache files are ignored and were not staged.
