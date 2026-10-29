"""Parser for KOF-filer.

Ren Python uten QGIS-avhengigheter, slik at den kan testes med pytest.

KOF lagrer koordinater som N (nord) før Ø (øst). Parseren beholder disse
navnene; byttet til x = Ø, y = N gjøres først når lagene bygges.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Union

ENCODINGS = ("utf-8-sig", "cp1252")

# Faste kolonner for 05-poster (0-baserte slicer).
COL_NAME = slice(4, 14)
COL_CODE = slice(15, 23)
COL_NORTH = slice(24, 36)
COL_EAST = slice(37, 48)
COL_HEIGHT = slice(49, 57)


@dataclass
class KofPoint:
    name: str
    code: str
    north: float
    east: float
    height: Optional[float]
    line_no: int


@dataclass
class KofResult:
    points: List[KofPoint] = field(default_factory=list)
    # "Nøkkel: verdi" fra 00-kommentarer, f.eks. {"Projeksjon": "NORWAY-EUREF89 UTM 32"}
    metadata: dict = field(default_factory=dict)
    comments: List[str] = field(default_factory=list)
    # Rå tekst fra 01-poster. Kolonneoppsettet tolkes ikke ennå.
    headers: List[str] = field(default_factory=list)
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
    for line_no, raw in enumerate(lines, start=1):
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        record = stripped[:2]
        if record == "00":
            _parse_comment(stripped[2:].strip(), result)
        elif record == "01":
            result.headers.append(stripped[2:].strip())
        elif record == "05":
            point = _parse_point(line, line_no)
            if point is None:
                result.warnings.append(f"Linje {line_no}: kunne ikke lese punkt: {stripped!r}")
            else:
                result.points.append(point)
        else:
            result.warnings.append(f"Linje {line_no}: ukjent postkode {record!r}, ignorert")
    return result


def _parse_comment(text: str, result: KofResult) -> None:
    result.comments.append(text)
    key, sep, value = text.partition(":")
    if sep and key.strip():
        result.metadata[key.strip()] = value.strip()


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
    # Tekst etter H-kolonnen betyr at linjen ikke følger standardoppsettet.
    if line[COL_HEIGHT.stop:].strip():
        return None
    return KofPoint(
        name=line[COL_NAME].strip(),
        code=line[COL_CODE].strip(),
        north=north,
        east=east,
        height=height,
        line_no=line_no,
    )


def _parse_point_tokens(line: str, line_no: int) -> Optional[KofPoint]:
    """Reserve for filer med avvikende kolonner: les koordinatene fra høyre.

    Første ord er punktnavnet. Av ordene etter navnet tolkes de siste 2–3
    tallene som N, Ø og eventuelt H; det som står foran, er objektkoden.
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
