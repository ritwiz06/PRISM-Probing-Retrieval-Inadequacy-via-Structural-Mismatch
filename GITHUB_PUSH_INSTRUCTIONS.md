# GitHub Push Instructions

## Current Local Git State

- Local repo path: `/Users/ritik/Documents/Projects/LLMRouter`
- Branch: `main`
- Initial project commit: `ad54d09 Initial PRISM project state`
- Current local `HEAD` also includes this helper file and should be pushed as-is.
- Git remote `origin` is configured.
- The repo was initialized locally because this directory was not previously a git repository.
- `.gitignore` is present and ignores local virtualenvs, caches, bytecode, local model/vector caches, and Python build artifacts.

## Configured Remote

```bash
origin  git@github.com:ritwiz06/PRISM-Probing-Retrieval-Inadequacy-via-Structural-Mismatch.git (fetch)
origin  git@github.com:ritwiz06/PRISM-Probing-Retrieval-Inadequacy-via-Structural-Mismatch.git (push)
```

## Push Attempt Result

Automatic push did not complete from this environment.

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

This means the local commit exists, but SSH trust/auth setup needs to be completed in your normal terminal.

## Recommended Manual Push Commands

Run these from the repo root:

```bash
cd /Users/ritik/Documents/Projects/LLMRouter
git status
git remote -v
ssh -T git@github.com
git push -u origin main
```

If `ssh -T git@github.com` asks to trust GitHub's host key, type `yes`.

If SSH keys are not configured for this GitHub account, add an SSH key to GitHub or use the HTTPS fallback below.

## HTTPS Fallback

If SSH is not appropriate on this machine, switch the remote to HTTPS:

```bash
cd /Users/ritik/Documents/Projects/LLMRouter
git remote set-url origin https://github.com/ritwiz06/PRISM-Probing-Retrieval-Inadequacy-via-Structural-Mismatch.git
git remote -v
git push -u origin main
```

GitHub may ask for browser auth or a personal access token when using HTTPS.

## Safety Notes

- Do not run `git reset --hard`.
- Do not rewrite history.
- The local project is committed and ready to push.
- Local virtualenv and cache files are ignored and were not staged.
