# 🔍 Code Review Workflow Agent (Google ADK)

An automated, multi-agent code review pipeline powered by **Google Agent Development Kit (ADK)**.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│              codereview_pipeline (SequentialAgent)               │
│                                                                  │
│  Phase 1: gather_phase (ParallelAgent)                          │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────┐          │
│  │ diff_fetcher │ │commit_reader │ │ secret_scanner │          │
│  └──────────────┘ └──────────────┘ └────────────────┘          │
│                          ↓                                       │
│  Phase 2: review_phase (ParallelAgent)                          │
│  ┌────────────────┐ ┌──────────────┐ ┌────────────────┐        │
│  │ logic_reviewer │ │style_checker │ │security_auditor│        │
│  └────────────────┘ └──────────────┘ └────────────────┘        │
│                          ↓                                       │
│  Phase 3: report_generator (LlmAgent)                           │
│  ┌──────────────────────────────────────────────────────┐       │
│  │          Final Structured Review Report              │       │
│  └──────────────────────────────────────────────────────┘       │
└──────────────────────────────────────────────────────────────────┘
```

## Features

| Feature | Description |
|---------|-------------|
| 🔀 **Git Diff Analysis** | Automatically fetches and analyzes code diffs between branches |
| 📝 **Commit Message Review** | Reads commit history to understand change intent |
| 🔐 **Secret Scanning** | Detects leaked API keys, tokens, passwords, and credentials |
| 🧠 **Logic Review** | Checks for bugs, edge cases, performance issues, and error handling |
| 🎨 **Style Review** | Evaluates naming, readability, documentation, and code consistency |
| 🛡️ **Security Audit** | Finds injection vulnerabilities, auth issues, and insecure patterns |
| 📊 **Structured Report** | Produces a prioritized report with APPROVE / REQUEST CHANGES / REJECT verdict |

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API key

Edit `.env` and set your Google API key:

```bash
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your-api-key-here
```

### 3. Run the agent

```bash
# Navigate to the PARENT directory of codereview_agent/
cd /path/to/this/project

# Launch ADK Web UI
adk web

# Open http://localhost:8000 and select "codereview_agent"
```

### 4. Example prompts

```
Review the changes on the current branch against main
```

```
Review the diff between develop and feature/auth-refactor
```

```
Code review all changes targeting the release/v2.0 branch
```

## Integration into Existing Projects

This agent is designed to be **easily portable**. To add code review to any project:

### Option A: Copy the agent folder

```bash
# Copy the codereview_agent/ folder into your project
cp -r codereview_agent/ /path/to/your/project/

# Navigate to your project root and run
cd /path/to/your/project
adk web
```

### Option B: Symlink (shared agent)

```bash
# Create a symlink in your project
ln -s /path/to/codereview_agent /path/to/your/project/codereview_agent

# Run from your project root
cd /path/to/your/project
adk web
```

### Option C: CI/CD Integration

```yaml
# .github/workflows/code-review.yml
name: AI Code Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for diff

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install ADK
        run: pip install google-adk

      - name: Run Code Review
        env:
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
        run: |
          adk run codereview_agent/ \
            --input "Review changes between origin/main and HEAD"
```

## Customization

### Switch Models

Edit `agent.py` and change the `MODEL` constant:

```python
# Default
MODEL = "gemini-2.0-flash"

# For deeper analysis
MODEL = "gemini-2.5-pro-preview-06-05"

# For non-Google models (requires LiteLLM)
MODEL = "litellm/anthropic/claude-sonnet-4-20250514"
```

### Add Custom Review Rules

Create project-specific review rules by adding a `.codereview.yml`:

```yaml
# .codereview.yml (future enhancement)
rules:
  max_function_length: 50
  require_docstrings: true
  forbidden_patterns:
    - "TODO"
    - "FIXME"
    - "HACK"
```

## Project Structure

```
.
├── codereview_agent/
│   ├── __init__.py        # Module initialization
│   ├── agent.py           # Agent pipeline definition (7 agents)
│   └── tools.py           # Git tools (diff, commits, secrets, etc.)
├── .env                   # API key configuration
├── .gitignore
├── requirements.txt
└── README.md
```

## How It Works

1. **Phase 1 — Data Gathering** (runs in parallel):
   - `diff_fetcher`: Gets git diff, changed files, and project structure
   - `commit_reader`: Reads commit messages and summarizes intent
   - `secret_scanner`: Scans diff text for leaked credentials

2. **Phase 2 — Specialist Review** (runs in parallel):
   - `logic_reviewer`: Checks correctness, edge cases, performance, error handling
   - `style_checker`: Evaluates naming, readability, documentation, consistency
   - `security_auditor`: Finds injection, auth, data exposure, config issues

3. **Phase 3 — Report**:
   - `report_generator`: Synthesizes all findings into a structured report with verdict

## License

MIT
