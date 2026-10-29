"""QGIS plugin for importing KOF files."""


def classFactory(iface):  # noqa: N802 (name required by QGIS)
    # Imported here so the parser modules can be used without QGIS.
    from .plugin import KofImportPlugin

    return KofImportPlugin(iface)
