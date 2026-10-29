import pytest

from kof_import.kof_parser import parse_lines


def test_topcon_antall_punkter(topcon):
    assert len(topcon.points) == 21
    assert [p.name for p in topcon.points] == [str(n) for n in range(100, 121)]
    assert topcon.warnings == []


def test_topcon_punkt_100(topcon):
    p = topcon.points[0]
    assert p.name == "100"
    assert p.code == ""
    assert p.north == pytest.approx(6615798.981)
    assert p.east == pytest.approx(599667.952)
    assert p.height == pytest.approx(98.848)
    assert p.line_no == 10


def test_topcon_metadata(topcon):
    assert topcon.metadata["Jobbnavn"] == "2026-OVING-3-GRUPPE-2"
    assert topcon.metadata["Projeksjon"] == "NORWAY-EUREF89 UTM 32"
    # Tidspunkt inneholder kolon; bare det første kolonet skal splitte.
    assert topcon.metadata["Eksportdato"] == "2026-08-21 13:30:16"


def test_topcon_tegnkoding(topcon):
    assert topcon.encoding == "cp1252"
    assert "Måleinnstillinger" in topcon.metadata


def test_utf8_med_bom(tmp_path):
    path = tmp_path / "utf8.kof"
    path.write_bytes("﻿ 00 Måling: test\n".encode("utf-8"))
    from kof_import.kof_parser import parse_file

    result = parse_file(path)
    assert result.encoding == "utf-8-sig"
    assert result.metadata == {"Måling": "test"}


def test_punkt_med_kode():
    line = " 05 P1         8510     6615798.981  599667.952   98.848"
    (p,) = parse_lines([line]).points
    assert (p.name, p.code) == ("P1", "8510")


def test_punkt_uten_hoyde():
    line = " 05 P1                  6615798.981  599667.952"
    (p,) = parse_lines([line]).points
    assert p.height is None
    assert p.east == pytest.approx(599667.952)


def test_avvikende_kolonner_leses_fra_hoyre():
    line = "05 P1 8510 6615798.981 599667.952 98.848"
    (p,) = parse_lines([line]).points
    assert (p.name, p.code) == ("P1", "8510")
    assert p.north == pytest.approx(6615798.981)
    assert p.height == pytest.approx(98.848)


def test_ugyldig_punkt_gir_advarsel():
    result = parse_lines([" 05 P1  tull"])
    assert result.points == []
    assert "Linje 1" in result.warnings[0]


def test_ukjent_postkode_gir_advarsel():
    result = parse_lines([" 09_91", " 77 noe"])
    assert len(result.warnings) == 2


def test_01_post_lagres_raatt():
    result = parse_lines([" 01 Oppdrag 29102026 1 1 22"])
    assert result.headers == ["Oppdrag 29102026 1 1 22"]
