"""Bygg linjer og flater fra programkodene i 09-blokker.

Ren Python uten QGIS-avhengigheter. Kodene følger KOF-spesifikasjonen 2.00
(Norkart, 2005), kapittel 4.2.2 Linjemåling:

    91  start enkel rett linje      92  start spline     93  start sirkelbue
    94  start punktsverm (ingen geometri)
    72-79  start 2-9 samtidige linjer, sagmetoden   (A, B, C, A, B, C, ...)
    82-89  start 2-9 samtidige linjer, bølgemetoden (A, B, C, C, B, A, A, ...)
    96  slutt, lukk til polygon     99  slutt linje/sverm

En ny start avslutter forrige linje. Punkter med beregningskode 37 er
enkeltpunkter og hører ikke til linjen. Andre programkoder (39-64) påvirker
ikke linjer og ignoreres her.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:  # kof_parser importerer denne modulen
    from .kof_parser import KofPoint

SINGLE_KINDS = {91: "linje", 92: "spline", 93: "bue"}
SWARM = 94
CLOSE = 96
END = 99
SINGLE_POINT_BK = 37


@dataclass
class KofLine:
    # "linje", "spline" eller "bue"
    kind: str
    pi: int
    # Linjen i filen der 09-blokken som startet linjen står.
    line_no: int
    points: List[KofPoint] = field(default_factory=list)
    closed: bool = False


def is_line_start(pi: int) -> bool:
    return pi in SINGLE_KINDS or pi == SWARM or 72 <= pi <= 79 or 82 <= pi <= 89


class LineTracker:
    def __init__(self, warnings: List[str]):
        self.lines: List[KofLine] = []
        self.warnings = warnings
        self._active: List[KofLine] = []
        self._pi: Optional[int] = None
        self._count = 0

    def program(self, pi: int, line_no: int) -> None:
        if is_line_start(pi):
            if self._pi is not None:
                self._finish(closed=False)
            self._start(pi, line_no)
        elif pi == CLOSE:
            if not self._active:
                self.warnings.append(f"Linje {line_no}: 09 96 (lukk polygon) uten aktiv linje")
            self._finish(closed=True)
        elif pi == END:
            self._finish(closed=False)

    def point(self, point: KofPoint) -> None:
        if not self._active or point.bk == SINGLE_POINT_BK:
            return
        self._active[self._line_index(self._count)].points.append(point)
        self._count += 1

    def finish(self) -> List[KofLine]:
        """Kalles ved filslutt. Returnerer alle ferdige linjer."""
        if self._pi is not None and self._pi != SWARM:
            self.warnings.append(
                f"Linje {self._active[0].line_no}: linjen ble ikke avsluttet med 09 99 eller 96"
            )
        self._finish(closed=False)
        return self.lines

    def _start(self, pi: int, line_no: int) -> None:
        self._pi = pi
        self._count = 0
        if pi == SWARM:
            self._active = []
            return
        if pi == 92:
            self.warnings.append(f"Linje {line_no}: spline (09 92) tegnes som rette linjer")
        kind = SINGLE_KINDS.get(pi, "linje")
        self._active = [KofLine(kind, pi, line_no) for _ in range(self._line_count(pi))]

    @staticmethod
    def _line_count(pi: int) -> int:
        if 72 <= pi <= 79:
            return pi - 70
        if 82 <= pi <= 89:
            return pi - 80
        return 1

    def _line_index(self, k: int) -> int:
        n = len(self._active)
        if 82 <= self._pi <= 89:
            # Bølgemetoden: fram og tilbake, A B C C B A A B C ...
            pos = k % (2 * n)
            return pos if pos < n else 2 * n - 1 - pos
        return k % n

    def _finish(self, closed: bool) -> None:
        for line in self._active:
            minimum = 3 if closed else 2
            if len(line.points) >= minimum:
                line.closed = closed
                self.lines.append(line)
            elif closed and len(line.points) == 2:
                self.warnings.append(
                    f"Linje {line.line_no}: polygon med bare 2 punkter, tegnes som linje"
                )
                self.lines.append(line)
            else:
                self.warnings.append(
                    f"Linje {line.line_no}: linje med {len(line.points)} punkt(er) ignorert"
                )
        self._active = []
        self._pi = None
        self._count = 0
