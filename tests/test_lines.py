"""Linjer fra 09-blokker. Eksemplene følger KOF-spesifikasjonen 2.00, kap. 4.2.2."""

import pytest

from conftest import DATA
from kof_import.kof_parser import parse_file, parse_lines


def p(name, n, e, bk=""):
    return f" 05 {name:<10} {'':8} {n:12.3f} {e:11.3f}          {bk}".rstrip()


@pytest.fixture(scope="module")
def spec():
    return parse_file(DATA / "spec_linjer.kof")


def names(line):
    return [pt.name for pt in line.points]


def test_spec_alle_linjer(spec):
    assert [(line.kind, line.pi, line.closed, names(line)) for line in spec.lines] == [
        ("linje", 72, False, ["9", "11", "13", "15"]),
        ("linje", 72, False, ["10", "12", "14", "16"]),
        ("linje", 83, False, ["17", "22", "23"]),
        ("linje", 83, False, ["18", "21", "24"]),
        ("linje", 83, False, ["19", "20", "25"]),
        ("bue", 93, False, ["60", "61", "62"]),
        ("bue", 93, False, ["41", "42", "43", "44"]),
        ("linje", 91, True, ["H1", "H2", "H3", "H4"]),
        ("linje", 91, False, ["A1", "A2"]),
        ("linje", 91, False, ["B1", "B2", "B3"]),
    ]
    assert spec.warnings == []


def test_spec_alle_punkter_beholdes(spec):
    # Også enkeltpunktet (Bk 37) og punktsvermen er med i punktlaget.
    assert len(spec.points) == 36
    assert {"SP", "S1", "S2"} <= {pt.name for pt in spec.points}


def test_09_med_fritekst_er_kommentar(spec):
    assert "Laget av versjon 5.5.1, T41" in spec.comments


def test_topcon_har_ingen_linjer(topcon):
    assert topcon.lines == []


@pytest.mark.parametrize("start", [" 09 91", " 09_91", " 09 91 18         !SH.18"])
def test_skrivemaater_for_start(start):
    result = parse_lines([start, p("1", 0, 0), p("2", 0, 10), " 09 99"])
    assert [names(line) for line in result.lines] == [["1", "2"]]


def test_andre_programkoder_avbryter_ikke_linjen():
    result = parse_lines([
        " 09 91", p("1", 0, 0), " 09 40", p("2", 0, 10), " 09 39", p("3", 0, 20), " 09 99",
    ])
    assert [names(line) for line in result.lines] == [["1", "2", "3"]]


def test_linje_uten_slutt_ved_filslutt():
    result = parse_lines([" 09 91", p("1", 0, 0), p("2", 0, 10)])
    assert [names(line) for line in result.lines] == [["1", "2"]]
    assert "ikke avsluttet" in result.warnings[0]


def test_polygon_med_to_punkter_blir_linje():
    result = parse_lines([" 09 91", p("1", 0, 0), p("2", 0, 10), " 09 96"])
    (line,) = result.lines
    assert not line.closed
    assert "bare 2 punkter" in result.warnings[0]


def test_linje_med_ett_punkt_ignoreres():
    result = parse_lines([" 09 91", p("1", 0, 0), " 09 99"])
    assert result.lines == []
    assert "1 punkt(er) ignorert" in result.warnings[0]


def test_96_uten_linje_gir_advarsel():
    result = parse_lines([" 09 96"])
    assert "uten aktiv linje" in result.warnings[0]


def test_99_uten_linje_er_stille():
    # Spesifikasjonens eksempel 6.1 har en 09_99 etter en oppstilling.
    assert parse_lines([" 09_99"]).warnings == []


def test_radius_gir_advarsel():
    result = parse_lines([" 09_91", p("74", 0, 0), " 08 141 12.000", p("75", 0, 10), " 09_99"])
    assert len(result.lines) == 1
    assert "radius" in result.warnings[0]


def test_spline_gir_advarsel():
    result = parse_lines([" 09 92", p("1", 0, 0), p("2", 0, 10), " 09 99"])
    assert result.lines[0].kind == "spline"
    assert "spline" in result.warnings[0]


def test_slaatt_av_09_ignoreres():
    result = parse_lines(["-09 91", p("1", 0, 0), p("2", 0, 10), "-09 99"])
    assert result.lines == []
    assert result.disabled == 2
