# 🚀 Profile Optimizer — Complete Career Toolkit

AI-powered career toolkit that optimizes your LinkedIn, GitHub, resume, interview prep, job search, and more — all in one app.

Works with **any AI model**: Claude, OpenAI GPT-4o, Google Gemini (free), Groq (free), or Ollama (free, local, offline).

---

## What This Tool Does

One app, 10 tools — upload your LinkedIn PDF once, use everywhere:

| # | Tool | Input | Output |
|---|------|-------|--------|
| 1 | **📋 LinkedIn Optimizer** | LinkedIn PDF | Rewritten headline, about, experience bullets, skills order |
| 2 | **🐙 GitHub Optimizer** | GitHub username | Optimized bio, profile README.md, repo descriptions, pin list |
| 3 | **🎯 JD Matcher** | LinkedIn PDF + Job Description | Match score %, skill gaps, "should I apply?" verdict |
| 4 | **📄 ATS Resume** | LinkedIn PDF | Clean, ATS-friendly resume (Markdown) |
| 5 | **🛠️ Project Suggestions** | LinkedIn PDF + target role | 7 project ideas with tech stack, difficulty, time estimate |
| 6 | **🎤 Interview Prep** | LinkedIn PDF + role + company | Personalized questions, sample answers, salary range |
| 7 | **📧 Cold Outreach** | LinkedIn PDF + target company | 9 templates: LinkedIn DMs, cold emails, referral requests |
| 8 | **📊 Skills Gap Analysis** | LinkedIn PDF + target role | Market readiness score, learning roadmap month-by-month |
| 9 | **🔍 Job Keywords** | LinkedIn PDF + location | Search strings for LinkedIn, Naukri, Indeed, Google |
| 10 | **✉️ Cover Letter** | LinkedIn PDF + Job Description | Tailored cover letter ready to send |

---

## Supported AI Providers

You choose which AI to use. You are NOT locked into any one provider.

| Provider | Cost per use | Speed | Quality | Free Tier? |
|----------|-------------|-------|---------|------------|
| **Claude** (Anthropic) | ~$0.01–0.05 | Fast | ⭐⭐⭐⭐⭐ | No (pay-per-use) |
| **OpenAI** (GPT-4o) | ~$0.01–0.05 | Fast | ⭐⭐⭐⭐⭐ | $5 free credit on signup |
| **Google Gemini** | **Free** | Fast | ⭐⭐⭐⭐ | ✅ Yes — generous free tier |
| **Groq** (Llama 3, Mixtral) | **Free** | Fastest | ⭐⭐⭐⭐ | ✅ Yes — free tier |
| **Ollama** (runs on your PC) | **Free forever** | Slow (depends on PC) | ⭐⭐⭐ | ✅ Fully offline, no account needed |

### Where to get API keys

| Provider | Signup Link | Steps |
|----------|------------|-------|
| **Claude** | https://console.anthropic.com | Sign up → API Keys → Create Key → copy `sk-ant-...` |
| **OpenAI** | https://platform.openai.com/api-keys | Sign up → API Keys → Create → copy `sk-...` |
| **Gemini** | https://aistudio.google.com/apikey | Sign in with Google → Get API Key → copy |
| **Groq** | https://console.groq.com/keys | Sign up → API Keys → Create → copy `gsk_...` |
| **Ollama** | https://ollama.com | Download & install → no key needed |

---

## Installation & Setup

### Prerequisites

- **Python 3.10 or higher** — check with `python3 --version`
- **pip** — comes with Python, check with `pip --version`
- **Internet connection** — for GitHub API and AI provider API calls
- **A web browser** — app opens in your default browser

### Step 1: Download the project

**Option A — Git clone:**
```bash
git clone https://github.com/humaniods/careerkit.git
cd careerkit
```

**Option B — Manual download:**
1. Download the ZIP from GitHub
2. Extract it
3. Open terminal in the extracted folder

### Step 2: Install dependencies

```bash
pip install -r requirements.txt
```

This installs:
| Package | What it does | Size |
|---------|-------------|------|
| `streamlit` | Web UI (the app runs in browser) | ~80MB |
| `pdfplumber` | Reads text from LinkedIn PDF | ~5MB |
| `requests` | Calls GitHub API, Gemini API, Groq API | ~1MB |
| `anthropic` | Claude AI SDK (skip if not using Claude) | ~5MB |
| `openai` | OpenAI SDK (skip if not using OpenAI) | ~5MB |

**If you only want free providers (Gemini/Groq/Ollama):**
```bash
pip install streamlit pdfplumber requests
```
No `anthropic` or `openai` needed — Gemini and Groq use REST API directly.

### Step 3: Run the app

```bash
streamlit run app.py
```

**What happens:**
1. Terminal shows: `Local URL: http://localhost:8501`
2. Browser opens automatically at that URL
3. If browser doesn't open, manually go to `http://localhost:8501`

### Step 4: First-time setup (in the app)

1. **Left sidebar** → Select your AI provider (e.g., "Google Gemini" for free)
2. **Enter API key** → paste your key (see table above for where to get one)
3. **Key saves automatically** → stored locally at `~/.profile_optimizer/config.json`
4. You only do this once — next time the key is already there

### Step 5: Start using

1. Go to **📋 LinkedIn** tab
2. Upload your LinkedIn PDF
3. Click **Optimize** → get results
4. Switch to other tabs — your profile is already loaded, no re-upload needed

---

## How to Get Your LinkedIn PDF

1. Open LinkedIn in a browser (not the mobile app)
2. Go to **your profile page**
3. Click the **More** button (below your banner image)
4. Click **Save to PDF**
5. A PDF file downloads — this is what you upload in the app

---

## How to Stop the App

Press `Ctrl+C` in the terminal where you ran `streamlit run app.py`.

---

## Using Ollama (Free, Local, Offline)

Ollama runs AI models on your own computer — completely free, no account, no internet needed for AI.

### Setup Ollama

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Mac:**
```bash
brew install ollama
```

**Windows:**
Download from https://ollama.com/download

### Pull a model

```bash
ollama pull llama3.1
```

This downloads the model (~4.7GB for llama3.1 8B). One-time download.

### Start the server

```bash
ollama serve
```

Keep this terminal open. Then in another terminal, run the app:

```bash
streamlit run app.py
```

Select **"Ollama (Local — Free)"** in the sidebar. Your downloaded models show up automatically.

### Which Ollama model to use?

| Model | RAM Needed | Quality | Speed |
|-------|-----------|---------|-------|
| `llama3.1` (8B) | 8GB | Good | Fast |
| `llama3.1:70b` | 40GB | Great | Slow |
| `mistral` (7B) | 8GB | Good | Fast |
| `qwen2.5` (7B) | 8GB | Good | Fast |

For most PCs, `llama3.1` works fine.

---

## Detailed Tool Guide

### 📋 LinkedIn Optimizer
**What you get:**
- Rewritten headline (under 220 chars, ATS keyword-rich)
- New About section (hook-first, action verbs, CTA at end)
- Experience bullets rewritten in STAR format (Situation → Action → Result)
- Skills reordered by recruiter relevance
- 30-second elevator pitch
- LinkedIn post idea for visibility
- List of issues found and fixed in your current profile

### 🎯 JD Matcher
**What you get:**
- Match score (0-100%)
- "Should I Apply?" verdict (Yes/No/Maybe)
- Matching skills vs missing skills
- Keyword gaps
- Tailored headline for THAT specific job
- Resume bullets to add for THAT role
- 5-step action plan to improve chances

### 📄 ATS Resume
**What it fixes:**
- Removes fancy formatting (ATS can't read columns/tables)
- Uses strong action verbs (Built, Developed, Optimized)
- Adds metrics and numbers
- Includes relevant keywords naturally
- Clean structure: Summary → Experience → Skills → Education

### 🛠️ Project Suggestions
**What you get per project:**
- Project name + tagline
- Why it helps (fills which skill gap)
- Full tech stack
- Difficulty level + time estimate
- Key features to implement
- GitHub repo description (ready to paste)
- Why recruiters would be impressed

### 🎤 Interview Prep
**Choose interview type:**
- Technical + Behavioral (Mixed)
- Technical Deep Dive
- Behavioral / Culture Fit
- System Design
- HR / Screening Round

**What you get:**
- Opening pitch for "Tell me about yourself"
- 10-15 questions with personalized answers from YOUR experience
- Questions to ask the interviewer
- Red flags to avoid
- Salary range suggestion

### 📧 Cold Outreach (9 templates)
1. LinkedIn connection note (under 300 chars)
2. DM to recruiter
3. DM to hiring manager
4. DM asking for referral
5. DM to startup founder/CTO
6. Cold email template
7. Follow-up after no response
8. Referral request to friend
9. Thank you after interview

### 📊 Skills Gap Analysis
**What you get:**
- Market readiness score (0-100%)
- Skills you have vs skills required
- Each gap ranked: Critical / Important / Nice-to-have
- How to learn each skill + time estimate
- Month-by-month learning roadmap with specific resources
- Certifications to get

### 🔍 Job Keywords
**Search strings for:**
- LinkedIn Jobs (10 queries)
- Naukri.com (10 queries)
- Indeed (10 queries)
- Google Jobs (5 queries like `site:lever.co "AI Engineer" "India"`)
- Advanced boolean search string
- 15 job title variations to search
- 20 companies to target
- Niche job boards for your field
- Hashtags to follow
- Google Alerts to set

### ✉️ Cover Letter
**What makes it good:**
- Opens with a hook (not "I am writing to apply")
- Connects YOUR experience to job requirements
- Shows company knowledge
- Includes 2-3 achievements with numbers
- Ends with confident call to action
- Under 400 words, sounds human

---

## Smart Profile Sharing

Upload your LinkedIn PDF **once** in any tab → it's automatically available in **all other tabs**. No re-uploading.

---

## Project Structure

```
careerkit/
├── app.py                 # Main app — all 10 tools (Streamlit)
├── requirements.txt       # Python dependencies
├── .gitignore             # Blocks secrets & generated files
└── README.md              # This file
```

---

## Privacy & Security

- **API keys** saved locally at `~/.profile_optimizer/config.json` — never uploaded anywhere
- **Your profile data** is sent ONLY to the AI provider you choose — not stored on any server
- **No analytics, no tracking, no telemetry** — the app doesn't phone home
- **With Ollama:** fully offline — zero data leaves your machine
- **App runs locally** on your computer at `localhost:8501` — not accessible from internet

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: No module named 'streamlit'` | Dependencies not installed | Run `pip install -r requirements.txt` |
| `ModuleNotFoundError: No module named 'anthropic'` | Using Claude without SDK | Run `pip install anthropic` |
| `ModuleNotFoundError: No module named 'openai'` | Using OpenAI without SDK | Run `pip install openai` |
| App says "Enter API key" | Key not set | Paste your API key in the sidebar |
| "API Error: 401" | Invalid API key | Check your key is correct, not expired |
| "API Error: 429" | Rate limited | Wait a minute and try again, or switch provider |
| PDF text extraction is empty | LinkedIn PDF format issue | Re-export PDF from LinkedIn using Chrome browser |
| GitHub fetch fails | Wrong username or private profile | Check spelling, ensure profile is public |
| JSON parse error | AI gave malformed response | Click the button again, or try a different model |
| Ollama not found / connection refused | Ollama server not running | Run `ollama serve` in a separate terminal |
| Ollama response very slow | Model too large for your PC | Use smaller model: `ollama pull llama3.1` |
| Browser doesn't open | Headless/SSH environment | Manually open `http://localhost:8501` |
| Port 8501 already in use | Another Streamlit running | Kill it: `pkill -f streamlit` then retry |
| `python3: command not found` | Python not installed | Install Python 3.10+ from python.org |

---

## FAQ

**Q: Is this free?**
A: The app itself is free. AI costs depend on provider — Gemini, Groq, and Ollama are free.

**Q: Is my data safe?**
A: Yes. Everything runs locally. Data goes only to the AI provider you pick.

**Q: Can I use this without internet?**
A: Partially. With Ollama, AI runs offline. But GitHub fetch still needs internet.

**Q: Which provider is best?**
A: Claude and GPT-4o give best quality. Gemini is best free option. Groq is fastest.

**Q: Do I need all dependencies?**
A: No. If you only use Gemini/Groq/Ollama: `pip install streamlit pdfplumber requests` is enough.

---

## License

MIT — use it, modify it, share it.
