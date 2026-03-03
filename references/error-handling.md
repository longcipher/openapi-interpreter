# Error Handling Reference

This file provides a deterministic diagnostic path for every common HTTP response code
and tool-level error. After executing a `curl` command, follow this procedure.

---

## Response Handling

### Step 1: Extract body and status code

```bash
# Capture body and status code separately
RESPONSE=$(curl -s -w "\n---HTTP_STATUS---%{http_code}" ...)
BODY=$(echo "$RESPONSE" | sed '/^---HTTP_STATUS---/d')
STATUS=$(echo "$RESPONSE" | grep '^---HTTP_STATUS---' | cut -d'%' -f2 || echo "$RESPONSE" | tail -1)
```

Simpler alternative — just pipe to jaq for pretty printing:
```bash
curl -s ... | jaq '.'
```

### Step 2: Extract error message

```bash
echo "$BODY" | jaq '.message // .error // .detail // .errors // .'
```

---

## Diagnostic Table

| HTTP Code | Meaning | Likely cause | Re-read action | Agent response |
|-----------|---------|--------------|----------------|----------------|
| **2xx** | Success | — | None needed | Surface the result body to the user |
| **400 Bad Request** | Server rejected the request | Missing required field, wrong type, or malformed JSON | Re-run L3 on this operation + L4 on request body schema | "The server rejected the request. Let me re-check the required fields for this operation." |
| **401 Unauthorized** | Auth missing or invalid | Wrong token, expired token, missing auth header | Re-read authentication.md; ask user to re-provide credentials | "Authentication failed. Please verify your API credentials and provide them again." |
| **403 Forbidden** | Insufficient permissions | Missing OAuth scope, wrong API key tier, IP blocklist | Re-read L3 for `security` scopes; ask user to confirm permission level | "The server denied access. Your credentials may lack the required permissions for this operation." |
| **404 Not Found** | Resource doesn't exist | Wrong path, wrong ID, resource was deleted | Re-run L2 to verify the exact path; check path param values | "The resource was not found. Please verify the ID or path values." |
| **405 Method Not Allowed** | Wrong HTTP method | Using GET instead of POST, etc. | Re-run L2 for this path to see valid methods | "This method is not allowed. Let me check which methods are available for this endpoint." |
| **409 Conflict** | Resource state conflict | Creating a duplicate, version mismatch | Check API docs for idempotency behavior; surface error to user | "A conflict was detected. The resource may already exist or be in an incompatible state." |
| **422 Unprocessable Entity** | Validation failed | Field value out of range, enum violation, pattern mismatch | Re-run L4 on the request body schema; check `enum` and `format` constraints | "Validation failed. Let me re-examine the schema constraints for the request body." |
| **429 Too Many Requests** | Rate limited | Too many requests in a time window | Wait (check `Retry-After` header); do not retry immediately | "Rate limit reached. Please wait before retrying. Check the `Retry-After` header for the wait time." |
| **500 Internal Server Error** | Server bug | Upstream service error | Do NOT retry automatically; surface verbatim to user | "The server returned an internal error. This is not caused by the request — please try again later or contact the API provider." |
| **502 Bad Gateway** | Proxy/gateway error | Upstream service unavailable | Same as 500 | Same as 500 |
| **503 Service Unavailable** | Server overloaded or in maintenance | Temporary outage | Check `Retry-After` header; surface to user | "The service is temporarily unavailable. Please try again later." |

---

## 400 / 422 Diagnostic Detail

These are the most actionable errors. Use this drill-down:

1. Extract the error body:
   ```bash
   echo "$BODY" | jaq '.errors // .message // .'
   ```

2. Identify which field caused the error (often named in the error body).

3. Re-run L3 to check if that field is `required` and its type:
   ```bash
   jaq --arg path "PATH" --arg method "METHOD" \
     '.paths[$path][$method].requestBody.content["application/json"].schema' spec.json
   ```

4. Follow `$ref` to get the schema and check `required` array, `enum`, `format`, `minimum/maximum`:
   ```bash
   jaq --arg name "SCHEMA_NAME" \
     '.components.schemas[$name] | {required, properties: (.properties | to_entries[] | {key: .key, type: .value.type, enum: .value.enum, format: .value.format})}' spec.json
   ```

---

## 401 Diagnostic Detail

1. Re-read `authentication.md` lookup sequence.
2. Ask the user to confirm the credential type and value.
3. Check if the scheme is `apiKey` vs `http/bearer` vs `http/basic` — the header name differs.
4. Check for token expiry (JWT `exp` claim):
   ```bash
   # Decode JWT payload (base64 decode middle segment)
   echo "$TOKEN" | cut -d. -f2 | base64 -d 2>/dev/null | jaq '{exp, iat, sub}'
   ```

---

## jaq Parse Errors

If `jaq` fails on a spec file:

**Step 1:** Confirm the file is valid JSON:
```bash
python3 -c "import json; json.load(open('spec.json'))" && echo "Valid JSON" || echo "Invalid JSON"
```

**Step 2:** If YAML (because jaq needs JSON), convert:
```bash
python3 -c "import yaml,json; json.dump(yaml.safe_load(open('spec.yaml')), open('spec.json','w'), indent=2)"
```

**Step 3:** If the JSON is malformed, validate the original:
```bash
npx @apidevtools/swagger-parser validate spec.yaml
```

**Step 4:** If external `$ref`s cause jaq path failures, bundle first:
```bash
npx @apidevtools/swagger-cli bundle spec.yaml -o spec-bundled.yaml
```

---

## Pretty-Printing Response Bodies

```bash
# Pretty-print JSON response
curl -s ... | jaq '.'

# Extract just the error field
curl -s ... | jaq '.message // .error // .detail // .'

# Get nested errors array
curl -s ... | jaq '.errors[] | {field: .source.pointer, message: .detail}'

# Get HTTP status code alongside body
curl -s -o /tmp/body.json -w "%{http_code}" ... 
# → status in stdout, body in /tmp/body.json
```

---

## Retry Policy

| Code | Auto-retry? | Condition |
|------|------------|-----------|
| 429 | Yes, once | Wait `Retry-After` seconds if header present, else 60s |
| 500/502/503 | No | Surface to user; retry only if user requests |
| 504 Gateway Timeout | Yes, once | Wait 5s then retry |
| All 4xx (not 429) | No | Fix the request first |

**Never retry 4xx errors** (except 429) without modifying the request — the same request
will produce the same error.

---

## Quick Reference

```bash
# Check status code
curl -s -o /dev/null -w "%{http_code}" URL

# Full response with status (best for debugging)
curl -s -i URL

# Extract error message from body
echo "$BODY" | jaq '.message // .error // .detail // .'

# Validate JSON file
python3 -c "import json; json.load(open('spec.json'))"

# Convert YAML to JSON
python3 -c "import yaml,json; json.dump(yaml.safe_load(open('s.yaml')), open('s.json','w'), indent=2)"
```
