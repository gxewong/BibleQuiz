# Bilingual Bible Quiz (English / 中文)

A console Bible quiz for church activities, Bible study groups, Sunday school, youth
fellowships and personal practice. It runs entirely in the terminal: no website, no GUI,
no server.

**Quick links:** [Run the quiz](#4-running) · [How to play](#5-how-to-play) ·
[AI book quiz with Ollama (free)](docs/OLLAMA_GUIDE.md) · [Add questions](#8-adding-or-editing-questions)

## 1. Language and design

**Language: Python 3.9+.** Python was chosen because it needs no compiler or build tool,
handles UTF-8 Chinese text well, and is easy for a beginner to read and modify. The program
uses only the Python standard library, so there is nothing to install. The optional
**Quiz by Bible Book** mode writes new questions with a free AI model running on your own
computer through Ollama, or optionally with the paid Claude API (section 6).

**Design.** The question data is kept separate from the program logic:

| Part | File | Responsibility |
|---|---|---|
| Entry point | `main.py` | Reads command-line options, starts the app |
| Menus and quiz session | `quiz_app/app.py` | Language and translation selection, main menu, category and difficulty menus, running a quiz, results, review, history screen |
| Quiz rules | `quiz_app/quiz_engine.py` | Picking questions, shuffling options, checking answers, calculating the score |
| Question bank | `quiz_app/question_bank.py` | Loading, validating and filtering `data/*.json` |
| History | `quiz_app/history.py` | Session history plus optional JSON file storage |
| All on-screen text | `quiz_app/strings.py` | English and Simplified Chinese text for menus and messages |
| AI question writer | `quiz_app/ai_generator.py` | Asks Ollama (local) or Claude (online) for questions, checks what comes back |
| Bible book list | `quiz_app/bible_books.py` | 66 book names (English / CUVMPS) and verse counts, used by the book picker and reference checks |
| Data classes | `quiz_app/models.py` | `Question`, `AnswerRecord`, `QuizResult` |
| Terminal helpers | `quiz_app/console.py` | Input validation, UTF-8 setup |

## 2. Folder structure

```
bible_quiz/
├── main.py                      # run this
├── README.md
├── docs/
│   └── OLLAMA_GUIDE.md          # step-by-step setup for the free AI book quiz
├── data/
│   ├── bible_books.json         # 66 books: names and verses per chapter
│   ├── questions_en.json        # 54 English questions (NIV / ESV / NLT)
│   └── questions_zh.json        # 54 Chinese questions (CUVMPS)
├── quiz_app/
│   ├── __init__.py
│   ├── ai_generator.py
│   ├── app.py
│   ├── bible_books.py
│   ├── console.py
│   ├── history.py
│   ├── models.py
│   ├── question_bank.py
│   ├── quiz_engine.py
│   └── strings.py
├── tests/
│   ├── __init__.py
│   ├── test_quiz_app.py         # 30 tests: menus, quiz, scoring, history
│   └── test_ai_book_quiz.py     # 23 tests: AI book quiz (with simulated AI replies)
├── tools/
│   ├── verify_references.py     # optional: checks references against Bible text
│   └── reference_checks.json
└── results/                     # created automatically; holds quiz_history.json
```

## 3. Installing

1. Install **Python 3.9 or newer** from <https://www.python.org/downloads/>.
   On Windows, tick **"Add Python to PATH"** during installation.
2. Download or copy the `bible_quiz` folder. No other packages are needed.

(Only the optional verification tool in `tools/` needs an extra package; see section 10.)

## 4. Running

Open a terminal in the `bible_quiz` folder, then:

```bash
python main.py          # Windows
python3 main.py         # macOS / Linux
```

Optional settings:

| Option | Meaning |
|---|---|
| `--no-save` | Keep history for this session only (no file written) |
| `--history-file PATH` | Save history somewhere else (default `results/quiz_history.json`) |
| `--questions N` | Questions per quiz (default 10) |
| `--seed N` | Fixed random order, useful for testing or a group playing the same quiz |
| `--data-dir PATH` | Use a different folder of question files |
| `--ai ENGINE` | AI for the book quiz: `ollama` (default, free, on your computer) or `claude` (online, paid). Or set `BIBLE_QUIZ_AI` |
| `--model NAME` | AI model, e.g. `qwen3:4b` (defaults: `qwen3:8b` for Ollama, `claude-sonnet-5-5` for Claude). Or set `BIBLE_QUIZ_MODEL` |

### If Chinese characters do not display correctly

The program switches its own input and output to UTF-8, which is enough on most systems.
If you still see `?`, boxes or garbled text:

* **Windows:** use **Windows Terminal** (installed by default on Windows 11). In the older
  Command Prompt, run `chcp 65001` first, or start the program with `python -X utf8 main.py`.
  If characters appear as boxes, choose a font that has Chinese characters, such as
  *Microsoft YaHei Mono*, *NSimSun* or *Cascadia Code* (Windows 11).
* **macOS / Linux:** make sure the terminal uses UTF-8. Running `locale` should show `UTF-8`.
  If it doesn't, run `export LANG=en_US.UTF-8` (or `zh_CN.UTF-8`) before starting the program.
* **Typing answers with a Chinese input method:** full-width letters such as `Ａ` are accepted.

## 5. How to play

1. Choose a language: `1` English or `2` 中文.
2. Choose a translation: NIV, ESV or NLT for English, CUVMPS for Chinese. `0` goes back.
3. In the main menu, optionally choose a **category** (option 3) and **difficulty** (option 4).
   Each menu shows how many questions are available.
4. Start the quiz (option 1). Type `A`–`D` (upper or lower case) or `Q` to quit early
   (asks for confirmation). After each answer you'll see whether it was right, the correct
   answer, the Bible reference and a short explanation.
5. At the end you see your results and can review **all** answers or **only incorrect** ones.
6. Option 6 shows previous results; option 7 changes language or translation.
7. Option 2, **Quiz by Bible Book (AI-generated)**, is explained in section 6.

If a category and difficulty have fewer than 10 questions, the program says so and lets you
play with what is available, include all difficulty levels in that category, or go back.

## 6. Quiz by Bible Book (AI-generated)

Main-menu option **2** lets you pick any of the 66 books (by number, or English or Chinese
name) and a difficulty, then writes a brand-new set of questions about that book. Each run
gives different questions, and questions already asked about that book in the same session
are not repeated.

**These questions are not checked by a person.** The program checks that each one has four
different options and one correct letter, and that its reference really exists in the
chosen book (for example it rejects "Ruth 5:2", because Ruth has 4 chapters). It cannot check
that the answer is right. Every AI quiz says so on screen. Look up the reference if an
answer seems wrong, and use the checked question bank (option 1) for church events where
accuracy matters. Small models that run on a laptop make more mistakes than big online ones.

### Option A (default): free, on your own computer with Ollama

**Full step-by-step guide, with example screens and a troubleshooting table:
[docs/OLLAMA_GUIDE.md](docs/OLLAMA_GUIDE.md).**

No account, no key, no cost. Internet is needed only for the one-time downloads, and nothing
you do leaves your computer.

**Quick start:**

1. **Pick a model:** 8 GB memory → `qwen3:4b` (about 2.5 GB). 16 GB or more → `qwen3:8b`
   (about 5 GB, the default). Check under **Apple menu → About This Mac → Memory**.
   ("8b" means 8 billion parameters, not 8 GB.)
2. **Install Ollama** from <https://ollama.com/download> and open it. Skip the sign-in if
   asked. Keep it open (llama icon in the menu bar) whenever you use the book quiz.
3. **Download the model** in Terminal:
   ```bash
   ollama pull qwen3:4b
   ```
   Typing only `ollama` opens a launcher menu; press `Esc` to close it.
4. **Test it:** `ollama run qwen3:4b "Who built the ark?"`
5. **Play:**
   ```bash
   python3 main.py --model qwen3:4b      # leave out --model if you use qwen3:8b
   ```
   Choose **2. Quiz by Bible Book (AI-generated)**, type a book (`8`, `Ruth` or `路得记`)
   and pick a difficulty. Writing 10 questions takes about 1–3 minutes on a laptop.

To make `qwen3:4b` the default so you don't need `--model` (Mac):
`echo 'export BIBLE_QUIZ_MODEL="qwen3:4b"' >> ~/.zshrc && source ~/.zshrc`

### Option B: Claude (online, paid)

Questions from a larger online model, usually more accurate. Start the quiz with
`python3 main.py --ai claude`. You need an **Anthropic API key** from
<https://platform.claude.com/> (billed per use, separately from any Claude.ai subscription;
a 10-question quiz with the default model should cost a few US cents). Paste the key when
asked. It is hidden, kept in memory only and never saved. Or store it once (Mac):
`echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.zshrc`. Never put a key in the project
files or commit it to GitHub.

### What is sent to the AI

Only the book name, difficulty, language and translation choice, and the text of questions
already asked about that book in this session (so it can avoid repeats). With Ollama this
stays on your computer.

### If something goes wrong

The program shows a plain message and returns to the main menu instead of crashing:

| Message | What to do |
|---|---|
| Ollama is not running | Open the Ollama app (llama icon in the menu bar), or run `ollama serve` in another terminal |
| The AI model '…' is not downloaded yet | Run the `ollama pull …` command shown |
| Ollama reported a problem … memory | Use the smaller model: `python3 main.py --model qwen3:4b` |
| Only X of 10 questions passed the checks | Some generated questions failed the checks; the quiz is just shorter |
| None of the generated questions passed the checks | Try again, or try a bigger model if your computer can run it |
| The API key was not accepted (Claude) | Check the key; you will be asked for it again |
| Secure connection failed (Claude, Mac) | Open **Applications → Python 3.x** and double-click **Install Certificates.command** |

## 7. Sample console output

These are real outputs from the program (`--questions 3 --seed 4`; menu screens trimmed and long lines wrapped).

**English (ESV):**

```
========== MAIN MENU ==========
Translation: ESV | Category: Mixed Questions (all categories) | Difficulty: Easy

1. Start a New Quiz
2. Quiz by Bible Book (AI-generated)
3. Choose Bible Category
4. Choose Difficulty
5. View Quiz Instructions
6. View Previous Results
7. Change Language or Translation
8. Exit

Please enter your choice: 1

============================================
Starting quiz — ESV — English Standard Version
Category: Mixed Questions (all categories) | Difficulty: Easy | Questions: 3
Note: questions are original; references point to passages in your chosen translation.
============================================

Question 1 of 3
Which sea did God divide so that the Israelites could cross on dry ground when leaving Egypt?
A. Sea of Galilee
B. Red Sea
C. Dead Sea
D. Mediterranean Sea
Your answer (A/B/C/D, or Q to quit): A

Incorrect.
The correct answer is B. Red Sea
Reference: Exodus 14:21-22
Explanation: Moses stretched out his hand and the LORD drove the sea back, so Israel walked
through on dry ground. Exodus 15:4 names this sea the Red Sea (Hebrew Yam Suph, which some
scholars render 'Sea of Reeds').
Press Enter to continue...
...
Question 3 of 3
How many apostles did Jesus choose from among his disciples?
A. 3
B. 7
C. 12
D. 40
Your answer (A/B/C/D, or Q to quit): c

Correct!
Reference: Luke 6:12-16
Explanation: After praying all night, Jesus chose twelve of his disciples and named them apostles.

========== QUIZ RESULTS ==========
Total Questions: 3
Correct Answers: 1
Incorrect Answers: 2
Final Score: 1/3
Percentage: 33.3%
Keep going! Every step in God's Word counts.

========== REVIEW ANSWERS ==========
1. Review all questions
2. Review incorrect answers only
3. Return to main menu
```

**中文（CUVMPS）：**

```
========== 主菜单 ==========
译本：CUVMPS | 类别：综合题（所有类别） | 难度：简单

1. 开始新的问答
2. 按圣经书卷问答（AI 生成）
3. 选择圣经类别
4. 选择难度
5. 查看问答说明
6. 查看以往成绩
7. 更改语言或译本
8. 退出

请输入你的选择：1

============================================
开始问答 — CUVMPS — 现代标点和合本（简体）
类别：综合题（所有类别） | 难度：简单 | 题数：3
注：题目为原创，经文出处可在你所选的译本中查阅。
============================================

第 2 题，共 3 题
在浪子的比喻中，小儿子把钱财耗尽后做了什么工作？
A. 打鱼
B. 盖房子
C. 收税
D. 放猪
你的答案（A/B/C/D，输入 Q 退出）：b

答错了。
正确答案是 D. 放猪
经文出处：路加福音 15:13-16
解释：小儿子耗尽了家业，被打发到田里去放猪，饿得恨不得拿猪所吃的豆荚充饥。

========== 问答成绩 ==========
总题数：3
答对题数：1
答错题数：2
最终得分：1/3
正确率：33.3%
继续加油！在神的话语上的每一步都有收获。
```

Quitting early (from an automated test run in Chinese): after 3 of 10 questions the results
show `已作答题数：3` and `未作答（提前退出）：7`, and the percentage is calculated from the
3 answered questions.

## 8. Adding or editing questions

Questions live in `data/questions_en.json` and `data/questions_zh.json`. You do not need to
change any Python code. Open the file in a UTF-8 text editor (VS Code, Notepad++, or Windows
Notepad saving as UTF-8) and add an entry to the `"questions"` list:

```json
{
  "id": "EN-055",
  "language": "en",
  "translations": ["NIV", "ESV", "NLT"],
  "category": "old_testament",
  "difficulty": "easy",
  "question": "Who was thrown into a den of lions for praying to God?",
  "options": {"A": "Daniel", "B": "Joseph", "C": "Jeremiah", "D": "Elijah"},
  "correct_answer": "A",
  "book": "Daniel",
  "chapter_verse": "6:10-16",
  "explanation": "Daniel kept praying three times a day despite the king's decree, so he was thrown into the lions' den.",
  "source_text": {},
  "shuffle_options": true,
  "verified": true
}
```

| Field | Rules |
|---|---|
| `id` | Unique, e.g. `EN-055` / `ZH-055` (use the same number for a matching pair) |
| `language` | `en` in the English file, `zh` in the Chinese file |
| `translations` | Translations the question applies to: `NIV`, `ESV`, `NLT` (English) or `CUVMPS` (Chinese). Use one code only if the question depends on that translation's wording |
| `category` | `old_testament`, `new_testament`, `people`, `events_miracles`, `parables`, `life_teachings`, `books`, `characters`, `general` |
| `difficulty` | `easy`, `intermediate`, `advanced` |
| `options` | Exactly four different answers with keys `A`–`D` |
| `correct_answer` | `A`, `B`, `C` or `D` (the program tracks it correctly when options are shuffled) |
| `book`, `chapter_verse` | Reference shown to the player, e.g. `Genesis` + `6:13-22`. Chinese books use CUVMPS names, e.g. `创世记` |
| `explanation` | Short explanation in your own words |
| `source_text` | Optional quotation **per translation**, e.g. `{"ESV": "..."}`. It is shown only when the player selected that same translation, so wording is never mixed. Add only text you are permitted to quote |
| `shuffle_options` | `false` keeps the A–D order (good for numbers like 3 / 7 / 12 / 40) |
| `verified` | Must be `true` or the question is skipped. Set it only after checking the question against the Bible |

Rules for a good question: exactly one defensible answer; a reference that really contains
the fact; no invented quotations; no tradition presented as Scripture (for example, the Bible
does not say there were three wise men). For Chinese questions, use CUVMPS names: 大马士革,
约旦河, 撒马利亚, 伊利莎白, 克里特 (the older 1919 CUV spellings 大马色, 约但河, 撒玛利亚,
以利沙伯, 革哩底 differ).

If a question is invalid, the program skips it and prints the reason when the bank loads, so a
mistake in one question will not stop the quiz. Run `python -m unittest` after editing to
check the files.

## 9. Bible translations and copyright

* **NIV** (Biblica), **ESV** (Crossway) and **NLT** (Tyndale House) are copyrighted.
* **CUVMPS** is the **Chinese Union Version with Modern Punctuation (Simplified)**,
  **《现代标点和合本》（简体）**, published by Global Bible Initiative (© 2011; publisher and
  year as listed on Bible Gateway). It is **not** the same as
  《和合本修订版》 (Revised Chinese Union Version, 2010) or 《新标点和合本》 (1988).
  CUVMPS keeps the CUV text but updates punctuation and modernises many names, for
  example 大马色 → 大马士革.

The program therefore **does not quote any of these translations**. Questions and
explanations are original wording; the reference tells players where to read the passage
in their own Bible. The selected translation is shown before the quiz and saved in the
history. Because the starter questions test facts that are the same in NIV, ESV and NLT,
each English question is tagged for all three. Where translations use different terms
(for example "talents" vs "bags of gold/silver"), the question says so.

If your church has permission to use quotations, add them per translation in `source_text`.

## 10. How the questions were checked

* Every question's book, chapter and verse range was checked by `tools/verify_references.py`
  against real Bible text: the public-domain **King James Version** for English and a
  **Chinese Union Version text with modernised names** (the `ChiUn` file from the
  scrollmapper/bible_databases project) for Chinese. For each question it confirms that the
  reference exists and contains the key words for the answer (e.g. *Patmos* in Revelation 1:9),
  plus extra facts mentioned in the explanations. **Result: 108/108 passed.** The two
  "books of the Bible" questions about chapter and book counts are checked by counting.
* That Chinese check text is not CUVMPS itself. About 20 key verses were compared by hand
  with the CUVMPS text on cnbible.com (a site showing several Chinese versions side by side),
  which is how the CUVMPS names above were confirmed (e.g. Acts 9:3 大马士革, Titus 1:5 克里特,
  Acts 8:27 埃塞俄比亚, Luke 1:5 伊利莎白, Matthew 3:13 约旦河, Luke 10:33 撒马利亚人,
  Numbers 14:33 漂流).
* Not checked against NIV, ESV or NLT text directly. KJV and these translations use the same
  chapter and verse numbering for every reference in the bank. Jonah 1:17 is numbered 2:1 in
  Hebrew Bibles, and the explanation mentions this.
* A keyword match shows that a reference is right. It cannot judge whether the question is
  fair or the wrong answers are clearly wrong; those were reviewed by reading. Please have a
  pastor or Bible teacher look over the bank before using it in your church.

To re-run the check:

```bash
pip install opencc-python-reimplemented        # converts Traditional → Simplified characters
python tools/verify_references.py --download   # first time: downloads the two texts (~12 MB)
python tools/verify_references.py
```

## 11. Testing checklist

`python -m unittest -v` runs 53 tests, including end-to-end tests that start `main.py` and
type answers into it. All 53 pass on Python 3.9 and 3.13 (Linux).

| # | Scenario | How it was tested | Result |
|---|---|---|---|
| 1 | English + NIV / ESV / NLT | `test_each_english_translation_can_be_selected` | Pass |
| 2 | Mandarin + CUVMPS | `test_chinese_quiz_quit_early_after_confirmation`, manual run | Pass |
| 3 | Start and complete a quiz | `test_full_english_quiz_with_invalid_input_review_and_history` | Pass |
| 4 | Correct and incorrect answers | Same test: counts match the "Correct!" lines; shuffled-option mapping checked 1,080 times | Pass |
| 5 | Invalid answers (`x`, `E`, blank, `AB`, `1`) | End-to-end test + `test_answer_input_is_case_insensitive_and_validated` | Pass |
| 6 | Categories and difficulty levels | Filter tests; `test_small_category_offers_choices` | Pass |
| 7 | Review incorrect answers | End-to-end test (review all / incorrect only / invalid menu input) | Pass |
| 8 | Previous results | End-to-end test (menu option 6) | Pass |
| 9 | Exit a quiz early | Quit with confirmation, cancel the quit, quit before answering | Pass |
| 10 | Empty / missing question bank | Missing folder, empty file, broken JSON, invalid entries | Pass |
| 11 | Restart and load saved results | `test_history_survives_restart`; corrupted history file is backed up | Pass |
| 12 | Score and percentage | 8/10 = 80%, 2/3 = 66.7%, 0 attempted = 0% (no division error) | Pass |

Also tested: Ctrl+D / end of input exits cleanly, going back from menus, cancelling a
language change, full-width letters from a Chinese keyboard.

**AI book quiz** (`tests/test_ai_book_quiz.py`): Ollama and Claude are replaced by simulated
replies, so these tests need no model, key or internet. They cover the request format for
both engines, building questions, rejecting bad ones (impossible references, duplicate
options, missing fields, repeats), the error messages (Ollama not running, model not
downloaded, out of memory, bad key, busy service), the book picker (numbers, English and
Chinese names, invalid input), English and Chinese book quizzes, and book quizzes in the
history. One test starts a small fake Ollama server so the real network code is used, and
another checks the real "Ollama is not running" case.

## 12. Known limitations

* **The AI book quiz has not been run with a real AI model yet.** Ollama and its models could
  not be downloaded in the environment where this was built, and no Claude API key was
  available. Requests follow the current Ollama and Claude API documentation and were tested
  against simulated replies (section 11). The first real run may show an error; if so, the
  message explains why. How good the questions are depends on the model.
* **AI questions can be wrong** (section 6), and their Chinese wording may not always use
  CUVMPS names even though the AI is asked to.
* **Not tested on Windows or macOS.** Tests ran on Linux only. Chinese display on Windows
  depends on the terminal and font (see section 4).
* **54 questions per language.** Each category has 6 (2 per difficulty), so a single
  category at one difficulty has only 2. The program offers to play those or include all
  levels. Choosing **Mixed** gives 18 per difficulty, enough for a full 10-question quiz. Add
  questions to make category quizzes longer.
* **No direct Scripture quotations** are included, because of copyright (section 9).
* The CUVMPS names were spot-checked by hand, not all compared automatically, because the
  CUVMPS text isn't openly downloadable. Wrong-answer options that are not in the reference
  (e.g. 地中海, 死海) use common modern names.
* Chinese text in the menus may not line up perfectly in columns in some terminals.
* History saves date and time, settings and score only, with no names. Anyone using the
  same computer can see it. Delete `results/quiz_history.json` to clear it, or use `--no-save`.
