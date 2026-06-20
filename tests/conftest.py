import sys
from pathlib import Path

# Ensure project root is on sys.path so `app` is importable.
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))