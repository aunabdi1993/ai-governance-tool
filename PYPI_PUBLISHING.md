# Publishing to PyPI

## Package Names

| Registry | Package name | Install command |
|----------|-------------|-----------------|
| **PyPI** (production) | `ai-governance-tool` | `pipx install ai-governance-tool` |
| **TestPyPI** (testing) | `ai-governance` | see below |

> The CLI command is **`ai-governance`** on both — only the PyPI package name differs.

---

## One-Time Setup

### 1. Install build tools

```bash
pip install --upgrade build twine
```

### 2. Configure `~/.pypirc`

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_PYPI_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN_HERE
```

```bash
chmod 600 ~/.pypirc   # keep it private
```

Get tokens from:
- PyPI: https://pypi.org/manage/account/token/
- TestPyPI: https://test.pypi.org/manage/account/token/

---

## Release Workflow

The `Makefile` and `scripts/build.py` handle the name difference automatically.
`pyproject.toml` always stays set to `ai-governance-tool` — nothing is committed differently.

### Full release (recommended)

```bash
make release
```

This runs: **clean → build both targets → validate → upload to TestPyPI → prompt → upload to PyPI**

### Step by step

```bash
# 1. Update the version (both files must match)
#    ai_governance/__init__.py  →  __version__ = "0.2.0"
#    pyproject.toml             →  version = "0.2.0"

# 2. Build both distribution targets
python scripts/build.py --target all
#   dist/test/  →  ai_governance-0.2.0.*        (TestPyPI, name: ai-governance)
#   dist/prod/  →  ai_governance_tool-0.2.0.*   (PyPI,     name: ai-governance-tool)

# 3. Validate both
python -m twine check dist/test/* dist/prod/*

# 4. Upload to TestPyPI and verify
make test-upload

pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            ai-governance
ai-governance --version   # confirm it works

# 5. Upload to production PyPI
make prod-upload
```

### Make targets at a glance

| Command | What it does |
|---------|-------------|
| `make build` | Build `dist/prod/` (PyPI) |
| `make test-build` | Build `dist/test/` (TestPyPI) |
| `make check` | Validate packages with twine |
| `make test-upload` | Build + upload to TestPyPI |
| `make prod-upload` | Build + upload to PyPI |
| `make release` | Full workflow with confirmation prompt |
| `make clean` | Remove all build artifacts |

---

## Versioning

Follow [Semantic Versioning](https://semver.org/):

| Change type | Example |
|-------------|---------|
| Bug fix | `0.1.0` → `0.1.1` |
| New feature | `0.1.0` → `0.2.0` |
| Breaking change | `0.1.0` → `1.0.0` |

Always update **both** of these before building:

```python
# ai_governance/__init__.py
__version__ = "0.2.0"
```

```toml
# pyproject.toml
version = "0.2.0"
```

---

## Release Checklist

- [ ] Code changes complete and tested locally
- [ ] Version bumped in `ai_governance/__init__.py`
- [ ] Version bumped in `pyproject.toml` (must match)
- [ ] `make release` run successfully
- [ ] Tested install from TestPyPI
- [ ] Verified `ai-governance --version` after prod install
- [ ] Git tag created: `git tag v0.2.0 && git push origin v0.2.0`

---

## Upgrading an existing install

```bash
# Users upgrade with the PyPI package name
pip install --upgrade ai-governance-tool
pipx upgrade ai-governance-tool
```

---

## Common Errors

**"File already exists"**
You cannot re-upload the same version. Bump the version number and rebuild.

**"Invalid distribution"**
Check that `README.md` and `LICENSE` are present. Rebuild with `make build`.

**"Not authorized" / wrong project name**
Ensure your token matches the target registry (PyPI vs TestPyPI tokens are separate).

**Missing data files after install**
Verify `MANIFEST.in` includes them and `package_data` in `pyproject.toml` is correct. Rebuild.

---

## Useful commands

```bash
# Inspect what's inside a built package
tar -tzf dist/prod/ai_governance_tool-0.1.0.tar.gz

# Test install from local wheel (without uploading)
pip install dist/prod/ai_governance_tool-0.1.0-py3-none-any.whl
ai-governance --version
```

---

## Reference

- PyPI: https://pypi.org/project/ai-governance-tool/
- TestPyPI: https://test.pypi.org/project/ai-governance/
- Python Packaging Guide: https://packaging.python.org/
- Twine docs: https://twine.readthedocs.io/
