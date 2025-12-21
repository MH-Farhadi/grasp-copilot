from __future__ import annotations

from pathlib import Path
from typing import Optional


def _repo_root() -> Path:
    # data_generator/ is a top-level package under the grasp-copilot repo.
    return Path(__file__).resolve().parents[1]


def allocate_numbered_run_dir(
    *,
    runs_root: Optional[Path] = None,
    width: int = 3,
) -> Path:
    """
    Create and return a unique run directory using a numeric pattern:
      data/runs/001, data/runs/002, ...

    By default, the base directory is: <repo_root>/data/runs
    """
    if width <= 0:
        raise ValueError("width must be >= 1")

    root = _repo_root()
    base = runs_root or (root / "data" / "runs")
    base.mkdir(parents=True, exist_ok=True)

    # Pick the next available integer id.
    existing = []
    for p in base.iterdir():
        if not p.is_dir():
            continue
        name = p.name
        if len(name) == width and name.isdigit():
            existing.append(int(name))

    next_id = (max(existing) + 1) if existing else 1

    # Be robust to races / accidental collisions by probing forward.
    while True:
        run_dir = base / f"{next_id:0{width}d}"
        try:
            run_dir.mkdir(parents=False, exist_ok=False)
            return run_dir
        except FileExistsError:
            next_id += 1


