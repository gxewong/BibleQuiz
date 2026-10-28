"""Quiz history: kept in memory for the session and (optionally) saved to a JSON file.

Only quiz settings and scores are stored — no names or other personal information.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from .models import QuizResult

FIELDS = ("date", "language", "translation", "category", "difficulty",
          "total_questions", "attempted", "correct", "percentage", "quit_early")


class HistoryStore:
    def __init__(self, path: Path | None):
        """`path=None` keeps history for this session only (nothing is written to disk)."""
        self.path = path
        self.results: list[dict] = []
        self.warnings: list[str] = []
        if path is not None:
            self.results = self._load()

    def _load(self) -> list[dict]:
        path = self.path
        if not path.exists():
            return []
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as err:
            self.warnings.append(f"could not read {path.name} ({err}); starting with empty history")
            return []
        if not text.strip():
            return []
        try:
            data = json.loads(text)
            entries = data["results"] if isinstance(data, dict) else data
            if not isinstance(entries, list):
                raise ValueError("no result list")
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            backup = self._backup_corrupt_file()
            self.warnings.append(
                f"{path.name} was damaged and could not be read; "
                + (f"it was moved to {backup.name}. " if backup else "")
                + "Starting with empty history."
            )
            return []
        valid = [e for e in entries if _is_valid_entry(e)]
        if len(valid) < len(entries):
            self.warnings.append(f"skipped {len(entries) - len(valid)} unreadable entries in {path.name}")
        return valid

    def _backup_corrupt_file(self) -> Path | None:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = self.path.with_name(f"{self.path.stem}.corrupt-{stamp}{self.path.suffix}")
        try:
            os.replace(self.path, backup)
            return backup
        except OSError:
            return None

    def add(self, result: QuizResult, language: str, translation: str,
            category: str, difficulty: str) -> bool:
        """Record a finished quiz. Returns True if it was also saved to disk."""
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "language": language,
            "translation": translation,
            "category": category,
            "difficulty": difficulty,
            "total_questions": result.total_questions,
            "attempted": result.attempted,
            "correct": result.correct,
            "percentage": round(result.percentage, 1),
            "quit_early": result.quit_early,
        }
        self.results.append(entry)
        return self._save()

    def _save(self) -> bool:
        if self.path is None:
            return False
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp = self.path.with_suffix(self.path.suffix + ".tmp")
            temp.write_text(json.dumps({"version": 1, "results": self.results},
                                       ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(temp, self.path)   # replace in one step so a crash can't leave half a file
            return True
        except OSError as err:
            self.warnings.append(f"could not save history to {self.path} ({err})")
            return False

    def pop_warnings(self) -> list[str]:
        warnings, self.warnings = self.warnings, []
        return warnings


def _is_valid_entry(entry) -> bool:
    if not isinstance(entry, dict) or not all(key in entry for key in FIELDS):
        return False
    numbers = ("total_questions", "attempted", "correct", "percentage")
    return all(isinstance(entry[k], (int, float)) and not isinstance(entry[k], bool) for k in numbers)
