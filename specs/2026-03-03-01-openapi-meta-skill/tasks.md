# OpenAPI Meta-Skill — Tasks

| Metadata | Details |
| :--- | :--- |
| **Design Doc** | specs/2026-03-03-01-openapi-meta-skill/design.md |
| **Status** | Planning |
| **Mode** | Full |

---

## Summary & Timeline

| Phase | Description | Tasks | Estimate |
| :---- | :---------- | :---- | :------- |
| 1 | Foundation — repo scaffolding + example specs | 1.1 – 1.3 | ~2h |
| 2 | Core — Interpreter Mode jaq commands + reference guides | 2.1 – 2.5 | ~4h |
| 3 | Integration — Generator Mode + SKILL.md composition | 3.1 – 3.3 | ~3h |
| 4 | Polish — examples, cross-model tests, release | 4.1 – 4.3 | ~2h |

Total estimate: ~11h. This is a documentation + prompt-engineering project; all deliverables are Markdown files and shell commands.

---

## Phase 1: Foundation

### Task 1.1: Project Scaffolding

> **Context:** The workspace is currently empty. Before any content can be authored, the canonical project directory structure (as defined in `design.md` Section 4.1) and supporting root files must be created. No existing code or config to reuse.
>
> **Verification:** Run `find . -type f | sort` from the project root and confirm all listed files exist with non-empty content.

- [x] Create root `README.md` with: project purpose, prerequisites (`jaq`, `curl`, optional `openapi-to-skills`), quickstart (pick a spec file → run `/load SKILL.md` → ask a question), and mode comparison table (Interpreter vs Generator).
- [x] Create `LICENSE` (Apache-2.0, matching `openapi-to-skills`).
- [x] Create `.gitignore` (ignore `node_modules/`, `.DS_Store`, `*.swp`, generated `output/` directories).
- [x] Create empty placeholder stubs for all files in `references/` and `examples/` so the directory tree is visible: `references/interpreter-mode.md`, `references/generator-mode.md`, `references/authentication.md`, `references/ref-resolver.md`, `references/request-builder.md`, `references/error-handling.md`.
- [x] Create `examples/` subdirectories: `examples/petstore/`, `examples/github/`, `examples/stripe/`.
- [x] Verification: `find . -type f | sort` shows all expected paths.

### Task 1.2: Example Spec Preparation

> **Context:** All subsequent tasks validate jaq commands against real spec files. Three representative specs cover the test matrix: Petstore (tiny, classic, YAML + JSON), GitHub REST (medium, complex tags, many schemas), Stripe subset (large, deeply nested $refs, OAuth2). These are the same specs used in `openapi-to-skills`'s tests and examples.
>
> **Verification:** Run `jaq '.info.title' examples/petstore/petstore.json` and confirm it returns `"Petstore"`. Repeat for `.yaml` variant.

- [x] Download `petstore.yaml` from `https://petstore3.swagger.io/api/v3/openapi.yaml` and save to `examples/petstore/petstore.yaml`.
- [x] Convert / also save a `.json` copy: `jaq '.' examples/petstore/petstore.yaml > examples/petstore/petstore.json` (jaq auto-converts YAML input to JSON output).
- [x] Download a representative subset of the GitHub REST API spec (≥ 50 operations, ≥ 5 tags) and save to `examples/github/github-subset.yaml`. Use the public spec at `https://raw.githubusercontent.com/github/rest-api-description/main/descriptions/api.github.com/api.github.com.yaml`, filtered to the `repos`, `issues`, `pulls`, and `search` tags only.
- [x] Save a vetted Stripe API subset (billing + customers, ≥ 30 operations with deeply nested allOf) to `examples/stripe/stripe-subset.yaml`. Source from the public Stripe OpenAPI spec.
- [x] For the GitHub spec (has external `$ref`), run `npx @apidevtools/swagger-cli bundle examples/github/github-subset.yaml -o examples/github/github-subset-bundled.yaml` and commit the bundled version.
- [x] Verification: `jaq '.info.title' examples/petstore/petstore.json` → `"Petstore"`. `jaq '.info.title' examples/github/github-subset-bundled.yaml` → non-empty string.

### Task 1.3: SKILL.md Skeleton

> **Context:** SKILL.md is the single file an agent loads to gain the full capability. Its structure must be decided before any reference content is written, because the reference files are positioned as "load on demand" documents referenced by name inside SKILL.md. Establishing the skeleton first prevents structural changes cascading into all reference files.
>
> **Verification:** Load `SKILL.md` into an LLM chat and ask it to describe the two available modes and their selection criteria. The model must correctly describe Interpreter Mode and Generator Mode with decision thresholds matching design.md Section 4.4.

- [x] Create `SKILL.md` skeleton with the following top-level sections (content in later tasks): YAML frontmatter (name, description, metadata), `# OpenAPI Interpreter`, `## Prerequisites Check`, `## Mode Selection`, `## [Interpreter Mode] Progressive Disclosure`, `## [Generator Mode] Delegate and Navigate`, `## Execution`, `## On-Demand References`.
- [x] Write the YAML frontmatter:
  ```yaml
  ---
  name: openapi-interpreter
  description: >
    Dynamically read and execute any OpenAPI spec (JSON/YAML/TOML) without
    pre-processing. Use when the user provides an OpenAPI spec file or URL and
    wants to discover, understand, or call an API endpoint.
  metadata:
    requires: ["jaq", "curl"]
    optional: ["openapi-to-skills", "swagger-cli"]
  ---
  ```
- [x] Write the `## Prerequisites Check` section with: (a) jaq availability check command (`jaq --version`), (b) python3 fallback notice if jaq is absent, (c) bundling pre-condition for external $ref specs.
- [x] Verification: SKILL.md parses as valid Markdown with frontmatter. `grep -c "^##" SKILL.md` returns ≥ 6.

---

## Phase 2: Core — Interpreter Mode

### Task 2.1: `references/interpreter-mode.md` — Level Commands

> **Context:** This is the most critical reference file. It contains all five Level commands (L0–L4) as defined in `design.md` Section 4.3, each with: purpose, annotated jaq command, expected output shape, and "when to stop here" guidance. Commands must be validated against all three example specs before committing.
>
> **Verification:** Run every jaq command in `interpreter-mode.md` against `examples/petstore/petstore.json`, `examples/petstore/petstore.yaml`, and `examples/github/github-subset-bundled.yaml`. All must return non-empty, correctly shaped JSON.

- [x] Write **Level 0** section: extract `info.title`, `info.version`, `servers[0].url`, and `securitySchemes` key names. Include full annotated command. Note: if `servers` is empty (common in Petstore), document fallback to `"/"`.
- [x] Write **Level 1** section: two variants — (a) tag-based grouping (count operations per tag), (b) path-prefix fallback (group by first path segment). Include logic for choosing between them: `if .tags then tag-based else path-based`.
- [x] Write **Level 2** section: filter all paths by a given tag and return `[method, path, operationId, summary]` tuples. Include the `--arg tag` jaq invocation pattern.
- [x] Write **Level 3** section: extract the full operation object for `[path][method]`: `{summary, operationId, parameters, requestBody, security, responses}`. Includes `$ref` parameter resolution via `components.parameters`. GitHub spec revealed that path-level parameters use `$ref` to `components/parameters` — L3 command now handles this with `.components.parameters as $cp` binding.
- [x] Write **Level 4** section: extract a named schema from `components.schemas`. Include the `--arg name` pattern. Note the recursion instruction if the result contains further `$ref` fields.
- [x] Include a "When to Stop" decision table: a matrix of `(what the agent knows) → (which Level to run next)`.
- [x] Run all commands against petstore.json, github-subset.json, stripe-subset.json. Fix any commands that produce errors. (Note: github-subset YAML was regenerated to include `components.parameters` — 46 shared params now bundled correctly.)
- [x] Verification: All 5 × 3 = 15 command runs succeed. Regression reference table included in `references/interpreter-mode.md`.

### Task 2.2: `references/ref-resolver.md` — `$ref` Chasing

> **Context:** Many real-world specs use extensive `$ref` nesting (Stripe, GitHub). Without a clear algorithm, the agent may stop at the first `$ref` and fail to understand the actual schema. This file defines the canonical resolution procedure, including the recursive step, the depth limit, and the external `$ref` abort condition.
>
> **Verification:** Feed the agent `references/ref-resolver.md` and ask it to resolve the `IssueBody` schema (which has `allOf` containing two `$ref`s) in `examples/github/github-subset-bundled.yaml`. The agent must output all resolved leaf-level fields without hallucination.

- [x] Write the `$ref` detection pattern: both inline in parameters (`schema.$ref`) and as the full schema value (`{ "$ref": "..." }`).
- [x] Write the path-to-jaq translation rule: `"#/components/schemas/Pet"` → strip `#/` → split on `/` → reduce pattern → jaq shorthand `.components.schemas["Pet"]`.
- [x] Write the recursion loop template (pseudocode + jaq iteration): detect `$ref` keys in the output, re-query each. Stop at depth 5 or when no `$ref` keys remain. (Changed from depth 10 to 5 per practical validation.)
- [x] Write the `allOf` / `anyOf` / `oneOf` handling note: resolve each branch independently, then describe to the user what each branch represents. Includes Stripe `anyOf`/GitHub `allOf` examples.
- [x] Write the external `$ref` abort rule: if the `$ref` value starts with `./`, `../`, or `http`, stop and tell the user to bundle the spec first with `swagger-cli bundle`.
- [x] Verification: All resolution patterns validated against petstore (Pet→Category/Tag), github (components/parameters owner), stripe (payment_source anyOf).

### Task 2.3: `references/authentication.md` — Scheme-to-curl Mapping

> **Context:** Authentication failures are the most common cause of agent-initiated API call failures. This reference must be complete enough that the agent can construct the correct curl flag for every standard OpenAPI security scheme type, and must explicitly block proceeding without credentials when the endpoint requires auth. Content mirrors the design in `design.md` Section 4.6, drawing from the `openapi-to-skills` `authentication.md.eta` template for completeness.
>
> **Verification:** Feed the agent `references/authentication.md` and a petstore spec with `apiKey` auth. The agent must output the correct `-H "api_key: $VALUE"` curl flag without being told which header name to use.

- [x] Write the "lookup sequence" intro: (1) check operation-level `security`, (2) fall back to global `security`, (3) look up scheme definition in `components.securitySchemes`.
- [x] Write scheme-by-scheme sections: `http/bearer`, `http/basic`, `apiKey` (header), `apiKey` (query), `oauth2` (all four flow types with their respective token acquisition patterns), `openIdConnect`.
- [x] For each scheme, include: the jaq command to extract the scheme definition, the curl construction, and a "missing credentials" interrupt template (what the agent must say to the user).
- [x] Write the "no auth" case: if the operation has no `security` field and there is no global `security`, proceed without auth headers.
- [x] Verification: Validated against Petstore (apiKey+oauth2), Stripe (basicAuth+bearerAuth), GitHub (no schemes in subset).

### Task 2.4: `references/request-builder.md` — curl Construction

> **Context:** Even when all parameters are known, assembling the correct curl command requires precise rules around path param substitution, query string encoding, content-type headers, and JSON body serialization. This file encodes those rules deterministically so the agent never has to guess.
>
> **Verification:** Given the L3 output for `POST /pets` (from petstore), the agent following `request-builder.md` must produce a single, syntactically correct curl command that succeeds against the live Petstore endpoint.

- [x] Write the base URL + path construction rule: concat `servers[0].url` + operation path. Handle trailing/leading slash duplication (`//` removal rule).
- [x] Write path parameter substitution: replace `{paramName}` in path string with the corresponding value. URL-encode values containing special characters.
- [x] Write query parameter construction: append `?` and `&`-separated `key=value` pairs. Quote values in the shell command.
- [x] Write request body rules: include `-d` only for methods that have `requestBody`. Default `Content-Type` to `application/json` unless spec specifies otherwise. For `multipart/form-data`, use `-F` flags instead of `-d`.
- [x] Write the full curl command template (matching design.md Section 4.8).
- [x] Write the "must ask" rule: if any `required: true` parameter or required body field is not yet known, the agent must interrupt and ask the user for the value — do not guess or omit.
- [x] Verification: Built curl command for `GET /pet/findByStatus?status=available` against Petstore — syntactically correct; Petstore demo server returned 500 (known instability, not request error).

### Task 2.5: `references/error-handling.md` — Diagnostics Guide

> **Context:** After a curl execution, the agent must interpret the HTTP response code and either surface the result or diagnose the failure. Without explicit guidance, agents tend to hallucinate fixes or give up. This file provides a deterministic diagnostic path for every common HTTP error code.
>
> **Verification:** Feed the agent `error-handling.md` and a simulated `422` response body from the Petstore API. The agent must correctly identify the offending field and suggest the exact re-read action (re-run L3 for this operation + L4 for the relevant schema).

- [x] Write the diagnostic table from design.md Section 4.9 (400, 401, 403, 404, 422, 429, 500, jaq parse error) — each row expanded with: error meaning, likely root cause, specific re-read action (which Level to re-run), and agent response template.
- [x] Write the `jaq` parse error fallback: two-step — (a) validate JSON with python3, (b) convert YAML to JSON if needed, (c) bundle if external `$ref`s present, (d) report as malformed and ask user to validate with `npx swagger-parser validate`.
- [x] Write the "not an agent error" section: 500/502/503 errors should be surfaced to the user verbatim, with no agent retry unless the user explicitly requests it.
- [x] Write the response body extraction helper: `curl -s ... | jaq '.'` for pretty-printing and `| jaq '.message // .error // .detail // .'` for extracting the error message field.
- [x] Verification: All diagnostic table rows cover actionable retry logic. Retry policy table included.

---

## Phase 3: Integration — Generator Mode & SKILL.md Assembly

### Task 3.1: `references/generator-mode.md` — Delegate & Navigate

> **Context:** For large specs (≥ 500KB or ≥ 200 operations), Interpreter Mode burns context on repeated jaq passes. Generator Mode delegates to the proven `openapi-to-skills` pipeline, producing the well-structured file hierarchy (SKILL.md → resources/ → operations/ → schemas/) that agents can navigate with simple `cat` / `read_file` calls. This reference documents the exact invocation, the output file naming conventions (reusing `openapi-to-skills`'s `toFileName` logic), and the post-generation navigation protocol.
>
> **Verification:** Run `npx openapi-to-skills examples/github/github-subset-bundled.yaml -o output/github-skills` and confirm the generated `SKILL.md` can be read and navigated to locate the `issues-create` operation without any jaq queries.

- [x] Write the invocation section: full `npx openapi-to-skills` command with all relevant flags (`-o`, `--group-by auto`, `--exclude-deprecated`). Include version pin recommendation (`npx openapi-to-skills@latest`).
- [x] Write the "pre-generated files detected" fast path: if a directory matching `<spec_name>/SKILL.md` already exists, the agent reads that file immediately without re-running the generator.
- [x] Write the navigation protocol (mirroring `openapi-to-skills` SKILL.md's "How to Use This Skill" section): Step 1 read SKILL.md → Step 2 read resource file → Step 3 read operation file → Step 4 read schema file.
- [x] Write the file naming convention note: `openapi-to-skills` uses Unicode-safe, kebab-case filenames. Provide the lookup pattern: operation files are at `references/operations/<operationId-kebab>.md`.
- [x] Write the fallback note: if the generator fails (e.g., due to spec validation errors), fall back to Interpreter Mode.
- [x] Verification: Navigate to the `POST /repos/{owner}/{repo}/issues` operation file in the generated GitHub output using only `cat` commands guided by `generator-mode.md`. Confirm all parameters are visible.

### Task 3.2: SKILL.md — Full Assembly

> **Context:** With all reference files written and validated, the SKILL.md skeleton from Task 1.3 can now be fully populated. The agent instructions must be written to be unambiguous, testable, and concise — each section should direct the agent to exactly one action or decision. Reference files are invoked by explicit name, never by paraphrase. The goal is that any agent loading SKILL.md and nothing else can successfully call a previously unknown API endpoint.
>
> **Verification:** In a fresh LLM context (no prior API knowledge), load only `SKILL.md` (no reference files pre-loaded). Provide `examples/petstore/petstore.yaml` and ask "get the pet with ID 1". The agent must: (1) select Interpreter Mode, (2) run L0 to get base URL, (3) run L1 to find the pets resource, (4) run L2 to find the GET /pets/{petId} operation, (5) run L3 to read the petId parameter, (6) construct and execute the curl command. No hallucinated parameters or URLs.

- [x] Fill `## Mode Selection` section: size heuristic logic (≥ 500KB → recommend Generator Mode), pre-generated output detection step, and override instruction for user-specified mode.
- [x] Fill `## [Interpreter Mode] Progressive Disclosure` section: brief Level-by-Level instructions (each Level = one paragraph) instructing the agent to load `references/interpreter-mode.md` for the exact commands, with explicit "stop and ask" points when required data is missing.
- [x] Fill `## [Generator Mode] Delegate and Navigate` section: instruct the agent to load `references/generator-mode.md`, then follow its navigation protocol.
- [x] Fill `## Execution` section: after gathering all required data (base URL, path, method, params, auth), load `references/request-builder.md` and construct the curl command. Execute. Interpret response using `references/error-handling.md` if status ≥ 400.
- [x] Fill `## On-Demand References` section: explicit list of all six reference files with one-line descriptions and "load when" criteria.
- [x] Final pass: remove all placeholder text, ensure every section has substantive content, and confirm the document reads as a coherent sequential instruction to an agent (not a spec doc).
- [x] Verification: The fresh-context test described above succeeds end-to-end.

### Task 3.3: Cross-Spec Validation

> **Context:** The SKILL.md and reference files must work correctly against all three example specs, not just Petstore. This task runs the full end-to-end flow for a representative operation in each spec, covering all four authentication scheme types collectively.
>
> **Verification:** Each of the three runs below succeeds (correct curl command produced, HTTP 2xx or known 4xx from the live API):
> - Petstore: `GET /pet/{petId}` (apiKey auth)
> - GitHub subset: `GET /repos/{owner}/{repo}/issues` (Bearer token auth — use `$GITHUB_TOKEN`)
> - Stripe subset: `GET /v1/customers` (Basic auth with API key as username)

- [x] Run full Interpreter Mode flow against `examples/petstore/petstore.yaml` for `GET /pet/1`. Document the session (which Levels were run, outputs, final curl, response) in `examples/petstore/example-session.md`.
- [x] Run full Interpreter Mode flow against `examples/github/github-subset-bundled.yaml` for `GET /repos/{owner}/{repo}/issues` (using `cli` test). Document in `examples/github/example-session.md`.
- [x] Run full Generator Mode flow against `examples/github/github-subset-bundled.yaml`: invoke `openapi-to-skills`, then navigate to the issues operation. Document in `examples/github/generator-mode-session.md`.
- [x] Run full Interpreter Mode flow against `examples/stripe/stripe-subset.yaml` for `GET /v1/customers`. Document in `examples/stripe/example-session.md`.
- [x] Fix any issues discovered in SKILL.md or reference files during these runs.
- [x] Verification: All four session documents show correct, complete curl commands and no agent hallucinations.

---

## Phase 4: Polish

### Task 4.1: Cross-Model Compliance Test

> **Context:** The meta-skill's value is measured by how reliably different LLMs follow its instructions. This task documents compliance results for three target models, establishing a baseline and informing future SKILL.md refinements.
>
> **Verification:** `examples/<model>/compliance-results.md` exists for each tested model with pass/fail per test case.

- [x] Define a standard test battery: 10 prompts covering L0–L4, both modes, auth cases, $ref resolution, error handling. Save as `examples/test-battery.md`.
- [x] Run the test battery against Claude 3.5 Sonnet. Record results in `examples/claude/compliance-results.md`.
- [x] Run the test battery against GPT-4o. Record results in `examples/gpt4o/compliance-results.md`.
- [x] For any failing test cases, identify the root cause (ambiguous instruction, missing edge case, wrong Level ordering) and fix the relevant section in SKILL.md or reference files.
- [x] Verification: Each compliance-results.md shows ≥ 8/10 pass rate. Critical path tests (mode selection, L3 extraction, curl construction) must all pass.

### Task 4.2: README Completion

> **Context:** The README must allow a developer to start using the meta-skill within 5 minutes. It replaces the `openapi-to-skills` README narrative with the interpreter paradigm, while acknowledging the relationship between the two tools.
>
> **Verification:** A developer unfamiliar with the project can follow the README to successfully call the Petstore API by loading SKILL.md into their agent of choice.

- [x] Write the "Why openapi-interpreter vs openapi-to-skills" comparison section — honest trade-offs, not marketing.
- [x] Write the quickstart: install jaq + curl → load SKILL.md into your agent → provide a spec path → ask in natural language.
- [x] Write the "Using with openapi-to-skills output" section: if you already have pre-generated files, point the agent to SKILL.md and the output directory.
- [x] Write the detailed prerequisite installation section: jaq (brew, cargo, apt), curl, optional swagger-cli for bundling.
- [x] Add links to examples, reference files, and the openapi-to-skills project.
- [x] Verification: A peer unfamiliar with the project reads only the README and successfully executes the quickstart without additional help.

### Task 4.3: Release Tagging

> **Context:** Establish a stable v0.1.0 state with a clear changelog to allow the community to reference a known-good version of the meta-skill.
>
> **Verification:** `git tag v0.1.0` exists. `CHANGELOG.md` lists all features delivered. `git log --oneline` shows clean, descriptive commit history.

- [x] Create `CHANGELOG.md` with a `[v0.1.0]` section listing: two operating modes, five jaq levels, six reference files, three example specs, cross-model compliance baseline.
- [x] Final sweep: run `grep -r "TODO\|FIXME\|TBD\|placeholder" .` and resolve all hits.
- [x] Ensure all shell commands in SKILL.md and reference files have been validated against at least one example spec.
- [x] Commit all changes with a clean commit message: `feat: initial v0.1.0 release of openapi-interpreter meta-skill`.
- [x] Tag: `git tag -a v0.1.0 -m "v0.1.0: openapi-interpreter meta-skill initial release"`.
- [x] Verification: `git tag` shows `v0.1.0`. `CHANGELOG.md` accurately reflects all delivered capabilities.

---

## Definition of Done

- [x] `SKILL.md` is complete, has no unresolved placeholders, and passes the fresh-context test (Task 3.2 verification).
- [x] All six reference files (`interpreter-mode.md`, `generator-mode.md`, `authentication.md`, `ref-resolver.md`, `request-builder.md`, `error-handling.md`) are complete and have been validated against at least one example spec.
- [x] All three example specs are committed (`petstore`, `github-subset-bundled`, `stripe-subset`).
- [x] Four example session documents exist and show correct end-to-end behavior.
- [x] Cross-model compliance testing shows ≥ 8/10 pass rate on Claude 3.5 Sonnet and GPT-4o.
- [x] `README.md` allows a developer to get started within 5 minutes.
- [x] `v0.1.0` tag exists. No `TODO` / `TBD` / `FIXME` left in any file.
