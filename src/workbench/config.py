"""
Configuration.

config.json holds everything; secrets can be kept out of it entirely by setting
environment variables instead, which is what you want on a shared server:

  BOX_CLIENT_ID  BOX_CLIENT_SECRET  BOX_ENTERPRISE_ID  BOX_USER_ID
  BOX_DEVELOPER_TOKEN
  MODEL_API_KEY  MODEL_BASE_URL  MODEL_NAME  MODEL_PROVIDER

Environment always wins over the file.
"""
from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DEFAULTS = {
    "storage": {
        "active": "local",
        "local": {"root": str(ROOT / "data")},
        "box": {
            "root_folder_id": "0",
            "client_id": "", "client_secret": "",
            "enterprise_id": "", "user_id": "",
            "developer_token": "", "as_user_id": "",
        },
    },
    "folders": {
        "inbox": "01_TO_PROCESS",
        "originals": "02_PROCESSED_ORIGINALS",
        "transformed": "03_TRANSFORMED_OUTPUT",
    },
    "model": {
        "provider": "none",
        "model": "",
        "base_url": "",
        "api_key": "",
        "endpoint": "",
        "deployment": "",
        "max_tokens": 1400,
        "vision": True,
    },
    "redaction": {"name_detector": "heuristic"},
    "window": {
        "day": "Wednesday",
        "start_hour": 18,
        "hours": 6,
        "max_files_per_run": 1200,
        "max_gb_per_run": 40,
        "lock_minutes_before": 60,
    },
    "paths": {
        "intake": str(ROOT / "intake"),
        "completed_intake": str(ROOT / "intake" / "completed"),
        "state": str(ROOT / "state"),
        "runs": str(ROOT / "runs"),
        "web": str(ROOT / "web"),
        "work": str(ROOT / "state" / "work"),
    },
    "server": {"host": "127.0.0.1", "port": 8765, "reviewer": ""},
}

ENV_MAP = [
    ("BOX_CLIENT_ID", ("storage", "box", "client_id")),
    ("BOX_CLIENT_SECRET", ("storage", "box", "client_secret")),
    ("BOX_ENTERPRISE_ID", ("storage", "box", "enterprise_id")),
    ("BOX_USER_ID", ("storage", "box", "user_id")),
    ("BOX_DEVELOPER_TOKEN", ("storage", "box", "developer_token")),
    ("BOX_ROOT_FOLDER_ID", ("storage", "box", "root_folder_id")),
    ("MODEL_PROVIDER", ("model", "provider")),
    ("MODEL_API_KEY", ("model", "api_key")),
    ("MODEL_BASE_URL", ("model", "base_url")),
    ("MODEL_NAME", ("model", "model")),
    ("AZURE_OPENAI_ENDPOINT", ("model", "endpoint")),
    ("AZURE_OPENAI_DEPLOYMENT", ("model", "deployment")),
]


def _deep_merge(base: dict, over: dict) -> dict:
    out = deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _set(cfg: dict, path: tuple, value) -> None:
    node = cfg
    for key in path[:-1]:
        node = node.setdefault(key, {})
    node[path[-1]] = value


def load(path: str | Path | None = None) -> dict:
    path = Path(path or ROOT / "config.json")
    file_cfg = {}
    if path.exists():
        file_cfg = json.loads(path.read_text(encoding="utf-8"))
    cfg = _deep_merge(DEFAULTS, file_cfg)
    for env, target in ENV_MAP:
        val = os.environ.get(env)
        if val:
            _set(cfg, target, val)
    for key in ("intake", "completed_intake", "state", "runs", "web", "work"):
        Path(cfg["paths"][key]).mkdir(parents=True, exist_ok=True)
    cfg["_config_path"] = str(path)
    return cfg


def save(cfg: dict, path: str | Path | None = None) -> Path:
    path = Path(path or cfg.get("_config_path") or ROOT / "config.json")
    out = {k: v for k, v in cfg.items() if not k.startswith("_")}
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return path
