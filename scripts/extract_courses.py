#!/usr/bin/env python3
"""One-time helper for regenerating public course data from the local transcript.

This intentionally writes only code, title, term, area, and note fields. Review
the generated YAML before publishing, and never commit the transcript PDF.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRANSCRIPT = ROOT / "unofficial_transcript.pdf"
OUTPUT = ROOT / "_data" / "courses.yml"


COURSES = [
    ("APSC 100", "Introduction to Engineering I", "2023W1", "General Engineering"),
    ("CHEM 154", "CHEM FOR ENGR", "2023W1", "General Engineering"),
    ("ECON 101", "Principles of Microeconomics", "2023W1", "General Engineering"),
    ("MATH 120", "Honours Differential Calculus", "2023W1", "Mathematics"),
    ("PHYS 157", "Introductory Physics for Engineers I", "2023W1", "Physics"),
    ("WRDS 150B", "Writing and Research in the Disciplines", "2023W1", "General Engineering"),
    ("APSC 101", "Introduction to Engineering II", "2023W2", "General Engineering"),
    ("APSC 160", "Introduction to Computation in Engineering Design", "2023W2", "Electrical / Computer Engineering"),
    ("MATH 121", "Honours Integral Calculus", "2023W2", "Mathematics"),
    ("MATH 152", "Linear Systems", "2023W2", "Mathematics"),
    ("PHYS 158", "Introductory Physics for Engineers II", "2023W2", "Physics"),
    ("PHYS 159", "Introductory Physics Laboratory for Engineers", "2023W2", "Physics"),
    ("PHYS 170", "Mechanics I", "2023W2", "Physics"),
    ("CPEN 221B", "Software Construction I", "2024W1", "Electrical / Computer Engineering"),
    ("ELEC 204", "Linear Circuits", "2024W1", "Electrical / Computer Engineering"),
    ("ENPH 259", "Experimental Techniques", "2024W1", "General Engineering"),
    ("MATH 217", "Multivariable and Vector Calculus", "2024W1", "Mathematics"),
    ("MATH 220", "Mathematical Proof", "2024W1", "Mathematics"),
    ("MATH 255", "Ordinary Differential Equations", "2024W1", "Mathematics"),
    ("APSC 278", "Engineering Materials", "2024W2", "General Engineering"),
    ("APSC 279", "Engineering Materials Laboratory", "2024W2", "General Engineering"),
    ("CIVL 250", "Engineering and Sustainable Development", "2024W2", "General Engineering"),
    ("ELEC 481", "Economic Analysis of Engineering Projects", "2024W2", "General Engineering"),
    ("MATH 307", "Applied Linear Algebra", "2024W2", "Mathematics"),
    ("MECH 260", "Introduction to Mechanics of Materials", "2024W2", "General Engineering"),
    ("MECH 280", "Introduction to Fluid Mechanics", "2024W2", "General Engineering"),
    ("PHYS 301", "Electricity and Magnetism", "2024W2", "Physics"),
    ("APSC 202", "Technical Communication Engineering Physics", "2025S", "General Engineering"),
    ("ENPH 253", "Introduction to Instrument Design", "2025S", "Robotics / Controls"),
    ("ENPH 257", "Heat and Thermodynamics", "2025S", "Physics"),
    ("ENPH 270", "Mechanics II", "2025S", "Physics"),
    ("MATH 257", "Partial Differential Equations", "2025S", "Mathematics"),
    ("PHYS 250", "Introduction to Modern Physics", "2025S", "Physics"),
    ("ENPH 353", "Engineering Physics Project I", "2025W1", "Robotics / Controls"),
    ("MATH 322", "Introduction to Group Theory", "2025W1", "Mathematics"),
    ("PHIL 220", "Symbolic Logic", "2025W1", "Mathematics"),
    ("PHYS 304", "Introduction to Quantum Mechanics", "2025W1", "Physics"),
    ("CPEN 312", "Digital Systems and Microcomputers", "2025W2", "Electrical / Computer Engineering"),
    ("MATH 305", "Applied Complex Analysis", "2025W2", "Mathematics"),
    ("MATH 443", "Graph Theory", "2025W2", "Mathematics"),
    ("PHYS 350", "Applications of Classical Mechanics", "2025W2", "Physics"),
    ("PHYS 401", "Electromagnetic Theory", "2025W2", "Physics"),
    ("PHYS 402", "Applications of Quantum Mechanics", "2025W2", "Physics"),
    ("APSC 110", "Co-operative Education Work Term I", "2026S", "General Engineering"),
]


def quote(value: str) -> str:
    return value.replace('"', '\\"')


def main() -> None:
    if not TRANSCRIPT.exists():
        raise SystemExit(f"Missing {TRANSCRIPT.name}; place it in the repository root first.")
    if shutil.which("pdftotext") is None:
        raise SystemExit("pdftotext is required for this helper.")

    text = subprocess.check_output(["pdftotext", str(TRANSCRIPT), "-"], text=True)
    missing = [code for code, _, _, _ in COURSES if code.replace(" ", "_V ", 1) not in text and code not in text]
    if missing:
        print("Warning: these course codes were not found in extracted text:", ", ".join(missing))

    lines = []
    for code, title, term, area in COURSES:
        note = "TODO: Add a short reflection on what this course contributed."
        if code == "APSC 110":
            note = "TODO: Decide whether to keep work terms in this public course list."
        lines.extend(
            [
                f'- code: "{quote(code)}"',
                f'  title: "{quote(title)}"',
                f'  term: "{quote(term)}"',
                f'  area: "{quote(area)}"',
                f'  note: "{quote(note)}"',
            ]
        )
    OUTPUT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
