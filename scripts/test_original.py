import json
import subprocess
import os
import time

script_dir = os.path.dirname(os.path.abspath(__file__))
artifact_dir = r"C:\Users\nangh\.gemini\antigravity\brain\ebba6e7b-5d89-46c8-bb3c-76a747786481"
screenshot_path = os.path.join(artifact_dir, "kibana_original_test.png")

# Let's restore the original executive-overview-dashboard from the original spec/file but with migrationVersion
original_dashboard_json = {
    "id": "executive-overview-dashboard",
    "type": "dashboard",
    "migrationVersion": {"dashboard": "8.17.0"},
    "attributes": {
        "title": "[OBS] Executive Overview - System Health",
        "description": "High-level system health overview. KPI panels, RPS time-series, latency p95/p99, and error distribution. Spec Section 5 - Screen 1.",
        "panelsJSON": '[{"version":"8.17.0","type":"lens","gridData":{"x":0,"y":0,"w":12,"h":8,"i":"kpi-health"},"panelIndex":"kpi-health","embeddableConfig":{"title":"Service Health Status","description":"Liveness/Readiness status of services","attributes":{"visualizationType":"lnsMetric","state":{"datasourceStates":{"formBased":{"layers":{"layer1":{"columns":{"col1":{"operationType":"count","label":"Total Requests","dataType":"number"}},"columnOrder":["col1"]}}}},"visualization":{"layerId":"layer1","accessor":"col1","layerType":"data"}},"references":[{"type":"index-pattern","id":"otel-traces-dataview","name":"indexpattern-datasource-layer-layer1"}]}},{"version":"8.17.0","type":"lens","gridData":{"x":12,"y":0,"w":12,"h":8,"i":"kpi-error-rate"},"panelIndex":"kpi-error-rate","embeddableConfig":{"title":"Error Rate %","description":"Current system-wide error rate","attributes":{"visualizationType":"lnsMetric","state":{"datasourceStates":{"formBased":{"layers":{"layer1":{"columns":{"col1":{"operationType":"count","label":"Error Count","dataType":"number","filter":{"query":"http.response.status_code >= 500","language":"kuery"}}},"columnOrder":["col1"]}}}},"visualization":{"layerId":"layer1","accessor":"col1","layerType":"data"}},"references":[{"type":"index-pattern","id":"otel-traces-dataview","name":"indexpattern-datasource-layer-layer1"}]}},{"version":"8.17.0","type":"lens","gridData":{"x":24,"y":0,"w":12,"h":8,"i":"kpi-rps"},"panelIndex":"kpi-rps","embeddableConfig":{"title":"Requests Per Second","description":"Current RPS","attributes":{"visualizationType":"lnsMetric","state":{"datasourceStates":{"formBased":{"layers":{"layer1":{"columns":{"col1":{"operationType":"count","label":"RPS","dataType":"number","timeScale":"s"}},"columnOrder":["col1"]}}}},"visualization":{"layerId":"layer1","accessor":"col1","layerType":"data"}},"references":[{"type":"index-pattern","id":"otel-traces-dataview","name":"indexpattern-datasource-layer-layer1"}]}},{"version":"8.17.0","type":"lens","gridData":{"x":36,"y":0,"w":12,"h":8,"i":"kpi-latency"},"panelIndex":"kpi-latency","embeddableConfig":{"title":"Avg Latency (ms)","description":"Average response latency","attributes":{"visualizationType":"lnsMetric","state":{"datasourceStates":{"formBased":{"layers":{"layer1":{"columns":{"col1":{"operationType":"average","sourceField":"duration","label":"Avg Latency","dataType":"number"}},"columnOrder":["col1"]}}}},"visualization":{"layerId":"layer1","accessor":"col1","layerType":"data"}},"references":[{"type":"index-pattern","id":"otel-traces-dataview","name":"indexpattern-datasource-layer-layer1"}]}},{"version":"8.17.0","type":"lens","gridData":{"x":0,"y":8,"w":24,"h":12,"i":"rps-timeseries"},"panelIndex":"rps-timeseries","embeddableConfig":{"title":"Request Rate (RPS) Over Time","description":"Time-series line chart of request throughput","attributes":{"visualizationType":"lnsXY","state":{"datasourceStates":{"formBased":{"layers":{"layer1":{"columns":{"col-x":{"operationType":"date_histogram","sourceField":"@timestamp","params":{"interval":"auto"}},"col-y":{"operationType":"count","label":"Requests","timeScale":"s"}},"columnOrder":["col-x","col-y"]}}}},"visualization":{"layers":[{"layerId":"layer1","layerType":"data","seriesType":"line","xAccessor":"col-x","accessors":["col-y"]}],"preferredSeriesType":"line"}},"references":[{"type":"index-pattern","id":"otel-traces-dataview","name":"indexpattern-datasource-layer-layer1"}]}},{"version":"8.17.0","type":"lens","gridData":{"x":24,"y":8,"w":24,"h":12,"i":"latency-timeseries"},"panelIndex":"latency-timeseries","embeddableConfig":{"title":"Latency Over Time","description":"Response latency time-series","attributes":{"visualizationType":"lnsXY","state":{"datasourceStates":{"formBased":{"layers":{"layer1":{"columns":{"col-x":{"operationType":"date_histogram","sourceField":"@timestamp","params":{"interval":"auto"}},"col-p95":{"operationType":"percentile","sourceField":"duration","params":{"percentile":95},"label":"p95 Latency"},"col-p99":{"operationType":"percentile","sourceField":"duration","params":{"percentile":99},"label":"p99 Latency"}},"columnOrder":["col-x","col-p95","col-p99"]}}}},"visualization":{"layers":[{"layerId":"layer1","layerType":"data","seriesType":"line","xAccessor":"col-x","accessors":["col-p95","col-p99"]}],"preferredSeriesType":"line"}},"references":[{"type":"index-pattern","id":"otel-traces-dataview","name":"indexpattern-datasource-layer-layer1"}]}},{"version":"8.17.0","type":"lens","gridData":{"x":0,"y":20,"w":48,"h":10,"i":"error-distribution"},"panelIndex":"error-distribution","embeddableConfig":{"title":"HTTP Status Code Distribution","description":"Distribution of 2xx, 4xx, 5xx responses over time","attributes":{"visualizationType":"lnsXY","state":{"datasourceStates":{"formBased":{"layers":{"layer1":{"columns":{"col-x":{"operationType":"date_histogram","sourceField":"@timestamp","params":{"interval":"auto"}},"col-y":{"operationType":"count","label":"Count"},"col-split":{"operationType":"terms","sourceField":"http.response.status_code","params":{"size":10}}},"columnOrder":["col-split","col-x","col-y"]}}}},"visualization":{"layers":[{"layerId":"layer1","layerType":"data","seriesType":"bar_stacked","xAccessor":"col-x","accessors":["col-y"],"splitAccessor":"col-split"}],"preferredSeriesType":"bar_stacked"}},"references":[{"type":"index-pattern","id":"otel-traces-dataview","name":"indexpattern-datasource-layer-layer1"}]}}]',
        "timeRestore": True,
        "timeTo": "now",
        "timeFrom": "now-1h",
        "refreshInterval": {"pause": False, "value": 10000},
        "kibanaSavedObjectMeta": {"searchSourceJSON": "{\"query\":{\"query\":\"\",\"language\":\"kuery\"},\"filter\":[]}"}
    },
    "references": [
        {"id": "otel-traces-dataview", "name": "indexpattern-datasource-layer-layer1", "type": "index-pattern"}
    ]
}

# Write temporary ndjson
temp_ndjson = os.path.join(script_dir, "temp_original.ndjson")
with open(temp_ndjson, "w", encoding="utf-8") as f:
    f.write(json.dumps(original_dashboard_json) + "\n")

# Import it
cmd = [
    'curl.exe', '-X', 'POST',
    'http://localhost:5601/api/saved_objects/_import?overwrite=true',
    '-H', 'kbn-xsrf: true',
    '-F', f'file=@{temp_ndjson}'
]
print("Importing original format dashboard...")
subprocess.run(cmd, check=True)
os.remove(temp_ndjson)

# Run Playwright to check UI
print("Running Playwright verification on original format...")
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    page.goto("http://localhost:5601/app/dashboards#/view/executive-overview-dashboard")
    print("Waiting 15 seconds...")
    time.sleep(15)
    page.screenshot(path=screenshot_path)
    print("Screenshot saved to:", screenshot_path)
    
    # Check errors
    errors = page.eval_on_selector_all(
        "p, div", 
        "elements => elements.map(el => el.innerText).filter(text => text && text.includes('Cannot read properties'))"
    )
    if errors:
        print("\n--- ERRORS FOUND IN ORIGINAL FORMAT ---")
        for err in set(errors):
            print(f"- {err}")
    else:
        print("\n--- ORIGINAL FORMAT WORKS PERFECTLY! NO ERRORS ---")
        
    browser.close()
