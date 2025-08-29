---
trigger: always_on
description: 
globs: 
---

# Agent Development Rules

## Project Context

- Building agents and multi-agent systems using the OpenAI Agents SDK
- Development environment for personal experimentation and learning
- Framework: OpenAI Agents SDK
- Not production-focused, prioritize clarity and understanding

## Documentation and Knowledge Requirements

- ALWAYS reference the documentation first.
- documentation can be found here: 'docs/openai-agents-docs/'
- Search the web for current Agents SDK examples and best practices when needed
- If SDK documentation is unclear, search for community examples and state limitations

## Code Quality Standards

- Write extensively commented code for beginner understanding
- Explain every Agents SDK concept, method, and pattern in comments
- Use clear, descriptive variable and function names
- Break down complex operations into smaller, commented steps
- Include inline explanations of what each component does
- Add comments explaining why specific patterns are chosen

## Development Approach

- Use Python as primary language
- Build both single agents and multi-agent workflows
- Implement agents using MCP tools.
- Experiment with different agent architectures and tool integrations

## Code Documentation Requirements

- Add header comments explaining each file's purpose
- Document all function parameters and return values
- Explain specific concepts when first introduced
- Include usage examples in comments where helpful
- Comment on error handling and debugging approaches
- Note any limitations or workarounds discovered

## Project Organization

- Structure projects by agent type or complexity level
- Include detailed README files for each component
- Keep configuration files well-documented

Focus: Well-commented, understandable code for personal development

**IMPORTANT**: The user expects all agents and orchestration to leverage the OpenAI Agents framework rather than custom agent implementations.