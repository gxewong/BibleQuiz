"""Simple data structures used throughout the quiz."""
from __future__ import annotations

from dataclasses import dataclass, field

LETTERS = ("A", "B", "C", "D")


@dataclass(frozen=True)
class Question:
    """One question as stored in the question bank (data/*.json)."""
    id: str
    language: str
    translations: tuple[str, ...]
    category: str
    difficulty: str
    question: str
    options: dict[str, str]          # {"A": "...", "B": "...", "C": "...", "D": "..."}
    correct_answer: str              # "A", "B", "C" or "D"
    book: str
    chapter_verse: str
    explanation: str
    source_text: dict[str, str] = field(default_factory=dict)  # {"ESV": "licensed quotation"}
    shuffle_options: bool = True
    verified: bool = False

    @property
    def reference(self) -> str:
        return f"{self.book} {self.chapter_verse}".strip()


@dataclass
class PresentedQuestion:
    """A question as shown in one quiz: options may be in a shuffled order."""
    question: Question
    options: list[tuple[str, str]]   # [("A", "Noah"), ("B", "Moses"), ...] in display order
    correct_letter: str              # display letter of the correct option

    def option_text(self, letter: str) -> str:
        return dict(self.options)[letter]


@dataclass
class AnswerRecord:
    presented: PresentedQuestion
    selected_letter: str
    is_correct: bool


@dataclass
class QuizResult:
    total_questions: int     # questions planned for the quiz
    attempted: int           # questions actually answered
    correct: int
    incorrect: int
    percentage: float        # correct / attempted * 100 (0 when nothing was attempted)
    quit_early: bool
    answers: list[AnswerRecord] = field(default_factory=list)

    @property
    def unanswered(self) -> int:
        return self.total_questions - self.attempted
