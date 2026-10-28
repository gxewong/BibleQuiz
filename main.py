"""Bilingual Bible Quiz — console application.

Run from this folder:
    python main.py

Options:
    --no-save            keep quiz history for this session only (no file is written)
    --history-file PATH  where to save quiz history (default: results/quiz_history.json)
    --data-dir PATH      folder containing questions_en.json and questions_zh.json
    --questions N        number of questions per quiz (default: 10)
    --seed N             fixed random seed (repeatable question order, useful for testing)
    --ai ENGINE          AI for "Quiz by Bible Book": ollama (default, free, on this
                         computer) or claude (online, needs an Anthropic API key)
    --model NAME         AI model (default: qwen3:8b for ollama, claude-sonnet-5-5 for claude)

Ollama setup (once):  install from https://ollama.com, then run:  ollama pull qwen3:8b
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if sys.version_info < (3, 9):
    sys.exit("This program needs Python 3.9 or newer.")

import os

from quiz_app.app import QuizApp
from quiz_app.console import configure_utf8
from quiz_app.history import HistoryStore

PROJECT_DIR = Path(__file__).resolve().parent


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be 1 or more")
    return number


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bilingual Bible Quiz (English / 中文)")
    parser.add_argument("--data-dir", type=Path, default=PROJECT_DIR / "data")
    parser.add_argument("--history-file", type=Path, default=PROJECT_DIR / "results" / "quiz_history.json")
    parser.add_argument("--no-save", action="store_true", help="do not save history to a file")
    parser.add_argument("--questions", type=positive_int, default=10, help="questions per quiz")
    parser.add_argument("--seed", type=int, default=None, help="random seed for repeatable quizzes")
    parser.add_argument("--ai", choices=("ollama", "claude"),
                        default=os.environ.get("BIBLE_QUIZ_AI", "ollama"),
                        help="AI engine for the book quiz (default: ollama)")
    parser.add_argument("--model", default=os.environ.get("BIBLE_QUIZ_MODEL"),
                        help="AI model name, e.g. qwen3:4b")
    return parser.parse_args(argv)


def main(argv=None) -> None:
    configure_utf8()
    args = parse_args(argv)
    history = HistoryStore(None if args.no_save else args.history_file)
    app = QuizApp(data_dir=args.data_dir, history=history,
                  questions_per_quiz=args.questions, seed=args.seed,
                  engine=args.ai, model=args.model)
    app.run()


if __name__ == "__main__":
    main()
