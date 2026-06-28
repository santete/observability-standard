import json
import sys
import os

sys.path.append(os.path.abspath('scripts'))

# Try to parse original dashboard directly from string to bypass quotes issue
from test_original import original_dashboard_json

try:
    with open('kibana/dashboards.ndjson', 'r', encoding='utf-8') as f:
        rebuilt_json = json.loads(f.readline().strip())
except Exception as e:
    print("Error reading dashboards.ndjson", e)
    sys.exit(1)

o_attrs = original_dashboard_json.get("attributes", {})
# Load panels JSON safely from original_dashboard_json
import ast
try:
    # Use json.loads after replacing single quotes? No, the string in test_original.py might just be valid JSON if loaded safely.
    # Actually, in test_original.py it's a raw string '[{"version"...}]'. Let's just load it.
    o_panels = json.loads(o_attrs["panelsJSON"])
except Exception as e:
    print("Failed to load original panels JSON:", e)
    sys.exit(1)

r_panels = json.loads(rebuilt_json["attributes"]["panelsJSON"])

print("Original panels count:", len(o_panels))
print("Rebuilt panels count:", len(r_panels))

p_o = o_panels[0]
p_r = r_panels[0]

print("\n--- Original kpi-health state ---")
print(json.dumps(p_o["embeddableConfig"]["attributes"]["state"], indent=2))

print("\n--- Rebuilt kpi-health state ---")
print(json.dumps(p_r["embeddableConfig"]["attributes"]["state"], indent=2))

print("\n--- Differences in column col1 ---")
print("Original:", p_o["embeddableConfig"]["attributes"]["state"]["datasourceStates"]["formBased"]["layers"]["layer1"]["columns"]["col1"])
print("Rebuilt:", p_r["embeddableConfig"]["attributes"]["state"]["datasourceStates"]["formBased"]["layers"]["layer1"]["columns"]["col1"])
