# 🔍 Code Review Agent

**[English README](README.md)**

基於 [Google ADK (Agent Development Kit)](https://google.github.io/adk-docs/) 建構的自動化 Code Review 多代理人 Pipeline。

## 架構概覽

本專案使用 Google ADK 的 **多代理人 (Multi-Agent)** 架構，將 Code Review 拆成三個階段依序執行：

```
codereview_pipeline (SequentialAgent)
│
├── Phase 1 — 資料收集 (ParallelAgent)
│   ├── diff_fetcher       取得 git diff 與變更檔案
│   ├── commit_reader      讀取 commit 訊息
│   └── secret_scanner     掃描洩漏的金鑰/密碼
│
├── Phase 2 — 平行審查 (ParallelAgent)
│   ├── logic_reviewer     邏輯正確性 / Bug / 效能
│   ├── style_checker      命名 / 可讀性 / 文件
│   └── security_auditor   注入、認證、資安風險
│
└── Phase 3 — 產出報告 (LlmAgent)
    └── report_generator   統整所有結果，給出結論
```

> **ADK 核心元件說明**
> - `SequentialAgent`：依序執行子代理人
> - `ParallelAgent`：平行執行子代理人，適合同時做不相依的工作
> - `LlmAgent`：搭配 LLM 做推理與生成

## 功能

| 功能 | 說明 |
|------|------|
| 🔀 Git Diff 分析 | 自動取得分支間的變更差異 |
| 📝 Commit 訊息理解 | 讀取 commit 歷史，了解修改意圖 |
| 🔐 機敏資訊掃描 | 偵測 API Key、Token、密碼等洩漏 |
| 🧠 邏輯審查 | 檢查 Bug、邊界條件、效能、錯誤處理 |
| 🎨 風格審查 | 命名慣例、可讀性、文件完整度 |
| 🛡️ 資安審查 | 注入漏洞、認證問題、不安全的設計模式 |
| 📊 結構化報告 | 產出 APPROVE / REQUEST CHANGES / REJECT 結論 |

## 快速開始

### 1. 安裝

```bash
pip install -r requirements.txt
```

### 2. 設定 API Key

在 `.env` 中填入你的 Google API Key：

```env
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your-api-key-here
```

### 3. 啟動

```bash
adk web
```

開啟 http://localhost:8000，在下拉選單選擇 **codereview_agent** 即可。

### 4. 使用範例

```
Review the changes on the current branch against main
```

```
Review the diff between develop and feature/auth-refactor
```

## 專案結構

```
.
├── codereview_agent/
│   ├── __init__.py     # 模組初始化
│   ├── agent.py        # 代理人定義 (7 個 Agent)
│   └── tools.py        # Git 工具函式 (diff, commits, secrets …)
├── .env                # API Key 設定
├── requirements.txt    # 相依套件 (google-adk)
└── README.md
```

## 整合到其他專案

把 `codereview_agent/` 資料夾複製到你的專案根目錄，然後在該目錄執行 `adk web` 就好：

```bash
cp -r codereview_agent/ /path/to/your/project/
cd /path/to/your/project
adk web
```

## 自訂模型

編輯 `codereview_agent/agent.py` 中的 `MODEL` 常數：

```python
MODEL = "gemini-2.0-flash"              # 預設（快速）
MODEL = "gemini-2.5-pro-preview-06-05"  # 更深入的分析
```

## License

MIT
