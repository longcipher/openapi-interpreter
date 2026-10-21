# Justfile — the openapi-interpreter meta-skill.
#
# The deliverable is Markdown: SKILL.md (the agent entry point), references/
# (six on-demand guides), examples/ (three regression specs + transcripts).
# The `test` recipe is the jaq regression suite from
# references/interpreter-mode.md.

# Default recipe to display help
default:
  @just --list

# Format the Markdown docs
format:
  rumdl fmt .

# Auto-fix what format cannot
fix:
  rumdl check --fix .

# Run all lints: Markdown and the Python helpers
lint:
  rumdl check --disable MD013,MD036 .
  python3 -c "import ast, pathlib; [ast.parse(p.read_text(encoding='utf-8'), str(p)) for p in sorted(pathlib.Path('scripts').glob('*.py'))]"

# Run the jaq regression suite
test:
  #!/usr/bin/env bash
  set -uo pipefail
  fail=0
  check() {
    if [[ "$3" == "$2" ]]; then
      printf 'ok   %s\n' "$1"
    else
      printf 'FAIL %s: expected [%s] got [%s]\n' "$1" "$2" "$3"
      fail=1
    fi
  }
  pet=examples/petstore/petstore.json
  gh=examples/github/github-subset.json
  stripe=examples/stripe/stripe-subset.json
  check "L0 petstore title" "Swagger Petstore - OpenAPI 3.0" "$(jaq -r '.info.title' "$pet")"
  check "L0 github server" "https://api.github.com" "$(jaq -r '.servers[0].url' "$gh")"
  check "L0 stripe auth_schemes[0]" "basicAuth" "$(jaq -r '.components.securitySchemes | keys[0]' "$stripe")"
  check "L1a petstore tag=pet count" "8" "$(jaq -r '[.paths | to_entries[] | .value | to_entries[] | select(.value | type == "object") | select(.value.tags?) | .value.tags[0]] | group_by(.) | map({tag: .[0], count: length}) | .[] | select(.tag == "pet") | .count' "$pet")"
  check "L1a github tag=repos count" "201" "$(jaq -r '[.paths | to_entries[] | .value | to_entries[] | select(.value | type == "object") | select(.value.tags?) | .value.tags[0]] | group_by(.) | map({tag: .[0], count: length}) | .[] | select(.tag == "repos") | .count' "$gh")"
  check "L1b stripe prefix=/v1/customers count" "25" "$(jaq -r '[.paths | keys[] | split("/")[0:3] | join("/")] | group_by(.) | map({prefix: .[0], count: length}) | .[] | select(.prefix == "/v1/customers") | .count' "$stripe")"
  check "L3 petstore operationId" "getPetById" "$(jaq -r --arg path '/pet/{petId}' --arg method 'get' '.paths[$path][$method].operationId' "$pet")"
  check "L3 github first parameter" "owner" "$(jaq -r --arg path '/repos/{owner}/{repo}/issues' --arg method 'get' '.components.parameters as $cp | .paths[$path][$method] as $op | [($op.parameters // [])[] | if has("$ref") then $cp[."$ref" | split("/")[-1]] else . end | .name][0]' "$gh")"
  check "L3 stripe operationId" "GetCustomersCustomer" "$(jaq -r --arg path '/v1/customers/{customer}' --arg method 'get' '.paths[$path][$method].operationId' "$stripe")"
  check "L4 petstore Pet.required[0]" "name" "$(jaq -r '.components.schemas["Pet"].required[0]' "$pet")"
  if [[ "$fail" -ne 0 ]]; then
    echo "error: jaq regression suite failed" >&2
    exit 1
  fi
  echo "ok: jaq regression suite passed"

# Regenerate the derived JSON spec from the YAML source
build:
  python3 scripts/finalize_specs.py

# Verify the runtime prerequisites are on PATH
prereqs:
  @command -v jaq >/dev/null || { echo "error: jaq is required" >&2; exit 1; }
  @command -v curl >/dev/null || { echo "error: curl is required" >&2; exit 1; }
  @jaq --version
  @curl --version | head -1

# Download and filter the Stripe spec into examples/stripe/
filter-stripe:
  python3 scripts/filter_stripe_spec.py

# Filter a locally downloaded full GitHub spec into examples/github/
filter-github:
  python3 scripts/filter_github_spec.py

# Fail if Chinese characters appear anywhere in the docs
check-cn:
  #!/usr/bin/env bash
  set -uo pipefail
  if rg --line-number --column "\p{Han}" SKILL.md README.md CHANGELOG.md references examples scripts specs; then
    echo "error: Chinese characters found above" >&2
    exit 1
  fi
  echo "ok: no Chinese characters found"

# Full CI check
ci: lint test

# ============================================================
# Maintenance & Tools
# ============================================================

# Remove generated caches
clean:
  rm -rf scripts/__pycache__/

# Install the tools this Justfile needs
setup:
  @command -v jaq >/dev/null 2>&1 || { echo "Installing jaq..."; brew install jaq; }
  @command -v rumdl >/dev/null 2>&1 || { echo "Installing rumdl..."; cargo install rumdl; }
  @python3 -c "import yaml" 2>/dev/null || { echo "Installing PyYAML..."; pip3 install --user pyyaml; }
