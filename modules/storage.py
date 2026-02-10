from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .utils import now_iso


def save_run(run_dir: str | Path, payload: dict[str, Any]) -> Path:
    run_path = Path(run_dir)
    run_path.mkdir(parents=True, exist_ok=True)
    filename = f"run_{now_iso().replace(':', '').replace('-', '')}.json"
    full_path = run_path / filename
    full_path.write_text(json.dumps(payload, indent=2, default=str))
    return full_path


def list_runs(run_dir: str | Path) -> list[Path]:
    run_path = Path(run_dir)
    if not run_path.exists():
        return []
    return sorted(run_path.glob("run_*.json"), reverse=True)


def load_run(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    return json.loads(p.read_text())
