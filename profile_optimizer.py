#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║     PROFILE OPTIMIZER — LinkedIn & GitHub AI Rewriter        ║
║     Powered by Claude AI (claude-sonnet-4-6)                 ║
║     GitHub: auto-fetched | LinkedIn: paste from PDF          ║
╚══════════════════════════════════════════════════════════════╝

Setup:
    pip install anthropic requests
    export ANTHROPIC_API_KEY="sk-ant-xxxx"
    python profile_optimizer.py
"""

import anthropic
import requests
import json
import sys
import os
from datetime import datetime

# ══════════════════════════════════════════════
#  CONFIG — only change these two things
# ══════════════════════════════════════════════

GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "humaniods")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Paste your LinkedIn data from PDF below
LINKEDIN_PROFILE = {
    "name": "Sanyam Sharma",
    "headline": "AI Engineer @ZestGeek Solution | Building @Unpod | VoiceEnabled AI Agents & Real-time AI Applications | IBM Certified Data Analyst & Cloud Developer",
    "about": """
    As an AI Intern at ZestGeek Solutions, I contribute to developing machine learning models,
    optimizing their performance, and delivering AI-driven automation solutions. My work focuses
    on real-world applications, including NLP and data analysis, under expert mentorship to address
    complex business challenges. Pursuing a B.Tech in Computer Software Engineering from Rayat Bahra
    University, I incorporate backend development skills, such as Python and Django REST Framework,
    to design scalable APIs and integrate machine learning models into production-ready environments.
    Motivated by the potential of AI to tackle real-world problems, I thrive in collaborative settings
    that emphasize innovation and impact-driven solutions.
    """,
    "experience": [
        {
            "title": "Artificial Intelligence Engineer",
            "company": "ZestGeek Solutions Pvt Ltd",
            "duration": "April 2025 – Present (1 year 3 months)",
            "bullets": [
                "Developing and implementing machine learning models and automation solutions",
                "Training algorithms and optimizing model performance",
                "Working on NLP, Voice AI agents, RAG pipelines, LangGraph multi-agent systems",
                "Building Unpod platform — real-time AI telephony using SIP, WebRTC, LiveKit, VAPI",
                "Model evaluation with DeepEval and RAGAS, fine-tuning SLMs with LoRA/QLoRA",
            ]
        },
        {
            "title": "Data Engineer",
            "company": "IBM",
            "duration": "September 2024 – March 2025 (7 months)",
            "bullets": [
                "Completed Cloud Application Developer training with IBM",
                "Deployed a chatbot for a restaurant website (CSB project)",
                "Built HR data dashboard — Accenture Data Analytics project",
            ]
        },
        {
            "title": "Software Developer",
            "company": "JSpiders Training & Development Center",
            "duration": "March 2024 – August 2024 (6 months)",
            "bullets": ["Software development training, hands-on project work"]
        }
    ],
    "certifications": [
        "Docker Essentials: A Developer Introduction",
        "Tata Group - Cybersecurity Analyst Job Simulation",
        "AWS APAC - Solutions Architecture Job Simulation",
        "Build Your Own Chatbot (IBM)",
    ],
    "skills": [
        "Python", "LangChain", "LangGraph", "VAPI", "LiveKit", "FAISS",
        "LoRA", "QLoRA", "DeepEval", "RAGAS", "Django REST", "OAuth 2.0",
        "SIP", "WebRTC", "NLP", "Voice AI", "RAG", "IBM SPSS", "IBM Cognos"
    ],
    "education": "B.Tech, Computer Software Engineering — Rayat Bahra University (2021–2025)",
    "target_roles": "AI Engineer at startups, MNCs, consulting firms in Chandigarh, Bangalore, Pune or Remote",
    "known_issues": [
        "About section says 'AI Intern' — should say AI Engineer",
        "Top skills show IBM SPSS/Cognos — hides actual AI stack",
        "No mention of Voice AI, RAG, LangGraph, LiveKit in About",
        "Experience bullets are vague — no metrics or stack names",
        "Headline is too cluttered — hard to scan in 3 seconds",
    ]
}

# ══════════════════════════════════════════════
#  STEP 1 — FETCH GITHUB DATA
# ══════════════════════════════════════════════

def fetch_github_profile(username: str) -> dict:
    print(f"🐙  Fetching GitHub profile: @{username} ...")
    base = "https://api.github.com"
    headers = {"Accept": "application/vnd.github+json"}

    # User profile
    user_resp = requests.get(f"{base}/users/{username}", headers=headers)
    if user_resp.status_code != 200:
        print(f"❌  GitHub API error: {user_resp.status_code}")
        sys.exit(1)
    user = user_resp.json()

    # Public repos
    repos_resp = requests.get(
        f"{base}/users/{username}/repos",
        headers=headers,
        params={"sort": "updated", "per_page": 30, "type": "public"}
    )
    repos = repos_resp.json() if repos_resp.status_code == 200 else []

    # Process repos — sort by stars + recency
    processed_repos = []
    for r in repos:
        if not r.get("fork"):  # skip forked repos
            processed_repos.append({
                "name": r.get("name"),
                "description": r.get("description") or "No description",
                "language": r.get("language") or "Unknown",
                "stars": r.get("stargazers_count", 0),
                "forks": r.get("forks_count", 0),
                "topics": r.get("topics", []),
                "url": r.get("html_url"),
                "updated": r.get("updated_at", "")[:10],
                "visibility": "public",
            })

    # Sort by stars
    processed_repos.sort(key=lambda x: x["stars"], reverse=True)

    # Check if profile README exists
    readme_resp = requests.get(
        f"{base}/repos/{username}/{username}/readme",
        headers=headers
    )
    has_readme = readme_resp.status_code == 200

    github_data = {
        "username": username,
        "name": user.get("name") or username,
        "current_bio": user.get("bio") or "No bio set",
        "location": user.get("location") or "Not set",
        "public_repos": user.get("public_repos", 0),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "profile_url": f"https://github.com/{username}",
        "has_profile_readme": has_readme,
        "repos": processed_repos[:15],  # top 15
        "top_languages": _get_top_languages(processed_repos),
    }

    print(f"   ✅  Found {len(processed_repos)} public repos | {user.get('followers', 0)} followers")
    print(f"   ✅  Profile README: {'exists ✓' if has_readme else 'MISSING ✗'}")
    return github_data


def _get_top_languages(repos: list) -> list:
    lang_count = {}
    for r in repos:
        lang = r.get("language")
        if lang and lang != "Unknown":
            lang_count[lang] = lang_count.get(lang, 0) + 1
    return sorted(lang_count, key=lang_count.get, reverse=True)[:6]


# ══════════════════════════════════════════════
#  STEP 2 — BUILD AI PROMPT
# ══════════════════════════════════════════════

def build_prompt(linkedin: dict, github: dict) -> str:
    repos_summary = "\n".join([
        f"  - [{r['name']}] ⭐{r['stars']} | {r['language']} | {r['description'][:80]}"
        for r in github["repos"][:10]
    ])

    return f"""
You are an elite AI/ML personal branding expert and technical recruiter with 10+ years placing engineers at top Indian startups and MNCs.

Your job: Completely rewrite this engineer's LinkedIn and GitHub profiles to MAXIMALLY impress recruiters and pass ATS systems. Be BOLD and SPECIFIC — not generic.

TARGET: AI Engineer roles at product startups, MNCs, and consulting firms in India (Chandigarh/Bangalore/Pune/Remote).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LINKEDIN PROFILE (current — has issues)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name: {linkedin['name']}
Headline: {linkedin['headline']}
About: {linkedin['about'].strip()}
Experience: {json.dumps(linkedin['experience'], indent=2)}
Certifications: {', '.join(linkedin['certifications'])}
Skills: {', '.join(linkedin['skills'])}
Education: {linkedin['education']}
Target Roles: {linkedin['target_roles']}
Known Issues to Fix: {json.dumps(linkedin['known_issues'], indent=2)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GITHUB PROFILE (auto-fetched: @{github['username']})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current Bio: {github['current_bio']}
Location: {github['location']}
Public Repos: {github['public_repos']} | Followers: {github['followers']}
Has Profile README: {github['has_profile_readme']}
Top Languages: {', '.join(github['top_languages'])}
Repos (by stars):
{repos_summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULES FOR REWRITING:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. LinkedIn headline MUST be under 220 chars, scannable in 3 seconds, keyword-rich for ATS
2. About section: hook in first line, NO "I am passionate about", use action verbs, end with CTA
3. Experience bullets: use STAR format — Situation→Action→Result. Add tech stack names. Add numbers where possible.
4. GitHub bio: max 160 chars, punchy, tech-forward
5. README.md: must be visually structured with emojis, badges, project showcase
6. Repo descriptions: recruiter sees these — make them specific and impressive
7. Use these high-value ATS keywords naturally: LLM, RAG, Voice AI, LangGraph, LangChain, VAPI, LiveKit, WebRTC, SIP, LoRA, QLoRA, Fine-tuning, MLOps, NLP, Agentic AI, Multi-agent, Real-time AI, Python, Django, REST API, FAISS, Vector DB, DeepEval, RAGAS

Return ONLY a valid JSON object. No markdown, no backticks, no explanation. Exactly this structure:

{{
  "linkedin": {{
    "headline": "string — recruiter-optimized, max 220 chars",
    "about": "string — full rewritten About section, 4 paragraphs, use \\n\\n between paragraphs",
    "experience_bullets": {{
      "ZestGeek Solutions Pvt Ltd": ["5 rewritten STAR bullets, specific tech stack + impact"],
      "IBM": ["3 rewritten bullets with outcomes"],
      "JSpiders": ["1-2 bullets, frame as foundational skills"]
    }},
    "skills_priority_order": ["top 15 skills, most recruiter-relevant first"],
    "30_sec_pitch": "What to say when recruiter asks tell me about yourself — conversational, 5 sentences",
    "linkedin_post_idea": "1 post idea to write this week to boost visibility"
  }},
  "github": {{
    "bio": "string — max 160 chars, punchy",
    "repos_to_make_public": ["list of repo names that sound private/unnamed but should be public"],
    "repos_to_pin": ["exactly 6 repo names from fetched list — best ones to pin"],
    "repo_description_rewrites": [
      {{"name": "repo-name", "new_description": "improved 1-liner"}}
    ],
    "profile_readme_full": "complete README.md content — use markdown, emojis, badges, sections for: intro, tech stack, featured projects, stats, contact. Make it visually stunning.",
    "topics_to_add": {{"repo-name": ["tag1", "tag2", "tag3"]}}
  }},
  "action_checklist": [
    "ordered list of 10 exact steps to do RIGHT NOW to fix both profiles"
  ],
  "ats_keywords_bank": ["20 keywords to use across both profiles"],
  "red_flags_fixed": ["5 specific things that were hurting the profile — fixed now"],
  "estimated_impact": "1 sentence — what will change after these updates"
}}
"""


# ══════════════════════════════════════════════
#  STEP 3 — CALL CLAUDE AI
# ══════════════════════════════════════════════

def call_claude(prompt: str) -> dict:
    print("🧠  Claude AI rewriting your profiles...")
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = msg.content[0].text.strip()
    # Strip markdown fences if present
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"❌  JSON parse error: {e}")
        print("Raw Claude output:\n", raw[:500])
        sys.exit(1)


# ══════════════════════════════════════════════
#  STEP 4 — DISPLAY RESULTS
# ══════════════════════════════════════════════

def display(data: dict, github: dict):
    SEP  = "═" * 62
    THIN = "─" * 62
    ts   = datetime.now().strftime("%d %b %Y, %I:%M %p")

    print(f"\n{SEP}")
    print(f"  🚀  PROFILE OPTIMIZER RESULTS  |  {ts}")
    print(f"{SEP}")

    # ── LINKEDIN ──────────────────────────────
    li = data.get("linkedin", {})
    print(f"\n{'📌  LINKEDIN':}")
    print(THIN)

    print("\n🏷️  HEADLINE  ← copy this exactly:")
    print(f"\n  {li.get('headline', '')}\n")

    print("📝  ABOUT SECTION  ← paste in LinkedIn About:")
    print()
    about = li.get("about", "")
    for para in about.split("\n\n"):
        p = para.strip()
        if p:
            print(f"  {p}\n")

    print("💼  EXPERIENCE BULLETS:")
    for company, bullets in li.get("experience_bullets", {}).items():
        print(f"\n  🏢 {company}")
        for b in bullets:
            print(f"     • {b}")

    print(f"\n🔑  SKILLS ORDER  ← drag to this order in LinkedIn:")
    skills = li.get("skills_priority_order", [])
    for i, s in enumerate(skills, 1):
        print(f"  {i:2}. {s}")

    print(f"\n🎤  30-SECOND PITCH:")
    print(f"\n  {li.get('30_sec_pitch', '')}\n")

    print(f"💡  POST IDEA THIS WEEK:")
    print(f"  {li.get('linkedin_post_idea', '')}")

    # ── GITHUB ────────────────────────────────
    gh = data.get("github", {})
    print(f"\n{THIN}")
    print("🐙  GITHUB  ←  @" + github["username"])
    print(THIN)

    print(f"\n📛  BIO  ← Settings → Edit Profile → Bio:")
    print(f"  {gh.get('bio', '')}")

    print(f"\n📌  REPOS TO PIN  ← github.com → Customize Profile:")
    for i, r in enumerate(gh.get("repos_to_pin", []), 1):
        print(f"  {i}. {r}")

    pub = gh.get("repos_to_make_public", [])
    if pub:
        print(f"\n🔓  MAKE THESE REPOS PUBLIC  ← Settings → Danger Zone → Change visibility:")
        for r in pub:
            print(f"  • {r}")

    print(f"\n📝  REPO DESCRIPTION REWRITES  ← each repo → Edit:")
    for rd in gh.get("repo_description_rewrites", []):
        print(f"  [{rd.get('name')}]")
        print(f"   → {rd.get('new_description')}")

    topics = gh.get("topics_to_add", {})
    if topics:
        print(f"\n🏷️  TOPICS TO ADD  ← each repo → Manage Topics:")
        for repo, tags in topics.items():
            print(f"  [{repo}]: {', '.join(tags)}")

    # ── README ────────────────────────────────
    readme = gh.get("profile_readme_full", "")
    if readme:
        readme_file = f"README_github_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(readme_file, "w") as f:
            f.write(readme)
        print(f"\n📄  PROFILE README.md  ← saved as: {readme_file}")
        print(f"   Steps: Create repo '{github['username']}/{github['username']}' → upload this file")
        print("\n   Preview (first 10 lines):")
        for line in readme.split("\n")[:10]:
            print(f"   {line}")
        print("   ...")

    # ── ACTION CHECKLIST ──────────────────────
    print(f"\n{THIN}")
    print("✅  ACTION CHECKLIST  ← do these RIGHT NOW, in order")
    print(THIN)
    for i, step in enumerate(data.get("action_checklist", []), 1):
        print(f"  {i:2}. {step}")

    # ── ATS KEYWORDS ─────────────────────────
    print(f"\n🔍  ATS KEYWORDS BANK  ← use these across both profiles:")
    kw = data.get("ats_keywords_bank", [])
    print("  " + " • ".join(kw))

    # ── RED FLAGS ─────────────────────────────
    print(f"\n🛠️  RED FLAGS FIXED:")
    for flag in data.get("red_flags_fixed", []):
        print(f"  ✅  {flag}")

    # ── IMPACT ────────────────────────────────
    print(f"\n🎯  ESTIMATED IMPACT:")
    print(f"  {data.get('estimated_impact', '')}")

    print(f"\n{SEP}")
    print("  Done! README.md saved separately. Update profiles now.")
    print(f"{SEP}\n")


# ══════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════

def main():
    if not ANTHROPIC_API_KEY:
        print("❌  ANTHROPIC_API_KEY not set. Run:")
        print('   export ANTHROPIC_API_KEY="sk-ant-your-key-here"')
        sys.exit(1)
    if GITHUB_USERNAME == "humaniods":
        print("✅  GitHub username: humaniods")

    print("\n" + "═"*62)
    print("  🚀  PROFILE OPTIMIZER  |  github.com/" + GITHUB_USERNAME)
    print("═"*62 + "\n")

    # 1. Fetch GitHub
    github_data = fetch_github_profile(GITHUB_USERNAME)

    # 2. Build prompt
    prompt = build_prompt(LINKEDIN_PROFILE, github_data)

    # 3. Call Claude
    result = call_claude(prompt)

    # 4. Display
    display(result, github_data)

    # 5. Save full JSON
    out_file = f"profile_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_file, "w") as f:
        json.dump({"github_fetched": github_data, "optimized": result}, f, indent=2)
    print(f"📁  Full report saved → {out_file}\n")


if __name__ == "__main__":
    main()
