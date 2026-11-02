"""Native fixtures run only with an explicit, hash-checked local developer config."""
import hashlib
import json
import os
from pathlib import Path

import pytest

from infrastructure.geometry import WorkerCommand


@pytest.fixture(scope="session")
def native_config():
    config_path = os.environ.get("P07_NATIVE_CONFIG")
    if not config_path:
        pytest.skip("P07 optional native fixtures require explicit P07_NATIVE_CONFIG; no autodetection/fallback")
    config = json.loads(Path(config_path).read_text())
    assert config["qualification"] == "local-software-fixtures-only" and not config["production_enabled"]
    for name, expected in config["sha256"].items():
        path = Path(name)
        assert path.is_absolute() and path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
    return config


def command(config, name):
    value = config[name]
    return WorkerCommand(tuple(value["argv"]), tuple((key, val) for key, val in value["environment"].items()))
