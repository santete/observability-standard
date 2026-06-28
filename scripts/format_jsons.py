import json

# Format original
with open('temp_original_panels.json', 'r', encoding='utf-8') as f:
    o_panels = json.load(f)
with open('temp_original_panels_fmt.json', 'w', encoding='utf-8') as out:
    json.dump(o_panels, out, indent=2)

# Format rebuilt
with open('kibana/dashboards.ndjson', 'r', encoding='utf-8') as f:
    r_json = json.loads(f.readline().strip())
    r_panels = json.loads(r_json['attributes']['panelsJSON'])
with open('temp_rebuilt_panels.json', 'w', encoding='utf-8') as out:
    json.dump(r_panels, out, indent=2)
