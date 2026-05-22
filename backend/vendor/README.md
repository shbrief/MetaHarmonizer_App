# `backend/vendor/`

Pre-built wheels we install instead of fetching from git, so
`pip install -r requirements.txt` works on every OS without a special path.

## `metaharmonizer-0.3.0-py3-none-any.whl`

Built from [`shbrief/MetaHarmonizer`](https://github.com/shbrief/MetaHarmonizer)
at commit `792eb75d4d81cb90b6480bf4e6226b781f402b11`, with the upstream
`data/corpus/` directory excluded.

**Why the exclusion**: a few files under `data/corpus/` have `:` in their
names, which NTFS forbids. Installing `git+https://github.com/...` on
Windows therefore fails at the checkout step. Excluding that directory
lets the wheel install cleanly everywhere. The corpus is only consumed by
upstream's `OntoMapEngine` (FAISS + SQLite knowledge DB), which the
dashboard does not call today — it uses `SchemaMapEngine` only.

## Rebuilding after a version bump

When upstream ships a new commit you want to pin:

```powershell
# 1. Pick the new commit SHA
$SHA = "<new-upstream-commit-sha>"
$VER = "0.3.0"   # bump if upstream's pyproject version changed

# 2. Download + extract (skip the corpus)
$tmp = "$env:TEMP\mh_wheel"
Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory $tmp -Force | Out-Null
Invoke-WebRequest "https://codeload.github.com/shbrief/MetaHarmonizer/tar.gz/$SHA" -OutFile "$tmp\mh.tar.gz" -UseBasicParsing
tar -xzf "$tmp\mh.tar.gz" -C $tmp --exclude='*/data/corpus/*'

# 3. Build the wheel
backend\venv\Scripts\python.exe -m pip wheel "$tmp\MetaHarmonizer-$SHA" --no-deps -w "$tmp\dist"

# 4. Drop the new wheel in this directory, remove the old one
Move-Item "$tmp\dist\metaharmonizer-$VER-py3-none-any.whl" backend\vendor\ -Force

# 5. Update the path in backend/requirements.txt if VER changed, commit, push
```

Linux/macOS: same flow with `bash`, `curl`/`wget`, and `tar`.
