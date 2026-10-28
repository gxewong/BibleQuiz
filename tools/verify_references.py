"""Check every question's Bible reference against public-domain Bible text.

This is a maintenance tool, not part of the quiz. It does NOT check NIV, ESV,
NLT or CUVMPS wording (those texts are copyrighted). Instead it checks that:

  * each question's book / chapter / verse reference actually exists, and
  * the referenced verses contain the keywords listed in reference_checks.json,
    using the public-domain King James Version for English questions and the
    "ChiUn" Chinese Union Version text from the scrollmapper/bible_databases
    project for Chinese questions. That ChiUn text uses modernised place and
    person names (大马士革, 约旦河, 伊利莎白 ...) like CUVMPS does, but it is NOT
    the CUVMPS text itself: punctuation and a few names differ (e.g. it has
    衣索匹亚 where CUVMPS has 埃塞俄比亚). Names in the Chinese question bank
    follow CUVMPS; keywords below were chosen to avoid the differing names.

A keyword match shows the reference points at the right passage. Choosing a
fair question and good distractors still needs a human reviewer.
The source texts are downloaded only to your computer for checking and are
not part of the quiz.

Usage (from the project folder):
    pip install opencc-python-reimplemented     # Traditional -> Simplified
    python tools/verify_references.py --download   # first time only
    python tools/verify_references.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TOOLS_DIR.parent
SOURCES_DIR = TOOLS_DIR / "sources"
KJV_FILE = SOURCES_DIR / "en_kjv.json"
CUV_FILE = SOURCES_DIR / "ChiUn.json"
KJV_URL = "https://raw.githubusercontent.com/thiagobodruk/bible/master/json/en_kjv.json"
CUV_URL = "https://raw.githubusercontent.com/scrollmapper/bible_databases/master/formats/json/ChiUn.json"

# The 66 books in canonical order: (English name, Chinese Union Version name)
BOOKS = [
    ("Genesis", "创世记"), ("Exodus", "出埃及记"), ("Leviticus", "利未记"), ("Numbers", "民数记"),
    ("Deuteronomy", "申命记"), ("Joshua", "约书亚记"), ("Judges", "士师记"), ("Ruth", "路得记"),
    ("1 Samuel", "撒母耳记上"), ("2 Samuel", "撒母耳记下"), ("1 Kings", "列王纪上"), ("2 Kings", "列王纪下"),
    ("1 Chronicles", "历代志上"), ("2 Chronicles", "历代志下"), ("Ezra", "以斯拉记"), ("Nehemiah", "尼希米记"),
    ("Esther", "以斯帖记"), ("Job", "约伯记"), ("Psalms", "诗篇"), ("Proverbs", "箴言"),
    ("Ecclesiastes", "传道书"), ("Song of Songs", "雅歌"), ("Isaiah", "以赛亚书"), ("Jeremiah", "耶利米书"),
    ("Lamentations", "耶利米哀歌"), ("Ezekiel", "以西结书"), ("Daniel", "但以理书"), ("Hosea", "何西阿书"),
    ("Joel", "约珥书"), ("Amos", "阿摩司书"), ("Obadiah", "俄巴底亚书"), ("Jonah", "约拿书"),
    ("Micah", "弥迦书"), ("Nahum", "那鸿书"), ("Habakkuk", "哈巴谷书"), ("Zephaniah", "西番雅书"),
    ("Haggai", "哈该书"), ("Zechariah", "撒迦利亚书"), ("Malachi", "玛拉基书"),
    ("Matthew", "马太福音"), ("Mark", "马可福音"), ("Luke", "路加福音"), ("John", "约翰福音"),
    ("Acts", "使徒行传"), ("Romans", "罗马书"), ("1 Corinthians", "哥林多前书"), ("2 Corinthians", "哥林多后书"),
    ("Galatians", "加拉太书"), ("Ephesians", "以弗所书"), ("Philippians", "腓立比书"), ("Colossians", "歌罗西书"),
    ("1 Thessalonians", "帖撒罗尼迦前书"), ("2 Thessalonians", "帖撒罗尼迦后书"), ("1 Timothy", "提摩太前书"),
    ("2 Timothy", "提摩太后书"), ("Titus", "提多书"), ("Philemon", "腓利门书"), ("Hebrews", "希伯来书"),
    ("James", "雅各书"), ("1 Peter", "彼得前书"), ("2 Peter", "彼得后书"), ("1 John", "约翰一书"),
    ("2 John", "约翰二书"), ("3 John", "约翰三书"), ("Jude", "犹大书"), ("Revelation", "启示录"),
]
BOOK_INDEX = {name: i for i, pair in enumerate(BOOKS) for name in pair}
NT_START = BOOK_INDEX["Matthew"]


def download() -> None:
    SOURCES_DIR.mkdir(exist_ok=True)
    for url, path in ((KJV_URL, KJV_FILE), (CUV_URL, CUV_FILE)):
        print(f"Downloading {url}")
        urllib.request.urlretrieve(url, path)


def character_converter():
    """Traditional -> Simplified, one character at a time.

    OpenCC's normal 't2s' mode also rewrites whole phrases into modern
    names (e.g. 大馬色 -> 大马士革), which would hide the CUV's own spelling
    (大马色). Using only the character table keeps the CUV names intact.
    """
    try:
        import opencc
    except ImportError:
        sys.exit("Please install the converter first: pip install opencc-python-reimplemented")
    table_file = Path(opencc.__file__).parent / "dictionary" / "TSCharacters.txt"
    table = {}
    for line in table_file.read_text(encoding="utf-8").splitlines():
        if "\t" in line:
            trad, simp = line.split("\t", 1)
            if len(trad) == 1:
                table[ord(trad)] = simp.split()[0]
    return lambda text: text.translate(table)


def load_texts() -> dict[str, list[list[list[str]]]]:
    """Return {'en': kjv, 'zh': cuv}, each indexed [book][chapter][verse] (0-based)."""
    if not KJV_FILE.exists() or not CUV_FILE.exists():
        sys.exit("Source texts missing. Run: python tools/verify_references.py --download")
    kjv_raw = json.loads(KJV_FILE.read_text(encoding="utf-8-sig"))
    kjv = [book["chapters"] for book in kjv_raw]

    to_simplified = character_converter()
    cuv_raw = json.loads(CUV_FILE.read_text(encoding="utf-8"))
    cuv = [
        [[re.sub(r"\s+", "", to_simplified(v["text"])) for v in ch["verses"]] for ch in book["chapters"]]
        for book in cuv_raw["books"]
    ]
    if len(kjv) != 66 or len(cuv) != 66:
        sys.exit("Unexpected source format: expected 66 books in each text.")
    return {"en": kjv, "zh": cuv}


def parse_reference(book: str, chapter_verse: str):
    """Return (book_index, [(chapter, verse), ...]) or raise ValueError."""
    if book not in BOOK_INDEX:
        raise ValueError(f"unknown book name '{book}'")
    cv = chapter_verse.strip()
    m = re.fullmatch(r"(\d+)(?::(\d+)(?:-(?:(\d+):)?(\d+))?)?", cv)
    if not m:
        raise ValueError(f"cannot parse chapter/verse '{chapter_verse}'")
    ch1, v1, ch2, v2 = m.groups()
    ch1 = int(ch1)
    if v1 is None:                      # whole chapter
        return BOOK_INDEX[book], [(ch1, None)]
    v1 = int(v1)
    if v2 is None:
        return BOOK_INDEX[book], [(ch1, v1)]
    return BOOK_INDEX[book], [(ch1, v1), (int(ch2) if ch2 else ch1, int(v2))]


def passage_text(bible, book_idx: int, span) -> str:
    chapters = bible[book_idx]
    (c1, v1) = span[0]
    (c2, v2) = span[-1]
    if not 1 <= c1 <= len(chapters) or not 1 <= c2 <= len(chapters):
        raise ValueError("chapter out of range")
    if v1 is None:
        return " ".join(chapters[c1 - 1])
    verses = []
    for c in range(c1, c2 + 1):
        chapter = chapters[c - 1]
        start = v1 if c == c1 else 1
        end = v2 if c == c2 else len(chapter)
        if not (1 <= start <= len(chapter) and 1 <= end <= len(chapter) and start <= end):
            raise ValueError(f"verse out of range in chapter {c}")
        verses.extend(chapter[start - 1:end])
    return " ".join(verses)


def split_ref(ref: str):
    book, _, cv = ref.rpartition(" ")
    return book, cv


def run_special(name: str, bible) -> tuple[bool, str]:
    if name == "most_chapters":
        counts = [len(b) for b in bible]
        top = max(range(66), key=lambda i: counts[i])
        ok = BOOKS[top][0] == "Psalms" and counts[top] == 150
        return ok, f"most chapters: {BOOKS[top][0]} ({counts[top]}); Isaiah {counts[22]}, Jeremiah {counts[23]}, Genesis {counts[0]}"
    if name == "nt_book_count":
        n = len(bible) - NT_START
        return n == 27, f"New Testament books: {n}"
    return False, f"unknown special check '{name}'"


def verify(data_dir: Path) -> int:
    texts = load_texts()
    checks = json.loads((TOOLS_DIR / "reference_checks.json").read_text(encoding="utf-8"))
    failures = 0
    total = 0
    for lang in ("en", "zh"):
        path = data_dir / f"questions_{lang}.json"
        questions = json.loads(path.read_text(encoding="utf-8"))["questions"]
        bible = texts[lang]
        for q in questions:
            total += 1
            qid = q["id"]
            problems = []
            q_checks = checks.get(qid)
            if not q_checks:
                problems.append("no keyword checks defined")
            # The question's own reference must exist (unless it is a whole-canon reference).
            own_text = None
            if q["chapter_verse"]:
                try:
                    b, span = parse_reference(q["book"], q["chapter_verse"])
                    own_text = passage_text(bible, b, span)
                except ValueError as err:
                    problems.append(f"bad reference {q['book']} {q['chapter_verse']}: {err}")
            for chk in q_checks or []:
                if "special" in chk:
                    ok, info = run_special(chk["special"], bible)
                    if not ok:
                        problems.append(info)
                    continue
                if "ref" in chk:
                    try:
                        b, span = parse_reference(*split_ref(chk["ref"]))
                        text = passage_text(bible, b, span)
                    except ValueError as err:
                        problems.append(f"bad check reference {chk['ref']}: {err}")
                        continue
                    where = chk["ref"]
                else:
                    text = own_text
                    where = f"{q['book']} {q['chapter_verse']}"
                if text is None:
                    problems.append("keyword check needs a verse reference")
                    continue
                if chk["keyword"].lower() not in text.lower():
                    problems.append(f"'{chk['keyword']}' not found in {where}")
            if problems:
                failures += 1
                print(f"FAIL {qid}: " + "; ".join(problems))
            else:
                print(f"ok   {qid}  {q['book']} {q['chapter_verse']}")
    print(f"\n{total - failures}/{total} questions passed reference checks.")
    return 1 if failures else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--download", action="store_true", help="download the public-domain source texts")
    parser.add_argument("--data-dir", type=Path, default=PROJECT_DIR / "data")
    args = parser.parse_args()
    if args.download:
        download()
    sys.exit(verify(args.data_dir))


if __name__ == "__main__":
    main()
