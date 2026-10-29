import pytest

from kof_import.crs_detect import (
    crs_from_sosi_code,
    crs_from_text,
    detect_crs,
    detect_vertical_crs,
)


def test_topcon_crs(topcon):
    assert detect_crs(topcon.metadata) == 25832
    assert detect_vertical_crs(topcon.metadata) == 5941


@pytest.mark.parametrize(
    "text, epsg",
    [
        ("NORWAY-EUREF89 UTM 32", 25832),
        ("EUREF89 UTM sone 33", 25833),
        ("ETRS89 / UTM zone 35N", 25835),
        ("EUREF89 NTM sone 10", 5110),
        ("NGO1948 Akse 3", None),
        ("", None),
    ],
)
def test_crs_from_text(text, epsg):
    assert crs_from_text(text) == epsg


def test_sosi_kode():
    assert crs_from_sosi_code(22) == 25832
    assert crs_from_sosi_code(999) is None


def test_ingen_metadata():
    assert detect_crs({}) is None
    assert detect_vertical_crs({}) is None
