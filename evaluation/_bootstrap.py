"""
Make repo-local packages importable when running evaluation scripts as files.

When executing `python evaluation/foo.py`, Python puts `evaluation/` on sys.path
(not the repo root), so imports like `import llm` fail. We fix that by inserting
the parent directory (repo root) onto sys.path.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))




