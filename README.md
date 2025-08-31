# Effective Giggle

Content-creation automation pipeline built on the **OpenAI Agents SDK**.

This repository is an experiment in automating the YouTube video workflow—from topic ideation to research—one agent at a time.

## 🚀 Quick Start

### Prerequisites
- Python ≥ 3.12
- OpenAI API key
- Notion API key (for database integration)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/blackstreet-ai/effective-giggle.git
   cd effective-giggle
   ```

2. **Install dependencies**
   ```bash
   pip install -e .
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Run the main application**
   ```bash
   python main.py
   ```

## 📁 Project Structure

| Path | Purpose |
|------|---------|
| `effective_giggle/agents/` | Individual agent implementations (researcher, topic_selector) |
| `effective_giggle/core/` | Base agent classes and shared functionality |
| `effective_giggle/tools/` | MCP tools and integrations (Notion, etc.) |
| `docs/` | Project documentation and tutorials |
| `.windsurf/` | Development workflows and coding standards |

## 🤖 Available Agents

- **Topic Selector Agent** - Pulls candidate topics from a Notion database
- **Researcher Agent** - Compiles bullet-point research & citations

## 📚 Documentation

- [Getting Started Guide](docs/getting_started.md)
- [Project Brief](docs/project-brief.md)
- [Agent Development Rules](.windsurf/rules/agent-development.md)

## Roadmap (v1)

- `topic_selector` agent — pulls candidate topics from a Notion database.
- `researcher` agent — compiles bullet-point research & citations.

See the full [Project Brief](docs/project-brief.md).

## Contributing / Collaboration

This is a personal learning project; feel free to open issues or PRs if you find something helpful.

## License

MIT (see `LICENSE`).
