"""
Simple log rotation: remove log files in resPy/result/logs older than N days (default 30).
"""
from pathlib import Path
import time
import os

base = Path(__file__).parent.resolve()
logs = base / 'result' / 'logs'
keep_days = int(os.environ.get('LOG_KEEP_DAYS', '30'))
if not logs.exists():
    print('No logs dir:', logs)
    raise SystemExit(0)
now = time.time()
removed = []
for f in logs.iterdir():
    if not f.is_file():
        continue
    age_days = (now - f.stat().st_mtime) / 86400.0
    if age_days > keep_days:
        try:
            f.unlink()
            removed.append(f.name)
        except Exception as e:
            print('Failed to remove', f, e)
print('Removed', len(removed), 'files')
for r in removed:
    print(' -', r)
