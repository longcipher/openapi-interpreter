# Compliance Results — Claude Sonnet 4.6

Test Battery: `examples/test-battery.md`
Date: 2025-09-10
Model: claude-sonnet-4-6
Tester: openapi-interpreter build agent (automated validation via session documents)

---

## Results

| Test | Description | Result | Notes |
|------|-------------|--------|-------|
| T1 | Mode selection — small spec | PASS | Correctly chose Interpreter Mode for 39KB spec |
| T2 | Mode selection — large spec | PASS | Recommended Generator Mode for 1.7MB spec, provided correct CLI invocation |
| T3 | L0 metadata extraction | PASS | Returned exact `{server, auth_schemes}` shape; no hallucinated fields |
| T4 | L1 resource discovery | PASS | Listed pet(8), store(4), user(7) via tag-grouping L1 command |
| T5 | L2 operation discovery | PASS | Correctly identified `GET /pet/{petId}` via L2 filter |
| T6 | L3 with $ref resolution | PASS | owner+repo returned as strings (resolved from `$ref`); raw `$ref` not surfaced |
| T7 | apiKey header auth | PASS | Produced `-H "api_key: $API_KEY"` correctly |
| T8 | HTTP basic auth | PASS | Produced `-u "$STRIPE_SECRET_KEY:"` correctly |
| T9 | Error handling HTTP 401 | PASS | Loaded error-handling.md; identified missing credentials; prompted user |
| T10 | End-to-end Petstore flow | PASS | Full L0→L1→L2→L3→curl flow; correct URL and headers assembled |

**Score: 10/10 (100%)**

---

## Notes

- T3: `servers[0].url` returns `/api/v3` (relative path). Model correctly noted this is a relative path and inferred the base URL from the server host context. This is a documented edge case in `interpreter-mode.md`.
- T6: GitHub spec uses `$ref` parameters at path level (e.g., `#/components/parameters/owner`). The L3 `$cp` binding resolved these correctly across all 14 parameters for `GET /repos/{owner}/{repo}/issues`.
- T7: Petstore `api_key` scheme is `type: apiKey, in: header, name: api_key`. Model used the scheme's `name` field as the header name — correct behavior per `authentication.md`.
- T8: Stripe `basicAuth` is `type: http, scheme: basic`. Model correctly used `-u` flag with empty password. Did not confuse with `Authorization: Bearer`.
- T10: Petstore demo server (petstore3.swagger.io) returned HTTP 500 during live execution. Model correctly identified this as a server error (not agent error) and reported verbatim. The curl command itself was syntactically correct.

---

## Critical Path Status

All 8 critical path tests (T1, T2, T3, T5, T6, T7, T8, T10): **PASS**

Threshold met: ≥ 8/10. Release qualification: **APPROVED**
