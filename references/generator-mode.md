# Generator Mode Reference

Generator Mode delegates spec parsing to `openapi-to-skills`, which produces a set of
Markdown files optimized for agent consumption. Use this mode when:
- The spec is ≥ 500KB (too large to traverse incrementally with jaq)
- You will call many operations from the same spec (amortizes the generation cost)
- Pre-generated output already exists (fastest path — no generation needed)

---

## Prerequisites

```bash
npm install -g openapi-to-skills   # or: npx openapi-to-skills@latest
openapi-to-skills --version
```

Requires: Node.js 18+, network access to spec URL (or local path).

---

## Step 1: Check for Pre-Generated Output

Before running the generator, check if output already exists:

```bash
ls ./output/<api-name-kebab>/SKILL.md 2>/dev/null && echo "EXISTS" || echo "MISSING"
```

The output directory name is derived from the API title (kebab-case):
- "Swagger Petstore - OpenAPI 3.0" → `swagger-petstore-openapi-3-0`
- "GitHub v3 REST API" → `github-v3-rest-api`
- "Stripe API" → `stripe-api`

**If the file exists:** load it immediately and follow the Navigation Protocol below.
**If not:** proceed to Step 2.

---

## Step 2: Generate Skills from Spec

### Basic invocation

```bash
openapi-to-skills spec.yaml -o ./output
```

The tool prints the output directory path on completion:
```
Skill generated at: ./output/swagger-petstore-openapi-3-0
```

### Recommended flags

```bash
openapi-to-skills spec.yaml \
  -o ./output \
  --excludeDeprecated \
  -g auto \
  -f
```

| Flag | Effect |
|------|--------|
| `-o ./output` | Write all files to `./output/` |
| `--excludeDeprecated` | Skip deprecated operations (reduces noise) |
| `-g auto` | Auto-detect grouping (tags if available, else path prefix) |
| `-f` | Overwrite existing output without prompting |
| `-n <name>` | Override the output subdirectory name |
| `--includeTags a,b,c` | Only generate for specific tags |
| `--excludeTags x,y` | Skip specific tags |

### Generate only for relevant tags (large specs)

For very large specs, limit to needed tags:
```bash
openapi-to-skills spec.yaml -o ./output --includeTags "repos,issues" -f
```

---

## Step 3: Navigate the Generated Output

### Output directory structure

```
output/
└── <api-name-kebab>/
    ├── SKILL.md                    ← entry point (read first)
    └── references/
        ├── resources/
        │   └── <tag>.md            ← operation list per resource group
        ├── operations/
        │   └── <operationId>.md    ← full details for one operation
        ├── schemas/
        │   └── <Group>/
        │       ├── _index.md       ← schema group overview
        │       └── <SchemaName>.md ← individual schema
        └── authentication.md       ← auth schemes
```

### Navigation Protocol (4 steps)

**Step 1 — Read SKILL.md first:**
```bash
cat output/<api-name>/SKILL.md
```
SKILL.md lists the resources, base URL, and auth summary. It also tells you the
navigation path.

**Step 2 — Find the operation's resource file:**
```bash
cat output/<api-name>/references/resources/<resource-name>.md
```
The resource file is a table: METHOD | PATH | Summary | Link to operation file.

Example output (Petstore `pet` resource):
```
| GET | /pet/{petId} | Find pet by ID. | [View](../operations/getPetById.md) |
```

**Step 3 — Read the operation file:**
```bash
cat output/<api-name>/references/operations/<operationId>.md
```
The operation file contains:
- Full parameter table (name, in, type, required, description)
- Response table (status codes + descriptions)
- Success response schema link
- Security requirements

Example operation file (truncated):
```markdown
# GET /pet/{petId}
**Operation ID:** `getPetById`
## Parameters
| Name | In | Type | Required |
|------|----|------|----------|
| petId | path | integer (int64) | Yes |
## Security
- api_key
- petstore_auth: write:pets, read:pets
```

**Step 4 — Read schema file (if needed):**
```bash
cat output/<api-name>/references/schemas/<Group>/<SchemaName>.md
```
Only do this if a parameter type is `object` and you need to know its required fields.

---

## File Naming Conventions

| File type | Name derivation | Example |
|-----------|----------------|---------|
| Resource file | OpenAPI tag name (kebab) | `pet.md`, `billing-portal.md` |
| Operation file | operationId with `/` and special chars → `-` | `getPetById.md`, `issues-create.md` |
| Schema file | Schema name (exact case) | `Pet.md`, `simple-user.md` |
| Schema group dir | First component of schema name | `Pet/`, `Api/` |

**Mapping operationId → filename:**
- No special characters (pure camelCase): preserved as-is. `getPetById` → `getPetById.md`
- Contains `/` (GitHub-style): replace each `/` with `-`. `issues/create` → `issues-create.md`
- Contains other special chars: replace each with `-`.

**Finding an operation file by operationId:**
```bash
# Pure camelCase operationId:
cat output/<api-name>/references/operations/getPetById.md

# Slash-separated operationId (GitHub style):
cat output/github-v3-rest-api/references/operations/issues-create.md
cat output/github-v3-rest-api/references/operations/issues-list-for-repo.md
```

**Finding a resource file by tag:**
```bash
cat output/<api-name>/references/resources/<tag-name>.md
# e.g.
cat output/github-v3-rest-api/references/resources/issues.md
```

---

## Sample Session (Petstore)

```bash
# 1. Generate
openapi-to-skills examples/petstore/petstore.yaml -o ./output --excludeDeprecated -f

# 2. Read entry point
cat output/swagger-petstore-openapi-3-0/SKILL.md
# → shows 3 resources: pet, store, user; base URL: /api/v3

# 3. Find the pet resource
cat output/swagger-petstore-openapi-3-0/references/resources/pet.md
# → shows 8 operations including: GET /pet/{petId} → getPetById.md

# 4. Read the operation
cat output/swagger-petstore-openapi-3-0/references/operations/getPetById.md
# → petId (path, integer, required), security: api_key or petstore_auth

# 5. Build and execute (using request-builder.md rules)
curl -s -H "Accept: application/json" -H "api_key: $API_KEY" \
  "https://petstore3.swagger.io/api/v3/pet/1"
```

---

## Fallback to Interpreter Mode

Fall back to Interpreter Mode if:

1. **Generation fails:**
   ```
   Error: Spec validation failed. Run with --debug for details.
   ```
   → Spec may have structural issues. Try bundling first, or switch to Interpreter Mode directly.

2. **Spec is too large even for generation:** Some specs (>50MB) may cause timeouts.
   → Use `--includeTags` to limit scope, or run Interpreter Mode on the spec as-is.

3. **No Node.js available:** `openapi-to-skills` requires Node.js 18+.
   → Fall back to Interpreter Mode immediately.

**Fallback command:**
> "Generation failed. Switching to Interpreter Mode. Please provide the spec file path."
> → Load `references/interpreter-mode.md` and run L0 on `spec.json`.

---

## Quick Reference

```bash
# Install
npm install -g openapi-to-skills

# Generate (recommended)
openapi-to-skills spec.yaml -o ./output --excludeDeprecated -g auto -f

# Check if output exists
ls output/*/SKILL.md

# Navigate
cat output/<name>/SKILL.md                                    # Step 1
cat output/<name>/references/resources/<resource>.md          # Step 2
cat output/<name>/references/operations/<operationId>.md      # Step 3
cat output/<name>/references/schemas/<Group>/<Schema>.md      # Step 4 (if needed)
```
