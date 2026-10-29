# Endringslogg

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
