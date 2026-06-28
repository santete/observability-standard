import sys

file_path = 'scripts/rebuild_dashboards.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix dashboard 1 params
content = content.replace(
    '"col-x": {"operationType": "date_histogram", "sourceField": "@timestamp"}',
    '"col-x": {"operationType": "date_histogram", "sourceField": "@timestamp", "params": {"interval": "auto"}}'
)
content = content.replace(
    '"col-p95": {"operationType": "percentile", "sourceField": "duration", "label": "p95 Latency", "dataType": "number"}',
    '"col-p95": {"operationType": "percentile", "sourceField": "duration", "params": {"percentile": 95}, "label": "p95 Latency", "dataType": "number"}'
)
content = content.replace(
    '"col-p99": {"operationType": "percentile", "sourceField": "duration", "label": "p99 Latency", "dataType": "number"}',
    '"col-p99": {"operationType": "percentile", "sourceField": "duration", "params": {"percentile": 99}, "label": "p99 Latency", "dataType": "number"}'
)
content = content.replace(
    '"col-split": {"operationType": "terms", "sourceField": "http.response.status_code", "dataType": "string"}',
    '"col-split": {"operationType": "terms", "sourceField": "http.response.status_code", "params": {"size": 10}, "dataType": "string"}'
)

# Fix dashboard 2 params
content = content.replace(
    '"col-route": {"operationType": "terms", "sourceField": "url.path", "dataType": "string", "label": "API Route"}',
    '"col-route": {"operationType": "terms", "sourceField": "url.path", "params": {"size": 10}, "dataType": "string", "label": "API Route"}'
)
content = content.replace(
    '"col-method": {"operationType": "terms", "sourceField": "http.request.method", "dataType": "string", "label": "Method"}',
    '"col-method": {"operationType": "terms", "sourceField": "http.request.method", "params": {"size": 5}, "dataType": "string", "label": "Method"}'
)
content = content.replace(
    '"col-p95": {"operationType": "percentile", "sourceField": "duration", "dataType": "number", "label": "p95 Latency (ms)"}',
    '"col-p95": {"operationType": "percentile", "sourceField": "duration", "params": {"percentile": 95}, "dataType": "number", "label": "p95 Latency (ms)"}'
)
content = content.replace(
    '"col-status": {"operationType": "terms", "sourceField": "http.response.status_code", "dataType": "string", "label": "Status Codes"}',
    '"col-status": {"operationType": "terms", "sourceField": "http.response.status_code", "params": {"size": 5}, "dataType": "string", "label": "Status Codes"}'
)
content = content.replace(
    '"col-split": {"operationType": "terms", "sourceField": "url.path", "dataType": "string"}',
    '"col-split": {"operationType": "terms", "sourceField": "url.path", "params": {"size": 5}, "dataType": "string"}'
)

# Fix log severity
content = content.replace(
    '"col-level": {"operationType": "terms", "sourceField": "severity_text"',
    '"col-level": {"operationType": "terms", "sourceField": "log.level"'
)

# Fix dashboard 3 metrics prefix
content = content.replace('"sourceField": "metrics.', '"sourceField": "')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch applied successfully.")
