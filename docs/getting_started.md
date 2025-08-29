# Getting Started

Welcome to **Effective Giggle**! This guide helps you set up the project locally using the `uv` package manager.

---

## Prerequisites

- **Python ≥ 3.12**
- **[uv](https://github.com/astral-sh/uv)** – lightning-fast package manager / virtual-env tool.
  ```bash
  # Install via pipx (recommended)
  pipx install uv
  # …or with pip
  pip install uv
  ```

---
## Installation steps

```bash
# 1. Clone the repo (if you haven’t already)
# git clone https://github.com/<you>/effective-giggle.git
cd effective-giggle

# 2. Create an isolated virtual environment
uv venv .venv
source .venv/bin/activate

# 3. Install project in editable mode
uv pip install -e .
```

> `uv` transparently replaces `pip` / `pip-tools`; use `uv pip` for any follow-up installs.

---
## First run

```bash
python -m effective_giggle --help  # CLI to be added soon
```

While the Python package is still a scaffold, you can explore the **OpenAI Agents SDK** docs stored offline at `vendor_docs/openai-agents-docs/`.

---
## Next steps

1. Read the [Project Brief](project-brief.md) to understand the roadmap.
2. Follow upcoming guides in `docs/` as agents are implemented.

Happy hacking! 💫
