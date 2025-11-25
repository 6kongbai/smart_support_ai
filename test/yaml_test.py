from pathlib import Path

import pytest
from app.core.loader import load_yaml_config


def test_yaml_loader():
    conf = load_yaml_config()
    print(conf.get("MCP"))

