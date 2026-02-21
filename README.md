# 🔍 Code Review Agent

**[中文版 README](README.zh-TW.md)**

An automated Code Review multi-agent pipeline built on [Google ADK (Agent Development Kit)](https://google.github.io/adk-docs/).

## Architecture

This project uses Google ADK's **Multi-Agent** architecture, splitting the review into three sequential phases:

```
codereview_pipeline (SequentialAgent)
│
├── Phase 1 — Data Gathering (ParallelAgent)
│   ├── diff_fetcher       Fetches git diff & changed files
│   ├── commit_reader      Reads commit messages
│   └── secret_scanner     Scans for leaked keys / passwords
│
├── Phase 2 — Parallel Review (ParallelAgent)
│   ├── logic_reviewer     Correctness / Bugs / Performance
│   ├── style_checker      Naming / Readability / Documentation
│   └── security_auditor   Injection, Auth, Security risks
│
└── Phase 3 — Report (LlmAgent)
    └── report_generator   Synthesizes findings into a verdict
```

> **ADK Core Components**
> - `SequentialAgent` — Runs sub-agents one after another
> - `ParallelAgent` — Runs sub-agents concurrently for independent tasks
> - `LlmAgent` — Uses an LLM for reasoning and generation

## Features

| Feature | Description |
|---------|-------------|
| 🔀 Git Diff Analysis | Fetches code diffs between branches automatically |
| 📝 Commit Understanding | Reads commit history to understand change intent |
| 🔐 Secret Scanning | Detects leaked API keys, tokens, and passwords |
| 🧠 Logic Review | Checks for bugs, edge cases, performance, error handling |
| 🎨 Style Review | Naming conventions, readability, documentation |
| 🛡️ Security Audit | Injection, authentication issues, insecure patterns |
| 📊 Structured Report | Outputs a verdict: APPROVE / REQUEST CHANGES / REJECT |

## Quick Start

### 1. Install

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Set your Google API Key in `.env`:

```env
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your-api-key-here
```

### 3. Run

```bash
adk web
```

Open http://localhost:8000 and select **codereview_agent** from the dropdown.

### 4. Example Prompts

```
Review the changes on the current branch against main
```

```
Review the diff between develop and feature/auth-refactor
```

## Project Structure

```
.
├── codereview_agent/
│   ├── __init__.py     # Module init
│   ├── agent.py        # Agent definitions (7 agents)
│   └── tools.py        # Git tool functions (diff, commits, secrets …)
├── .env                # API Key config
├── requirements.txt    # Dependencies (google-adk)
└── README.md
```

## Integration

Copy `codereview_agent/` into your project root, then run `adk web` from there:

```bash
cp -r codereview_agent/ /path/to/your/project/
cd /path/to/your/project
adk web
```

## Switching Models

Edit the `MODEL` constant in `codereview_agent/agent.py`:

```python
MODEL = "gemini-2.0-flash"              # Default (fast)
MODEL = "gemini-2.5-pro-preview-06-05"  # Deeper analysis
```

## License

MIT
