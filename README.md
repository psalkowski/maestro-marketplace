# Maestro Marketplace

Claude Code plugins for provider-agnostic docs, knowledge graphs, spec workflows, and Conductor integration. Install `maestro` and run `/maestro:setup` to onboard a project — it sets up the rest for you.

## Getting started

```
/plugin marketplace add psalkowski/maestro-marketplace
/plugin install maestro
/maestro:setup
```

`maestro` is the front door — it interviews you in plain terms and installs &
configures the rest for you, so you don't need to know the other plugins by
name. The list below is what it can set up (you can also install any of them
individually).

## Available Plugins

| Plugin | Description | Version |
| --- | --- | --- |
| maestro | Start here. `/maestro:setup` interviews you (docs location, Conductor, knowledge graph, spec workflow) and installs + configures the right plugins in order | 0.1.1 |
| docs-hub | Provider-agnostic project docs: per-repo Docs Root at `.docs/vault` (symlink to a durable Backing Store), unified `## docs configuration` block, built-in filesystem provider, front-door setup with legacy migration | 0.1.0 |
| docs-obsidian | Obsidian driver for the docs-hub contract: vault bootstrap, Backing Store linking into `.docs/vault`, optional MCP add-on with Local REST API port detection | 0.1.0 |
| conductor-kit | Conductor integration: discovery-first GUI/terminal-parity action skills (create-pr, code-review, fix-errors, resolve-conflicts, rename-branch, address-cr), grounded in Conductor's real defaults; personal-layer prompt overrides; workspace setup script with docs/graph seeding | 0.2.0 |
| graphify-kit | Battle-tested graphify (knowledge graph) onboarding for any repo: exclusion analysis, agent navigation protocol, Explore override, session sync hooks, worktree seeding, and a graph-health doctor | 0.5.0 |
| spec | Provider-agnostic spec workflow (storage via docs-hub): `spec:plan` single front door (brainstorm + grill + spec, optional lean plan doc, execution-mode decision); `spec:execute` runs handed-off plans through pinned subagents | 0.3.0 |

## Installing a plugin individually

`/maestro:setup` installs what you need, but you can also install any plugin
directly:

```
/plugin marketplace add psalkowski/maestro-marketplace
/plugin install <plugin-name>
```

## How the plugins relate

`docs-hub` owns the storage contract (Docs Root, config block, filesystem provider). `docs-obsidian` is the first provider driver; future drivers (Notion, Google Drive) follow the same shape. `spec` and `graphify-kit` are consumers — they read/write docs through the Docs Root without knowing the provider. `conductor-kit` wires it all into Conductor workspaces (worktree seeding, prompt overrides).

## Adding a Plugin

Each plugin lives in `plugins/<name>/` with the following structure:

```
plugins/<name>/
  .claude-plugin/
    plugin.json     # plugin manifest
  skills/           # skill definitions
  agents/           # agent definitions
```
