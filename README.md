# openapi-interpreter

A meta-skill that teaches any AI agent to navigate and execute **any OpenAPI spec on demand** — no pre-processing, no code generation, no special integrations.

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](./LICENSE)

---

## Why openapi-interpreter?

| Approach | Tokens consumed | Setup required | Works with any agent framework |
| :--- | :--- | :--- | :--- |
| Paste full spec into prompt | 10k–100k+ | None | ✅ |
| `openapi-to-skills` (pre-generated files) | ~200–500 per query | `npx openapi-to-skills` offline | ✅ |
| **openapi-interpreter (this project)** | **~100–500 per query** | **None (jaq + curl only)** | **✅** |
| MCP server per API | ~50–200 per call | Build + deploy a sidecar | ❌ Framework-specific |

**openapi-interpreter** finds the sweet spot: zero setup overhead like the raw-paste approach, low context consumption like `openapi-to-skills`, and no framework lock-in like MCP.

### Honest trade-offs

| | openapi-interpreter | openapi-to-skills |
| :--- | :--- | :--- |
| Setup | Install `jaq` + `curl` | Run `npx openapi-to-skills` first |
| Spec discovery | Real-time via `jaq` | Pre-built file tree |
| Large specs (≥ 500KB) | Slower (multiple jaq passes) | Fast (pre-indexed files) |
| Spec changes | Instant (reads the live file) | Re-run the generator |
| Best for | Exploration, prototyping, CI | High-volume, large stable APIs |

Both modes are supported: `openapi-interpreter` can delegate to `openapi-to-skills` output for large specs — you get the best of both.

---

## Prerequisites

### Required

- **`jaq`** — A fast, Rust-native `jq`-compatible JSON processor.

  ```bash
  # macOS
  brew install jaq

  # Rust (all platforms)
  cargo install jaq

  # Linux (apt)
  # Download from https://github.com/01mf02/jaq/releases
  ```

  **YAML specs:** `jaq` processes JSON only. The SKILL.md skill automatically converts YAML to JSON using `python3` (available on all platforms) before running any `jaq` commands.

- **`curl`** — Pre-installed on macOS and most Linux distros. Verify: `curl --version`.

### Optional

- **`openapi-to-skills`** — Required only for Generator Mode (large specs).

  ```bash
  npm install -g openapi-to-skills
  # or use without installing:
  npx openapi-to-skills@latest
  ```

- **`@apidevtools/swagger-cli`** — Required only if your spec contains external `$ref` references pointing to other files.

  ```bash
  npx @apidevtools/swagger-cli bundle ./api-with-refs.yaml -o ./bundled.yaml
  ```

---

## Quickstart (5 minutes)

1. **Install jaq** (see Prerequisites above).

2. **Load `SKILL.md` into your agent.**
   In Claude Code, Cursor, or any agent that supports loading context files:
   ```
   /load SKILL.md
   ```
   Or paste the contents of `SKILL.md` as a system/context message.

3. **Provide a spec file and ask a question in natural language:**
   ```
   I have examples/petstore/petstore.yaml — get the pet with ID 5.
   ```

4. The agent will:
   - Run `jaq` commands to progressively discover the endpoint
   - Construct a `curl` command
   - Execute it and return the formatted result

That's it. No code to write, no files to generate.

---

## Using with openapi-to-skills output

If you have already run `openapi-to-skills` on a spec, point the agent to the generated directory:

```
I have the openapi-to-skills output for GitHub in ./github-skills/. 
Find the endpoint to create a GitHub issue and call it.
```

The agent (via `SKILL.md`'s Generator Mode) will navigate the pre-built file tree directly — no `jaq` needed.

---

## Project Structure

```
openapi-interpreter/
├── SKILL.md                       ← Load this into your agent
├── README.md                      ← This file
├── LICENSE                        ← Apache-2.0
├── references/
│   ├── interpreter-mode.md        ← jaq Level 0–4 commands (Interpreter Mode)
│   ├── generator-mode.md          ← openapi-to-skills invocation + navigation
│   ├── authentication.md          ← curl auth header construction per scheme
│   ├── ref-resolver.md            ← $ref resolution algorithm
│   ├── request-builder.md         ← curl command construction rules
│   └── error-handling.md          ← HTTP error diagnosis + recovery
└── examples/
    ├── petstore/                  ← Classic Petstore spec (JSON + YAML)
    ├── github/                    ← GitHub REST API subset
    └── stripe/                    ← Stripe API subset
```

---

## How it works

`SKILL.md` encodes a **Progressive Disclosure** strategy with five levels:

| Level | What it finds | Analogous to |
| :---- | :------------ | :----------- |
| L0 | API title, base URL, auth schemes | `openapi-to-skills` SKILL.md header |
| L1 | Resource groups (tags or path prefixes) | `references/resources/` index |
| L2 | Operations in a resource | `references/resources/<tag>.md` |
| L3 | Full operation detail (params, body, security) | `references/operations/<op>.md` |
| L4 | Schema definition | `references/schemas/<prefix>/<schema>.md` |

The agent runs exactly the levels it needs for the task — never more.

---

## Examples

Fully documented session transcripts showing the agent navigating each spec from scratch:

| Example | Mode | Spec | Operation |
| :--- | :--- | :--- | :--- |
| [Petstore session](examples/petstore/example-session.md) | Interpreter | 39KB YAML | `GET /pet/{petId}` |
| [GitHub Interpreter session](examples/github/example-session.md) | Interpreter | 1.7MB JSON | `GET /repos/{owner}/{repo}/issues` |
| [GitHub Generator session](examples/github/generator-mode-session.md) | Generator | 1.7MB YAML | `POST /repos/{owner}/{repo}/issues` |
| [Stripe session](examples/stripe/example-session.md) | Interpreter | 210KB YAML | `GET /v1/customers` |

Cross-model compliance test results: [Claude Sonnet 4.6](examples/claude/compliance-results.md) (10/10), [GPT-4o](examples/gpt4o/compliance-results.md) (pending).

---

## Related

- [openapi-to-skills](https://github.com/neutree-ai/openapi-to-skills) — The static file generator that openapi-interpreter's Generator Mode delegates to.
- [agentskills.io](https://agentskills.io) — The Agent Skills format specification.

---

## License

Apache-2.0 — see [LICENSE](./LICENSE).
