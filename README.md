# KOF Import for QGIS

A QGIS plugin that imports KOF files, the coordinate file format used by
Norwegian surveying instruments and software.

The user interface is available in English and Norwegian, following the
QGIS language setting.

## Features

- **Points** from `05` records, as a PointZ layer with name, code, N, E, H,
  calculation code and remark.
- **Lines and polygons** from `09` blocks: straight lines (`91`), arcs (`93`),
  splines (`92`, drawn straight), several simultaneous lines (`72`–`79` saw
  method, `82`–`89` wave method), closed polygons (`96`) and point swarms (`94`).
- **Coordinate reference system** from the `01` block (all SOSI codes:
  EUREF89 UTM and NTM, NGO1948, ED50, WGS84 UTM …) or from comments such as
  `Projeksjon: EUREF89 UTM 32`, `EXPORT PROJECTION: ETRS_1989_UTM_Zone_32N`
  or `SRID: 25832`. You can always choose another CRS.
- **Axis order** from the `01` block, with a check that corrects files where
  north and east are obviously swapped.
- **Repeated measurements**: points within a tolerance (default 5 cm) are
  merged into a mean layer with standard deviations and largest deviation.
  Pairs just outside the tolerance are reported as warnings.
- Handles Windows-1252 and UTF-8, disabled lines (`-` in column 1), `!`
  comments and files with irregular columns or tabs.

## Usage

- Drag a `.kof` file onto the map or the layers panel, or
- choose **Vector → KOF Import → Import KOF file…** (or the toolbar button) to
  set the CRS and tolerance yourself. The algorithm is also in the Processing
  toolbox, so it works in batch mode and in the graphical modeler.

You get a point layer and a mean layer. Files with `09` blocks also give a
line layer and a polygon layer.

### Layers and fields

| Layer | Fields |
|---|---|
| Points | `name`, `code`, `N`, `E`, `H`, `calc_code`, `remark`, `line_no`, `source_file` |
| Mean | `group`, `name`, `names`, `count`, `N`, `E`, `H`, `std_N`, `std_E`, `std_H`, `max_dev`, `source_file` |
| Lines / polygons | `name`, `type` (`line`, `arc`, `spline`, `polygon`), `code`, `count`, `points`, `pi`, `line_no`, `source_file` |

`line_no` is the line in the KOF file. In the line layers it is the line of
the `09` block that started the line.

## Limitations

- Only coordinate blocks (`05`) are read. Observations (`02`–`04`, `3x`, `4x`,
  `8x`) need a survey adjustment and are skipped with a warning.
- Radius (`08 141`) is not supported; such arcs are drawn as straight lines.
- Line support follows the KOF specification and its examples, but has not
  yet been tested against real files with lines. Example files are welcome as
  [issues](https://github.com/Kabax04/qgis-kof-import/issues).

## Development

The plugin is in `kof_import/`. The parser modules (`kof_parser.py`,
`kof_lines.py`, `crs_detect.py`, `duplicates.py`, `i18n.py`) are plain Python
and can be tested without QGIS:

```bash
python -m pip install pytest
python -m pytest
```

Tests that need QGIS are skipped with plain Python. Run them with the Python
that comes with QGIS, for example on Windows:

```bash
"C:/Program Files/QGIS 3.40.15/bin/python-qgis-ltr.bat" -m pip install --user pytest
"C:/Program Files/QGIS 3.40.15/bin/python-qgis-ltr.bat" -m pytest
```

To try the plugin in QGIS, link or copy `kof_import/` into the plugin folder of
your QGIS profile and use the Plugin Reloader plugin.

### Translations

Texts are written in English and wrapped in `tr()`. Norwegian translations are
in `kof_import/i18n.py`; a test checks that every text is translated.

### KOF format notes

- The record type is in columns 2–3; column 1 is blank or `-` (disabled).
- `05` records use fixed columns: name `[4:14]`, code `[15:23]`, N `[24:36]`,
  E `[37:48]`, H `[49:57]` (0-based Python slices). **North comes before east.**
- Files from Topcon Field have no `01` record; the CRS is in `00 Projeksjon: …`.
- Some instruments use `09` for free text; only `09` followed by a number is a
  program code.
- `tests/data/spec_linjer.kof` is built from the examples in the KOF
  specification 2.00 (Norkart, 2005). `tests/data/ngi/` holds real files from
  [NGI kof-parser](https://github.com/norwegian-geotechnical-institute/kof-parser) (MIT).

## License

GPL-2.0, see [LICENSE](LICENSE).
