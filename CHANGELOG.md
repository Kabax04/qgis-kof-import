# Endringslogg

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
