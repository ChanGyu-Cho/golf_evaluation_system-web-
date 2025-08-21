import importlib, traceback, sys, os
# ensure project root is on sys.path so 'resPy' package can be imported when running this test
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
try:
    importlib.import_module('resPy.mlp_classifier')
    print('IMPORT_OK')
except Exception:
    traceback.print_exc()
    sys.exit(2)
