"""Verify the checked-in blocker packet; no network, no replay, no mutations."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    seal = json.loads((HERE / 'reproducibility.json').read_text())
    for name, expected in seal['packet_sha256'].items():
        path = HERE / name
        if path.parent != HERE or not path.is_file():
            raise RuntimeError('INVALID_PACKET_PATH: ' + name)
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError('PACKET_HASH_MISMATCH: ' + name)
    expected_names = set(seal['packet_sha256']) | {'reproducibility.json'}
    actual_names = {p.name for p in HERE.iterdir() if p.is_file()}
    if actual_names != expected_names:
        raise RuntimeError('PACKET_FILE_SET_CHANGED')
    summary = json.loads((HERE / 'summary.json').read_text())
    assert summary['overall_status'] == 'SOURCE_DATA_BLOCKED_M15'
    assert summary['COMPUTATIONAL_AUDIT'] == 'NOT_RUN'
    assert summary['gross_R'] is None
    assert not list(HERE.glob('*.csv'))
    assert seal['full_strategy_replay_runs'] == 0
    print('PASS: blocker packet hashes/statuses; historical strategy audit NOT_RUN')


if __name__ == '__main__':
    main()
