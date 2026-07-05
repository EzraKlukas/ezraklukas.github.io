#!/usr/bin/env python3
"""Verify curated public coursework against the local transcript.

The transcript is used only as a local source check. The site data remains the
hand-written curated YAML in _data/courses.yml and contains no grades, student
identifiers, addresses, or transcript metadata.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRANSCRIPT = ROOT / "unofficial_transcript.pdf"
OUTPUT = ROOT / "_data" / "courses.yml"


def course_token(code: str) -> str:
    subject, number = code.split(maxsplit=1)
    return f"{subject}_V {number}"


def main() -> None:
    if not TRANSCRIPT.exists():
        raise SystemExit(f"Missing {TRANSCRIPT.name}; place it in the repository root first.")
    if shutil.which("pdftotext") is None:
        raise SystemExit("pdftotext is required for this helper.")

    course_codes = []
    for line in OUTPUT.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("- code:"):
            course_codes.append(stripped.split(":", 1)[1].strip().strip('"'))

    text = subprocess.check_output(["pdftotext", str(TRANSCRIPT), "-"], text=True)
    missing = [code for code in course_codes if course_token(code) not in text]
    if missing:
        raise SystemExit("Missing selected course codes in transcript: " + ", ".join(missing))
    print(f"Verified {len(course_codes)} curated course codes against {TRANSCRIPT.name}.")


if __name__ == "__main__":
    main()
