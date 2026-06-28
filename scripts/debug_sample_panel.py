import urllib.request
import json

def api(path, method='GET', body=None):
    url = f"http://localhost:5601{path}"
    headers = {'kbn-xsrf': 'true', 'Content-Type': 'application/json'}
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            return json.loads(res.read().decode())
    except Exception as e:
        return {'error': str(e)}

# Get the working [Logs] Web Traffic dashboard and look at one of its Lens panels
r = api('/api/saved_objects/dashboard/edf84fe0-e1a0-11e7-b6d5-4dc382ef7f5b')
panels_str = r.get('attributes', {}).get('panelsJSON', '[]')
panels = json.loads(panels_str)

print(f"Total panels: {len(panels)}")

# Find a lens panel
for i, p in enumerate(panels):
    if p.get('type') == 'lens':
        print(f"\n=== LENS PANEL [{i}] ===")
        print(json.dumps(p, indent=2))
        break

# Also look at the references at dashboard level
refs = r.get('references', [])
print(f"\n=== DASHBOARD REFERENCES ===")
print(json.dumps(refs, indent=2))
