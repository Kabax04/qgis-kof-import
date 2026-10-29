from pathlib import Path

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsFeatureSink,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterCrs,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFile,
)

from ..crs_detect import detect_crs, detect_vertical_crs
from ..kof_parser import parse_file
from ..layer_builder import POINT_WKB_TYPE, point_features, point_fields


class ImportKofAlgorithm(QgsProcessingAlgorithm):
    INPUT = "INPUT"
    CRS = "CRS"
    OUTPUT = "OUTPUT"

    def name(self):
        return "importkof"

    def displayName(self):  # noqa: N802
        return "Importer KOF-fil"

    def shortHelpString(self):  # noqa: N802
        return (
            "Leser punkter (05-poster) fra en KOF-fil og lager et PointZ-lag.\n\n"
            "Koordinatsystemet hentes fra filhodet (f.eks. «Projeksjon: EUREF89 UTM 32»). "
            "Velg CRS manuelt hvis filen ikke oppgir det, eller for å overstyre."
        )

    def createInstance(self):  # noqa: N802
        return ImportKofAlgorithm()

    def initAlgorithm(self, config=None):  # noqa: N802
        self.addParameter(
            QgsProcessingParameterFile(self.INPUT, "KOF-fil", extension="kof")
        )
        self.addParameter(
            QgsProcessingParameterCrs(
                self.CRS, "Koordinatsystem (tom = fra filen)", optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT, "KOF-punkter", QgsProcessing.TypeVectorPoint
            )
        )

    def processAlgorithm(self, parameters, context, feedback):  # noqa: N802
        path = self.parameterAsFile(parameters, self.INPUT, context)
        result = parse_file(path)
        for warning in result.warnings:
            feedback.pushWarning(warning)

        crs = self.parameterAsCrs(parameters, self.CRS, context)
        if crs.isValid():
            feedback.pushInfo(f"Bruker valgt koordinatsystem {crs.authid()}")
        else:
            epsg = detect_crs(result.metadata)
            if epsg is None:
                raise QgsProcessingException(
                    "Fant ikke koordinatsystem i filen. Velg koordinatsystem manuelt."
                )
            crs = QgsCoordinateReferenceSystem(f"EPSG:{epsg}")
            feedback.pushInfo(f"Koordinatsystem fra filen: {crs.authid()}")
        if detect_vertical_crs(result.metadata):
            feedback.pushInfo("Høyder er oppgitt i NN2000")

        fields = point_fields()
        sink, dest_id = self.parameterAsSink(
            parameters, self.OUTPUT, context, fields, POINT_WKB_TYPE, crs
        )
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        for feature in point_features(result, fields):
            if feedback.isCanceled():
                break
            sink.addFeature(feature, QgsFeatureSink.FastInsert)

        if context.willLoadLayerOnCompletion(dest_id):
            context.layerToLoadOnCompletionDetails(dest_id).name = Path(path).stem

        feedback.pushInfo(
            f"{len(result.points)} punkter importert, "
            f"{len(result.warnings)} linjer ignorert (tegnkoding {result.encoding})"
        )
        return {self.OUTPUT: dest_id}
