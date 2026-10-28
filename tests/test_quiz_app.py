"""Automated tests. Run from the project folder:  python -m unittest -v"""
from __future__ import annotations

import json
import random
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from quiz_app.history import HistoryStore                                   # noqa: E402
from quiz_app.models import LETTERS                                         # noqa: E402
from quiz_app.question_bank import filter_questions, load_questions          # noqa: E402
from quiz_app.quiz_engine import (calculate_score, check_answer, format_percent,  # noqa: E402
                                  normalize_answer, performance_key, pick_questions,
                                  prepare_question)
from quiz_app.strings import (CATEGORY_KEYS, DIFFICULTY_KEYS, MIXED, TEXT,   # noqa: E402
                              TRANSLATIONS)

DATA_DIR = PROJECT_DIR / "data"


def sample_question(**overrides) -> dict:
    question = {
        "id": "T-1", "language": "en", "translations": ["NIV"], "category": "general",
        "difficulty": "easy", "question": "Q?", "options": {"A": "w", "B": "x", "C": "y", "D": "z"},
        "correct_answer": "B", "book": "Genesis", "chapter_verse": "1:1",
        "explanation": "E.", "verified": True,
    }
    question.update(overrides)
    return question


def write_bank(folder: Path, language: str, questions) -> None:
    (folder / f"questions_{language}.json").write_text(
        json.dumps({"questions": questions}, ensure_ascii=False), encoding="utf-8")


class QuestionBankTests(unittest.TestCase):
    def test_starter_banks_load_without_problems(self):
        for lang in ("en", "zh"):
            bank = load_questions(DATA_DIR, lang)
            self.assertIsNone(bank.error)
            self.assertEqual(bank.skipped, [], bank.skipped)
            self.assertGreaterEqual(len(bank.questions), 30)

    def test_every_category_and_difficulty_is_covered(self):
        for lang in ("en", "zh"):
            questions = load_questions(DATA_DIR, lang).questions
            cells = Counter((q.category, q.difficulty) for q in questions)
            for category in CATEGORY_KEYS:
                if category == MIXED:
                    continue
                for difficulty in DIFFICULTY_KEYS:
                    self.assertGreaterEqual(cells[(category, difficulty)], 1, (lang, category, difficulty))

    def test_english_and_chinese_banks_are_paired(self):
        en = load_questions(DATA_DIR, "en").questions
        zh = load_questions(DATA_DIR, "zh").questions
        self.assertEqual(len(en), len(zh))
        for q_en, q_zh in zip(en, zh):
            self.assertEqual(q_en.id[3:], q_zh.id[3:])
            self.assertEqual((q_en.category, q_en.difficulty, q_en.correct_answer),
                             (q_zh.category, q_zh.difficulty, q_zh.correct_answer), q_en.id)

    def test_translation_filter(self):
        en = load_questions(DATA_DIR, "en").questions
        zh = load_questions(DATA_DIR, "zh").questions
        for code, _ in TRANSLATIONS["en"]:
            self.assertEqual(len(filter_questions(en, code, MIXED, None)), len(en))
        self.assertEqual(len(filter_questions(zh, "CUVMPS", MIXED, None)), len(zh))
        self.assertEqual(filter_questions(zh, "NIV", MIXED, None), [])

    def test_category_and_difficulty_filters_change_the_questions(self):
        en = load_questions(DATA_DIR, "en").questions
        parables_easy = filter_questions(en, "NIV", "parables", "easy")
        self.assertTrue(parables_easy)
        self.assertTrue(all(q.category == "parables" and q.difficulty == "easy" for q in parables_easy))
        mixed_hard = filter_questions(en, "NIV", MIXED, "advanced")
        self.assertTrue(all(q.difficulty == "advanced" for q in mixed_hard))
        self.assertGreater(len({q.category for q in mixed_hard}), 1)

    def test_missing_empty_and_broken_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.assertIn("not found", load_questions(folder, "en").error)
            (folder / "questions_en.json").write_text("", encoding="utf-8")
            self.assertIn("empty", load_questions(folder, "en").error)
            (folder / "questions_en.json").write_text("{ not json", encoding="utf-8")
            self.assertIn("not valid JSON", load_questions(folder, "en").error)

    def test_invalid_unverified_and_duplicate_questions_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            write_bank(folder, "en", [
                sample_question(id="ok"),
                sample_question(id="ok"),                                   # duplicate
                sample_question(id="unverified", verified=False),
                sample_question(id="bad-answer", correct_answer="E"),
                sample_question(id="same-options", options={"A": "x", "B": "x", "C": "y", "D": "z"}),
                sample_question(id="three-options", options={"A": "x", "B": "y", "C": "z"}),
                sample_question(id="bad-cat", category="history"),
                sample_question(id="bad-trans", translations=["KJV"]),
                "not an object",
            ])
            bank = load_questions(folder, "en")
            self.assertEqual([q.id for q in bank.questions], ["ok"])
            self.assertEqual(len(bank.skipped), 8)


class EngineTests(unittest.TestCase):
    def test_shuffled_options_keep_the_correct_answer(self):
        questions = load_questions(DATA_DIR, "en").questions
        rng = random.Random(1)
        for _ in range(20):
            for q in questions:
                presented = prepare_question(q, rng)
                self.assertEqual(presented.option_text(presented.correct_letter), q.options[q.correct_answer])
                self.assertEqual(sorted(t for _, t in presented.options), sorted(q.options.values()))
                self.assertEqual([letter for letter, _ in presented.options], list(LETTERS))

    def test_numeric_questions_are_not_shuffled(self):
        q = next(q for q in load_questions(DATA_DIR, "en").questions if not q.shuffle_options)
        presented = prepare_question(q, random.Random(3))
        self.assertEqual(dict(presented.options), q.options)

    def test_answer_input_is_case_insensitive_and_validated(self):
        self.assertEqual(normalize_answer("a"), "A")
        self.assertEqual(normalize_answer("  D "), "D")
        self.assertEqual(normalize_answer("ｂ"), "B")     # full-width letter from a Chinese keyboard
        self.assertEqual(normalize_answer("q"), "Q")
        for bad in ("", "E", "AB", "1", "答"):
            self.assertIsNone(normalize_answer(bad))

    def test_no_repeated_questions(self):
        questions = load_questions(DATA_DIR, "en").questions
        picked = pick_questions(questions, 10, random.Random(5))
        self.assertEqual(len(picked), 10)
        self.assertEqual(len({q.id for q in picked}), 10)
        self.assertEqual(len(pick_questions(questions[:3], 10, random.Random(5))), 3)

    def _answers(self, correct: int, wrong: int):
        q = load_questions(DATA_DIR, "en").questions[0]
        presented = prepare_question(q, random.Random(0))
        wrong_letter = next(l for l in LETTERS if l != presented.correct_letter)
        return ([check_answer(presented, presented.correct_letter) for _ in range(correct)]
                + [check_answer(presented, wrong_letter) for _ in range(wrong)])

    def test_score_and_percentage(self):
        result = calculate_score(self._answers(8, 2), 10, quit_early=False)
        self.assertEqual((result.attempted, result.correct, result.incorrect), (10, 8, 2))
        self.assertEqual(format_percent(result.percentage), "80")
        self.assertEqual(performance_key(result), "perf_great")

    def test_quit_early_percentage_uses_answered_questions(self):
        result = calculate_score(self._answers(2, 1), 10, quit_early=True)
        self.assertEqual(result.unanswered, 7)
        self.assertEqual(format_percent(result.percentage), "66.7")

    def test_zero_attempts_do_not_divide_by_zero(self):
        result = calculate_score([], 10, quit_early=True)
        self.assertEqual(result.percentage, 0.0)
        self.assertEqual(performance_key(result), "perf_none")
        self.assertEqual(calculate_score([], 0, quit_early=False).percentage, 0.0)

    def test_performance_bands(self):
        self.assertEqual(performance_key(calculate_score(self._answers(10, 0), 10, False)), "perf_excellent")
        self.assertEqual(performance_key(calculate_score(self._answers(5, 5), 10, False)), "perf_good")
        self.assertEqual(performance_key(calculate_score(self._answers(1, 9), 10, False)), "perf_keep_going")


class HistoryTests(unittest.TestCase):
    def _result(self):
        return calculate_score(EngineTests._answers(EngineTests(), 3, 1), 4, quit_early=False)

    def test_missing_and_empty_files_give_empty_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "h.json"
            self.assertEqual(HistoryStore(path).results, [])
            path.write_text("   ", encoding="utf-8")
            store = HistoryStore(path)
            self.assertEqual((store.results, store.warnings), ([], []))

    def test_results_persist_between_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sub" / "h.json"
            self.assertTrue(HistoryStore(path).add(self._result(), "zh", "CUVMPS", "parables", "easy"))
            reloaded = HistoryStore(path).results
            self.assertEqual(len(reloaded), 1)
            self.assertEqual((reloaded[0]["correct"], reloaded[0]["percentage"]), (3, 75.0))

    def test_corrupted_file_is_backed_up_not_lost(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "h.json"
            path.write_text("{broken", encoding="utf-8")
            store = HistoryStore(path)
            self.assertEqual(store.results, [])
            self.assertTrue(store.warnings)
            backups = list(Path(tmp).glob("h.corrupt-*.json"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding="utf-8"), "{broken")

    def test_bad_entries_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "h.json"
            good = {"date": "2026-01-01 10:00", "language": "en", "translation": "NIV",
                    "category": "mixed", "difficulty": "easy", "total_questions": 10,
                    "attempted": 10, "correct": 7, "percentage": 70.0, "quit_early": False}
            path.write_text(json.dumps({"results": [good, {"date": "x"}, 5]}), encoding="utf-8")
            store = HistoryStore(path)
            self.assertEqual(store.results, [good])
            self.assertTrue(store.warnings)

    def test_session_only_mode_writes_nothing(self):
        store = HistoryStore(None)
        self.assertFalse(store.add(self._result(), "en", "NIV", "mixed", "easy"))
        self.assertEqual(len(store.results), 1)


class StringsTests(unittest.TestCase):
    def test_both_languages_have_the_same_keys(self):
        self.assertEqual(set(TEXT["en"]), set(TEXT["zh"]))


def run_app(inputs: list[str], *args: str) -> str:
    """Run main.py with scripted keyboard input and return everything it printed."""
    completed = subprocess.run(
        [sys.executable, str(PROJECT_DIR / "main.py"), *args],
        input="\n".join(inputs) + "\n", capture_output=True, text=True, encoding="utf-8", timeout=60,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)
    return completed.stdout


class EndToEndTests(unittest.TestCase):
    """Drive the real program through the terminal, as a user would."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.history = str(Path(self.tmp.name) / "history.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_each_english_translation_can_be_selected(self):
        for number, code in (("1", "NIV"), ("2", "ESV"), ("3", "NLT")):
            out = run_app(["1", number, "8"], "--no-save")
            self.assertIn(f"Selected translation: {code}", out)
            self.assertIn("========== MAIN MENU ==========", out)

    def test_full_english_quiz_with_invalid_input_review_and_history(self):
        answers = ["x", "E", "", "a"] + [""] + ["b", ""] * 8 + ["C"]
        out = run_app(["1", "1", "1"] + answers + ["9", "2", "", "1", "", "3", "6", "", "8"],
                      "--seed", "11", "--history-file", self.history)
        self.assertIn("Question 1 of 10", out)
        self.assertIn("Question 10 of 10", out)
        self.assertIn("Please enter A, B, C or D (or Q to quit).", out)
        self.assertIn("Reference:", out)
        self.assertIn("========== QUIZ RESULTS ==========", out)
        self.assertIn("Total Questions: 10", out)
        self.assertIn("Invalid choice", out)
        self.assertIn("========== REVIEW ANSWERS ==========", out)
        self.assertIn("Your answer:", out)
        self.assertIn("Score:", out)          # previous results screen
        correct = out.count("\nCorrect!")
        self.assertIn(f"Correct Answers: {correct}", out)
        self.assertIn(f"Incorrect Answers: {10 - correct}", out)
        self.assertIn(f"Percentage: {format_percent(correct * 10)}%", out)

    def test_chinese_quiz_quit_early_after_confirmation(self):
        out = run_app(["2", "1", "1", "A", "", "B", "", "q", "n", "C", "", "Q", "y", "3", "8"],
                      "--seed", "3", "--history-file", self.history)
        self.assertIn("已选择译本：CUVMPS", out)
        self.assertIn("第 1 题，共 10 题", out)
        self.assertIn("继续问答。", out)
        self.assertIn("已作答题数：3", out)
        self.assertIn("未作答（提前退出）：7", out)
        self.assertIn("========== 问答成绩 ==========", out)
        saved = json.loads(Path(self.history).read_text(encoding="utf-8"))["results"]
        self.assertEqual((saved[0]["attempted"], saved[0]["quit_early"], saved[0]["language"]), (3, True, "zh"))

    def test_quit_before_answering_anything(self):
        out = run_app(["1", "1", "1", "q", "y", "", "8"], "--history-file", self.history)
        self.assertIn("Percentage: 0%", out)
        self.assertIn("No questions were answered", out)
        self.assertFalse(Path(self.history).exists())

    def test_small_category_offers_choices(self):
        # Parables (5) + Advanced (3) has only 2 questions -> offered: play 2, or all levels (6)
        out = run_app(["1", "1", "3", "5", "4", "3", "1", "2"] + ["A", ""] * 5 + ["A", "3", "8"], "--no-save")
        self.assertIn("Only 2 question(s) match", out)
        self.assertIn("Include all difficulty levels for this category (6 questions)", out)
        self.assertIn("Question 6 of 6", out)

    def test_history_survives_restart(self):
        run_app(["1", "2", "1"] + ["A", ""] * 9 + ["A", "3", "8"], "--history-file", self.history)
        out = run_app(["1", "2", "6", "", "8"], "--history-file", self.history)
        self.assertIn("ESV", out.split("========== PREVIOUS RESULTS ==========")[1])

    def test_missing_question_bank_is_reported(self):
        out = run_app(["1", "1", "1", "8"], "--no-save", "--data-dir", self.tmp.name)
        self.assertIn("The question bank is not available", out)
        self.assertIn("========== MAIN MENU ==========", out)

    def test_change_language_and_back_navigation(self):
        out = run_app(["1", "0", "2", "1", "7", "0", "7", "1", "3", "8"], "--no-save")
        self.assertIn("已选择译本：CUVMPS", out)
        self.assertIn("Selected translation: NLT", out)

    def test_end_of_input_exits_cleanly(self):
        out = run_app(["1"], "--no-save")
        self.assertIn("God bless you", out)


if __name__ == "__main__":
    unittest.main()
