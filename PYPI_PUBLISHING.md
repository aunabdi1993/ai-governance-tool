# Publishing to PyPI

This guide walks you through publishing the `ai-governance` package to PyPI so users can install it with `pip install ai-governance`.

## Prerequisites

1. **Create a PyPI account**: https://pypi.org/account/register/
2. **Create a TestPyPI account** (for testing): https://test.pypi.org/account/register/
3. **Install build tools**:
   ```bash
   pip install --upgrade build twine
   ```

## Step-by-Step Publishing Process

### 1. Update Version Number

Before each release, update the version in:
- `ai_governance/__init__.py` - Change `__version__ = "0.1.0"` to your new version
- `pyproject.toml` - Change `version = "0.1.0"` to match

Follow [Semantic Versioning](https://semver.org/):
- `0.1.0` → `0.1.1` for bug fixes
- `0.1.0` → `0.2.0` for new features
- `0.1.0` → `1.0.0` for major changes/breaking changes

### 2. Clean Previous Builds

```bash
rm -rf dist/ build/ *.egg-info
```

### 3. Build the Distribution Packages

```bash
python -m build
```

This creates two files in the `dist/` directory:
- `ai_governance-0.1.0-py3-none-any.whl` (wheel - preferred format)
- `ai_governance-0.1.0.tar.gz` (source distribution)

### 4. Test on TestPyPI First (Recommended)

Upload to TestPyPI to verify everything works:

```bash
python -m twine upload --repository testpypi dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: Your TestPyPI API token (get from https://test.pypi.org/manage/account/token/)

Then test installation:
```bash
pip install --index-url https://test.pypi.org/simple/ --no-deps ai-governance
```

### 5. Upload to Real PyPI

Once you've verified on TestPyPI:

```bash
python -m twine upload dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: Your PyPI API token (get from https://pypi.org/manage/account/token/)

### 6. Verify Installation

After uploading, test that users can install it:

```bash
pip install ai-governance
# or
pipx install ai-governance
```

## Using API Tokens (Recommended)

Instead of entering credentials each time, create a `~/.pypirc` file:

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

**Security**: Make sure to set proper permissions:
```bash
chmod 600 ~/.pypirc
```

## Automated Publishing Script

Use the provided `publish.sh` script for convenience:

```bash
# Test release to TestPyPI
bash publish.sh test

# Production release to PyPI
bash publish.sh
```

## Release Checklist

Before each release:

- [ ] Update version in `ai_governance/__init__.py`
- [ ] Update version in `pyproject.toml`
- [ ] Update CHANGELOG (if you have one)
- [ ] Test the package locally: `pip install -e .`
- [ ] Run your tests (if you have them)
- [ ] Clean old builds: `rm -rf dist/ build/ *.egg-info`
- [ ] Build: `python -m build`
- [ ] Test on TestPyPI
- [ ] Upload to PyPI
- [ ] Test installation: `pip install ai-governance`
- [ ] Create a git tag: `git tag v0.1.0 && git push origin v0.1.0`
- [ ] Create a GitHub release (optional)

## Updating the Package

When you want to release a new version:

1. Make your code changes
2. Update version numbers
3. Follow steps 2-6 above
4. Users can upgrade with: `pip install --upgrade ai-governance`

## Common Issues

**"File already exists" error:**
- You can't re-upload the same version
- Increment the version number and rebuild

**"Invalid distribution" error:**
- Make sure all required files are included (README.md, LICENSE)
- Check that MANIFEST.in includes all necessary files

**Missing data files after installation:**
- Verify `MANIFEST.in` includes them
- Check `package_data` in `pyproject.toml`
- Rebuild the package

## Useful Commands

```bash
# Check package before uploading
twine check dist/*

# View package contents
tar -tzf dist/ai_governance-0.1.0.tar.gz

# Test local installation
pip install dist/ai_governance-0.1.0-py3-none-any.whl
```

## Documentation Links

- PyPI: https://pypi.org/
- TestPyPI: https://test.pypi.org/
- Python Packaging Guide: https://packaging.python.org/
- Twine docs: https://twine.readthedocs.io/
- Build docs: https://build.pypa.io/
