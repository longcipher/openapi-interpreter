# Example Session — GitHub: GET /repos/{owner}/{repo}/issues

Spec: `examples/github/github-subset.json`
Goal: List open issues for the `cli/cli` GitHub repository.
Mode: Interpreter Mode

---

## Step 1: Prerequisites

```bash
$ jaq --version
jaq 2.3.0
```

Spec is already in JSON format (`github-subset.json`). No YAML conversion needed.

---

## Step 2: Mode Selection

```bash
$ ls -lh examples/github/github-subset.json
-rw-r--r--  1 user  staff  1.7M  github-subset.json
```

1.7MB — exceeds 500KB threshold. Recommend Generator Mode.

However, for this session we proceed with Interpreter Mode to demonstrate the full flow.

---

## Step 3: Level 0 — API Metadata

```bash
$ jaq '{title: .info.title, version: .info.version, server: (.servers[0].url // "/"), auth_schemes: (.components.securitySchemes // {} | keys)}' examples/github/github-subset.json
```

Output:
```json
{
  "title": "GitHub v3 REST API",
  "version": "1.1.4",
  "server": "https://api.github.com",
  "auth_schemes": []
}
```

**Recorded:** BASE_URL = `https://api.github.com`. No security schemes defined in subset.
Note: GitHub uses Bearer token auth via the global `Authorization` header even though `securitySchemes` is absent in this subset — document the token requirement when asking the user.

---

## Step 4: Level 1 — Resource Index

```bash
$ jaq -r '[.paths | to_entries[] | .value | to_entries[] | select(.value | type == "object") | select(.value.tags?) | .value.tags[0]] | group_by(.) | map({tag: .[0], count: length}) | .[]' examples/github/github-subset.json
```

Output:
```json
{"tag": "issues", "count": 51}
{"tag": "pulls",  "count": 27}
{"tag": "repos",  "count": 201}
{"tag": "search", "count": 7}
```

**Selected:** `issues` (51 operations).

---

## Step 5: Level 2 — Operations in `issues` Resource

```bash
$ jaq -r --arg tag "issues" '[.paths | to_entries[] | .key as $path | .value | to_entries[] | select(.value | type == "object") | select(.value.tags[]? == $tag) | {method: .key, path: $path, operationId: .value.operationId, summary: .value.summary}] | .[] | select(.path | contains("/repos/{owner}/{repo}/issues"))' examples/github/github-subset.json
```

Output (abbreviated to relevant operations):
```json
{"method": "get",  "path": "/repos/{owner}/{repo}/issues",          "operationId": "issues/list-for-repo",    "summary": "List repository issues"}
{"method": "post", "path": "/repos/{owner}/{repo}/issues",          "operationId": "issues/create",           "summary": "Create an issue"}
{"method": "get",  "path": "/repos/{owner}/{repo}/issues/{issue_number}", "operationId": "issues/get",        "summary": "Get an issue"}
```

**Selected:** `GET /repos/{owner}/{repo}/issues` → operationId `issues/list-for-repo`.

---

## Step 6: Level 3 — Operation Detail (with `$ref` resolution)

```bash
$ jaq --arg path "/repos/{owner}/{repo}/issues" --arg method "get" \
  '.components.parameters as $cp | .paths[$path][$method] as $op | {
    summary: $op.summary,
    operationId: $op.operationId,
    parameters: [($op.parameters // [])[] |
      if has("$ref") then $cp[."$ref" | split("/")[-1]] else . end |
      {name: .name, in: .in, required: (.required // false), type: (.schema.type // "string")}],
    security: ($op.security // []),
    responses: ($op.responses | to_entries | map({status: .key, description: .value.description}))
  }' examples/github/github-subset.json
```

Output (abbreviated parameters):
```json
{
  "summary": "List repository issues",
  "operationId": "issues/list-for-repo",
  "parameters": [
    {"name": "owner",     "in": "path",  "required": true,  "type": "string"},
    {"name": "repo",      "in": "path",  "required": true,  "type": "string"},
    {"name": "milestone", "in": "query", "required": false, "type": "string"},
    {"name": "state",     "in": "query", "required": false, "type": "string"},
    {"name": "labels",    "in": "query", "required": false, "type": "string"},
    {"name": "sort",      "in": "query", "required": false, "type": "string"},
    {"name": "direction", "in": "query", "required": false, "type": "string"},
    {"name": "since",     "in": "query", "required": false, "type": "string"},
    {"name": "per_page",  "in": "query", "required": false, "type": "integer"},
    {"name": "page",      "in": "query", "required": false, "type": "integer"}
  ],
  "security": [],
  "responses": [
    {"status": "200", "description": "Response"},
    {"status": "301", "description": null},
    {"status": "404", "description": null},
    {"status": "422", "description": null}
  ]
}
```

Note: `$ref` parameters (owner, repo) were resolved from `components.parameters` via the L3 `$cp` binding.

**Recorded:** `owner` and `repo` are required path params. Auth: none in spec — use Bearer token from `$GITHUB_TOKEN`.

Values: owner=`cli`, repo=`cli`, state=`open` (optional, set for clarity).

---

## Step 7: curl Construction

```bash
curl -s \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/cli/cli/issues?state=open&per_page=5"
```

---

## Step 8: Execution

```bash
$ curl -s \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/cli/cli/issues?state=open&per_page=5" | jaq '[.[] | {number: .number, title: .title, state: .state}]'
```

Sample output (with valid `$GITHUB_TOKEN`):
```json
[
  {"number": 10100, "title": "gh release upload should not fail...", "state": "open"},
  {"number": 10098, "title": "Support for --env-file in gh run watch", "state": "open"},
  ...
]
```

---

## Summary

| Step | Action | Output |
|------|--------|--------|
| L0 | Extract metadata | BASE_URL=https://api.github.com, no auth schemes |
| L1 | List resources | issues(51), pulls(27), repos(201), search(7) |
| L2 | List issues ops | GET /repos/{owner}/{repo}/issues → issues/list-for-repo |
| L3 | Get op detail | owner+repo: path required; 8 optional query params; $ref resolved |
| curl | Execute | HTTP 200, paginated list of issues |
