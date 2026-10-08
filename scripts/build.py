"""Build a deterministic deployable ZIP: python scripts/build.py"""
import fnmatch
import hashlib
import os
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT / "dist"
ARTIFACT = DIST_DIR / "bookstore-ai-sdlc-capstone.zip"

INCLUDE_DIRS = ("app", "frontend", "scripts", "tests", "docs")
INCLUDE_FILES = ("requirements.txt", "README.md", ".gitignore", "PROJECT_STATUS.md")
REQUIRED = (
    "app/main.py",
    "frontend/index.html",
    "scripts/seed.py",
    "scripts/build.py",
    "requirements.txt",
    "README.md",
    ".gitignore",
)

EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".idea", ".claude", ".codemie",
    "dist", ".pytest_cache",
}
EXCLUDED_PATTERNS = ("*.pyc", "*.pyo", "*.db", "*.sqlite", ".env")

# Fixed metadata so identical sources always produce a byte-identical ZIP.
FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
FILE_MODE = 0o644


def is_excluded(relative: Path) -> bool:
    if any(part in EXCLUDED_DIRS for part in relative.parts):
        return True
    return any(fnmatch.fnmatch(relative.name, pattern) for pattern in EXCLUDED_PATTERNS)


def collect_files() -> list[str]:
    found: set[str] = set()
    for name in INCLUDE_FILES:
        path = ROOT / name
        if path.is_file():
            found.add(name)
    for directory in INCLUDE_DIRS:
        base = ROOT / directory
        if not base.is_dir():
            continue
        for current, dirs, files in os.walk(base):
            current_path = Path(current)
            dirs[:] = [d for d in dirs if not is_excluded((current_path / d).relative_to(ROOT))]
            for file_name in files:
                relative = (current_path / file_name).relative_to(ROOT)
                if not is_excluded(relative):
                    found.add(relative.as_posix())
    return sorted(found)


def write_zip(files: list[str], target: Path) -> None:
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in files:
            info = zipfile.ZipInfo(name, FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = FILE_MODE << 16
            archive.writestr(info, (ROOT / name).read_bytes(), compresslevel=9)


def verify(target: Path, files: list[str]) -> None:
    with zipfile.ZipFile(target) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"Corrupt entry in archive: {bad}")
        if sorted(archive.namelist()) != files:
            raise RuntimeError("Archive contents do not match the expected file list")


def main() -> int:
    try:
        files = collect_files()
        missing = [name for name in REQUIRED if name not in files]
        if missing:
            raise RuntimeError(f"Required files missing: {', '.join(missing)}")

        DIST_DIR.mkdir(exist_ok=True)
        partial = ARTIFACT.with_suffix(".zip.part")
        write_zip(files, partial)
        verify(partial, files)
        partial.replace(ARTIFACT)

        digest = hashlib.sha256(ARTIFACT.read_bytes()).hexdigest()
        print(f"Artifact: {ARTIFACT}")
        print(f"Size:     {ARTIFACT.stat().st_size} bytes")
        print(f"SHA-256:  {digest}")
        print(f"Files included ({len(files)}):")
        for name in files:
            print(f"  {name}")
        print("BUILD SUCCESS")
        return 0
    except Exception as error:
        print(f"BUILD FAILURE: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
