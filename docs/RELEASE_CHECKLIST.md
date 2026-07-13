# Release Checklist — v0.1.0-alpha

Prepare the first organized public release. **Do not publish automatically** —
these are the commands and gates; a human performs the tag/publish.

## 1. Versioning (SemVer)

- [ ] `src/nutev/__version__.py` set to the target version (e.g. `0.1.0`).
- [ ] `CITATION.cff` `version:` matches (`0.1.0-alpha`).
- [ ] `CHANGELOG.md` has a dated section for the release.

## 2. Clean-environment install (Python 3.12)

```bash
python3.12 -m venv /tmp/nutev-rel && . /tmp/nutev-rel/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dashboard]"
```

- [ ] Install succeeds with **core + dashboard only** (no legacy heavy stack).

## 3. `nutev` command test (zero-key)

```bash
nutev --help
nutev demo-data --project-root ./project_output_demo
test -f project_output_demo/07_logs/run_summary.json && echo "OK: demo output present"
```

- [ ] `nutev` runs; demo generates outputs without any API key or network.

## 4. Canonical tests

```bash
PYTHONPATH=src python -m pytest -q nutev_tests
```

- [ ] Canonical suite green (document any known pre-existing failures in
  `CHANGELOG.md`).

## 5. Build distribution artifacts

```bash
python -m pip install build
python -m build            # produces dist/*.whl and dist/*.tar.gz
python -m pip install twine && twine check dist/*
```

- [ ] Wheel + sdist build; `twine check` passes.

## 6. Documentation link verification

```bash
# Fail if any relative markdown link points to a missing file.
python - <<'PY'
import re, pathlib, sys
root = pathlib.Path('.')
bad = []
for md in root.rglob('*.md'):
    if any(p in md.parts for p in ('.git','node_modules','.venv')): continue
    for m in re.finditer(r'\]\(([^)]+)\)', md.read_text(encoding='utf-8', errors='ignore')):
        link = m.group(1).split('#')[0].strip()
        if not link or link.startswith(('http://','https://','mailto:')): continue
        if not (md.parent / link).exists():
            bad.append(f"{md}: {link}")
print("\n".join(bad) if bad else "OK: no broken relative links")
sys.exit(1 if bad else 0)
PY
```

- [ ] No broken relative documentation links.

## 7. Security gates

- [ ] `security-scan` (gitleaks + repo-hygiene) green.
- [ ] No secrets, `.env`, PDFs, real outputs, or local DBs tracked.
- [ ] `.gitleaksignore` re-triaged (manual).

## 8. Tag & publish (manual — do not automate)

```bash
git tag -a v0.1.0-alpha -m "NutEV/NutMEV v0.1.0-alpha"
git push origin v0.1.0-alpha
# Then draft the GitHub Release from CHANGELOG.md notes.
```

- [ ] Draft release notes from the `CHANGELOG.md` section.
- [ ] (Optional) Zenodo/OSF archival + DOI, then update `CITATION.cff`.
