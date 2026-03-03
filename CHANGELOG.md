# Changelog

All notable changes to `openapi-interpreter` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] — 2025-09-10

### Added

#### Core Skill

- **`SKILL.md`** — The entry-point meta-skill file that agents load to gain full OpenAPI interpreter capabilities. Includes:
  - YAML frontmatter (`name: openapi-interpreter`, `requires: [jaq, curl]`, `optional: [openapi-to-skills, swagger-cli]`)
  - Two operating modes: Interpreter Mode (real-time `jaq` traversal) and Generator Mode (delegate to `openapi-to-skills`)
  - Mode selection heuristic: automatically recommends Generator Mode for specs ≥ 500KB
  - Pre-generated output fast-path detection
  - On-demand reference loading table (6 reference files, lazy-loaded)

#### Interpreter Mode (Reference Files)

- **`references/interpreter-mode.md`** — Five progressive disclosure levels (L0–L4):
  - L0: API metadata (title, base URL, auth schemes)
  - L1: Resource index (tag-based or path-prefix grouping)
  - L2: Operations in a resource (filtered by tag, with operationId + summary)
  - L3: Full operation detail (parameters with `$ref` resolution, security, responses)
  - L4: Schema definition extraction
  - Decision table, common patterns, regression reference for all 3 example specs

- **`references/ref-resolver.md`** — `$ref` chasing algorithm:
  - Internal `$ref` detection and path-to-jaq translation
  - Recursive resolution template (depth limit: 5)
  - `allOf` / `anyOf` / `oneOf` handling (GitHub allOf + Stripe anyOf examples)
  - External `$ref` abort condition → prompt user to bundle

- **`references/authentication.md`** — Scheme-to-curl mapping:
  - All 6 OpenAPI security scheme types: `apiKey/header`, `apiKey/query`, `http/bearer`, `http/basic`, `oauth2` (4 flows), `openIdConnect`
  - Lookup sequence: operation → global → scheme definition
  - Missing-credentials interrupt template

- **`references/request-builder.md`** — curl construction rules:
  - 7-step procedure: base URL → path param substitution → query string → headers → request body → full template → must-ask interrupts
  - URL-encoding rules, `multipart/form-data` handling
  - Complete examples for Petstore, GitHub, Stripe

- **`references/error-handling.md`** — Diagnostic guide:
  - Status code table: 2xx, 400, 401, 403, 404, 405, 409, 422, 429, 500, 502, 503
  - `jaq` parse error fallback sequence (validate JSON → convert YAML → bundle → swagger-parser validate)
  - Retry policy table
  - "Not an agent error" section for 500/502/503

#### Generator Mode (Reference File)

- **`references/generator-mode.md`** — `openapi-to-skills` delegation and navigation:
  - Pre-generated file fast-path detection
  - Full CLI invocation with recommended flags (`--excludeDeprecated`, `--groupBy auto`, `--force`)
  - Output directory naming convention (API title → kebab-case slug)
  - 4-step navigation protocol: SKILL.md → resource file → operation file → schema file
  - File naming conventions: camelCase preserved for Petstore-style operationIds; `/` → `-` for GitHub-style
  - Fallback to Interpreter Mode on generation failure

#### Example Specs

- **`examples/petstore/`** — Swagger Petstore (39KB, 19 ops, 3 tags, apiKey + OAuth2 auth)
  - `petstore.yaml`, `petstore.json`
  - `example-session.md` — Full Interpreter Mode session: `GET /pet/{petId}`

- **`examples/github/`** — GitHub v3 REST API subset (1.7MB, 286 ops, 4 tags, 46 shared `components.parameters`)
  - `github-subset.yaml`, `github-subset.json`, `github-subset-bundled.yaml`
  - `example-session.md` — Interpreter Mode session: `GET /repos/{owner}/{repo}/issues`
  - `generator-mode-session.md` — Generator Mode session: `POST /repos/{owner}/{repo}/issues`

- **`examples/stripe/`** — Stripe API subset (210KB, 79 ops, path-prefix grouped, basicAuth + bearerAuth, deep anyOf nesting)
  - `stripe-subset.yaml`, `stripe-subset.json`
  - `example-session.md` — Interpreter Mode session: `GET /v1/customers`

#### Testing + Compliance

- **`examples/test-battery.md`** — 10-case standard test battery covering L0–L4, both modes, auth, `$ref` resolution, error handling
- **`examples/claude/compliance-results.md`** — Claude Sonnet 4.6 compliance: 10/10 (100% pass rate)
- **`examples/gpt4o/compliance-results.md`** — GPT-4o compliance: pending

### Technical Notes

- `jaq` 2.3.0 used for all validation (JSON-only; YAML specs converted with `python3 -c "import yaml, json..."`)
- `openapi-to-skills` v0.2.3 used for Generator Mode validation
- GitHub spec required special handling: path-level parameters use `$ref` to `components/parameters`. L3 command binds `.components.parameters as $cp` and resolves inline.
- All shell commands validated against at least one of the three example specs.

---

[0.1.0]: https://github.com/longcipher/openapi-interpreter/releases/tag/v0.1.0
