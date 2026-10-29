"""Parser for KOF-filer.

Ren Python uten QGIS-avhengigheter, slik at den kan testes med pytest.
Kolonneoppsettet følger KOF-spesifikasjonen versjon 2.00 (Norkart, 2005).

KOF lagrer koordinater som N (nord) før Ø (øst). Parseren beholder disse
navnene; byttet til x = Ø, y = N gjøres først når lagene bygges.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Union

from .kof_lines import KofLine, LineTracker

ENCODINGS = ("utf-8-sig", "cp1252")

# Faste kolonner for 05-poster (0-baserte slicer).
COL_NAME = slice(4, 14)
COL_CODE = slice(15, 23)
COL_NORTH = slice(24, 36)
COL_EAST = slice(37, 48)
COL_HEIGHT = slice(49, 57)
COL_BK = slice(57, 61)
COL_REMARK = slice(61, None)

# Faste kolonner for 01-poster, versjon 2 (gjenkjennes på "$" i enhetsfeltet).
COL_01_JOB = slice(4, 16)
COL_01_DATE = slice(17, 25)
COL_01_VERSION = slice(26, 29)
COL_01_CRS = slice(30, 37)
COL_01_MUNICIPALITY = slice(38, 42)
COL_01_UNITS = slice(43, 55)
COL_01_OBSERVER = slice(56, None)


@dataclass
class KofPoint:
    name: str
    code: str
    north: float
    east: float
    height: Optional[float]
    line_no: int
    # Beregningskode (30-38) og merknad, inkludert kommentar etter "!".
    bk: Optional[int] = None
    remark: str = ""


@dataclass
class KofHeader:
    """01-blokk i versjon 2-format."""

    job: str
    date: str
    version: Optional[int]
    crs_code: Optional[int]
    municipality: Optional[int]
    units: str
    observer: str

    @property
    def east_first(self) -> bool:
        # 2. tegn i enhetsfeltet: retning på 1. akse, 1 = nord, 2 = øst.
        return self.units[1:2] == "2"


@dataclass
class KofResult:
    points: List[KofPoint] = field(default_factory=list)
    # Linjer og polygoner fra 09-blokker. Punktene finnes også i `points`.
    lines: List[KofLine] = field(default_factory=list)
    # "Nøkkel: verdi" fra 00-kommentarer, f.eks. {"Projeksjon": "NORWAY-EUREF89 UTM 32"}
    metadata: dict = field(default_factory=dict)
    comments: List[str] = field(default_factory=list)
    # Rå tekst fra alle 01-poster, og den siste som kunne tolkes som versjon 2.
    headers: List[str] = field(default_factory=list)
    header: Optional[KofHeader] = None
    # Antall linjer satt ut av funksjon med "-" i kolonne 1.
    disabled: int = 0
    warnings: List[str] = field(default_factory=list)
    encoding: Optional[str] = None
    source: Optional[str] = None


def read_text(path: Union[str, Path]) -> "tuple[str, str]":
    """Les filen og returner (tekst, tegnkoding)."""
    data = Path(path).read_bytes()
    for encoding in ENCODINGS:
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    # cp1252 har noen udefinerte byte; ta vare på resten av filen.
    return data.decode("cp1252", errors="replace"), "cp1252"


def parse_file(path: Union[str, Path]) -> KofResult:
    text, encoding = read_text(path)
    result = parse_lines(text.splitlines())
    result.encoding = encoding
    result.source = str(path)
    return result


def parse_lines(lines: Iterable[str]) -> KofResult:
    result = KofResult()
    tracker = LineTracker(result.warnings)
    for line_no, raw in enumerate(lines, start=1):
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if line.startswith("-"):
            result.disabled += 1
            continue
        record = stripped[:2]
        if record == "00":
            # Fri tekst; "!" er ikke kommentartegn her.
            _parse_comment(stripped[2:].strip(), result)
            continue

        line, _, comment = line.partition("!")
        line = line.rstrip()
        if record == "01":
            result.headers.append(line.strip()[2:].strip())
            header = _parse_header(line)
            if header is not None:
                result.header = header
        elif record == "05":
            point = _parse_point(line, line_no)
            if point is None:
                result.warnings.append(f"Linje {line_no}: kunne ikke lese punkt: {stripped!r}")
                continue
            if result.header is not None and result.header.east_first:
                point.north, point.east = point.east, point.north
            point.remark = " ".join(t for t in (point.remark, comment.strip()) if t)
            result.points.append(point)
            tracker.point(point)
        elif record == "09":
            pi = _program_code(stripped)
            if pi is None:
                # Noen instrumenter bruker 09 til fritekst, f.eks. "09 Laget av versjon 5.5.1".
                result.comments.append(stripped[2:].strip())
            else:
                tracker.program(pi, line_no)
        elif record == "08":
            if stripped[2:].split()[:1] == ["141"]:
                result.warnings.append(
                    f"Linje {line_no}: radius (08 141) støttes ikke, tegnes som rett linje"
                )
            # Andre egenskapskoder påvirker ikke geometrien.
        else:
            result.warnings.append(f"Linje {line_no}: ukjent postkode {record!r}, ignorert")
    result.lines = tracker.finish()
    return result


def _program_code(stripped: str) -> Optional[int]:
    """Programkoden (Pi) i en 09-blokk, f.eks. 91 i "09 91" eller "09_91"."""
    tokens = stripped[2:].lstrip("_").split()
    if tokens and tokens[0].isdigit() and len(tokens[0]) <= 2:
        return int(tokens[0])
    return None


def _parse_comment(text: str, result: KofResult) -> None:
    result.comments.append(text)
    key, sep, value = text.partition(":")
    if sep and key.strip():
        result.metadata[key.strip()] = value.strip()


def _to_int(text: str) -> Optional[int]:
    text = text.strip()
    return int(text) if text.isdigit() else None


def _parse_header(line: str) -> Optional[KofHeader]:
    units = line[COL_01_UNITS].strip()
    if not units.startswith("$"):
        # Versjon 1 har et annet, fritt oppsett. Vi tolker det ikke.
        return None
    return KofHeader(
        job=line[COL_01_JOB].strip(),
        date=line[COL_01_DATE].strip(),
        version=_to_int(line[COL_01_VERSION]),
        crs_code=_to_int(line[COL_01_CRS]),
        municipality=_to_int(line[COL_01_MUNICIPALITY]),
        units=units,
        observer=line[COL_01_OBSERVER].strip(),
    )


def _parse_point(line: str, line_no: int) -> Optional[KofPoint]:
    return _parse_point_fixed(line, line_no) or _parse_point_tokens(line, line_no)


def _to_float(text: str) -> Optional[float]:
    try:
        return float(text)
    except ValueError:
        return None


def _parse_point_fixed(line: str, line_no: int) -> Optional[KofPoint]:
    """Les 05-post etter standard kolonneoppsett."""
    north = _to_float(line[COL_NORTH])
    east = _to_float(line[COL_EAST])
    if north is None or east is None:
        return None
    height_text = line[COL_HEIGHT].strip()
    height = _to_float(height_text) if height_text else None
    if height_text and height is None:
        return None
    # Etter H kommer beregningskode (I2) og merknad. Står det noe annet
    # enn et heltall der Bk skal være, regnes alt som merknad.
    bk_text = line[COL_BK].strip()
    bk = _to_int(bk_text)
    if bk_text and bk is None:
        remark = line[COL_BK.start:].strip()
    else:
        remark = line[COL_REMARK].strip()
    return KofPoint(
        name=line[COL_NAME].strip(),
        code=line[COL_CODE].strip(),
        north=north,
        east=east,
        height=height,
        line_no=line_no,
        bk=bk,
        remark=remark,
    )


def _parse_point_tokens(line: str, line_no: int) -> Optional[KofPoint]:
    """Reserve for filer med avvikende kolonner: les koordinatene fra høyre.

    Første ord er punktnavnet. Av ordene etter navnet tolkes de siste 2–3
    tallene som N, Ø og eventuelt H; det som står foran, er objektkoden.
    Beregningskode og merknad støttes ikke her.
    """
    tokens = line.split()[1:]
    if len(tokens) < 3:
        return None
    name, rest = tokens[0], tokens[1:]
    numbers = []
    while rest and len(numbers) < 3 and _to_float(rest[-1]) is not None:
        numbers.insert(0, float(rest.pop()))
    if len(numbers) < 2:
        return None
    if len(numbers) == 2:
        north, east, height = numbers[0], numbers[1], None
    else:
        north, east, height = numbers
    return KofPoint(
        name=name,
        code=" ".join(rest),
        north=north,
        east=east,
        height=height,
        line_no=line_no,
    )
