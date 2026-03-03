# $ref Resolver Reference

OpenAPI specs use `$ref` extensively to reuse definitions. This file gives you a
deterministic procedure for resolving any `$ref` pointer using `jaq`, without needing
a bundling tool for internal references.

---

## Anatomy of a `$ref`

A `$ref` is a JSON Pointer prefixed with `#/`.

```
"$ref": "#/components/schemas/Pet"
          │   └─ path segments separated by "/"
          └─ "#/" means "start at the root of this document"
```

**Internal `$ref`** (starts with `#/`) — resolve directly with jaq.
**External `$ref`** (starts with `http`, `./`, or `../`) — cannot resolve inline;
bundle the spec first (see [Bundle First](#bundle-first-for-external-refs)).

---

## Canonical Resolution Command

Given any internal `$ref` string, resolve it to the pointed-to value:

```bash
jaq --arg ref "#/components/schemas/Pet" \
  '($ref | ltrimstr("#/") | split("/")) as $path |
   reduce $path[] as $seg (.; .[$seg])' spec.json
```

**How it works:**
1. `ltrimstr("#/")` strips the leading `#/` → `"components/schemas/Pet"`
2. `split("/")` creates path segments → `["components","schemas","Pet"]`
3. `reduce .[] as $seg (.; .[$seg])` walks the spec object segment by segment

This pattern works for **any** `$ref` target — schemas, parameters, responses, etc.

### Shorthand for schema resolution

When you know the target is always a schema:
```bash
jaq --arg name "Pet" '.components.schemas[$name]' spec.json
```

### Shorthand for parameter resolution

When the `$ref` points to a shared path/operation parameter:
```bash
jaq --arg name "owner" '.components.parameters[$name]' spec.json
```

---

## Detecting `$ref` Pointers in Any Output

After running an L3 or L4 command, check whether the output contains further `$ref` fields:

```bash
jaq '[.. | strings | select(startswith("#/"))] | unique' <(jaq '...' spec.json)
```

Or in a single pipeline — detect `$ref`s inside a named schema:
```bash
jaq --arg name "SCHEMA_NAME" \
  '[.components.schemas[$name] | .. | strings | select(startswith("#/"))] | unique' spec.json
```

**Example — Petstore `Pet` schema:**
```bash
jaq --arg name "Pet" '[.components.schemas[$name] | .. | strings | select(startswith("#/"))] | unique' examples/petstore/petstore.json
```
Output:
```json
["#/components/schemas/Category", "#/components/schemas/Tag"]
```

This tells you to run L4 twice more (for `Category` and `Tag`) if you need the full shape.

---

## Iterative `$ref` Resolution

For deeply nested schemas, follow this algorithm:

1. Run L4 to get the schema body.
2. Scan output for `$ref` strings (command above).
3. For each unresolved `$ref`: extract the last segment → run the shorthand resolution.
4. Repeat until no `$ref` strings remain **or** you have enough information to build the call.
5. Stop at **depth 5** to prevent infinite loops in circular schemas.

> **Depth limit:** Most API bodies rarely need more than 2 levels of expansion.
> If you hit depth 5 without resolving all refs, describe the unresolved ones by name
> and continue with the information you have.

---

## `allOf` — Required + Optional Composition

`allOf` means the schema is the **intersection** of all listed branches (all must apply).
Think of it as "extends" in object-oriented terms.

**Detect:**
```bash
jaq --arg name "SCHEMA" '.components.schemas[$name] | has("allOf")' spec.json
```

**Expand branches:**
```bash
jaq --arg name "SCHEMA" \
  '.components.schemas[$name].allOf | map({"$ref": ."$ref", type: .type, keys: (.properties // {} | keys)})' spec.json
```

**Example — GitHub `ruleset-version-with-state`:**
```json
[
  {"$ref": "#/components/schemas/ruleset-version", "type": null, "keys": []},
  {"$ref": null, "type": null, "keys": ["state"]}
]
```
→ This schema has the fields from `ruleset-version` **plus** a `state` field defined inline.
→ Resolve `ruleset-version` with L4 to get its fields, then add `state`.

**Merge properties from all `allOf` branches (flat view):**
```bash
jaq --arg name "SCHEMA" \
  '.components.schemas[$name] | [.allOf[] | .properties // {}] | add // {}' spec.json
```

---

## `anyOf` — Union Type (pick one)

`anyOf` means the value may match **any one** of the listed branches.
Think of it as a tagged union / discriminated union.

**Detect:**
```bash
jaq --arg name "SCHEMA" '.components.schemas[$name] | has("anyOf")' spec.json
```

**List branches:**
```bash
jaq --arg name "SCHEMA" \
  '.components.schemas[$name].anyOf | map({"$ref": ."$ref", type: .type})' spec.json
```

**Example — Stripe `payment_source`:**
```json
[
  {"$ref": "#/components/schemas/account", "type": null},
  {"$ref": "#/components/schemas/alipay_account", "type": null},
  {"$ref": "#/components/schemas/bank_account", "type": null},
  {"$ref": "#/components/schemas/card", "type": null}
]
```
→ A `payment_source` can be an `account`, `alipay_account`, `bank_account`, or `card`.
→ Ask the user which type they intend and resolve only the relevant branch.

---

## `oneOf` — Exclusive Union (exactly one)

Same lookup pattern as `anyOf`:
```bash
jaq --arg name "SCHEMA" \
  '.components.schemas[$name].oneOf | map({"$ref": ."$ref", type: .type})' spec.json
```

Semantically, `oneOf` means exactly one branch must match (vs. `anyOf`'s "at least one").
In practice, use the same strategy: identify which branch applies and resolve it.

---

## `components.parameters` vs `components.schemas`

The `components` section can contain both `parameters` and `schemas`.
Operations use `$ref` to **either**:

- `components/schemas/...` — for request/response body shapes
- `components/parameters/...` — for shared path, query, or header params

The L3 command in `interpreter-mode.md` already resolves `components.parameters` refs.
But if you encounter a `$ref` pointing to `components/parameters` in another context,
use this command:
```bash
jaq --arg name "PARAM_NAME" '.components.parameters[$name]' spec.json
```

**Example — GitHub `owner` parameter:**
```bash
jaq --arg name "owner" '.components.parameters[$name]' examples/github/github-subset.json
```
Output:
```json
{
  "name": "owner",
  "description": "The account owner of the repository. The name is not case sensitive.",
  "in": "path",
  "required": true,
  "schema": {"type": "string"}
}
```

---

## Bundle First for External `$ref`s

If the spec contains external references (URLs or relative file paths), `jaq` cannot
resolve them — they point to files or URLs not in the spec document.

**Detect external refs:**
```bash
jaq '[.. | strings | select(startswith("http") or startswith("./") or startswith("../"))] | unique | .[0:10]' spec.json
```

If this returns `$ref`-like strings (i.e., not just docs links), bundle first:
```bash
npx @apidevtools/swagger-cli bundle spec.yaml -o spec-bundled.yaml
# Then convert to JSON
python3 -c "import yaml,json; json.dump(yaml.safe_load(open('spec-bundled.yaml')), open('spec-bundled.json','w'), indent=2)"
```

> **Note:** The Petstore external URLs (`https://swagger.io/...`) are in `info.license`
> and `externalDocs` fields — these are documentation links, not `$ref` pointers.
> Only strings that appear as values of `"$ref"` keys require resolution.

---

## Quick Reference

| Situation | Command |
|-----------|---------|
| Resolve any internal `$ref` string | `($ref \| ltrimstr("#/") \| split("/")) as $p \| reduce $p[] as $s (.; .[$s])` |
| Look up a schema by name | `jaq --arg name "NAME" '.components.schemas[$name]' spec.json` |
| Look up a parameter by name | `jaq --arg name "NAME" '.components.parameters[$name]' spec.json` |
| Find all `$ref`s in a schema | `[.components.schemas[$name] \| .. \| strings \| select(startswith("#/"))] \| unique` |
| Check if schema uses `allOf` | `.components.schemas[$name] \| has("allOf")` |
| Expand `allOf` branches | `.components.schemas[$name].allOf \| map({"$ref": ."$ref", keys: (.properties // {} \| keys)})` |
| Expand `anyOf`/`oneOf` branches | same pattern with `.anyOf` or `.oneOf` |
| Detect external refs | `[.. \| strings \| select(startswith("http") or startswith("./"))] \| unique` |
