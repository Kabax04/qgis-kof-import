"""QGIS-plugin for import av KOF-filer."""


def classFactory(iface):  # noqa: N802 (navnet er bestemt av QGIS)
    # Importeres her slik at parsermodulene kan brukes uten QGIS.
    from .plugin import KofImportPlugin

    return KofImportPlugin(iface)
