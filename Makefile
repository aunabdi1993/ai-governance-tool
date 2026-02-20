.PHONY: help clean install install-dev test lint format typecheck quality \
        build test-build check test-upload prod-upload release

help:
	@echo "Development Commands:"
	@echo "  make install      Install package and core dependencies"
	@echo "  make install-dev  Install package in dev mode with all extras"
	@echo "  make test         Run test suite with coverage"
	@echo "  make lint         Run ruff linter"
	@echo "  make format       Format code with black and ruff"
	@echo "  make typecheck    Run mypy type checker"
	@echo "  make quality      Run all quality checks (lint + typecheck + test)"
	@echo ""
	@echo "Release Commands:"
	@echo "  make build        Build dist/ packages for production"
	@echo "  make test-build   Build dist/ packages for TestPyPI"
	@echo "  make check        Validate packages with twine"
	@echo "  make test-upload  Upload to TestPyPI"
	@echo "  make prod-upload  Upload to PyPI"
	@echo "  make release      Full workflow: build → check → test → prod"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make clean        Remove build artifacts and caches"

# Development setup
install:
	pip install -e .

install-dev:
	pip install -e ".[dev,test,openai,dashboard]"
	pre-commit install

# Code quality
test:
	pytest tests/ -v

lint:
	ruff check ai_governance/

format:
	ruff check --fix ai_governance/
	black ai_governance/ tests/

typecheck:
	mypy ai_governance/

quality: lint typecheck test
	@echo "✓ All quality checks passed!"

# Build and release
clean:
	rm -rf dist/ build/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .mypy_cache .pytest_cache .ruff_cache htmlcov/ .coverage

build: clean
	python scripts/build.py --target prod
	@echo "\nBuilt prod dist:"
	@ls -lh dist/prod/

test-build: clean
	python scripts/build.py --target test
	@echo "\nBuilt test dist:"
	@ls -lh dist/test/

check:
	python -m twine check dist/prod/* 2>/dev/null || python -m twine check dist/test/*

test-upload: test-build
	python -m twine upload --repository testpypi dist/test/*
	@echo "\nInstall from TestPyPI:"
	@echo "  pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ ai-governance"

prod-upload: build
	python -m twine upload --repository pypi dist/prod/*
	@echo "\nInstall from PyPI:"
	@echo "  pipx install ai-governance-tool"

release:
	@echo "=== Step 1: Build both targets ==="
	python scripts/build.py --target all
	@echo "\n=== Step 2: Validate ==="
	python -m twine check dist/prod/* dist/test/*
	@echo "\n=== Step 3: Upload to TestPyPI ==="
	python -m twine upload --repository testpypi dist/test/*
	@echo "\n"
	@read -p "TestPyPI OK? Upload to production PyPI? [y/N] " ans && [ "$$ans" = "y" ]
	@echo "\n=== Step 4: Upload to PyPI ==="
	python -m twine upload --repository pypi dist/prod/*
