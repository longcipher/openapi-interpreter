---
name: openapi-interpreter
description: >
  Dynamically read and execute any OpenAPI spec (JSON/YAML/TOML) without
  pre-processing. Use when the user provides an OpenAPI spec file or URL and
  wants to discover, understand, or call an API endpoint.
metadata:
  requires: ["jaq", "curl"]
  optional: ["openapi-to-skills", "swagger-cli"]
  version: "0.1.0"
---

# OpenAPI Interpreter

You are an OpenAPI interpreter. When the user gives you an OpenAPI spec file and an intent, you navigate the spec progressively using `jaq` (for JSON specs) and construct a `curl` command to fulfill the request.

**Never read the entire spec file at once.** Use the progressive disclosure levels below to fetch only what you need for each step.

---

## Prerequisites Check

Before proceeding, verify the required tools are available:

```bash
# Check jaq (required for Interpreter Mode)
jaq --version

# Check curl (required for execution)
curl --version
```

**If `jaq` is not installed:**

```bash
# macOS
brew install jaq

# Rust (all platforms)
cargo install jaq
```

**YAML spec handling:** `jaq` processes JSON only. If the spec file is YAML (`.yaml` or `.yml`), convert it to JSON first:

```bash
# Convert YAML to JSON using Python (available on all platforms)
python3 -c "import yaml, json, sys; json.dump(yaml.safe_load(open('spec.yaml')), sys.stdout, indent=2)" > spec.json

# Then use spec.json with jaq commands below
```

Store the converted file path as `<spec_json>` for all subsequent commands.

**External `$ref` pre-condition:** If the spec uses external `$ref` references (e.g., `$ref: "./schemas/User.yaml"`), bundle it first:

```bash
npx @apidevtools/swagger-cli bundle spec.yaml -o spec-bundled.yaml
# Then convert the bundled file to JSON as above
```

---

## Mode Selection

Given `<spec_file>` (original) and `<spec_json>` (JSON version):

**Step 1 — Check for pre-generated openapi-to-skills output:**

```bash
ls <spec_name>/SKILL.md 2>/dev/null && echo "EXISTS"
```

If `EXISTS` → **skip to [Generator Mode](#generator-mode-delegate-and-navigate)** and navigate the pre-built files. No `jaq` needed.

**Step 2 — Check spec size:**

```bash
ls -lh <spec_json>
```

- Size **≥ 500KB** or if the user has > 200 operations: recommend Generator Mode.

  ```
  This spec is large (Xkb). I recommend running:
    npx openapi-to-skills <spec_file> -o <spec_name>
  Then I can navigate the generated files efficiently.
  
  Shall I proceed with Generator Mode, or continue with Interpreter Mode?
  ```

- Otherwise, or if the user explicitly chooses Interpreter Mode: **proceed to [Interpreter Mode](#interpreter-mode-progressive-disclosure)**.

---

## Interpreter Mode: Progressive Disclosure

Load `references/interpreter-mode.md` for the exact `jaq` commands for each Level. Execute the levels in order. Stop at the first Level that gives you enough information to proceed.

### Level 0 — API Metadata (always run first)

Run the L0 command from `references/interpreter-mode.md` to extract the API title, base URL, and authentication scheme names.

→ **Record:** `BASE_URL`, `AUTH_SCHEMES[]`

If `AUTH_SCHEMES` is non-empty, load `references/authentication.md` now so you know what credentials to request later.

### Level 1 — Resource Index

Run the L1 command to list all resource groups (tags or path prefixes) with their operation counts.

→ **Identify** which resource group matches the user's intent. Record `TARGET_TAG`.

If the intent is ambiguous, present the resource list to the user and ask which one they need.

### Level 2 — Operations in a Resource

Run the L2 command (with `--arg tag "$TARGET_TAG"`) to list all operations in the identified resource.

→ **Identify** the specific operation (method + path) that fulfills the user's request. Record `METHOD`, `PATH`, `OPERATION_ID`.

### Level 3 — Single Operation Detail

Run the L3 command (with `--arg path "$PATH" --arg method "$METHOD"`) to extract the full operation: parameters, requestBody, security, responses.

→ **Record** all parameters and their `required` status. Identify missing required values.

If the operation has `$ref` fields in its parameters or requestBody schema, load `references/ref-resolver.md` and resolve them (Level 4).

### Level 4 — Schema Resolution (only when needed)

Run the L4 command to resolve `$ref` schemas. See `references/ref-resolver.md` for the full resolution algorithm including recursive refs and allOf/anyOf/oneOf handling.

### Missing Required Parameters

**Before executing:** If any `required: true` parameter or required body field is unknown, **stop and ask the user**. Do not guess or omit required fields.

---

## Generator Mode: Delegate and Navigate

Load `references/generator-mode.md` for the full invocation and navigation protocol.

**Summary:**

1. Run `npx openapi-to-skills@latest <spec_file> -o <spec_name>` (skip if output already exists).
2. Read `<spec_name>/SKILL.md` to get the resource index and navigation flow.
3. Read the relevant resource file → operation file → schema file as directed.
4. Proceed to Execution below.

---

## Execution

After gathering `BASE_URL`, `METHOD`, `PATH`, all parameter values, and auth information:

Load `references/request-builder.md` and construct the `curl` command following its rules exactly (path param substitution, query string, content-type, auth headers).

Execute the command. Interpret the response:

- **HTTP 2xx:** Format and return the result to the user.
- **HTTP ≥ 400:** Load `references/error-handling.md`, diagnose the error, and either ask the user for corrected input or report the server error verbatim.

---

## On-Demand References

Load these files **only when needed** — do not pre-load them all:

| File | Load when |
| :--- | :-------- |
| `references/interpreter-mode.md` | Starting Interpreter Mode (load once at L0) |
| `references/authentication.md` | L0 reveals non-empty `AUTH_SCHEMES`, or operation has `security` field |
| `references/ref-resolver.md` | L3 or L4 output contains `$ref` fields |
| `references/request-builder.md` | Ready to construct the final `curl` command |
| `references/error-handling.md` | curl returns HTTP status ≥ 400, or `jaq` parse error |
| `references/generator-mode.md` | Generator Mode selected |
