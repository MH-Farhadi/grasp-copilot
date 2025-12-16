from __future__ import annotations

import json
import os
import random
import subprocess
import time
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Optional


def set_seed(seed: int) -> None:
    random.seed(seed)
    try:
        import numpy as np

        np.random.seed(seed)
    except Exception:
        pass
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except Exception:
        pass


def get_git_commit_hash(cwd: Optional[str] = None) -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip()
    except Exception:
        return "unknown"


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _jsonable(obj: Any) -> Any:
    if is_dataclass(obj):
        return asdict(obj)
    if hasattr(obj, "__dict__"):
        return dict(obj.__dict__)
    return obj


def save_run_config(path: str, args: Any, extra: Optional[Dict[str, Any]] = None) -> None:
    payload: Dict[str, Any] = {
        "saved_at_unix": time.time(),
        "git_commit": get_git_commit_hash(),
        "args": _jsonable(args),
    }
    if extra:
        payload.update(extra)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)


def json_loads_strict(s: str) -> Any:
    try:
        return json.loads(s)
    except Exception as e:
        raise ValueError(f"Invalid JSON: {e}") from e

