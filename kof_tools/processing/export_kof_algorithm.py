from qgis.core import (
    Qgis,
    QgsFeatureRequest,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterCrs,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterFileDestination,
)

from ..crs_detect import sosi_code_from_epsg
from ..i18n import tr
from ..kof_writer import KofWriter

# QGIS 3.36 moved these enums to Qgis. QGIS 4 (Qt6) only has the scoped names.
if Qgis.QGIS_VERSION_INT >= 33600:
    VECTOR_POINT = Qgis.ProcessingSourceType.VectorPoint
    FIELD_ANY = Qgis.ProcessingFieldParameterDataType.Any
else:
    VECTOR_POINT = QgsProcessing.SourceType.TypeVectorPoint
    FIELD_ANY = QgsProcessingParameterField.DataType.Any

# (label, Python codec) for the ENCODING parameter.
ENCODINGS = (("Windows-1252", "cp1252"), ("UTF-8", "utf-8"))


def _value(feature, index):
    """The attribute, or None for NULL. Whole numbers stored as decimals lose the ".0"."""
    if index < 0:
        return None
    value = feature.attribute(index)
    # QGIS 3 returns NULL as an invalid QVariant, QGIS 4 as None.
    if value is None or (hasattr(value, "isNull") and value.isNull()):
        return None
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _text(value) -> str:
    return "" if value is None else str(value)


class ExportKofAlgorithm(QgsProcessingAlgorithm):
    INPUT = "INPUT"
    NAME_FIELD = "NAME_FIELD"
    CODE_FIELD = "CODE_FIELD"
    HEIGHT_FIELD = "HEIGHT_FIELD"
    BK_FIELD = "BK_FIELD"
    REMARK_FIELD = "REMARK_FIELD"
    TARGET_CRS = "TARGET_CRS"
    ENCODING = "ENCODING"
    OUTPUT = "OUTPUT"

    def name(self):
        return "exportkof"

    def displayName(self):  # noqa: N802
        return tr("Export to KOF file")

    def shortHelpString(self):  # noqa: N802
        return tr("HELP_EXPORT")

    def createInstance(self):  # noqa: N802
        return ExportKofAlgorithm()

    def initAlgorithm(self, config=None):  # noqa: N802
        self.addParameter(
            QgsProcessingParameterFeatureSource(self.INPUT, tr("Point layer"), [VECTOR_POINT])
        )
        # The defaults match the fields of layers made by the import.
        for key, description, default in (
            (self.NAME_FIELD, tr("Point name field (empty = number the points)"), "name"),
            (self.CODE_FIELD, tr("Code field"), "code"),
            (self.HEIGHT_FIELD, tr("Height field (empty = Z of the geometry)"), "H"),
            (self.BK_FIELD, tr("Calculation code field"), "calc_code"),
            (self.REMARK_FIELD, tr("Remark field"), "remark"),
        ):
            self.addParameter(
                QgsProcessingParameterField(
                    key, description, defaultValue=default, parentLayerParameterName=self.INPUT,
                    type=FIELD_ANY, optional=True,
                )
            )
        self.addParameter(
            QgsProcessingParameterCrs(
                self.TARGET_CRS, tr("Coordinate reference system in the file (empty = the layer's)"),
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.ENCODING, tr("Encoding"), options=[label for label, _ in ENCODINGS], defaultValue=0
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(self.OUTPUT, tr("KOF file"), tr("KOF files (*.kof)"))
        )

    def processAlgorithm(self, parameters, context, feedback):  # noqa: N802
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
        path = self.parameterAsFileOutput(parameters, self.OUTPUT, context)
        encoding = ENCODINGS[self.parameterAsEnum(parameters, self.ENCODING, context)][1]

        crs = self.parameterAsCrs(parameters, self.TARGET_CRS, context)
        if not crs.isValid():
            crs = source.sourceCrs()
        if not crs.isValid() or crs.isGeographic():
            raise QgsProcessingException(tr(
                "KOF files hold projected coordinates (north and east in metres), but {crs} is not projected. "
                "Select a projected coordinate reference system for the file, e.g. EUREF89 UTM 32 (EPSG:25832).",
                crs=crs.authid() or crs.description() or "?",
            ))
        epsg = crs.postgisSrid() if crs.authid().upper().startswith("EPSG:") else None
        if epsg is None or sosi_code_from_epsg(epsg) is None:
            feedback.pushWarning(tr(
                "{crs} has no SOSI coordinate system code. The 01 block is written without one, "
                "and some instruments may not recognise the coordinate reference system.",
                crs=crs.authid(),
            ))
        if crs != source.sourceCrs():
            feedback.pushInfo(tr(
                "Transforming from {source} to {target}",
                source=source.sourceCrs().authid(), target=crs.authid(),
            ))

        fields = source.fields()
        indexes = {}
        for key in (self.NAME_FIELD, self.CODE_FIELD, self.HEIGHT_FIELD, self.BK_FIELD, self.REMARK_FIELD):
            name = self.parameterAsString(parameters, key, context)
            index = fields.lookupField(name) if name else -1
            if name and index < 0:
                feedback.pushInfo(tr("The layer has no field {field}, not used", field=name))
            indexes[key] = index

        writer = KofWriter()
        writer.comment(f"Exported from QGIS {Qgis.version()} with KOF Tools")
        writer.header(job=source.sourceName(), epsg=epsg)

        request = QgsFeatureRequest().setDestinationCrs(crs, context.transformContext())
        total = source.featureCount()
        number = 0
        for current, feature in enumerate(source.getFeatures(request)):
            if feedback.isCanceled():
                break
            name = _text(_value(feature, indexes[self.NAME_FIELD]))
            code = _text(_value(feature, indexes[self.CODE_FIELD]))
            bk = _value(feature, indexes[self.BK_FIELD])
            remark = _text(_value(feature, indexes[self.REMARK_FIELD]))
            # A multipoint gives one 05 record per part, all with the same name.
            # No geometry gives one record without coordinates, which the writer reports.
            vertices = list(feature.geometry().vertices()) if feature.hasGeometry() else []
            vertices = vertices or [None]
            for vertex in vertices:
                number += 1
                if indexes[self.HEIGHT_FIELD] >= 0:
                    height = _value(feature, indexes[self.HEIGHT_FIELD])
                elif vertex is not None and vertex.is3D():
                    height = vertex.z()
                else:
                    height = None
                writer.point(
                    name if indexes[self.NAME_FIELD] >= 0 else str(number),
                    code,
                    vertex.y() if vertex is not None else None,
                    vertex.x() if vertex is not None else None,
                    height,
                    bk,
                    remark,
                )
            if total:
                feedback.setProgress(100 * (current + 1) / total)

        for warning in writer.save(path, encoding):
            feedback.pushWarning(warning)
        feedback.pushInfo(tr(
            "{count} points written to {path} ({encoding})",
            count=writer.points, path=path, encoding=encoding,
        ))
        return {self.OUTPUT: path}
