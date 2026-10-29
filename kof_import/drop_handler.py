"""Importer .kof-filer som slippes i kartet eller lagpanelet."""

from pathlib import Path

from qgis.core import Qgis, QgsProcessingException, QgsProcessingFeedback
from qgis.gui import QgsCustomDropHandler

ALGORITHM_ID = "kof:importkof"


class _CollectingFeedback(QgsProcessingFeedback):
    def __init__(self):
        super().__init__()
        self.warnings = []

    def pushWarning(self, warning):  # noqa: N802
        self.warnings.append(warning)
        super().pushWarning(warning)


class KofDropHandler(QgsCustomDropHandler):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface

    def handleFileDrop(self, file):  # noqa: N802
        path = Path(file)
        if path.suffix.lower() != ".kof":
            return False
        import processing

        params = {
            "INPUT": str(path),
            "OUTPUT": "TEMPORARY_OUTPUT",
            "OUTPUT_GROUPS": "TEMPORARY_OUTPUT",
            # Lages bare hvis filen har linjer eller flater.
            "OUTPUT_LINES": "TEMPORARY_OUTPUT",
            "OUTPUT_POLYGONS": "TEMPORARY_OUTPUT",
        }
        feedback = _CollectingFeedback()
        try:
            processing.runAndLoadResults(ALGORITHM_ID, params, feedback=feedback)
        except QgsProcessingException:
            # Typisk mangler koordinatsystem: la brukeren velge i dialogen.
            processing.execAlgorithmDialog(ALGORITHM_ID, {"INPUT": str(path)})
            return True

        bar = self.iface.messageBar()
        if feedback.warnings:
            count = len(feedback.warnings)
            bar.pushMessage(
                "KOF Import",
                f"{path.name} importert med {count} {'advarsel' if count == 1 else 'advarsler'}.",
                "\n".join(feedback.warnings),
                level=Qgis.Warning,
            )
        else:
            bar.pushMessage("KOF Import", f"{path.name} importert.", level=Qgis.Success)
        return True
