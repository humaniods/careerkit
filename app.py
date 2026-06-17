#!/usr/bin/env python3
"""
Profile Optimizer — Complete Career Toolkit
Streamlit UI — runs locally on your PC
Supports: Claude, OpenAI, Gemini, Groq, Ollama (local/free)

Features:
  1. LinkedIn Profile Optimizer
  2. GitHub Profile Optimizer
  3. JD Matcher (match score + gaps)
  4. ATS Resume Generator
  5. Project Suggestions
  6. Interview Prep
  7. Cold Outreach Templates
  8. Skills Gap Analysis
  9. Job Keywords Generator
  10. Cover Letter Generator
"""

import streamlit as st
import requests
import pdfplumber
import json
from datetime import datetime
from pathlib import Path

# ── Config ──────────────────────────────────────
CONFIG_DIR = Path.home() / ".profile_optimizer"
CONFIG_FILE = CONFIG_DIR / "config.json"
GITHUB_API = "https://api.github.com"

# ── Provider definitions ────────────────────────
PROVIDERS = {
    "Claude (Anthropic)": {
        "key_name": "anthropic_api_key",
        "key_help": "Get from [console.anthropic.com](https://console.anthropic.com) → API Keys",
        "models": ["claude-sonnet-4-6", "claude-haiku-4-5-20251001", "claude-opus-4-6"],
        "needs_key": True,
    },
    "OpenAI": {
        "key_name": "openai_api_key",
        "key_help": "Get from [platform.openai.com](https://platform.openai.com/api-keys) → API Keys",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "o3-mini"],
        "needs_key": True,
    },
    "Google Gemini": {
        "key_name": "gemini_api_key",
        "key_help": "Get from [aistudio.google.com](https://aistudio.google.com/apikey) → Get API Key",
        "models": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"],
        "needs_key": True,
    },
    "Groq": {
        "key_name": "groq_api_key",
        "key_help": "Get from [console.groq.com](https://console.groq.com/keys) → API Keys (free tier available)",
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"],
        "needs_key": True,
    },
    "Ollama (Local — Free)": {
        "key_name": None,
        "key_help": "Install from [ollama.com](https://ollama.com). Run: `ollama pull llama3.1`",
        "models": [],
        "needs_key": False,
    },
}


# ══════════════════════════════════════════════════
#  UTILITY FUNCTIONS
# ══════════════════════════════════════════════════

def load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(data: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, indent=2))


def extract_text_from_pdf(pdf_file) -> str:
    text_parts = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts)


def get_ollama_models() -> list[str]:
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=3)
        if resp.status_code == 200:
            return [m["name"] for m in resp.json().get("models", [])]
    except Exception:
        pass
    return []


def fetch_github_data(username: str) -> dict | None:
    headers = {"Accept": "application/vnd.github+json"}

    user_resp = requests.get(f"{GITHUB_API}/users/{username}", headers=headers, timeout=10)
    if user_resp.status_code != 200:
        return None
    user = user_resp.json()

    repos_resp = requests.get(
        f"{GITHUB_API}/users/{username}/repos",
        headers=headers,
        params={"sort": "updated", "per_page": 30, "type": "public"},
        timeout=10,
    )
    repos_raw = repos_resp.json() if repos_resp.status_code == 200 else []

    repos = []
    for r in repos_raw:
        if not r.get("fork"):
            repos.append({
                "name": r.get("name"),
                "description": r.get("description") or "No description",
                "language": r.get("language") or "Unknown",
                "stars": r.get("stargazers_count", 0),
                "forks": r.get("forks_count", 0),
                "topics": r.get("topics", []),
                "url": r.get("html_url"),
                "updated": r.get("updated_at", "")[:10],
            })
    repos.sort(key=lambda x: x["stars"], reverse=True)

    lang_count = {}
    for r in repos:
        lang = r.get("language")
        if lang and lang != "Unknown":
            lang_count[lang] = lang_count.get(lang, 0) + 1
    top_langs = sorted(lang_count, key=lang_count.get, reverse=True)[:6]

    readme_resp = requests.get(
        f"{GITHUB_API}/repos/{username}/{username}/readme",
        headers=headers,
        timeout=10,
    )

    return {
        "username": username,
        "name": user.get("name") or username,
        "bio": user.get("bio") or "No bio set",
        "location": user.get("location") or "Not set",
        "public_repos": user.get("public_repos", 0),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "has_profile_readme": readme_resp.status_code == 200,
        "top_languages": top_langs,
        "repos": repos[:15],
    }


# ══════════════════════════════════════════════════
#  AI CALL — MULTI PROVIDER
# ══════════════════════════════════════════════════

def call_ai(provider: str, api_key: str, model: str, prompt: str) -> str:
    if provider == "Claude (Anthropic)":
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=model,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()

    elif provider == "OpenAI":
        import openai
        client = openai.OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content.strip()

    elif provider == "Google Gemini":
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

    elif provider == "Groq":
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "max_tokens": 8192, "messages": [{"role": "user", "content": prompt}]},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    elif provider == "Ollama (Local — Free)":
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=300,
        )
        resp.raise_for_status()
        return resp.json()["response"].strip()

    raise ValueError(f"Unknown provider: {provider}")


def parse_json_response(raw: str) -> dict | None:
    text = raw.strip()
    if "```" in text:
        start = text.index("```")
        end = text.rindex("```")
        if start != end:
            inner = text[start + 3:end]
            if inner.startswith("json"):
                inner = inner[4:]
            text = inner.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def ai_call_with_json(provider, api_key, model, prompt) -> dict | None:
    """Call AI and parse JSON response. Returns dict or None."""
    try:
        raw = call_ai(provider, api_key, model, prompt)
        return parse_json_response(raw)
    except Exception as e:
        st.error(f"❌ API Error: {e}")
        return None


def ai_call_with_text(provider, api_key, model, prompt) -> str | None:
    """Call AI and return raw text. Returns str or None."""
    try:
        return call_ai(provider, api_key, model, prompt)
    except Exception as e:
        st.error(f"❌ API Error: {e}")
        return None


# ══════════════════════════════════════════════════
#  SHARED: Get profile text from session or upload
# ══════════════════════════════════════════════════

def get_profile_text_widget(key_prefix: str) -> str | None:
    """Show PDF uploader or use cached profile text. Returns text or None."""
    if "profile_text" in st.session_state and st.session_state["profile_text"]:
        st.success("✅ Using your uploaded LinkedIn profile (from LinkedIn tab or previous upload)")
        with st.expander("📄 View profile text", expanded=False):
            st.text_area("Profile", st.session_state["profile_text"], height=200, disabled=True, key=f"{key_prefix}_preview")
        return st.session_state["profile_text"]

    pdf = st.file_uploader(
        "Upload your LinkedIn PDF",
        type=["pdf"],
        help="LinkedIn → Your Profile → More → Save to PDF",
        key=f"{key_prefix}_pdf",
    )
    if pdf:
        text = extract_text_from_pdf(pdf)
        if text.strip():
            st.session_state["profile_text"] = text
            return text
        st.error("❌ Could not extract text from PDF.")
    return None


# ══════════════════════════════════════════════════
#  TAB 1: LINKEDIN OPTIMIZER
# ══════════════════════════════════════════════════

def tab_linkedin(provider, api_key, model):
    st.header("📋 LinkedIn Profile Optimizer")
    st.markdown("""
    **How it works:**
    1. Go to your LinkedIn profile → Click **More** → **Save to PDF**
    2. Upload that PDF below
    3. Get an optimized profile ready to copy-paste!
    """)

    col1, col2 = st.columns([2, 1])
    with col1:
        pdf_file = st.file_uploader("Upload your LinkedIn PDF", type=["pdf"], key="li_pdf")
    with col2:
        target = st.text_input("Target Roles (optional)", placeholder="e.g., AI Engineer at startups", key="li_target")

    if pdf_file:
        pdf_text = extract_text_from_pdf(pdf_file)
        st.session_state["profile_text"] = pdf_text

        with st.expander("📄 Preview extracted text", expanded=False):
            st.text_area("Extracted Text", pdf_text, height=300, disabled=True)

        if st.button("🚀 Optimize LinkedIn Profile", type="primary", key="btn_li"):
            if not pdf_text.strip():
                st.error("❌ Could not extract text from PDF.")
                return

            prompt = f"""You are an elite personal branding expert and technical recruiter.

TASK: Rewrite this LinkedIn profile to MAXIMALLY impress recruiters and pass ATS systems.

TARGET ROLES: {target or 'general tech roles'}

LINKEDIN PROFILE (from PDF):
{pdf_text}

RULES:
1. Headline: under 220 chars, scannable, keyword-rich for ATS
2. About: hook first line, NO "I am passionate about", action verbs, CTA at end, 3-4 paragraphs
3. Experience: STAR format bullets — Situation→Action→Result. Tech stack names. Numbers.
4. Skills: reorder by recruiter relevance
5. Fix all issues (wrong titles, vague bullets, missing keywords)

Return ONLY valid JSON:
{{
  "name": "detected name",
  "headline": "rewritten headline, max 220 chars",
  "about": "full About section, use \\n\\n between paragraphs",
  "experience": [
    {{"title": "Job Title", "company": "Company", "duration": "dates", "bullets": ["bullet1", "bullet2"]}}
  ],
  "skills_priority_order": ["top 15 skills"],
  "certifications_to_highlight": ["top certs"],
  "30_sec_pitch": "elevator pitch, 5 sentences",
  "linkedin_post_idea": "1 post idea for this week",
  "issues_found_and_fixed": ["issues found and fixed"],
  "ats_keywords": ["20 high-value keywords"],
  "estimated_impact": "1 sentence"
}}"""

            with st.spinner(f"🧠 {provider} optimizing your profile..."):
                result = ai_call_with_json(provider, api_key, model, prompt)

            if result:
                st.session_state["li_result"] = result

    if "li_result" in st.session_state:
        r = st.session_state["li_result"]
        st.success("✅ Profile optimized!")

        st.subheader("🏷️ New Headline")
        st.code(r.get("headline", ""), language=None)

        st.subheader("📝 New About Section")
        st.markdown(r.get("about", ""))

        st.subheader("💼 Experience (Rewritten)")
        for exp in r.get("experience", []):
            st.markdown(f"**{exp.get('title', '')}** — {exp.get('company', '')}")
            st.caption(exp.get("duration", ""))
            for b in exp.get("bullets", []):
                st.markdown(f"- {b}")
            st.divider()

        st.subheader("🔑 Skills (Priority Order)")
        st.markdown(" → ".join(r.get("skills_priority_order", [])))

        st.subheader("🎤 30-Second Pitch")
        st.info(r.get("30_sec_pitch", ""))

        issues = r.get("issues_found_and_fixed", [])
        if issues:
            st.subheader("🛠️ Issues Found & Fixed")
            for i in issues:
                st.markdown(f"- ✅ {i}")

        impact = r.get("estimated_impact", "")
        if impact:
            st.metric("🎯 Estimated Impact", impact)

        # Download
        md = _linkedin_to_md(r)
        st.download_button("📥 Download as Markdown", data=md,
                           file_name=f"linkedin_optimized_{datetime.now().strftime('%Y%m%d')}.md", mime="text/markdown")


def _linkedin_to_md(d: dict) -> str:
    lines = [f"# LinkedIn Profile — Optimized",
             f"**Generated:** {datetime.now().strftime('%d %b %Y, %I:%M %p')}\n",
             f"## Headline\n", d.get("headline", ""), "",
             f"## About\n", d.get("about", ""), "",
             f"## Experience\n"]
    for exp in d.get("experience", []):
        lines += [f"### {exp.get('title', '')} — {exp.get('company', '')}",
                  f"*{exp.get('duration', '')}*\n"]
        lines += [f"- {b}" for b in exp.get("bullets", [])]
        lines.append("")
    lines.append("## Skills (Priority Order)\n")
    lines += [f"{i}. {s}" for i, s in enumerate(d.get("skills_priority_order", []), 1)]
    lines += ["", f"## 30-Second Pitch\n", d.get("30_sec_pitch", ""), ""]
    kw = d.get("ats_keywords", [])
    if kw:
        lines += [f"## ATS Keywords\n", " • ".join(kw), ""]
    return "\n".join(lines)


# ══════════════════════════════════════════════════
#  TAB 2: GITHUB OPTIMIZER
# ══════════════════════════════════════════════════

def tab_github(provider, api_key, model):
    st.header("🐙 GitHub Profile Optimizer")
    st.markdown("Enter your GitHub username → auto-fetch repos → AI generates optimized bio, README.md, repo descriptions.")

    col1, col2 = st.columns([2, 1])
    with col1:
        username = st.text_input("GitHub Username", placeholder="e.g., torvalds", key="gh_user")
    with col2:
        target = st.text_input("Target Roles (optional)", placeholder="e.g., Backend Engineer", key="gh_target")

    if username:
        if st.button("🔍 Fetch & Analyze", key="btn_gh_fetch"):
            with st.spinner(f"Fetching @{username}..."):
                gh = fetch_github_data(username)
            if gh is None:
                st.error(f"❌ Could not fetch @{username}. Check username.")
            else:
                st.session_state["gh_data"] = gh
                st.success(f"✅ Found {len(gh['repos'])} repos | {gh['followers']} followers")

    if "gh_data" in st.session_state:
        gh = st.session_state["gh_data"]
        with st.expander("📊 Fetched Data", expanded=False):
            c1, c2, c3 = st.columns(3)
            c1.metric("Repos", gh["public_repos"])
            c2.metric("Followers", gh["followers"])
            c3.metric("README", "✅" if gh["has_profile_readme"] else "❌")
            st.markdown(f"**Bio:** {gh['bio']}")
            st.markdown(f"**Languages:** {', '.join(gh['top_languages'])}")
            for r in gh["repos"][:8]:
                st.markdown(f"- **{r['name']}** ⭐{r['stars']} | {r['language']} — {r['description'][:60]}")

        if st.button("🚀 Optimize GitHub Profile", type="primary", key="btn_gh"):
            repos_summary = "\n".join([
                f"  - [{r['name']}] ⭐{r['stars']} | {r['language']} | {r['description'][:80]}"
                for r in gh["repos"][:10]
            ])
            prompt = f"""You are an elite developer branding expert. Optimize this GitHub profile.

TARGET ROLES: {target or 'general tech roles'}

GITHUB: @{gh['username']}
Name: {gh['name']} | Bio: {gh['bio']} | Location: {gh['location']}
Repos: {gh['public_repos']} | Followers: {gh['followers']} | README: {gh['has_profile_readme']}
Languages: {', '.join(gh['top_languages'])}
Repos:\n{repos_summary}

Return ONLY valid JSON:
{{
  "bio": "max 160 chars",
  "repos_to_pin": ["6 repo names"],
  "repo_description_rewrites": [{{"name": "repo", "new_description": "improved"}}],
  "topics_to_add": {{"repo": ["tag1", "tag2"]}},
  "profile_readme": "COMPLETE README.md with emojis, badges, sections for intro/stack/projects/stats/contact",
  "action_steps": ["ordered steps"],
  "issues_found": ["problems found"],
  "estimated_impact": "1 sentence"
}}"""
            with st.spinner(f"🧠 {provider} optimizing GitHub..."):
                result = ai_call_with_json(provider, api_key, model, prompt)
            if result:
                st.session_state["gh_result"] = result

    if "gh_result" in st.session_state:
        r = st.session_state["gh_result"]
        gh = st.session_state["gh_data"]
        st.success("✅ GitHub optimized!")

        st.subheader("📛 New Bio")
        st.code(r.get("bio", ""), language=None)

        st.subheader("📌 Repos to Pin")
        for i, name in enumerate(r.get("repos_to_pin", []), 1):
            st.markdown(f"{i}. **{name}**")

        st.subheader("📝 Repo Description Rewrites")
        for rd in r.get("repo_description_rewrites", []):
            st.markdown(f"**{rd.get('name', '')}** → {rd.get('new_description', '')}")

        readme = r.get("profile_readme", "")
        if readme:
            st.subheader("📄 Profile README.md")
            with st.expander("Preview", expanded=True):
                st.markdown(readme)
            st.download_button("📥 Download README.md", data=readme, file_name="README.md",
                               mime="text/markdown", key="dl_readme")

        steps = r.get("action_steps", [])
        if steps:
            st.subheader("✅ Action Steps")
            for i, s in enumerate(steps, 1):
                st.markdown(f"{i}. {s}")


# ══════════════════════════════════════════════════
#  TAB 3: JD MATCHER
# ══════════════════════════════════════════════════

def tab_jd_matcher(provider, api_key, model):
    st.header("🎯 Job Description Matcher")
    st.markdown("Paste a job description → get match score, skill gaps, and tailored suggestions.")

    profile_text = get_profile_text_widget("jd")
    jd_text = st.text_area("📋 Paste Job Description", height=300, placeholder="Paste the full job description here...", key="jd_text")

    if profile_text and jd_text and st.button("🔍 Analyze Match", type="primary", key="btn_jd"):
        prompt = f"""You are an expert ATS analyst and career coach.

Compare this candidate's LinkedIn profile against the job description. Give an honest, detailed analysis.

CANDIDATE PROFILE:
{profile_text}

JOB DESCRIPTION:
{jd_text}

Return ONLY valid JSON:
{{
  "match_score": 75,
  "match_verdict": "Strong Match / Moderate Match / Weak Match",
  "matching_skills": ["skills the candidate HAS that match the JD"],
  "missing_skills": ["skills the JD requires but candidate LACKS"],
  "experience_match": "analysis of experience alignment",
  "education_match": "analysis of education alignment",
  "keyword_gaps": ["important JD keywords missing from profile"],
  "strengths": ["3-5 candidate strengths for this role"],
  "weaknesses": ["3-5 gaps or concerns"],
  "tailored_headline": "rewritten headline specifically for THIS job",
  "tailored_about_first_line": "new first line of About section targeting this JD",
  "resume_bullets_to_add": ["3-5 new bullets to add to resume for this specific role"],
  "action_plan": ["5 specific steps to improve chances for THIS job"],
  "should_apply": "Yes/No/Maybe with reasoning"
}}"""

        with st.spinner("🔍 Analyzing match..."):
            result = ai_call_with_json(provider, api_key, model, prompt)

        if result:
            st.session_state["jd_result"] = result

    if "jd_result" in st.session_state:
        r = st.session_state["jd_result"]

        # Score display
        score = r.get("match_score", 0)
        col1, col2, col3 = st.columns(3)
        col1.metric("Match Score", f"{score}%")
        col2.metric("Verdict", r.get("match_verdict", ""))
        col3.metric("Should Apply?", r.get("should_apply", "").split(" ")[0] if r.get("should_apply") else "")

        if score >= 70:
            st.success(f"🟢 {r.get('match_verdict', '')} — {r.get('should_apply', '')}")
        elif score >= 50:
            st.warning(f"🟡 {r.get('match_verdict', '')} — {r.get('should_apply', '')}")
        else:
            st.error(f"🔴 {r.get('match_verdict', '')} — {r.get('should_apply', '')}")

        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("✅ Matching Skills")
            for s in r.get("matching_skills", []):
                st.markdown(f"- ✅ {s}")
            st.subheader("💪 Strengths")
            for s in r.get("strengths", []):
                st.markdown(f"- 💪 {s}")

        with col_b:
            st.subheader("❌ Missing Skills")
            for s in r.get("missing_skills", []):
                st.markdown(f"- ❌ {s}")
            st.subheader("⚠️ Weaknesses")
            for s in r.get("weaknesses", []):
                st.markdown(f"- ⚠️ {s}")

        st.subheader("🔑 Keyword Gaps")
        st.markdown(" • ".join(r.get("keyword_gaps", [])))

        st.subheader("🏷️ Tailored Headline for This Job")
        st.code(r.get("tailored_headline", ""), language=None)

        st.subheader("📝 Resume Bullets to Add")
        for b in r.get("resume_bullets_to_add", []):
            st.markdown(f"- {b}")

        st.subheader("📋 Action Plan")
        for i, step in enumerate(r.get("action_plan", []), 1):
            st.markdown(f"{i}. {step}")


# ══════════════════════════════════════════════════
#  TAB 4: ATS RESUME GENERATOR
# ══════════════════════════════════════════════════

def tab_resume(provider, api_key, model):
    st.header("📄 ATS Resume Generator")
    st.markdown("Upload LinkedIn PDF → get a clean, ATS-optimized resume in Markdown format.")

    profile_text = get_profile_text_widget("resume")
    target = st.text_input("Target Role (optional)", placeholder="e.g., Senior Backend Engineer", key="resume_target")

    if profile_text and st.button("📄 Generate ATS Resume", type="primary", key="btn_resume"):
        prompt = f"""You are a professional resume writer who specializes in ATS-optimized resumes.

Create a clean, professional, ATS-friendly resume from this LinkedIn profile data. The resume should pass automated screening systems.

PROFILE DATA:
{profile_text}

TARGET ROLE: {target or 'general tech roles'}

RULES:
1. Clean, structured format — no fancy formatting, no tables, no columns (ATS can't parse them)
2. Contact info at top
3. Professional Summary: 3-4 lines, keyword-rich
4. Experience: reverse chronological, STAR bullets with metrics
5. Skills: grouped by category (Languages, Frameworks, Tools, etc.)
6. Education: degree, university, dates
7. Certifications: relevant ones only
8. NO photos, NO graphics, NO icons — pure text for ATS
9. Use strong action verbs: Built, Developed, Implemented, Optimized, Led, Delivered
10. Include relevant keywords naturally throughout

Return the resume as clean Markdown text. Do NOT wrap in JSON. Just return the resume content directly."""

        with st.spinner("📄 Generating ATS resume..."):
            result = ai_call_with_text(provider, api_key, model, prompt)

        if result:
            st.session_state["resume_result"] = result

    if "resume_result" in st.session_state:
        r = st.session_state["resume_result"]
        st.success("✅ Resume generated!")

        st.markdown("---")
        st.markdown(r)

        st.download_button("📥 Download Resume (Markdown)", data=r,
                           file_name=f"resume_{datetime.now().strftime('%Y%m%d')}.md", mime="text/markdown")


# ══════════════════════════════════════════════════
#  TAB 5: PROJECT SUGGESTIONS
# ══════════════════════════════════════════════════

def tab_projects(provider, api_key, model):
    st.header("🛠️ Project Suggestions")
    st.markdown("Based on your profile and target role → get project ideas that fill skill gaps and impress recruiters.")

    profile_text = get_profile_text_widget("proj")
    target = st.text_input("Target Role", placeholder="e.g., AI Engineer at startups", key="proj_target")

    if profile_text and st.button("💡 Suggest Projects", type="primary", key="btn_proj"):
        prompt = f"""You are a senior engineering mentor and hiring manager.

Analyze this candidate's profile and suggest 7 portfolio projects that would SIGNIFICANTLY boost their chances of landing their target role. Projects should fill skill gaps visible in their profile.

PROFILE:
{profile_text}

TARGET ROLE: {target or 'general tech roles'}

Return ONLY valid JSON:
{{
  "skill_gaps_identified": ["gaps between current profile and target role"],
  "projects": [
    {{
      "name": "Project Name",
      "tagline": "1-line description",
      "why_it_helps": "how this project fills a specific gap",
      "tech_stack": ["tech1", "tech2", "tech3"],
      "difficulty": "Beginner / Intermediate / Advanced",
      "time_estimate": "2 weeks",
      "key_features": ["feature 1", "feature 2", "feature 3"],
      "github_description": "1-liner for GitHub repo description",
      "recruiter_appeal": "why a recruiter would be impressed by this"
    }}
  ],
  "project_priority_order": "which to build first and why",
  "bonus_tip": "1 extra tip for making projects stand out"
}}"""

        with st.spinner("💡 Generating project ideas..."):
            result = ai_call_with_json(provider, api_key, model, prompt)

        if result:
            st.session_state["proj_result"] = result

    if "proj_result" in st.session_state:
        r = st.session_state["proj_result"]
        st.success("✅ Projects suggested!")

        st.subheader("🔍 Skill Gaps Identified")
        for g in r.get("skill_gaps_identified", []):
            st.markdown(f"- 🔍 {g}")

        st.subheader("📋 Priority Order")
        st.info(r.get("project_priority_order", ""))

        st.subheader("🛠️ Suggested Projects")
        for i, p in enumerate(r.get("projects", []), 1):
            with st.expander(f"Project {i}: {p.get('name', '')} — {p.get('difficulty', '')}", expanded=i <= 3):
                st.markdown(f"**{p.get('tagline', '')}**")
                st.markdown(f"**Why it helps:** {p.get('why_it_helps', '')}")
                st.markdown(f"**Tech Stack:** {', '.join(p.get('tech_stack', []))}")
                st.markdown(f"**Time:** {p.get('time_estimate', '')} | **Difficulty:** {p.get('difficulty', '')}")
                st.markdown("**Key Features:**")
                for f in p.get("key_features", []):
                    st.markdown(f"  - {f}")
                st.markdown(f"**GitHub Description:** `{p.get('github_description', '')}`")
                st.markdown(f"**Recruiter Appeal:** {p.get('recruiter_appeal', '')}")

        tip = r.get("bonus_tip", "")
        if tip:
            st.info(f"💡 **Bonus Tip:** {tip}")


# ══════════════════════════════════════════════════
#  TAB 6: INTERVIEW PREP
# ══════════════════════════════════════════════════

def tab_interview(provider, api_key, model):
    st.header("🎤 Interview Prep")
    st.markdown("Get role-specific interview questions with sample answers based on YOUR experience.")

    profile_text = get_profile_text_widget("intv")
    col1, col2 = st.columns(2)
    with col1:
        target = st.text_input("Target Role", placeholder="e.g., AI Engineer", key="intv_target")
    with col2:
        company = st.text_input("Company (optional)", placeholder="e.g., Google, Zomato", key="intv_company")

    interview_type = st.selectbox("Interview Type", [
        "Technical + Behavioral (Mixed)",
        "Technical Deep Dive",
        "Behavioral / Culture Fit",
        "System Design",
        "HR / Screening Round",
    ], key="intv_type")

    if profile_text and st.button("🎤 Generate Interview Prep", type="primary", key="btn_intv"):
        prompt = f"""You are a senior technical interviewer and career coach.

Generate interview preparation material for this candidate based on their profile, target role, and interview type.

CANDIDATE PROFILE:
{profile_text}

TARGET ROLE: {target or 'general tech role'}
COMPANY: {company or 'not specified'}
INTERVIEW TYPE: {interview_type}

Return ONLY valid JSON:
{{
  "questions": [
    {{
      "question": "the interview question",
      "type": "Technical / Behavioral / System Design / HR",
      "difficulty": "Easy / Medium / Hard",
      "why_asked": "why interviewers ask this for this role",
      "sample_answer": "sample answer using the CANDIDATE'S actual experience from their profile — personalized, specific, with STAR format for behavioral",
      "tips": "what to emphasize, what to avoid"
    }}
  ],
  "opening_pitch": "How to answer 'Tell me about yourself' — personalized to this candidate and role, 30 seconds",
  "questions_to_ask_interviewer": ["5 smart questions to ask the interviewer"],
  "red_flags_to_avoid": ["5 things NOT to say in this interview"],
  "confidence_boosters": ["3 specific strengths this candidate should highlight"],
  "salary_range_suggestion": "suggested salary range for this role + location based on profile experience"
}}"""

        with st.spinner("🎤 Preparing interview..."):
            result = ai_call_with_json(provider, api_key, model, prompt)

        if result:
            st.session_state["intv_result"] = result

    if "intv_result" in st.session_state:
        r = st.session_state["intv_result"]
        st.success("✅ Interview prep ready!")

        st.subheader("🗣️ Opening Pitch — 'Tell me about yourself'")
        st.info(r.get("opening_pitch", ""))

        st.subheader("💪 Your Key Strengths to Highlight")
        for s in r.get("confidence_boosters", []):
            st.markdown(f"- 💪 {s}")

        st.subheader("❓ Interview Questions & Answers")
        for i, q in enumerate(r.get("questions", []), 1):
            with st.expander(f"Q{i}: {q.get('question', '')} [{q.get('type', '')} — {q.get('difficulty', '')}]"):
                st.markdown(f"**Why they ask this:** {q.get('why_asked', '')}")
                st.markdown(f"**Sample Answer:**\n\n{q.get('sample_answer', '')}")
                st.markdown(f"**Tips:** {q.get('tips', '')}")

        st.subheader("🙋 Questions to Ask the Interviewer")
        for q in r.get("questions_to_ask_interviewer", []):
            st.markdown(f"- 🙋 {q}")

        st.subheader("🚫 Red Flags to Avoid")
        for f in r.get("red_flags_to_avoid", []):
            st.markdown(f"- 🚫 {f}")

        salary = r.get("salary_range_suggestion", "")
        if salary:
            st.subheader("💰 Salary Range Suggestion")
            st.info(salary)


# ══════════════════════════════════════════════════
#  TAB 7: COLD OUTREACH
# ══════════════════════════════════════════════════

def tab_outreach(provider, api_key, model):
    st.header("📧 Cold Outreach Templates")
    st.markdown("Get personalized LinkedIn messages, emails, and referral requests.")

    profile_text = get_profile_text_widget("outreach")
    col1, col2 = st.columns(2)
    with col1:
        target_role = st.text_input("Target Role", placeholder="e.g., AI Engineer", key="out_role")
    with col2:
        target_company = st.text_input("Target Company (optional)", placeholder="e.g., Flipkart", key="out_company")

    outreach_type = st.selectbox("Who are you reaching out to?", [
        "Recruiter / HR",
        "Hiring Manager / Engineering Lead",
        "Employee for Referral",
        "Founder / CTO (Startup)",
        "All of the above",
    ], key="out_type")

    if profile_text and st.button("📧 Generate Templates", type="primary", key="btn_out"):
        prompt = f"""You are a career networking expert who helps engineers land jobs through strategic outreach.

Create personalized outreach templates for this candidate. Messages should be professional yet human — not robotic or generic.

CANDIDATE PROFILE:
{profile_text}

TARGET ROLE: {target_role or 'tech role'}
TARGET COMPANY: {target_company or 'not specified'}
OUTREACH TO: {outreach_type}

Return ONLY valid JSON:
{{
  "linkedin_connection_note": "Short LinkedIn connection request (under 300 chars)",
  "linkedin_dm_recruiter": "LinkedIn DM to a recruiter — personalized, specific about your skills, shows you researched the company. 4-5 sentences.",
  "linkedin_dm_hiring_manager": "LinkedIn DM to a hiring manager — shows technical depth, references specific projects. 4-5 sentences.",
  "linkedin_dm_referral": "LinkedIn DM asking an employee for a referral — warm, non-pushy, gives them reason to help. 4-5 sentences.",
  "linkedin_dm_founder": "LinkedIn DM to a startup founder/CTO — shows passion, references their product. 4-5 sentences.",
  "cold_email_template": "Professional cold email for job inquiry — subject line + body. 6-8 sentences.",
  "follow_up_message": "Follow-up message after no response (1 week later). 3-4 sentences.",
  "referral_request_to_friend": "Message to a friend/connection asking for internal referral. Casual but clear.",
  "thank_you_after_interview": "Thank you message after an interview. Professional, references specific conversation points.",
  "tips": ["5 networking tips specific to this candidate's situation"]
}}"""

        with st.spinner("📧 Generating templates..."):
            result = ai_call_with_json(provider, api_key, model, prompt)

        if result:
            st.session_state["out_result"] = result

    if "out_result" in st.session_state:
        r = st.session_state["out_result"]
        st.success("✅ Templates ready!")

        templates = [
            ("🔗 LinkedIn Connection Note", "linkedin_connection_note"),
            ("💬 DM to Recruiter", "linkedin_dm_recruiter"),
            ("💬 DM to Hiring Manager", "linkedin_dm_hiring_manager"),
            ("🤝 DM for Referral", "linkedin_dm_referral"),
            ("🚀 DM to Founder/CTO", "linkedin_dm_founder"),
            ("📧 Cold Email", "cold_email_template"),
            ("🔄 Follow-up Message", "follow_up_message"),
            ("👥 Referral Request to Friend", "referral_request_to_friend"),
            ("🙏 Thank You After Interview", "thank_you_after_interview"),
        ]

        for title, key in templates:
            with st.expander(title):
                text = r.get(key, "")
                st.text_area(title, text, height=150, key=f"ta_{key}")
                st.button(f"📋 Copy", key=f"cp_{key}", help="Select all text above and copy")

        tips = r.get("tips", [])
        if tips:
            st.subheader("💡 Networking Tips")
            for t in tips:
                st.markdown(f"- 💡 {t}")


# ══════════════════════════════════════════════════
#  TAB 8: SKILLS GAP ANALYSIS
# ══════════════════════════════════════════════════

def tab_skills_gap(provider, api_key, model):
    st.header("📊 Skills Gap Analysis")
    st.markdown("Compare your current skills vs market demand for your target role.")

    profile_text = get_profile_text_widget("skills")
    target = st.text_input("Target Role", placeholder="e.g., Senior AI Engineer at MNC", key="skills_target")

    if profile_text and st.button("📊 Analyze Skills Gap", type="primary", key="btn_skills"):
        prompt = f"""You are a tech career strategist with deep knowledge of current job market demands.

Analyze the gap between this candidate's current skills and what the market demands for their target role. Be specific and actionable.

CANDIDATE PROFILE:
{profile_text}

TARGET ROLE: {target or 'general tech roles'}

Return ONLY valid JSON:
{{
  "current_skills": ["skills detected from profile"],
  "required_skills": ["skills the market demands for target role, grouped"],
  "skill_gaps": [
    {{
      "skill": "missing skill name",
      "importance": "Critical / Important / Nice-to-have",
      "current_level": "None / Beginner / Intermediate",
      "required_level": "Intermediate / Advanced / Expert",
      "how_to_learn": "specific resource or approach to learn this",
      "time_to_learn": "estimated time to reach required level"
    }}
  ],
  "strongest_skills": ["candidate's strongest marketable skills"],
  "underrated_skills": ["skills candidate has but isn't highlighting enough"],
  "skills_to_remove_from_profile": ["outdated or irrelevant skills to remove"],
  "learning_roadmap": [
    {{
      "month": "Month 1",
      "focus": "what to learn",
      "resources": ["specific courses, tutorials, projects"],
      "milestone": "what you should be able to do by end of month"
    }}
  ],
  "certifications_to_get": [
    {{"name": "cert name", "provider": "platform", "why": "how it helps", "cost": "free/paid", "time": "duration"}}
  ],
  "market_readiness_score": 65,
  "time_to_market_ready": "estimated time to be fully competitive"
}}"""

        with st.spinner("📊 Analyzing skills gap..."):
            result = ai_call_with_json(provider, api_key, model, prompt)

        if result:
            st.session_state["skills_result"] = result

    if "skills_result" in st.session_state:
        r = st.session_state["skills_result"]
        st.success("✅ Analysis complete!")

        score = r.get("market_readiness_score", 0)
        col1, col2 = st.columns(2)
        col1.metric("Market Readiness", f"{score}%")
        col2.metric("Time to Market Ready", r.get("time_to_market_ready", ""))

        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("💪 Strongest Skills")
            for s in r.get("strongest_skills", []):
                st.markdown(f"- 💪 {s}")
            st.subheader("🔍 Underrated Skills (highlight more!)")
            for s in r.get("underrated_skills", []):
                st.markdown(f"- 🔍 {s}")
        with col_b:
            st.subheader("🗑️ Remove from Profile")
            for s in r.get("skills_to_remove_from_profile", []):
                st.markdown(f"- 🗑️ {s}")

        st.subheader("⚠️ Skill Gaps")
        for gap in r.get("skill_gaps", []):
            imp = gap.get("importance", "")
            icon = "🔴" if imp == "Critical" else "🟡" if imp == "Important" else "🟢"
            with st.expander(f"{icon} {gap.get('skill', '')} — {imp}"):
                st.markdown(f"**Current Level:** {gap.get('current_level', '')} → **Required:** {gap.get('required_level', '')}")
                st.markdown(f"**How to learn:** {gap.get('how_to_learn', '')}")
                st.markdown(f"**Time:** {gap.get('time_to_learn', '')}")

        st.subheader("🗓️ Learning Roadmap")
        for m in r.get("learning_roadmap", []):
            with st.expander(f"📅 {m.get('month', '')} — {m.get('focus', '')}"):
                st.markdown("**Resources:**")
                for res in m.get("resources", []):
                    st.markdown(f"  - {res}")
                st.markdown(f"**Milestone:** {m.get('milestone', '')}")

        certs = r.get("certifications_to_get", [])
        if certs:
            st.subheader("🎓 Certifications to Get")
            for c in certs:
                st.markdown(f"- **{c.get('name', '')}** ({c.get('provider', '')}) — {c.get('why', '')} | {c.get('cost', '')} | {c.get('time', '')}")


# ══════════════════════════════════════════════════
#  TAB 9: JOB KEYWORDS
# ══════════════════════════════════════════════════

def tab_keywords(provider, api_key, model):
    st.header("🔍 Job Search Keywords")
    st.markdown("Get optimized search keywords for LinkedIn, Naukri, Indeed, and Google to find the best jobs.")

    profile_text = get_profile_text_widget("kw")
    col1, col2 = st.columns(2)
    with col1:
        target = st.text_input("Target Role", placeholder="e.g., AI Engineer", key="kw_target")
    with col2:
        location = st.text_input("Preferred Location", placeholder="e.g., Bangalore, Remote", key="kw_location")

    if profile_text and st.button("🔍 Generate Keywords", type="primary", key="btn_kw"):
        prompt = f"""You are a job search strategist who helps engineers find hidden job opportunities.

Based on this candidate's profile, generate optimized search keywords and strategies for different job platforms.

PROFILE:
{profile_text}

TARGET: {target or 'tech roles'}
LOCATION: {location or 'India / Remote'}

Return ONLY valid JSON:
{{
  "linkedin_search_queries": ["10 exact search strings to use on LinkedIn Jobs"],
  "naukri_keywords": ["10 keyword combinations for Naukri.com"],
  "indeed_queries": ["10 search queries for Indeed"],
  "google_job_search": ["5 Google search strings like: site:lever.co 'AI Engineer' 'India'"],
  "job_titles_to_search": ["15 job title variations to search — many companies use different titles for the same role"],
  "companies_to_target": ["20 companies hiring for this role in the specified location"],
  "niche_job_boards": ["5 specialized job boards for this field"],
  "boolean_search_string": "advanced LinkedIn boolean search string",
  "hashtags_to_follow": ["10 LinkedIn/Twitter hashtags for job openings"],
  "google_alerts_to_set": ["3 Google Alert queries to get notified of new openings"],
  "hidden_job_market_tips": ["5 tips to find unadvertised jobs"],
  "search_schedule": "recommended daily/weekly job search routine"
}}"""

        with st.spinner("🔍 Generating keywords..."):
            result = ai_call_with_json(provider, api_key, model, prompt)

        if result:
            st.session_state["kw_result"] = result

    if "kw_result" in st.session_state:
        r = st.session_state["kw_result"]
        st.success("✅ Keywords generated!")

        st.subheader("🔎 LinkedIn Job Search Queries")
        for q in r.get("linkedin_search_queries", []):
            st.code(q, language=None)

        st.subheader("📋 Naukri Keywords")
        for q in r.get("naukri_keywords", []):
            st.code(q, language=None)

        st.subheader("🌐 Indeed Queries")
        for q in r.get("indeed_queries", []):
            st.code(q, language=None)

        st.subheader("🔍 Google Job Search Strings")
        for q in r.get("google_job_search", []):
            st.code(q, language=None)

        st.subheader("💼 Job Titles to Search")
        st.markdown(" • ".join(r.get("job_titles_to_search", [])))

        st.subheader("🏢 Companies to Target")
        companies = r.get("companies_to_target", [])
        cols = st.columns(4)
        for i, c in enumerate(companies):
            cols[i % 4].markdown(f"- {c}")

        st.subheader("🔗 Boolean Search String")
        st.code(r.get("boolean_search_string", ""), language=None)

        niche = r.get("niche_job_boards", [])
        if niche:
            st.subheader("🎯 Niche Job Boards")
            for n in niche:
                st.markdown(f"- {n}")

        st.subheader("#️⃣ Hashtags to Follow")
        st.markdown(" ".join(r.get("hashtags_to_follow", [])))

        st.subheader("🔔 Google Alerts to Set")
        for a in r.get("google_alerts_to_set", []):
            st.code(a, language=None)

        tips = r.get("hidden_job_market_tips", [])
        if tips:
            st.subheader("🕵️ Hidden Job Market Tips")
            for t in tips:
                st.markdown(f"- 🕵️ {t}")

        schedule = r.get("search_schedule", "")
        if schedule:
            st.subheader("📅 Search Schedule")
            st.info(schedule)


# ══════════════════════════════════════════════════
#  TAB 10: COVER LETTER GENERATOR
# ══════════════════════════════════════════════════

def tab_cover_letter(provider, api_key, model):
    st.header("✉️ Cover Letter Generator")
    st.markdown("Paste a job description → get a tailored cover letter based on your profile.")

    profile_text = get_profile_text_widget("cl")
    jd_text = st.text_area("📋 Paste Job Description", height=250, placeholder="Paste the job description here...", key="cl_jd")

    col1, col2 = st.columns(2)
    with col1:
        company = st.text_input("Company Name", placeholder="e.g., Razorpay", key="cl_company")
    with col2:
        hiring_manager = st.text_input("Hiring Manager (optional)", placeholder="e.g., Priya Sharma", key="cl_hm")

    tone = st.selectbox("Tone", ["Professional & Confident", "Friendly & Enthusiastic", "Formal & Corporate"], key="cl_tone")

    if profile_text and jd_text and st.button("✉️ Generate Cover Letter", type="primary", key="btn_cl"):
        prompt = f"""You are a professional cover letter writer.

Write a compelling, personalized cover letter for this candidate applying to a specific job.

CANDIDATE PROFILE:
{profile_text}

JOB DESCRIPTION:
{jd_text}

COMPANY: {company or 'the company'}
HIRING MANAGER: {hiring_manager or 'Hiring Manager'}
TONE: {tone}

RULES:
1. Open with a strong hook — NOT "I am writing to apply for..."
2. Connect candidate's SPECIFIC experience to job requirements
3. Show knowledge of the company
4. Include 2-3 concrete achievements with numbers
5. End with a confident call to action
6. Keep it under 400 words
7. Make it sound human, not AI-generated

Return the cover letter as plain text. No JSON. No markdown fences. Just the letter."""

        with st.spinner("✉️ Writing cover letter..."):
            result = ai_call_with_text(provider, api_key, model, prompt)

        if result:
            st.session_state["cl_result"] = result

    if "cl_result" in st.session_state:
        r = st.session_state["cl_result"]
        st.success("✅ Cover letter ready!")

        st.markdown("---")
        st.markdown(r)

        st.download_button("📥 Download Cover Letter", data=r,
                           file_name=f"cover_letter_{datetime.now().strftime('%Y%m%d')}.txt", mime="text/plain")


# ══════════════════════════════════════════════════
#  CUSTOM CSS — animations, gradients, cards
# ══════════════════════════════════════════════════

CUSTOM_CSS = """
<style>
/* ── Animations ─────────────────────────────── */
@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes slideInLeft {
    from { opacity: 0; transform: translateX(-30px); }
    to { opacity: 1; transform: translateX(0); }
}

@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.02); }
}

@keyframes shimmer {
    0% { background-position: -200% center; }
    100% { background-position: 200% center; }
}

@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-6px); }
}

/* ── Global ─────────────────────────────────── */
.stApp {
    background: linear-gradient(135deg, #0f0c29 0%, #1a1a2e 40%, #16213e 100%);
}

/* ── Force all text visible on dark bg ──────── */
.stApp, .stApp p, .stApp li, .stApp span, .stApp label,
.stApp .stMarkdown, .stApp .stMarkdown p,
.stApp .stMarkdown li, .stApp .stMarkdown span,
.stApp .stText, .stApp div {
    color: #e0e0ff !important;
}

.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 {
    color: #ffffff !important;
}

.stApp .stCaption, .stApp small, .stApp figcaption {
    color: rgba(224, 224, 255, 0.6) !important;
}

/* Keep colored alerts readable */
div[data-testid="stAlert"] p,
div[data-testid="stAlert"] span {
    color: inherit !important;
}

/* Labels above inputs */
.stSelectbox label, .stTextInput label, .stTextArea label,
.stFileUploader label, .stMultiSelect label, .stCheckbox label {
    color: #c0c0e0 !important;
    font-weight: 500 !important;
}

/* Help text / placeholder */
.stTextInput input::placeholder, .stTextArea textarea::placeholder {
    color: #8888bb !important;
    opacity: 1 !important;
    -webkit-text-fill-color: #8888bb !important;
}

/* ── Force dark bg on ALL input-like elements ── */
[data-baseweb="input"] {
    background-color: #1e1e3a !important;
}

[data-baseweb="textarea"] {
    background-color: #1e1e3a !important;
}

[data-baseweb="select"] > div {
    background-color: #1e1e3a !important;
    border-color: rgba(102, 126, 234, 0.3) !important;
}

[data-baseweb="popover"],
[data-baseweb="popover"] ul,
[data-baseweb="menu"],
[data-baseweb="menu"] ul,
[role="listbox"],
[role="listbox"] ul {
    background: #1a1a3e !important;
    background-color: #1a1a3e !important;
}

[data-baseweb="menu"] li,
[role="option"],
[role="listbox"] li {
    color: #d0d0f0 !important;
    -webkit-text-fill-color: #d0d0f0 !important;
    background: transparent !important;
}

[data-baseweb="menu"] li:hover,
[role="option"]:hover,
[role="listbox"] li:hover {
    background: #2a2a5a !important;
    background-color: #2a2a5a !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

/* Selected item in dropdown */
[aria-selected="true"],
[data-baseweb="menu"] li[aria-selected="true"] {
    background: rgba(102, 126, 234, 0.25) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

/* Bold text */
strong, b {
    color: #ffffff !important;
}

/* Links */
a {
    color: #8b9cf7 !important;
}

a:hover {
    color: #a5b4fc !important;
}

/* Expander header text */
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary span,
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary div,
[data-testid="stExpanderToggleDetails"] span,
[data-testid="stExpanderToggleDetails"] p {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-weight: 600 !important;
}

/* Expander arrow icon */
[data-testid="stExpander"] summary svg {
    fill: #667eea !important;
    color: #667eea !important;
}

/* Tab content area text */
.stTabs [data-testid="stTabContent"] {
    color: #e0e0ff !important;
}

/* Metric labels */
[data-testid="stMetricLabel"] {
    color: rgba(224, 224, 255, 0.7) !important;
}

[data-testid="stMetricValue"] {
    color: #667eea !important;
    font-weight: 700 !important;
}

/* Markdown inside expanders */
[data-testid="stExpander"] .stMarkdown p,
[data-testid="stExpander"] .stMarkdown li,
[data-testid="stExpander"] .stMarkdown span {
    color: #d0d0f0 !important;
}

/* ── Hero Header ────────────────────────────── */
.hero-container {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 30%, #f093fb 60%, #667eea 100%);
    background-size: 300% 300%;
    animation: gradientShift 8s ease infinite;
    border-radius: 20px;
    padding: 2.5rem 2rem;
    margin-bottom: 2rem;
    text-align: center;
    box-shadow: 0 20px 60px rgba(102, 126, 234, 0.3);
    position: relative;
    overflow: hidden;
}

.hero-container::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 60%);
    animation: float 6s ease-in-out infinite;
}

.hero-title {
    font-size: 2.8rem;
    font-weight: 800;
    color: white;
    margin: 0;
    text-shadow: 0 2px 20px rgba(0,0,0,0.3);
    letter-spacing: -0.5px;
    position: relative;
}

.hero-subtitle {
    font-size: 1.15rem;
    color: rgba(255,255,255,0.9);
    margin-top: 0.5rem;
    font-weight: 400;
    position: relative;
}

.hero-badge {
    display: inline-block;
    background: rgba(255,255,255,0.2);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 50px;
    padding: 0.4rem 1.2rem;
    margin-top: 1rem;
    color: white;
    font-size: 0.85rem;
    font-weight: 500;
    position: relative;
}

/* ── Sidebar ────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%) !important;
    border-right: 1px solid rgba(102, 126, 234, 0.2);
}

section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stTextInput label,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #e0e0ff !important;
}

/* ── Tab Styling ────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.03);
    border-radius: 16px;
    padding: 6px;
    gap: 4px;
    border: 1px solid rgba(102, 126, 234, 0.15);
    backdrop-filter: blur(10px);
    overflow-x: auto;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 12px;
    padding: 10px 18px;
    font-weight: 600;
    font-size: 0.85rem;
    color: rgba(255,255,255,0.7);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    white-space: nowrap;
}

.stTabs [data-baseweb="tab"]:hover {
    background: rgba(102, 126, 234, 0.15);
    color: white;
    transform: translateY(-1px);
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.stTabs [data-baseweb="tab-highlight"] {
    display: none;
}

.stTabs [data-baseweb="tab-border"] {
    display: none;
}

/* ── Cards / Containers ─────────────────────── */
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(102, 126, 234, 0.15) !important;
    border-radius: 14px !important;
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
    animation: fadeInUp 0.5s ease-out;
}

[data-testid="stExpander"]:hover {
    border-color: rgba(102, 126, 234, 0.4) !important;
    box-shadow: 0 8px 30px rgba(102, 126, 234, 0.15);
    transform: translateY(-2px);
}

/* ── Metrics ────────────────────────────────── */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
    border: 1px solid rgba(102, 126, 234, 0.2);
    border-radius: 14px;
    padding: 1.2rem !important;
    animation: fadeInUp 0.6s ease-out;
    transition: all 0.3s ease;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.2);
    border-color: rgba(102, 126, 234, 0.4);
}

[data-testid="stMetricValue"] {
    color: #667eea !important;
    font-weight: 700;
}

/* ── Buttons ────────────────────────────────── */
.stButton > button[kind="primary"],
.stButton > button[data-testid*="primary"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.7rem 2rem !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid*="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5) !important;
}

.stButton > button[kind="primary"]:active {
    transform: translateY(0px) !important;
}

.stButton > button[kind="secondary"] {
    border: 1px solid rgba(102, 126, 234, 0.3) !important;
    border-radius: 12px !important;
    color: #667eea !important;
    background: rgba(102, 126, 234, 0.05) !important;
    transition: all 0.3s ease !important;
}

.stButton > button[kind="secondary"]:hover {
    background: rgba(102, 126, 234, 0.15) !important;
    border-color: #667eea !important;
}

/* ── Download button ────────────────────────── */
.stDownloadButton > button {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%) !important;
    border: none !important;
    border-radius: 12px !important;
    color: white !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 15px rgba(17, 153, 142, 0.3);
    transition: all 0.3s ease !important;
}

.stDownloadButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(17, 153, 142, 0.4) !important;
}

/* ── Text areas & inputs ────────────────────── */
.stTextArea textarea, .stTextInput input {
    background: #1e1e3a !important;
    border: 1px solid rgba(102, 126, 234, 0.3) !important;
    border-radius: 12px !important;
    color: #e0e0ff !important;
    -webkit-text-fill-color: #e0e0ff !important;
    transition: all 0.3s ease !important;
}

.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #667eea !important;
    box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2) !important;
    background: #242450 !important;
}

/* ── File uploader ──────────────────────────── */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.03);
    border: 2px dashed rgba(102, 126, 234, 0.3);
    border-radius: 16px;
    padding: 1rem;
    transition: all 0.3s ease;
}

[data-testid="stFileUploader"]:hover {
    border-color: #667eea;
    background: rgba(102, 126, 234, 0.05);
}

/* File uploader dropzone — dark bg */
[data-testid="stFileUploaderDropzone"],
[data-testid="stFileUploaderDropzone"] > div {
    background: #1e1e3a !important;
    border-color: rgba(102, 126, 234, 0.3) !important;
}

/* File uploader inner text */
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] p,
[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploaderDropzone"] small {
    color: #8888bb !important;
    -webkit-text-fill-color: #8888bb !important;
}

/* Cloud icon */
[data-testid="stFileUploaderDropzone"] svg {
    color: #667eea !important;
    fill: #667eea !important;
}

/* Browse files button */
[data-testid="stFileUploaderDropzone"] button,
[data-testid="stFileUploader"] button {
    color: #667eea !important;
    border-color: rgba(102, 126, 234, 0.4) !important;
    background: rgba(102, 126, 234, 0.15) !important;
}

/* Selectbox text inside dropdown */
[data-baseweb="select"] span,
[data-baseweb="select"] div {
    color: #c0c0e0 !important;
    -webkit-text-fill-color: #c0c0e0 !important;
}

/* Selectbox selected value */
[data-baseweb="select"] [data-baseweb="tag"] span {
    color: #e0e0ff !important;
    -webkit-text-fill-color: #e0e0ff !important;
}

/* Selectbox arrow icon */
[data-baseweb="select"] svg {
    fill: #8888bb !important;
}

/* ── Success/Error/Warning/Info ──────────────── */
.stSuccess, .stAlert[data-baseweb*="success"] {
    border-radius: 12px !important;
    animation: fadeInUp 0.4s ease-out;
}

.stWarning {
    border-radius: 12px !important;
}

.stError {
    border-radius: 12px !important;
}

div[data-testid="stAlert"] {
    border-radius: 12px !important;
    animation: fadeInUp 0.4s ease-out;
}

/* ── Code blocks — nuclear override ─────────── */
.stCode, .stCodeBlock,
.stCode > div, .stCodeBlock > div,
.stCode pre, .stCodeBlock pre,
.stCode code, .stCodeBlock code,
[data-testid="stCode"],
[data-testid="stCode"] > div,
[data-testid="stCode"] pre,
[data-testid="stCode"] code,
[data-testid="stCodeBlock"],
[data-testid="stCodeBlock"] > div,
[data-testid="stCodeBlock"] pre,
[data-testid="stCodeBlock"] code,
.element-container pre,
.element-container code,
pre, code {
    background: #1e1e3a !important;
    background-color: #1e1e3a !important;
    color: #e0e0ff !important;
    -webkit-text-fill-color: #e0e0ff !important;
    border-radius: 12px !important;
    border-color: rgba(102, 126, 234, 0.25) !important;
}

/* Inline code in markdown */
.stMarkdown code {
    background: #1e1e3a !important;
    background-color: #1e1e3a !important;
    color: #c0c0f0 !important;
    -webkit-text-fill-color: #c0c0f0 !important;
    padding: 2px 6px;
    border-radius: 4px;
}

/* ── Divider ────────────────────────────────── */
hr {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.3), transparent);
    margin: 1.5rem 0;
}

/* ── Headers inside tabs ────────────────────── */
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    animation: slideInLeft 0.5s ease-out;
}

/* ── Selectbox ──────────────────────────────── */
[data-baseweb="select"] {
    border-radius: 12px !important;
}

/* Input instruction text (Press Enter to apply) */
.stTextInput div[data-testid="InputInstructions"],
.stTextInput div[data-testid="InputInstructions"] span {
    color: #8888bb !important;
    -webkit-text-fill-color: #8888bb !important;
}

/* ── Spinner ────────────────────────────────── */
.stSpinner > div {
    border-radius: 12px;
    animation: pulse 2s ease-in-out infinite;
}

/* ── Welcome cards (landing page) ───────────── */
.welcome-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(102, 126, 234, 0.15);
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    animation: fadeInUp 0.6s ease-out;
    backdrop-filter: blur(10px);
}

.welcome-card:hover {
    transform: translateY(-5px);
    border-color: rgba(102, 126, 234, 0.4);
    box-shadow: 0 15px 40px rgba(102, 126, 234, 0.15);
}

.welcome-card-icon {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
    animation: float 3s ease-in-out infinite;
}

.welcome-card-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #e0e0ff;
    margin: 0.5rem 0 0.3rem 0;
}

.welcome-card-desc {
    font-size: 0.85rem;
    color: rgba(255,255,255,0.6);
    line-height: 1.4;
}

/* ── Scrollbar ──────────────────────────────── */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(0,0,0,0.1);
}

::-webkit-scrollbar-thumb {
    background: rgba(102, 126, 234, 0.3);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(102, 126, 234, 0.5);
}

/* ── Footer ─────────────────────────────────── */
.footer {
    text-align: center;
    padding: 2rem 0 1rem 0;
    color: rgba(255,255,255,0.3);
    font-size: 0.8rem;
    border-top: 1px solid rgba(102, 126, 234, 0.1);
    margin-top: 3rem;
}
</style>
"""


# ══════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════

def main():
    st.set_page_config(
        page_title="Profile Optimizer — Career Toolkit",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Inject custom CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # ── Animated Hero Header ────────────────────
    st.markdown("""
    <div class="hero-container">
        <p class="hero-title">🚀 Profile Optimizer</p>
        <p class="hero-subtitle">AI-Powered Career Toolkit — LinkedIn, GitHub, Resume, Interview & More</p>
        <span class="hero-badge">✨ 10 Tools • 5 AI Providers • 100% Local & Private</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Sidebar ─────────────────────────────────
    with st.sidebar:
        st.markdown("### 🤖 AI Provider")
        config = load_config()

        provider = st.selectbox(
            "Provider",
            list(PROVIDERS.keys()),
            index=list(PROVIDERS.keys()).index(config.get("last_provider", "Claude (Anthropic)")),
        )
        provider_info = PROVIDERS[provider]

        if config.get("last_provider") != provider:
            config["last_provider"] = provider
            save_config(config)

        # Model
        if provider == "Ollama (Local — Free)":
            ollama_models = get_ollama_models()
            if not ollama_models:
                st.warning("⚠️ Ollama not running.\n```\nollama serve\nollama pull llama3.1\n```")
                model = st.text_input("Model name", value="llama3.1")
            else:
                model = st.selectbox("Model", ollama_models)
        else:
            model = st.selectbox("Model", provider_info["models"])

        st.divider()

        # API key
        api_key = ""
        if provider_info["needs_key"]:
            key_name = provider_info["key_name"]
            saved_key = config.get(key_name, "")
            api_key = st.text_input("🔑 API Key", value=saved_key, type="password", help=provider_info["key_help"])
            if api_key and api_key != saved_key:
                config[key_name] = api_key
                save_config(config)
                st.success("✅ Saved!")
            if not api_key:
                st.warning(f"⚠️ Enter {provider} API key")
                st.markdown(provider_info["key_help"])
        else:
            st.success("✅ No API key needed — free!")

        st.divider()

        with st.expander("💰 Provider Comparison"):
            st.markdown("""
| Provider | Cost | Speed |
|----------|------|-------|
| **Claude** | ~$0.03 | Fast |
| **OpenAI** | ~$0.03 | Fast |
| **Gemini** | Free! | Fast |
| **Groq** | Free! | Fastest |
| **Ollama** | Free | Slow |
            """)

        st.divider()
        st.caption("🔒 Keys saved locally at `~/.profile_optimizer/`")

    # Check ready
    if provider_info["needs_key"] and not api_key:
        # Show welcome landing page
        st.markdown("### 👈 Select your AI provider and enter API key to begin")
        st.markdown("---")

        # Tool showcase cards
        tools = [
            ("📋", "LinkedIn", "Rewrite headline, about, experience"),
            ("🐙", "GitHub", "Bio, README.md, repo descriptions"),
            ("🎯", "JD Matcher", "Match score, skill gaps, verdict"),
            ("📄", "Resume", "ATS-optimized resume from PDF"),
            ("🛠️", "Projects", "7 project ideas with tech stack"),
            ("🎤", "Interview", "Questions + personalized answers"),
            ("📧", "Outreach", "LinkedIn DMs, emails, referrals"),
            ("📊", "Skills Gap", "Learning roadmap + certifications"),
            ("🔍", "Keywords", "Job search strings for all platforms"),
            ("✉️", "Cover Letter", "Tailored letter for any JD"),
        ]

        cols = st.columns(5)
        for i, (icon, title, desc) in enumerate(tools):
            with cols[i % 5]:
                st.markdown(f"""
                <div class="welcome-card">
                    <div class="welcome-card-icon" style="animation-delay: {i * 0.1}s">{icon}</div>
                    <div class="welcome-card-title">{title}</div>
                    <div class="welcome-card-desc">{desc}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("""
        <div class="footer">
            Built with ❤️ — Profile Optimizer v2.0 • Streamlit + Claude/GPT/Gemini/Groq/Ollama
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Tabs ────────────────────────────────────
    tabs = st.tabs([
        "📋 LinkedIn",
        "🐙 GitHub",
        "🎯 JD Matcher",
        "📄 Resume",
        "🛠️ Projects",
        "🎤 Interview",
        "📧 Outreach",
        "📊 Skills Gap",
        "🔍 Keywords",
        "✉️ Cover Letter",
    ])

    with tabs[0]:
        tab_linkedin(provider, api_key, model)
    with tabs[1]:
        tab_github(provider, api_key, model)
    with tabs[2]:
        tab_jd_matcher(provider, api_key, model)
    with tabs[3]:
        tab_resume(provider, api_key, model)
    with tabs[4]:
        tab_projects(provider, api_key, model)
    with tabs[5]:
        tab_interview(provider, api_key, model)
    with tabs[6]:
        tab_outreach(provider, api_key, model)
    with tabs[7]:
        tab_skills_gap(provider, api_key, model)
    with tabs[8]:
        tab_keywords(provider, api_key, model)
    with tabs[9]:
        tab_cover_letter(provider, api_key, model)

    # Footer
    st.markdown("""
    <div class="footer">
        Built with ❤️ — Profile Optimizer v2.0 • 10 Tools • 5 AI Providers • 100% Local
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
