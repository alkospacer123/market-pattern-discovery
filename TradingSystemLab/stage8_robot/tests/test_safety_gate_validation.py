from TradingSystemLab.stage8_robot.safety_gate_validation import validate
def test_matrix(tmp_path):
    result=validate(workspace=tmp_path)
    assert (result["synthetic_case_count"],result["synthetic_open_case_count"],result["synthetic_blocked_case_count"])==(25,1,24)
    assert result["synthetic_matrix_validation"]==result["emergency_halt_validation"]=="PASS"
