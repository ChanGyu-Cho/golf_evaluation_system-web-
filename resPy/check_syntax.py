import py_compile
from pathlib import Path
import sys
errors = []
count = 0
for p in Path('.').rglob('*.py'):
    count += 1
    try:
        py_compile.compile(str(p), doraise=True)
    except Exception as e:
        errors.append((str(p), str(e)))
print('FILES_CHECKED', count)
if errors:
    for f,e in errors:
        print('ERROR', f, e)
    sys.exit(2)
print('OK')
