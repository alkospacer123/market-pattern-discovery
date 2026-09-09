from market_pattern_discovery.research import *


def cell(track):
    return ResearchCell("CNY", ResearchHorizon.SCALPING, "M1", ("M15",), track)


def test_tracks_receive_same_contract_and_unknown_has_no_family_filter(tmp_path):
    seen = []
    def handler(**contract):
        seen.append(tuple(contract))
        evaluation = Evaluation("e1", .1, 10, {"hypothesis_id": "h1"})
        return ScientificResult("arbitrary-open-search", "h1", evaluation,
                                Evidence("e1", True, "enough data"))
    executor = UnifiedResearchExecutor(handler, handler)
    known, _ = executor.execute(cell(ResearchTrack.KNOWN), 1, 2, 3)
    unknown, _ = executor.execute(cell(ResearchTrack.UNKNOWN), 1, 2, 3)
    assert seen == [("cell", "market_data", "context", "features")] * 2
    assert unknown.discovery_method == "arbitrary-open-search"
    memory = ResearchMemory(tmp_path)
    assert memory.record_research_attempt(known)
    assert memory.record_research_attempt(unknown)
    assert not memory.record_research_attempt(unknown)
    assert len(memory.research_attempts()) == 2


def test_label_only_handler_is_rejected():
    executor = UnifiedResearchExecutor(lambda **_: {"discovery_method": "fake"},
                                       lambda **_: {"discovery_method": "fake"})
    import pytest
    with pytest.raises(TypeError, match="ScientificResult"):
        executor.execute(cell(ResearchTrack.KNOWN), 1, 2, 3)
