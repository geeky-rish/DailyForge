#!/usr/bin/env python3
"""
Import questions from a CSV or JSON file into the DailyForge database.

Usage:
  python scripts/import_questions.py data/questions/striver_sde180_sample.json
  python scripts/import_questions.py data/questions/your_full_list.csv

The script is idempotent: it upserts on problem_id.
"""
import json
import csv
import sys
import os
from pathlib import Path

# Allow running from the backend directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.database import SessionLocal, engine, Base
from app.models.models import Problem


def load_from_json(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return data.get("questions", [])


def load_from_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def import_questions(file_path: str) -> None:
    path = Path(file_path)
    if not path.exists():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(1)

    if path.suffix.lower() == ".json":
        questions = load_from_json(path)
    elif path.suffix.lower() == ".csv":
        questions = load_from_csv(path)
    else:
        print(f"ERROR: Unsupported file type: {path.suffix}", file=sys.stderr)
        sys.exit(1)

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        imported = 0
        updated = 0
        for q in questions:
            problem_id = str(q.get("id") or q.get("problem_id", "")).strip()
            if not problem_id:
                print(f"SKIP: missing id in row: {q}")
                continue

            existing = db.query(Problem).filter(Problem.problem_id == problem_id).first()
            if existing:
                existing.sheet_order = int(q.get("sheet_order", existing.sheet_order))
                existing.title = str(q.get("title", existing.title)).strip()
                existing.topic = str(q.get("topic", existing.topic)).strip()
                existing.subtopic = str(q.get("subtopic") or "").strip() or None
                existing.difficulty = str(q.get("difficulty") or "").strip() or None
                existing.url = str(q.get("url") or "").strip() or None
                existing.notes = str(q.get("notes") or "").strip() or None
                updated += 1
            else:
                problem = Problem(
                    problem_id=problem_id,
                    sheet_order=int(q.get("sheet_order", 0)),
                    title=str(q.get("title", "")).strip(),
                    topic=str(q.get("topic", "")).strip(),
                    subtopic=str(q.get("subtopic") or "").strip() or None,
                    difficulty=str(q.get("difficulty") or "").strip() or None,
                    url=str(q.get("url") or "").strip() or None,
                    notes=str(q.get("notes") or "").strip() or None,
                )
                db.add(problem)
                imported += 1

        db.commit()
        print(f"Import complete: {imported} new, {updated} updated")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_questions.py <path_to_json_or_csv>")
        sys.exit(1)
    import_questions(sys.argv[1])
