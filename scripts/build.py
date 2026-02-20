"""Build script that handles TestPyPI and production PyPI with different package names."""

import argparse
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).parent.parent

TARGETS = {
    "prod": {
        "name": "ai-governance-tool",
        "out":  ROOT / "dist" / "prod",
    },
    "test": {
        "name": "ai-governance",
        "out":  ROOT / "dist" / "test",
    },
}


def build(target_name: str):
    cfg = TARGETS[target_name]
    pkg_name = cfg["name"]
    out_dir  = cfg["out"]

    # Read the canonical pyproject.toml
    pyproject = ROOT / "pyproject.toml"
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)

    original_name = data["project"]["name"]
    print(f"Building '{pkg_name}' → {out_dir.relative_to(ROOT)}/")

    # Temporarily write a modified pyproject.toml if names differ
    needs_patch = original_name != pkg_name
    if needs_patch:
        content = pyproject.read_text()
        patched  = content.replace(
            f'name = "{original_name}"',
            f'name = "{pkg_name}"',
            1,
        )
        pyproject.write_text(patched)

    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        # Clear previous artifacts for this target
        for f in out_dir.iterdir():
            f.unlink()

        result = subprocess.run(
            [sys.executable, "-m", "build", "--outdir", str(out_dir)],
            cwd=ROOT,
            check=True,
        )
    finally:
        # Restore only the name patch — never overwrite the whole file
        # so that version bumps or other edits made outside this script are preserved
        if needs_patch:
            current = pyproject.read_text()
            pyproject.write_text(current.replace(
                f'name = "{pkg_name}"',
                f'name = "{original_name}"',
                1,
            ))

    print(f"  Done — {pkg_name}")


def main():
    parser = argparse.ArgumentParser(description="Build for TestPyPI or PyPI")
    parser.add_argument(
        "--target",
        choices=["test", "prod", "all"],
        default="prod",
        help="Which target to build (default: prod)",
    )
    args = parser.parse_args()

    if args.target == "all":
        build("test")
        build("prod")
    else:
        build(args.target)


if __name__ == "__main__":
    main()
