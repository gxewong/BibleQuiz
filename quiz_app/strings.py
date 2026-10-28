"""All text shown to the user, in English ("en") and Simplified Chinese ("zh").

To change a menu label or message, edit it here. Each language must have the
same keys. Use {placeholders} for values filled in by the program.
"""
from __future__ import annotations

LANGUAGES = ("en", "zh")

# Bible translations available for each interface language.
TRANSLATIONS: dict[str, list[tuple[str, dict[str, str]]]] = {
    "en": [
        ("NIV", {"en": "New International Version", "zh": "新国际版"}),
        ("ESV", {"en": "English Standard Version", "zh": "英文标准版"}),
        ("NLT", {"en": "New Living Translation", "zh": "新普及译本"}),
    ],
    "zh": [
        ("CUVMPS", {
            "en": "Chinese Union Version with Modern Punctuation (Simplified)",
            "zh": "现代标点和合本（简体）",
        }),
    ],
}

# Category keys in menu order. "mixed" means "all categories".
CATEGORY_KEYS = (
    "old_testament", "new_testament", "people", "events_miracles", "parables",
    "life_teachings", "books", "characters", "general", "mixed",
)
MIXED = "mixed"

CATEGORY_NAMES = {
    "en": {
        "old_testament": "Old Testament",
        "new_testament": "New Testament",
        "people": "People in the Bible",
        "events_miracles": "Bible Events and Miracles",
        "parables": "Parables of Jesus",
        "life_teachings": "Life and Teachings of Jesus",
        "books": "Books of the Bible",
        "characters": "Bible Characters",
        "general": "General Bible Knowledge",
        "mixed": "Mixed Questions (all categories)",
    },
    "zh": {
        "old_testament": "旧约",
        "new_testament": "新约",
        "people": "圣经中的人物",
        "events_miracles": "圣经事件与神迹",
        "parables": "耶稣的比喻",
        "life_teachings": "耶稣的生平与教导",
        "books": "圣经书卷",
        "characters": "圣经角色",
        "general": "圣经常识",
        "mixed": "综合题（所有类别）",
    },
}

CATEGORY_HINTS = {
    "en": {
        "people": "who did what",
        "characters": "family, background and occupation",
    },
    "zh": {
        "people": "谁做了什么",
        "characters": "家庭、背景与职业",
    },
}

DIFFICULTY_KEYS = ("easy", "intermediate", "advanced")

DIFFICULTY_NAMES = {
    "en": {"easy": "Easy", "intermediate": "Intermediate", "advanced": "Advanced"},
    "zh": {"easy": "简单", "intermediate": "中等", "advanced": "进阶"},
}

DIFFICULTY_DESCRIPTIONS = {
    "en": {
        "easy": "Basic Bible knowledge and familiar stories.",
        "intermediate": "More detailed knowledge of Bible events, people, teachings, and references.",
        "advanced": "More challenging questions requiring deeper knowledge of Scripture.",
    },
    "zh": {
        "easy": "基本的圣经知识和熟悉的故事。",
        "intermediate": "对圣经事件、人物、教导和经文出处有更详细的认识。",
        "advanced": "更具挑战性的问题，需要对圣经有更深入的认识。",
    },
}

TEXT: dict[str, dict[str, str]] = {
    "en": {
        "app_title": "BIBLE QUIZ",
        "welcome": "Welcome to the Bible Quiz!",
        "invalid_choice": "Invalid choice. Please enter one of: {options}.",
        "translation_title": "========== SELECT BIBLE TRANSLATION ==========",
        "back": "Back",
        "cancel": "Cancel (keep current settings)",
        "enter_choice": "Enter your choice: ",
        "selected_translation": "Selected translation: {code} — {name}",
        "menu_title": "========== MAIN MENU ==========",
        "menu_items": "Start a New Quiz|Quiz by Bible Book (AI-generated)|Choose Bible Category|Choose Difficulty|View Quiz Instructions|View Previous Results|Change Language or Translation|Exit",
        "menu_prompt": "Please enter your choice: ",
        "settings_line": "Translation: {translation} | Category: {category} | Difficulty: {difficulty}",
        "category_title": "========== CHOOSE BIBLE CATEGORY ==========",
        "difficulty_title": "========== CHOOSE DIFFICULTY ==========",
        "count_suffix": "({count} questions)",
        "category_set": "Category set to: {name}",
        "difficulty_set": "Difficulty set to: {name}",
        "instructions_title": "========== QUIZ INSTRUCTIONS ==========",
        "instructions": (
            "1. Each quiz has up to {count} multiple-choice questions.\n"
            "2. Type A, B, C or D and press Enter (lowercase is fine).\n"
            "3. Type Q to quit the quiz early (you will be asked to confirm).\n"
            "4. After each answer you will see whether it was correct, the Bible\n"
            "   reference, and a short explanation.\n"
            "5. You get 1 point for each correct answer.\n"
            "6. At the end you can review all answers or only incorrect ones.\n"
            "7. Use the main menu to choose a category and difficulty first.\n"
            "8. 'Quiz by Bible Book' writes new questions about any book with AI\n"
            "   (free with Ollama on your computer; see README section 6). These are\n"
            "   NOT checked by a person, so confirm answers with your Bible.\n"
            "\n"
            "About the questions: these are original quiz questions. Explanations are\n"
            "short summaries in our own words, not quotations from NIV, ESV or NLT,\n"
            "which are copyrighted. Look up each reference in your chosen\n"
            "translation to read the passage itself."
        ),
        "press_enter": "Press Enter to continue...",
        "bank_missing": "The question bank is not available: {detail}",
        "bank_empty": "There are no questions available for this language and translation.",
        "no_match": "No questions match Category: {category} and Difficulty: {difficulty}.",
        "try_other": "Please choose a different category or difficulty from the main menu.",
        "insufficient": "Only {available} question(s) match Category: {category} and Difficulty: {difficulty} (a full quiz has {wanted}).",
        "all_levels": "All levels",
        "insufficient_play": "Play with the {available} available question(s)",
        "insufficient_all_levels": "Include all difficulty levels for this category ({count} questions)",
        "quiz_start": "Starting quiz — {translation}",
        "quiz_settings": "Category: {category} | Difficulty: {difficulty} | Questions: {count}",
        "quiz_note": "Note: questions are original; references point to passages in your chosen translation.",
        "question_header": "Question {number} of {total}",
        "answer_prompt": "Your answer (A/B/C/D, or Q to quit): ",
        "invalid_answer": "Please enter A, B, C or D (or Q to quit).",
        "confirm_quit": "Are you sure you want to quit this quiz? (Y/N): ",
        "invalid_yes_no": "Please enter Y or N.",
        "continue_quiz": "Continuing the quiz.",
        "correct": "Correct!",
        "incorrect": "Incorrect.",
        "correct_answer_is": "The correct answer is {letter}. {text}",
        "reference": "Reference: {reference}",
        "explanation": "Explanation: {text}",
        "source_text": "Scripture ({translation}): {text}",
        "results_title": "========== QUIZ RESULTS ==========",
        "total_questions": "Total Questions: {total}",
        "attempted": "Questions Attempted: {attempted}",
        "correct_answers": "Correct Answers: {correct}",
        "incorrect_answers": "Incorrect Answers: {incorrect}",
        "unanswered": "Not Answered (quit early): {count}",
        "final_score": "Final Score: {correct}/{attempted}",
        "percentage": "Percentage: {percent}%",
        "perf_none": "No questions were answered this time. Try again when you are ready!",
        "perf_excellent": "Excellent! You know your Bible very well.",
        "perf_great": "Great job! Keep studying God's Word.",
        "perf_good": "Good effort! Keep reading and you will keep growing.",
        "perf_keep_going": "Keep going! Every step in God's Word counts.",
        "result_saved": "Result saved to quiz history.",
        "review_title": "========== REVIEW ANSWERS ==========",
        "review_items": "Review all questions|Review incorrect answers only|Return to main menu",
        "no_incorrect": "There are no incorrect answers to review. Well done!",
        "your_answer": "Your answer: {letter}. {text}",
        "review_correct_tag": "[Correct]",
        "review_incorrect_tag": "[Incorrect]",
        "history_title": "========== PREVIOUS RESULTS ==========",
        "history_empty": "No quiz results yet.",
        "history_entry": "{date} | {language} | {translation} | {category} | {difficulty}",
        "history_score": "    Score: {correct}/{attempted} ({percent}%){quit_note}",
        "history_quit_note": " — quit early after {attempted} of {total}",
        "history_showing": "(Showing the {shown} most recent of {total} results.)",
        "history_warning": "Warning: {detail}",
        "language_names": "English|中文（普通话）",
        "goodbye": "Thank you for playing the Bible Quiz. God bless you!",
        "book_title": "========== QUIZ BY BIBLE BOOK (AI) ==========",
        "book_hint": "Type a book number or name (e.g. 1, Genesis, 1 Samuel). 0 = Back.",
        "book_prompt": "Book: ",
        "book_invalid": "Book not found. Type a number from 1 to 66 or a book name, or 0 to go back.",
        "book_difficulty_title": "========== {book}: CHOOSE DIFFICULTY ==========",
        "book_label": "Book: {book}",
        "books_missing": "The list of Bible books could not be loaded: {detail}",
        "ai_generating": "Writing {count} {difficulty} questions about {book} with {model}...",
        "ai_generating_local": "(Running on your computer: this can take 1-3 minutes, longer the first time.)",
        "ai_fewer": "Only {count} of {wanted} questions passed the checks, so this quiz is shorter.",
        "ai_notice": "AI-generated questions: NOT checked by a person. Please confirm answers with your Bible.",
        "ai_results_note": "Reminder: these questions were written by AI and may contain mistakes. If an answer looks wrong, check the reference in your Bible.",
        "ai_key_needed": "This mode uses the Claude API, which needs an Anthropic API key (get one at platform.claude.com).\nTip: set the ANTHROPIC_API_KEY environment variable so you aren't asked each time.",
        "ai_key_prompt": "Paste your API key (hidden, not saved) or press Enter to go back: ",
        "ai_error_auth": "The API key was not accepted. Please check it and try again.",
        "ai_error_permission": "This API key is not allowed to use the model ({detail}).",
        "ai_error_model": "The AI model '{model}' was not found. Start the program with --model and a current model name.",
        "ai_error_rate_limit": "Too many requests right now. Please wait a minute and try again.",
        "ai_error_overloaded": "The AI service is busy or unavailable ({detail}). Please try again shortly.",
        "ai_error_bad_request": "The AI service rejected the request ({detail}).",
        "ai_error_refusal": "The AI declined to write these questions. Please try a different book or difficulty.",
        "ai_error_incomplete": "The AI's answer was cut off. Please try again.",
        "ai_error_bad_response": "The AI's answer could not be read ({detail}). Please try again.",
        "ai_error_network": "Could not connect to the AI service. Check your internet connection. ({detail})",
        "ai_error_ssl": "Secure connection failed ({detail}). On a Mac with Python from python.org, open Applications > Python 3.x and double-click 'Install Certificates.command', then try again.",
        "ai_error_timeout": "The AI service took too long to answer. Please try again.",
        "ai_error_none_valid": "None of the generated questions passed the checks. Please try again.",
        "ai_error_ollama_not_running": "Ollama is not running ({detail}). Open the Ollama app (or run 'ollama serve' in another terminal), then try again.",
        "ai_error_ollama_model_missing": "The AI model '{detail}' is not downloaded yet. In a terminal, run:  ollama pull {detail}",
        "ai_error_ollama_error": "Ollama reported a problem ({detail}). If it mentions memory, try a smaller model, e.g. start the quiz with --model qwen3:4b",
        "bank_warning": "Note: {count} question(s) in {file} were skipped because they are invalid or unverified.",
    },
    "zh": {
        "app_title": "圣经问答",
        "welcome": "欢迎来到圣经问答！",
        "invalid_choice": "无效的选择。请输入以下其中一项：{options}。",
        "translation_title": "========== 选择圣经译本 ==========",
        "back": "返回",
        "cancel": "取消（保留当前设置）",
        "enter_choice": "请输入你的选择：",
        "selected_translation": "已选择译本：{code} — {name}",
        "menu_title": "========== 主菜单 ==========",
        "menu_items": "开始新的问答|按圣经书卷问答（AI 生成）|选择圣经类别|选择难度|查看问答说明|查看以往成绩|更改语言或译本|退出",
        "menu_prompt": "请输入你的选择：",
        "settings_line": "译本：{translation} | 类别：{category} | 难度：{difficulty}",
        "category_title": "========== 选择圣经类别 ==========",
        "difficulty_title": "========== 选择难度 ==========",
        "count_suffix": "（{count} 题）",
        "category_set": "类别已设为：{name}",
        "difficulty_set": "难度已设为：{name}",
        "instructions_title": "========== 问答说明 ==========",
        "instructions": (
            "1. 每次问答最多有 {count} 道选择题。\n"
            "2. 输入 A、B、C 或 D 后按回车键（大小写均可）。\n"
            "3. 输入 Q 可提前结束问答（系统会请你确认）。\n"
            "4. 每次作答后，会显示答案是否正确、经文出处和简短解释。\n"
            "5. 每答对一题得 1 分。\n"
            "6. 问答结束后，可以回顾全部题目或只看答错的题目。\n"
            "7. 请先在主菜单中选择类别和难度。\n"
            "8. “按圣经书卷问答”会用 AI 为任何一卷书即时出题（用 Ollama 在你的电脑上\n"
            "   免费运行，见 README 第 6 节）。这些题目未经人工核对，请以圣经核对答案。\n"
            "\n"
            "关于题目：所有题目均为原创。解释是用我们自己的话所写的简短说明，\n"
            "并非引用受版权保护的《现代标点和合本》经文。请按出处在你的圣经中\n"
            "查阅相关经文。"
        ),
        "press_enter": "按回车键继续……",
        "bank_missing": "题库无法使用：{detail}",
        "bank_empty": "此语言和译本目前没有可用的题目。",
        "no_match": "没有符合 类别：{category}、难度：{difficulty} 的题目。",
        "try_other": "请在主菜单中选择其他类别或难度。",
        "insufficient": "符合 类别：{category}、难度：{difficulty} 的题目只有 {available} 题（完整问答需要 {wanted} 题）。",
        "all_levels": "所有难度",
        "insufficient_play": "用现有的 {available} 题进行问答",
        "insufficient_all_levels": "包括此类别的所有难度（共 {count} 题）",
        "quiz_start": "开始问答 — {translation}",
        "quiz_settings": "类别：{category} | 难度：{difficulty} | 题数：{count}",
        "quiz_note": "注：题目为原创，经文出处可在你所选的译本中查阅。",
        "question_header": "第 {number} 题，共 {total} 题",
        "answer_prompt": "你的答案（A/B/C/D，输入 Q 退出）：",
        "invalid_answer": "请输入 A、B、C 或 D（或输入 Q 退出）。",
        "confirm_quit": "确定要退出这次问答吗？(Y/N)：",
        "invalid_yes_no": "请输入 Y 或 N。",
        "continue_quiz": "继续问答。",
        "correct": "答对了！",
        "incorrect": "答错了。",
        "correct_answer_is": "正确答案是 {letter}. {text}",
        "reference": "经文出处：{reference}",
        "explanation": "解释：{text}",
        "source_text": "经文（{translation}）：{text}",
        "results_title": "========== 问答成绩 ==========",
        "total_questions": "总题数：{total}",
        "attempted": "已作答题数：{attempted}",
        "correct_answers": "答对题数：{correct}",
        "incorrect_answers": "答错题数：{incorrect}",
        "unanswered": "未作答（提前退出）：{count}",
        "final_score": "最终得分：{correct}/{attempted}",
        "percentage": "正确率：{percent}%",
        "perf_none": "这次没有作答任何题目。准备好了再来挑战吧！",
        "perf_excellent": "太好了！你对圣经非常熟悉。",
        "perf_great": "做得很好！继续研读神的话语。",
        "perf_good": "不错的努力！继续读经，你会不断进步。",
        "perf_keep_going": "继续加油！在神的话语上的每一步都有收获。",
        "result_saved": "成绩已保存到问答记录。",
        "review_title": "========== 回顾答案 ==========",
        "review_items": "回顾全部题目|只回顾答错的题目|返回主菜单",
        "no_incorrect": "没有答错的题目。做得好！",
        "your_answer": "你的答案：{letter}. {text}",
        "review_correct_tag": "[答对]",
        "review_incorrect_tag": "[答错]",
        "history_title": "========== 以往成绩 ==========",
        "history_empty": "目前还没有问答记录。",
        "history_entry": "{date} | {language} | {translation} | {category} | {difficulty}",
        "history_score": "    得分：{correct}/{attempted}（{percent}%）{quit_note}",
        "history_quit_note": " — 在 {total} 题中作答 {attempted} 题后提前退出",
        "history_showing": "（显示最近 {shown} 条记录，共 {total} 条。）",
        "history_warning": "警告：{detail}",
        "language_names": "English|中文（普通话）",
        "goodbye": "感谢参加圣经问答。愿神赐福给你！",
        "book_title": "========== 按圣经书卷问答（AI） ==========",
        "book_hint": "请输入书卷编号或名称（例如 1、创世记、撒母耳记上）。0 = 返回。",
        "book_prompt": "书卷：",
        "book_invalid": "找不到这卷书。请输入 1 至 66 的编号或书卷名称，或输入 0 返回。",
        "book_difficulty_title": "========== {book}：选择难度 ==========",
        "book_label": "书卷：{book}",
        "books_missing": "无法载入圣经书卷列表：{detail}",
        "ai_generating": "正在用 {model} 为《{book}》出 {count} 道“{difficulty}”题目……",
        "ai_generating_local": "（在你的电脑上运行：可能需要 1 至 3 分钟，第一次会更久。）",
        "ai_fewer": "只有 {count} 道题目（共 {wanted} 道）通过检查，所以这次问答题数较少。",
        "ai_notice": "AI 生成的题目：未经人工核对。请以圣经核对答案。",
        "ai_results_note": "提醒：这些题目由 AI 编写，可能有错误。如有疑问，请按经文出处查阅圣经。",
        "ai_key_needed": "此模式使用 Claude API，需要 Anthropic API 密钥（可在 platform.claude.com 申请）。\n提示：设置 ANTHROPIC_API_KEY 环境变量后，就不用每次输入。",
        "ai_key_prompt": "请粘贴你的 API 密钥（不会显示，也不会保存），或按回车键返回：",
        "ai_error_auth": "API 密钥无效。请检查后再试。",
        "ai_error_permission": "此 API 密钥无权使用该模型（{detail}）。",
        "ai_error_model": "找不到 AI 模型“{model}”。请在启动程序时用 --model 指定现有的模型名称。",
        "ai_error_rate_limit": "目前请求太多。请稍等一分钟再试。",
        "ai_error_overloaded": "AI 服务繁忙或暂时无法使用（{detail}）。请稍后再试。",
        "ai_error_bad_request": "AI 服务拒绝了这个请求（{detail}）。",
        "ai_error_refusal": "AI 拒绝编写这些题目。请换一卷书或难度再试。",
        "ai_error_incomplete": "AI 的回答不完整。请再试一次。",
        "ai_error_bad_response": "无法读取 AI 的回答（{detail}）。请再试一次。",
        "ai_error_network": "无法连接 AI 服务。请检查网络连接。（{detail}）",
        "ai_error_ssl": "安全连接失败（{detail}）。如果你在 Mac 上使用 python.org 的 Python，请打开“应用程序 > Python 3.x”，双击“Install Certificates.command”后再试。",
        "ai_error_timeout": "AI 服务回应时间太长。请再试一次。",
        "ai_error_none_valid": "生成的题目都没有通过检查。请再试一次。",
        "ai_error_ollama_not_running": "Ollama 没有运行（{detail}）。请打开 Ollama 应用程序（或在另一个终端运行 ollama serve），然后再试。",
        "ai_error_ollama_model_missing": "AI 模型“{detail}”尚未下载。请在终端运行：ollama pull {detail}",
        "ai_error_ollama_error": "Ollama 出现问题（{detail}）。如果提到内存不足，请改用较小的模型，例如启动时加上 --model qwen3:4b",
        "bank_warning": "注意：{file} 中有 {count} 道题目因格式无效或未经核实而被略过。",
    },
}

LANGUAGE_PROMPT = (
    "Please select your language / 请选择语言：\n"
    "\n"
    "1. English\n"
    "2. 中文（普通话）\n"
)
LANGUAGE_INPUT = "Enter your choice (1 or 2) / 请输入 1 或 2："
LANGUAGE_INVALID = "Invalid choice. Please enter 1 or 2. / 无效的选择，请输入 1 或 2。"
LANGUAGE_CANCEL = "0. Cancel / 取消"


def t(lang: str, key: str, **values) -> str:
    """Return the text for `key` in `lang`, filling in any {placeholders}."""
    text = TEXT[lang][key]
    return text.format(**values) if values else text


def translation_name(code: str, lang: str) -> str:
    for translations in TRANSLATIONS.values():
        for trans_code, names in translations:
            if trans_code == code:
                return names[lang]
    return code
