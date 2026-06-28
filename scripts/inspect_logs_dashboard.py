import json
import urllib.request

def kibana_request(path, method='GET', body=None):
    url = f"http://localhost:5601{path}"
    headers = {
        'kbn-xsrf': 'true',
        'Content-Type': 'application/json'
    }
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode())
    except Exception as e:
        print(f"Request failed: {e}")
        return None

res = kibana_request("/api/saved_objects/_find?type=dashboard&search=logs")
if res and 'saved_objects' in res and len(res['saved_objects']) > 0:
    dash = res['saved_objects'][0]
    panels = json.loads(dash['attributes']['panelsJSON'])
    lens_panels = [p for p in panels if p.get('type') == 'lens']
    print("Panel 5 (lnsDatatable) Details:")
    print(json.dumps(lens_panels[5], indent=2))
    print("\nPanel 7 (lnsDatatable) Details:")
    print(json.dumps(lens_panels[7], indent=2))
else:
    print("No dashboard found.")
