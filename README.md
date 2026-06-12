# Claude Marketplace

A personal collection of Claude Code plugins.

## Available Plugins

| Plugin | Description | Version |
| --- | --- | --- |
| graphify-kit | Battle-tested graphify (knowledge graph) onboarding for any repo: exclusion analysis, agent navigation protocol, Explore override, session sync hooks, worktree seeding, and a graph-health doctor | 0.3.0 |

## Installation

```
/plugin marketplace add psalkowski/claude-marketplace
/plugin install graphify-kit
```

## Adding a Plugin

Each plugin lives in `plugins/<name>/` with the following structure:

```
plugins/<name>/
  .claude-plugin/
    plugin.json     # plugin manifest
  skills/           # skill definitions
  agents/           # agent definitions
```
