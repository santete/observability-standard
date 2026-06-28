import sys

file_path = 'scripts/rebuild_dashboards.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Clean up existing random definitions
content = content.replace(', "dataType": "date", "scale": "interval", "isBucketed": True', '')
content = content.replace(', "dataType": "number", "scale": "ratio", "isBucketed": False', '')
content = content.replace(', "dataType": "string", "scale": "ordinal", "isBucketed": True', '')
content = content.replace('"dataType": "number", ', '')
content = content.replace('"dataType": "string", ', '')
content = content.replace('"dataType": "date", ', '')
content = content.replace(', "dataType": "number"', '')
content = content.replace(', "dataType": "string"', '')
content = content.replace(', "dataType": "date"', '')
content = content.replace(', "scale": "ratio"', '')
content = content.replace(', "scale": "interval"', '')
content = content.replace(', "scale": "ordinal"', '')
content = content.replace(', "isBucketed": False', '')
content = content.replace(', "isBucketed": True', '')

# Inject exactly after operationType
content = content.replace(
    '"operationType": "date_histogram"',
    '"operationType": "date_histogram", "isBucketed": True, "scale": "interval", "dataType": "date"'
)

content = content.replace(
    '"operationType": "terms"',
    '"operationType": "terms", "isBucketed": True, "scale": "ordinal", "dataType": "string"'
)

content = content.replace(
    '"operationType": "count"',
    '"operationType": "count", "isBucketed": False, "scale": "ratio", "dataType": "number"'
)

content = content.replace(
    '"operationType": "average"',
    '"operationType": "average", "isBucketed": False, "scale": "ratio", "dataType": "number"'
)

content = content.replace(
    '"operationType": "percentile"',
    '"operationType": "percentile", "isBucketed": False, "scale": "ratio", "dataType": "number"'
)

content = content.replace(
    '"operationType": "max"',
    '"operationType": "max", "isBucketed": False, "scale": "ratio", "dataType": "number"'
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Bucketed patch applied successfully.")
