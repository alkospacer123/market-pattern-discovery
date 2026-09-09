import pytest
from market_pattern_discovery.research import (MultiHorizonScheduler, PROFILES,
    ResearchCell, ResearchHorizon, ResearchTrack, research_space)


def test_profiles_and_space_cover_both_symbols_and_tracks():
    cells = research_space()
    assert len(cells) == 28
    assert {c.symbol for c in cells} == {"CNY", "Si"}
    assert {c.research_track for c in cells} == set(ResearchTrack)
    assert PROFILES[ResearchHorizon.INTRADAY] == (("M5", "M15", "M30"), ("H1", "D1"))


def test_cell_rejects_profile_leakage():
    with pytest.raises(ValueError):
        ResearchCell("CNY", ResearchHorizon.SCALPING, "D1", ("M15",), ResearchTrack.KNOWN)


def test_scheduler_is_deterministic_and_skips_completed():
    scheduler = MultiHorizonScheduler(seed=7)
    first = scheduler.plan(set(), 3)
    assert first == MultiHorizonScheduler(seed=7).plan(set(), 3)
    assert not ({c.identity for c in first} & {c.identity for c in scheduler.plan({c.identity for c in first}, 25)})
