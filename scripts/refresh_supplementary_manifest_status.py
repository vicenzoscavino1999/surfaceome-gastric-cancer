from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "results" / "tables" / "supplementary_table_manifest.tsv"
SENTINEL = ROOT / "results" / "tables" / "supplementary_table_manifest.status.ok"


def main() -> int:
    if not MANIFEST.exists():
        raise FileNotFoundError(f"Missing supplementary manifest: {MANIFEST}")

    with MANIFEST.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    if "path" not in fieldnames or "exists" not in fieldnames:
        raise ValueError("supplementary manifest must include path and exists columns")

    missing: list[str] = []
    for row in rows:
        rel_path = row.get("path", "")
        target = ROOT / rel_path
        exists = target.exists()
        row["exists"] = str(exists).lower()
        if row.get("status", "").startswith("available") and not exists:
            missing.append(rel_path)

    if missing:
        raise FileNotFoundError("Supplementary manifest paths are missing: " + ", ".join(missing))

    with MANIFEST.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    SENTINEL.write_text("supplementary_table_manifest_status=ok\n", encoding="utf-8")
    print("Refreshed supplementary table manifest path status.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
