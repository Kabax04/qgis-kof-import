"""Translations.

The source language is English. When QGIS runs in Norwegian (bokmål or
nynorsk), texts are looked up in NB below. A plain Python dictionary keeps
the plugin free of compiled .qm files and lets the tests check that every
text is translated.

Every call to tr() must take a single string literal, so the tests can find
all texts in the source code. Values are filled in with str.format().
"""

from typing import Optional

NORWEGIAN = ("nb", "nn", "no")

_language: Optional[str] = None


def set_language(language: Optional[str]) -> None:
    """Set the language explicitly ("en", "nb", ...). None means detect from QGIS."""
    global _language
    _language = language


def language() -> str:
    global _language
    if _language is None:
        _language = _detect_language()
    return _language


def _detect_language() -> str:
    try:
        from qgis.core import QgsApplication
    except ImportError:
        return "en"
    locale = (QgsApplication.locale() or "en")[:2].lower()
    return "nb" if locale in NORWEGIAN else "en"


def tr(text: str, **values) -> str:
    if language() in NORWEGIAN:
        text = NB.get(text, text)
    else:
        text = EN.get(text, text)
    return text.format(**values) if values else text


# Long texts are looked up by a short key in both languages.
EN = {
    "HELP": (
        "Reads points (05 records) from a KOF file and creates a PointZ layer.\n\n"
        "The coordinate reference system is taken from the file header (the 01 block or e.g. "
        "\"Projeksjon: EUREF89 UTM 32\"). Select one manually if the file does not state it, or to override.\n\n"
        "Repeated measurements: points within the horizontal tolerance (directly or through a chain of "
        "neighbours) are merged into one mean point with standard deviation and largest deviation. Point "
        "pairs up to twice the tolerance apart are reported as warnings in the log.\n\n"
        "Lines and polygons: 09 blocks with line codes (91 straight line, 92 spline, 93 arc, 72-79 and 82-89 "
        "several simultaneous lines, 96 close polygon, 99 end) produce a line layer and a polygon layer. These "
        "layers are only created when the file contains such data."
    ),
}


NB = {
    # Plugin and menu
    "Import KOF file…": "Importer KOF-fil…",
    "{file} imported.": "{file} importert.",
    "{file} imported with 1 warning.": "{file} importert med 1 advarsel.",
    "{file} imported with {count} warnings.": "{file} importert med {count} advarsler.",
    # Algorithm
    "Import KOF file": "Importer KOF-fil",
    "KOF file": "KOF-fil",
    "Coordinate reference system (empty = from file)": "Koordinatsystem (tom = fra filen)",
    "KOF points": "KOF-punkter",
    "Tolerance for repeated measurements (horizontal)": "Toleranse for gjentatte målinger (horisontalt)",
    "Height tolerance (empty = no limit)": "Høydetoleranse (tom = ingen krav)",
    "Include points measured only once in the mean layer": "Ta med punkter som bare er målt én gang i middellaget",
    "Mean of repeated measurements": "Middel av gjentatte målinger",
    "Lines (09 blocks)": "Linjer (09-blokker)",
    "Polygons (closed with 09 96)": "Flater (lukket med 09 96)",
    "mean": "middel",
    "lines": "linjer",
    "polygons": "flater",
    "Using selected coordinate reference system {crs}": "Bruker valgt koordinatsystem {crs}",
    "Coordinate reference system from file: {crs}": "Koordinatsystem fra filen: {crs}",
    "Unknown coordinate system code {code} in the 01 block, ignored": "Ukjent koordinatsystemkode {code} i 01-blokken, ignorert",
    "No coordinate reference system found in the file. Select one manually.": "Fant ikke koordinatsystem i filen. Velg koordinatsystem manuelt.",
    "Heights are in NN2000": "Høyder er oppgitt i NN2000",
    "The coordinates look like east before north for {crs}. North and east have been swapped.": "Koordinatene ser ut til å stå med øst før nord for {crs}. Nord og øst er byttet.",
    "{points} points imported, {warnings} warnings, {disabled} lines disabled (encoding {encoding})": "{points} punkter importert, {warnings} advarsler, {disabled} linjer satt ut av funksjon (tegnkoding {encoding})",
    "{count} groups of repeated measurements (tolerance {tolerance} m)": "{count} grupper av gjentatte målinger (toleranse {tolerance} m)",
    "  {names}: largest deviation {deviation:.1f} mm": "  {names}: største avvik {deviation:.1f} mm",
    "{a} and {b} are {distance:.3f} m apart, just outside the tolerance. Check whether they are the same point.": "{a} og {b} ligger {distance:.3f} m fra hverandre, litt utenfor toleransen. Sjekk om de er samme punkt.",
    "{lines} lines and {polygons} polygons from 09 blocks": "{lines} linjer og {polygons} flater fra 09-blokker",
    "HELP": (
        "Leser punkter (05-poster) fra en KOF-fil og lager et PointZ-lag.\n\n"
        "Koordinatsystemet hentes fra filhodet (01-blokken eller f.eks. «Projeksjon: EUREF89 UTM 32»). "
        "Velg koordinatsystem manuelt hvis filen ikke oppgir det, eller for å overstyre.\n\n"
        "Gjentatte målinger: punkter som ligger innenfor toleransen horisontalt (direkte eller via en kjede "
        "av naboer) slås sammen til ett middelpunkt med standardavvik og største avvik. Punktpar som ligger "
        "opptil dobbel toleranse fra hverandre, rapporteres som advarsel i loggen.\n\n"
        "Linjer og flater: 09-blokker med linjekoder (91 rett linje, 92 spline, 93 bue, 72-79 og 82-89 flere "
        "samtidige linjer, 96 lukk polygon, 99 slutt) gir et linjelag og et flatelag. Lagene lages bare når "
        "filen har slike data."
    ),
    # Parser
    "Line {line_no}: could not read point: {text}": "Linje {line_no}: kunne ikke lese punkt: {text}",
    "Line {line_no}: point {name} is missing north or east coordinate, ignored": "Linje {line_no}: punkt {name} mangler nord- eller østkoordinat, ignorert",
    "Line {line_no}: unknown record type {record}, ignored": "Linje {line_no}: ukjent postkode {record}, ignorert",
    "Line {line_no}: radius (08 141) is not supported, drawn as a straight line": "Linje {line_no}: radius (08 141) støttes ikke, tegnes som rett linje",
    # Lines
    "Line {line_no}: 09 96 (close polygon) without an active line": "Linje {line_no}: 09 96 (lukk polygon) uten aktiv linje",
    "Line {line_no}: the line was not ended with 09 99 or 96": "Linje {line_no}: linjen ble ikke avsluttet med 09 99 eller 96",
    "Line {line_no}: spline (09 92) is drawn as straight lines": "Linje {line_no}: spline (09 92) tegnes som rette linjer",
    "Line {line_no}: polygon with only 2 points, drawn as a line": "Linje {line_no}: polygon med bare 2 punkter, tegnes som linje",
    "Line {line_no}: line with {count} point(s) ignored": "Linje {line_no}: linje med {count} punkt(er) ignorert",
    # Writer
    "{count} point name(s) longer than 10 characters were shortened, e.g. {examples}": "{count} punktnavn lengre enn 10 tegn ble forkortet, f.eks. {examples}",
    "{count} code(s) longer than 8 characters were shortened, e.g. {examples}": "{count} koder lengre enn 8 tegn ble forkortet, f.eks. {examples}",
    "{count} point(s) without north or east coordinate were skipped, e.g. {examples}": "{count} punkt(er) uten nord- eller østkoordinat ble hoppet over, f.eks. {examples}",
    "{count} point(s) with north or east too large for the KOF columns were skipped, e.g. {examples}. Check the coordinate reference system.": "{count} punkt(er) med nord eller øst for store for KOF-kolonnene ble hoppet over, f.eks. {examples}. Sjekk koordinatsystemet.",
    "{count} height(s) too large for the KOF column were left empty, e.g. for point {examples}": "{count} høyde(r) for store for KOF-kolonnen ble stående tomme, f.eks. for punkt {examples}",
    "{count} calculation code(s) that are not a whole number from 0 to 99 were left out, e.g. for point {examples}": "{count} beregningskode(r) som ikke er et heltall fra 0 til 99 ble utelatt, f.eks. for punkt {examples}",
    "{count} line(s) have characters that {encoding} cannot store, written as '?'. First at line {line_no}.": "{count} linje(r) har tegn som {encoding} ikke kan lagre, skrevet som '?'. Første gang på linje {line_no}.",
}
