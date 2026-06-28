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

# ======================================================
# STEP 1: List all dashboards in Kibana
# ======================================================
print("=" * 60)
print("ALL DASHBOARDS IN KIBANA:")
print("=" * 60)
r = api('/api/saved_objects/_find?type=dashboard&per_page=20')
for d in r.get('saved_objects', []):
    dash_id = d['id']
    title = d['attributes'].get('title', '?')
    panels_str = d['attributes'].get('panelsJSON', '[]')
    panels = json.loads(panels_str)
    print(f"\nDashboard: {dash_id}")
    print(f"  Title: {title}")
    print(f"  Panel count: {len(panels)}")
    
    for i, p in enumerate(panels[:2]):
        panel_type = p.get('type', '?')
        panel_index = p.get('panelIndex', '?')
        ec = p.get('embeddableConfig', {})
        ec_keys = list(ec.keys())
        attrs = ec.get('attributes', {})
        attrs_keys = list(attrs.keys())
        saved_id = p.get('savedObjectId', 'NOT PRESENT')
        
        print(f"  Panel[{i}] - index={panel_index} type={panel_type}")
        print(f"    savedObjectId: {saved_id}")
        print(f"    embeddableConfig keys: {ec_keys}")
        if attrs_keys:
            print(f"    attributes keys: {attrs_keys}")

# ======================================================
# STEP 2: Look at the specific lnsXY panel that fails
# ======================================================
print("\n" + "=" * 60)
print("DETAILED: RPS TIMESERIES PANEL (executive-overview)")
print("=" * 60)

r = api('/api/saved_objects/dashboard/executive-overview-dashboard')
panels_str = r.get('attributes', {}).get('panelsJSON', '[]')
panels = json.loads(panels_str)

for p in panels:
    panel_index = p.get('panelIndex', '')
    if panel_index == 'rps-timeseries':
        ec = p.get('embeddableConfig', {})
        attrs = ec.get('attributes', {})
        state = attrs.get('state', {})
        
        print("\nFull panel structure:")
        print(json.dumps(p, indent=2))
        break

# ======================================================
# STEP 3: Check what the Kibana sample Lens object
# looks like when used in a dashboard
# ======================================================
print("\n" + "=" * 60)
print("FINDING A DASHBOARD THAT USES LENS SAVED OBJECTS:")
print("=" * 60)

r = api('/api/saved_objects/_find?type=dashboard&per_page=10')
for d in r.get('saved_objects', []):
    panels_str = d['attributes'].get('panelsJSON', '[]')
    panels = json.loads(panels_str)
    for p in panels:
        if p.get('type') == 'lens' and p.get('savedObjectId'):
            print(f"Found lens panel with savedObjectId: {p['savedObjectId']}")
            print(f"Dashboard: {d['id']}")
            print(f"Panel: {json.dumps(p, indent=2)[:1000]}")
            break

# ======================================================
# STEP 4: Check what fields exist in the traces data view
# ======================================================
print("\n" + "=" * 60)
print("TRACES DATA VIEW FIELDS (first 30):")
print("=" * 60)

r = api('/api/data_views/data_view/otel-traces-dataview')
if 'data_view' in r:
    dv = r['data_view']
    print(f"Title: {dv.get('title', '?')}")
    print(f"Time field: {dv.get('timeFieldName', '?')}")
    fields = dv.get('fields', {})
    print(f"Field count: {len(fields)}")
    for i, (fname, finfo) in enumerate(list(fields.items())[:30]):
        print(f"  {fname}: {finfo.get('type', '?')}")
else:
    print("Data view not found:", r)
