"""Tests for the AI book quiz. The Claude API is replaced by fake responses, so these
tests need no internet and no API key."""
from __future__ import annotations

import builtins
import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from quiz_app.ai_generator import (API_VERSION, ClaudeGenerator, GenerationError,  # noqa: E402
                                   GenerationResult, OllamaGenerator,
                                   validate_generated)
from quiz_app.ai_generator import make_generator as make_engine                     # noqa: E402
from quiz_app.app import QuizApp                                                    # noqa: E402
from quiz_app.bible_books import find_book, load_books                              # noqa: E402
from quiz_app.history import HistoryStore                                           # noqa: E402

DATA_DIR = PROJECT_DIR / "data"
BOOKS = load_books(DATA_DIR)
RUTH = find_book(BOOKS, "Ruth")


def item(n: int, chapter: int = 1, start: int = 4, end: int = 4, **overrides) -> dict:
    data = {
        "question": f"Sample question {n}?", "option_a": f"right {n}", "option_b": f"wrong1 {n}",
        "option_c": f"wrong2 {n}", "option_d": f"wrong3 {n}", "correct_answer": "A",
        "chapter": chapter, "verse_start": start, "verse_end": end, "explanation": "Because.",
    }
    data.update(overrides)
    return data


def api_reply(items, stop_reason="end_turn") -> str:
    return json.dumps({"type": "message", "stop_reason": stop_reason,
                       "content": [{"type": "text", "text": json.dumps({"questions": items})}]})


class FakeTransport:
    """Records each request and replays canned (status, body) replies."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.requests = []

    def __call__(self, url, headers, body, timeout):
        self.requests.append((url, headers, json.loads(body)))
        return self.replies.pop(0)


def make_generator(*replies):
    transport = FakeTransport(*replies)
    return ClaudeGenerator("test-key", model="test-model", transport=transport,
                           sleep=lambda s: None), transport


class BookDataTests(unittest.TestCase):
    def test_book_list(self):
        self.assertEqual(len(BOOKS), 66)
        self.assertEqual(sum(b.chapters for b in BOOKS), 1189)
        self.assertEqual(BOOKS[18].en, "Psalms")
        self.assertEqual(BOOKS[18].chapters, 150)

    def test_find_book(self):
        self.assertEqual(find_book(BOOKS, "9").en, "1 Samuel")
        self.assertEqual(find_book(BOOKS, "1samuel").en, "1 Samuel")
        self.assertEqual(find_book(BOOKS, " 1 SAMUEL ").en, "1 Samuel")
        self.assertEqual(find_book(BOOKS, "创世记").en, "Genesis")
        self.assertEqual(find_book(BOOKS, "启示").en, "Revelation")
        self.assertEqual(find_book(BOOKS, "gen").en, "Genesis")
        for bad in ("0", "67", "", "j", "xyz"):          # "j" matches several books
            self.assertIsNone(find_book(BOOKS, bad), bad)

    def test_reference_exists(self):
        genesis = BOOKS[0]
        self.assertTrue(genesis.reference_exists(50, 26, 26))
        self.assertFalse(genesis.reference_exists(51, 1, 1))
        self.assertFalse(genesis.reference_exists(1, 32, 32))   # Genesis 1 has 31 verses
        self.assertFalse(genesis.reference_exists(1, 5, 3))
        self.assertFalse(genesis.reference_exists(0, 1, 1))


class GeneratorTests(unittest.TestCase):
    def test_request_format(self):
        generator, transport = make_generator((200, api_reply([item(n) for n in range(1, 14)])))
        result = generator.generate(RUTH, "en", "ESV", "easy", 10, avoid=["Old question?"])
        self.assertEqual(len(result.questions), 10)
        url, headers, body = transport.requests[0]
        self.assertEqual(url, "https://api.anthropic.com/v1/messages")
        self.assertEqual(headers["anthropic-version"], API_VERSION)
        self.assertEqual(headers["x-api-key"], "test-key")
        self.assertEqual(body["model"], "test-model")
        self.assertEqual(body["output_config"]["format"]["type"], "json_schema")
        self.assertNotIn("temperature", body)          # removed in API version 2026-10-21
        self.assertIn("Ruth", body["system"])
        self.assertIn("Write 13 easy questions", body["messages"][0]["content"])
        self.assertIn("Old question?", body["messages"][0]["content"])

    def test_questions_are_built_correctly(self):
        generator, _ = make_generator((200, api_reply([item(1, chapter=1, start=16, end=17)])))
        q = generator.generate(RUTH, "zh", "CUVMPS", "advanced", 10).questions[0]
        self.assertEqual((q.book, q.chapter_verse, q.correct_answer), ("路得记", "1:16-17", "A"))
        self.assertEqual((q.language, q.translations, q.difficulty), ("zh", ("CUVMPS",), "advanced"))

    def test_bad_questions_are_rejected(self):
        items = [
            item(1),
            item(2, chapter=5),                      # Ruth has only 4 chapters
            item(3, chapter=1, start=23, end=23),    # Ruth 1 has 22 verses
            item(4, option_b="right 4"),             # duplicate option
            item(5, correct_answer="E"),
            item(6, question=""),
            {k: v for k, v in item(7).items() if k != "explanation"},
            item(1),                                 # repeats question 1
            item(8, question="Asked before?"),
            "not an object",
        ]
        questions, rejected = validate_generated(items, RUTH, "en", "NIV", "easy", ["asked before?"])
        self.assertEqual([q.question for q in questions], ["Sample question 1?"])
        self.assertEqual(rejected, 9)

    def test_retry_then_success(self):
        generator, transport = make_generator((529, '{"error":{"message":"Overloaded"}}'),
                                              (200, api_reply([item(1)])))
        self.assertEqual(len(generator.generate(RUTH, "en", "NIV", "easy", 10).questions), 1)
        self.assertEqual(len(transport.requests), 2)

    def test_errors(self):
        cases = [
            ([(401, '{"error":{"message":"invalid x-api-key"}}')], "auth"),
            ([(404, '{"error":{"message":"model not found"}}')], "model"),
            ([(400, '{"error":{"message":"bad"}}')], "bad_request"),
            ([(429, "{}"), (429, "{}")], "rate_limit"),
            ([(503, "{}"), (529, "{}")], "overloaded"),
            ([(200, "not json")], "bad_response"),
            ([(200, api_reply([], stop_reason="refusal"))], "refusal"),
            ([(200, api_reply([], stop_reason="max_tokens"))], "incomplete"),
            ([(200, json.dumps({"content": [{"type": "text", "text": "oops"}]}))], "bad_response"),
            ([(200, api_reply([item(1, chapter=9)]))], "none_valid"),
        ]
        for replies, key in cases:
            generator, _ = make_generator(*replies)
            with self.assertRaises(GenerationError) as ctx:
                generator.generate(RUTH, "en", "NIV", "easy", 10)
            self.assertEqual(ctx.exception.key, key)

    def test_network_errors_become_generation_errors(self):
        def offline(url, headers, body, timeout):
            raise GenerationError("network", "no route")
        generator = ClaudeGenerator("k", transport=offline)
        with self.assertRaises(GenerationError) as ctx:
            generator.generate(RUTH, "en", "NIV", "easy", 10)
        self.assertEqual(ctx.exception.key, "network")


class FakeGenerator:
    """Stands in for QuestionGenerator inside the app."""
    calls = []
    error: GenerationError | None = None

    def __init__(self, engine, model, api_key):
        self.engine, self.api_key = engine, api_key

    def generate(self, book, lang, translation, difficulty, count, avoid):
        FakeGenerator.calls.append((book.en, lang, translation, difficulty, count, list(avoid)))
        if FakeGenerator.error:
            raise FakeGenerator.error
        items = [item(n, chapter=1, start=n, end=n) for n in range(1, count + 1)]
        questions, _ = validate_generated(items, book, lang, translation, difficulty, avoid)
        return GenerationResult(questions=questions, rejected=0)


def run_app_in_process(inputs, api_key="test-key", questions=3, engine="claude"):
    FakeGenerator.calls = []
    feed = iter(inputs)

    def fake_input(prompt=""):
        print(prompt, end="")
        try:
            return next(feed)
        except StopIteration:
            raise EOFError from None

    app = QuizApp(DATA_DIR, HistoryStore(None), questions_per_quiz=questions, seed=1,
                  engine=engine, api_key=api_key, generator_factory=FakeGenerator)
    out = io.StringIO()
    with mock.patch.object(builtins, "input", fake_input), redirect_stdout(out):
        app.run()
    return out.getvalue(), app


class BookQuizAppTests(unittest.TestCase):
    def tearDown(self):
        FakeGenerator.error = None

    def test_full_book_quiz_flow(self):
        out, app = run_app_in_process(
            ["1", "2",                       # English, ESV
             "2", "ruth", "2",               # book quiz: Ruth, intermediate
             "A", "", "B", "", "C",          # three answers
             "3",                            # leave review
             "6", "",                        # previous results
             "2", "Ruth", "1",               # second Ruth quiz: earlier questions passed as 'avoid'
             "q", "y", "",
             "8"])
        self.assertIn("========== QUIZ BY BIBLE BOOK (AI) ==========", out)
        self.assertIn("Writing 3 Intermediate questions about Ruth", out)
        self.assertIn("AI-generated questions: NOT checked by a person", out)
        self.assertIn("Question 3 of 3", out)
        self.assertIn("Reference: Ruth 1:1", out)
        self.assertIn("Reminder: these questions were written by AI", out)
        self.assertIn("Book: Ruth (AI)", out)
        self.assertEqual(FakeGenerator.calls[0][:5], ("Ruth", "en", "ESV", "intermediate", 3))
        self.assertEqual(len(FakeGenerator.calls[1][5]), 3)
        self.assertEqual(app.history.results[0]["category"], "book:Ruth")

    def test_chinese_book_quiz(self):
        out, _ = run_app_in_process(["2", "1", "2", "路得记", "1", "A", "", "A", "", "A", "3", "8"])
        self.assertIn("为《路得记》出 3 道“简单”题目", out)
        self.assertIn("经文出处：路得记 1:1", out)
        self.assertEqual(FakeGenerator.calls[0][1:3], ("zh", "CUVMPS"))

    def test_missing_key_is_requested_and_blank_goes_back(self):
        out, app = run_app_in_process(["1", "1", "2", "1", "1", "", "8"], api_key="")
        self.assertIn("needs an Anthropic API key", out)
        self.assertEqual(FakeGenerator.calls, [])

    def test_pasted_key_is_used_for_the_session(self):
        out, app = run_app_in_process(["1", "1", "2", "1", "1", "pasted-key",
                                       "A", "", "A", "", "A", "3", "8"], api_key="")
        self.assertEqual(app.api_key, "pasted-key")
        self.assertEqual(len(FakeGenerator.calls), 1)

    def test_api_error_returns_to_menu(self):
        FakeGenerator.error = GenerationError("auth", "invalid x-api-key")
        out, app = run_app_in_process(["1", "1", "2", "1", "1", "", "8"])
        self.assertIn("The API key was not accepted", out)
        self.assertEqual(app.api_key, "")              # will ask again next time
        self.assertIn("========== MAIN MENU ==========", out.split("not accepted")[1])

    def test_ollama_engine_needs_no_key(self):
        out, app = run_app_in_process(["1", "1", "2", "Jonah", "1", "A", "", "A", "", "A", "3", "8"],
                                      api_key="", engine="ollama")
        self.assertNotIn("API key", out)
        self.assertIn("with qwen3:8b", out)
        self.assertIn("Running on your computer", out)
        self.assertEqual(FakeGenerator.calls[0][0], "Jonah")

    def test_ollama_errors_are_explained(self):
        FakeGenerator.error = GenerationError("ollama_model_missing", "qwen3:8b")
        out, _ = run_app_in_process(["1", "1", "2", "1", "1", "", "8"], engine="ollama")
        self.assertIn("ollama pull qwen3:8b", out)

    def test_invalid_book_and_back(self):
        out, _ = run_app_in_process(["1", "1", "2", "Hezekiah", "67", "0", "8"])
        self.assertEqual(out.count("Book not found"), 2)
        self.assertEqual(FakeGenerator.calls, [])


if __name__ == "__main__":
    unittest.main()


class OllamaGeneratorTests(unittest.TestCase):
    def ollama_reply(self, items, done_reason="stop"):
        return json.dumps({"model": "qwen3:8b", "done": True, "done_reason": done_reason,
                           "message": {"role": "assistant", "content": json.dumps({"questions": items})}})

    def test_request_format_and_success(self):
        transport = FakeTransport((200, self.ollama_reply([item(n) for n in range(1, 14)])))
        generator = OllamaGenerator(model="qwen3:4b", base_url="http://localhost:11434",
                                    transport=transport)
        result = generator.generate(RUTH, "zh", "CUVMPS", "easy", 10)
        self.assertEqual(len(result.questions), 10)
        url, headers, body = transport.requests[0]
        self.assertEqual(url, "http://localhost:11434/api/chat")
        self.assertEqual(body["model"], "qwen3:4b")
        self.assertFalse(body["stream"])
        self.assertFalse(body["think"])
        self.assertEqual(body["format"]["required"], ["questions"])
        self.assertEqual([m["role"] for m in body["messages"]], ["system", "user"])

    def test_retry_without_think_for_models_that_do_not_support_it(self):
        transport = FakeTransport((400, '{"error":"\\"llama3.2\\" does not support thinking"}'),
                                  (200, self.ollama_reply([item(1)])))
        generator = OllamaGenerator(model="llama3.2", transport=transport)
        self.assertEqual(len(generator.generate(RUTH, "en", "NIV", "easy", 10).questions), 1)
        self.assertNotIn("think", transport.requests[1][2])

    def test_errors(self):
        cases = [
            ([(404, '{"error":"model \'qwen3:8b\' not found"}')], "ollama_model_missing"),
            ([(500, '{"error":"model requires more system memory"}')], "ollama_error"),
            ([(200, self.ollama_reply([], done_reason="length"))], "incomplete"),
            ([(200, "oops")], "bad_response"),
        ]
        for replies, key in cases:
            generator = OllamaGenerator(transport=FakeTransport(*replies))
            with self.assertRaises(GenerationError) as ctx:
                generator.generate(RUTH, "en", "NIV", "easy", 10)
            self.assertEqual(ctx.exception.key, key)

    def test_not_running(self):
        # Nothing listens on this port, so the real network code gets "connection refused".
        generator = OllamaGenerator(base_url="http://127.0.0.1:9", timeout=5)
        with self.assertRaises(GenerationError) as ctx:
            generator.generate(RUTH, "en", "NIV", "easy", 10)
        self.assertEqual(ctx.exception.key, "ollama_not_running")

    def test_against_a_fake_ollama_server(self):
        """Use the real HTTP code against a tiny local server that answers like Ollama."""
        import threading
        from http.server import BaseHTTPRequestHandler, HTTPServer
        reply = self.ollama_reply([item(n) for n in range(1, 6)]).encode("utf-8")
        received = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                received.append((self.path, json.loads(self.rfile.read(int(self.headers["Content-Length"])))))
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(reply)

            def log_message(self, *args):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            generator = OllamaGenerator(base_url=f"127.0.0.1:{server.server_port}", timeout=10)
            result = generator.generate(RUTH, "en", "NIV", "advanced", 10)
        finally:
            server.shutdown()
        self.assertEqual(len(result.questions), 5)
        self.assertEqual(received[0][0], "/api/chat")
        self.assertEqual(received[0][1]["model"], "qwen3:8b")

    def test_make_generator(self):
        self.assertIsInstance(make_engine("ollama"), OllamaGenerator)
        claude = make_engine("claude", None, "key")
        self.assertIsInstance(claude, ClaudeGenerator)
        self.assertEqual(claude.model, "claude-sonnet-5-5")
