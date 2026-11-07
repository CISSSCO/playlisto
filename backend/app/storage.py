import json
from pathlib import Path
from cryptography.fernet import Fernet
import uuid

# =====================================================
# PATHS
# =====================================================

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_PATH = DATA_DIR / "folders.json"
PROVIDERS_PATH = DATA_DIR / "providers.enc"
SOURCES_PATH = DATA_DIR / "sources.enc"
KEY_PATH = DATA_DIR / "secret.key"

# =====================================================
# ENCRYPTION
# =====================================================

def get_cipher():
    KEY_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not KEY_PATH.exists():
        KEY_PATH.write_bytes(Fernet.generate_key())

    key = KEY_PATH.read_bytes()
    return Fernet(key)

# =====================================================
# PLAYLIST CACHE (NOT ENCRYPTED)
# =====================================================

def load_data():
    if not DATA_PATH.exists():
        return {"last_folder": None, "folders": []}
    return json.loads(DATA_PATH.read_text())


def save_data(data):
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(data, indent=2))

# =====================================================
# PROVIDERS (Encrypted API Keys)
# =====================================================

def load_providers():
    cipher = get_cipher()

    if not PROVIDERS_PATH.exists():
        return {"active_provider_id": None, "providers": []}

    decrypted = cipher.decrypt(PROVIDERS_PATH.read_bytes())
    return json.loads(decrypted.decode())


def save_providers(data):
    cipher = get_cipher()
    encrypted = cipher.encrypt(json.dumps(data).encode())

    PROVIDERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROVIDERS_PATH.write_bytes(encrypted)


def add_provider(name, api_key):
    data = load_providers()

    provider = {
        "id": str(uuid.uuid4()),
        "name": name,
        "type": "google_drive",
        "api_key": api_key
    }

    data["providers"].append(provider)

    if not data["active_provider_id"]:
        data["active_provider_id"] = provider["id"]

    save_providers(data)
    return provider


def get_providers_metadata():
    data = load_providers()

    return [
        {
            "id": p["id"],
            "name": p["name"],
            "type": p["type"],
            "active": p["id"] == data["active_provider_id"]
        }
        for p in data["providers"]
    ]


def set_active_provider(provider_id):
    data = load_providers()
    data["active_provider_id"] = provider_id
    save_providers(data)


def get_active_provider():
    data = load_providers()
    active_id = data.get("active_provider_id")

    for p in data["providers"]:
        if p["id"] == active_id:
            return p

    return None


def get_provider_by_id(provider_id):
    data = load_providers()
    for p in data["providers"]:
        if p["id"] == provider_id:
            return p
    return None


def delete_provider(provider_id):
    data = load_providers()
    data["providers"] = [p for p in data["providers"] if p["id"] != provider_id]
    if data.get("active_provider_id") == provider_id:
        data["active_provider_id"] = data["providers"][0]["id"] if data["providers"] else None
    save_providers(data)

# =====================================================
# SOURCES (Encrypted URLs)
# =====================================================

def load_sources():
    cipher = get_cipher()

    if not SOURCES_PATH.exists():
        return {"active_source_id": None, "sources": []}

    decrypted = cipher.decrypt(SOURCES_PATH.read_bytes())
    return json.loads(decrypted.decode())


def save_sources(data):
    cipher = get_cipher()
    encrypted = cipher.encrypt(json.dumps(data).encode())

    SOURCES_PATH.parent.mkdir(parents=True, exist_ok=True)
    SOURCES_PATH.write_bytes(encrypted)


def add_source(name, url, provider_id):
    data = load_sources()

    source = {
        "id": str(uuid.uuid4()),
        "name": name,
        "url": url,
        "provider_id": provider_id
    }

    data["sources"].append(source)

    if not data["active_source_id"]:
        data["active_source_id"] = source["id"]

    save_sources(data)
    return source


def activate_source(source_id):
    data = load_sources()
    data["active_source_id"] = source_id
    save_sources(data)


def delete_source(source_id):
    data = load_sources()
    data["sources"] = [s for s in data["sources"] if s["id"] != source_id]
    if data.get("active_source_id") == source_id:
        data["active_source_id"] = data["sources"][0]["id"] if data["sources"] else None
    save_sources(data)


def get_active_source():
    data = load_sources()
    active_id = data.get("active_source_id")

    for s in data["sources"]:
        if s["id"] == active_id:
            return s

    return None
