# openapi-interpreter Agent Instructions

## Non-negotiables

- Surgical edits only: every changed line must trace to the request. No drive-by refactors, no reformatting untouched code, no deleting pre-existing dead code (mention it instead).
- Fix root causes. Never silence a warning, weaken a check, or patch a symptom to make a gate pass.
- Never report completion while any `just` gate below fails. Report the failure verbatim and stop.
- Stop and ask when a request is ambiguous, conflicts with existing conventions, or requires credentials, publishing, or destructive operations.
- When a correction reveals a missing rule, add one specific rule here ("always X for Y", never "be careful with Y"); delete rules that never catch real errors.

## Scope

- `openapi-interpreter` is a meta-skill, not a service: `SKILL.md` is the file an agent loads, and it teaches the agent to navigate any OpenAPI spec on demand with `jaq` and to execute the resulting call with `curl`.
- `SKILL.md` is the contract — its frontmatter (`name`, `description`, `metadata.requires: [jaq, curl]`, `metadata.optional`, `metadata.version`) is what the Agent Skills loader reads, so treat it as an API.
- `references/` holds six on-demand guides: `interpreter-mode.md`, `generator-mode.md`, `authentication.md`, `ref-resolver.md`, `request-builder.md`, `error-handling.md`. They are lazy-loaded — never inline their content into `SKILL.md`.
- `examples/` holds the three regression specs (petstore, github subset, stripe subset) with worked session transcripts, plus `test-battery.md` and the cross-model `compliance-results.md` files.
- `scripts/` holds three one-off Python helpers that regenerate the example specs; they are not part of the skill's runtime.
- `specs/2026-03-03-01-openapi-meta-skill/` is the design record (`design.md`, `tasks.md`).
- English only in code, comments, docs, and commit messages.

## Execution

- Parallelize aggressively: dispatch subagents for independent research, exploration, and implementation.
- The three example specs are independent fixtures — validate them in parallel.
- NEVER use `git worktree`. Edit the current branch in place.
- TDD for behavior changes: add the assertion to the `just test` regression suite first, make the smallest change that passes it, then run the whole suite.

## Verification loop

After each feature or bug fix, in order; any failure means the task is not done:

```bash
just format
just lint
just test
```

`format` runs `rumdl fmt`; `lint` runs `rumdl check` and a Python syntax check of `scripts/`; `test` runs the `jaq` regression suite from the table at the end of `references/interpreter-mode.md`.

## Repository rules

- Two modes, and the mode choice is a documented heuristic: Interpreter Mode (live `jaq`) by default, Generator Mode (delegate to `npx openapi-to-skills`) once the spec is ≥ 500KB or has more than 200 operations.
- Interpreter Mode is progressive disclosure, five levels: L0 metadata → L1 resource groups → L2 operations → L3 operation detail → L4 schema. Stop at the first level that answers the question; never read a whole spec into context.
- Every `jaq` command in `references/interpreter-mode.md` carries an inline comment saying what it extracts — keep that convention when adding or editing a command.
- The regression table at the bottom of `references/interpreter-mode.md` is the executable contract: each row states a spec, a level, a key, and the expected value. `just test` executes exactly those rows.
- `jaq` reads JSON only. YAML specs must be converted first (`python3` + `yaml`), and external `$ref`s must be bundled first (`npx @apidevtools/swagger-cli bundle`).
- Authentication is per-scheme: `apiKey` in header becomes `-H "name: $KEY"`, `apiKey` in query becomes a query parameter, `http/basic` becomes `-u "$KEY:"`. Never guess a scheme — read it from `components.securitySchemes`.
- A missing required parameter or body field is a stop-and-ask, never a guess. A 4xx response is diagnosed against `references/error-handling.md` and reported verbatim, never retried blindly.
- Known drift, do not "fix" silently: `examples/petstore/README.md` still lists `l0-output.json` … `l4-output.json`, which were never committed, and the github/stripe READMEs omit the `.json` fixtures that the regression suite actually uses.

## Dependency choices

- Required at runtime: `jaq` (JSON processor) and `curl`. Optional: `openapi-to-skills` for Generator Mode and `@apidevtools/swagger-cli` for bundling external `$ref`s.
- The scripts in `scripts/` need `PyYAML`; the skill itself does not.
- `rumdl` lints the Markdown. `typos` is not wired in — the vendored Stripe spec contains upstream typos that are not ours to fix.
- No framework, no bundler, no runtime dependency on the skill: the whole point is that `SKILL.md` plus `jaq` and `curl` is enough.

## Code conventions

- Markdown is the product: ATX headings, `-` bullets, fenced blocks with a language tag.
- `jaq` filters are written in the single-line form in the reference guides so they can be pasted straight into a shell.
- Paths in the docs are repo-relative and start with `examples/` or `references/`; never hardcode an absolute path.
- `scripts/` are standalone Python 3 scripts with a shebang and a docstring — no shared module, no package, no import of each other.
- `CHANGELOG.md` follows Keep a Changelog and SemVer; add an entry under the unreleased heading for every user-visible change.
- The skill version in `SKILL.md` frontmatter and the `CHANGELOG.md` heading must move together.
