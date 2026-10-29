from qgis.core import QgsApplication
from qgis.PyQt.QtWidgets import QAction

from .processing.provider import KofProvider

MENU = "&KOF Import"
ALGORITHM_ID = "kof:importkof"


class KofImportPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.provider = None

    def initProcessing(self):  # noqa: N802
        self.provider = KofProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):  # noqa: N802
        self.initProcessing()
        self.action = QAction("Importer KOF-fil…", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToVectorMenu(MENU, self.action)

    def unload(self):
        if self.action:
            self.iface.removePluginVectorMenu(MENU, self.action)
            self.action = None
        if self.provider:
            QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None

    def run(self):
        import processing

        processing.execAlgorithmDialog(ALGORITHM_ID)
