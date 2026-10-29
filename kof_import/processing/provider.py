from qgis.core import QgsProcessingProvider

from .import_kof_algorithm import ImportKofAlgorithm


class KofProvider(QgsProcessingProvider):
    def id(self):
        return "kof"

    def name(self):
        return "KOF Import"

    def loadAlgorithms(self):  # noqa: N802
        self.addAlgorithm(ImportKofAlgorithm())
