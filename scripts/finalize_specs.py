#!/usr/bin/env python3
"""Create JSON versions of YAML specs and copy bundled GitHub spec."""
import yaml, json, shutil, os

# Stripe YAML -> JSON
print("Converting stripe-subset.yaml to JSON...", flush=True)
with open("examples/stripe/stripe-subset.yaml") as f:
    data = yaml.safe_load(f)
with open("examples/stripe/stripe-subset.json", "w") as f:
    json.dump(data, f, indent=2)
print(f"stripe-subset.json: {os.path.getsize('examples/stripe/stripe-subset.json'):,} bytes", flush=True)

# GitHub subset is already self-contained (extracted from pre-bundled JSON)
print("Copying github-subset.yaml as bundled version...", flush=True)
shutil.copy("examples/github/github-subset.yaml", "examples/github/github-subset-bundled.yaml")
print("Done.", flush=True)
