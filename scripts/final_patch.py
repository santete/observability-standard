import sys

file_path = 'scripts/rebuild_dashboards.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Restore attributes. prefix for Dashboard 1 and 2
content = content.replace('"sourceField": "http.response.status_code"', '"sourceField": "attributes.http.response.status_code"')
content = content.replace('"sourceField": "url.path"', '"sourceField": "attributes.url.path"')
content = content.replace('"sourceField": "http.request.method"', '"sourceField": "attributes.http.request.method"')

# Restore metrics. prefix for Dashboard 3
content = content.replace('"sourceField": "process.runtime', '"sourceField": "metrics.process.runtime')
content = content.replace('"sourceField": "kestrel.active_connections"', '"sourceField": "metrics.kestrel.active_connections"')

# Restore severity_text for logs
content = content.replace('"sourceField": "log.level"', '"sourceField": "severity_text"')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Final patch applied successfully.")
