# qgis-kof-import

QGIS-plugin for import av KOF-filer (koordinatfilformat brukt av landmålingsutstyr, f.eks. Topcon Field).

## Status

Tidlig utvikling. Se [CHANGELOG.md](CHANGELOG.md).

## Bruk

- Dra en `.kof`-fil inn i kartet eller lagpanelet, eller
- velg **Vektor → KOF Import → Importer KOF-fil…** (eller ikonet i verktøylinjen) for å velge koordinatsystem og toleranse selv.

Du får to lag: alle målte punkter, og et middellag der gjentatte målinger av samme punkt er slått sammen.

## Struktur

- `kof_import/` – selve pluginen (denne mappen zippes og installeres i QGIS)
  - `kof_parser.py` – leser KOF-filer, ren Python uten QGIS
  - `crs_detect.py` – finner EPSG-kode fra filhodet
  - `duplicates.py` – grupperer gjentatte målinger av samme punkt
  - `layer_builder.py` – lager QGIS-felt og -geometri (x = Ø, y = N)
  - `processing/` – Processing-algoritmen «Importer KOF-fil»
  - `layer_style.py` – standardstil og etiketter
  - `drop_handler.py` – dra og slipp av `.kof`-filer
- `tests/` – pytest-tester, med eksempelfiler i `tests/data/`

## Utvikling

Testene for parseren krever bare Python og pytest:

```bash
python -m pip install pytest
python -m pytest
```

Testene i `tests/test_layers.py` krever QGIS og hoppes over med vanlig Python. Kjør dem med QGIS sin Python:

```bash
"C:/Program Files/QGIS 3.40.15/bin/python-qgis-ltr.bat" -m pip install --user pytest
"C:/Program Files/QGIS 3.40.15/bin/python-qgis-ltr.bat" -m pytest
```

For å teste i QGIS: lag en symlink (eller kopi) av `kof_import/` i QGIS-profilens plugin-mappe,
f.eks. `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\kof_import`, og bruk Plugin Reloader.

## KOF-format – notater

- Postkoden står i kolonne 2–3 (linjen starter med mellomrom).
- `05`-poster har faste kolonner: navn `[4:14]`, kode `[15:23]`, N `[24:36]`, Ø `[37:48]`, H `[49:57]`
  (0-baserte Python-slicer). **N kommer før Ø.**
- Filer fra Topcon Field har ingen `01`-post; koordinatsystemet står i `00 Projeksjon: …`.
- Filene er ofte Windows-1252.
