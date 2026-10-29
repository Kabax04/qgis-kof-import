from pathlib import Path

from qgis.core import QgsApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from .drop_handler import ALGORITHM_ID, KofDropHandler
from .processing.provider import KofProvider

MENU = "&KOF Import"
ICON = str(Path(__file__).parent / "icon.svg")


class KofImportPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.provider = None
        self.drop_handler = None

    def initProcessing(self):  # noqa: N802
        self.provider = KofProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):  # noqa: N802
        self.initProcessing()
        self.action = QAction(QIcon(ICON), "Importer KOF-fil…", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToVectorMenu(MENU, self.action)
        self.iface.addToolBarIcon(self.action)
        self.drop_handler = KofDropHandler(self.iface)
        self.iface.registerCustomDropHandler(self.drop_handler)

    def unload(self):
        if self.action:
            self.iface.removePluginVectorMenu(MENU, self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action = None
        if self.drop_handler:
            self.iface.unregisterCustomDropHandler(self.drop_handler)
            self.drop_handler = None
        if self.provider:
            QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None

    def run(self):
        import processing

        processing.execAlgorithmDialog(ALGORITHM_ID)
