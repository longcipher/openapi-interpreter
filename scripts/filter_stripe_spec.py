#!/usr/bin/env python3
"""Download and filter the Stripe OpenAPI spec to customers/billing tags."""
import json, yaml, os, sys, urllib.request

# Stripe has no tags — filter by path prefix instead
TARGET_PREFIXES = ("/v1/customers", "/v1/billing_portal", "/v1/invoices", "/v1/subscriptions")
URL = "https://raw.githubusercontent.com/stripe/openapi/master/openapi/spec3.json"

print("Downloading Stripe spec...", flush=True)
try:
    with urllib.request.urlopen(URL, timeout=120) as resp:
        data = json.load(resp)
    print(f"Downloaded OK: {data['info']['title']}", flush=True)
except Exception as e:
    print(f"Download failed: {e}", flush=True)
    sys.exit(1)

def collect_refs(obj, refs):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "$ref" and isinstance(v, str):
                refs.add(v)
            else:
                collect_refs(v, refs)
    elif isinstance(obj, list):
        for item in obj:
            collect_refs(item, refs)

filtered_paths = {}
used_schemas = set()

for path, path_item in data.get("paths", {}).items():
    if not any(path.startswith(prefix) for prefix in TARGET_PREFIXES):
        continue
    keep_ops = {}
    for method, op in path_item.items():
        if method in ("get", "post", "put", "patch", "delete"):
            keep_ops[method] = op
            collect_refs(op, used_schemas)
    if keep_ops:
        fp = {}
        if "parameters" in path_item:
            fp["parameters"] = path_item["parameters"]
        fp.update(keep_ops)
        filtered_paths[path] = fp

total_ops = sum(
    len([m for m in v if m in ("get", "post", "put", "patch", "delete")])
    for v in filtered_paths.values()
)
print(f"Filtered paths: {len(filtered_paths)}, operations: {total_ops}", flush=True)

components = data.get("components", {})
all_schemas = components.get("schemas", {})
schema_refs = {r.split("/")[-1] for r in used_schemas if r.startswith("#/components/schemas/")}
expanded = set()

def expand_schemas(names):
    new_refs = set()
    for name in names:
        if name in all_schemas and name not in expanded:
            expanded.add(name)
            collect_refs(all_schemas[name], new_refs)
    more = {r.split("/")[-1] for r in new_refs if r.startswith("#/components/schemas/")}
    return more - expanded

to_expand = schema_refs.copy()
while to_expand:
    to_expand = expand_schemas(to_expand)

print(f"Referenced schemas: {len(expanded)}", flush=True)

# Check for allOf/anyOf/oneOf (should be present in Stripe spec)
allof_count = sum(
    1 for s in all_schemas.values()
    if isinstance(s, dict) and ("allOf" in s or "anyOf" in s or "oneOf" in s)
)
print(f"allOf/anyOf/oneOf schemas in full spec: {allof_count}", flush=True)

filtered = {
    "openapi": data["openapi"],
    "info": data["info"],
    "servers": data.get("servers", [{"url": "https://api.stripe.com"}]),
    "paths": filtered_paths,
    "components": {
        "schemas": {k: all_schemas[k] for k in expanded if k in all_schemas},
        "securitySchemes": components.get("securitySchemes", {}),
    }
}

out = "examples/stripe/stripe-subset.yaml"
with open(out, "w") as f:
    yaml.dump(filtered, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
print(f"Saved {out} ({os.path.getsize(out):,} bytes)", flush=True)
