# Using the AI Book Quiz with Ollama

This guide shows how to set up **Quiz by Bible Book (AI-generated)** (main-menu option 2),
which writes new questions about any book of the Bible. It uses **Ollama**, a free program
that runs an AI model on your own computer.

- **No account, no API key, no cost.**
- **Internet is needed only for the one-time downloads.** After that it works offline.
- **Nothing you do leaves your computer.**

The rest of the quiz (option 1, the checked question bank) does not need Ollama at all.

> **AI questions are not checked by a person.** Small models that run on a laptop make
> mistakes. The quiz reminds you of this on screen. Check the Bible reference if an answer
> looks wrong, and use option 1 for church events where accuracy matters.

---

## Quick start (about 10 minutes, mostly downloading)

| Step | What to do |
|---|---|
| 1 | Check your computer's memory (below) to choose a model |
| 2 | Install Ollama from <https://ollama.com/download> and open it once |
| 3 | In Terminal: `ollama pull qwen3:4b` (or `qwen3:8b`) |
| 4 | Test: `ollama run qwen3:4b "Who built the ark?"` |
| 5 | Start the quiz: `python3 main.py --model qwen3:4b`, then choose **2** |

Each step is explained below.

---

## Step 1: Choose a model

Check your memory: **Apple menu → About This Mac → Memory**
(Windows: **Settings → System → About → Installed RAM**).

| Your computer | Model | Download | Notes |
|---|---|---|---|
| 8 GB memory | `qwen3:4b` | about 2.5 GB | Faster, a bit less accurate |
| 16 GB or more | `qwen3:8b` | about 5 GB | Better questions, slower. The quiz's default |

Both handle English and Chinese. On a 16 GB computer you can still choose `qwen3:4b` if you
prefer speed and a smaller download.

**"8b" does not mean 8 GB.** The number in the model name is its size in **billions of
parameters**: `qwen3:8b` is the *bigger* model and needs roughly 6–8 GB of free memory,
while `qwen3:4b` is the smaller one for 8 GB computers.

---

## Step 2: Install Ollama

1. Go to <https://ollama.com/download> and download it for your computer.
2. **Mac:** open the download and drag **Ollama** into **Applications**, then open it.
   A small llama icon appears in the menu bar at the top of the screen.
   **Windows:** run the installer, then open Ollama from the Start menu.
3. If Ollama asks you to **sign in**, you can skip it. Signing in is only for Ollama's
   optional online models, which this quiz does not use.

**Typing just `ollama` in Terminal opens a menu** listing tools such as "Launch Claude Code",
"OpenCode" and so on. You don't need any of them. **Press `Esc`** to close it (don't press
Enter, or it will start installing one). Always type a full command such as `ollama pull …`.

---

## Step 3: Download the model (once)

Open **Terminal** (Mac: press Cmd + Space, type `Terminal`, press Enter) and type the line for
the model you chose:

```bash
ollama pull qwen3:4b
```

or

```bash
ollama pull qwen3:8b
```

Wait until it shows `success`. Check it is installed:

```bash
ollama list
```

---

## Step 4: Test that it works

```bash
ollama run qwen3:4b "Who built the ark?"
```

(Use `qwen3:8b` if that is the one you downloaded.) After a few seconds it should answer.
If it stays open waiting for more, type `/bye` and press Enter.

---

## Step 5: Use it in the quiz

Go to the quiz folder and start it. Replace the path with wherever your folder is; you can
type `cd ` and drag the folder into the Terminal window.

```bash
cd /Users/yourname/Downloads/bible_quiz
python3 main.py --model qwen3:4b
```

With `qwen3:8b` you can leave out `--model`, because it is the default.

Then:

1. Choose your language and translation.
2. In the main menu choose **2. Quiz by Bible Book (AI-generated)**.
3. Type a book by number, English name or Chinese name: `8`, `Ruth` or `路得记`.
   Type `0` to go back.
4. Choose **Easy**, **Intermediate** or **Advanced**.
5. Wait while the questions are written, then play as normal.

What you will see (real program output):

```
Book: ruth

========== Ruth: CHOOSE DIFFICULTY ==========

1. Easy — Basic Bible knowledge and familiar stories.
2. Intermediate — More detailed knowledge of Bible events, people, teachings, and references.
3. Advanced — More challenging questions requiring deeper knowledge of Scripture.
0. Back

Enter your choice: 1

Writing 10 Easy questions about Ruth with qwen3:4b...
(Running on your computer: this can take 1-3 minutes, longer the first time.)
```

**How long it takes:** about 1–3 minutes for 10 questions on a laptop. The first quiz after
opening Ollama is slower because the model has to load. The model then stays loaded for 15
minutes, so the next quiz is quicker. Fewer questions are faster: `--questions 5`.

---

## Make your model the default

So you can type plain `python3 main.py` without `--model` each time:

**Mac:**

```bash
echo 'export BIBLE_QUIZ_MODEL="qwen3:4b"' >> ~/.zshrc
source ~/.zshrc
```

**Windows (PowerShell):**

```powershell
setx BIBLE_QUIZ_MODEL "qwen3:4b"
```

Then close and reopen the terminal.

To undo it on a Mac, open `~/.zshrc` in a text editor and delete that line.

---

## Switching or deleting models

```bash
ollama list              # see which models you have and their sizes
ollama pull qwen3:4b     # download another model
ollama rm qwen3:8b       # delete a model to free disk space
```

You can keep more than one model and choose each time with `--model`. Any model from the
Ollama library works with the quiz, for example `--model gemma3:4b`, but the quiz was written
with Qwen in mind and smaller or older models may produce more rejected questions.

---

## Every time you use the book quiz

1. Make sure **Ollama is open** (the llama icon in the menu bar on a Mac).
2. Run the quiz as in Step 5.

The model unloads by itself after 15 minutes without use. To free memory immediately:
`ollama stop qwen3:4b`, or quit the Ollama app. `ollama ps` shows what is loaded right now.

---

## Troubleshooting

| What you see | What it means | What to do |
|---|---|---|
| A menu with "Launch Claude Code …" after typing `ollama` | That's Ollama's launcher | Press `Esc`. Type full commands like `ollama pull qwen3:4b` |
| `Ollama is not running` (in the quiz) | Ollama's background service is off | Open the Ollama app, or run `ollama serve` in a second Terminal window and leave it open |
| `could not connect to ollama` (in Terminal) | Same as above | Same as above |
| `The AI model 'qwen3:8b' is not downloaded yet` | The quiz is asking for a model you don't have | Run `ollama pull qwen3:8b`, or start the quiz with `--model` set to the model you have (`ollama list`) |
| `Ollama reported a problem … memory` | Not enough free memory for that model | Close other apps, or use the smaller model `--model qwen3:4b` |
| `Only 7 of 10 questions passed the checks` | Some AI questions were badly formed or pointed to verses that don't exist, and were thrown away | Nothing to fix; the quiz is just shorter |
| `None of the generated questions passed the checks` | Every question failed the checks | Try again; try `qwen3:8b` if your computer can run it |
| Very slow, or the Mac gets hot | The model works the processor hard | Normal on a laptop. Use `qwen3:4b`, or `--questions 5` |
| A question or answer seems wrong | The AI made a mistake | Check the reference in your Bible. Small models do make errors |
| Chinese quiz has some English, or old name spellings | Small models don't always follow the instructions | Try again, or use `qwen3:8b` |

---

## Removing Ollama

1. Delete the models to get the disk space back: `ollama rm qwen3:4b` (repeat for each one
   in `ollama list`). Models are stored in the `.ollama` folder in your home folder.
2. Quit Ollama, then delete it from **Applications** (Mac) or uninstall it from
   **Settings → Apps** (Windows).

The quiz itself keeps working without Ollama; only option 2 needs it.

---

## Using Claude instead (optional, paid)

If you have an Anthropic API key, `python3 main.py --ai claude` uses Claude, a larger
online model that usually writes more accurate questions. See README section 6.

---

## 中文快速指南

1. **选择模型：** 内存 8 GB 用 `qwen3:4b`（约 2.5 GB）；16 GB 或以上可用 `qwen3:8b`（约 5 GB）。
   注意：“8b”指 80 亿个参数，不是 8 GB 内存。
2. **安装 Ollama：** 从 <https://ollama.com/download> 下载并打开。不需要注册账号；如要求登录，可以跳过。
3. **下载模型：** 在终端输入 `ollama pull qwen3:4b`，等到显示 `success`。
   （只输入 `ollama` 会出现一个菜单，按 `Esc` 关闭即可。）
4. **测试：** `ollama run qwen3:4b "谁建造了方舟？"`
5. **开始问答：** `python3 main.py --model qwen3:4b`，在主菜单选择 **2. 按圣经书卷问答（AI 生成）**，
   输入书卷编号或名称（例如 `8` 或 `路得记`），再选择难度。出题约需 1 至 3 分钟。
6. **每次使用前**请先打开 Ollama 应用程序。

AI 生成的题目未经人工核对，可能有错误，请按经文出处查阅圣经核对。
