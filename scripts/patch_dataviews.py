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

dataview_ids = ["otel-traces-dataview", "otel-logs-dataview", "otel-metrics-dataview"]

for dv_id in dataview_ids:
    print(f"\nFetching saved object: {dv_id}")
    obj = kibana_request(f"/api/saved_objects/index-pattern/{dv_id}")
    if obj and 'attributes' in obj:
        attrs = obj['attributes']
        print(f"Current fields attribute: {attrs.get('fields')}")
        
        # We can either delete the key or set it to None. Let's delete the 'fields' key if present,
        # or set it to None to overwrite it.
        if 'fields' in attrs:
            del attrs['fields']
            
        print("Updating saved object attributes (removing fields)...")
        # To update, we POST to /api/saved_objects/{type}/{id}
        res = kibana_request(f"/api/saved_objects/index-pattern/{dv_id}", method="PUT", body={
            "attributes": attrs
        })
        if res:
            print("Successfully updated!")
            print("New attributes keys:", list(res.get('attributes', {}).keys()))
        else:
            print("Failed to update.")
    else:
        print(f"Could not fetch index-pattern {dv_id}")
