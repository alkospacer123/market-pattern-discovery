"""CC-07: independent Windows operator stage, not yet deployed or UI-callable."""
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'controller/cc07-v20-operator.ps1'
SCRIPT=PATH.read_text(encoding='utf-8')

def test_action_semantics_and_immutable_v20_operator():
    assert "'start','pause','stop','restart'" in SCRIPT
    assert "'preview','execute'" in SCRIPT
    assert "6f539f9c421efb56d492f1c903b998b4e8f4a9ca" in SCRIPT
    assert "93fc1ce4aded6c40453da14deb4846e10da1b14f" in SCRIPT
    assert "$modeStock=if($action -in @('pause','stop')){'stop'}else{$action}" in SCRIPT
    assert "stop-scheduledtask" in SCRIPT
    assert "flat" in SCRIPT and "v20_08_4_active_orders=0" in SCRIPT
    assert "v20_08_4_positions=0" in SCRIPT

def test_admin_release_and_durable_audit_required_before_change():
    for required in (
        "cc07_admin_required", "cc07_operator_sid_mismatch",
        "cc07_no_matching_release", "cc07_release_expired",
        "cc07_duplicate_request_id", "cc07_confirmation_refused",
        "cc07_audit_full", "cc07_untrusted_writer",
        "$stream.flush($true)", "Global\\ControlCenter_CC07_V20",
        "audit 'began' 'preflight_pass'", "unknown_outcome_reconcile_manually",
    ):
        assert required in SCRIPT
    assert SCRIPT.index("if($action -ne 'pause'){release}") < SCRIPT.index("stop-scheduledtask")
    assert SCRIPT.index("audit 'began' 'preflight_pass'") < SCRIPT.index("$modeStock=if")

def test_not_called_by_streamlit_or_legacy_h1():
    ui=(ROOT/'v20_app.py').read_text(encoding='utf-8')
    assert "cc07-v20-operator" not in ui
    assert "stop-scheduledtask" not in ui.lower()
    assert "'c:\\tradingsystemlab" not in SCRIPT.lower()
    assert "'c:\\intradaylab" not in SCRIPT.lower()
    assert "mode='preview'" in SCRIPT
    assert not re.search(r'(^|\n)\s*(register-scheduledtask|start-scheduledtask|remove-item)\b',SCRIPT,re.I)
