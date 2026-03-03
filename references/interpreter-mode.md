# Interpreter Mode Reference

Interpreter Mode lets you navigate any OpenAPI spec incrementally using `jaq`, without
pre-generating tool wrappers. You drill down through five levels — from spec overview to
a single operation's details — then build and execute the HTTP call directly.

---

## Prerequisites

`jaq` (version ≥ 1.0) must be available on the path and the spec must be **JSON**.

**Convert YAML to JSON first:**
```bash
python3 -c "import yaml,json; json.dump(yaml.safe_load(open('spec.yaml')), open('spec.json','w'), indent=2)"
```

All examples below assume `spec.json` is the converted file.

---

## Level Overview

| Level | Input needed | Question answered |
|-------|-------------|-------------------|
| L0 | spec file only | What API is this? What auth does it use? |
| L1 | L0 output | What groups/tags exist? How many operations each? |
| L2 | tag/prefix from L1 | What endpoints are in this group? |
| L3 | path + method from L2 | What parameters / auth / responses does this endpoint need? |
| L4 | schema name from L3 | What are the required fields in this request/response body? |

**Stop as soon as you have enough information to form the HTTP call.** You rarely need L4
except when a parameter has type `object` and the spec does not explain its shape inline.

---

## L0 — Spec Overview

**Purpose:** Identify the API, base server URL, and active authentication schemes.
Run this exactly once per spec.

```bash
jaq '{
  title: .info.title,
  version: .info.version,
  server: (.servers[0].url // "/"),
  auth_schemes: (.components.securitySchemes // {} | keys)
}' spec.json
```

Single-line form:
```bash
jaq '{title: .info.title, version: .info.version, server: (.servers[0].url // "/"), auth_schemes: (.components.securitySchemes // {} | keys)}' spec.json
```

### Sample outputs

**Petstore:**
```json
{
  "title": "Swagger Petstore - OpenAPI 3.0",
  "version": "1.0.27",
  "server": "/api/v3",
  "auth_schemes": ["api_key", "petstore_auth"]
}
```

**GitHub REST API:**
```json
{
  "title": "GitHub v3 REST API",
  "version": "1.1.4",
  "server": "https://api.github.com",
  "auth_schemes": []
}
```

**Stripe API:**
```json
{
  "title": "Stripe API",
  "version": "2026-02-25.clover",
  "server": "https://api.stripe.com/",
  "auth_schemes": ["basicAuth", "bearerAuth"]
}
```

> **Note:** `auth_schemes: []` does not mean the API is unauthenticated — the spec may rely
> on implicit auth (e.g. GitHub uses token headers not declared in components). Check the
> spec's top-level `security` field or the API's documentation.

---

## L1 — Group Discovery

**Purpose:** List all logical groups (tags or path prefixes) with operation counts so you
can narrow down to the relevant section without loading all endpoints.

### L1a — Tag-based (most specs)

Use when the spec has tags.

```bash
jaq -r '[.paths | to_entries[] | .value | to_entries[] |
  select(.value | type == "object") | select(.value.tags?) |
  .value.tags[0]] | group_by(.) | map({tag: .[0], count: length}) | .[]' spec.json
```

Single-line form:
```bash
jaq -r '[.paths | to_entries[] | .value | to_entries[] | select(.value | type == "object") | select(.value.tags?) | .value.tags[0]] | group_by(.) | map({tag: .[0], count: length}) | .[]' spec.json
```

**Detect whether spec has tags** (run before L1 if unsure):
```bash
jaq '([.paths | to_entries[] | .value | to_entries[] | select(.value | type == "object") | .value.tags? | select(.) | length] | add // 0) > 0' spec.json
```
Returns `true` → use L1a. Returns `false` → use L1b.

**Petstore sample:**
```json
{"tag": "pet",   "count": 8}
{"tag": "store", "count": 4}
{"tag": "user",  "count": 7}
```

**GitHub sample:**
```json
{"tag": "issues", "count": 51}
{"tag": "pulls",  "count": 27}
{"tag": "repos",  "count": 201}
{"tag": "search", "count": 7}
```

### L1b — Path-prefix (when spec has no tags)

Use when the spec has no tags (e.g. Stripe groups operations by URL prefix).

```bash
jaq -r '[.paths | keys[] | split("/")[0:3] | join("/")] |
  group_by(.) | map({prefix: .[0], count: length}) | .[]' spec.json
```

Single-line form:
```bash
jaq -r '[.paths | keys[] | split("/")[0:3] | join("/")] | group_by(.) | map({prefix: .[0], count: length}) | .[]' spec.json
```

**Stripe sample:**
```json
{"prefix": "/v1/billing_portal", "count": 3}
{"prefix": "/v1/customers",      "count": 25}
{"prefix": "/v1/invoices",       "count": 15}
{"prefix": "/v1/subscriptions",  "count": 6}
```

---

## L2 — Operation Listing

**Purpose:** List all operations in a specific tag or path prefix with their method, path,
operationId, and one-line summary. Use this to identify the exact operation you need.

### L2a — By tag

```bash
jaq -r --arg tag "TAG" '[.paths | to_entries[] | .key as $path |
  .value | to_entries[] | select(.value | type == "object") |
  select(.value.tags[]? == $tag) |
  {method: .key, path: $path, operationId: .value.operationId, summary: .value.summary}
] | .[]' spec.json
```

Single-line form:
```bash
jaq -r --arg tag "TAG" '[.paths | to_entries[] | .key as $path | .value | to_entries[] | select(.value | type == "object") | select(.value.tags[]? == $tag) | {method: .key, path: $path, operationId: .value.operationId, summary: .value.summary}] | .[]' spec.json
```

**Petstore `pet` tag sample:**
```json
{"method": "put",    "path": "/pet",                     "operationId": "updatePet",         "summary": "Update an existing pet."}
{"method": "post",   "path": "/pet",                     "operationId": "addPet",            "summary": "Add a new pet to the store."}
{"method": "get",    "path": "/pet/findByStatus",        "operationId": "findPetsByStatus",  "summary": "Finds Pets by status."}
{"method": "get",    "path": "/pet/findByTags",          "operationId": "findPetsByTags",    "summary": "Finds Pets by tags."}
{"method": "get",    "path": "/pet/{petId}",             "operationId": "getPetById",        "summary": "Find pet by ID."}
{"method": "post",   "path": "/pet/{petId}",             "operationId": "updatePetWithForm", "summary": "Updates a pet in the store with form data."}
{"method": "delete", "path": "/pet/{petId}",             "operationId": "deletePet",         "summary": "Deletes a pet."}
{"method": "post",   "path": "/pet/{petId}/uploadImage", "operationId": "uploadFile",        "summary": "Uploads an image."}
```

### L2b — By path prefix

```bash
jaq -r --arg prefix "/PREFIX" '[.paths | to_entries[] | select(.key | startswith($prefix)) |
  .key as $path | .value | to_entries[] | select(.value | type == "object") |
  {method: .key, path: $path, operationId: .value.operationId, summary: .value.summary}
] | .[]' spec.json
```

Single-line form:
```bash
jaq -r --arg prefix "/PREFIX" '[.paths | to_entries[] | select(.key | startswith($prefix)) | .key as $path | .value | to_entries[] | select(.value | type == "object") | {method: .key, path: $path, operationId: .value.operationId, summary: .value.summary}] | .[]' spec.json
```

---

## L3 — Operation Detail

**Purpose:** Get all parameters, security requirements, and response codes for one
specific operation. This is the core level — it gives you everything needed to build the
HTTP call.

This command handles `$ref` parameters (inline or in `components/parameters`) automatically.

```bash
jaq --arg path "PATH" --arg method "METHOD" '
  .components.parameters as $cp |
  .paths[$path][$method] as $op |
  {
    summary: $op.summary,
    operationId: $op.operationId,
    parameters: [($op.parameters // [])[] |
      if has("$ref") then $cp[."$ref" | split("/")[-1]] else . end |
      {name: .name, in: .in, required: (.required // false), type: (.schema.type // "string")}
    ],
    security: ($op.security // []),
    responses: ($op.responses | to_entries | map({status: .key, description: .value.description}))
  }
' spec.json
```

Single-line form:
```bash
jaq --arg path "PATH" --arg method "METHOD" '.components.parameters as $cp | .paths[$path][$method] as $op | {summary: $op.summary, operationId: $op.operationId, parameters: [($op.parameters // [])[] | if has("$ref") then $cp[."$ref" | split("/")[-1]] else . end | {name: .name, in: .in, required: (.required // false), type: (.schema.type // "string")}], security: ($op.security // []), responses: ($op.responses | to_entries | map({status: .key, description: .value.description}))}' spec.json
```

### Sample outputs

**Petstore `GET /pet/{petId}`:**
```json
{
  "summary": "Find pet by ID.",
  "operationId": "getPetById",
  "parameters": [
    {"name": "petId", "in": "path", "required": true, "type": "integer"}
  ],
  "security": [
    {"api_key": []},
    {"petstore_auth": ["write:pets", "read:pets"]}
  ],
  "responses": [
    {"status": "200", "description": "successful operation"},
    {"status": "400", "description": "Invalid ID supplied"},
    {"status": "404", "description": "Pet not found"}
  ]
}
```

**GitHub `GET /repos/{owner}/{repo}/issues`** (`owner`/`repo` are resolved from
`components/parameters` via the `$ref` resolution in this command):
```json
{
  "summary": "List repository issues",
  "operationId": "issues/list-for-repo",
  "parameters": [
    {"name": "owner",     "in": "path",  "required": true,  "type": "string"},
    {"name": "repo",      "in": "path",  "required": true,  "type": "string"},
    {"name": "milestone", "in": "query", "required": false, "type": "string"},
    {"name": "state",     "in": "query", "required": false, "type": "string"},
    {"name": "assignee",  "in": "query", "required": false, "type": "string"}
  ],
  "security": [],
  "responses": [
    {"status": "200", "description": "Response"},
    {"status": "301", "description": "Moved permanently"},
    {"status": "404", "description": "Resource not found"},
    {"status": "422", "description": "Validation failed, or the endpoint has been spammed."}
  ]
}
```

**Stripe `GET /v1/customers/{customer}`:**
```json
{
  "summary": "Retrieve a customer",
  "operationId": "GetCustomersCustomer",
  "parameters": [
    {"name": "customer", "in": "path",  "required": true,  "type": "string"},
    {"name": "expand",   "in": "query", "required": false, "type": "array"}
  ],
  "security": [],
  "responses": [
    {"status": "200",     "description": "Successful response."},
    {"status": "default", "description": "Error response."}
  ]
}
```

> **Checking for request body:** The `parameters` array only contains path/query/header
> params. For POST/PUT/PATCH operations, also check for a request body schema:
> ```bash
> jaq --arg path "PATH" --arg method "METHOD" '.paths[$path][$method].requestBody' spec.json
> ```
> If non-null, use L4 to explore the content schema by following its `$ref`.

---

## L4 — Schema Inspection

**Purpose:** Inspect a schema definition to understand what fields are required or
available for a request/response body. Use only when you need to know the shape of a
complex object parameter.

```bash
jaq --arg name "SCHEMA_NAME" '.components.schemas[$name]' spec.json
```

**List all schema names:**
```bash
jaq '[.components.schemas // {} | keys[]]' spec.json
```

**Petstore `Pet` schema:**
```json
{
  "required": ["name", "photoUrls"],
  "type": "object",
  "properties": {
    "id":        {"type": "integer", "format": "int64"},
    "name":      {"type": "string",  "example": "doggie"},
    "category":  {"$ref": "#/components/schemas/Category"},
    "photoUrls": {"type": "array",   "items": {"type": "string"}},
    "tags":      {"type": "array",   "items": {"$ref": "#/components/schemas/Tag"}},
    "status":    {"type": "string",  "enum": ["available", "pending", "sold"]}
  }
}
```

> **If a property contains `$ref`:** Run L4 again with the referenced schema name to
> expand it. See [ref-resolver.md](ref-resolver.md) for `allOf`/`anyOf`/`oneOf` handling
> and depth limits.

---

## Decision Table: When to Stop

| Situation | Required level | Action |
|-----------|---------------|--------|
| You know the endpoint path already | L3 only | Run L3, then build the call |
| You know the tag but not the exact path | L1 → L2 → L3 | List ops, pick one, inspect |
| You don't know what the API offers | L0 → L1 → L2 → L3 | Full drill-down |
| Body param is a primitive (string/int/bool) | L3 sufficient | Use type from L3 output |
| Body param is type `object` or has `$ref` | L3 → L4 | Expand schema |
| L3 returns `null` for the operation | — | Wrong path/method; re-run L2 |
| L3 `parameters` shows `{name: null}` entries | — | Spec has dangling `$ref` with no matching `components.parameters` entry — treat field as undocumented string |

---

## Common Patterns

### Find all paths containing a keyword
```bash
jaq -r '[.paths | keys[] | select(test("keyword"; "i"))] | .[]' spec.json
```

### List operations requiring a specific security scheme
```bash
jaq -r --arg scheme "SCHEME" '[.paths | to_entries[] | .key as $p | .value | to_entries[] | select(.value | type == "object") | select(.value.security[]?[$scheme]?) | {method: .key, path: $p}] | .[]' spec.json
```

### Count total operations
```bash
jaq '[.paths | to_entries[] | .value | to_entries[] | select(.key | test("^(get|post|put|patch|delete|head|options)$"))] | length' spec.json
```

---

## Regression Reference

These exact outputs were validated against the three example specs with `jaq` 2.3.0.
Run them to confirm compatibility.

| Spec | Level | Key | Expected value |
|------|-------|-----|----------------|
| `examples/petstore/petstore.json` | L0 | `title` | `"Swagger Petstore - OpenAPI 3.0"` |
| `examples/github/github-subset.json` | L0 | `server` | `"https://api.github.com"` |
| `examples/stripe/stripe-subset.json` | L0 | `auth_schemes[0]` | `"basicAuth"` |
| `examples/petstore/petstore.json` | L1a tag=pet | `count` | `8` |
| `examples/github/github-subset.json` | L1a tag=repos | `count` | `201` |
| `examples/stripe/stripe-subset.json` | L1b prefix=/v1/customers | `count` | `25` |
| `examples/petstore/petstore.json` | L3 GET /pet/{petId} | `operationId` | `"getPetById"` |
| `examples/github/github-subset.json` | L3 GET /repos/{owner}/{repo}/issues | first param `name` | `"owner"` (resolved from $ref) |
| `examples/stripe/stripe-subset.json` | L3 GET /v1/customers/{customer} | `operationId` | `"GetCustomersCustomer"` |
| `examples/petstore/petstore.json` | L4 schema=Pet | `required[0]` | `"name"` |
