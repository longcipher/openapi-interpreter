# Request Builder Reference

This file gives you the deterministic rules for assembling a `curl` command from
the information gathered at L0–L4. Follow these steps in order.

---

## Step 1: Base URL

Extract the server base URL from L0:
```bash
jaq -r '.servers[0].url // "/"' spec.json
```

**Base URL rules:**
- Use `servers[0].url` as-is (it may include a path prefix like `/api/v3`)
- If `.servers[0].url` is `"/"`, the spec is relative — ask the user for the actual host
- Strip a trailing `/` from the base URL before concatenation

**Examples:**
```
Petstore: "/api/v3"      → relative URL, needs real host
GitHub:   "https://api.github.com"
Stripe:   "https://api.stripe.com/"  → strip trailing "/"
```

---

## Step 2: Path Parameter Substitution

Replace every `{paramName}` placeholder in the operation path with its actual value.

**Rule:** Replace literally — `{owner}` → the actual owner string.

```bash
PATH_TEMPLATE="/repos/{owner}/{repo}/issues"
OWNER="octocat"
REPO="hello-world"
PATH=$(echo "$PATH_TEMPLATE" | sed "s/{owner}/$OWNER/" | sed "s/{repo}/$REPO/")
# → /repos/octocat/hello-world/issues
```

**URL encoding:** If a path value contains `/`, `?`, `#`, `@`, or spaces, percent-encode it:
```bash
ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$VALUE', safe=''))")
```

**Combining base URL + path:**
```bash
FULL_URL="${BASE_URL}${PATH}"
# Remove accidental double slash if base URL has trailing "/" and path has leading ":
FULL_URL=$(echo "$FULL_URL" | sed 's|([^:])//|\1/|g')
```

---

## Step 3: Query Parameters

Collect all parameters with `"in": "query"` from the L3 output.

**Required query params:** must be included; ask user if value is unknown.
**Optional query params:** include only if the user specified a value.

**Construction:**
```bash
curl "https://api.example.com/path?param1=value1&param2=value2"
```

**Shell quoting rule:** always wrap the full URL in double quotes when it contains `?` or `&`.

**Multiple values for the same parameter** (array type): repeat the key:
```
?label=bug&label=enhancement
```

---

## Step 4: Request Headers

**Always include:**
```bash
-H "Accept: application/json"
```

**For request bodies (POST/PUT/PATCH):**
```bash
-H "Content-Type: application/json"
```

**For `multipart/form-data` bodies:** Use `-F` instead — curl sets `Content-Type` automatically.

**Auth headers:** from `authentication.md` lookup (run before this step).

**Spec-defined headers:** any parameters with `"in": "header"` from L3:
```bash
-H "$HEADER_NAME: $VALUE"
```

---

## Step 5: Request Body

Check for `requestBody` in the L3 output:
```bash
jaq --arg path "PATH" --arg method "METHOD" '.paths[$path][$method].requestBody // null' spec.json
```

**If non-null and `content` has `application/json`:**
```bash
-H "Content-Type: application/json" -d '{"field": "value"}'
```

**If `content` has `multipart/form-data`:**
```bash
-F "field=value" -F "file=@/path/to/file"
```

**If `content` has `application/x-www-form-urlencoded`:**
```bash
--data-urlencode "field=value"
```

**Must ask rule:** If the operation has a `requestBody` with `required: true` and you
do not have all `required` body fields, **stop and ask the user** before proceeding.
Do not guess, omit required fields, or use placeholder values.

---

## Step 6: Full curl Command Template

```bash
curl -s -X METHOD \
  -H "Accept: application/json" \
  [-H "Content-Type: application/json"] \
  [-H "Authorization: Bearer $TOKEN"] \
  [-H "$CUSTOM_HEADER: $VALUE"] \
  [-d '{"key": "value"}'] \
  "https://BASE_URL/path/{param1}/action?query1=v1&query2=v2"
```

Add `-i` to include response headers (useful for debugging):
```bash
curl -s -i -X GET ...
```

Add `-w "\nHTTP %{http_code}\n"` to show HTTP status code at the end:
```bash
curl -s -w "\nHTTP %{http_code}\n" ...
```

---

## Step 7: Must-Ask Interrupts

Before executing, verify you have values for every **required** field:

**Required path parameters:** always required (path would be malformed without them)
**Required query parameters:** `L3 output: "required": true` for `"in": "query"` params
**Required body fields:** from L4 schema's `required` array

**Interrupt template:**
> "To call `METHOD PATH`, I need the following required values:
> - `paramName` (path): [description from spec]
> - `fieldName` (body): [description from spec]
> Please provide these values."

---

## Complete Examples

### Petstore - GET /pet/1

**L0:** base URL = `/api/v3` (relative → use `https://petstore3.swagger.io/api/v3`)
**L3:** parameters: `petId` (path, required, integer), security: `api_key` or `petstore_auth`

```bash
curl -s -w "\nHTTP %{http_code}\n" \
  -H "Accept: application/json" \
  -H "api_key: $API_KEY" \
  "https://petstore3.swagger.io/api/v3/pet/1"
```

### GitHub - GET /repos/{owner}/{repo}/issues

**L0:** base URL = `https://api.github.com`
**L3:** path params: `owner`, `repo` (required); query params: `state`, `labels` (optional)

```bash
curl -s \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/octocat/hello-world/issues?state=open"
```

### Stripe - POST /v1/customers

**L0:** base URL = `https://api.stripe.com` (strip trailing `/`)
**L3:** no required body fields (all optional for customer creation)

```bash
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $STRIPE_SECRET_KEY" \
  -d '{"email": "user@example.com", "name": "Jane Doe"}' \
  "https://api.stripe.com/v1/customers"
```

---

## Quick Reference

| Parameter location | curl placement |
|-------------------|----------------|
| `in: path` | substituted in URL path |
| `in: query` | `?key=value&key2=value2` in URL |
| `in: header` | `-H "Name: Value"` |
| `in: cookie` | `-b "name=value"` |
| `requestBody (json)` | `-H "Content-Type: application/json" -d '...'` |
| `requestBody (form)` | `-F "key=value"` |
| `requestBody (urlencoded)` | `--data-urlencode "key=value"` |
