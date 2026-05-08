"""
앱 설정 로컬 저장
  ~/.rsi_macd_trader/
    .key         — Fernet 암호화 키 (최초 실행 시 자동 생성, 파일 권한 600)
    secrets.enc  — 민감 정보 암호화 저장 (App Key / App Secret / 계좌번호)
    config.json  — 일반 설정 평문 JSON (티커, 파라미터 등)
"""
import json
import os
from pathlib import Path
from typing import Any

_DIR = Path.home() / ".rsi_macd_trader"
_KEY_FILE = _DIR / ".key"
_ENC_FILE = _DIR / "secrets.enc"
_CFG_FILE = _DIR / "config.json"


def _ensure_dir() -> None:
    _DIR.mkdir(exist_ok=True)


def _fernet():
    from cryptography.fernet import Fernet
    if _KEY_FILE.exists():
        key = _KEY_FILE.read_bytes()
    else:
        _ensure_dir()
        key = Fernet.generate_key()
        _KEY_FILE.write_bytes(key)
        os.chmod(_KEY_FILE, 0o600)   # 소유자만 읽기/쓰기
    return Fernet(key)


# ── 민감 정보 (암호화) ──────────────────────────────────────────────

def _load_secrets_raw() -> dict:
    if not _ENC_FILE.exists():
        return {}
    try:
        return json.loads(_fernet().decrypt(_ENC_FILE.read_bytes()))
    except Exception:
        return {}


def _save_secrets_raw(data: dict) -> None:
    _ensure_dir()
    _ENC_FILE.write_bytes(_fernet().encrypt(json.dumps(data).encode()))
    os.chmod(_ENC_FILE, 0o600)


def save_secret(key: str, val: str) -> None:
    data = _load_secrets_raw()
    data[key] = val
    _save_secrets_raw(data)


def load_secret(key: str, default: str = "") -> str:
    return _load_secrets_raw().get(key, default)


# ── 일반 설정 (평문 JSON) ────────────────────────────────────────────

def save_config(data: dict) -> None:
    _ensure_dir()
    _CFG_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_config() -> dict:
    if not _CFG_FILE.exists():
        return {}
    try:
        return json.loads(_CFG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_value(key: str, val: Any) -> None:
    data = load_config()
    data[key] = val
    save_config(data)


def load_value(key: str, default: Any = None) -> Any:
    return load_config().get(key, default)
