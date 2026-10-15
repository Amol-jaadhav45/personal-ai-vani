<<<<<<< HEAD
# 🤖 Vani — Autonomous Agentic AI Assistant

A modern, enterprise-ready Windows desktop assistant built with Python.
Vani utilizes a **ReAct (Reasoning and Acting) Agentic Loop** to autonomously write code, search the web, analyze screen context, and orchestrate systems through a sleek dark-mode GUI.

---

## ✨ Enterprise Features

| Feature | Details |
|---------|---------|
| 🧠 **Agentic Loop Engine** | Dynamically pauses to fetch, read, and analyze web data before answering. |
| �️ **Computer Vision** | Context-aware screen analysis via Gemini 1.5 Pro / GPT-4o Vision APIs. |
| 💻 **Dynamic Execution** | Autonomously writes and executes Python code to solve complex queries. |
| �️ **Realistic Human Voice** | Low-latency OpenAI TTS voice synthesis (with pyttsx3 offline fallback). |
| � **Infinite RAG Memory** | Embedded ChromaDB vector store for permanent semantic recall across sessions. |
| 🌐 **Autonomous Browsing** | Headless DuckDuckGo search + BeautifulSoup4 web scraper. |
| � **Conversational UI** | Modern dark-mode bubble UI (CustomTkinter) with continuous microphone listening. |
| 📊 **OS Intelligence** | Live CPU, RAM, Disk monitoring & file system CRUD operations. |

---

## 📁 System Architecture

```text
vani-ai-assistant/
│
├── main.py                    ← Entry point
├── requirements.txt           ← Python dependencies
├── .env                       ← API Keys (OpenAI, Gemini)
├── README.md
│
├── config/                    ← Configuration bindings
│   └── settings.py            ← Environment loading & prompt definitions
│
├── core/                      ← Brain & Cognitive Processes
│   ├── ai_engine.py           ← Multi-LLM wrapper (OpenAI, Gemini, Groq)
│   ├── command_dispatcher.py  ← ReAct loop routing and tool hooking
│   ├── memory.py              ← SQLite transactional history
│   └── rag_memory.py          ← ChromaDB Infinite Semantic Vector Database
│
├── tools/                     ← Agentic Capabilities
│   ├── python_executor.py     ← Dynamic code execution engine
│   ├── vision.py              ← Screen capture & LLM vision analysis
│   ├── search_engine.py       ← Headless DuckDuckGo search
│   ├── web_scraper.py         ← Autonomous URL content extraction
│   ├── app_launcher.py        ← Windows process management
│   ├── file_ops.py            ← System IO & automation
│   ├── system_info.py         ← OS telemetry (psutil)
│   └── youtube/spotify        ← Automated media controllers
│
├── voice/                     ← Speech Systems
│   ├── speech_to_text.py      ← VAD & Wake-word detection ("Hey Vani")
│   └── text_to_speech.py      ← OpenAI human voice & pyttsx3 threaded synthesis
│
├── gui/                       ← Presentation Layer (MVC)
│   └── main_window.py         ← Root interface, threads, and UI bindings
│
├── scripts/                   ← Dev utilities (audio tests, diag)
├── tests/                     ← Unit testing suite
├── logs/                      ← Rotating debug telemetry
└── data/                      ← Local databases (SQLite & ChromaDB)
```

---

## ⚡ Quick Start

### 1. Prerequisites

- **Python 3.10+** (download from [python.org](https://python.org))
- **Windows 10/11**
- **Microphone** (optional, for voice commands)
- **OpenAI API key** (optional — basic commands work without it)

---

### 2. Install Dependencies

Open a terminal in the project folder and run:

```bash
pip install -r requirements.txt
```

> **PyAudio Note:** If `pip install PyAudio` fails on Windows, use:
> ```bash
> pip install pipwin
> pipwin install pyaudio
> ```
> Or download the wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

---

### 3. Configure Environment

```bash
# Copy the template
copy .env.example .env

# Edit .env with your favourite text editor
notepad .env
```

Set your OpenAI API key:

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

> **No API key?** The app runs in Offline Mode with keyword-based commands.

---

### 4. Run the Application

```bash
python main.py
```

---

## 🗣️ Example Commands

### Typing or Speaking:

| Command | What Vani Does |
|---------|---------------|
| `Open Chrome` | Launches Google Chrome |
| `Open Notepad` | Launches Notepad |
| `Open Calculator` | Launches Calculator |
| `Open VS Code` | Launches VS Code |
| `Search Python tutorials` | Google search in browser |
| `Open https://github.com` | Opens the URL |
| `Take a screenshot` | Captures screen → saves to Desktop |
| `Show system info` | Displays CPU, RAM, Disk usage |
| `Show CPU usage` | Shows CPU stats only |
| `List files in C:\Users` | Lists directory contents |
| `Create folder C:\MyProject` | Creates a new folder |
| `Delete file C:\test.txt` | Asks confirmation → deletes |

### AI Conversation (with API key):

| You say | Vani responds |
|---------|--------------|
| `What is machine learning?` | Explains ML in plain English |
| `Write a Python hello world program` | Provides code |
| `Remind me how to use Git` | Git tutorial |
| `What's the capital of France?` | Paris |

---

## ⚙️ Configuration Reference

Edit `.env` to customise behaviour:

```env
# AI Settings
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini     # or gpt-4, gpt-3.5-turbo
MAX_TOKENS=1024
TEMPERATURE=0.7              # 0.0 = focused, 1.0 = creative

# Text-to-Speech
TTS_RATE=175                 # Words per minute
TTS_VOLUME=0.9               # 0.0 to 1.0

# Voice Input
VOICE_TIMEOUT=5              # Seconds to wait for speech
VOICE_PHRASE_LIMIT=10        # Max recording duration

# Custom App Paths (if not in system PATH)
CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe
VSCODE_PATH=C:\Users\YourName\AppData\Local\Programs\Microsoft VS Code\Code.exe
```

---

## 🔧 Troubleshooting

### PyAudio installation fails
```bash
pip install pipwin
pipwin install pyaudio
```

### "No module named 'customtkinter'"
```bash
pip install customtkinter
```

### Voice not working
- Ensure your microphone is connected and set as default in Windows Sound Settings.
- Check that `SpeechRecognition` and `PyAudio` are installed.
- Voice recognition requires an internet connection (uses Google's free STT API).

### App won't open (Chrome, VS Code)
- Set the full path in `.env` under `CHROME_PATH=` or `VSCODE_PATH=`.

### AI responses not working
- Verify `OPENAI_API_KEY` is correctly set in `.env`.
- Check your OpenAI account has credits.

---

## 📋 Dependencies

| Package | Purpose |
|---------|---------|
| `customtkinter` | Modern dark-mode GUI widgets |
| `openai` | GPT API integration |
| `python-dotenv` | Load .env configuration |
| `pyttsx3` | Offline text-to-speech |
| `SpeechRecognition` | Microphone → text |
| `PyAudio` | Audio input device support |
| `Pillow` | Image processing (screenshots) |
| `psutil` | CPU / RAM / Disk monitoring |
| `pyautogui` | Screenshot capture |
| `requests` | HTTP utilities |

---

## 📝 Logs

Log files are saved in the `logs/` directory:
- `ai_laptop_assistant.log` — rotating, max 5 MB × 3 files
- Console shows INFO level; file records DEBUG level

---

## 🏗️ Architecture Notes (for Students)

This project follows **Separation of Concerns**:

1. **`config/`** — all settings in one place; nothing else reads `.env` directly
2. **`core/`** — reusable business logic (AI, DB, routing) with no GUI dependency
3. **`tools/`** — independent, testable functions; each returns `(bool, str)`
4. **`voice/`** — hardware abstraction behind clean Python classes
5. **`gui/`** — purely presentation; calls core/tools, never the other way around

This makes the code easy to test, extend, and understand.

---

## 🎓 College Project Notes

- **SQLite** used without any ORM — demonstrates raw SQL skills
- **Threading** used for AI calls and TTS/STT to keep the GUI responsive
- **Design patterns**: Factory (logger), Callback (STT events), Dispatcher (routing)
- **Security**: API keys in `.env`, never committed; destructive ops require confirmation

---

## 📄 License

MIT License — free to use for educational purposes.
=======
# personal-ai-vani
>>>>>>> 5cd8d82c30d4bd6d373d466f2de74ec98abaf71a
