import json
from pathlib import Path
from typing import Dict, Any

from cryptography.fernet import Fernet


# Encrypted storage files
DATA_PATH = Path("data/folders.enc")
CONFIG_PATH = Path("data/config.enc")
SECRET_KEY_PATH = Path("data/secret.key")


# ---------------------------
# Encryption Core
# ---------------------------

def _get_cipher() -> Fernet:
    """
    Loads or creates encryption key.
    This key MUST NOT be committed to git.
    """
    SECRET_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not SECRET_KEY_PATH.exists():
        key = Fernet.generate_key()
        SECRET_KEY_PATH.write_bytes(key)
    else:
        key = SECRET_KEY_PATH.read_bytes()

    return Fernet(key)


# ---------------------------
# Folder Data (Encrypted)
# ---------------------------

def load_data() -> Dict[str, Any]:
    if not DATA_PATH.exists():
        return {"last_folder": None, "folders": []}

    try:
        cipher = _get_cipher()
        encrypted = DATA_PATH.read_bytes()
        decrypted = cipher.decrypt(encrypted)
        return json.loads(decrypted.decode())
    except Exception:
        return {"last_folder": None, "folders": []}


def save_data(data: Dict[str, Any]):
    cipher = _get_cipher()
    raw = json.dumps(data).encode()
    encrypted = cipher.encrypt(raw)

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_bytes(encrypted)


# ---------------------------
# Config (Encrypted API Key)
# ---------------------------

def load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {"google_api_key": None}

    try:
        cipher = _get_cipher()
        encrypted = CONFIG_PATH.read_bytes()
        decrypted = cipher.decrypt(encrypted)
        config = json.loads(decrypted.decode())
        return config
    except Exception:
        return {"google_api_key": None}


def save_config(config: Dict[str, Any]):
    cipher = _get_cipher()
    raw = json.dumps(config).encode()
    encrypted = cipher.encrypt(raw)

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_bytes(encrypted)
