"""Find the coordinate reference system (EPSG) of a KOF file."""

from __future__ import annotations

import re
from typing import Optional, Sequence

# Metadata keys (from "00 Key: value" comments) that may describe the CRS.
CRS_KEY_WORDS = ("projeksjon", "projection", "koordinatsystem", "coordinate system", "srid", "epsg", "crs")
VERTICAL_KEYS = ("Geoidemodell", "Høydesystem", "Geoid model")

# SOSI KOORDSYS codes (the K.sys field of the 01 block) -> EPSG.
# Source: KoordSys.csv in NGI kof-parser (MIT). Geographic systems are left
# out because 05 blocks hold projected coordinates.
SOSI_TO_EPSG = {
    # NGO1948 Gauss-Krüger axis I-VIII
    **{axis: 27390 + axis for axis in range(1, 9)},
    # EUREF89 UTM zone 29-36 has code 19-26
    **{zone - 10: 25800 + zone for zone in range(29, 37)},
    # ED50 UTM zone 31-36 has code 31-36
    **{zone: 23000 + zone for zone in range(31, 37)},
    # WGS84 UTM zone 29-36 has code 59-66
    **{zone + 30: 32600 + zone for zone in range(29, 37)},
    # EUREF89 NTM zone 5-30 has code 205-230
    **{200 + zone: 5100 + zone for zone in range(5, 31)},
    73: 3035,  # ETRS89-LAEA
    74: 3034,  # ETRS89-LCC
    300: 3857,  # Web Mercator
}

_ETRS89 = r"(?:EUREF|ETRS)[\s_-]*(?:19)?89"
_UTM = re.compile(_ETRS89 + r".*?UTM\D{0,10}?(\d{2})(?!\d)", re.I)
_NTM = re.compile(_ETRS89 + r".*?NTM\D{0,10}?(\d{1,2})(?!\d)", re.I)
_ED50_UTM = re.compile(r"ED[\s_-]*50.*?UTM\D{0,10}?(\d{2})(?!\d)", re.I)
_EPSG = re.compile(r"(?:EPSG|SRID)\D{0,5}?(\d{4,5})(?!\d)", re.I)
_LEADING_NUMBER = re.compile(r"\s*(\d{4,5})(?!\d)")

NN2000_EPSG = 5941

# Projected systems where north is always larger than east within Norway.
_UTM_EPSG = set(range(25829, 25837)) | set(range(23031, 23037)) | set(range(32629, 32637))
_NTM_EPSG = set(range(5105, 5131))

# Plausible (north, east) ranges in Norway, Svalbard included, with margin.
# UTM easting can be negative in western Norway when zone 33 is used for the
# whole country. NTM northing is 1 000 000 at 58°N.
_UTM_RANGE = ((6_200_000, 9_100_000), (-300_000, 1_400_000))
_NTM_RANGE = ((800_000, 2_700_000), (-200_000, 400_000))


def crs_from_text(text: str) -> Optional[int]:
    """Interpret e.g. "NORWAY-EUREF89 UTM 32" or "ETRS_1989_UTM_Zone_32N" as an EPSG code."""
    match = _EPSG.search(text)
    if match:
        return int(match.group(1))
    match = _UTM.search(text)
    if match and 29 <= int(match.group(1)) <= 36:
        return 25800 + int(match.group(1))
    match = _NTM.search(text)
    if match and 5 <= int(match.group(1)) <= 30:
        return 5100 + int(match.group(1))
    match = _ED50_UTM.search(text)
    if match and 31 <= int(match.group(1)) <= 36:
        return 23000 + int(match.group(1))
    return None


def crs_from_sosi_code(code: int) -> Optional[int]:
    return SOSI_TO_EPSG.get(code)


def detect_crs(metadata: dict, sosi_code: Optional[int] = None) -> Optional[int]:
    """Return the EPSG code of the horizontal CRS, or None.

    The coordinate system code of the 01 block takes precedence over text in
    00 comments.
    """
    if sosi_code is not None and crs_from_sosi_code(sosi_code):
        return crs_from_sosi_code(sosi_code)
    for key, value in metadata.items():
        lowered = key.lower()
        if not any(word in lowered for word in CRS_KEY_WORDS):
            continue
        # "Spatial Reference ID (SRID): 25832" names the code in the key.
        if "srid" in lowered or "epsg" in lowered:
            match = _LEADING_NUMBER.match(value)
            if match:
                return int(match.group(1))
        epsg = crs_from_text(value)
        if epsg:
            return epsg
    return None


def detect_vertical_crs(metadata: dict) -> Optional[int]:
    """Return the EPSG code of the height system (only NN2000 for now), or None."""
    for key in VERTICAL_KEYS:
        if "NN2000" in metadata.get(key, "").upper():
            return NN2000_EPSG
    return None


def axes_look_swapped(points: Sequence, epsg: int) -> bool:
    """True if most points only fit Norway in a UTM or NTM system with north and east swapped.

    Catches files whose 01 header states the wrong axis order. Points that
    fit neither way round, such as local coordinates labelled as UTM, are
    left alone.
    """
    if epsg in _UTM_EPSG:
        ranges = _UTM_RANGE
    elif epsg in _NTM_EPSG:
        ranges = _NTM_RANGE
    else:
        return False
    if not points:
        return False
    swapped = sum(
        1 for p in points
        if not _fits(p.north, p.east, ranges) and _fits(p.east, p.north, ranges)
    )
    return swapped > len(points) / 2


def _fits(north: float, east: float, ranges) -> bool:
    (north_min, north_max), (east_min, east_max) = ranges
    return north_min <= north <= north_max and east_min <= east <= east_max
