"""Gruppering av gjentatte målinger av samme punkt."""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import mean, stdev
from typing import List, Optional, Sequence

from .kof_parser import KofPoint


@dataclass
class PointGroup:
    members: List[KofPoint]
    north: float
    east: float
    height: Optional[float]
    std_north: float
    std_east: float
    std_height: Optional[float]
    # Største horisontale avstand fra et medlem til middelpunktet.
    max_deviation: float

    @property
    def names(self) -> List[str]:
        return [p.name for p in self.members]


def find_groups(
    points: Sequence[KofPoint],
    tolerance: float = 0.05,
    height_tolerance: Optional[float] = None,
    include_singles: bool = False,
) -> List[PointGroup]:
    """Grupper punkter som ligger innenfor `tolerance` meter horisontalt.

    To punkter havner i samme gruppe hvis de er naboer, eller er knyttet
    sammen via en kjede av naboer (single linkage). Med `height_tolerance`
    må høydeforskjellen også være innenfor den grensen.
    """
    parent = list(range(len(points)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    # Sorter på Ø, så vi kan stoppe når avstanden i Ø alene er for stor.
    order = sorted(range(len(points)), key=lambda i: points[i].east)
    for a_pos, a in enumerate(order):
        pa = points[a]
        for b in order[a_pos + 1:]:
            pb = points[b]
            if pb.east - pa.east > tolerance:
                break
            if math.hypot(pa.north - pb.north, pa.east - pb.east) > tolerance:
                continue
            if height_tolerance is not None and not _heights_close(pa, pb, height_tolerance):
                continue
            parent[find(a)] = find(b)

    clusters: dict = {}
    for i in range(len(points)):
        clusters.setdefault(find(i), []).append(points[i])

    groups = [
        _summarize(members)
        for members in clusters.values()
        if include_singles or len(members) > 1
    ]
    groups.sort(key=lambda g: g.members[0].line_no)
    return groups


def _heights_close(a: KofPoint, b: KofPoint, tolerance: float) -> bool:
    if a.height is None or b.height is None:
        return True
    return abs(a.height - b.height) <= tolerance


def _std(values: List[float]) -> float:
    return stdev(values) if len(values) > 1 else 0.0


def _summarize(members: List[KofPoint]) -> PointGroup:
    members = sorted(members, key=lambda p: p.line_no)
    north = mean(p.north for p in members)
    east = mean(p.east for p in members)
    heights = [p.height for p in members if p.height is not None]
    return PointGroup(
        members=members,
        north=north,
        east=east,
        height=mean(heights) if heights else None,
        std_north=_std([p.north for p in members]),
        std_east=_std([p.east for p in members]),
        std_height=_std(heights) if heights else None,
        max_deviation=max(math.hypot(p.north - north, p.east - east) for p in members),
    )
