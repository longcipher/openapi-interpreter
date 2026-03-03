# Example Session — Petstore: GET /pet/{petId}

Spec: `examples/petstore/petstore.yaml`
Goal: Retrieve the pet with ID 1 from the Petstore API.
Mode: Interpreter Mode

---

## Step 1: Prerequisites

```bash
$ jaq --version
jaq 2.3.0

$ curl --version
curl 8.9.1 (x86_64-apple-darwin23.0)
```

Spec is YAML — convert to JSON first:

```bash
python3 -c "import yaml, json, sys; json.dump(yaml.safe_load(open('examples/petstore/petstore.yaml')), sys.stdout, indent=2)" > examples/petstore/petstore.json
```

---

## Step 2: Mode Selection

```bash
$ ls -lh examples/petstore/petstore.json
-rw-r--r--  1 user  staff  39K  petstore.json
```

39KB — under 500KB threshold. Proceed with Interpreter Mode.

No pre-generated output detected (`ls petstore/SKILL.md` → not found).

---

## Step 3: Level 0 — API Metadata

```bash
$ jaq '{title: .info.title, version: .info.version, server: (.servers[0].url // "/"), auth_schemes: (.components.securitySchemes // {} | keys)}' examples/petstore/petstore.json
```

Output:
```json
{
  "title": "Swagger Petstore - OpenAPI 3.0",
  "version": "1.0.27",
  "server": "/api/v3",
  "auth_schemes": [
    "api_key",
    "petstore_auth"
  ]
}
```

**Recorded:** BASE_URL = `https://petstore3.swagger.io/api/v3` (absolute URL from known server host; `/api/v3` is relative — inferred from spec description), AUTH_SCHEMES = `[api_key, petstore_auth]`.

Auth schemes present → load `references/authentication.md`.

---

## Step 4: Level 1 — Resource Index

```bash
$ jaq -r '[.paths | to_entries[] | .value | to_entries[] | select(.value | type == "object") | select(.value.tags?) | .value.tags[0]] | group_by(.) | map({tag: .[0], count: length}) | .[]' examples/petstore/petstore.json
```

Output:
```json
{"tag": "pet", "count": 8}
{"tag": "store", "count": 4}
{"tag": "user", "count": 7}
```

**Selected:** `pet` (8 operations) — matches user intent "get a pet".

---

## Step 5: Level 2 — Operations in `pet` Resource

```bash
$ jaq -r --arg tag "pet" '[.paths | to_entries[] | .key as $path | .value | to_entries[] | select(.value | type == "object") | select(.value.tags[]? == $tag) | {method: .key, path: $path, operationId: .value.operationId, summary: .value.summary}] | .[]' examples/petstore/petstore.json
```

Output (abbreviated):
```json
{"method": "get", "path": "/pet/findByStatus", "operationId": "findPetsByStatus", "summary": "Finds Pets by status."}
{"method": "get", "path": "/pet/{petId}",       "operationId": "getPetById",       "summary": "Find pet by ID."}
{"method": "post","path": "/pet/{petId}",       "operationId": "updatePetWithForm","summary": "Updates a pet in the store with form data."}
{"method": "delete","path": "/pet/{petId}",    "operationId": "deletePet",        "summary": "Deletes a pet."}
...
```

**Selected:** `GET /pet/{petId}` → operationId `getPetById`.

---

## Step 6: Level 3 — Operation Detail

```bash
$ jaq --arg path "/pet/{petId}" --arg method "get" \
  '.components.parameters as $cp | .paths[$path][$method] as $op | {
    summary: $op.summary,
    operationId: $op.operationId,
    parameters: [($op.parameters // [])[] |
      if has("$ref") then $cp[."$ref" | split("/")[-1]] else . end |
      {name: .name, in: .in, required: (.required // false), type: (.schema.type // "string")}],
    security: ($op.security // []),
    responses: ($op.responses | to_entries | map({status: .key, description: .value.description}))
  }' examples/petstore/petstore.json
```

Output:
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

**Recorded:** 1 required path param: `petId` (integer). Auth: `api_key` (single key OR petstore_auth OAuth2 — api_key is simpler).

petId value: `1` (provided by user). API key: `$API_KEY` (from environment).

---

## Step 7: curl Construction (following request-builder.md)

1. Base URL + path: `https://petstore3.swagger.io/api/v3` + `/pet/{petId}` → substitute `{petId}` → `/api/v3/pet/1`
2. Method: GET → no `-d` flag
3. Auth: `api_key` is an apiKey header scheme → `-H "api_key: $API_KEY"`
4. Accept: application/json → `-H "Accept: application/json"`

**Final command:**
```bash
curl -s -H "Accept: application/json" -H "api_key: $API_KEY" \
  "https://petstore3.swagger.io/api/v3/pet/1"
```

---

## Step 8: Execution

```bash
$ curl -s -H "Accept: application/json" -H "api_key: $API_KEY" \
  "https://petstore3.swagger.io/api/v3/pet/1"
```

Response: HTTP 500 — the Petstore demo server (`petstore3.swagger.io`) has known intermittent instability. Per `references/error-handling.md` Section "Not an Agent Error": surface the error verbatim and report to the user:

> "The Petstore demo server returned HTTP 500 (server error). The curl command is correct — this is a known instability of the public demo server. You can retry, or test with a different pet ID (e.g., try IDs 2–10)."

Alternative endpoint that often works:
```bash
curl -s -H "Accept: application/json" \
  "https://petstore3.swagger.io/api/v3/pet/findByStatus?status=available" | jaq '.[0]'
```

---

## Summary

| Step | Action | Output |
|------|--------|--------|
| L0 | Extract metadata | BASE_URL=/api/v3, auth=[api_key, petstore_auth] |
| L1 | List resources | pet(8), store(4), user(7) |
| L2 | List pet ops | GET /pet/{petId} → getPetById |
| L3 | Get op detail | petId: path, integer, required; security: api_key |
| curl | Execute | HTTP 500 (demo server instability) |
