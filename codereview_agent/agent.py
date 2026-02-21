"""
Code Review Workflow Agent — ADK Multi-Agent Pipeline

Architecture:
  ┌─────────────────────────────────────────────────────────────────┐
  │                 codereview_pipeline (Sequential)                │
  │                                                                 │
  │  ┌──────────────────────────────────────────────────────────┐   │
  │  │          Phase 1: gather_phase (Parallel)                │  │
  │  │  ┌──────────────┐ ┌──────────────┐ ┌────────────────┐  │  │
  │  │  │ diff_fetcher │ │commit_reader │ │ secret_scanner │  │  │
  │  │  └──────────────┘ └──────────────┘ └────────────────┘  │  │
  │  └──────────────────────────────────────────────────────────┘  │
  │                            ↓                                    │
  │  ┌──────────────────────────────────────────────────────────┐  │
  │  │          Phase 2: review_phase (Parallel)                │  │
  │  │  ┌────────────────┐ ┌─────────────┐ ┌───────────────┐  │  │
  │  │  │ logic_reviewer │ │style_checker│ │security_audit │  │  │
  │  │  └────────────────┘ └─────────────┘ └───────────────┘  │  │
  │  └──────────────────────────────────────────────────────────┘  │
  │                            ↓                                    │
  │  ┌──────────────────────────────────────────────────────────┐  │
  │  │          Phase 3: report_generator (LLM)                 │  │
  │  └──────────────────────────────────────────────────────────┘  │
  └─────────────────────────────────────────────────────────────────┘

Usage:
  1. cd to the parent directory of codereview_agent/
  2. Run: adk web
  3. Select codereview_agent from the dropdown
  4. Ask: "Review the changes on branch feature/xxx against main"
"""

from google.adk.agents import Agent, LlmAgent, SequentialAgent, ParallelAgent

from .tools import (
    get_git_diff,
    get_file_content,
    get_commit_messages,
    check_for_secrets,
    list_repo_structure,
)

# ──────────────────────────────────────────────────────────────────
# Model configuration — change this to switch models globally
# ──────────────────────────────────────────────────────────────────
MODEL = "gemini-2.0-flash"


# ══════════════════════════════════════════════════════════════════
# PHASE 1: Data Gathering (Parallel)
# Simultaneously fetch diff, commit messages, and scan for secrets
# ══════════════════════════════════════════════════════════════════

diff_fetcher = LlmAgent(
    name="diff_fetcher",
    model=MODEL,
    description="Fetches the git diff and changed file list between branches.",
    instruction=(
        "You are a diff retrieval specialist. Your ONLY job is to fetch the code diff.\n\n"
        "Steps:\n"
        "1. Use the get_git_diff tool with the branches the user specified.\n"
        "   - If no branches specified, use target_branch='main' and source_branch='HEAD'.\n"
        "2. If the diff is large, also use list_repo_structure to understand the project layout.\n"
        "3. Output the complete diff content, file list, and stats. Do NOT analyze the code.\n"
        "4. If certain changed files are complex, use get_file_content to fetch full context.\n"
    ),
    tools=[get_git_diff, get_file_content, list_repo_structure],
    output_key="diff_data",
)

commit_reader = LlmAgent(
    name="commit_reader",
    model=MODEL,
    description="Reads commit messages to understand the intent of changes.",
    instruction=(
        "You are a commit message reader. Your ONLY job is to fetch and summarize commits.\n\n"
        "Steps:\n"
        "1. Use get_commit_messages to fetch all commits between branches.\n"
        "   - Default: target_branch='main', source_branch='HEAD'.\n"
        "2. Output a concise summary of what the commits intend to achieve.\n"
        "3. Note any commit message quality issues (vague messages, missing context).\n"
    ),
    tools=[get_commit_messages],
    output_key="commit_summary",
)

secret_scanner = LlmAgent(
    name="secret_scanner",
    model=MODEL,
    description="Scans code changes for leaked secrets and sensitive data.",
    instruction=(
        "You are a secret detection specialist. Your ONLY job is to find leaked secrets.\n\n"
        "Steps:\n"
        "1. First use get_git_diff to get the raw diff text.\n"
        "2. Then use check_for_secrets with the diff text.\n"
        "3. Output the security scan results clearly:\n"
        "   - Risk level (CLEAN / MEDIUM / HIGH)\n"
        "   - Any findings with type and severity\n"
        "4. If risk is HIGH, emphasize this strongly in your output.\n"
    ),
    tools=[get_git_diff, check_for_secrets],
    output_key="secret_scan",
)

gather_phase = ParallelAgent(
    name="gather_phase",
    description="Phase 1: Gather all necessary data in parallel.",
    sub_agents=[diff_fetcher, commit_reader, secret_scanner],
)


# ══════════════════════════════════════════════════════════════════
# PHASE 2: Code Review (Parallel)
# Three specialist reviewers analyze the code simultaneously
# ══════════════════════════════════════════════════════════════════

logic_reviewer = LlmAgent(
    name="logic_reviewer",
    model=MODEL,
    description="Reviews code logic, correctness, and potential bugs.",
    instruction=(
        "You are a senior software engineer performing a logic review.\n\n"
        "Analyze the diff data: {diff_data}\n\n"
        "Review for:\n"
        "1. **Correctness**: Logic errors, off-by-one errors, null/undefined handling\n"
        "2. **Edge Cases**: Unhandled error conditions, boundary values, empty inputs\n"
        "3. **Performance**: N+1 queries, unnecessary loops, memory leaks, blocking calls\n"
        "4. **Concurrency**: Race conditions, deadlocks, thread safety issues\n"
        "5. **Error Handling**: Missing try/catch, unhandled promise rejections, error propagation\n"
        "6. **Testing**: Whether changes include tests, test coverage gaps\n\n"
        "Context from commits: {commit_summary}\n\n"
        "Output format:\n"
        "- List each finding with: file, line range, severity (🔴 Critical / 🟡 Warning / 🔵 Info), description\n"
        "- If no issues found, state that explicitly.\n"
    ),
    output_key="logic_review",
)

style_checker = LlmAgent(
    name="style_checker",
    model=MODEL,
    description="Reviews code style, readability, and maintainability.",
    instruction=(
        "You are a code style and readability reviewer.\n\n"
        "Analyze the diff data: {diff_data}\n\n"
        "Review for:\n"
        "1. **Naming**: Variable/function/class naming — clear, descriptive, consistent conventions\n"
        "2. **Code Structure**: Function length, nesting depth, single responsibility\n"
        "3. **Documentation**: Missing docstrings, outdated comments, unclear code sections\n"
        "4. **Duplication**: Copy-pasted code, opportunities for abstraction\n"
        "5. **Readability**: Complex expressions, magic numbers, unexplained abbreviations\n"
        "6. **Consistency**: Coding style matching the rest of the project\n\n"
        "Output format:\n"
        "- List each finding with: file, line range, category, suggestion\n"
        "- Prioritize actionable suggestions over nitpicks.\n"
    ),
    output_key="style_review",
)

security_auditor = LlmAgent(
    name="security_auditor",
    model=MODEL,
    description="Reviews code for security vulnerabilities and best practices.",
    instruction=(
        "You are a security auditor reviewing code changes.\n\n"
        "Analyze the diff data: {diff_data}\n\n"
        "Secret scan results: {secret_scan}\n\n"
        "Review for:\n"
        "1. **Injection**: SQL injection, command injection, XSS, template injection\n"
        "2. **Authentication/Authorization**: Broken access control, missing auth checks\n"
        "3. **Data Exposure**: Sensitive data in logs, responses, or error messages\n"
        "4. **Input Validation**: Unsanitized user input, missing validation\n"
        "5. **Dependencies**: Known vulnerable packages, outdated dependencies\n"
        "6. **Configuration**: Hardcoded credentials, insecure defaults, debug mode\n"
        "7. **Secrets**: Incorporate the secret scan findings from {secret_scan}\n\n"
        "Output format:\n"
        "- List each finding with: severity (🔴 Critical / 🟡 Warning / 🔵 Info), "
        "OWASP category if applicable, file, description, remediation\n"
    ),
    output_key="security_review",
)

review_phase = ParallelAgent(
    name="review_phase",
    description="Phase 2: Three specialist reviewers analyze the code in parallel.",
    sub_agents=[logic_reviewer, style_checker, security_auditor],
)


# ══════════════════════════════════════════════════════════════════
# PHASE 3: Report Generation
# Synthesize all reviews into one structured report
# ══════════════════════════════════════════════════════════════════

report_generator = LlmAgent(
    name="report_generator",
    model=MODEL,
    description="Synthesizes all review results into a final structured report.",
    instruction=(
        "You are the lead reviewer. Compile a comprehensive code review report.\n\n"
        "═══════════════════════════════════════\n"
        "INPUT DATA\n"
        "═══════════════════════════════════════\n"
        "Commit Summary: {commit_summary}\n"
        "Logic Review: {logic_review}\n"
        "Style Review: {style_review}\n"
        "Security Review: {security_review}\n"
        "Secret Scan: {secret_scan}\n\n"
        "═══════════════════════════════════════\n"
        "OUTPUT FORMAT\n"
        "═══════════════════════════════════════\n"
        "Generate the report in this EXACT structure:\n\n"
        "# 📋 Code Review Report\n\n"
        "## 📊 Overview\n"
        "- **Branch**: (from context)\n"
        "- **Files Changed**: (count)\n"
        "- **Commits**: (count + brief summary)\n"
        "- **Overall Rating**: ✅ APPROVE / ⚠️ REQUEST CHANGES / ❌ REJECT\n"
        "- **Risk Level**: LOW / MEDIUM / HIGH\n\n"
        "## 🔐 Security Summary\n"
        "- Secret scan results\n"
        "- Security findings (if any)\n\n"
        "## 🔴 Critical Issues (Must Fix)\n"
        "List all critical findings from all reviewers. Include file, line, description.\n\n"
        "## 🟡 Warnings (Should Fix)\n"
        "List all warnings. Include file, line, description.\n\n"
        "## 🔵 Suggestions (Nice to Have)\n"
        "List all informational suggestions.\n\n"
        "## ✅ What's Good\n"
        "Highlight positive aspects of the code changes.\n\n"
        "## 📝 Recommended Actions\n"
        "Numbered list of prioritized actions for the author.\n\n"
        "═══════════════════════════════════════\n"
        "RULES:\n"
        "- De-duplicate findings from different reviewers\n"
        "- Prioritize critical issues at the top\n"
        "- Be constructive — explain WHY something is an issue\n"
        "- If no issues found, say so and approve\n"
        "- Use the Overall Rating to give a clear verdict\n"
    ),
)


# ══════════════════════════════════════════════════════════════════
# ROOT AGENT: Full Pipeline
# ══════════════════════════════════════════════════════════════════

root_agent = SequentialAgent(
    name="codereview_pipeline",
    description=(
        "A comprehensive code review workflow that gathers diffs, "
        "runs parallel reviews (logic, style, security), and produces "
        "a structured review report."
    ),
    sub_agents=[gather_phase, review_phase, report_generator],
)
