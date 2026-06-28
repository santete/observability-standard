"""
debug_real_browser.py - Use Playwright with real Chrome (non-headless) to 
capture ACTUAL browser errors and compare with headless behavior.
Also verify what Kibana actually has stored.
"""
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

print("=" * 60)
print("STEP 1: Verify what Kibana currently has")
print("=" * 60)

# Check dashboards
for db_id in ['executive-overview-dashboard', 'developer-deepdive-dashboard', 'infrastructure-runtime-dashboard']:
    r = api(f'/api/saved_objects/dashboard/{db_id}')
    if 'error' in r:
        print(f"[MISSING] {db_id}: {r['error']}")
    else:
        title = r.get('attributes', {}).get('title', '?')
        panels_str = r.get('attributes', {}).get('panelsJSON', '[]')
        panels = json.loads(panels_str)
        refs = r.get('references', [])
        print(f"[OK] {db_id}")
        print(f"     Title: {title}")
        print(f"     Panels: {len(panels)}, Refs: {len(refs)}")
        # Show first panel type and embeddableConfig keys
        if panels:
            p0 = panels[0]
            ec = p0.get('embeddableConfig', {})
            attrs = ec.get('attributes', {})
            print(f"     Panel[0] type={p0.get('type')}, title={p0.get('title', '?')}")
            print(f"     embeddableConfig keys: {list(ec.keys())}")
            print(f"     attributes keys: {list(attrs.keys())}")

print()
print("=" * 60)
print("STEP 2: Verify data views")
print("=" * 60)

for dv_id in ['otel-logs-dataview', 'otel-traces-dataview', 'otel-metrics-dataview']:
    r = api(f'/api/data_views/data_view/{dv_id}')
    if 'error' in r:
        print(f"[MISSING] {dv_id}: {r['error']}")
    else:
        dv = r.get('data_view', {})
        print(f"[OK] {dv_id}: title={dv.get('title')}, timeField={dv.get('timeFieldName')}")

print()
print("=" * 60)
print("STEP 3: Show first panel full JSON (executive-overview)")
print("=" * 60)

r = api('/api/saved_objects/dashboard/executive-overview-dashboard')
panels_str = r.get('attributes', {}).get('panelsJSON', '[]')
panels = json.loads(panels_str)
if panels:
    p0 = panels[0]
    print(json.dumps(p0, indent=2))

print()
print("=" * 60)
print("STEP 4: Show dashboard references")
print("=" * 60)

refs = r.get('references', [])
print(json.dumps(refs[:5], indent=2))
