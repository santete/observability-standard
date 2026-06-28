import ast
import json
import sys
import os

# 1. Parse original_dashboard_json from test_original.py using AST
try:
    with open('scripts/test_original.py', 'r', encoding='utf-8') as f:
        source = f.read()

    tree = ast.parse(source)
    original_panels = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'original_dashboard_json':
                    dashboard_dict = ast.literal_eval(node.value)
                    panels_json_str = dashboard_dict['attributes']['panelsJSON']
                    original_panels = json.loads(panels_json_str)
                    break
            if original_panels:
                break
                
    if not original_panels:
        print("Could not parse original_panels")
        sys.exit(1)
        
    with open('scratch/original_panels.json', 'w', encoding='utf-8') as out:
        json.dump(original_panels, out, indent=2)
        
except Exception as e:
    print("Error parsing test_original.py:", e)
    sys.exit(1)

# 2. Extract first dashboard panels from rebuilt NDJSON
try:
    with open('kibana/dashboards.ndjson', 'r', encoding='utf-8') as f:
        for line in f:
            d = json.loads(line)
            if d.get('id') == 'executive-overview-dashboard':
                rebuilt_panels = json.loads(d['attributes']['panelsJSON'])
                with open('scratch/rebuilt_panels.json', 'w', encoding='utf-8') as out:
                    json.dump(rebuilt_panels, out, indent=2)
                break
except Exception as e:
    print("Error parsing rebuilt NDJSON:", e)
    sys.exit(1)

# 3. Perform a deep comparison and print differences
def compare_dicts(d1, d2, path=""):
    if isinstance(d1, dict) and isinstance(d2, dict):
        keys = set(d1.keys()).union(set(d2.keys()))
        for k in keys:
            if k not in d1:
                print(f"Missing in ORIGINAL: {path}.{k} (in rebuilt it is {d2[k]})")
            elif k not in d2:
                print(f"Missing in REBUILT: {path}.{k} (in original it is {d1[k]})")
            else:
                compare_dicts(d1[k], d2[k], f"{path}.{k}" if path else k)
    elif isinstance(d1, list) and isinstance(d2, list):
        if len(d1) != len(d2):
            print(f"Length mismatch at {path}: original len {len(d1)}, rebuilt len {len(d2)}")
        for i, (v1, v2) in enumerate(zip(d1, d2)):
            compare_dicts(v1, v2, f"{path}[{i}]")
    else:
        if d1 != d2:
            print(f"Value mismatch at {path}: original='{d1}', rebuilt='{d2}'")

print("--- COMPARING KPI HEALTH PANEL (Panel 0) ---")
compare_dicts(original_panels[0], rebuilt_panels[0])

print("\n--- COMPARING RPS TIMESERIES PANEL (Panel 4) ---")
compare_dicts(original_panels[4], rebuilt_panels[4])

print("\nComparison finished.")
