import re

file_path = 'scripts/rebuild_dashboards.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Dashboard 1 references
content = content.replace(
    '''    "references": [
        {"id": "otel-traces-dataview", "name": "indexpattern-datasource-layer-layer1", "type": "index-pattern"},
        {"id": "otel-metrics-dataview", "name": "indexpattern-datasource-layer-layer1", "type": "index-pattern"}
    ]''',
    '''    "references": [
        {"id": "otel-traces-dataview", "name": "indexpattern-datasource-layer-layer1", "type": "index-pattern"},
        {"id": "otel-metrics-dataview", "name": "indexpattern-datasource-layer-layer1", "type": "index-pattern"},
        {"id": "otel-traces-dataview", "name": "indexpattern-datasource-current-indexpattern", "type": "index-pattern"}
    ]'''
)

# Dashboard 2 references
content = content.replace(
    '''    "references": [
        {"id": "otel-traces-dataview", "name": "indexpattern-datasource-layer-layer1", "type": "index-pattern"},
        {"id": "otel-logs-dataview", "name": "indexpattern-datasource-layer-logs", "type": "index-pattern"}
    ]''',
    '''    "references": [
        {"id": "otel-traces-dataview", "name": "indexpattern-datasource-layer-layer1", "type": "index-pattern"},
        {"id": "otel-logs-dataview", "name": "indexpattern-datasource-layer-logs", "type": "index-pattern"},
        {"id": "otel-traces-dataview", "name": "indexpattern-datasource-current-indexpattern", "type": "index-pattern"}
    ]'''
)

# Dashboard 3 references
content = content.replace(
    '''    "references": [
        {"id": "otel-metrics-dataview", "name": "indexpattern-datasource-layer-layer1", "type": "index-pattern"}
    ]''',
    '''    "references": [
        {"id": "otel-metrics-dataview", "name": "indexpattern-datasource-layer-layer1", "type": "index-pattern"},
        {"id": "otel-metrics-dataview", "name": "indexpattern-datasource-current-indexpattern", "type": "index-pattern"}
    ]'''
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched dashboard references successfully.")
