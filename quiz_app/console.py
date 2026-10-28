"""Small helpers for reading input and printing in the terminal."""
from __future__ import annotations

import sys


class ExitRequested(Exception):
    """Raised when input ends (Ctrl+D / Ctrl+Z) or the user presses Ctrl+C."""


def configure_utf8() -> None:
    """Ask Python to read and write UTF-8 so Chinese characters display correctly."""
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError, OSError):
            pass  # not a normal text stream (e.g. inside some IDEs) — leave it alone


def ask(prompt: str) -> str:
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        raise ExitRequested from None


def ask_menu(prompt: str, valid: list[str], invalid_message: str) -> str:
    """Keep asking until the user types one of `valid` (e.g. ["1", "2", "0"])."""
    while True:
        choice = ask(prompt).strip()
        if choice in valid:
            return choice
        print(invalid_message)


def ask_yes_no(prompt: str, invalid_message: str) -> bool:
    yes = {"Y", "YES", "是", "Ｙ"}
    no = {"N", "NO", "否", "Ｎ"}
    while True:
        answer = ask(prompt).strip().upper()
        if answer in yes:
            return True
        if answer in no:
            return False
        print(invalid_message)


def ask_secret(prompt: str) -> str:
    """Like ask(), but hides what is typed (for API keys) when running in a real terminal."""
    if not sys.stdin.isatty():
        return ask(prompt)
    import getpass
    try:
        return getpass.getpass(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        raise ExitRequested from None


def pause(prompt: str) -> None:
    ask(prompt)


def print_numbered(items: list[str], start: int = 1) -> None:
    for number, item in enumerate(items, start=start):
        print(f"{number}. {item}")
