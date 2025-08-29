# Project Brief

## One-liner
Content-creation automation pipeline for YouTube built with the **OpenAI Agents SDK**.

## Problem & Users
This is a personal learning project whose goal is to automate as much of the YouTube video workflow as possible.

## Core Features (v1)
- Agents communicate with a Notion database through MCP tools.
- Initial pipeline phases:
  1. **`topic_selector`** – reads candidate topics from Notion (Status ="Idea") and moves the chosen one to "Research".
  2. **`researcher`** – gathers web sources and outputs:
     - concise bullet-point digest
     - citation list (URL + title)
- Ability to switch models via **LiteLLM** backend.

## Tech Stack
- Python ≥ 3.12
- **OpenAI Agents SDK**  
  (`openai` package plus `openai-agents` extras once released)
- **uv** package manager & virtual-env tool
- Notion API (exposed to agents through a custom MCP server)
- LiteLLM for model abstraction

## Constraints
No external deadlines—optimize for clarity, experimentation, and well-documented code.

## Deliverables
- Well-commented agent & tool source code (`effective_giggle/`)
- Markdown docs & tutorials (`docs/`)
- Workflow definitions (`.windsurf/workflows/`)

## Collaboration Style
You (Cascade) handle most programming; I provide direction, review, and tuning.

## Future Roadmap (beyond v1)
- `script_writer` – drafts the video script.
- `narrator` – generates voice-over via TTS.
- `video_renderer` – stitches visuals & audio.
- `uploader` – publishes to YouTube with title/description/thumbnail.

*Last updated: 2025-08-28*