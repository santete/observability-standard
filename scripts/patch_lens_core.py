import sys

file_path = 'scripts/rebuild_dashboards.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add incompleteColumns
old_layers = '''                    layer_id: {
                        "columns": layers_columns,
                        "columnOrder": column_order
                    }'''
new_layers = '''                    layer_id: {
                        "columns": layers_columns,
                        "columnOrder": column_order,
                        "incompleteColumns": {}
                    }'''
content = content.replace(old_layers, new_layers)

# Add current-indexpattern reference
old_refs = '''                "references": [
                    {
                        "type": "index-pattern",
                        "id": dataview_id,
                        "name": dataview_ref_name
                    }
                ]'''
new_refs = '''                "references": [
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
                ]'''
content = content.replace(old_refs, new_refs)

# Fix lnsDatatable viz config to have "layers" instead of root layerId
# For dashboard 2 slow-endpoints and error-endpoints
old_dt_viz1 = '''        {
            "layerId": "layer1",
            "layerType": "data",
            "columns": [{"columnId": "col-route"}, {"columnId": "col-method"}, {"columnId": "col-p95"}, {"columnId": "col-max"}, {"columnId": "col-count"}]
        }'''
new_dt_viz1 = '''        {
            "layers": [{
                "layerId": "layer1",
                "layerType": "data",
                "columns": [{"columnId": "col-route"}, {"columnId": "col-method"}, {"columnId": "col-p95"}, {"columnId": "col-max"}, {"columnId": "col-count"}]
            }]
        }'''
content = content.replace(old_dt_viz1, new_dt_viz1)

old_dt_viz2 = '''        {
            "layerId": "layer1",
            "layerType": "data",
            "columns": [{"columnId": "col-route"}, {"columnId": "col-errors"}, {"columnId": "col-status"}]
        }'''
new_dt_viz2 = '''        {
            "layers": [{
                "layerId": "layer1",
                "layerType": "data",
                "columns": [{"columnId": "col-route"}, {"columnId": "col-errors"}, {"columnId": "col-status"}]
            }]
        }'''
content = content.replace(old_dt_viz2, new_dt_viz2)

old_dt_viz3 = '''        {
            "layerId": "logs",
            "layerType": "data",
            "columns": [{"columnId": "col-time"}, {"columnId": "col-level"}, {"columnId": "col-count"}]
        }'''
new_dt_viz3 = '''        {
            "layers": [{
                "layerId": "logs",
                "layerType": "data",
                "columns": [{"columnId": "col-time"}, {"columnId": "col-level"}, {"columnId": "col-count"}]
            }]
        }'''
content = content.replace(old_dt_viz3, new_dt_viz3)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Lens core patch applied.")
