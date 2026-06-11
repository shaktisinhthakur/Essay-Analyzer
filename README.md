# UPSC Essay Analyzer 🎓

A Django-based web application that uses AI to evaluate UPSC (Union Public Service Commission) essays across three key dimensions: **Language**, **Analysis**, and **Clarity** — powered by your own API key (BYOK).

---

## ✨ Features

- 🤖 **Multi-Provider AI Support** — Groq, Anthropic (Claude), OpenAI (GPT), Google Gemini
- 📊 **3-Dimension Evaluation** — Language quality, Depth of analysis, Clarity & structure
- 🏷️ **Mistake Tagging** — Color-coded tags with tooltip descriptions for each mistake
- ⚡ **Parallel Processing** — All 3 dimensions evaluated simultaneously using `ThreadPoolExecutor`
- 🔑 **BYOK (Bring Your Own Key)** — Your API key is never stored; it lives only in your browser session
- 📱 **Responsive Design** — Works on desktop and mobile
- 🔢 **Live Word Count** — Real-time word counter as you type

---

## 🖥️ Demo

| Metric | Description |
|--------|-------------|
| **Language** | Grammar, vocabulary, sentence structure, writing style |
| **Analysis** | Multiple perspectives, examples, critical thinking, root causes |
| **Clarity** | Introduction, body, conclusion, paragraph flow, logical coherence |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Django 6.0 |
| Frontend | Vanilla HTML, CSS, JavaScript |
| Database | SQLite (dev) |
| AI Providers | Groq, OpenAI, Anthropic, Google Gemini |
| Concurrency | Python `ThreadPoolExecutor` |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- pip
- An API key from **at least one** of the supported providers:
  - [Groq](https://console.groq.com/) ← Free & fastest
  - [OpenAI](https://platform.openai.com/)
  - [Anthropic](https://console.anthropic.com/)
  - [Google AI Studio](https://aistudio.google.com/)

---

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/your-username/upsc-essay-analyzer.git
cd upsc-essay-analyzer/essay
```

**2. Create a virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install django requests
```

**4. Run database migrations**
```bash
python manage.py migrate
```

**5. Start the development server**
```bash
python manage.py runserver
```

**6. Open your browser**
```
http://127.0.0.1:8000
```

---

## 📖 How to Use

1. **Select a Provider** — Choose from Groq, OpenAI, Anthropic, or Gemini
2. **Select a Model** — Pick the AI model you want to use
3. **Enter your API Key** — Paste your API key (it's never stored or sent anywhere except the provider)
4. **Paste your Essay** — Type or paste your UPSC essay in the text area
5. **Click "Analyze Essay"** — The button activates automatically when all fields are filled
6. **View Results** — See scores and detailed feedback for each dimension

---

## 🤖 Supported Models

| Provider | Models |
|----------|--------|
| **Groq** | `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `qwen/qwen3-32b` |
| **Anthropic** | `claude-opus-4`, `claude-sonnet-4`, `claude-haiku-4-5` |
| **OpenAI** | `gpt-4o`, `gpt-4o-mini`, `gpt-3.5-turbo` |
| **Google Gemini** | `gemini-1.5-pro`, `gemini-1.5-flash`, `gemini-2.0-flash` |

> **Tip:** Groq is free and extremely fast — great for testing!

---

## 📁 Project Structure

```
essay/
├── analyzer/                    # Main Django app
│   ├── templates/
│   │   └── analyzer/
│   │       └── index.html       # Single-page UI
│   ├── views.py                 # API logic, LLM calls, prompt engineering
│   ├── urls.py                  # App URL routes
│   ├── models.py
│   └── apps.py
├── essay_project/               # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
└── db.sqlite3                   # Auto-generated SQLite DB
```

---

## 🔑 API Key Security

This app uses a **BYOK (Bring Your Own Key)** model:

- ✅ Your API key is entered in the browser and sent only to the AI provider
- ✅ The key is **never stored** in the database or server logs
- ✅ The key lives only in your current browser session
- ❌ Never commit your API key to GitHub — use `.env` files locally

---

## ⚙️ Environment Variables (Optional)

If you want to pre-configure a default API key for local development, create a `.env` file in the project root. **Never commit this file.**

```env
# .env  (DO NOT COMMIT)
GROQ_API_KEY=your_groq_key_here
```

---

## 🐛 Known Issues & Fixes

### `'score'` error on Analyze
**Cause:** Python's `.format()` was interpreting `{score}` in the prompt template as a format placeholder.  
**Fix:** Escaped JSON schema braces in prompt strings using `{{` and `}}`.

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 🙌 Acknowledgements

- [Groq](https://groq.com/) for ultra-fast LLM inference
- [Django](https://www.djangoproject.com/) for the web framework
- UPSC aspirants who inspired this tool 🇮🇳
