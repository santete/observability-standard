"""
inspect_datatable.py - Create a minimal lnsDatatable via Kibana API and read it back
to get the exact format Kibana expects.
"""
import urllib.request
import json

def api(path, method='GET', body=None):
    url = f"http://localhost:5601{path}"
    headers = {'kbn-xsrf': 'true', 'Content-Type': 'application/json'}
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return json.loads(res.read().decode())
    except Exception as e:
        return {'error': str(e)}

# Create a minimal Lens saved object with lnsDatatable type
# using the exact same structure as other working panels (lnsXY)
# but with lnsDatatable visualization type
LAYER_ID = "test-layer-001"
DV_ID = "otel-traces-dataview"

lens_obj = {
    "attributes": {
        "title": "TEST_DATATABLE_DEBUG",
        "visualizationType": "lnsDatatable",
        "type": "lens",
        "references": [
            {
                "type": "index-pattern",
                "id": DV_ID,
                "name": f"indexpattern-datasource-layer-{LAYER_ID}"
            }
        ],
        "state": {
            "visualization": {
                "layers": [
                    {
                        "layerId": LAYER_ID,
                        "layerType": "data",
                        "columns": [
                            {"columnId": "col-route", "isTransposed": False},
                            {"columnId": "col-count", "isTransposed": False}
                        ],
                        "columnOrder": [],
                        "sorting": None
                    }
                ],
                "rowHeight": "single",
                "rowHeightLines": 1,
                "headerRowHeight": "single",
                "headerRowHeightLines": 1
            },
            "query": {"query": "", "language": "kuery"},
            "filters": [],
            "datasourceStates": {
                "formBased": {
                    "layers": {
                        LAYER_ID: {
                            "columns": {
                                "col-route": {
                                    "label": "API Route",
                                    "dataType": "string",
                                    "operationType": "terms",
                                    "scale": "ordinal",
                                    "isBucketed": True,
                                    "sourceField": "attributes.url.path",
                                    "params": {
                                        "size": 10,
                                        "orderBy": {"type": "alphabetical"},
                                        "orderDirection": "asc",
                                        "otherBucket": True,
                                        "missingBucket": False
                                    }
                                },
                                "col-count": {
                                    "label": "Count",
                                    "dataType": "number",
                                    "operationType": "count",
                                    "scale": "ratio",
                                    "isBucketed": False,
                                    "sourceField": "___records___",
                                    "params": {"emptyAsNull": True}
                                }
                            },
                            "columnOrder": ["col-route", "col-count"],
                            "incompleteColumns": {}
                        }
                    }
                },
                "textBased": {"layers": {}}
            },
            "internalReferences": [],
            "adHocDataViews": {}
        }
    }
}

# Delete if exists
api("/api/saved_objects/lens/test-datatable-debug", method="DELETE")

# Create
print("Creating test datatable Lens saved object...")
r = api("/api/saved_objects/lens/test-datatable-debug", method="POST", body=lens_obj)
if 'error' in r:
    print("Create error:", r)
else:
    print("Created OK. ID:", r.get('id', '?'))

# Read it back
print("\nReading it back...")
r = api("/api/saved_objects/lens/test-datatable-debug")
if 'error' in r:
    print("Read error:", r)
else:
    state = r.get('attributes', {}).get('state', {})
    viz = state.get('visualization', {})
    print("Visualization keys:", list(viz.keys()))
    print("Visualization JSON:")
    print(json.dumps(viz, indent=2))
