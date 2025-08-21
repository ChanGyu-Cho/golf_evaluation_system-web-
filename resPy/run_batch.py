"""
Batch runner: iterate uploaded-videos, run analyze_golf_video.py for files missing success results,
capture per-run logs and write a summary JSON to result/batch_summary.json
"""
import os
import json
import subprocess
from pathlib import Path

base = Path(__file__).parent.resolve()
upload_dir = base / 'uploaded-videos'
result_dir = base / 'result'
logs_dir = result_dir / 'logs'
result_dir.mkdir(exist_ok=True)
logs_dir.mkdir(exist_ok=True)
# rotate old logs at start
try:
    import subprocess, sys
    subprocess.run([sys.executable, str(base / 'rotate_logs.py')], check=False)
except Exception:
    pass

files = sorted([p for p in upload_dir.glob('*.mp4')])
summary = {'runs': []}

for p in files:
    name = p.name
    out_name = 'result_' + name + '.json'
    out_path = result_dir / out_name
    skip = False
    if out_path.exists():
        try:
            j = json.load(open(out_path, 'r', encoding='utf-8'))
            if j.get('status') == 'success':
                summary['runs'].append({'video': name, 'result_file': out_name, 'status': 'skipped-already-success'})
                skip = True
        except Exception:
            pass
    if skip:
        continue
    log_file = logs_dir / ('batch_' + name + '.log')
    cmd = ['python', str(base / 'analyze_golf_video.py'), '--video', str(p), '--out', out_name, '--user', 'batch_auto']
    print('\n=== RUNNING', name)
    print('CMD:', ' '.join(cmd))
    with open(log_file, 'w', encoding='utf-8') as lf:
        res = subprocess.run(cmd, stdout=lf, stderr=lf)
    status = 'ok' if res.returncode == 0 else 'fail'
    # read result json if present
    rdata = None
    if out_path.exists():
        try:
            rdata = json.load(open(out_path, 'r', encoding='utf-8'))
        except Exception as e:
            rdata = {'_read_error': str(e)}
    summary['runs'].append({'video': name, 'result_file': out_name, 'exit_code': res.returncode, 'status': status, 'result': rdata, 'log': str(log_file)})

# write summary
with open(result_dir / 'batch_summary.json', 'w', encoding='utf-8') as sf:
    json.dump(summary, sf, ensure_ascii=False, indent=2)

print('\nBatch finished. Summary written to', result_dir / 'batch_summary.json')
print('Runs:', len(summary['runs']))
print('You can inspect', result_dir)
