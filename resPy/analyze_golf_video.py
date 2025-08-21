"""
Golf AI 멀티모달 분석 파이프라인 (단일 비디오)
- 입력: 비디오 파일 경로
- 출력: skeleton 비디오, crop_video, crop_csv, 임베딩, 분류 결과
"""


import os
from pathlib import Path
import json
import subprocess
import sys
from openpose_skeleton_overlay import openpose_skeleton_overlay

# 1. OpenPose로 skeleton 추출 및 skeleton 비디오 생성
# 2. crop_video, crop_csv 생성
# 3. crop_video → Timesformer 임베딩 추출
# 4. crop_csv → mmaction 임베딩 추출
# 5. MLP 이진분류
# 6. 결과 및 skeleton 비디오 spring으로 반환

def analyze_golf_video(input_video_path, user_id=None):
    """
    전체 파이프라인 실행 함수
    input_video_path: str or Path
    user_id: str or None (선택 사항)
    return: dict (결과 json)
    """
    from pathlib import Path
    import shutil
    import numpy as np
    import torch
    import sys
    import logging
    # 경로 세팅
    input_video_path = Path(input_video_path)
    basename = input_video_path.stem
    base_dir = Path(__file__).parent.resolve()
    crop_video_dir = base_dir / "crop_video"
    crop_csv_dir = base_dir / "crop_csv"
    skeleton_video_dir = base_dir / "skeleton_video"
    embedding_dir = base_dir / "embedding"
    result_dir = base_dir / "result"
    for d in [crop_video_dir, crop_csv_dir, skeleton_video_dir, embedding_dir, result_dir]:
        d.mkdir(exist_ok=True, parents=True)

    # angle json 저장 폴더
    angle_dir = base_dir / "angle"
    angle_dir.mkdir(exist_ok=True, parents=True)

    # 1. OpenPose 실행 및 skeleton 비디오 생성
    # (openpose 실행, crop, csv, skeleton 비디오 생성)
    try:
        print(f'[STEP] OpenPose start: input={input_video_path}'); sys.stdout.flush()
        from openpose_utils import run_openpose_and_crop
        crop_video_path, crop_csv_path = run_openpose_and_crop(
            input_video_path, crop_video_dir, crop_csv_dir, skeleton_video_dir
        )
        # sanity check: ensure outputs exist
        if not Path(crop_video_path).exists():
            raise FileNotFoundError(f'crop_video not created by OpenPose: {crop_video_path}')
        if not Path(crop_csv_path).exists():
            raise FileNotFoundError(f'crop_csv not created by OpenPose: {crop_csv_path}')
        print(f'[SUCCESS] OpenPose done: crop_video={crop_video_path}, crop_csv={crop_csv_path}'); sys.stdout.flush()

        # openpose 좌표 기반 skeleton overlay 비디오(h264)만 생성
        base_name = Path(crop_video_path).stem.replace('_crop', '')
        openpose_skeleton_video_path = skeleton_video_dir / (base_name + '_crop_openpose_skeleton_h264.mp4')
        print(f'[STEP] openpose_skeleton_overlay: crop_video={crop_video_path}, crop_csv={crop_csv_path}, out={openpose_skeleton_video_path}'); sys.stdout.flush()
        # Generate points-only overlay to match frontend expectation
        openpose_skeleton_overlay(str(crop_video_path), str(crop_csv_path), str(openpose_skeleton_video_path), fourcc_code='avc1', points_only=True)
        print(f'[SUCCESS] openpose_skeleton_overlay done: {openpose_skeleton_video_path}'); sys.stdout.flush()

        # --- generate angle JSON (angles, fps, com_stability_scores) and embed in result ---
        generated_angles = None
        generated_fps = None
        generated_com_scores = []
        angle_json_path = None
        try:
            # local import to avoid heavy deps at module import timeB
            import cv2 as _cv2
            from save_angle_json import save_angle_json
            # store angle JSONs in dedicated angle directory (not result folder)
            angle_json_path = angle_dir / (base_name + '_angles.json')
            # read fps from crop video
            cap_tmp = _cv2.VideoCapture(str(crop_video_path))
            fps_val = cap_tmp.get(_cv2.CAP_PROP_FPS)
            cap_tmp.release()
            if fps_val is None or fps_val != fps_val:  # NaN check
                fps_val = 30
            # create angle json
            save_angle_json(str(crop_csv_path), str(angle_json_path), int(round(fps_val)))
            # read back and attach
            if angle_json_path.exists():
                with open(angle_json_path, 'r', encoding='utf-8') as af:
                    aj = json.load(af)
                generated_angles = aj.get('angles')
                generated_fps = aj.get('fps')
                generated_com_scores = aj.get('com_stability_scores', [])
        except Exception as e:
            print(f'[WARN] angle JSON generation failed: {e}', file=sys.stderr); sys.stderr.flush()
            angle_json_path = None
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f'[FAIL] OpenPose/Angle failed: input={input_video_path}, error={e}', file=sys.stderr); sys.stderr.flush()
        print(tb, file=sys.stderr); sys.stderr.flush()
        raise

    # 2. Timesformer 임베딩 추출 (crop_video) - 가상환경 subprocess 실행
    def run_in_conda_env(env_name, script_path, args):
        cmd = ['conda', 'run', '--no-capture-output', '-n', env_name, 'python', '-u', script_path] + [str(a) for a in args]
        env = os.environ.copy()
        env['CUBLAS_WORKSPACE_CONFIG'] = ':16:8'
        env['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
        env['PYTHONIOENCODING'] = 'utf-8'
        print('[RUN] ' + ' '.join(cmd)); sys.stdout.flush()
        print('[DEBUG] run_in_conda_env: cwd=' + os.getcwd()); sys.stdout.flush()
        print('[DEBUG] run_in_conda_env: env=' + str({k:env[k] for k in ["CUBLAS_WORKSPACE_CONFIG","KMP_DUPLICATE_LIB_OK","PYTHONIOENCODING"] if k in env})); sys.stdout.flush()
        result = subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stderr, env=env)
        if result.returncode != 0:
            print(f'[FAIL] Subprocess failed: cmd={cmd}, returncode={result.returncode}', file=sys.stderr); sys.stderr.flush()
            raise subprocess.CalledProcessError(result.returncode, result.args)

    timesformer_emb_path = embedding_dir / f"{basename}_timesformer.npy"
    try:
        print(f'[STEP] Timesformer embedding start: input={crop_video_path}, output={timesformer_emb_path}'); sys.stdout.flush()
        run_in_conda_env('timesformer', str(Path(__file__).parent / 'extract_timesformer_single.py'), [crop_video_path, timesformer_emb_path])
        print(f'[SUCCESS] Timesformer embedding done: {timesformer_emb_path}'); sys.stdout.flush()
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(tb, file=sys.stderr); sys.stderr.flush()
        raise

    # 3. STGCN 임베딩 추출 (crop_csv) - 가상환경 subprocess 실행
    stgcn_emb_path = embedding_dir / f"{basename}_stgcn.npy"
    try:
        print(f'[STEP] STGCN embedding start: input={crop_csv_path}, output={stgcn_emb_path}'); sys.stdout.flush()
        run_in_conda_env('mmaction', str(Path(__file__).parent / 'extract_stgcn_single.py'), [crop_csv_path, stgcn_emb_path])
        # npy 파일 생성 후 존재 여부 체크
        if not stgcn_emb_path.exists():
            print(f'[FAIL] STGCN embedding npy not found: {stgcn_emb_path}', file=sys.stderr); sys.stderr.flush()
            raise FileNotFoundError(f'STGCN npy not found: {stgcn_emb_path}')
        print(f'[SUCCESS] STGCN embedding done: {stgcn_emb_path}'); sys.stdout.flush()
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f'[FAIL] STGCN embedding failed: input={crop_csv_path}, output={stgcn_emb_path}, error={e}', file=sys.stderr); sys.stderr.flush()
        print(tb, file=sys.stderr); sys.stderr.flush()
        raise

    # 4. MLP 이진분류 (예외 발생 시에도 결과 구조 보장)
    from mlp_classifier import mlp_predict
    mlp_result = None
    mlp_error = None
    try:
        print(f'[STEP] MLP classification start: timesformer={timesformer_emb_path}, stgcn={stgcn_emb_path}'); sys.stdout.flush()
        # Pass explicit model_path to avoid legacy two-arg ambiguity in mlp_predict
        default_model = Path(__file__).parent.resolve() / 'mlp_model.pth'
        mlp_result = mlp_predict(str(stgcn_emb_path), model_path=str(default_model))
        print(f'[SUCCESS] MLP classification done: result={mlp_result}'); sys.stdout.flush()
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f'[FAIL] MLP classification failed: timesformer={timesformer_emb_path}, stgcn={stgcn_emb_path}, error={e}', file=sys.stderr); sys.stderr.flush()
        print(tb, file=sys.stderr); sys.stderr.flush()
        mlp_error = str(e)
        mlp_result = {
            "prob_true": None,
            "prob_false": None,
            "pred": None,
            "error": mlp_error
        }

    # 5. 결과 반환
    result = {
        "user_id": user_id,
        "openpose_skeleton_video_h264": str(openpose_skeleton_video_path),
        "crop_video": str(crop_video_path),
        "crop_csv": str(crop_csv_path),
        "embedding_timesformer": str(timesformer_emb_path),
        "embedding_stgcn": str(stgcn_emb_path),
        "mlp_result": mlp_result,
    "status": "success",
    "result_version": 1,
        # 호환성: 이전 파이프라인 key도 항상 포함
        "angle_json": None,
        "skeleton_video": None
    }
    # Attach angle/com info if generated
    if generated_angles is not None:
        result['angles'] = generated_angles
    if generated_fps is not None:
        result['fps'] = generated_fps
    if generated_com_scores:
        result['com_stability_scores'] = generated_com_scores
    if angle_json_path is not None:
        # store filename only for frontend compatibility
        try:
            result['angle_json'] = Path(angle_json_path).name
        except Exception:
            result['angle_json'] = str(angle_json_path)
    else:
        # ensure angle_json points at filename if it exists in angle folder
        candidate = angle_dir / (Path(crop_video_path).stem.replace('_crop', '') + '_angles.json')
        if candidate.exists():
            try:
                result['angle_json'] = candidate.name
            except Exception:
                result['angle_json'] = str(candidate)
    if mlp_error:
        result["mlp_error_detail"] = mlp_error
    return result


def validate_result_schema(res):
    """Validate result using resPy/result_schema.json when jsonschema is available.

    Falls back to a lightweight ad-hoc validator when jsonschema isn't installed or schema file
    is missing. This keeps the pipeline runnable in minimal environments while enabling
    strict validation when available.
    """
    import json
    schema_path = Path(__file__).parent.resolve() / 'result_schema.json'
    # Try to use jsonschema if available
    try:
        if schema_path.exists():
            with open(schema_path, 'r', encoding='utf-8') as sf:
                schema = json.load(sf)
            try:
                import jsonschema
                jsonschema.validate(instance=res, schema=schema)
                return
            except Exception as e:
                # If jsonschema not installed or validation error, fall back
                if 'jsonschema' not in str(type(e)) and not isinstance(e, jsonschema.ValidationError if 'jsonschema' in globals() else Exception):
                    # jsonschema likely missing; fall back to lightweight
                    pass
                else:
                    raise
    except Exception:
        # proceed to lightweight validation
        pass

    # Lightweight fallback validator
    required_keys = [
        "user_id", "openpose_skeleton_video_h264", "crop_video", "crop_csv",
        "embedding_timesformer", "embedding_stgcn", "mlp_result", "status"
    ]
    for k in required_keys:
        if k not in res:
            raise ValueError(f"Result missing required key: {k}")
    if res.get("status") not in ("success", "error"):
        raise ValueError("Invalid status in result; must be 'success' or 'error'")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=str, required=True, help="분석할 비디오 파일 경로")
    parser.add_argument("--out", type=str, default="result/result.json", help="결과 json 저장 경로")
    parser.add_argument("--user", type=str, default=None, help="사용자 ID (선택)")
    args = parser.parse_args()
    try:
        print('Starting analyze_golf_video main...'); sys.stdout.flush()
        res = analyze_golf_video(args.video, user_id=args.user)
        # 결과는 항상 result 폴더에 저장
        result_dir = Path(__file__).parent.resolve() / "result"
        result_dir.mkdir(exist_ok=True, parents=True)
        out_name = Path(args.out).name  # 파일명만 추출
        out_path = result_dir / out_name
        # validate result schema
        try:
            validate_result_schema(res)
        except Exception as e:
            print(f"Result schema validation failed: {e}", file=sys.stderr); sys.stderr.flush()
            raise
        # atomic write: write to temp then replace
        tmp_out = out_path.with_suffix(out_path.suffix + ".tmp")
        with open(tmp_out, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
        os.replace(tmp_out, out_path)
        print(f"Analysis done: {out_path}"); sys.stdout.flush()
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        # Try to write an error JSON so the server/frontend can read the failure
        try:
            result_dir = Path(__file__).parent.resolve() / "result"
            result_dir.mkdir(exist_ok=True, parents=True)
            out_name = Path(args.out).name
            out_path = result_dir / out_name
            err_obj = {
                "status": "error",
                "error": str(e),
                "cmd_error": str(e),
                "traceback": tb,
                "user_id": args.user
            }
            tmp_out = out_path.with_suffix(out_path.suffix + ".tmp")
            with open(tmp_out, "w", encoding="utf-8") as f:
                json.dump(err_obj, f, ensure_ascii=False, indent=2)
            os.replace(tmp_out, out_path)
            print(f"Wrote error JSON to {out_path}", file=sys.stderr); sys.stderr.flush()
        except Exception as e2:
            print(f"Failed to write error JSON: {e2}", file=sys.stderr); sys.stderr.flush()
        print("[ERROR] Exception in analyze_golf_video.py:", file=sys.stderr); sys.stderr.flush()
        print(tb, file=sys.stderr); sys.stderr.flush()
        sys.exit(1)
