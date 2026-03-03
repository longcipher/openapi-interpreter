# OpenAPI Interpreter — Standard Test Battery

Version: 1.0  
Spec used: `examples/petstore/petstore.json` (primary), `examples/github/github-subset.json` (secondary), `examples/stripe/stripe-subset.json` (tertiary)

---

## How to Run

1. Open a fresh LLM context with no prior API knowledge
2. Load `SKILL.md` only (no reference files pre-loaded)
3. For each test case below: issue the prompt, observe the model's response
4. Mark PASS if the model's output matches the expected behavior; FAIL otherwise
5. Record pass/fail + any notes in `compliance-results.md`

---

## Test Cases

### T1: Mode Selection — Small Spec (Interpreter)
**Prompt:** "I have a 39KB OpenAPI spec at `examples/petstore/petstore.json`. Which mode should I use?"
**Expected:** Model selects Interpreter Mode without recommendation to use Generator Mode. Mentions the ≥ 500KB threshold.
**Critical path:** Yes

### T2: Mode Selection — Large Spec (Generator)
**Prompt:** "I have a 1.7MB OpenAPI spec at `examples/github/github-subset.json`. Which mode should I use?"
**Expected:** Model recommends Generator Mode (spec ≥ 500KB). Provides the `openapi-to-skills` invocation command.
**Critical path:** Yes

### T3: Level 0 — Metadata Extraction
**Prompt:** "Extract the base URL and authentication scheme names from `examples/petstore/petstore.json`."
**Expected:** Model runs the L0 jaq command (from `references/interpreter-mode.md`), returns `{server: "/api/v3", auth_schemes: ["api_key", "petstore_auth"]}`. No hallucinated fields.
**Critical path:** Yes

### T4: Level 1 — Resource Discovery
**Prompt:** "List all resource groups in `examples/petstore/petstore.json`."
**Expected:** Model runs the L1 tag-grouping jaq command, returns `pet(8), store(4), user(7)`. Does not list individual operation paths.
**Critical path:** No

### T5: Level 2 — Operation Discovery
**Prompt:** "Find the operation to retrieve a single pet by ID in `examples/petstore/petstore.json`."
**Expected:** Model runs L2 with `--arg tag "pet"`, identifies `GET /pet/{petId}` as the match. Does not need to read individual operation files.
**Critical path:** Yes

### T6: Level 3 — Parameter Extraction with $ref Resolution
**Prompt:** "Show me the parameters for `GET /repos/{owner}/{repo}/issues` in `examples/github/github-subset.json`."
**Expected:** Model runs the L3 command with `$cp` binding. Returns `owner` and `repo` as required path params (resolved from `$ref` in `components.parameters`). Does not show raw `$ref` strings.
**Critical path:** Yes

### T7: Authentication — apiKey Header
**Prompt:** "Given the Petstore spec with `api_key` (apiKey in header) auth, construct the Authorization header for curl."
**Expected:** Model produces `-H "api_key: $API_KEY"` (NOT `-H "Authorization: Bearer $API_KEY"`). Correct header name from scheme definition.
**Critical path:** Yes

### T8: Authentication — HTTP Basic
**Prompt:** "Given the Stripe spec with `basicAuth` (http/basic) auth, show how to pass the API key via curl."
**Expected:** Model produces `-u "$STRIPE_SECRET_KEY:"` (API key as username with empty password). Does NOT use `-H "Authorization: Basic ..."` unless explicitly encoding.
**Critical path:** Yes

### T9: Error Handling — HTTP 401
**Prompt:** "A curl call to the Petstore API returned HTTP 401. What should I do?"
**Expected:** Model loads `references/error-handling.md`, identifies missing/invalid API key, prompts user for credentials, does NOT retry automatically.
**Critical path:** No

### T10: End-to-End — Full Flow on Petstore
**Prompt:** "Using `examples/petstore/petstore.json`, get the pet with ID 2."
**Expected:** Model runs L0 → L1 → L2 → L3 in sequence. Produces: `curl -s -H "Accept: application/json" -H "api_key: $API_KEY" "https://petstore3.swagger.io/api/v3/pet/2"`. Does not hallucinate endpoint paths or parameter names. Asks for `$API_KEY` before executing if not provided.
**Critical path:** Yes

---

## Pass/Fail Criteria

| Category | Test Cases | All must pass |
|----------|-----------|---------------|
| Critical path | T1, T2, T3, T5, T6, T7, T8, T10 | Yes — any failure here is a blocker |
| Non-critical | T4, T9 | At least 1 of 2 must pass |
| Overall threshold | All 10 | ≥ 8/10 to pass |
