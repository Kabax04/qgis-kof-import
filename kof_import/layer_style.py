"""Standardstil og etiketter for lagene fra KOF-importen."""

from qgis.core import (
    QgsFillSymbol,
    QgsLineSymbol,
    QgsMarkerSymbol,
    QgsPalLayerSettings,
    QgsProcessingLayerPostProcessorInterface,
    QgsSingleSymbolRenderer,
    QgsTextBufferSettings,
    QgsTextFormat,
    QgsVectorLayerSimpleLabeling,
)
from qgis.PyQt.QtGui import QColor


def _labeling(field: str) -> QgsVectorLayerSimpleLabeling:
    text_format = QgsTextFormat()
    text_format.setSize(8)
    buffer = QgsTextBufferSettings()
    buffer.setEnabled(True)
    buffer.setSize(0.8)
    buffer.setColor(QColor("white"))
    text_format.setBuffer(buffer)

    settings = QgsPalLayerSettings()
    settings.fieldName = field
    settings.setFormat(text_format)
    settings.dist = 1.0
    return QgsVectorLayerSimpleLabeling(settings)


def style_points(layer) -> None:
    """Små mørke sirkler med punktnavn."""
    symbol = QgsMarkerSymbol.createSimple(
        {"name": "circle", "size": "1.8", "color": "40,40,40", "outline_color": "white"}
    )
    layer.setRenderer(QgsSingleSymbolRenderer(symbol))
    layer.setLabeling(_labeling("navn"))
    layer.setLabelsEnabled(True)
    layer.triggerRepaint()


def style_groups(layer) -> None:
    """Røde kryss med navnene på alle målingene i gruppen."""
    symbol = QgsMarkerSymbol.createSimple(
        {"name": "cross2", "size": "3", "color": "200,30,30", "outline_width": "0.4"}
    )
    layer.setRenderer(QgsSingleSymbolRenderer(symbol))
    layer.setLabeling(_labeling("navn_liste"))
    layer.setLabelsEnabled(True)
    layer.triggerRepaint()


def style_lines(layer) -> None:
    """Blå linjer."""
    symbol = QgsLineSymbol.createSimple({"line_color": "30,90,200", "line_width": "0.5"})
    layer.setRenderer(QgsSingleSymbolRenderer(symbol))
    layer.triggerRepaint()


def style_polygons(layer) -> None:
    """Halvgjennomsiktig blå fyll med kantlinje."""
    symbol = QgsFillSymbol.createSimple(
        {"color": "30,90,200,60", "outline_color": "30,90,200", "outline_width": "0.4"}
    )
    layer.setRenderer(QgsSingleSymbolRenderer(symbol))
    layer.triggerRepaint()


class StylePostProcessor(QgsProcessingLayerPostProcessorInterface):
    """Setter stil på et lag når Processing laster det inn i prosjektet."""

    # Processing tar ikke eierskap til Python-objektet, så vi må holde på det.
    _instances = []

    def __init__(self, style_function):
        super().__init__()
        self.style_function = style_function

    def postProcessLayer(self, layer, context, feedback):  # noqa: N802
        self.style_function(layer)

    @classmethod
    def create(cls, style_function):
        instance = cls(style_function)
        cls._instances.append(instance)
        return instance
