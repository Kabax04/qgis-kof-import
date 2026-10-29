from pathlib import Path

import pytest

from kof_import.kof_parser import parse_file

DATA = Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def topcon():
    return parse_file(DATA / "topcon_ovingsfil.kof")
