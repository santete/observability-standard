import sys

with open('original_panels_str.txt', encoding='utf-8') as f:
    a = f.read()

with open('rebuilt_panels_str.txt', encoding='utf-8') as f:
    # json.dumps generates ', ' and ': ', while literal original uses ',' and ':'
    b = f.read().replace(', ', ',').replace(': ', ':')

print("Original length:", len(a))
print("Rebuilt length:", len(b))

diff_idx = -1
m = min(len(a), len(b))
for i in range(m):
    if a[i] != b[i]:
        diff_idx = i
        break

if diff_idx != -1:
    print(f"Diff at {diff_idx}:")
    print(f"original=...{a[diff_idx:diff_idx+50]}...")
    print(f"rebuilt =...{b[diff_idx:diff_idx+50]}...")
else:
    if len(a) != len(b):
        print("One string is a prefix of the other!")
    else:
        print("Strings are IDENTICAL!")
