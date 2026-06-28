import re

file_path = 'scripts/rebuild_dashboards.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Dashboard 1 - rps-timeseries
content = content.replace(
    '''            "col-x": {"operationType": "date_histogram", "isBucketed": True, "scale": "interval", "dataType": "date", "sourceField": "@timestamp", "params": {"interval": "auto"}}
        },
        ["col-x", "col-y"],''',
    '''            "col-x": {"operationType": "date_histogram", "isBucketed": True, "scale": "interval", "dataType": "date", "sourceField": "@timestamp", "params": {"interval": "auto"}},
            "col-y": {"operationType": "count", "isBucketed": False, "scale": "ratio", "dataType": "number", "label": "RPS"}
        },
        ["col-x", "col-y"],'''
)

# Dashboard 1 - latency-timeseries
content = content.replace(
    '''            "col-p99": {"operationType": "percentile", "isBucketed": False, "scale": "ratio", "dataType": "number", "sourceField": "duration", "params": {"percentile": 99}, "label": "p99 Latency", "dataType": "number"}
        },
        ["col-x", "col-p95", "col-p99", "col-avg"],''',
    '''            "col-p99": {"operationType": "percentile", "isBucketed": False, "scale": "ratio", "dataType": "number", "sourceField": "duration", "params": {"percentile": 99}, "label": "p99 Latency"},
            "col-avg": {"operationType": "average", "isBucketed": False, "scale": "ratio", "dataType": "number", "sourceField": "duration", "label": "Avg Latency"}
        },
        ["col-x", "col-p95", "col-p99", "col-avg"],'''
)

# Dashboard 1 - error-distribution
content = content.replace(
    '''            "col-split": {"operationType": "terms", "isBucketed": True, "scale": "ordinal", "dataType": "string", "sourceField": "attributes.http.response.status_code", "params": {"size": 10}, "dataType": "string"}
        },
        ["col-split", "col-x", "col-y"],''',
    '''            "col-split": {"operationType": "terms", "isBucketed": True, "scale": "ordinal", "dataType": "string", "sourceField": "attributes.http.response.status_code", "params": {"size": 10}},
            "col-y": {"operationType": "count", "isBucketed": False, "scale": "ratio", "dataType": "number", "label": "Count"}
        },
        ["col-split", "col-x", "col-y"],'''
)

# Dashboard 2 - slow-endpoints
content = content.replace(
    '''            "col-p95": {"operationType": "percentile", "isBucketed": False, "scale": "ratio", "dataType": "number", "sourceField": "duration", "params": {"percentile": 95}, "dataType": "number", "label": "p95 Latency (ms)"}
        },
        ["col-route", "col-method", "col-p95", "col-max", "col-count"],''',
    '''            "col-p95": {"operationType": "percentile", "isBucketed": False, "scale": "ratio", "dataType": "number", "sourceField": "duration", "params": {"percentile": 95}, "label": "p95 Latency (ms)"},
            "col-max": {"operationType": "max", "isBucketed": False, "scale": "ratio", "dataType": "number", "sourceField": "duration", "label": "Max Latency"},
            "col-count": {"operationType": "count", "isBucketed": False, "scale": "ratio", "dataType": "number", "label": "Requests"}
        },
        ["col-route", "col-method", "col-p95", "col-max", "col-count"],'''
)

# Dashboard 2 - error-endpoints
content = content.replace(
    '''            "col-status": {"operationType": "terms", "isBucketed": True, "scale": "ordinal", "dataType": "string", "sourceField": "attributes.http.response.status_code", "params": {"size": 5}, "dataType": "string", "label": "Status Codes"}
        },
        ["col-route", "col-errors", "col-status"],''',
    '''            "col-status": {"operationType": "terms", "isBucketed": True, "scale": "ordinal", "dataType": "string", "sourceField": "attributes.http.response.status_code", "params": {"size": 5}, "label": "Status Codes"},
            "col-errors": {"operationType": "count", "isBucketed": False, "scale": "ratio", "dataType": "number", "label": "Error Count"}
        },
        ["col-route", "col-errors", "col-status"],'''
)

# Dashboard 2 - error-timeline
content = content.replace(
    '''            "col-split": {"operationType": "terms", "isBucketed": True, "scale": "ordinal", "dataType": "string", "sourceField": "attributes.url.path", "params": {"size": 5}, "dataType": "string"}
        },
        ["col-split", "col-x", "col-y"],''',
    '''            "col-split": {"operationType": "terms", "isBucketed": True, "scale": "ordinal", "dataType": "string", "sourceField": "attributes.url.path", "params": {"size": 5}},
            "col-y": {"operationType": "count", "isBucketed": False, "scale": "ratio", "dataType": "number", "label": "Errors"}
        },
        ["col-split", "col-x", "col-y"],'''
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Restored missing columns successfully.")
