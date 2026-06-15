---
description: Use when wiring a repository into Conductor with conductor-kit — writes the personal-layer prompt overrides (.conductor/settings.local.toml) that delegate Conductor's GUI actions to the conductor-kit Action Skills, and generates the workspace lifecycle scripts (.conductor/setup.sh, run.sh, archive.sh) that seed .docs/, CLAUDE.local.md, and the graphify graph into every new workspace, run its start command, and stop its processes on archive. Triggers on /conductor-kit:setup.
---

# /conductor-kit:setup

Wire this repository into Conductor: Prompt Overrides in the Personal Layer (`.conductor/settings.local.toml`) so every Conductor action — GUI button or terminal mode — invokes the matching conductor-kit Action Skill, plus generated lifecycle scripts (`.conductor/setup.sh`, `run.sh`, `archive.sh`) for new-workspace seeding, the Run button, and archive teardown. Idempotent — re-running refreshes the managed parts and preserves everything else (unknown TOML keys, each script's project-specific section).

Both files are personal and never committed (see ADR 0003): a committed "invoke /conductor-kit:…" would break teammates without the plugin.

## Step 1 — Worktree check (config MUST land on the main checkout)

Conductor reads `.conductor/` from the repo's main checkout, so writing it into a worktree would be invisible.

1. Run `git rev-parse --git-dir` and `git rev-parse --path-format=absolute --git-common-dir`.
2. If the two outputs are **equal** (allowing for relative vs absolute of the same path): this is the main checkout — proceed, target directory is the repo root.
3. If they **differ**, this is a worktree. Derive the main checkout path: the parent directory of the `--git-common-dir` output (strip the trailing `/.git`). Ask the user where to write the config:
   - **Main checkout** (default, recommended) — use the derived path as the target; all writes below go to `<main>/.conductor/`.
   - **Here** — only if the user explicitly wants it; warn that Conductor will not pick it up from a worktree.

All paths below are relative to the chosen target root.

## Step 2 — Write `.conductor/settings.local.toml`

Create the `.conductor/` directory if missing. The managed content is:

```toml
[prompts]
code_review = "Invoke the conductor-kit code-review skill."
create_pr = "Invoke the conductor-kit create-pr skill."
fix_errors = "Invoke the conductor-kit fix-errors skill."
resolve_merge_conflicts = "Invoke the conductor-kit resolve-conflicts skill."
rename_branch = "Invoke the conductor-kit rename-branch skill."

[scripts]
setup = "bash \"$CONDUCTOR_ROOT_PATH/.conductor/setup.sh\""
run = "bash \"$CONDUCTOR_ROOT_PATH/.conductor/run.sh\""
archive = "bash \"$CONDUCTOR_ROOT_PATH/.conductor/archive.sh\""
```

The five `prompts` keys override exactly the **five native task actions**, each a one-liner delegating to the matching conductor-kit Action Skill. The three `scripts` keys wire Conductor's workspace lifecycle hooks to the scripts generated in Step 3 — `setup` (new-workspace seeding, runs from the main checkout), `run` (the Run button / `auto_run_after_setup`), and `archive` (teardown when a workspace is archived). All three resolve from `$CONDUCTOR_ROOT_PATH/.conductor/` so they share one copy across worktrees. There is **no `general` override** — `general` is the user's own preferences surface (their `CLAUDE.local.md` / Conductor's General box), which conductor-kit leaves untouched. There is also no `address_cr` key — Conductor has no native "address review" button, so address-cr is invoked in terminal mode via `/conductor-kit:address-cr` (and naturally during code review's loop), not from `settings.local.toml`.

- **File absent:** Write it exactly as above.
- **File present:** Read it first, then merge idempotently — set/replace only these eight keys (`prompts.code_review`, `prompts.create_pr`, `prompts.fix_errors`, `prompts.resolve_merge_conflicts`, `prompts.rename_branch`, `scripts.setup`, `scripts.run`, `scripts.archive`) and preserve every other table, key, and comment exactly as found (e.g. an existing `prompts.general`, `run_mode`, `auto_run_after_setup`, or unknown tables stay untouched — never write or remove a `general` prompt). If the user has already pointed `scripts.run`/`scripts.archive` at their own scripts, surface that and ask before replacing — don't clobber a deliberate custom wiring. Use Edit for surgical key replacement; rewrite the whole file only when the table structure has to change.

## Step 3 — Generate the workspace scripts (`setup.sh`, `run.sh`, `archive.sh`)

Generate three scripts under `.conductor/`, one per Conductor lifecycle hook wired in Step 2. Write each verbatim with the Write tool — do **not** substitute machine paths or plugin cache paths into them; each is self-contained and resolves everything from `$CONDUCTOR_ROOT_PATH` / `$CONDUCTOR_WORKSPACE_PATH` at run time.

The same **regeneration rule applies to all three** (each template ends with the `# --- project-specific (preserved) ---` marker):

- **File absent:** write the template as-is.
- **File present:** Read it and look for the line `# --- project-specific (preserved) ---`.
  - If found: regenerate everything **above** that line from the template, and keep everything **from that line to the end of the file** byte-for-byte from the existing file (the template's own marker section is replaced by the preserved one).
  - If the marker is missing (hand-written script): show the user a diff of what would change and ask before overwriting; offer to move their existing content below the marker.

After writing, make all three executable: `chmod +x .conductor/setup.sh .conductor/run.sh .conductor/archive.sh` (use target-root-relative paths).

### setup.sh template

```bash
#!/usr/bin/env bash
# Conductor workspace setup — generated by /conductor-kit:setup.
# Runs from the new workspace directory (non-interactive shell); Conductor
# provides CONDUCTOR_ROOT_PATH (main checkout) and CONDUCTOR_WORKSPACE_PATH.
# Re-running /conductor-kit:setup regenerates everything ABOVE the
# "project-specific (preserved)" marker and never touches what is below it.
set -u

ROOT="${CONDUCTOR_ROOT_PATH:?CONDUCTOR_ROOT_PATH is required}"
WS="${CONDUCTOR_WORKSPACE_PATH:-$PWD}"

# --- 1. Seed .docs/ (Docs Root symlink to the backing store) ---
CONFIG="$ROOT/CLAUDE.local.md"
STORE=""
if [ -f "$CONFIG" ]; then
  STORE="$(sed -n '/^## docs configuration/,/^## /p' "$CONFIG" \
    | grep -m1 -o '"store"[[:space:]]*:[[:space:]]*"[^"]*"' \
    | sed -e 's/^"store"[[:space:]]*:[[:space:]]*"//' -e 's/"$//')"
fi

if [ -n "$STORE" ]; then
  mkdir -p "$WS/.docs"
  if [ ! -f "$WS/.docs/.gitignore" ]; then
    printf '*\n' > "$WS/.docs/.gitignore"
  fi
  if [ -L "$WS/.docs/vault" ]; then
    CUR="$(readlink "$WS/.docs/vault")"
    if [ "$CUR" = "$STORE" ]; then
      echo "[conductor-kit] .docs/vault already linked -> $STORE"
    else
      # Stale target — the store moved or was corrected in CLAUDE.local.md.
      # A symlink is cheap and recoverable, so re-point it (loudly) rather than
      # leaving the workspace pointing at the wrong vault.
      rm "$WS/.docs/vault"
      ln -s "$STORE" "$WS/.docs/vault"
      echo "[conductor-kit] re-pointed .docs/vault: $CUR -> $STORE"
    fi
  elif [ -e "$WS/.docs/vault" ]; then
    echo "[conductor-kit] WARNING: $WS/.docs/vault exists and is not a symlink — left untouched"
  else
    ln -s "$STORE" "$WS/.docs/vault"
    echo "[conductor-kit] linked .docs/vault -> $STORE"
  fi
else
  echo "[conductor-kit] no '## docs configuration' block in $CONFIG — skipping docs seeding (run /docs-hub:setup on the main checkout)"
fi

# --- 2. Copy CLAUDE.local.md from the main checkout if absent ---
if [ -f "$ROOT/CLAUDE.local.md" ] && [ ! -f "$WS/CLAUDE.local.md" ]; then
  cp "$ROOT/CLAUDE.local.md" "$WS/CLAUDE.local.md"
  echo "[conductor-kit] copied CLAUDE.local.md from main checkout"
fi

# --- 3. Graphify worktree seeding (after all copy steps, per graphify-kit) ---
if [ -d "$ROOT/graphify-out" ]; then
  if [ -f "$WS/scripts/graphify/worktree-setup.sh" ]; then
    bash "$WS/scripts/graphify/worktree-setup.sh" || true
  elif [ -f "$ROOT/scripts/graphify/worktree-setup.sh" ]; then
    bash "$ROOT/scripts/graphify/worktree-setup.sh" || true
  else
    echo "[conductor-kit] graphify-out exists on main but scripts/graphify/worktree-setup.sh is missing — run /graphify-kit:setup on the main checkout"
  fi
fi

# --- project-specific (preserved) ---
# Anything below this marker survives /conductor-kit:setup regeneration.
```

Notes on the template (do not copy these notes into the file):

- Every path expansion is quoted — backing stores can live under iCloud paths containing spaces.
- The `store` value is parsed from the `## docs configuration` fenced JSON with `sed`/`grep` only — no `jq` dependency. Missing config is tolerated (skip with a message), and an existing non-symlink `.docs/vault` is never overwritten.
- Graphify seeding reuses graphify-kit's committed `scripts/graphify/worktree-setup.sh` (it honors `CONDUCTOR_WORKSPACE_PATH`/`CONDUCTOR_ROOT_PATH` itself); the script is never duplicated here and no plugin cache path is referenced.
- Graphify seeding is step 3 **on purpose — it must run after every copy step**, and nothing in this script may `cp -R` the graph directory itself: a direct `cp -R graphify-out` racing the seeding script's rsync produces a nested `graphify-out/graphify-out`. The script rsyncs idempotently; never add a naive copy of the graph above the preserved marker.

### run.sh template

Write this boilerplate verbatim. The actual start command is **not** in the template — it is seeded below the marker on first creation (detection rules follow); on regeneration the below-marker content is preserved untouched.

```bash
#!/usr/bin/env bash
# Conductor run script — generated by /conductor-kit:setup.
# Runs from the workspace when you press Run (or after setup, if
# auto_run_after_setup is set). Conductor provides CONDUCTOR_WORKSPACE_PATH.
# Re-running /conductor-kit:setup regenerates everything ABOVE the
# "project-specific (preserved)" marker and never touches what is below it.
set -u

WS="${CONDUCTOR_WORKSPACE_PATH:-$PWD}"
cd "$WS" || { echo "[run] cannot cd into $WS"; exit 1; }

# --- project-specific (preserved) ---
# Your project's start command. /conductor-kit:setup seeds the line below from
# the detected stack on first creation; edit it freely — it survives regeneration.
```

**Seed the run command (first creation only — never overwrite an existing below-marker section).** Inspect the target root and append exactly one command line below the marker:

- `pnpm-lock.yaml` present → `pnpm <script>`; `yarn.lock` present → `yarn <script>`; otherwise (`package-lock.json` or a bare `package.json`) → `npm run <script>`.
- `<script>`: read `package.json` `scripts` and prefer `start`, else `dev`; for the `start` script use the package manager's shorthand (`npm start` / `yarn start` / `pnpm start`).
- A couple of common non-Node stacks may be detected too if no `package.json`: `Cargo.toml` → `cargo run`; `go.mod` → `go run .`.
- **Nothing detected → TODO fallback.** Append `echo "[run] no run command configured — edit .conductor/run.sh below the marker"` so pressing Run prints a clear instruction instead of failing silently. Tell the user in the Step 5 report that run.sh needs a command.

Keep detection shallow and fast (lockfile + `package.json` `scripts`); never guess beyond the cases above — the preserved section is the user's to refine.

### archive.sh template

Write verbatim. Stops only the processes started **from this workspace**, so archiving one workspace never disturbs another's dev servers; shared/external services (a Docker stack, a database — anything single-instance across workspaces) are deliberately left alone.

```bash
#!/usr/bin/env bash
# Conductor archive script — generated by /conductor-kit:setup.
# Stops processes started FROM THIS workspace only — matched when their argv OR
# current working directory live under CONDUCTOR_WORKSPACE_PATH — so archiving
# one workspace never touches another's. Shared/external services (a Docker
# stack, a database, anything single-instance across workspaces) are left alone;
# stop those by hand. Re-running /conductor-kit:setup regenerates everything
# ABOVE the "project-specific (preserved)" marker.
set -u

WS="${CONDUCTOR_WORKSPACE_PATH:-$PWD}"
WS_REAL="$(cd "$WS" 2>/dev/null && pwd -P || printf '%s' "$WS")"
SELF=$$

# Safety: never operate on an empty path, the filesystem root, or $HOME — a
# match against those would sweep up unrelated (or all) processes.
case "$WS_REAL" in
  "" | "/" | "$HOME")
    echo "[archive] refusing to operate on '$WS_REAL' — aborting"
    exit 0
    ;;
esac

echo "[archive] stopping processes under $WS_REAL"

# Process-name filter for the cwd-based pass (children that don't carry the
# workspace path in argv). Override by exporting PROC_RE for other stacks
# (e.g. PROC_RE='python|go|cargo').
PROC_RE="${PROC_RE:-node|yarn|npm|pnpm|nodemon}"

# Candidate PIDs: argv references the workspace path, OR (for children) the
# process cwd is under it. lsof is the portable way to read a cwd on macOS.
list_pids() {
  {
    # Trailing slash so we match paths that DESCEND into the workspace, never a
    # sibling whose name merely shares this one's prefix (foo vs foo-2).
    pgrep -f -- "$WS_REAL/" 2>/dev/null
    if command -v lsof >/dev/null 2>&1; then
      for pid in $(pgrep -f -- "$PROC_RE" 2>/dev/null); do
        cwd="$(lsof -a -p "$pid" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' | head -1)"
        case "$cwd" in
          "$WS_REAL" | "$WS_REAL"/*) printf '%s\n' "$pid" ;;
        esac
      done
    fi
  } | sort -un | grep -vxE "${SELF}|${PPID}" || true
}

PIDS="$(list_pids)"
if [ -n "$PIDS" ]; then
  echo "[archive] terminating (SIGTERM): $(printf '%s ' $PIDS)"
  for pid in $PIDS; do kill -TERM "$pid" 2>/dev/null || true; done
  # Grace period, then SIGKILL whatever ignored the TERM (recomputed — children
  # may already have exited with their parent).
  sleep 3
  STRAGGLERS="$(list_pids)"
  if [ -n "$STRAGGLERS" ]; then
    echo "[archive] force-killing (SIGKILL): $(printf '%s ' $STRAGGLERS)"
    for pid in $STRAGGLERS; do kill -KILL "$pid" 2>/dev/null || true; done
  fi
else
  echo "[archive] no workspace processes found"
fi

echo "[archive] done"

# --- project-specific (preserved) ---
# Extra teardown (always runs after the standard sweep above): stop a
# workspace-local container, remove a scratch dir, etc. Survives regeneration.
```

## Step 4 — Ensure the personal files are git-invisible

Conductor settings and the generated scripts are personal; they must never show up in `git status`.

1. From the target root run `git check-ignore -q <path>` for each of `.conductor/settings.local.toml`, `.conductor/setup.sh`, `.conductor/run.sh`, and `.conductor/archive.sh` (exit 0 = already ignored; on many machines `.conductor/` is globally gitignored, covering all of them at once).
2. For each path NOT already ignored: Read `<git-common-dir>/info/exclude` (use the `--git-common-dir` path from Step 1; create the file if missing) and append the missing path(s) — each on its own line, using Edit/Write. Never add them to the repo's committed `.gitignore`.
3. Re-run the `git check-ignore` checks to confirm, and report which mechanism covers them.

## Step 5 — Report

Summarize: target root used (main checkout vs worktree override), settings keys written vs preserved, which of `setup.sh` / `run.sh` / `archive.sh` were created fresh vs regenerated with a preserved section, the run command seeded into `run.sh` (or that it needs one — the TODO fallback fired), and the ignore mechanism. Remind the user that new Conductor workspaces will now auto-seed `.docs/vault`, `CLAUDE.local.md`, and the graphify graph, run their start command on Run, and stop their own processes on archive — and that existing workspaces can be re-seeded by running `bash "$CONDUCTOR_ROOT_PATH/.conductor/setup.sh"` manually inside them (this also re-points a `.docs/vault` symlink left pointing at a stale store).

**Existing-workspace caveat:** files seeded with a copy-if-missing guard (`CLAUDE.local.md`, and any personal config such as `.claude/settings.local.json`) are **never refreshed** in a workspace that already has them — re-running setup on the main checkout only changes what _new_ workspaces receive. So when the seeded content itself changes (e.g. a hooks block is dropped because a plugin now owns it), existing workspaces keep the stale copy until each is updated by hand; only fresh workspaces get the new version. Flag this whenever the change being made alters seeded content.
