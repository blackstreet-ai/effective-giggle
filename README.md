# Effective Giggle

Content-creation automation pipeline built on the **OpenAI Agents SDK**.

This repository is an experiment in automating the YouTube video workflow—from topic ideation to research—one agent at a time.

---

## Directory layout

| Path | Purpose |
|------|---------|
| `effective_giggle/` | Python package where all agents & tools will live (to be added). |
| `vendor_docs/openai-agents-docs/` | **Third-party reference docs** for the OpenAI Agents SDK (mirrored for offline reading). |
| `docs/` | Project-specific docs & tutorials. |

## Getting started

1. Ensure Python ≥ 3.12 and [Poetry](https://python-poetry.org/) (or `pip` + virtualenv).
2. Install deps:
   ```bash
   pip install -e .
   ```
3. Read the quick tutorial in [`docs/getting_started.md`](docs/getting_started.md).

> For detailed SDK reference browse `vendor_docs/openai-agents-docs/index.html` or the upstream site.

## Roadmap (v1)

- `topic_selector` agent — pulls candidate topics from a Notion database.
- `researcher` agent — compiles bullet-point research & citations.

See the full [Project Brief](docs/project-brief.md).

## Contributing / Collaboration

This is a personal learning project; feel free to open issues or PRs if you find something helpful.

## License

MIT (see `LICENSE`).
