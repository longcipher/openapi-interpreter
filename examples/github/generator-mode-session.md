# Example Session — GitHub: Generator Mode

Spec: `examples/github/github-subset.yaml`
Goal: Locate the `POST /repos/{owner}/{repo}/issues` operation using Generator Mode.
Mode: Generator Mode (spec is 1.7MB — too large for Interpreter Mode)

---

## Step 1: Check for Pre-Generated Output

```bash
$ ls github-v3-rest-api/SKILL.md 2>/dev/null && echo "EXISTS" || echo "MISSING"
MISSING
```

No pre-generated output. Run the generator.

---

## Step 2: Generate Skills

```bash
$ openapi-to-skills examples/github/github-subset.yaml \
  -o output/github \
  --excludeDeprecated \
  -g auto \
  -f
```

Output:
```
Skill generated at: output/github/github-v3-rest-api
```

Generated 200+ operation files. Output directory: `output/github/github-v3-rest-api/`.

---

## Step 3: Read Entry Point

```bash
$ cat output/github/github-v3-rest-api/SKILL.md
```

Output (abbreviated):
```markdown
---
name: GitHub v3 REST API
...
---

## How to Use This Skill
1. Find your resource in the list below
2. Read references/resources/<resource>.md for operations
3. Read references/operations/<operationId>.md for details
4. Read references/schemas/<Group>/<Schema>.md if needed

## Resources
- **issues** → references/resources/issues.md (51 ops)
- **pulls**  → references/resources/pulls.md (27 ops)
- **repos**  → references/resources/repos.md (201 ops)
- **search** → references/resources/search.md (7 ops)
```

**Identified resource:** `issues`.

---

## Step 4: Read Resource File

```bash
$ cat output/github/github-v3-rest-api/references/resources/issues.md | grep -A2 "Create an issue"
```

Output (relevant row):
```
| POST | /repos/{owner}/{repo}/issues | Create an issue | [View](../operations/issues-create.md) |
```

**Identified operation file:** `references/operations/issues-create.md`.

---

## Step 5: Read Operation File

```bash
$ cat output/github/github-v3-rest-api/references/operations/issues-create.md
```

Output (abbreviated):
```markdown
# POST /repos/{owner}/{repo}/issues

**Operation ID:** `issues/create`
**Create an issue**

## Parameters
| Name  | In   | Type   | Required |
|-------|------|--------|----------|
| owner | path | string | Yes      |
| repo  | path | string | Yes      |

## Request Body
**Required:** Yes
**Content Types:** `application/json`

| Field   | Type   | Required | Description |
|---------|--------|----------|-------------|
| title   | string | Yes      | Issue title |
| body    | string | No       | Issue body  |
| labels  | array  | No       | Labels      |

## Responses
| Status | Description |
|--------|-------------|
| 201    | Created     |
| 403    | Forbidden   |
| 404    | Not Found   |
| 410    | Gone        |
| 422    | Validation Failed |

## Security
- token (Bearer): write:issues
```

All parameters visible without any jaq queries.

---

## Step 6: curl Construction

```bash
curl -s -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/cli/cli/issues" \
  -d '{"title": "Test issue", "body": "Created via openapi-interpreter"}'
```

---

## Summary

| Step | Action | jaq queries |
|------|--------|------------|
| 1 | Check pre-generated | 0 |
| 2 | Generate (one-time) | 0 |
| 3 | Read SKILL.md | 0 (cat) |
| 4 | Read resource file | 0 (cat + grep) |
| 5 | Read operation file | 0 (cat) |
| curl | Execute | 0 |

**Total jaq queries: 0** (vs. 4 for Interpreter Mode). Generator Mode amortizes the generation cost across all operations in the spec.
