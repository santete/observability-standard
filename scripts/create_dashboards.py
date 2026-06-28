import subprocess
import os

# Define paths relative to the script location
script_dir = os.path.dirname(os.path.abspath(__file__))
ndjson_path = os.path.join(script_dir, '..', 'kibana', 'dashboards.ndjson')
ndjson_path = os.path.abspath(ndjson_path)

cmd = [
    'curl.exe', '-X', 'POST',
    'http://localhost:5601/api/saved_objects/_import?overwrite=true',
    '-H', 'kbn-xsrf: true',
    '-F', f'file=@{ndjson_path}'
]

print(f"Importing dashboards from: {ndjson_path}")
print("Executing curl.exe import command...")

try:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    print("\n--- IMPORT SUCCESS ---")
    print(result.stdout)
except subprocess.CalledProcessError as e:
    print("\n--- IMPORT FAILED ---")
    print("Exit code:", e.returncode)
    print("Error output:", e.stderr)
    print("Standard output:", e.stdout)
