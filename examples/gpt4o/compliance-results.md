# Compliance Results — GPT-4o

Test Battery: `examples/test-battery.md`
Date: PENDING
Model: gpt-4o
Tester: PENDING — external test run required

---

## Status

This compliance test has not yet been run against GPT-4o. To run it:

1. Open ChatGPT or the OpenAI API with the `gpt-4o` model
2. Start a fresh context (no system prompt)
3. Upload or paste the contents of `SKILL.md`
4. Run each prompt from `examples/test-battery.md`
5. Record pass/fail below

---

## Results Placeholder

| Test | Description | Result | Notes |
|------|-------------|--------|-------|
| T1 | Mode selection — small spec | — | |
| T2 | Mode selection — large spec | — | |
| T3 | L0 metadata extraction | — | |
| T4 | L1 resource discovery | — | |
| T5 | L2 operation discovery | — | |
| T6 | L3 with $ref resolution | — | |
| T7 | apiKey header auth | — | |
| T8 | HTTP basic auth | — | |
| T9 | Error handling HTTP 401 | — | |
| T10 | End-to-end Petstore flow | — | |

**Score: —/10**

---

## Expected Known Issues

From prior experience with GPT-4o on tool-use tasks:
- T6 ($ref resolution): GPT-4o sometimes shows raw `$ref` strings rather than resolving them. If this occurs, add a disambiguation note to L3 section of `interpreter-mode.md`.
- T7 (apiKey header): GPT-4o may default to `Authorization: Bearer` instead of reading the `name` field from the scheme definition. If this occurs, add an explicit example to `authentication.md`.
