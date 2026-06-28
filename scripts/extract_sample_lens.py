import urllib.request, json

req = urllib.request.Request('http://localhost:5601/api/saved_objects/_find?type=lens', headers={'kbn-xsrf': 'true'})
res = urllib.request.urlopen(req)
d = json.loads(res.read().decode())

sample_panel = next(obj for obj in d['saved_objects'] if obj['attributes']['title'] == '[Logs] Bytes distribution')

with open('sample_lens.json', 'w', encoding='utf-8') as f:
    json.dump(sample_panel, f, indent=2)

print("Exported to scratch/sample_lens.json")
