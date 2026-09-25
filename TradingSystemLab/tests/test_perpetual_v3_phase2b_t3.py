from TradingSystemLab.perpetual_v3_phase2b_t3 import (
    BASELINE, PARAMETER_SPACE, bounded_design, configuration_id, neighbors,
)


def test_exact_oat_design_and_stable_ids():
    rows = bounded_design()
    assert len(rows) == 22
    assert sum(row == BASELINE for row in rows) == 1
    assert len({configuration_id("M30", row) for row in rows}) == 22
    assert [value.rsplit("-", 1)[1] for value in map(lambda row: configuration_id("M30", row), rows)] == [
        value.rsplit("-", 1)[1] for value in map(lambda row: configuration_id("H1", row), rows)
    ]
    for row in rows:
        assert sum(row[name] != BASELINE[name] for name in PARAMETER_SPACE) in (0, 1)
        assert all(row[name] in PARAMETER_SPACE[name] for name in PARAMETER_SPACE)


def test_neighbors_are_only_adjacent_single_factor_levels():
    rows = bounded_design()
    for index, row in enumerate(rows):
        for other_index in neighbors(rows, index):
            differing = [name for name in PARAMETER_SPACE if row[name] != rows[other_index][name]]
            assert len(differing) == 1
            values = PARAMETER_SPACE[differing[0]]
            assert abs(values.index(row[differing[0]]) - values.index(rows[other_index][differing[0]])) == 1
