"""Load, check and filter the question bank stored in data/questions_<lang>.json."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .models import LETTERS, Question
from .strings import CATEGORY_KEYS, DIFFICULTY_KEYS, MIXED, TRANSLATIONS

QUESTION_CATEGORIES = tuple(c for c in CATEGORY_KEYS if c != MIXED)
REQUIRED_TEXT_FIELDS = ("id", "question", "book", "explanation")


class QuestionBankError(Exception):
    """The question file is missing or cannot be read at all."""


@dataclass
class QuestionBank:
    questions: list[Question] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)   # reasons questions were skipped
    error: str | None = None                            # set when the whole file failed


def bank_path(data_dir: Path, language: str) -> Path:
    return data_dir / f"questions_{language}.json"


def load_questions(data_dir: Path, language: str) -> QuestionBank:
    """Load one language's questions. Never raises: problems are reported in the result."""
    path = bank_path(data_dir, language)
    try:
        raw = _read_json(path)
    except QuestionBankError as err:
        return QuestionBank(error=str(err))

    items = raw.get("questions") if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        return QuestionBank(error=f"{path.name}: expected a list of questions")

    bank = QuestionBank()
    seen_ids: set[str] = set()
    for index, item in enumerate(items, start=1):
        try:
            question = parse_question(item, language)
        except ValueError as err:
            label = item.get("id", f"#{index}") if isinstance(item, dict) else f"#{index}"
            bank.skipped.append(f"{label}: {err}")
            continue
        if question.id in seen_ids:
            bank.skipped.append(f"{question.id}: duplicate id")
            continue
        if not question.verified:
            bank.skipped.append(f"{question.id}: not marked as verified")
            continue
        seen_ids.add(question.id)
        bank.questions.append(question)
    return bank


def _read_json(path: Path):
    if not path.exists():
        raise QuestionBankError(f"file not found: {path}")
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as err:
        raise QuestionBankError(f"cannot read {path}: {err}") from err
    if not text.strip():
        raise QuestionBankError(f"file is empty: {path}")
    try:
        return json.loads(text)
    except json.JSONDecodeError as err:
        raise QuestionBankError(f"{path.name} is not valid JSON (line {err.lineno}): {err.msg}") from err


def parse_question(item, language: str) -> Question:
    """Turn one JSON object into a Question, raising ValueError if anything is wrong."""
    if not isinstance(item, dict):
        raise ValueError("entry is not an object")
    for key in REQUIRED_TEXT_FIELDS:
        if not isinstance(item.get(key), str) or not item[key].strip():
            raise ValueError(f"missing or empty '{key}'")

    if item.get("language") != language:
        raise ValueError(f"language must be '{language}'")

    known = {code for code, _ in TRANSLATIONS[language]}
    translations = item.get("translations")
    if not isinstance(translations, list) or not translations or not set(translations) <= known:
        raise ValueError(f"'translations' must list one or more of {sorted(known)}")

    if item.get("category") not in QUESTION_CATEGORIES:
        raise ValueError(f"unknown category '{item.get('category')}'")
    if item.get("difficulty") not in DIFFICULTY_KEYS:
        raise ValueError(f"unknown difficulty '{item.get('difficulty')}'")

    options = item.get("options")
    if not isinstance(options, dict) or sorted(options) != list(LETTERS):
        raise ValueError("'options' must have exactly the keys A, B, C and D")
    texts = [options[letter] for letter in LETTERS]
    if any(not isinstance(text, str) or not text.strip() for text in texts):
        raise ValueError("every option needs text")
    if len({text.strip() for text in texts}) != 4:
        raise ValueError("the four options must be different")

    correct = item.get("correct_answer")
    if correct not in LETTERS:
        raise ValueError("'correct_answer' must be A, B, C or D")

    chapter_verse = item.get("chapter_verse", "")
    if not isinstance(chapter_verse, str):
        raise ValueError("'chapter_verse' must be text")

    source_text = item.get("source_text") or {}
    if not isinstance(source_text, dict):
        raise ValueError("'source_text' must be an object like {\"ESV\": \"...\"}")

    return Question(
        id=item["id"].strip(),
        language=language,
        translations=tuple(translations),
        category=item["category"],
        difficulty=item["difficulty"],
        question=item["question"].strip(),
        options={letter: options[letter].strip() for letter in LETTERS},
        correct_answer=correct,
        book=item["book"].strip(),
        chapter_verse=chapter_verse.strip(),
        explanation=item["explanation"].strip(),
        source_text={k: v for k, v in source_text.items() if isinstance(v, str) and v.strip()},
        shuffle_options=bool(item.get("shuffle_options", True)),
        verified=item.get("verified") is True,
    )


def filter_questions(questions: list[Question], translation: str,
                     category: str, difficulty: str | None) -> list[Question]:
    """Questions for this translation, category ("mixed" = all) and difficulty (None = all)."""
    return [
        q for q in questions
        if translation in q.translations
        and (category == MIXED or q.category == category)
        and (difficulty is None or q.difficulty == difficulty)
    ]
