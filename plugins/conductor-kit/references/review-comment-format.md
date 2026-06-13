# Ephemeral Review Store — comment block format

The contract for `.context/reviews/<branch>.md`: the file **code-review** writes when
`mcp__conductor__DiffComment` is unavailable, and one of the sources **address-cr** reads back.
Both playbooks cite this file; neither should diverge from the shape below.

`<branch>` is the current branch name with slashes replaced by `-` (so `feature/x` → `feature-x.md`),
to keep the path a single filesystem segment.

## File shape

The file is plain Markdown. A short header, then one `## Comment` section per finding.
Findings are appended; a re-review may rewrite the whole file from the current diff.

```markdown
# Code review — <branch>

Source: <conductor-diffcomment | terminal | github-pr>
Reviewed: <ISO-8601 date>
Diff base: <merge-base ref or describe how the diff was taken>

## Comment

File: path/to/file.ext
Lines: <start>-<end>        # a single line is written as "Lines: 42-42"
Comment ID: <id>           # present only when sourced from GitHub
Thread ID: <id>            # present only when sourced from GitHub
Remote URL: <url>          # present only when sourced from GitHub

<body — one paragraph, plain text, matter-of-fact. A ```suggestion fenced block MAY
follow when there is a concrete replacement, preserving exact leading whitespace.>

## Comment

File: path/to/other.ext
Lines: 10-10

<body>
```

## Field rules

- **File** — repo-relative path of the file the comment is anchored to. Required.
- **Lines** — `<start>-<end>` line range in the new (post-change) file. A single line uses the same
  number on both sides. Required.
- **Comment ID / Thread ID / Remote URL** — identifiers carried only when the comment came from a
  GitHub PR review (so address-cr can reply to / resolve the thread). Omit the lines entirely when
  unknown — do not write empty placeholders.
- **Body** — everything after the blank line up to the next `## Comment` (or end of file). One
  paragraph of plain prose; no markdown headers inside a body. An optional trailing ```suggestion
  block is allowed for concrete replacements.

## Why this shape

The `File:` / `Lines:` / body trio is the minimum a reviewer needs to act, and it is forward-compatible
with a typical CR comment block (which adds `Comment ID:` / `Thread ID:` / `Remote URL:` identifiers
when the comment originates from a forge). address-cr normalizes whatever it finds — args, attachments,
GitHub reviews, or this file — into exactly these fields before driving its edit loop, so a user's own
review-addressing skill that consumes such a block can be discovered and handed the same structure.
