import json
import urllib.request
import subprocess
import os

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

# 1. Recreate Data Views via high-level API
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

# 2. Helper to construct Lens panels (using dataview_id as the reference name to avoid mapping errors)
def make_lens_panel(x, y, w, h, index, title, description, visualization_type, layers_columns, column_order, viz_config, dataview_id):
    layer = {
        "layerId": "layer1",
        "layerType": "data",
        "columns": layers_columns,
        "columnOrder": column_order
    }
    
    state = {
        "datasourceStates": {
            "indexpattern": {
                "currentIndexPatternId": dataview_id,
                "layers": [layer]
            }
        },
        "visualization": viz_config
    }
    
    # visualization object compatibility
    if "layerId" not in viz_config and visualization_type != "lnsXY":
        viz_config["layerId"] = "layer1"
        viz_config["layerType"] = "data"
        
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
                "state": state
            },
            "references": [
                {
                    "type": "index-pattern",
                    "id": dataview_id,
                    "name": dataview_id
                }
            ]
        }
    }
    return panel

# 3. Build Dashboard 1 (Executive Overview)
d1_panels = [
    # KPI 1: Service Health Status (Total requests count)
    make_lens_panel(
        0, 0, 12, 8, "kpi-health", "Service Health Status", "Liveness/Readiness status of services", "lnsMetric",
        {"col1": {"operationType": "count", "label": "Total Requests", "dataType": "number"}},
        ["col1"], {"accessor": "col1"}, "otel-traces-dataview"
    ),
    # KPI 2: Error Rate %
    make_lens_panel(
        12, 0, 12, 8, "kpi-error-rate", "Error Rate %", "Current system-wide error rate", "lnsMetric",
        {"col1": {"operationType": "count", "label": "Error Count", "dataType": "number", "filter": {"query": "http.response.status_code >= 500", "language": "kuery"}}},
        ["col1"], {"accessor": "col1"}, "otel-traces-dataview"
    ),
    # KPI 3: RPS
    make_lens_panel(
        24, 0, 12, 8, "kpi-rps", "Requests Per Second", "Current RPS", "lnsMetric",
        {"col1": {"operationType": "count", "label": "RPS", "dataType": "number", "timeScale": "s"}},
        ["col1"], {"accessor": "col1"}, "otel-traces-dataview"
    ),
    # KPI 4: Avg Latency
    make_lens_panel(
        36, 0, 12, 8, "kpi-latency", "Avg Latency (ms)", "Average response latency", "lnsMetric",
        {"col1": {"operationType": "average", "sourceField": "duration", "label": "Avg Latency", "dataType": "number"}},
        ["col1"], {"accessor": "col1"}, "otel-traces-dataview"
    ),
    # Chart 1: RPS over time
    make_lens_panel(
        0, 8, 24, 12, "rps-timeseries", "Request Rate (RPS) Over Time", "Time-series line chart of request throughput", "lnsXY",
        {
            "col-x": {"operationType": "date_histogram", "sourceField": "@timestamp", "params": {"interval": "auto"}},
            "col-y": {"operationType": "count", "label": "Requests", "timeScale": "s"}
        },
        ["col-x", "col-y"],
        {
            "layers": [{"layerId": "layer1", "layerType": "data", "seriesType": "line", "xAccessor": "col-x", "accessors": ["col-y"]}],
            "preferredSeriesType": "line"
        },
        "otel-traces-dataview"
    ),
    # Chart 2: Latency p95/p99 over time
    make_lens_panel(
        24, 8, 24, 12, "latency-timeseries", "Latency Over Time", "Response latency time-series", "lnsXY",
        {
            "col-x": {"operationType": "date_histogram", "sourceField": "@timestamp", "params": {"interval": "auto"}},
            "col-p95": {"operationType": "percentile", "sourceField": "duration", "params": {"percentile": 95}, "label": "p95 Latency"},
            "col-p99": {"operationType": "percentile", "sourceField": "duration", "params": {"percentile": 99}, "label": "p99 Latency"}
        },
        ["col-x", "col-p95", "col-p99"],
        {
            "layers": [{"layerId": "layer1", "layerType": "data", "seriesType": "line", "xAccessor": "col-x", "accessors": ["col-p95", "col-p99"]}],
            "preferredSeriesType": "line"
        },
        "otel-traces-dataview"
    ),
    # Chart 3: HTTP status code distribution
    make_lens_panel(
        0, 20, 48, 10, "error-distribution", "HTTP Status Code Distribution", "Distribution of 2xx, 4xx, 5xx responses over time", "lnsXY",
        {
            "col-x": {"operationType": "date_histogram", "sourceField": "@timestamp", "params": {"interval": "auto"}},
            "col-y": {"operationType": "count", "label": "Count"},
            "col-split": {"operationType": "terms", "sourceField": "http.response.status_code", "params": {"size": 10}}
        },
        ["col-split", "col-x", "col-y"],
        {
            "layers": [{"layerId": "layer1", "layerType": "data", "seriesType": "bar_stacked", "xAccessor": "col-x", "accessors": ["col-y"], "splitAccessor": "col-split"}],
            "preferredSeriesType": "bar_stacked"
        },
        "otel-traces-dataview"
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
        {"id": "otel-traces-dataview", "name": "otel-traces-dataview", "type": "index-pattern"}
    ]
}

# 4. Build Dashboard 2 (Developer Deep-Dive)
d2_panels = [
    # Table 1: Top 10 slowest endpoints
    make_lens_panel(
        0, 0, 24, 12, "slow-endpoints", "Top 10 Slowest Endpoints (by p95 Latency)", "API routes with highest p95 response time", "lnsDatatable",
        {
            "col-route": {"operationType": "terms", "sourceField": "url.path", "params": {"size": 10, "orderBy": {"columnId": "col-p95", "type": "column"}, "orderDirection": "desc"}, "label": "API Route"},
            "col-method": {"operationType": "terms", "sourceField": "http.request.method", "params": {"size": 5}, "label": "Method"},
            "col-p95": {"operationType": "percentile", "sourceField": "duration", "params": {"percentile": 95}, "label": "p95 Latency (ms)"},
            "col-max": {"operationType": "max", "sourceField": "duration", "label": "Max Latency (ms)"},
            "col-count": {"operationType": "count", "label": "Call Count"}
        },
        ["col-route", "col-method", "col-p95", "col-max", "col-count"],
        {
            "columns": [{"columnId": "col-route"}, {"columnId": "col-method"}, {"columnId": "col-p95"}, {"columnId": "col-max"}, {"columnId": "col-count"}]
        },
        "otel-traces-dataview"
    ),
    # Table 2: Top 10 error endpoints
    make_lens_panel(
        24, 0, 24, 12, "error-endpoints", "Top 10 Most Error-Prone Endpoints", "API routes with most 5xx errors", "lnsDatatable",
        {
            "col-route": {"operationType": "terms", "sourceField": "url.path", "params": {"size": 10, "orderBy": {"columnId": "col-errors", "type": "column"}, "orderDirection": "desc"}, "label": "API Route"},
            "col-errors": {"operationType": "count", "label": "Error Count"},
            "col-status": {"operationType": "terms", "sourceField": "http.response.status_code", "params": {"size": 5}, "label": "Status Codes"}
        },
        ["col-route", "col-errors", "col-status"],
        {
            "columns": [{"columnId": "col-route"}, {"columnId": "col-errors"}, {"columnId": "col-status"}]
        },
        "otel-traces-dataview"
    ),
    # Chart 1: Errors over time
    make_lens_panel(
        0, 12, 48, 8, "error-timeline", "Errors Over Time", "Timeline of errors by endpoint", "lnsXY",
        {
            "col-x": {"operationType": "date_histogram", "sourceField": "@timestamp", "params": {"interval": "auto"}},
            "col-y": {"operationType": "count", "label": "Errors"},
            "col-split": {"operationType": "terms", "sourceField": "url.path", "params": {"size": 5}}
        },
        ["col-split", "col-x", "col-y"],
        {
            "layers": [{"layerId": "layer1", "layerType": "data", "seriesType": "bar_stacked", "xAccessor": "col-x", "accessors": ["col-y"], "splitAccessor": "col-split"}],
            "preferredSeriesType": "bar_stacked"
        },
        "otel-traces-dataview"
    ),
    # Table 3: Log Stream (Filtered / Search by TraceId)
    make_lens_panel(
        0, 20, 48, 15, "log-stream", "Log Stream (Search by TraceId)", "Real-time log viewer with TraceId search capability", "lnsDatatable",
        {
            "col-time": {"operationType": "date_histogram", "sourceField": "@timestamp", "params": {"interval": "auto"}, "label": "Timestamp"},
            "col-level": {"operationType": "terms", "sourceField": "severity_text", "params": {"size": 5}, "label": "Level"},
            "col-count": {"operationType": "count", "label": "Count"}
        },
        ["col-time", "col-level", "col-count"],
        {
            "columns": [{"columnId": "col-time"}, {"columnId": "col-level"}, {"columnId": "col-count"}]
        },
        "otel-logs-dataview"
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
        {"id": "otel-traces-dataview", "name": "otel-traces-dataview", "type": "index-pattern"},
        {"id": "otel-logs-dataview", "name": "otel-logs-dataview", "type": "index-pattern"}
    ]
}

# 5. Build Dashboard 3 (Infrastructure & Runtime Performance)
d3_panels = [
    # Chart 1: ThreadPool Stats
    make_lens_panel(
        0, 0, 24, 12, "threadpool-stats", "ThreadPool Threads & Queue Length", "Active worker threads vs queue length", "lnsXY",
        {
            "col-x": {"operationType": "date_histogram", "sourceField": "@timestamp", "params": {"interval": "auto"}},
            "col-threads": {"operationType": "average", "sourceField": "metrics.process.runtime.dotnet.thread_pool.threads.count", "label": "Thread Count"},
            "col-queue": {"operationType": "average", "sourceField": "metrics.process.runtime.dotnet.thread_pool.queue.length", "label": "Queue Length"}
        },
        ["col-x", "col-threads", "col-queue"],
        {
            "layers": [{"layerId": "layer1", "layerType": "data", "seriesType": "line", "xAccessor": "col-x", "accessors": ["col-threads", "col-queue"]}],
            "preferredSeriesType": "line"
        },
        "otel-metrics-dataview"
    ),
    # Chart 2: GC Memory
    make_lens_panel(
        24, 0, 24, 12, "gc-memory", "GC Heap & Committed Memory", "Heap memory vs total committed memory", "lnsXY",
        {
            "col-x": {"operationType": "date_histogram", "sourceField": "@timestamp", "params": {"interval": "auto"}},
            "col-heap": {"operationType": "average", "sourceField": "metrics.process.runtime.dotnet.gc.heap.size", "label": "Heap Size (Bytes)"},
            "col-committed": {"operationType": "average", "sourceField": "metrics.process.runtime.dotnet.gc.committed_memory.size", "label": "Committed Memory (Bytes)"}
        },
        ["col-x", "col-heap", "col-committed"],
        {
            "layers": [{"layerId": "layer1", "layerType": "data", "seriesType": "line", "xAccessor": "col-x", "accessors": ["col-heap", "col-committed"]}],
            "preferredSeriesType": "line"
        },
        "otel-metrics-dataview"
    ),
    # Chart 3: GC Stats (Collections & Duration)
    make_lens_panel(
        0, 12, 24, 12, "gc-stats", "GC Collections & Pause Time", "GC collections frequency and pause duration", "lnsXY",
        {
            "col-x": {"operationType": "date_histogram", "sourceField": "@timestamp", "params": {"interval": "auto"}},
            "col-pause": {"operationType": "average", "sourceField": "metrics.process.runtime.dotnet.gc.duration", "label": "GC Pause Time (ms)"},
            "col-collections": {"operationType": "average", "sourceField": "metrics.process.runtime.dotnet.gc.collections.count", "label": "GC Collections"}
        },
        ["col-x", "col-pause", "col-collections"],
        {
            "layers": [{"layerId": "layer1", "layerType": "data", "seriesType": "line", "xAccessor": "col-x", "accessors": ["col-pause", "col-collections"]}],
            "preferredSeriesType": "line"
        },
        "otel-metrics-dataview"
    ),
    # Chart 4: Kestrel active connections vs exceptions
    make_lens_panel(
        24, 12, 24, 12, "kestrel-exceptions", "Kestrel Connections & Exceptions", "Active connections vs runtime exception count", "lnsXY",
        {
            "col-x": {"operationType": "date_histogram", "sourceField": "@timestamp", "params": {"interval": "auto"}},
            "col-conn": {"operationType": "average", "sourceField": "metrics.kestrel.active_connections", "label": "Active Connections"},
            "col-ex": {"operationType": "average", "sourceField": "metrics.process.runtime.dotnet.exceptions.count", "label": "Exceptions Count"}
        },
        ["col-x", "col-conn", "col-ex"],
        {
            "layers": [{"layerId": "layer1", "layerType": "data", "seriesType": "line", "xAccessor": "col-x", "accessors": ["col-conn", "col-ex"]}],
            "preferredSeriesType": "line"
        },
        "otel-metrics-dataview"
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
        {"id": "otel-metrics-dataview", "name": "otel-metrics-dataview", "type": "index-pattern"}
    ]
}

# 6. Write out the NDJSON file
print(f"Generating NDJSON file at: {ndjson_path}")
all_objects = [dashboard1, dashboard2, dashboard3]

with open(ndjson_path, 'w', encoding='utf-8') as f:
    for obj in all_objects:
        f.write(json.dumps(obj) + '\n')

print("Generating finished successfully!")

# 7. Execute curl import
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
