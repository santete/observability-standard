import re

file_path = 'scripts/rebuild_dashboards.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Define patterns to add isBucketed, scale, dataType based on operationType
# Find all column dicts: "col-...": {"operationType": "...", ...}
def replacer(match):
    col_def = match.group(0)
    
    # Determine what to inject
    if '"operationType": "date_histogram"' in col_def:
        if '"isBucketed"' not in col_def: col_def = col_def.replace('}', ', "isBucketed": True}')
        if '"scale"' not in col_def: col_def = col_def.replace('}', ', "scale": "interval"}')
        if '"dataType"' not in col_def: col_def = col_def.replace('}', ', "dataType": "date"}')
    elif '"operationType": "terms"' in col_def:
        if '"isBucketed"' not in col_def: col_def = col_def.replace('}', ', "isBucketed": True}')
        if '"scale"' not in col_def: col_def = col_def.replace('}', ', "scale": "ordinal"}')
        if '"dataType"' not in col_def: col_def = col_def.replace('}', ', "dataType": "string"}')
    elif any(op in col_def for op in ['"count"', '"average"', '"percentile"', '"max"']):
        if '"isBucketed"' not in col_def: col_def = col_def.replace('}', ', "isBucketed": False}')
        if '"scale"' not in col_def: col_def = col_def.replace('}', ', "scale": "ratio"}')
        if '"dataType"' not in col_def: col_def = col_def.replace('}', ', "dataType": "number"}')
    
    # Fix Python boolean formatting if any
    col_def = col_def.replace('True}', 'True}').replace('False}', 'False}')
    return col_def

# The regex matches "col-something": { ... }
# We use a greedy match up to the closing brace, assuming no nested braces in column definition
# Actually, params has nested braces! "params": {"interval": "auto"}
# So regex is risky. Let's write a python AST or just string replacement for specific lines.

lines = content.split('\n')
for i, line in enumerate(lines):
    if '"operationType":' in line and '"col-' in line:
        if '"date_histogram"' in line:
            if '"isBucketed"' not in line: line = line.replace('}', ', "isBucketed": True}')
            if '"scale"' not in line: line = line.replace('}', ', "scale": "interval"}')
            if '"dataType"' not in line: line = line.replace('}', ', "dataType": "date"}')
        elif '"terms"' in line:
            if '"isBucketed"' not in line: line = line.replace('}', ', "isBucketed": True}')
            if '"scale"' not in line: line = line.replace('}', ', "scale": "ordinal"}')
            if '"dataType"' not in line: line = line.replace('}', ', "dataType": "string"}')
        elif any(op in line for op in ['"count"', '"average"', '"percentile"', '"max"']):
            if '"isBucketed"' not in line: line = line.replace('}', ', "isBucketed": False}')
            if '"scale"' not in line: line = line.replace('}', ', "scale": "ratio"}')
            if '"dataType"' not in line: line = line.replace('}', ', "dataType": "number"}')
        
        # Clean up multiple closing braces like }}
        # If it had params: {"size": 10}, the replace('}') might put the keys inside params!
        # Oh, that's bad!
        pass

# Better approach: parse the files using regex that handles nested brackets? No.
# I will just write a python script that actually evaluates the python lists/dicts, modifies them, and overwrites the file!
