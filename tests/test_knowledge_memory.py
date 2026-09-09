from market_pattern_discovery.research import KnowledgeRecord, ResearchMemory


def test_knowledge_is_append_only_deduplicated_and_restart_safe(tmp_path):
    record = KnowledgeRecord("CNY", "Scalping", "M1", "M15", "UNKNOWN",
        "evaluation-1", "unresolved", "CURRENT", {"method": "open"})
    first = ResearchMemory(tmp_path)
    assert first.add_knowledge_record(record)
    assert not first.add_knowledge_record(record)
    restarted = ResearchMemory(tmp_path)
    assert len(restarted.knowledge_records()) == 1
    assert restarted.knowledge_records()[0]["knowledge_id"] == record.identity
    # Existing memory APIs remain independently readable.
    assert restarted.experiments() == []


def test_metadata_order_does_not_change_identity():
    args = ("Si", "Intraday", "M5", "H1", "KNOWN", "e", "positive", "CURRENT")
    assert KnowledgeRecord(*args, {"a": 1, "b": 2}).identity == KnowledgeRecord(*args, {"b": 2, "a": 1}).identity
