from qgis.core import Qgis
from qgis.PyQt.QtWidgets import QAction

MENU = "&KOF Import"


class KofImportPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None

    def initGui(self):  # noqa: N802
        self.action = QAction("Importer KOF-fil…", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToVectorMenu(MENU, self.action)

    def unload(self):
        if self.action:
            self.iface.removePluginVectorMenu(MENU, self.action)
            self.action = None

    def run(self):
        self.iface.messageBar().pushMessage(
            "KOF Import", "Import er ikke implementert ennå.", level=Qgis.Info
        )
