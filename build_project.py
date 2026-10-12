#!/usr/bin/env python3
"""Rebuild Orbitly's generated artifacts from the synthetic source data.

From a fresh clone, this generates orbitly.db, creates the shared event view,
rebuilds the three Excel workbooks and rebuilds dashboard/index.html.
Use --regenerate-data to recreate the seeded data even if orbitly.db exists.
"""
from __future__ import annotations
import argparse
import subprocess
import sys
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT / "orbitly.db"


def run(label: str, args: list[str]) -> None:
    print(f"\n== {label} ==", flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regenerate-data", action="store_true",
                        help="recreate the synthetic database even if it already exists")
    parser.add_argument("--skip-validation", action="store_true",
                        help="skip the final SQL/workbook/dashboard consistency checks")
    args = parser.parse_args()

    if args.regenerate_data or not DB.exists():
        run("Generate synthetic data", [sys.executable, "data_generator.py"])
    else:
        print("Using existing orbitly.db. Pass --regenerate-data to recreate it.", flush=True)

    print("\n== Create normalized event view ==", flush=True)
    with sqlite3.connect(DB) as con:
        con.executescript((ROOT / "sql" / "00_views.sql").read_text(encoding="utf-8"))
        con.commit()

    run("Build Excel models and experiment readouts", [sys.executable, "build_excel.py"])
    run("Build interactive dashboard", [sys.executable, "dashboard/build_dashboard.py"])
    if not args.skip_validation:
        run("Validate generated outputs", [sys.executable, "validate_project.py"])

    print("\nBuild complete. The generated database is local and should not be committed.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
