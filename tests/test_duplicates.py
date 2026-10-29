import pytest

from kof_import.duplicates import find_groups, find_near_misses
from kof_import.kof_parser import KofPoint


def test_topcon_5_cm(topcon):
    groups = find_groups(topcon.points, tolerance=0.05)
    assert [g.names for g in groups] == [
        ["104", "105", "106"],
        ["109", "110", "111"],
        ["112", "113", "114"],
        ["115", "117", "120"],
        ["116", "118", "119"],
    ]


def test_topcon_10_cm_tar_med_102_og_108(topcon):
    names = [g.names for g in find_groups(topcon.points, tolerance=0.10)]
    assert ["102", "108"] in names
    assert len(names) == 6


def test_100_og_104_slaas_aldri_sammen(topcon):
    for g in find_groups(topcon.points, tolerance=1.0, height_tolerance=0.5):
        assert not {"100", "104"} <= set(g.names)


def test_middel_og_spredning(topcon):
    group = find_groups(topcon.points)[0]  # 104, 105, 106
    assert group.north == pytest.approx((6615799.708 + 6615799.707 + 6615799.695) / 3)
    assert group.east == pytest.approx((599668.467 + 599668.474 + 599668.469) / 3)
    assert group.height == pytest.approx((96.967 + 96.974 + 96.955) / 3)
    assert 0 < group.std_north < 0.01
    assert 0 < group.max_deviation < 0.02


def test_med_enkeltpunkter(topcon):
    groups = find_groups(topcon.points, include_singles=True)
    assert sum(len(g.members) for g in groups) == 21
    assert len(groups) == 21 - 5 * 2


def test_nesten_treff_102_og_108(topcon):
    misses = find_near_misses(topcon.points, tolerance=0.05)
    assert [(m.a.name, m.b.name) for m in misses] == [("102", "108")]
    assert misses[0].distance == pytest.approx(0.0607, abs=0.001)


def test_ingen_nesten_treff_naar_de_er_gruppert(topcon):
    assert find_near_misses(topcon.points, tolerance=0.10) == []


def test_kjede_i_samme_gruppe_er_ikke_nesten_treff():
    points = [KofPoint(f"P{i}", "", 0.0, 0.04 * i, None, i) for i in range(3)]
    assert len(find_groups(points, tolerance=0.05)) == 1
    assert find_near_misses(points, tolerance=0.05) == []
