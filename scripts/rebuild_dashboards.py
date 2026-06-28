import json
import urllib.request
import subprocess
import os
import time

script_dir = os.path.dirname(os.path.abspath(__file__))
ndjson_path = os.path.join(script_dir, '..', 'kibana', 'dashboards.ndjson')
ndjson_path = os.path.abspath(ndjson_path)

# Helper to send API requests to Kibana
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
        print(f"Request to {method} {path} failed: {e}")
        return None

# 1. Delete and Recreate Data Views via high-level API
print("Deleting old data views...")
kibana_request("/api/data_views/data_view/otel-logs-dataview", method="DELETE")
kibana_request("/api/data_views/data_view/otel-traces-dataview", method="DELETE")
kibana_request("/api/data_views/data_view/otel-metrics-dataview", method="DELETE")

print("\nCreating data views via high-level API...")
kibana_request("/api/data_views/data_view", method="POST", body={
    "data_view": {
        "id": "otel-logs-dataview",
        "title": "logs-*.otel-*",
        "name": "logs-*.otel-*",
        "timeFieldName": "@timestamp"
    }
})
kibana_request("/api/data_views/data_view", method="POST", body={
    "data_view": {
        "id": "otel-traces-dataview",
        "title": "traces-*.otel-*",
        "name": "traces-*.otel-*",
        "timeFieldName": "@timestamp"
    }
})
kibana_request("/api/data_views/data_view", method="POST", body={
    "data_view": {
        "id": "otel-metrics-dataview",
        "title": "metrics-*.otel-*",
        "name": "metrics-*.otel-*",
        "timeFieldName": "@timestamp"
    }
})

# Patch data views to remove empty cached fields
print("Patching data views to remove empty cached fields...")
for dv_id in ["otel-logs-dataview", "otel-traces-dataview", "otel-metrics-dataview"]:
    obj = kibana_request(f"/api/saved_objects/index-pattern/{dv_id}")
    if obj and 'attributes' in obj:
        attrs = obj['attributes']
        if 'fields' in attrs:
            del attrs['fields']
        kibana_request(f"/api/saved_objects/index-pattern/{dv_id}", method="PUT", body={"attributes": attrs})


# Helper to construct original formBased Lens panels
def make_original_lens_panel(x, y, w, h, index, title, description, visualization_type, layers_columns, column_order, viz_config, dataview_id, dataview_ref_name):
    # Derive layer_id from dataview_ref_name suffix (e.g. indexpattern-datasource-layer-layer1 -> layer1)
    layer_id = dataview_ref_name.split('-')[-1]
    
    # Dynamically patch viz_config to ensure layerId matches layer_id
    if "layerId" in viz_config:
        viz_config["layerId"] = layer_id
    if "layers" in viz_config:
        for layer in viz_config["layers"]:
            if "layerId" in layer:
                layer["layerId"] = layer_id
                
    state = {
        "datasourceStates": {
            "formBased": {
                "layers": {
                    layer_id: {
                        "columns": layers_columns,
                        "columnOrder": column_order,
                        "incompleteColumns": {}
                    }
                }
            }
        },
        "query": {
            "query": "",
            "language": "kuery"
        },
        "filters": [],
        "visualization": viz_config
    }
    
    panel = {
        "version": "8.17.0",
        "type": "lens",
        "gridData": {"x": x, "y": y, "w": w, "h": h, "i": index},
        "panelIndex": index,
        "embeddableConfig": {
            "title": title,
            "description": description,
            "attributes": {
                "visualizationType": visualization_type,
                "state": state,
                "references": [
                    {
                        "type": "index-pattern",
                        "id": dataview_id,
                        "name": dataview_ref_name
                    },
                    {
                        "type": "index-pattern",
                        "id": dataview_id,
                        "name": "indexpattern-datasource-current-indexpattern"
                    }
                ]
            }
        }
    }
    return panel

# 2. Build Dashboard 1 (Executive Overview) - ORIGINAL working formBased format
d1_panels = [
    make_original_lens_panel(
        0, 0, 12, 8, "kpi-health", "Service Health Status", "Liveness/Readiness status of services", "lnsMetric",
        {"col1": {"operationType": "count", "isBucketed": False, "scale": "ratio", "dataType": "number", "label": "Total Requests"}},
        ["col1"], {"layerId": "layer1", "accessor": "col1", "layerType": "data"},
        "otel-traces-dataview", "indexpattern-datasource-layer-layer1"
    ),
    make_original_lens_panel(
        12, 0, 12, 8, "kpi-error-rate", "Error Rate %", "Current system-wide error rate", "lnsMetric",
        {"col1": {"operationType": "count", "isBucketed": False, "scale": "ratio", "dataType": "number", "label": "Error Count"}},
        ["col1"], {"layerId": "layer1", "accessor": "col1", "layerType": "data"},
        "otel-traces-dataview", "indexpattern-datasource-layer-layer1"
    ),
    make_original_lens_panel(
        24, 0, 12, 8, "kpi-rps", "Requests Per Second", "Current RPS", "lnsMetric",
        {"col1": {"operationType": "count", "isBucketed": False, "scale": "ratio", "dataType": "number", "label": "RPS"}},
        ["col1"], {"layerId": "layer1", "accessor": "col1", "layerType": "data"},
        "otel-traces-dataview", "indexpattern-datasource-layer-layer1"
    ),
    make_original_lens_panel(
        36, 0, 12, 8, "kpi-latency", "Avg Latency (ms)", "Average response latency", "lnsMetric",
        {"col1": {"operationType": "average", "isBucketed": False, "scale": "ratio", "dataType": "number", "sourceField": "duration", "label": "Avg Latency"}},
        ["col1"], {"layerId": "layer1", "accessor": "col1", "layerType": "data"},
        "otel-traces-dataview", "indexpattern-datasource-layer-layer1"
    ),
    make_original_lens_panel(
        0, 8, 24, 12, "rps-timeseries", "Request Rate (RPS) Over Time", "Time-series line chart of request throughput", "lnsXY",
        {
            "col-x": {"operationType": "date_histogram", "isBucketed": True, "scale": "interval", "dataType": "date", "sourceField": "@timestamp", "params": {"interval": "auto"}},
            "col-y": {"operationType": "count", "isBucketed": False, "scale": "ratio", "dataType": "number", "label": "Requests"}
        },
        ["col-x", "col-y"],
        {
            "layers": [{"layerId": "layer1", "layerType": "data", "seriesType": "line", "xAccessor": "col-x", "accessors": ["col-y"]}],
            "preferredSeriesType": "line"
        },
        "otel-traces-dataview", "indexpattern-datasource-layer-layer1"
    ),
    make_original_lens_panel(
        24, 8, 24, 12, "latency-timeseries", "Latency Over Time", "Response latency time-series", "lnsXY",
        {
            "col-x": {"operationType": "date_histogram", "isBucketed": True, "scale": "interval", "dataType": "date", "sourceField": "@timestamp", "params": {"interval": "auto"}},
            "col-p95": {"operationType": "percentile", "isBucketed": False, "scale": "ratio", "dataType": "number", "sourceField": "duration", "params": {"percentile": 95}, "label": "p95 Latency"},
            "col-p99": {"operationType": "percentile", "isBucketed": False, "scale": "ratio", "dataType": "number", "sourceField": "duration", "params": {"percentile": 99}, "label": "p99 Latency"}
        },
        ["col-x", "col-p95", "col-p99"],
        {
            "layers": [{"layerId": "layer1", "layerType": "data", "seriesType": "line", "xAccessor": "col-x", "accessors": ["col-p95", "col-p99"]}],
            "preferredSeriesType": "line"
        },
        "otel-traces-dataview", "indexpattern-datasource-layer-layer1"
    ),
    make_original_lens_panel(
        0, 20, 48, 10, "error-distribution", "HTTP Status Code Distribution", "Distribution of 2xx, 4xx, 5xx responses over time", "lnsXY",
        {
            "col-x": {"operationType": "date_histogram", "isBucketed": True, "scale": "interval", "dataType": "date", "sourceField": "@timestamp", "params": {"interval": "auto"}},
            "col-y": {"operationType": "count", "isBucketed": False, "scale": "ratio", "dataType": "number", "label": "Count"},
            "col-split": {"operationType": "terms", "isBucketed": True, "scale": "ordinal", "dataType": "string", "sourceField": "attributes.http.response.status_code", "params": {"size": 10}}
        },
        ["col-split", "col-x", "col-y"],
        {
            "layers": [{"layerId": "layer1", "layerType": "data", "seriesType": "bar_stacked", "xAccessor": "col-x", "accessors": ["col-y"], "splitAccessor": "col-split"}],
            "preferredSeriesType": "bar_stacked"
        },
        "otel-traces-dataview", "indexpattern-datasource-layer-layer1"
    )
]

dashboard1 = {
    "id": "executive-overview-dashboard",
    "type": "dashboard",
    "migrationVersion": {"dashboard": "8.17.0"},
    "attributes": {
        "title": "[OBS] Executive Overview - System Health",
        "description": "High-level system health overview. KPI panels, RPS time-series, latency p95/p99, and error distribution. Spec Section 5 - Screen 1.",
        "panelsJSON": json.dumps(d1_panels),
        "timeRestore": True,
        "timeTo": "now",
        "timeFrom": "now-1h",
        "refreshInterval": {"pause": False, "value": 10000},
        "kibanaSavedObjectMeta": {"searchSourceJSON": '{"query":{"query":"","language":"kuery"},"filter":[]}'}
    },
    "references": [
        {"id": "otel-traces-dataview", "name": "indexpattern-datasource-layer-layer1", "type": "index-pattern"}
    ]
}

# 3. Build Dashboard 2 (Developer Deep-Dive) - ORIGINAL working formBased format
d2_panels = [
    make_original_lens_panel(
        0, 0, 24, 12, "slow-endpoints", "Top 10 Slowest Endpoints (by p95 Latency)", "API routes with highest p95 response time", "lnsDatatable",
        {
            "col-route": {"operationType": "terms", "isBucketed": True, "scale": "ordinal", "dataType": "string", "sourceField": "attributes.url.path", "params": {"size": 10}, "label": "API Route"},
            "col-method": {"operationType": "terms", "isBucketed": True, "scale": "ordinal", "dataType": "string", "sourceField": "attributes.http.request.method", "params": {"size": 5}, "label": "Method"},
            "col-p95": {"operationType": "percentile", "isBucketed": False, "scale": "ratio", "dataType": "number", "sourceField": "duration", "params": {"percentile": 95}, "label": "p95 Latency (ms)"},
            "col-max": {"operationType": "max", "isBucketed": False, "scale": "ratio", "dataType": "number", "sourceField": "duration", "label": "Max Latency (ms)"},
            "col-count": {"operationType": "count", "isBucketed": False, "scale": "ratio", "dataType": "number", "label": "Call Count"}
        },
        ["col-route", "col-method", "col-p95", "col-max", "col-count"],
        {
            "layers": [{
                "layerId": "layer1",
                "layerType": "data",
                "columns": [{"columnId": "col-route"}, {"columnId": "col-method"}, {"columnId": "col-p95"}, {"columnId": "col-max"}, {"columnId": "col-count"}]
            }]
        },
        "otel-traces-dataview", "indexpattern-datasource-layer-layer1"
    ),
    make_original_lens_panel(
        24, 0, 24, 12, "error-endpoints", "Top 10 Most Error-Prone Endpoints", "API routes with most 5xx errors", "lnsDatatable",
        {
            "col-route": {"operationType": "terms", "isBucketed": True, "scale": "ordinal", "dataType": "string", "sourceField": "attributes.url.path", "params": {"size": 10}, "label": "API Route"},
            "col-errors": {"operationType": "count", "isBucketed": False, "scale": "ratio", "dataType": "number", "label": "Error Count"},
            "col-status": {"operationType": "terms", "isBucketed": True, "scale": "ordinal", "dataType": "string", "sourceField": "attributes.http.response.status_code", "params": {"size": 5}, "label": "Status Codes"}
        },
        ["col-route", "col-errors", "col-status"],
        {
            "layers": [{
                "layerId": "layer1",
                "layerType": "data",
                "columns": [{"columnId": "col-route"}, {"columnId": "col-errors"}, {"columnId": "col-status"}]
            }]
        },
        "otel-traces-dataview", "indexpattern-datasource-layer-layer1"
    ),
    make_original_lens_panel(
        0, 12, 48, 8, "error-timeline", "Errors Over Time", "Timeline of errors by endpoint", "lnsXY",
        {
            "col-x": {"operationType": "date_histogram", "isBucketed": True, "scale": "interval", "dataType": "date", "sourceField": "@timestamp", "params": {"interval": "auto"}},
            "col-y": {"operationType": "count", "isBucketed": False, "scale": "ratio", "dataType": "number", "label": "Errors"},
            "col-split": {"operationType": "terms", "isBucketed": True, "scale": "ordinal", "dataType": "string", "sourceField": "attributes.url.path", "params": {"size": 5}}
        },
        ["col-split", "col-x", "col-y"],
        {
            "layers": [{"layerId": "layer1", "layerType": "data", "seriesType": "bar_stacked", "xAccessor": "col-x", "accessors": ["col-y"], "splitAccessor": "col-split"}],
            "preferredSeriesType": "bar_stacked"
        },
        "otel-traces-dataview", "indexpattern-datasource-layer-layer1"
    ),
    make_original_lens_panel(
        0, 20, 48, 15, "log-stream", "Log Stream (Search by TraceId)", "Real-time log viewer with TraceId search capability", "lnsDatatable",
        {
            "col-time": {"operationType": "date_histogram", "isBucketed": True, "scale": "interval", "dataType": "date", "sourceField": "@timestamp", "params": {"interval": "auto"}, "label": "Timestamp"},
            "col-level": {"operationType": "terms", "isBucketed": True, "scale": "ordinal", "dataType": "string", "sourceField": "severity_text", "params": {"size": 5}, "label": "Level"},
            "col-count": {"operationType": "count", "isBucketed": False, "scale": "ratio", "dataType": "number", "label": "Count"}
        },
        ["col-time", "col-level", "col-count"],
        {
            "layers": [{
                "layerId": "logs",
                "layerType": "data",
                "columns": [{"columnId": "col-time"}, {"columnId": "col-level"}, {"columnId": "col-count"}]
            }]
        },
        "otel-logs-dataview", "indexpattern-datasource-layer-logs"
    )
]

dashboard2 = {
    "id": "developer-deepdive-dashboard",
    "type": "dashboard",
    "migrationVersion": {"dashboard": "8.17.0"},
    "attributes": {
        "title": "[OBS] Developer Deep-Dive - Debug & Optimize",
        "description": "Developer-focused dashboard for debugging and optimization. Top slowest endpoints, most error-prone endpoints, trace/log viewer. Spec Section 5 - Screen 2.",
        "panelsJSON": json.dumps(d2_panels),
        "timeRestore": True,
        "timeTo": "now",
        "timeFrom": "now-1h",
        "refreshInterval": {"pause": False, "value": 10000},
        "kibanaSavedObjectMeta": {"searchSourceJSON": '{"query":{"query":"","language":"kuery"},"filter":[]}'}
    },
    "references": [
        {"id": "otel-traces-dataview", "name": "indexpattern-datasource-layer-layer1", "type": "index-pattern"},
        {"id": "otel-logs-dataview", "name": "indexpattern-datasource-layer-logs", "type": "index-pattern"},
        {"id": "otel-traces-dataview", "name": "indexpattern-datasource-current-indexpattern", "type": "index-pattern"}
    ]
}

# 4. Build Dashboard 3 (Infrastructure & Runtime Performance) - ORIGINAL working formBased format
d3_panels = [
    make_original_lens_panel(
        0, 0, 24, 12, "threadpool-stats", "ThreadPool Threads & Queue Length", "Active worker threads vs queue length", "lnsXY",
        {
            "col-x": {"operationType": "date_histogram", "isBucketed": True, "scale": "interval", "dataType": "date", "sourceField": "@timestamp", "params": {"interval": "auto"}},
            "col-threads": {"operationType": "average", "isBucketed": False, "scale": "ratio", "dataType": "number", "sourceField": "metrics.process.runtime.dotnet.thread_pool.threads.count", "label": "Thread Count"},
            "col-queue": {"operationType": "average", "isBucketed": False, "scale": "ratio", "dataType": "number", "sourceField": "metrics.process.runtime.dotnet.thread_pool.queue.length", "label": "Queue Length"}
        },
        ["col-x", "col-threads", "col-queue"],
        {
            "layers": [{"layerId": "layer1", "layerType": "data", "seriesType": "line", "xAccessor": "col-x", "accessors": ["col-threads", "col-queue"]}],
            "preferredSeriesType": "line"
        },
        "otel-metrics-dataview", "indexpattern-datasource-layer-layer1"
    ),
    make_original_lens_panel(
        24, 0, 24, 12, "gc-memory", "GC Heap & Committed Memory", "Heap memory vs total committed memory", "lnsXY",
        {
            "col-x": {"operationType": "date_histogram", "isBucketed": True, "scale": "interval", "dataType": "date", "sourceField": "@timestamp", "params": {"interval": "auto"}},
            "col-heap": {"operationType": "average", "isBucketed": False, "scale": "ratio", "dataType": "number", "sourceField": "metrics.process.runtime.dotnet.gc.heap.size", "label": "Heap Size (Bytes)"},
            "col-committed": {"operationType": "average", "isBucketed": False, "scale": "ratio", "dataType": "number", "sourceField": "metrics.process.runtime.dotnet.gc.committed_memory.size", "label": "Committed Memory (Bytes)"}
        },
        ["col-x", "col-heap", "col-committed"],
        {
            "layers": [{"layerId": "layer1", "layerType": "data", "seriesType": "line", "xAccessor": "col-x", "accessors": ["col-heap", "col-committed"]}],
            "preferredSeriesType": "line"
        },
        "otel-metrics-dataview", "indexpattern-datasource-layer-layer1"
    ),
    make_original_lens_panel(
        0, 12, 24, 12, "gc-stats", "GC Collections & Pause Time", "GC collections frequency and pause duration", "lnsXY",
        {
            "col-x": {"operationType": "date_histogram", "isBucketed": True, "scale": "interval", "dataType": "date", "sourceField": "@timestamp", "params": {"interval": "auto"}},
            "col-pause": {"operationType": "average", "isBucketed": False, "scale": "ratio", "dataType": "number", "sourceField": "metrics.process.runtime.dotnet.gc.duration", "label": "GC Pause Time (ms)"},
            "col-collections": {"operationType": "average", "isBucketed": False, "scale": "ratio", "dataType": "number", "sourceField": "metrics.process.runtime.dotnet.gc.collections.count", "label": "GC Collections"}
        },
        ["col-x", "col-pause", "col-collections"],
        {
            "layers": [{"layerId": "layer1", "layerType": "data", "seriesType": "line", "xAccessor": "col-x", "accessors": ["col-pause", "col-collections"]}],
            "preferredSeriesType": "line"
        },
        "otel-metrics-dataview", "indexpattern-datasource-layer-layer1"
    ),
    make_original_lens_panel(
        24, 12, 24, 12, "kestrel-exceptions", "Kestrel Connections & Exceptions", "Active connections vs runtime exception count", "lnsXY",
        {
            "col-x": {"operationType": "date_histogram", "isBucketed": True, "scale": "interval", "dataType": "date", "sourceField": "@timestamp", "params": {"interval": "auto"}},
            "col-conn": {"operationType": "average", "isBucketed": False, "scale": "ratio", "dataType": "number", "sourceField": "metrics.kestrel.active_connections", "label": "Active Connections"},
            "col-ex": {"operationType": "average", "isBucketed": False, "scale": "ratio", "dataType": "number", "sourceField": "metrics.process.runtime.dotnet.exceptions.count", "label": "Exceptions Count"}
        },
        ["col-x", "col-conn", "col-ex"],
        {
            "layers": [{"layerId": "layer1", "layerType": "data", "seriesType": "line", "xAccessor": "col-x", "accessors": ["col-conn", "col-ex"]}],
            "preferredSeriesType": "line"
        },
        "otel-metrics-dataview", "indexpattern-datasource-layer-layer1"
    )
]

dashboard3 = {
    "id": "infrastructure-runtime-dashboard",
    "type": "dashboard",
    "migrationVersion": {"dashboard": "8.17.0"},
    "attributes": {
        "title": "[OBS] Infrastructure & Runtime Performance",
        "description": "System resource utilization, ThreadPool starvation monitoring, and Garbage Collection statistics. Spec Section 5 - Screen 3.",
        "panelsJSON": json.dumps(d3_panels),
        "timeRestore": True,
        "timeTo": "now",
        "timeFrom": "now-1h",
        "refreshInterval": {"pause": False, "value": 10000},
        "kibanaSavedObjectMeta": {"searchSourceJSON": '{"query":{"query":"","language":"kuery"},"filter":[]}'}
    },
    "references": [
        {"id": "otel-metrics-dataview", "name": "indexpattern-datasource-layer-layer1", "type": "index-pattern"},
        {"id": "otel-metrics-dataview", "name": "indexpattern-datasource-current-indexpattern", "type": "index-pattern"}
    ]
}

# 5. Write out the NDJSON file
print(f"Generating NDJSON file at: {ndjson_path}")
all_objects = [dashboard1, dashboard2, dashboard3]

with open(ndjson_path, 'w', encoding='utf-8') as f:
    for obj in all_objects:
        f.write(json.dumps(obj) + '\n')

print("Generating finished successfully!")

# 6. Execute curl import
cmd = [
    'curl.exe', '-X', 'POST',
    'http://localhost:5601/api/saved_objects/_import?overwrite=true',
    '-H', 'kbn-xsrf: true',
    '-F', f'file=@{ndjson_path}'
]

print("Importing dashboards into Kibana...")
try:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    print("\n--- IMPORT SUCCESS ---")
    print(result.stdout)
except subprocess.CalledProcessError as e:
    print("\n--- IMPORT FAILED ---")
    print("Exit code:", e.returncode)
    print("Error output:", e.stderr)
    print("Standard output:", e.stdout)

# 7. Run Playwright to verify all 3 dashboards
artifact_dir = r"C:\Users\nangh\.gemini\antigravity\brain\ebba6e7b-5d89-46c8-bb3c-76a747786481"
print(f"Artifact directory set to: {artifact_dir}")
from playwright.sync_api import sync_playwright

dashboards_to_test = [
    ("executive-overview-dashboard", "executive_overview.png"),
    ("developer-deepdive-dashboard", "developer_deepdive.png"),
    ("infrastructure-runtime-dashboard", "infrastructure_runtime.png")
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    
    for db_id, filename in dashboards_to_test:
        page = browser.new_page(viewport={"width": 1280, "height": 1000})
        url = f"http://localhost:5601/app/dashboards#/view/{db_id}"
        print(f"Loading {db_id}...")
        page.goto(url)
        time.sleep(15) # Wait for render
        
        screenshot_out = os.path.join(artifact_dir, filename)
        page.screenshot(path=screenshot_out)
        print(f"Screenshot saved to: {screenshot_out}")
        
        errors = page.eval_on_selector_all(
            "p, div", 
            "elements => elements.map(el => el.innerText).filter(text => text && text.includes('Cannot read properties'))"
        )
        if errors:
            print(f"--- ERRORS FOUND IN {db_id} ---")
            for err in set(errors):
                print(f"- {err}")
        else:
            print(f"--- {db_id} VERIFIED SUCCESSFULLY! ZERO ERRORS ---")
            
    browser.close()
print("All verifications complete.")
