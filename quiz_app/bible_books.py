"""The 66 books of the Bible: names, testament and verse counts (from data/bible_books.json)."""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BibleBook:
    number: int                       # 1-66 in canonical order
    en: str                           # English name, e.g. "1 Samuel"
    zh: str                           # Chinese name (CUVMPS), e.g. "撒母耳记上"
    testament: str                    # "OT" or "NT"
    verses_per_chapter: tuple[int, ...]

    def name(self, lang: str) -> str:
        return self.zh if lang == "zh" else self.en

    @property
    def chapters(self) -> int:
        return len(self.verses_per_chapter)

    def reference_exists(self, chapter: int, verse_start: int, verse_end: int) -> bool:
        if not 1 <= chapter <= self.chapters:
            return False
        last_verse = self.verses_per_chapter[chapter - 1]
        return 1 <= verse_start <= verse_end <= last_verse


def load_books(data_dir: Path) -> list[BibleBook]:
    """Load the book list. Raises OSError or ValueError if the file is missing or damaged."""
    raw = json.loads((data_dir / "bible_books.json").read_text(encoding="utf-8"))
    books = [
        BibleBook(number=i, en=b["en"], zh=b["zh"], testament=b["testament"],
                  verses_per_chapter=tuple(int(v) for v in b["verses_per_chapter"]))
        for i, b in enumerate(raw["books"], start=1)
    ]
    if len(books) != 66:
        raise ValueError("bible_books.json must list 66 books")
    return books


def _simplify(text: str) -> str:
    return re.sub(r"[\s.]", "", text).lower()


def find_book(books: list[BibleBook], typed: str) -> BibleBook | None:
    """Find a book by number (\"9\"), English name (\"1 samuel\", \"1samuel\") or Chinese name."""
    typed = typed.strip()
    if typed.isdigit():
        number = int(typed)
        return books[number - 1] if 1 <= number <= len(books) else None
    wanted = _simplify(typed)
    if not wanted:
        return None
    for book in books:
        if wanted in (_simplify(book.en), _simplify(book.zh)):
            return book
    # Allow an unambiguous start of a name, e.g. "gen" or "启示"
    matches = [b for b in books if _simplify(b.en).startswith(wanted) or _simplify(b.zh).startswith(wanted)]
    return matches[0] if len(matches) == 1 else None


def display_width(text: str) -> int:
    """Chinese characters take two columns in a terminal."""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)


def pad(text: str, width: int) -> str:
    return text + " " * max(0, width - display_width(text))
