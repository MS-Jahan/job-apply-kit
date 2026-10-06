import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CORE = REPO / "skills" / "job-apply-core"
SCRIPTS = CORE / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
