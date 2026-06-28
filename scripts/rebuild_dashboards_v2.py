"""
rebuild_dashboards_v2.py
Complete rebuild using exact Kibana 8.17.0 format discovered from live panel inspection.

Key discoveries:
1. attributes must have `type: "lens"` field
2. state must have `internalReferences: []` and `adHocDataViews: {}`  
3. datasourceStates must have `textBased: {layers: {}}`
4. Dashboard references must use `panelIndex:name` format
5. lnsMetric uses flat viz config (no layers array), lnsXY/lnsDatatable use layers array
"""

import json
import urllib.request
import subprocess
import os
import time

script_dir = os.path.dirname(os.path.abspath(__file__))
ndjson_path = os.path.join(script_dir, '..', 'kibana', 'dashboards.ndjson')
ndjson_path = os.path.abspath(ndjson_path)

def kibana_request(path, method='GET', body=None):
    url = f"http://localhost:5601{path}"
    headers = {
        'kbn-xsrf': 'true',
        'Content-Type': 'application/json'
    }
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return json.loads(res.read().decode())
    except Exception as e:
        print(f"  [WARN] Request {method} {path} failed: {e}")
        return None

# ======================================================
# STEP 1: Setup data views
# ======================================================
print("Step 1: Setting up data views...")
for dv_id in ["otel-logs-dataview", "otel-traces-dataview", "otel-metrics-dataview"]:
    kibana_request(f"/api/data_views/data_view/{dv_id}", method="DELETE")

kibana_request("/api/data_views/data_view", method="POST", body={
    "data_view": {
        "id": "otel-logs-dataview",
        "title": ".ds-logs-generic.otel-*",
        "name": "OTel Logs",
        "timeFieldName": "@timestamp"
    }
})
kibana_request("/api/data_views/data_view", method="POST", body={
    "data_view": {
        "id": "otel-traces-dataview",
        "title": ".ds-traces-generic.otel-*",
        "name": "OTel Traces",
        "timeFieldName": "@timestamp"
    }
})
kibana_request("/api/data_views/data_view", method="POST", body={
    "data_view": {
        "id": "otel-metrics-dataview",
        "title": ".ds-metrics-generic.otel-*",
        "name": "OTel Metrics",
        "timeFieldName": "@timestamp"
    }
})
print("  Data views created.")

# ======================================================
# HELPER: Build a complete Lens state in the EXACT format
# that Kibana 8.17 expects
# ======================================================

def make_formBased_state(layers_columns, column_order, layer_id):
    """Build the formBased datasource state."""
    return {
        "formBased": {
            "layers": {
                layer_id: {
                    "columns": layers_columns,
                    "columnOrder": column_order,
                    "incompleteColumns": {}
                }
            }
        },
        "textBased": {
            "layers": {}
        }
    }

def make_lens_attributes(viz_type, viz_config, layers_columns, column_order, layer_id, dataview_id):
    """Build a complete Lens attributes object in the exact Kibana 8.17 format."""
    ref_name = f"indexpattern-datasource-layer-{layer_id}"
    return {
        "title": "",
        "visualizationType": viz_type,
        "type": "lens",
        "references": [{"type": "index-pattern", "id": dataview_id, "name": ref_name}],
        "state": {
            "visualization": viz_config,
            "query": {"query": "", "language": "kuery"},
            "filters": [],
            "datasourceStates": make_formBased_state(layers_columns, column_order, layer_id),
            "internalReferences": [],
            "adHocDataViews": {}
        }
    }

def make_panel(x, y, w, h, panel_index, title, viz_type, viz_config, layers_columns, column_order, layer_id, dataview_id):
    """Build a complete dashboard panel in the exact Kibana 8.17 format."""
    attrs = make_lens_attributes(viz_type, viz_config, layers_columns, column_order, layer_id, dataview_id)
    return {
        "type": "lens",
        "gridData": {"x": x, "y": y, "w": w, "h": h, "i": panel_index},
        "panelIndex": panel_index,
        "embeddableConfig": {
            "attributes": attrs,
            "enhancements": {},
            "type": "lens"
        },
        "title": title,
        "version": "8.17.0"
    }

def make_search_panel(x, y, w, h, panel_index, title, search_id):
    """Build a Saved Search dashboard panel."""
    return {
        "type": "search",
        "gridData": {"x": x, "y": y, "w": w, "h": h, "i": panel_index},
        "panelIndex": panel_index,
        "embeddableConfig": {
            "enhancements": {}
        },
        "title": title,
        "version": "8.17.0",
        "panelRefName": f"panel_{panel_index}",
        "savedObjectId": search_id
    }

# ======================================================
# STEP 2: Dashboard 1 - Executive Overview
# ======================================================
print("\nStep 2: Building Dashboard 1 - Executive Overview...")

# lnsMetric: flat format - layerId/layerType/metricAccessor at top level (NOT layers array)
# This is the correct format for Kibana 8.17 - layers[] format renders but shows NO numbers
def metric_viz(layer_id, accessor):
    return {
        "layerId": layer_id,
        "layerType": "data",
        "metricAccessor": accessor
    }

# lnsXY: layers array with seriesType, xAccessor, accessors
def xy_line_viz(layer_id, x_col, y_cols):
    return {
        "layers": [{
            "layerId": layer_id,
            "layerType": "data",
            "seriesType": "line",
            "xAccessor": x_col,
            "accessors": y_cols
        }],
        "preferredSeriesType": "line",
        "legend": {"isVisible": True, "position": "right"},
        "valueLabels": "hide",
        "fittingFunction": "None",
        "axisTitlesVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
        "gridlinesVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
        "tickLabelsVisibilitySettings": {"x": True, "yLeft": True, "yRight": True}
    }

def xy_bar_stacked_viz(layer_id, x_col, y_cols, split_col=None):
    layer = {
        "layerId": layer_id,
        "layerType": "data",
        "seriesType": "bar_stacked",
        "xAccessor": x_col,
        "accessors": y_cols
    }
    if split_col:
        layer["splitAccessor"] = split_col
    return {
        "layers": [layer],
        "preferredSeriesType": "bar_stacked",
        "legend": {"isVisible": True, "position": "right"},
        "valueLabels": "hide",
        "fittingFunction": "None",
        "axisTitlesVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
        "gridlinesVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
        "tickLabelsVisibilitySettings": {"x": True, "yLeft": True, "yRight": True}
    }

# lnsDatatable: layers array with columns list (NO sorting inside layer - it's top-level)
def datatable_viz(layer_id, col_ids, sort_col=None, sort_dir="desc"):
    layer = {
        "layerId": layer_id,
        "layerType": "data",
        "columns": [{"columnId": c, "hidden": False} for c in col_ids]
    }
    result = {
        "layers": [layer],
        "rowHeight": "single",
        "headerRowHeight": "single"
    }
    if sort_col:
        result["sorting"] = {"columnId": sort_col, "direction": sort_dir}
    return result

# Common column definitions
def col_count(label="Count", filter_query=None, emptyAsNull=True):
    col = {"label": label, "dataType": "number", "operationType": "count",
            "scale": "ratio", "isBucketed": False, "sourceField": "___records___",
            "params": {"emptyAsNull": emptyAsNull}}
    if filter_query:
        col["filter"] = {"query": filter_query, "language": "kuery"}
    return col

def col_unique_count(field, label="Unique Count", filter_query=None, emptyAsNull=False):
    col = {"label": label, "dataType": "number", "operationType": "unique_count",
            "scale": "ratio", "isBucketed": False, "sourceField": field,
            "params": {"emptyAsNull": emptyAsNull}}
    if filter_query:
        col["filter"] = {"query": filter_query, "language": "kuery"}
    return col

def col_count_errors(label="Error Count"):
    """Count of HTTP 4xx/5xx responses. emptyAsNull=False shows 0 (not N/A) when no errors."""
    return {
        "label": label,
        "dataType": "number",
        "operationType": "count",
        "scale": "ratio",
        "isBucketed": False,
        "sourceField": "___records___",
        "filter": {
            "query": "attributes.http.response.status_code >= 400",
            "language": "kuery"
        },
        "params": {"emptyAsNull": False}
    }

def col_avg(field, label="Avg"):
    return {"label": label, "dataType": "number", "operationType": "average",
            "scale": "ratio", "isBucketed": False, "sourceField": field,
            "params": {"emptyAsNull": False}}

def col_max(field, label="Max"):
    return {"label": label, "dataType": "number", "operationType": "max",
            "scale": "ratio", "isBucketed": False, "sourceField": field,
            "params": {"emptyAsNull": False}}

def col_percentile(field, pct, label=None):
    if not label:
        label = f"p{pct}"
    return {"label": label, "dataType": "number", "operationType": "percentile",
            "scale": "ratio", "isBucketed": False, "sourceField": field,
            "params": {"percentile": pct, "emptyAsNull": False}}

def col_date_histogram(label="@timestamp"):
    return {"label": label, "dataType": "date", "operationType": "date_histogram",
            "scale": "interval", "isBucketed": True, "sourceField": "@timestamp",
            "params": {"interval": "auto", "includeEmptyRows": True}}

def col_terms(field, size, label=None):
    if not label:
        label = field
    return {"label": label, "dataType": "string", "operationType": "terms",
            "scale": "ordinal", "isBucketed": True, "sourceField": field,
            "params": {"size": size, "orderBy": {"type": "alphabetical"}, "orderDirection": "asc", "otherBucket": True, "missingBucket": False}}

def col_last_values(field, size=10, label=None):
    if not label: label = field
    return {"label": label, "dataType": "string", "operationType": "last_values",
            "scale": "ordinal", "isBucketed": False, "sourceField": field,
            "params": {"size": size}}

# Removed complex RPS columns - using simple p95 latency instead

d1_panels = []

# KPI Panel 1: Total Requests (all spans/traces)
d1_panels.append(make_panel(
    0, 0, 12, 8, "kpi-health", "Total Requests",
    "lnsMetric",
    metric_viz("layer1", "col1"),
    {"col1": col_count("Total Requests")},
    ["col1"], "layer1", "otel-traces-dataview"
))

# KPI Panel 2: Error Count - uses filter on count to only count 4xx/5xx
d1_panels.append(make_panel(
    12, 0, 12, 8, "kpi-error-rate", "Error Count (4xx/5xx)",
    "lnsMetric",
    metric_viz("layer1", "col1"),
    {"col1": col_count_errors("Error Count")},
    ["col1"], "layer1", "otel-traces-dataview"
))

# KPI Panel 3: Max Latency (Worst-case)
d1_panels.append(make_panel(
    24, 0, 12, 8, "kpi-max-latency", "Max Latency (ms)",
    "lnsMetric",
    metric_viz("layer1", "col1"),
    {"col1": {"label": "Max Latency (ms)", "dataType": "number", "operationType": "max",
              "scale": "ratio", "isBucketed": False, "sourceField": "duration",
              "params": {"emptyAsNull": True}}},
    ["col1"], "layer1", "otel-traces-dataview"
))

# KPI Panel 4: Avg Latency
d1_panels.append(make_panel(
    36, 0, 12, 8, "kpi-latency", "Avg Latency (ms)",
    "lnsMetric",
    metric_viz("layer1", "col1"),
    {"col1": col_avg("duration", "Avg Latency (ms)")},
    ["col1"], "layer1", "otel-traces-dataview"
))

# RPS Time Series - lnsXY line
d1_panels.append(make_panel(
    0, 8, 24, 12, "rps-timeseries", "Request Rate (RPS) Over Time",
    "lnsXY",
    xy_line_viz("layer1", "col-x", ["col-y"]),
    {
        "col-x": col_date_histogram(),
        "col-y": col_count("Requests")
    },
    ["col-x", "col-y"], "layer1", "otel-traces-dataview"
))

# Latency Time Series - lnsXY line with p95/p99
d1_panels.append(make_panel(
    24, 8, 24, 12, "latency-timeseries", "Latency Over Time (p95 & p99)",
    "lnsXY",
    xy_line_viz("layer1", "col-x", ["col-p95", "col-p99"]),
    {
        "col-x": col_date_histogram(),
        "col-p95": col_percentile("duration", 95, "p95 Latency (ms)"),
        "col-p99": col_percentile("duration", 99, "p99 Latency (ms)")
    },
    ["col-x", "col-p95", "col-p99"], "layer1", "otel-traces-dataview"
))

# Error Distribution - lnsXY bar stacked by status code
d1_panels.append(make_panel(
    0, 20, 48, 10, "error-distribution", "HTTP Status Code Distribution",
    "lnsXY",
    xy_bar_stacked_viz("layer1", "col-x", ["col-y"], "col-split"),
    {
        "col-split": col_terms("attributes.http.response.status_code", 10, "Status Code"),
        "col-x": col_date_histogram(),
        "col-y": col_count("Count")
    },
    ["col-split", "col-x", "col-y"], "layer1", "otel-traces-dataview"
))

# Build dashboard-level references (panelIndex:name format)
def build_dashboard_refs(panels):
    refs = []
    seen = set()
    for p in panels:
        pi = p["panelIndex"]
        
        # 1. References for "by-value" panels (Lens)
        inner_refs = p.get("embeddableConfig", {}).get("attributes", {}).get("references", [])
        for r in inner_refs:
            key = (pi, r["name"])
            if key not in seen:
                seen.add(key)
                refs.append({
                    "id": r["id"],
                    "name": f"{pi}:{r['name']}",
                    "type": r["type"]
                })
        
        # 2. References for "by-reference" panels (Saved Search, etc.)
        if "savedObjectId" in p:
            # For Kibana 8.x, the reference name for the panel itself is usually panel_{panelIndex}
            ref_name = f"panel_{pi}"
            refs.append({
                "id": p["savedObjectId"],
                "name": f"{pi}:{ref_name}",
                "type": p["type"]
            })
            
    return refs

dashboard1 = {
    "id": "executive-overview-dashboard",
    "type": "dashboard",
    "migrationVersion": {"dashboard": "8.17.0"},
    "attributes": {
        "title": "[OBS] Executive Overview - System Health",
        "description": "High-level system health: KPI panels, RPS time-series, latency p95/p99, error distribution.",
        "panelsJSON": json.dumps(d1_panels),
        "timeRestore": True,
        "timeTo": "now",
        "timeFrom": "now-1h",
        "refreshInterval": {"pause": False, "value": 10000},
        "kibanaSavedObjectMeta": {"searchSourceJSON": '{"query":{"query":"","language":"kuery"},"filter":[]}'}
    },
    "references": build_dashboard_refs(d1_panels)
}

# ======================================================
# STEP 3: Dashboard 2 - Developer Deep-Dive
# ======================================================
print("Step 3: Building Dashboard 2 - Developer Deep-Dive...")
d2_panels = []

# 1. Recent Error Logs (Get TraceId here) - Saved Search
import json
recent_error_logs_search = {
    "id": "recent-error-logs-search",
    "type": "search",
    "attributes": {
        "title": "Recent Error Logs (Get TraceId Here)",
        "description": "",
        "hits": 0,
        "columns": ["@timestamp", "attributes.url.path", "trace_id", "body"],
        "sort": [["@timestamp", "desc"]],
        "kibanaSavedObjectMeta": {
            "searchSourceJSON": json.dumps({
                "query": {
                    "language": "kuery",
                    "query": "severity_text: \"Error\" OR severity_text: \"Warning\" OR severity_text: \"Critical\""
                },
                "filter": [],
                "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index"
            })
        }
    },
    "references": [
        {
            "name": "kibanaSavedObjectMeta.searchSourceJSON.index",
            "type": "index-pattern",
            "id": "otel-logs-dataview"
        }
    ]
}


# 1. Top 10 Slowest Endpoints - lnsXY horizontal bar
d2_panels.append(make_panel(
    0, 0, 24, 12, "slow-endpoints", "Top 10 Slowest Endpoints (p95 Latency)",
    "lnsXY",
    {
        "layers": [{
            "layerId": "layer1",
            "layerType": "data",
            "seriesType": "bar_horizontal",
            "xAccessor": "col-route",
            "accessors": ["col-p95"]
        }],
        "preferredSeriesType": "bar_horizontal",
        "legend": {"isVisible": True, "position": "right"},
        "valueLabels": "hide",
        "fittingFunction": "None",
        "axisTitlesVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
        "gridlinesVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
        "tickLabelsVisibilitySettings": {"x": True, "yLeft": True, "yRight": True}
    },
    {
        "col-route": col_terms("attributes.url.path", 10, "API Route"),
        "col-p95": col_percentile("duration", 95, "p95 Latency (ms)")
    },
    ["col-route", "col-p95"], "layer1", "otel-traces-dataview"
))

# Top 10 Most Error-Prone Endpoints - lnsXY horizontal bar (sorted by error count desc)
# Answers: Which endpoints have the most errors?
d2_panels.append(make_panel(
    24, 0, 24, 12, "error-endpoints", "Top 10 Most Error-Prone Endpoints",
    "lnsXY",
    {
        "layers": [{
            "layerId": "layer1",
            "layerType": "data",
            "seriesType": "bar_horizontal",
            "xAccessor": "col-route",
            "accessors": ["col-errors"]
        }],
        "preferredSeriesType": "bar_horizontal",
        "legend": {"isVisible": True, "position": "right"},
        "valueLabels": "hide",
        "fittingFunction": "None",
        "axisTitlesVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
        "gridlinesVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
        "tickLabelsVisibilitySettings": {"x": True, "yLeft": True, "yRight": True}
    },
    {
        "col-route": col_terms("attributes.url.path", 10, "API Route"),
        "col-errors": col_count("Error Count", filter_query="attributes.http.response.status_code >= 400")
    },
    ["col-route", "col-errors"], "layer1", "otel-traces-dataview"
))

# 4. Errors Over Time by Endpoint - lnsXY bar stacked
d2_panels.append(make_panel(
    0, 12, 48, 8, "error-timeline", "Errors Over Time by Endpoint",
    "lnsXY",
    xy_bar_stacked_viz("layer1", "col-x", ["col-y"], "col-split"),
    {
        "col-split": col_terms("attributes.url.path", 5, "Endpoint"),
        "col-x": col_date_histogram(),
        "col-y": col_count("Errors", filter_query="attributes.http.response.status_code >= 400")
    },
    ["col-split", "col-x", "col-y"], "layer1", "otel-traces-dataview"
))

# 5. Log Volume by Severity Over Time - lnsXY bar stacked
d2_panels.append(make_panel(
    0, 20, 48, 12, "log-stream", "Log Volume by Severity Level Over Time",
    "lnsXY",
    xy_bar_stacked_viz("logs", "col-x", ["col-y"], "col-split"),
    {
        "col-split": col_terms("severity_text", 5, "Severity Level"),
        "col-x": col_date_histogram(),
        "col-y": col_count("Log Count")
    },
    ["col-split", "col-x", "col-y"], "logs", "otel-logs-dataview"
))

# Recent Error Logs - Saved Search (bottom)
d2_panels.append(make_search_panel(
    0, 32, 48, 16, "recent-error-logs", "Recent Error Logs (Copy TraceId Here)",
    "recent-error-logs-search"
))

dashboard2 = {
    "id": "developer-deepdive-dashboard",
    "type": "dashboard",
    "migrationVersion": {"dashboard": "8.17.0"},
    "attributes": {
        "title": "[OBS] Developer Deep-Dive - Debug & Optimize",
        "description": "Developer-focused: slowest endpoints, error-prone endpoints, error timeline, log stream.",
        "panelsJSON": json.dumps(d2_panels),
        "timeRestore": True,
        "timeTo": "now",
        "timeFrom": "now-1h",
        "refreshInterval": {"pause": False, "value": 10000},
        "kibanaSavedObjectMeta": {"searchSourceJSON": '{"query":{"query":"","language":"kuery"},"filter":[]}'}
    },
    "references": build_dashboard_refs(d2_panels)
}

# ======================================================
# STEP 4: Dashboard 3 - Infrastructure & Runtime
# ======================================================
print("Step 4: Building Dashboard 3 - Infrastructure & Runtime...")

d3_panels = []

# Panel 1: Resource Usage (CPU & RAM)
d3_panels.append(make_panel(
    0, 12, 24, 12, "resource-usage", "Resource Usage (CPU & RAM)",
    "lnsXY",
    xy_line_viz("layer1", "col-x", ["col-cpu", "col-ram"]),
    {
        "col-x": col_date_histogram(),
        "col-cpu": col_avg("metrics.process.cpu.utilization", "CPU Utilization (%)"),
        "col-ram": col_avg("metrics.process.memory.usage", "Memory Usage (Bytes)")
    },
    ["col-x", "col-cpu", "col-ram"], "layer1", "otel-metrics-dataview"
))

# Panel 2: ThreadPool Starvation Monitors
d3_panels.append(make_panel(
    0, 0, 24, 12, "threadpool-stats", "ThreadPool Starvation Monitors",
    "lnsXY",
    xy_line_viz("layer1", "col-x", ["col-threads", "col-queue"]),
    {
        "col-x": col_date_histogram(),
        "col-threads": col_avg("metrics.process.runtime.dotnet.thread_pool.threads.count", "Active Threads"),
        "col-queue": col_avg("metrics.process.runtime.dotnet.thread_pool.queue.length", "Queue Length")
    },
    ["col-x", "col-threads", "col-queue"], "layer1", "otel-metrics-dataview"
))

# Panel 3: Garbage Collection (GC) Stats
d3_panels.append(make_panel(
    24, 0, 24, 12, "gc-stats", "Garbage Collection (Pause Time & Heap)",
    "lnsXY",
    xy_line_viz("layer1", "col-x", ["col-pause", "col-heap"]),
    {
        "col-x": col_date_histogram(),
        "col-pause": col_avg("metrics.process.runtime.dotnet.gc.duration", "GC Pause Time (ms)"),
        "col-heap": col_avg("metrics.process.runtime.dotnet.gc.heap.size", "Heap Size (Bytes)")
    },
    ["col-x", "col-pause", "col-heap"], "layer1", "otel-metrics-dataview"
))

# Panel 4: Network & Disk I/O
d3_panels.append(make_panel(
    24, 12, 24, 12, "io-stats", "Network & Disk I/O",
    "lnsXY",
    xy_line_viz("layer1", "col-x", ["col-net", "col-disk"]),
    {
        "col-x": col_date_histogram(),
        "col-net": col_avg("metrics.system.network.io.bytes", "Network I/O (Bytes)"),
        "col-disk": col_avg("metrics.system.disk.io.bytes", "Disk I/O (Bytes)")
    },
    ["col-x", "col-net", "col-disk"], "layer1", "otel-metrics-dataview"
))

dashboard3 = {
    "id": "infrastructure-runtime-dashboard",
    "type": "dashboard",
    "migrationVersion": {"dashboard": "8.17.0"},
    "attributes": {
        "title": "[OBS] Infrastructure & Runtime Performance",
        "description": "System resources: ThreadPool, GC Heap, GC Collections, Kestrel Connections.",
        "panelsJSON": json.dumps(d3_panels),
        "timeRestore": True,
        "timeTo": "now",
        "timeFrom": "now-1h",
        "refreshInterval": {"pause": False, "value": 10000},
        "kibanaSavedObjectMeta": {"searchSourceJSON": '{"query":{"query":"","language":"kuery"},"filter":[]}'}
    },
    "references": build_dashboard_refs(d3_panels)
}

# ======================================================
# STEP 4.5: Dashboard 4 - QA Compliance Tracker
# ======================================================
print("Step 4.5: Building Dashboard 4 - QA Compliance Tracker...")

d4_panels = []

# Total Compliant Services - Unique Count of Service Names
d4_panels.append(make_panel(
    0, 0, 12, 12, "qa-compliant-services", "Total Active Compliant Services (Unique)",
    "lnsMetric",
    metric_viz("layer1", "col1"),
    {"col1": col_unique_count("service.name", "Compliant Services", filter_query="message: \"[Compliance=True]\" OR body: \"[Compliance=True]\"", emptyAsNull=False)},
    ["col1"], "layer1", "otel-logs-dataview"
))

# Audit Log Distribution - lnsXY Bar Stacked
d4_panels.append(make_panel(
    12, 0, 36, 12, "qa-audit-log", "SDK Initialization by Service Over Time",
    "lnsXY",
    xy_bar_stacked_viz("layer1", "col-x", ["col-y"], "col-split"),
    {
        "col-split": col_terms("service.name", 10, "Service Name"),
        "col-x": col_date_histogram("Time"),
        "col-y": col_count("SDK Starts", filter_query="message: \"[Compliance=True]\" OR body: \"[Compliance=True]\"")
    },
    ["col-split", "col-x", "col-y"], "layer1", "otel-logs-dataview"
))

dashboard4 = {
    "id": "qa-compliance-dashboard",
    "type": "dashboard",
    "migrationVersion": {"dashboard": "8.17.0"},
    "attributes": {
        "title": "[OBS] QA Compliance Tracker",
        "description": "Tracks which services have successfully integrated the Standard Observability SDK.",
        "panelsJSON": json.dumps(d4_panels),
        "timeRestore": True,
        "timeTo": "now",
        "timeFrom": "now-24h",
        "refreshInterval": {"pause": False, "value": 10000},
        "kibanaSavedObjectMeta": {"searchSourceJSON": '{"query":{"query":"","language":"kuery"},"filter":[]}'}
    },
    "references": build_dashboard_refs(d4_panels)
}

# ======================================================
# STEP 5: Write NDJSON and import
# ======================================================
print(f"\nStep 5: Writing NDJSON to {ndjson_path}...")
dashboard_objects = [dashboard1, dashboard2, dashboard3, dashboard4, recent_error_logs_search]

with open(ndjson_path, 'w', encoding='utf-8') as f:
    for obj in dashboard_objects:
        f.write(json.dumps(obj) + '\n')

print("NDJSON written successfully.")

# Import via curl
cmd = [
    'curl.exe', '-X', 'POST',
    'http://localhost:5601/api/saved_objects/_import?overwrite=true',
    '-H', 'kbn-xsrf: true',
    '-F', f'file=@{ndjson_path}'
]

print("Importing dashboards into Kibana...")
try:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
    resp = json.loads(result.stdout)
    print(f"  Success: {resp.get('successCount', 0)} objects imported")
    errors = resp.get('errors', [])
    if errors:
        print(f"  Errors: {len(errors)}")
        for e in errors:
            print(f"    - {e}")
    else:
        print("  No import errors!")
except Exception as e:
    print(f"  Import failed: {e}")

# ======================================================
# STEP 6: Playwright verification
# ======================================================
print("\nStep 6: Running Playwright verification...")
artifact_dir = r"C:\Users\nangh\.gemini\antigravity\brain\ebba6e7b-5d89-46c8-bb3c-76a747786481"

from playwright.sync_api import sync_playwright

dashboards_to_test = [
    ("executive-overview-dashboard", "executive_overview_v2.png"),
    ("developer-deepdive-dashboard", "developer_deepdive_v2.png"),
    ("infrastructure-runtime-dashboard", "infrastructure_runtime_v2.png"),
    ("qa-compliance-dashboard", "qa_compliance_dashboard.png")
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    
    for db_id, filename in dashboards_to_test:
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        url = f"http://localhost:5601/app/dashboards#/view/{db_id}"
        print(f"\n  Loading {db_id}...")
        page.goto(url)
        page.wait_for_timeout(18000)  # Wait 18s for data to render
        
        screenshot_out = os.path.join(artifact_dir, filename)
        page.screenshot(path=screenshot_out, full_page=False)
        print(f"  Screenshot: {screenshot_out}")
        
        # Check for errors
        errors = page.eval_on_selector_all(
            "p, div, span",
            "els => els.map(el => el.innerText).filter(t => t && (t.includes('Cannot read properties') || t.includes('visualization error') || t.includes('Error loading')))"
        )
        unique_errors = list(set(e.strip() for e in errors if e.strip()))
        
        if unique_errors:
            print(f"  [FAIL] ERRORS in {db_id}:")
            for err in unique_errors[:5]:
                print(f"    - {err[:150]}")
        else:
            print(f"  [PASS] {db_id}: ZERO ERRORS!")
        
        page.close()
    
    browser.close()

print("\nAll verifications complete.")
