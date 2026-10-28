"""Generate quiz questions about one Bible book with AI.

Two engines are supported:
  * Ollama  (default) — a free AI model running on your own computer. No key, no account.
                        Install from https://ollama.com and run:  ollama pull qwen3:8b
  * Claude            — Anthropic's online API (paid). Needs ANTHROPIC_API_KEY.

Uses only the Python standard library (urllib), so nothing extra needs installing.

AI-generated questions are NOT checked by a person. The program checks their format and
that each Bible reference exists, but the answers themselves may contain mistakes.
"""
from __future__ import annotations

import json
import os
import socket
import ssl
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable

from .bible_books import BibleBook
from .models import LETTERS, Question

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2026-10-21"
CLAUDE_DEFAULT_MODEL = "claude-sonnet-5-5"
OLLAMA_DEFAULT_MODEL = "qwen3:8b"
OLLAMA_DEFAULT_URL = "http://localhost:11434"
DEFAULT_MODELS = {"ollama": OLLAMA_DEFAULT_MODEL, "claude": CLAUDE_DEFAULT_MODEL}
DEFAULT_MODEL = CLAUDE_DEFAULT_MODEL      # kept for older imports
MAX_TOKENS = 16000
EXTRA_QUESTIONS = 3          # ask for a few spare questions in case some fail the checks
RETRY_STATUSES = (429, 500, 502, 503, 529)

QUESTION_SCHEMA = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "option_a": {"type": "string"},
                    "option_b": {"type": "string"},
                    "option_c": {"type": "string"},
                    "option_d": {"type": "string"},
                    "correct_answer": {"type": "string", "enum": list(LETTERS)},
                    "chapter": {"type": "integer"},
                    "verse_start": {"type": "integer"},
                    "verse_end": {"type": "integer"},
                    "explanation": {"type": "string"},
                },
                "required": ["question", "option_a", "option_b", "option_c", "option_d",
                             "correct_answer", "chapter", "verse_start", "verse_end", "explanation"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["questions"],
    "additionalProperties": False,
}

DIFFICULTY_GUIDE = {
    "easy": "Easy: the best-known stories, people and teachings of this book, which a regular "
            "Sunday-school student would know.",
    "intermediate": "Intermediate: more specific details of this book, such as names, places, "
                    "numbers, the order of events and who said what.",
    "advanced": "Advanced: less familiar details of this book that need careful reading, but "
                "still clearly stated in the text.",
}

LANGUAGE_GUIDE = {
    "en": "Write in English. The facts tested must be the same in the NIV, ESV and NLT. If those "
          "translations use different words for something (e.g. talents / bags of gold), mention "
          "both. Use standard English chapter and verse numbering.",
    "zh": "所有内容用简体中文书写。人名、地名和用语请采用《现代标点和合本》（CUVMPS）的译名，"
          "例如：大马士革、约旦河、撒马利亚、伊利莎白、克里特、埃塞俄比亚、挪亚、摩西、耶和华，"
          "称神为“神”。章节编号采用和合本的编号。",
}


class GenerationError(Exception):
    """Something went wrong. `key` selects a message in strings.py; `detail` adds context."""

    def __init__(self, key: str, detail: str = ""):
        super().__init__(f"{key}: {detail}")
        self.key = key
        self.detail = detail


@dataclass
class GenerationResult:
    questions: list[Question]
    rejected: int                     # how many generated questions failed the checks


Transport = Callable[[str, dict, bytes, float], "tuple[int, str]"]


def post_json(url: str, headers: dict, body: bytes, timeout: float) -> tuple[int, str]:
    """Send the request; return (HTTP status, response text). Network problems raise GenerationError."""
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as err:
        if isinstance(err.reason, ssl.SSLError):
            raise GenerationError("ssl", str(err.reason)) from err
        if isinstance(err.reason, (socket.timeout, TimeoutError)):
            raise GenerationError("timeout") from err
        raise GenerationError("network", str(err.reason)) from err
    except (socket.timeout, TimeoutError) as err:
        raise GenerationError("timeout") from err


def build_system_prompt(book: BibleBook, lang: str, difficulty: str) -> str:
    return "\n".join([
        "You write multiple-choice Bible quiz questions for church groups and Sunday schools. "
        "Accuracy matters more than variety.",
        "",
        "Rules:",
        f"- Every question must be about the book of {book.en} ({book.zh}) only.",
        "- chapter, verse_start and verse_end must point to a passage in that book that directly "
        "states the answer. Use the narrowest range that contains the answer.",
        "- Exactly one option is correct. The other three must be clearly wrong according to the "
        "passage, but plausible. Do not use 'all of the above' or 'none of the above'.",
        "- Test what the text actually says, not later traditions or interpretations "
        "(for example, the Bible does not say how many wise men there were).",
        "- Only include facts you are sure of. Leave out anything uncertain.",
        "- Do not quote any Bible translation word for word; paraphrase in your own words.",
        "- Keep options short. The explanation is one or two sentences.",
        "- Every question must be different from the others and from the 'already asked' list.",
        "",
        DIFFICULTY_GUIDE[difficulty],
        "",
        LANGUAGE_GUIDE[lang],
    ])


def build_user_prompt(book: BibleBook, difficulty: str, count: int, avoid: list[str]) -> str:
    text = f"Write {count} {difficulty} questions about the book of {book.en} ({book.zh})."
    if avoid:
        text += "\n\nAlready asked (do not repeat these):\n" + "\n".join(f"- {q}" for q in avoid)
    return text


class QuestionGenerator:
    """Shared logic: build the prompt, ask the engine, check the questions it returns.

    Engines (ClaudeGenerator, OllamaGenerator) only implement `_complete`, which sends the
    prompt and returns the JSON text of the model's answer.
    """
    engine = "ai"

    def __init__(self, model: str, transport: Transport = post_json, timeout: float = 150,
                 sleep: Callable[[float], None] = time.sleep):
        self.model = model
        self.transport = transport
        self.timeout = timeout
        self.sleep = sleep

    def generate(self, book: BibleBook, lang: str, translation: str, difficulty: str,
                 count: int, avoid: list[str] | None = None) -> GenerationResult:
        system = build_system_prompt(book, lang, difficulty)
        user = build_user_prompt(book, difficulty, count + EXTRA_QUESTIONS, (avoid or [])[-40:])
        text = self._complete(system, user)
        items = parse_question_json(text)
        questions, rejected = validate_generated(items, book, lang, translation, difficulty, avoid or [])
        if not questions:
            raise GenerationError("none_valid")
        return GenerationResult(questions=questions[:count], rejected=rejected)

    def _complete(self, system: str, user: str) -> str:
        raise NotImplementedError


class ClaudeGenerator(QuestionGenerator):
    """Anthropic's Claude API (online, paid, needs an API key)."""
    engine = "claude"

    def __init__(self, api_key: str, model: str = CLAUDE_DEFAULT_MODEL, **kwargs):
        super().__init__(model, **kwargs)
        self.api_key = api_key

    def _complete(self, system: str, user: str) -> str:
        body = {
            "model": self.model,
            "max_tokens": MAX_TOKENS,
            "system": system,
            "messages": [{"role": "user", "content": user}],
            "output_config": {
                "effort": "medium",
                "format": {"type": "json_schema", "schema": QUESTION_SCHEMA},
            },
        }
        data = self._call_api(body)
        stop = data.get("stop_reason")
        if stop == "refusal":
            raise GenerationError("refusal")
        if stop == "max_tokens":
            raise GenerationError("incomplete")
        return "".join(block.get("text", "") for block in data.get("content", [])
                       if isinstance(block, dict) and block.get("type") == "text")

    def _call_api(self, body: dict) -> dict:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": API_VERSION,
            "content-type": "application/json",
        }
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        for attempt in (1, 2):
            status, text = self.transport(API_URL, headers, payload, self.timeout)
            if status == 200:
                try:
                    return json.loads(text)
                except json.JSONDecodeError as err:
                    raise GenerationError("bad_response", "response was not JSON") from err
            if status in RETRY_STATUSES and attempt == 1:
                self.sleep(3)
                continue
            raise _error_for_status(status, text)
        raise GenerationError("bad_response")  # not reached


class OllamaGenerator(QuestionGenerator):
    """A free model running on this computer through Ollama (https://ollama.com)."""
    engine = "ollama"

    def __init__(self, model: str = OLLAMA_DEFAULT_MODEL, base_url: str | None = None,
                 timeout: float = 900, **kwargs):
        # A local model can be slow, especially the first time it loads, so wait up to 15 minutes.
        super().__init__(model, timeout=timeout, **kwargs)
        host = base_url or os.environ.get("OLLAMA_HOST") or OLLAMA_DEFAULT_URL
        if not host.startswith("http"):
            host = "http://" + host
        self.url = host.rstrip("/") + "/api/chat"

    def _complete(self, system: str, user: str) -> str:
        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "stream": False,
            "format": QUESTION_SCHEMA,       # Ollama forces the answer to match this JSON shape
            "think": False,                  # skip "thinking" (much faster on Qwen3)
            "options": {"temperature": 0.7, "num_ctx": 8192},
            "keep_alive": "15m",             # keep the model loaded for the next quiz
        }
        status, text = self._send(body)
        if status != 200 and "think" in text.lower():
            body.pop("think")                # this model has no thinking switch; try without it
            status, text = self._send(body)
        if status != 200:
            raise _ollama_error(status, text, self.model)
        try:
            data = json.loads(text)
        except json.JSONDecodeError as err:
            raise GenerationError("bad_response", "response was not JSON") from err
        if data.get("done_reason") == "length":
            raise GenerationError("incomplete")
        message = data.get("message") or {}
        return message.get("content", "")

    def _send(self, body: dict) -> tuple[int, str]:
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers = {"content-type": "application/json"}
        try:
            return self.transport(self.url, headers, payload, self.timeout)
        except GenerationError as err:
            if err.key == "network":
                raise GenerationError("ollama_not_running", self.url) from err
            raise


def make_generator(engine: str, model: str | None = None, api_key: str = "") -> QuestionGenerator:
    if engine == "claude":
        return ClaudeGenerator(api_key=api_key, model=model or CLAUDE_DEFAULT_MODEL)
    return OllamaGenerator(model=model or OLLAMA_DEFAULT_MODEL)


def parse_question_json(text: str) -> list:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as err:
        raise GenerationError("bad_response", "the questions were not valid JSON") from err
    items = parsed.get("questions") if isinstance(parsed, dict) else None
    if not isinstance(items, list):
        raise GenerationError("bad_response", "no question list in the response")
    return items


def _ollama_error(status: int, text: str, model: str) -> GenerationError:
    try:
        message = str(json.loads(text).get("error", text))
    except (ValueError, AttributeError):
        message = text[:200]
    if status == 404 or "not found" in message.lower():
        return GenerationError("ollama_model_missing", model)
    return GenerationError("ollama_error", f"HTTP {status}: {message}")


def _error_for_status(status: int, text: str) -> GenerationError:
    try:
        message = json.loads(text)["error"]["message"]
    except (ValueError, KeyError, TypeError):
        message = text[:200]
    if status == 401:
        return GenerationError("auth", message)
    if status == 403:
        return GenerationError("permission", message)
    if status == 404:
        return GenerationError("model", message)
    if status == 429:
        return GenerationError("rate_limit", message)
    if status >= 500:
        return GenerationError("overloaded", f"HTTP {status}")
    return GenerationError("bad_request", f"HTTP {status}: {message}")


def validate_generated(items: list, book: BibleBook, lang: str, translation: str,
                       difficulty: str, avoid: list[str]) -> tuple[list[Question], int]:
    """Keep only well-formed questions whose reference exists in the chosen book."""
    seen = {q.strip().lower() for q in avoid}
    questions: list[Question] = []
    rejected = 0
    for item in items:
        question = _to_question(item, book, lang, translation, difficulty, len(questions) + 1)
        if question is None or question.question.lower() in seen:
            rejected += 1
            continue
        seen.add(question.question.lower())
        questions.append(question)
    return questions, rejected


def _to_question(item, book: BibleBook, lang: str, translation: str,
                 difficulty: str, number: int) -> Question | None:
    if not isinstance(item, dict):
        return None
    texts = {key: item.get(key) for key in ("question", "option_a", "option_b", "option_c",
                                             "option_d", "explanation")}
    if any(not isinstance(v, str) or not v.strip() for v in texts.values()):
        return None
    options = {letter: texts[f"option_{letter.lower()}"].strip() for letter in LETTERS}
    if len({o.lower() for o in options.values()}) != 4:
        return None
    correct = str(item.get("correct_answer", "")).strip().upper()
    if correct not in LETTERS:
        return None
    try:
        chapter, start, end = int(item["chapter"]), int(item["verse_start"]), int(item["verse_end"])
    except (KeyError, TypeError, ValueError):
        return None
    if not book.reference_exists(chapter, start, end):
        return None
    chapter_verse = f"{chapter}:{start}" if start == end else f"{chapter}:{start}-{end}"
    return Question(
        id=f"AI-{book.number:02d}-{number:02d}",
        language=lang,
        translations=(translation,),
        category="book",
        difficulty=difficulty,
        question=texts["question"].strip(),
        options=options,
        correct_answer=correct,
        book=book.name(lang),
        chapter_verse=chapter_verse,
        explanation=texts["explanation"].strip(),
        shuffle_options=True,
        verified=False,
    )
