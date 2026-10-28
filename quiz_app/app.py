"""The interactive console application: menus, quiz session, results and review."""
from __future__ import annotations

import os
import random
from collections import defaultdict
from pathlib import Path

from . import console
from .ai_generator import DEFAULT_MODELS, GenerationError, make_generator
from .bible_books import BibleBook, display_width, find_book, load_books, pad
from .console import ExitRequested
from .history import HistoryStore
from .models import QuizResult
from .question_bank import QuestionBank, bank_path, filter_questions, load_questions
from .quiz_engine import (calculate_score, check_answer, format_percent, normalize_answer,
                          performance_key, pick_questions, prepare_question)
from .strings import (CATEGORY_HINTS, CATEGORY_KEYS, CATEGORY_NAMES, DIFFICULTY_DESCRIPTIONS,
                      DIFFICULTY_KEYS, DIFFICULTY_NAMES, LANGUAGE_CANCEL, LANGUAGE_INPUT,
                      LANGUAGE_INVALID, LANGUAGE_PROMPT, LANGUAGES, MIXED, TEXT, TRANSLATIONS,
                      t, translation_name)

HISTORY_DISPLAY_LIMIT = 20


class QuizApp:
    def __init__(self, data_dir: Path, history: HistoryStore,
                 questions_per_quiz: int = 10, seed: int | None = None,
                 engine: str = "ollama", model: str | None = None, api_key: str | None = None,
                 generator_factory=make_generator):
        self.data_dir = data_dir
        self.history = history
        self.questions_per_quiz = questions_per_quiz
        self.rng = random.Random(seed)
        self.banks: dict[str, QuestionBank] = {}
        self.lang = "en"
        self.translation = "NIV"
        self.category = MIXED
        self.difficulty = "easy"
        # Book quiz (AI). engine is "ollama" (free, on this computer) or "claude" (online, paid).
        # A Claude API key is kept in memory only, never written to disk.
        self.engine = engine
        self.model = model or DEFAULT_MODELS[engine]
        self.api_key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY", "").strip()
        self.generator_factory = generator_factory
        self.books: list[BibleBook] | None = None
        self.ai_asked: dict[tuple, list[str]] = defaultdict(list)   # avoid repeats in a session

    # ------------------------------------------------------------------ helpers
    def tr(self, key: str, **values) -> str:
        return t(self.lang, key, **values)

    def category_name(self, key: str, lang: str | None = None) -> str:
        return CATEGORY_NAMES[lang or self.lang].get(key, key)

    def difficulty_name(self, key: str, lang: str | None = None) -> str:
        return DIFFICULTY_NAMES[lang or self.lang].get(key, key)

    def invalid(self, choices: list[str]) -> str:
        return self.tr("invalid_choice", options=", ".join(choices))

    def bank(self) -> QuestionBank:
        """Load the current language's question bank once and reuse it."""
        if self.lang not in self.banks:
            bank = load_questions(self.data_dir, self.lang)
            self.banks[self.lang] = bank
            if bank.skipped:
                print(self.tr("bank_warning", count=len(bank.skipped),
                              file=bank_path(self.data_dir, self.lang).name))
                for reason in bank.skipped:
                    print(f"  - {reason}")
        return self.banks[self.lang]

    def show_history_warnings(self) -> None:
        for warning in self.history.pop_warnings():
            print(self.tr("history_warning", detail=warning))

    # ------------------------------------------------------------------ main loop
    def run(self) -> None:
        try:
            print("=" * 44)
            print("        BIBLE QUIZ  /  圣经问答")
            print("=" * 44)
            self.show_history_warnings()
            self.select_language_and_translation(first_time=True)
            self.main_menu_loop()
        except ExitRequested:
            pass
        print()
        print(self.tr("goodbye"))

    def main_menu_loop(self) -> None:
        actions = {
            "1": self.run_quiz,
            "2": self.run_book_quiz,
            "3": self.select_category,
            "4": self.select_difficulty,
            "5": self.show_instructions,
            "6": self.show_history,
            "7": lambda: self.select_language_and_translation(first_time=False),
        }
        valid = [str(n) for n in range(1, 9)]
        while True:
            self.display_menu()
            choice = console.ask_menu(self.tr("menu_prompt"), valid, self.invalid(valid))
            if choice == "8":
                return
            actions[choice]()

    def display_menu(self) -> None:
        print()
        print(self.tr("menu_title"))
        print(self.tr("settings_line", translation=self.translation,
                      category=self.category_name(self.category),
                      difficulty=self.difficulty_name(self.difficulty)))
        print()
        console.print_numbered(self.tr("menu_items").split("|"))
        print()

    # ------------------------------------------------------------------ settings
    def select_language_and_translation(self, first_time: bool) -> None:
        while True:
            lang = self.select_language(allow_cancel=not first_time)
            if lang is None:          # cancelled: keep current settings
                return
            old_lang = self.lang
            self.lang = lang
            translation = self.select_translation()
            if translation is not None:
                self.translation = translation
                print(self.tr("selected_translation", code=translation,
                              name=translation_name(translation, self.lang)))
                return
            if not first_time:
                self.lang = old_lang  # went back: restore and ask for language again

    def select_language(self, allow_cancel: bool) -> str | None:
        print()
        print(LANGUAGE_PROMPT, end="")
        valid = ["1", "2"]
        if allow_cancel:
            print(LANGUAGE_CANCEL)
            valid.append("0")
        print()
        choice = console.ask_menu(LANGUAGE_INPUT, valid, LANGUAGE_INVALID)
        if choice == "0":
            return None
        return LANGUAGES[int(choice) - 1]

    def select_translation(self) -> str | None:
        """Returns the translation code, or None if the user chose Back."""
        options = TRANSLATIONS[self.lang]
        print()
        print(self.tr("translation_title"))
        print()
        for number, (code, names) in enumerate(options, start=1):
            print(f"{number}. {code} — {names[self.lang]}")
        print(f"0. {self.tr('back')}")
        print()
        valid = [str(n) for n in range(len(options) + 1)]
        choice = console.ask_menu(self.tr("enter_choice"), valid, self.invalid(valid))
        if choice == "0":
            return None
        return options[int(choice) - 1][0]

    def select_category(self) -> None:
        questions = self.bank().questions
        print()
        print(self.tr("category_title"))
        print()
        for number, key in enumerate(CATEGORY_KEYS, start=1):
            count = len(filter_questions(questions, self.translation, key, None))
            hint = CATEGORY_HINTS[self.lang].get(key)
            label = self.category_name(key) + (f" — {hint}" if hint else "")
            print(f"{number:>2}. {label} {self.tr('count_suffix', count=count)}")
        print(f" 0. {self.tr('back')}")
        print()
        valid = [str(n) for n in range(len(CATEGORY_KEYS) + 1)]
        choice = console.ask_menu(self.tr("enter_choice"), valid, self.invalid(valid))
        if choice != "0":
            self.category = CATEGORY_KEYS[int(choice) - 1]
            print(self.tr("category_set", name=self.category_name(self.category)))

    def select_difficulty(self) -> None:
        questions = self.bank().questions
        print()
        print(self.tr("difficulty_title"))
        print()
        for number, key in enumerate(DIFFICULTY_KEYS, start=1):
            count = len(filter_questions(questions, self.translation, self.category, key))
            print(f"{number}. {self.difficulty_name(key)} — {DIFFICULTY_DESCRIPTIONS[self.lang][key]} "
                  f"{self.tr('count_suffix', count=count)}")
        print(f"0. {self.tr('back')}")
        print()
        valid = [str(n) for n in range(len(DIFFICULTY_KEYS) + 1)]
        choice = console.ask_menu(self.tr("enter_choice"), valid, self.invalid(valid))
        if choice != "0":
            self.difficulty = DIFFICULTY_KEYS[int(choice) - 1]
            print(self.tr("difficulty_set", name=self.difficulty_name(self.difficulty)))

    def show_instructions(self) -> None:
        print()
        print(self.tr("instructions_title"))
        print(self.tr("instructions", count=self.questions_per_quiz))
        print()
        console.pause(self.tr("press_enter"))

    # ------------------------------------------------------------------ quiz
    def choose_question_pool(self):
        """Return (questions, difficulty_label_key) for the quiz, or None to go back."""
        bank = self.bank()
        if bank.error:
            print(self.tr("bank_missing", detail=bank.error))
            return None
        if not filter_questions(bank.questions, self.translation, MIXED, None):
            print(self.tr("bank_empty"))
            return None

        category = self.category_name(self.category)
        difficulty = self.difficulty_name(self.difficulty)
        pool = filter_questions(bank.questions, self.translation, self.category, self.difficulty)
        if len(pool) >= self.questions_per_quiz:
            return pool, self.difficulty

        all_levels = filter_questions(bank.questions, self.translation, self.category, None)
        if not pool and not all_levels:
            print(self.tr("no_match", category=category, difficulty=difficulty))
            print(self.tr("try_other"))
            return None

        print()
        print(self.tr("insufficient", available=len(pool), category=category,
                      difficulty=difficulty, wanted=self.questions_per_quiz))
        choices = []
        if pool:
            choices.append(("play", self.tr("insufficient_play", available=len(pool))))
        if len(all_levels) > len(pool):
            choices.append(("all", self.tr("insufficient_all_levels", count=len(all_levels))))
        for number, (_, label) in enumerate(choices, start=1):
            print(f"{number}. {label}")
        print(f"0. {self.tr('back')}")
        valid = [str(n) for n in range(len(choices) + 1)]
        choice = console.ask_menu(self.tr("enter_choice"), valid, self.invalid(valid))
        if choice == "0":
            return None
        if choices[int(choice) - 1][0] == "play":
            return pool, self.difficulty
        return all_levels, "all"

    def run_quiz(self) -> None:
        chosen = self.choose_question_pool()
        if chosen is None:
            return
        pool, difficulty_key = chosen
        questions = pick_questions(pool, self.questions_per_quiz, self.rng)
        difficulty_label = (self.difficulty_name(self.difficulty) if difficulty_key != "all"
                            else self.tr("all_levels"))
        self.run_session(questions, self.category_name(self.category), difficulty_label,
                         history_category=self.category,
                         history_difficulty="all" if difficulty_key == "all" else self.difficulty)

    def run_session(self, questions, category_label: str, difficulty_label: str,
                    history_category: str, history_difficulty: str, ai: bool = False) -> None:
        """Ask the questions, show results, save to history and offer a review."""
        print()
        print("=" * 44)
        print(self.tr("quiz_start", translation=f"{self.translation} — "
                      f"{translation_name(self.translation, self.lang)}"))
        print(self.tr("quiz_settings", category=category_label,
                      difficulty=difficulty_label, count=len(questions)))
        print(self.tr("ai_notice") if ai else self.tr("quiz_note"))
        print("=" * 44)

        answers = []
        quit_early = False
        for number, question in enumerate(questions, start=1):
            presented = prepare_question(question, self.rng)
            print()
            print(self.tr("question_header", number=number, total=len(questions)))
            print(question.question)
            for letter, text in presented.options:
                print(f"{letter}. {text}")

            selected = self.ask_answer()
            if selected is None:
                quit_early = True
                break
            record = check_answer(presented, selected)
            answers.append(record)
            self.show_feedback(record)
            if number < len(questions):
                console.pause(self.tr("press_enter"))

        result = calculate_score(answers, len(questions), quit_early)
        self.display_results(result)
        if ai:
            print(self.tr("ai_results_note"))
            print()
        if result.attempted:
            saved = self.history.add(result, self.lang, self.translation,
                                     history_category, history_difficulty)
            if saved:
                print(self.tr("result_saved"))
            self.show_history_warnings()
            self.review_answers(result)
        else:
            console.pause(self.tr("press_enter"))

    # ------------------------------------------------------------------ book quiz (AI)
    def bible_books(self) -> list[BibleBook] | None:
        if self.books is None:
            try:
                self.books = load_books(self.data_dir)
            except (OSError, ValueError, KeyError) as err:
                print(self.tr("books_missing", detail=err))
                return None
        return self.books

    def run_book_quiz(self) -> None:
        books = self.bible_books()
        if books is None:
            return
        book = self.select_book(books)
        if book is None:
            return
        difficulty = self.select_book_difficulty(book)
        if difficulty is None:
            return
        if self.engine == "claude" and not self.ensure_api_key():
            return

        wanted = self.questions_per_quiz
        print()
        print(self.tr("ai_generating", count=wanted, book=book.name(self.lang),
                      difficulty=self.difficulty_name(difficulty), model=self.model))
        if self.engine == "ollama":
            print(self.tr("ai_generating_local"))
        asked = self.ai_asked[(self.lang, book.number)]
        generator = self.generator_factory(self.engine, self.model, self.api_key)
        try:
            generated = generator.generate(book, self.lang, self.translation, difficulty, wanted, asked)
        except GenerationError as err:
            print(self.tr(f"ai_error_{err.key}", detail=err.detail, model=self.model))
            if err.key == "auth":
                self.api_key = ""          # ask for the key again next time
            console.pause(self.tr("press_enter"))
            return

        questions = generated.questions
        if len(questions) < wanted:
            print(self.tr("ai_fewer", count=len(questions), wanted=wanted))
        asked.extend(q.question for q in questions)
        self.run_session(questions, self.tr("book_label", book=book.name(self.lang)),
                         self.difficulty_name(difficulty),
                         history_category=f"book:{book.en}", history_difficulty=difficulty, ai=True)

    def select_book(self, books: list[BibleBook]) -> BibleBook | None:
        width = max(display_width(b.name(self.lang)) for b in books)
        print()
        print(self.tr("book_title"))
        for testament, title_key in (("OT", "old_testament"), ("NT", "new_testament")):
            print()
            print(f"[{self.category_name(title_key)}]")
            group = [b for b in books if b.testament == testament]
            for row_start in range(0, len(group), 4):
                row = group[row_start:row_start + 4]
                print("  ".join(pad(f"{b.number:>2}. {b.name(self.lang)}", width + 4) for b in row).rstrip())
        print()
        print(self.tr("book_hint"))
        while True:
            typed = console.ask(self.tr("book_prompt")).strip()
            if typed == "0":
                return None
            book = find_book(books, typed)
            if book is not None:
                return book
            print(self.tr("book_invalid"))

    def select_book_difficulty(self, book: BibleBook) -> str | None:
        print()
        print(self.tr("book_difficulty_title", book=book.name(self.lang)))
        print()
        for number, key in enumerate(DIFFICULTY_KEYS, start=1):
            print(f"{number}. {self.difficulty_name(key)} — {DIFFICULTY_DESCRIPTIONS[self.lang][key]}")
        print(f"0. {self.tr('back')}")
        print()
        valid = [str(n) for n in range(len(DIFFICULTY_KEYS) + 1)]
        choice = console.ask_menu(self.tr("enter_choice"), valid, self.invalid(valid))
        return None if choice == "0" else DIFFICULTY_KEYS[int(choice) - 1]

    def ensure_api_key(self) -> bool:
        if self.api_key:
            return True
        print()
        print(self.tr("ai_key_needed"))
        key = console.ask_secret(self.tr("ai_key_prompt")).strip()
        if not key:
            return False
        self.api_key = key
        return True

    def ask_answer(self) -> str | None:
        """Return the chosen letter, or None if the user confirmed quitting."""
        while True:
            answer = normalize_answer(console.ask(self.tr("answer_prompt")))
            if answer is None:
                print(self.tr("invalid_answer"))
            elif answer == "Q":
                if console.ask_yes_no(self.tr("confirm_quit"), self.tr("invalid_yes_no")):
                    return None
                print(self.tr("continue_quiz"))
            else:
                return answer

    def show_feedback(self, record) -> None:
        presented = record.presented
        question = presented.question
        print()
        if record.is_correct:
            print(self.tr("correct"))
        else:
            print(self.tr("incorrect"))
            print(self.tr("correct_answer_is", letter=presented.correct_letter,
                          text=presented.option_text(presented.correct_letter)))
        self.print_reference_and_explanation(question)

    def print_reference_and_explanation(self, question) -> None:
        print(self.tr("reference", reference=question.reference))
        print(self.tr("explanation", text=question.explanation))
        quotation = question.source_text.get(self.translation)
        if quotation:   # shown only if a licensed quotation for THIS translation was added
            print(self.tr("source_text", translation=self.translation, text=quotation))

    def display_results(self, result: QuizResult) -> None:
        print()
        print(self.tr("results_title"))
        print(self.tr("total_questions", total=result.total_questions))
        if result.quit_early:
            print(self.tr("attempted", attempted=result.attempted))
        print(self.tr("correct_answers", correct=result.correct))
        print(self.tr("incorrect_answers", incorrect=result.incorrect))
        if result.quit_early:
            print(self.tr("unanswered", count=result.unanswered))
        print(self.tr("final_score", correct=result.correct, attempted=result.attempted))
        print(self.tr("percentage", percent=format_percent(result.percentage)))
        print(self.tr(performance_key(result)))
        print()

    # ------------------------------------------------------------------ review & history
    def review_answers(self, result: QuizResult) -> None:
        while True:
            print()
            print(self.tr("review_title"))
            console.print_numbered(self.tr("review_items").split("|"))
            print()
            choice = console.ask_menu(self.tr("enter_choice"), ["1", "2", "3"],
                                      self.invalid(["1", "2", "3"]))
            if choice == "3":
                return
            records = result.answers if choice == "1" else [a for a in result.answers if not a.is_correct]
            if not records:
                print(self.tr("no_incorrect"))
                continue
            for record in records:
                self.print_review_entry(result.answers.index(record) + 1, len(result.answers), record)
            console.pause(self.tr("press_enter"))

    def print_review_entry(self, number: int, total: int, record) -> None:
        presented = record.presented
        tag = self.tr("review_correct_tag" if record.is_correct else "review_incorrect_tag")
        print()
        print(f"{self.tr('question_header', number=number, total=total)} {tag}")
        print(presented.question.question)
        print(self.tr("your_answer", letter=record.selected_letter,
                      text=presented.option_text(record.selected_letter)))
        print(self.tr("correct_answer_is", letter=presented.correct_letter,
                      text=presented.option_text(presented.correct_letter)))
        self.print_reference_and_explanation(presented.question)

    def history_category_label(self, category: str) -> str:
        if category.startswith("book:"):
            english_name = category[5:]
            books = self.books or []
            if not books:
                try:
                    books = load_books(self.data_dir)
                except (OSError, ValueError, KeyError):
                    books = []
            name = next((b.name(self.lang) for b in books if b.en == english_name), english_name)
            return self.tr("book_label", book=name) + " (AI)"
        return self.category_name(category)

    def show_history(self) -> None:
        print()
        print(self.tr("history_title"))
        entries = self.history.results
        if not entries:
            print(self.tr("history_empty"))
        else:
            recent = list(reversed(entries))[:HISTORY_DISPLAY_LIMIT]
            for entry in recent:
                language = TEXT[self.lang]["language_names"].split("|")[
                    LANGUAGES.index(entry["language"]) if entry["language"] in LANGUAGES else 0]
                difficulty = (self.tr("all_levels") if entry["difficulty"] == "all"
                              else self.difficulty_name(entry["difficulty"]))
                print(self.tr("history_entry", date=entry["date"], language=language,
                              translation=entry["translation"],
                              category=self.history_category_label(entry["category"]),
                              difficulty=difficulty))
                quit_note = (self.tr("history_quit_note", attempted=entry["attempted"],
                                     total=entry["total_questions"]) if entry["quit_early"] else "")
                print(self.tr("history_score", correct=entry["correct"], attempted=entry["attempted"],
                              percent=format_percent(entry["percentage"]), quit_note=quit_note))
            if len(entries) > HISTORY_DISPLAY_LIMIT:
                print(self.tr("history_showing", shown=HISTORY_DISPLAY_LIMIT, total=len(entries)))
        print()
        console.pause(self.tr("press_enter"))
