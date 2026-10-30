# Changelog

Entries before 1.0.0 are in Norwegian.

## [Unreleased]

### Changed
- The plugin is renamed from KOF Import to KOF Tools, to make room for export to KOF. The plugin folder and id are now `kof_tools`, the release zip is `kof_tools.x.y.z.zip` and the repository is `Kabax04/qgis-kof-tools`. The Processing ids (`kof`, `kof:importkof`) are unchanged, so saved models and scripts keep working. If you installed KOF Import, uninstall it after installing KOF Tools.

## [1.1.0] – 2026-10-29

### Changed
- The plugin is offered in QGIS 4 (`qgisMaximumVersion=4.99`) and still supports QGIS 3.22 and later.
- Geometry types, Processing enums and message levels use the scoped names that QGIS 4 (Qt6) requires, with a fallback for older QGIS 3 versions.

## [1.0.1] – 2026-10-29

### Fixed
- The axis order check only swaps north and east when the swapped coordinates fit Norway (Svalbard included) in UTM or NTM, and the original ones do not. Local coordinates labelled as UTM are no longer swapped.

## [1.0.0] – 2026-10-29

First stable release.

### Changed
- English user interface with Norwegian translation (bokmål and nynorsk), following the QGIS language setting.
- Field names are now English: `name`, `code`, `calc_code`, `remark`, `line_no`, `source_file`; in the mean layer `group`, `names`, `count`, `max_dev`; in the line layers `count`, `points`, and `type` values `line`, `arc`, `spline`, `polygon`. Layer names use English suffixes (`mean`, `lines`, `polygons`).
- Author and contact in the metadata.

### Added
- Coordinate system codes from the `01` block cover all SOSI codes from NGI kof-parser, including EUREF89 NTM zones 5–30 (codes 205–230), EUREF89 UTM 29–30 and WGS84 UTM.
- CRS recognised from ArcGIS export text (`ETRS_1989_UTM_Zone_32N`, `ETRS_1989_NTM_Zone_10`) and from `SRID`/`EPSG` comments.
- The axis order is checked: if most points have east larger than north in a UTM or NTM system, north and east are swapped with a warning.
- Real test files from NGI kof-parser (MIT) in `tests/data/ngi/`.

### Fixed
- Points with an empty north or east field are reported as missing coordinates instead of being misread from the remaining numbers.

## [0.4.0] – 2026-10-29

### Lagt til
- Linjer og flater fra `09`-blokker etter KOF-spesifikasjonen 2.00: `91` rett linje, `92` spline (tegnes rett), `93` sirkelbue, `94` punktsverm, `72`–`79` og `82`–`89` flere samtidige linjer (sag- og bølgemetoden), `96` lukk polygon og `99` slutt.
- Nye utdatalag «Linjer» (LineStringZ) og «Flater» (PolygonZ) med feltene `navn`, `type`, `kode`, `antall`, `punkter`, `pi`, `linjenr` og `kildefil`. Lagene lages bare når filen har linjer eller flater.
- En ny linjestart avslutter forrige linje. Punkter med beregningskode 37 regnes som enkeltpunkter og tas ikke med i linjen.
- Advarsler for linjer som ikke avsluttes, polygoner med for få punkter, spline og radius (`08 141`, støttes ikke ennå).

### Endret
- `09`-blokker uten programkode (f.eks. `09 Laget av versjon 5.5.1`) tolkes som kommentarer.
- `08`-blokker gir ikke lenger advarsel om ukjent postkode.

## [0.3.1] – 2026-10-29

Rettelser etter gjennomgang av KOF-spesifikasjonen 2.00 (Norkart, 2005).

### Rettet
- Linjer som er satt ut av funksjon med `-` i kolonne 1, hoppes nå over i stedet for å gi advarsel.
- `05`-poster med beregningskode og/eller merknad etter høyden leses nå. Punktlaget har nye felt `bk` og `merknad`.
- Tekst etter `!` på slutten av en linje tolkes som kommentar og legges i `merknad` (gjelder ikke `00`-poster).
- Meldingen ved dra og slipp sier «1 advarsel», ikke «1 advarsler».

### Lagt til
- `01`-hodet i versjon 2-format tolkes: oppdrag, dato, koordinatsystemkode, kommunenr, enheter og observatør.
- Koordinatsystemkoden i `01` brukes til å finne EPSG (NGO1948 akse I–VIII, EUREF89 UTM 31–36, ED50 UTM 31–36), og går foran teksten i `00`-kommentarer.
- Akserekkefølgen i `01` respekteres: står det at 1. akse er øst, byttes koordinatene.

## [0.3.0] – 2026-10-29

### Lagt til
- Dra og slipp: en `.kof`-fil som slippes i kartet eller lagpanelet, importeres direkte med punktlag og middellag. Advarsler vises i meldingslinjen. Mangler filen koordinatsystem, åpnes dialogen.
- Standardstil: punktlaget får mørke sirkler med punktnavn, middellaget røde kryss med navnene på alle målingene i gruppen.
- Ikon i meny, verktøylinje, Processing-verktøykassen og pluginlisten.

## [0.2.0] – 2026-10-29

### Lagt til
- Middellag for gjentatte målinger i «Importer KOF-fil»: ett punkt per gruppe med middel, standardavvik og største avvik.
- Parametere for horisontal toleranse (standard 5 cm), valgfri høydetoleranse og om enkeltmålte punkter skal tas med.
- Advarsel i loggen for punktpar som ligger opptil dobbel toleranse fra hverandre.

## [0.1.0] – 2026-10-29

### Lagt til
- Processing-algoritme «Importer KOF-fil» (`kof:importkof`) som lager et PointZ-lag, med CRS fra filen eller valgt manuelt.
- Menyvalget Vektor → KOF Import → Importer KOF-fil… åpner algoritmen.
- Parser for `00`-metadata, `01`-hoder (rå tekst) og `05`-punkter, med cp1252/UTF-8.
- Gjenkjenning av EPSG fra `Projeksjon:` (EUREF89 UTM/NTM) og NN2000 fra geoidemodell.
- Gruppering av gjentatte målinger med middelverdi og spredning.
- Tester mot eksempelfil fra Topcon Field, og CI med GitHub Actions.

## [0.0.1] – 2026-10-29

### Lagt til
- Plugin-skjelett som lastes i QGIS (meny under Vektor → KOF Import).
