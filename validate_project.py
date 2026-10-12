#!/usr/bin/env python3
"""Fast checks for Orbitly's SQL, workbook files, funnel counts, and dashboard."""
from __future__ import annotations
import sqlite3
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT / "orbitly.db"


def statements(path: Path) -> list[str]:
    src = "\n".join(line for line in path.read_text(encoding="utf-8").splitlines()
                     if not line.lstrip().startswith("--"))
    parts, buf = [], ""
    for line in src.splitlines(True):
        buf += line
        if sqlite3.complete_statement(buf):
            if buf.strip():
                parts.append(buf.strip())
            buf = ""
    if buf.strip():
        parts.append(buf.strip())
    return parts


def select_queries(path: Path) -> list[str]:
    return [s for s in statements(path) if s.lstrip().upper().startswith(("WITH", "SELECT"))]


def main() -> int:
    if not DB.exists():
        raise FileNotFoundError("orbitly.db is missing; run python3 build_project.py first")

    checks = 0
    with sqlite3.connect(DB) as con:
        if not con.execute("SELECT 1 FROM sqlite_master WHERE type='view' AND name='v_events'").fetchone():
            raise AssertionError("Expected view v_events is missing")
        for path in sorted((ROOT / "sql").glob("*.sql")):
            if path.name == "00_views.sql":
                continue
            for sql in select_queries(path):
                con.execute(sql).fetchone()
                checks += 1
            print(f"SQL OK: {path.relative_to(ROOT)}")

        drop_query = select_queries(ROOT / "sql" / "04_drop.sql")[0]
        drop_rows = con.execute(drop_query).fetchall()
        if any(row[2] < 0 for row in drop_rows):
            raise AssertionError(f"Negative funnel loss found: {drop_rows}")
        if len(drop_rows) != 5:
            raise AssertionError(f"Expected 5 sequential funnel transitions, found {len(drop_rows)}")
        print("Funnel nesting OK: all 5 step losses are non-negative")

    workbooks = sorted((ROOT / "excel").glob("*.xlsx"))
    if len(workbooks) != 3:
        raise AssertionError(f"Expected 3 Excel workbooks, found {len(workbooks)}")
    for workbook in workbooks:
        if workbook.read_bytes()[:4] != b"PK\x03\x04":
            raise AssertionError(f"Not a binary XLSX archive: {workbook.name}")
        with zipfile.ZipFile(workbook) as zf:
            bad = zf.testzip()
            if bad:
                raise AssertionError(f"Corrupt workbook {workbook.name}: {bad}")
            if "xl/workbook.xml" not in zf.namelist():
                raise AssertionError(f"Missing workbook XML: {workbook.name}")
        print(f"Workbook OK: excel/{workbook.name}")

    dashboard = ROOT / "dashboard" / "index.html"
    html = dashboard.read_text(encoding="utf-8")
    for required in ["Synthetic dataset", "channel-adjusted", "95% CI", "What +5 percentage points of activation could be worth", "12-month retention assumption"]:
        if required.lower() not in html.lower():
            raise AssertionError(f"Dashboard is missing expected content: {required}")
    if "$1.4M" in html or "5.0% activation" in html or "largest raw retention gap" in html:
        raise AssertionError("Dashboard appears to contain a stale hardcoded claim")
    print(f"Dashboard OK: {dashboard.stat().st_size:,} bytes")
    print(f"Validation complete: {checks} SQL statements, {len(workbooks)} workbooks, dashboard and funnel checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
