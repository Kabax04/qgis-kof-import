from pathlib import Path

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsFeatureSink,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterCrs,
    QgsProcessingParameterDistance,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFile,
    QgsProcessingParameterNumber,
)

from ..crs_detect import crs_from_sosi_code, detect_crs, detect_vertical_crs
from ..duplicates import find_groups, find_near_misses
from ..kof_parser import parse_file
from ..layer_builder import (
    POINT_WKB_TYPE,
    group_features,
    group_fields,
    point_features,
    point_fields,
)
from ..layer_style import StylePostProcessor, style_groups, style_points


class ImportKofAlgorithm(QgsProcessingAlgorithm):
    INPUT = "INPUT"
    CRS = "CRS"
    OUTPUT = "OUTPUT"
    TOLERANCE = "TOLERANCE"
    HEIGHT_TOLERANCE = "HEIGHT_TOLERANCE"
    INCLUDE_SINGLES = "INCLUDE_SINGLES"
    OUTPUT_GROUPS = "OUTPUT_GROUPS"

    def name(self):
        return "importkof"

    def displayName(self):  # noqa: N802
        return "Importer KOF-fil"

    def shortHelpString(self):  # noqa: N802
        return (
            "Leser punkter (05-poster) fra en KOF-fil og lager et PointZ-lag.\n\n"
            "Koordinatsystemet hentes fra filhodet (f.eks. «Projeksjon: EUREF89 UTM 32»). "
            "Velg CRS manuelt hvis filen ikke oppgir det, eller for å overstyre.\n\n"
            "Gjentatte målinger: punkter som ligger innenfor toleransen horisontalt "
            "(direkte eller via en kjede av naboer) slås sammen til ett middelpunkt med "
            "standardavvik og største avvik. Punktpar som ligger opptil dobbel toleranse "
            "fra hverandre, rapporteres som advarsel i loggen."
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
        self.addParameter(
            QgsProcessingParameterDistance(
                self.TOLERANCE,
                "Toleranse for gjentatte målinger (horisontalt)",
                defaultValue=0.05,
                parentParameterName=self.CRS,
                minValue=0.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.HEIGHT_TOLERANCE,
                "Høydetoleranse (tom = ingen krav)",
                type=QgsProcessingParameterNumber.Double,
                optional=True,
                minValue=0.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.INCLUDE_SINGLES,
                "Ta med punkter som bare er målt én gang i middellaget",
                defaultValue=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_GROUPS,
                "Middel av gjentatte målinger",
                QgsProcessing.TypeVectorPoint,
                optional=True,
                createByDefault=True,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):  # noqa: N802
        path = self.parameterAsFile(parameters, self.INPUT, context)
        result = parse_file(path)
        for warning in result.warnings:
            feedback.pushWarning(warning)

        crs = self._crs(parameters, context, feedback, result)

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

        outputs = {self.OUTPUT: dest_id}
        stem = Path(path).stem
        self._configure_output(context, dest_id, stem, style_points)
        feedback.pushInfo(
            f"{len(result.points)} punkter importert, "
            f"{len(result.warnings)} linjer ignorert (tegnkoding {result.encoding})"
        )

        groups_id = self._write_groups(parameters, context, feedback, result, crs)
        if groups_id is not None:
            outputs[self.OUTPUT_GROUPS] = groups_id
            self._configure_output(context, groups_id, f"{stem} (middel)", style_groups)
        return outputs

    def _crs(self, parameters, context, feedback, result):
        crs = self.parameterAsCrs(parameters, self.CRS, context)
        if crs.isValid():
            feedback.pushInfo(f"Bruker valgt koordinatsystem {crs.authid()}")
        else:
            sosi_code = result.header.crs_code if result.header else None
            if sosi_code is not None and crs_from_sosi_code(sosi_code) is None:
                feedback.pushWarning(
                    f"Ukjent koordinatsystemkode {sosi_code} i 01-blokken, ignorert"
                )
            epsg = detect_crs(result.metadata, sosi_code)
            if epsg is None:
                raise QgsProcessingException(
                    "Fant ikke koordinatsystem i filen. Velg koordinatsystem manuelt."
                )
            crs = QgsCoordinateReferenceSystem(f"EPSG:{epsg}")
            feedback.pushInfo(f"Koordinatsystem fra filen: {crs.authid()}")
        if detect_vertical_crs(result.metadata):
            feedback.pushInfo("Høyder er oppgitt i NN2000")
        return crs

    def _write_groups(self, parameters, context, feedback, result, crs):
        tolerance = self.parameterAsDouble(parameters, self.TOLERANCE, context)
        height_tolerance = None
        if parameters.get(self.HEIGHT_TOLERANCE) is not None:
            height_tolerance = self.parameterAsDouble(
                parameters, self.HEIGHT_TOLERANCE, context
            )
        include_singles = self.parameterAsBoolean(parameters, self.INCLUDE_SINGLES, context)

        repeated = find_groups(result.points, tolerance, height_tolerance)
        feedback.pushInfo(
            f"{len(repeated)} grupper av gjentatte målinger (toleranse {tolerance} m)"
        )
        for g in repeated:
            feedback.pushInfo(
                f"  {','.join(g.names)}: største avvik {g.max_deviation * 1000:.1f} mm"
            )
        for miss in find_near_misses(result.points, tolerance, height_tolerance):
            feedback.pushWarning(
                f"{miss.a.name} og {miss.b.name} ligger {miss.distance:.3f} m fra "
                f"hverandre, litt utenfor toleransen. Sjekk om de er samme punkt."
            )

        fields = group_fields()
        sink, dest_id = self.parameterAsSink(
            parameters, self.OUTPUT_GROUPS, context, fields, POINT_WKB_TYPE, crs
        )
        if sink is None:
            return None
        groups = (
            find_groups(result.points, tolerance, height_tolerance, include_singles=True)
            if include_singles
            else repeated
        )
        for feature in group_features(groups, fields, result.source):
            sink.addFeature(feature, QgsFeatureSink.FastInsert)
        return dest_id

    @staticmethod
    def _configure_output(context, dest_id, name, style_function):
        if context.willLoadLayerOnCompletion(dest_id):
            details = context.layerToLoadOnCompletionDetails(dest_id)
            details.name = name
            details.setPostProcessor(StylePostProcessor.create(style_function))
