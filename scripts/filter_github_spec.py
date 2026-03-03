#!/usr/bin/env python3
"""Filter the full GitHub REST API spec to repos/issues/pulls/search tags only."""
import json, yaml, os, sys

TARGET_TAGS = {"repos", "issues", "pulls", "search"}

with open("/tmp/github-full.json") as f:
    spec = json.load(f)

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

# Filter paths
filtered_paths = {}
used_schemas = set()

for path, path_item in spec.get("paths", {}).items():
    keep_ops = {}
    for method, op in path_item.items():
        if method in ("get", "post", "put", "patch", "delete", "head", "options"):
            op_tags = set(op.get("tags", []))
            if op_tags & TARGET_TAGS:
                keep_ops[method] = op
                collect_refs(op, used_schemas)
    if keep_ops:
        filtered_path = {}
        if "parameters" in path_item:
            filtered_path["parameters"] = path_item["parameters"]
            collect_refs(path_item["parameters"], used_schemas)
        filtered_path.update(keep_ops)
        filtered_paths[path] = filtered_path

print(f"Filtered paths: {len(filtered_paths)}")
total_ops = sum(
    len([m for m in v if m in ("get", "post", "put", "patch", "delete")])
    for v in filtered_paths.values()
)
print(f"Total operations: {total_ops}")

# Resolve schema refs iteratively
components = spec.get("components", {})
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

print(f"Referenced schemas: {len(expanded)}")

security_schemes = components.get("securitySchemes", {})
all_parameters = components.get("parameters", {})

# Collect referenced components/parameters
param_refs = {r.split("/")[-1] for r in used_schemas if r.startswith("#/components/parameters/")}
print(f"Referenced parameters: {len(param_refs)}")

filtered_spec = {
    "openapi": spec["openapi"],
    "info": spec["info"],
    "tags": [t for t in spec.get("tags", []) if t["name"] in TARGET_TAGS],
    "servers": spec.get("servers", []),
    "paths": filtered_paths,
    "components": {
        "schemas": {k: all_schemas[k] for k in expanded if k in all_schemas},
        "parameters": {k: all_parameters[k] for k in param_refs if k in all_parameters},
        "securitySchemes": security_schemes,
    }
}

out_path = "examples/github/github-subset.yaml"
with open(out_path, "w") as f:
    yaml.dump(filtered_spec, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

size = os.path.getsize(out_path)
print(f"Saved {out_path} ({size:,} bytes)")
