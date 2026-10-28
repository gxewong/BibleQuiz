"""Quiz rules that do not involve input or output, so they are easy to test."""
from __future__ import annotations

import random

from .models import LETTERS, AnswerRecord, PresentedQuestion, Question, QuizResult


def pick_questions(pool: list[Question], count: int, rng: random.Random) -> list[Question]:
    """Pick up to `count` different questions in random order (no repeats)."""
    return rng.sample(pool, min(count, len(pool)))


def prepare_question(question: Question, rng: random.Random) -> PresentedQuestion:
    """Shuffle the answer options (if allowed) and work out the new correct letter."""
    original_letters = list(LETTERS)
    if question.shuffle_options:
        rng.shuffle(original_letters)
    options = []
    correct_letter = ""
    for display_letter, original_letter in zip(LETTERS, original_letters):
        options.append((display_letter, question.options[original_letter]))
        if original_letter == question.correct_answer:
            correct_letter = display_letter
    return PresentedQuestion(question=question, options=options, correct_letter=correct_letter)


def normalize_answer(raw: str) -> str | None:
    """Return "A"-"D", "Q" for quit, or None for anything else. Case-insensitive."""
    answer = raw.strip().upper()
    # Accept full-width letters typed with a Chinese input method (Ａ, ｑ ...).
    if len(answer) == 1 and "Ａ" <= answer <= "Ｚ":
        answer = chr(ord(answer) - 0xFEE0)
    if answer in LETTERS or answer == "Q":
        return answer
    return None


def check_answer(presented: PresentedQuestion, selected_letter: str) -> AnswerRecord:
    return AnswerRecord(
        presented=presented,
        selected_letter=selected_letter,
        is_correct=selected_letter == presented.correct_letter,
    )


def calculate_score(answers: list[AnswerRecord], total_questions: int, quit_early: bool) -> QuizResult:
    attempted = len(answers)
    correct = sum(1 for a in answers if a.is_correct)
    percentage = (correct / attempted * 100) if attempted else 0.0
    return QuizResult(
        total_questions=total_questions,
        attempted=attempted,
        correct=correct,
        incorrect=attempted - correct,
        percentage=percentage,
        quit_early=quit_early,
        answers=list(answers),
    )


def format_percent(value: float) -> str:
    """80.0 -> "80", 66.666 -> "66.7"."""
    rounded = round(value, 1)
    return str(int(rounded)) if rounded == int(rounded) else f"{rounded:.1f}"


def performance_key(result: QuizResult) -> str:
    """Which encouraging message to show (a key in strings.TEXT)."""
    if result.attempted == 0:
        return "perf_none"
    if result.percentage >= 90:
        return "perf_excellent"
    if result.percentage >= 70:
        return "perf_great"
    if result.percentage >= 50:
        return "perf_good"
    return "perf_keep_going"
