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

def test_windows_powershell_native_parser():
    import os
    import subprocess
    import pytest
    if os.name != 'nt':
        pytest.skip('native Windows PowerShell parser only')
    # Syntax only: ParseFile NEVER executes the operator or accesses FINAM.
    literal=str(PATH).replace("'", "''")
    command=("$errors=$null;$tokens=$null;"
             "[void][system.management.automation.language.parser]::parsefile('"
             +literal+"',[ref]$tokens,[ref]$errors);"
             "if($errors.count -ne 0){$errors|out-string|write-output;exit 1}")
    child=subprocess.run(['powershell.exe','-noprofile','-noninteractive',
                          '-command',command],
                         capture_output=True,text=True,timeout=15,check=False)
    assert child.returncode == 0, child.stdout+child.stderr


def test_halted_check_requires_exact_native_exit_and_brokerless_proof():
    """Regression: PowerShell's stderr must not abort before checking HALTED proof."""
    assert "$ErrorActionPreference='Continue'" in SCRIPT
    assert '$checkexit=$lastexitcode' in SCRIPT
    assert "V20_08_5_HEALTH_PARTIAL" in SCRIPT
    assert "HALTED_NO_NEW_ENTRIES" in SCRIPT
    assert "$checkexit -eq 1" in SCRIPT
    assert "$checkexit -eq 0" in SCRIPT
    assert "cc07_check_not_expected_halted_partial" in SCRIPT
    assert "cc07_armed_check_failed" in SCRIPT
    assert "cc07_stock_readonly_banner_missing" in SCRIPT
    assert "cc07_cycle_stale" in SCRIPT



def test_postflight_waits_for_one_verified_cycle_without_rearming():
    # CC-only settlement after a single stock ARM. No retry of stock execution.
    assert "function settle([string]$target)" in SCRIPT
    settle = SCRIPT.split("function settle([string]$target)", 1)[1].split("function flat {", 1)[0]
    assert "for($attempt=0;$attempt -lt 12;$attempt++)" in settle
    assert "start-sleep -seconds 5" in settle
    assert "cc07_postflight_unsettled" in settle
    assert "$got=proof" in settle
    assert "cc07_postflight_wrong_switch" in settle
    assert "powershell.exe" not in settle
    assert "stop-scheduledtask" not in settle
    assert "cc07_armed_check_failed" in settle
    assert "cc07_check_not_expected_halted_partial" in settle
    assert "$after=settle $expected" in SCRIPT
    assert "$state=proof ($action -eq 'pause')" in SCRIPT
    assert "$state=proof ($mode -eq 'execute' -and $action -eq 'pause')" in SCRIPT
    assert "if(-not ($allowArmedHalted -and $pending))" in SCRIPT


def test_native_halted_partial_and_negative_cases_without_real_v20(tmp_path):
    """Run extracted PowerShell function against mocked child (no V20 access)."""
    import os
    import subprocess
    import pytest
    if os.name != "nt":
        pytest.skip("native Windows PowerShell only")
    payload = r'''
$ErrorActionPreference='Stop'
$source=get-content -literalpath $env:cc07_source_file -raw -encoding utf8
$start=$source.indexof('function proof(')
$end=$source.indexof('function flat {')
if($start -lt 0 -or $end -le $start){throw 'proof_not_found'}
invoke-expression $source.substring($start,$end-$start)
function need([bool]$condition,[string]$code){if(-not $condition){throw $code}}
$robot='v20-shallow'
$operator='do-not-touch-v20.ps1'
function powershell.exe {
    'NO_ORDER_NO_CANCEL_NO_FINAM_API_NO_SQLITE_OPEN_NO_TASK_MUTATION_NO_REARM=YES'
    'v20_08_5_v20-shallow_task='+$script:mocktask
    'v20_08_5_v20-shallow_switch='+$script:mockswitch
    'v20_08_5_v20-shallow_age_seconds='+$script:mockage
    'v20_08_5_v20-shallow_cycle='+$script:mockcycle
    'v20_08_5_v20-shallow_cycle_code='+$script:mockcode
    if($script:mockerror){
        write-error $script:mockerror
    }
    $global:lastexitcode=$script:mockexit
}
function testcase([string]$name,[int]$exit,[string]$err,[string]$task,[string]$age,[bool]$shouldpass){
    $script:mockswitch='HALTED'
    $script:mockcycle='HALTED'
    $script:mockcode='HALTED_NO_NEW_ENTRIES'
    $script:mockexit=$exit
    $script:mockerror=$err
    $script:mocktask=$task
    $script:mockage=$age
    $passed=$false
    try{$status=proof;$passed=($status -ceq 'HALTED')}catch{$passed=$false}
    if($passed -ne $shouldpass){throw ('cc07_native_wrong_result_'+$name)}
    write-output ('cc07_native_'+$name+'=pass')
}
testcase 'expected_halted' 1 'V20_08_5_HEALTH_PARTIAL' 'Running' '12' $true
testcase 'unexpected_nonzero' 1 'NOT_A_HEALTH_PARTIAL' 'Running' '12' $false
testcase 'healthy_exit_but_halted' 0 '' 'Running' '12' $false
testcase 'stale_halted' 1 'V20_08_5_HEALTH_PARTIAL' 'Running' '120' $false
testcase 'not_running' 1 'V20_08_5_HEALTH_PARTIAL' 'Ready' '12' $false

# Transitional ARMED/HALTED is unacceptable for START proof.
$script:mockswitch='ARMED'
$script:mockcycle='HALTED'
$script:mockcode='HALTED_NO_NEW_ENTRIES'
$script:mocktask='Running'
$script:mockage='12'
$script:mockerror='V20_08_5_HEALTH_PARTIAL'
$script:mockexit=1
$allowed=$false
try{$r=proof;$allowed=$true}catch{}
if($allowed){throw 'cc07_armed_old_cycle_not_refused'}
$r=proof $true
if($r -cne 'ARMED'){throw 'cc07_pause_transitional_not_accepted'}
write-output 'cc07_native_transitional_pause_only=pass'

'''
    script = tmp_path / "cc07-native-proof-test.ps1"
    script.write_text(payload, encoding="utf-8-sig")
    environment = os.environ.copy()
    environment["cc07_source_file"] = str(PATH)
    completed = subprocess.run(
        ["powershell.exe", "-noprofile", "-noninteractive",
         "-executionpolicy", "bypass", "-file", str(script)],
        cwd=tmp_path, env=environment,
        capture_output=True, text=True, timeout=25, check=False
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    for case in ("expected_halted", "unexpected_nonzero",
                 "healthy_exit_but_halted", "stale_halted", "not_running"):
        assert "cc07_native_" + case + "=pass" in completed.stdout
