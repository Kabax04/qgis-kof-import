"""Finn koordinatsystem (EPSG) fra metadata i en KOF-fil."""

from __future__ import annotations

import re
from typing import Optional

# Metadatanøkler som kan beskrive koordinatsystemet, i prioritert rekkefølge.
CRS_KEYS = ("Projeksjon", "Koordinatsystem", "Projection", "Coordinate system")
VERTICAL_KEYS = ("Geoidemodell", "Høydesystem", "Geoid model")

# SOSI KOORDSYS-koder (brukes i 01-blokkens K.sys-felt) -> EPSG.
# NTM-sonene er utelatt til kodene er bekreftet mot SOSI-standarden.
SOSI_TO_EPSG = {
    # NGO1948 Gauss-Krüger akse I-VIII
    **{axis: 27390 + axis for axis in range(1, 9)},
    # EUREF89 UTM sone 31-36 har kode 21-26
    **{zone - 10: 25800 + zone for zone in range(31, 37)},
    # ED50 UTM sone 31-36 har kode 31-36
    **{zone: 23000 + zone for zone in range(31, 37)},
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


def detect_crs(metadata: dict, sosi_code: Optional[int] = None) -> Optional[int]:
    """Returner EPSG-kode for det horisontale koordinatsystemet, eller None.

    Koordinatsystemkoden fra 01-blokken går foran tekst i 00-kommentarer.
    """
    if sosi_code is not None and crs_from_sosi_code(sosi_code):
        return crs_from_sosi_code(sosi_code)
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
