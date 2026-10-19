"""Hosted-only fixture adapter; run the real, unchanged app in a real server.

Only policy location and UUID Task selection differ from an installed panel.
Identity, native file trust, gates, helper, conversion and UI remain real.
"""
import json
import os
from pathlib import Path
import sys
import time


def main():
    assert os.name == 'nt' and os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted'
    from observer.identity import current_identity
    from cc.providers import h1_windows_os as manual
    from streamlit.web import bootstrap
    root = Path(os.environ['CC03_CI_DISPOSABLE_ROOT'])
    sid, unsafe = current_identity()
    assert sid == sys.argv[1] and not unsafe
    location = json.loads((root / 'manual-policy-location.json').read_text())
    fixtures = json.loads((root / 'Os-Fixtures.json').read_text())
    manual.POLICY_ROOT = Path(location['root'])
    manual.POLICY_NAME = 'Running-manual-os-policy.json'
    output = root / 'data/logs/streamlit-click.json'
    result = dict(sid_standard=True, policy_reads=0, probes=0, clicks=0)

    def save():
        output.write_text(json.dumps(result), encoding='utf-8')

    original_read, original_facts = manual.read_windows, manual.os_facts
    original_refresh = manual.manual_os_refresh

    def read(*args, **kwargs):
        result['policy_reads'] += 1
        started = time.monotonic()
        try:
            return original_read(*args, **kwargs)
        except Exception as exc:
            # Test evidence also excludes exception text, paths and stacks.
            result['read_error_type'] = type(exc).__name__
            result['read_error_code'] = str(exc) if str(exc) in {
                'READ_TIMEOUT', 'SECURE_READ_UNAVAILABLE'} else 'UNCLASSIFIED'
            raise
        finally:
            result['read_seconds'] = round(time.monotonic() - started, 3)
            save()

    def facts(query):
        result['probes'] += 1
        assert query['require_ccpanel'] and query['observer_sid'] == sid
        save()
        return original_facts(dict(query, task_name=fixtures['Running']['task_name']))

    def refresh(now):
        result['clicks'] += 1
        snapshot, accepted = original_refresh(now)
        result.update(accepted=accepted, task=snapshot.status.task_state,
                      robot_state=snapshot.status.state.value,
                      heartbeat=snapshot.status.heartbeat_at,
                      trading=snapshot.status.trading_allowed)
        save()
        return snapshot, accepted

    manual.read_windows, manual.os_facts, manual.manual_os_refresh = read, facts, refresh
    save()
    bootstrap.run(str(Path(__file__).parents[1] / 'app.py'), False, [], {
        'server.address': '127.0.0.1', 'server.port': 8502,
        'server.headless': True, 'browser.gatherUsageStats': False,
        'server.enableCORS': True, 'server.enableXsrfProtection': True})


if __name__ == '__main__':
    main()
