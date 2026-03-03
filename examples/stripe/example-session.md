# Example Session — Stripe: GET /v1/customers

Spec: `examples/stripe/stripe-subset.yaml`
Goal: List the first 5 customers in our Stripe account.
Mode: Interpreter Mode

---

## Step 1: Prerequisites

```bash
$ jaq --version
jaq 2.3.0
```

Spec is YAML — convert to JSON first:

```bash
python3 -c "import yaml, json, sys; json.dump(yaml.safe_load(open('examples/stripe/stripe-subset.yaml')), sys.stdout, indent=2)" > examples/stripe/stripe-subset.json
```

---

## Step 2: Mode Selection

```bash
$ ls -lh examples/stripe/stripe-subset.json
-rw-r--r--  1 user  staff  210K  stripe-subset.json
```

210KB — under 500KB threshold. Interpreter Mode viable.

---

## Step 3: Level 0 — API Metadata

```bash
$ jaq '{title: .info.title, version: .info.version, server: (.servers[0].url // "/"), auth_schemes: (.components.securitySchemes // {} | keys)}' examples/stripe/stripe-subset.json
```

Output:
```json
{
  "title": "Stripe API",
  "version": "2026-02-25.clover",
  "server": "https://api.stripe.com/",
  "auth_schemes": ["basicAuth", "bearerAuth"]
}
```

**Recorded:** BASE_URL = `https://api.stripe.com`, AUTH_SCHEMES = `[basicAuth, bearerAuth]`.

Load `references/authentication.md` — check basicAuth scheme:

```bash
$ jaq '.components.securitySchemes.basicAuth' examples/stripe/stripe-subset.json
```

Output:
```json
{
  "type": "http",
  "scheme": "basic",
  "description": "Basic HTTP authentication. Allowed headers-- Authorization: Basic <api_key>"
}
```

Basic auth with API key as username, empty password: `-u "$STRIPE_API_KEY:"`.

---

## Step 4: Level 1 — Resource Index (path-prefix, no tags)

```bash
$ jaq -r '[.paths | keys[] | split("/")[0:3] | join("/")] | group_by(.) | map({prefix: .[0], count: length}) | .[]' examples/stripe/stripe-subset.json
```

Output (abbreviated):
```json
{"prefix": "/v1/billing_portal", "count": 3}
{"prefix": "/v1/customers",      "count": 25}
{"prefix": "/v1/invoices",       "count": 4}
```

**Selected:** `/v1/customers` (25 operations) — matches user intent "list customers".

---

## Step 5: Level 2 — Operations with `/v1/customers` prefix

```bash
$ jaq -r '[.paths | to_entries[] | select(.key | startswith("/v1/customers")) | .key as $path | .value | to_entries[] | select(.value | type == "object") | {method: .key, path: $path, operationId: .value.operationId, summary: .value.summary}] | .[] | select(.path == "/v1/customers")' examples/stripe/stripe-subset.json
```

Output:
```json
{"method": "get",  "path": "/v1/customers", "operationId": "GetCustomers", "summary": "List all customers"}
{"method": "post", "path": "/v1/customers", "operationId": "PostCustomers", "summary": "Create a customer"}
```

**Selected:** `GET /v1/customers` → operationId `GetCustomers`.

---

## Step 6: Level 3 — Operation Detail

```bash
$ jaq --arg path "/v1/customers" --arg method "get" \
  '.components.parameters as $cp | .paths[$path][$method] as $op | {
    summary: $op.summary,
    operationId: $op.operationId,
    parameters: [($op.parameters // [])[] |
      if has("$ref") then $cp[."$ref" | split("/")[-1]] else . end |
      {name: .name, in: .in, required: (.required // false), type: (.schema.type // "string")}],
    security: ($op.security // []),
    responses: ($op.responses | to_entries | map({status: .key, description: .value.description}))
  }' examples/stripe/stripe-subset.json
```

Output (abbreviated parameters):
```json
{
  "summary": "List all customers",
  "operationId": "GetCustomers",
  "parameters": [
    {"name": "created",        "in": "query", "required": false, "type": "string"},
    {"name": "email",          "in": "query", "required": false, "type": "string"},
    {"name": "ending_before",  "in": "query", "required": false, "type": "string"},
    {"name": "expand",         "in": "query", "required": false, "type": "array"},
    {"name": "limit",          "in": "query", "required": false, "type": "integer"},
    {"name": "starting_after", "in": "query", "required": false, "type": "string"}
  ],
  "security": [],
  "responses": [
    {"status": "200",     "description": "Successful response."},
    {"status": "default", "description": "Error response."}
  ]
}
```

**Recorded:** No required params. All optional. Auth: none in operation — check global `security` (often `basicAuth` for Stripe). Use `$STRIPE_SECRET_KEY` with basic auth.

---

## Step 7: curl Construction

```bash
curl -s \
  -H "Accept: application/json" \
  -u "$STRIPE_SECRET_KEY:" \
  "https://api.stripe.com/v1/customers?limit=5"
```

---

## Step 8: Execution

```bash
$ curl -s -u "$STRIPE_SECRET_KEY:" "https://api.stripe.com/v1/customers?limit=5" \
  | jaq '{count: .data | length, has_more: .has_more, first_customer: .data[0].id}'
```

Sample output (with valid `$STRIPE_SECRET_KEY`):
```json
{
  "count": 5,
  "has_more": true,
  "first_customer": "cus_ABC123"
}
```

---

## Summary

| Step | Action | Output |
|------|--------|--------|
| L0 | Extract metadata | BASE_URL=https://api.stripe.com, auth=[basicAuth, bearerAuth] |
| L1 | Path-prefix grouping | /v1/customers(25), /v1/invoices(4), /v1/billing_portal(3) |
| L2 | List /v1/customers ops | GET /v1/customers → GetCustomers |
| L3 | Get op detail | All params optional; basic auth scheme |
| curl | Execute | HTTP 200, paginated customer list |
