"""Finn koordinatsystem (EPSG) fra metadata i en KOF-fil."""

from __future__ import annotations

import re
from typing import Optional

# Metadatanøkler som kan beskrive koordinatsystemet, i prioritert rekkefølge.
CRS_KEYS = ("Projeksjon", "Koordinatsystem", "Projection", "Coordinate system")
VERTICAL_KEYS = ("Geoidemodell", "Høydesystem", "Geoid model")

# SOSI KOORDSYS-koder for EUREF89 UTM -> EPSG (ETRS89 / UTM).
SOSI_TO_EPSG = {
    21: 25831,
    22: 25832,
    23: 25833,
    24: 25834,
    25: 25835,
    26: 25836,
}

_UTM = re.compile(r"(?:EUREF\s*-?\s*89|ETRS\s*-?\s*89).*?UTM\D{0,10}?(3[1-6])(?!\d)", re.I)
_NTM = re.compile(r"(?:EUREF\s*-?\s*89|ETRS\s*-?\s*89).*?NTM\D{0,10}?(\d{1,2})(?!\d)", re.I)

NN2000_EPSG = 5941


def crs_from_text(text: str) -> Optional[int]:
    """Tolk en beskrivelse som "NORWAY-EUREF89 UTM 32" til en EPSG-kode."""
    match = _UTM.search(text)
    if match:
        return 25800 + int(match.group(1))
    match = _NTM.search(text)
    if match and 5 <= int(match.group(1)) <= 30:
        return 5100 + int(match.group(1))
    return None


def crs_from_sosi_code(code: int) -> Optional[int]:
    return SOSI_TO_EPSG.get(code)


def detect_crs(metadata: dict) -> Optional[int]:
    """Returner EPSG-kode for det horisontale koordinatsystemet, eller None."""
    for key in CRS_KEYS:
        if key in metadata:
            epsg = crs_from_text(metadata[key])
            if epsg:
                return epsg
    return None


def detect_vertical_crs(metadata: dict) -> Optional[int]:
    """Returner EPSG-kode for høydesystemet (foreløpig bare NN2000), eller None."""
    for key in VERTICAL_KEYS:
        if "NN2000" in metadata.get(key, "").upper():
            return NN2000_EPSG
    return None
