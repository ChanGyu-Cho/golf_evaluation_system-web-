import json
from pathlib import Path

res_dir = Path(r"D:\golf_evaluation_system-web-\resPy\result")
results = sorted(res_dir.glob('result_*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
if not results:
    print('No result_*.json found in', res_dir)
    raise SystemExit(1)
res_path = results[0]
print('Updating:', res_path)
with open(res_path, 'r', encoding='utf-8') as f:
    res = json.load(f)

angle_path = res.get('angle_json')
if not angle_path:
    print('No angle_json field in result; nothing to do.')
    raise SystemExit(0)

angle_file = Path(angle_path)
if not angle_file.exists():
    # maybe it's absolute with backslashes escaped; try to resolve in res_dir
    candidate = res_dir / angle_file.name
    if candidate.exists():
        angle_file = candidate
    else:
        # also check dedicated angle folder
        angle_dir = Path(r"D:\golf_evaluation_system-web-\resPy\angle")
        candidate2 = angle_dir / angle_file.name
        if candidate2.exists():
            angle_file = candidate2
        else:
            print('Angle file not found at', angle_path, 'or', candidate, 'or', candidate2)
            raise SystemExit(1)

with open(angle_file, 'r', encoding='utf-8') as f:
    angle_data = json.load(f)

# Inject fields
res['fps'] = angle_data.get('fps')
res['angles'] = angle_data.get('angles')
res['com_stability_scores'] = angle_data.get('com_stability_scores')
# normalize angle_json to filename only
res['angle_json'] = angle_file.name

with open(res_path, 'w', encoding='utf-8') as f:
    json.dump(res, f, indent=2, ensure_ascii=False)

print('Embedded angles into', res_path)
print('fps:', res.get('fps'))
print('angles count:', len(res.get('angles') or []))
print('com scores count:', len(res.get('com_stability_scores') or []))
