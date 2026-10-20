"""Real Edge DOM click against a real standard-SID Streamlit server, hosted only.

Uses the existing Tornado dependency for local CDP. No driver download, network
service, runtime dependency or product capability is added.
"""
import asyncio
import base64
from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from threading import Thread
import urllib.request
from tornado.websocket import websocket_connect


def state(evidence):
    complete = evidence.read_bytes().split(b'\n')[:-1]
    return json.loads(complete[-1]) if complete else {}


@asynccontextmanager
async def cpu_load(logs):
    """Bounded fixture contention, never a delay or patch in the native reader."""
    count = min(8, max(1, os.cpu_count() or 1))
    children = []
    report = dict(logical_cpu=os.cpu_count(), workers=count, maximum_seconds=45)
    code = ('import sys,time; print("READY",flush=True); sys.stdin.buffer.read(1); '
            'deadline=time.monotonic()+45; value=1; print("RUNNING",flush=True)\n'
            'while time.monotonic()<deadline: value=(value*17+11)%2147483647\n')
    try:
        for _ in range(count):
            child = await asyncio.create_subprocess_exec(sys.executable, '-I', '-B', '-c', code,
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL)
            children.append(child)
        for child in children:
            assert (await asyncio.wait_for(child.stdout.readline(), 10)).strip() == b'READY'
        for child in children:
            child.stdin.write(b'X')
            await child.stdin.drain()
            child.stdin.close()
        for child in children:
            assert (await asyncio.wait_for(child.stdout.readline(), 10)).strip() == b'RUNNING'
        report['all_workers_started'] = True
        yield report, children
    finally:
        for child in children:
            if child.returncode is None:
                child.terminate()
        for child in children:
            await asyncio.wait_for(child.wait(), 10)
        report['all_children_exited'] = all(child.returncode is not None for child in children)
        (logs / 'streamlit-cpu-load.json').write_text(json.dumps(report, indent=2), encoding='utf-8')


def load_controls(sid):
    """Real standard-SID direct/threaded controls under the SAME live CPU load."""
    from cc.providers import h1_windows_os as manual
    from observer.identity import current_identity
    from datetime import datetime, timezone
    actual, unsafe = current_identity()
    assert actual == sid and not unsafe
    root = Path(os.environ['CC03_CI_DISPOSABLE_ROOT'])
    fixtures = json.loads((root / 'Os-Fixtures.json').read_text())
    location = json.loads((root / 'manual-policy-location.json').read_text())
    saved = manual.POLICY_ROOT, manual.POLICY_NAME, manual.os_facts, manual.read_windows
    original = manual.os_facts
    original_read = manual.read_windows
    timing = {}
    def read(*args, **kwargs):
        started = time.monotonic()
        try:
            return original_read(*args, **kwargs)
        except Exception as exc:
            timing['read_error_code'] = str(exc) if str(exc) in {
                'READ_TIMEOUT', 'READ_WORKER_UNAVAILABLE', 'SECURE_READ_UNAVAILABLE'} else 'UNCLASSIFIED'
            raise
        finally:
            timing['read_seconds'] = round(time.monotonic() - started, 3)
    manual.read_windows = read
    manual.POLICY_ROOT, manual.POLICY_NAME = Path(location['root']), 'Running-manual-os-policy.json'
    def facts(query):
        assert query['require_ccpanel'] and query['observer_sid'] == sid
        return original(dict(query, task_name=fixtures['Running']['task_name']))
    manual.os_facts = facts
    results = {}
    try:
        for mode in ('direct', 'threaded'):
            timing.clear()
            completed = []
            started = time.monotonic()
            def refresh():
                completed.append(manual.manual_os_refresh(datetime.now(timezone.utc)))
            if mode == 'threaded':
                thread = Thread(target=refresh)
                thread.start(); thread.join(12)
                assert not thread.is_alive(), 'LOAD_CONTROL_THREAD_TIMEOUT'
            else:
                refresh()
            assert len(completed) == 1
            snapshot, accepted = completed[0]
            reason = snapshot.events[0].message if not accepted else 'NONE'
            assert reason in {'NONE', 'MANUAL_REFRESH_REQUIRED', 'MANUAL_REFRESH_BUSY',
                *('MANUAL_REFRESH_BLOCKED_' + stage for stage in (
                    'GATE', 'POLICY_READ', 'POLICY_VALIDATE', 'IDENTITY', 'OS_PROBE', 'OS_VALIDATE', 'SOURCE'))}
            results[mode] = dict(accepted=accepted, task=snapshot.status.task_state, reason=reason,
                                 seconds=round(time.monotonic() - started, 3), **timing)
            (root / 'data/logs/streamlit-load-controls.json').write_text(
                json.dumps(results, indent=2), encoding='utf-8')
            assert accepted and snapshot.status.task_state == 'TASK_RUNNING', results
        return results
    finally:
        manual.POLICY_ROOT, manual.POLICY_NAME, manual.os_facts, manual.read_windows = saved


async def browser_click(edge, profile, evidence):
    with (evidence.parent / 'edge-stderr.txt').open('w', encoding='utf-8') as log:
        return await _browser_click(edge, profile, evidence, log)


async def _browser_click(edge, profile, evidence, log):
    process = subprocess.Popen([str(edge), '--headless=new', '--no-first-run',
        '--no-default-browser-check', '--disable-background-networking',
        '--remote-debugging-port=0', '--remote-debugging-address=127.0.0.1',
        '--user-data-dir=' + str(profile), 'about:blank'],
        stdout=log, stderr=subprocess.STDOUT)
    socket = None
    try:
        deadline = time.monotonic() + 20
        active = profile / 'DevToolsActivePort'
        while not active.exists():
            assert process.poll() is None, ('EDGE_EXITED', process.poll())
            assert time.monotonic() < deadline, 'EDGE_START_TIMEOUT'
            await asyncio.sleep(.1)
        port = int(active.read_text().splitlines()[0])
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f'http://127.0.0.1:{port}/json/list', timeout=5) as response:
            targets = json.load(response)
        target = next(t for t in targets if t['type'] == 'page')
        socket = await websocket_connect(target['webSocketDebuggerUrl'], connect_timeout=5)
        serial = 0

        async def call(method, params):
            nonlocal serial
            serial += 1
            await socket.write_message(json.dumps(dict(id=serial, method=method, params=params)))
            while True:
                message = json.loads(await asyncio.wait_for(socket.read_message(), 15))
                if message.get('id') == serial:
                    assert 'error' not in message, message
                    return message['result']

        async def evaluate(expression):
            value = await call('Runtime.evaluate', dict(expression=expression, returnByValue=True))
            assert 'exceptionDetails' not in value, value
            return value['result'].get('value')

        async def until(expression, timeout=20):
            deadline = time.monotonic() + timeout
            while not await evaluate(expression):
                assert time.monotonic() < deadline, 'DOM_WAIT_TIMEOUT: ' + expression
                await asyncio.sleep(.1)

        await call('Page.navigate', dict(url='http://127.0.0.1:8502'))
        await until("document.querySelectorAll('[data-testid=stSelectbox]').length >= 1")
        assert state(evidence)['policy_reads'] == 0
        await evaluate("document.querySelector('[data-testid=stSelectbox] [role=combobox]').click()")
        await until("Array.from(document.querySelectorAll('[role=option]')).some(e=>e.textContent==='WINDOWS_OS_ONLY')")
        await evaluate("Array.from(document.querySelectorAll('[role=option]')).find(e=>e.textContent==='WINDOWS_OS_ONLY').click()")
        button = "Array.from(document.querySelectorAll('button')).find(e=>e.textContent==='Обновить данные')"
        await until(f"Boolean(({button}) && !({button}).disabled)")
        assert state(evidence)['policy_reads'] == 0
        async with cpu_load(evidence.parent) as (load, children):
            # The coordinator uses the actual standard token and original full
            # manual wrapper. Only this browser click runs beneath Streamlit.
            (evidence.parent / 'streamlit-load.ready').write_text('ready', encoding='ascii')
            deadline = time.monotonic() + 30
            while not (evidence.parent / 'streamlit-load.done').exists():
                assert time.monotonic() < deadline, 'LOAD_CONTROLS_TIMEOUT'
                await asyncio.sleep(.1)
            controls = json.loads((evidence.parent / 'streamlit-load-controls.json').read_text())
            assert all(controls[k]['accepted'] and controls[k]['task'] == 'TASK_RUNNING'
                       for k in ('direct', 'threaded')), controls
            assert all(child.returncode is None for child in children), 'CPU_LOAD_ENDED_BEFORE_CLICK'
            await evaluate(f"({button}).click()")
            deadline = time.monotonic() + 20
            while 'accepted' not in state(evidence):
                assert time.monotonic() < deadline, 'MANUAL_CLICK_TIMEOUT'
                await asyncio.sleep(.1)
            value = state(evidence)
            assert all(child.returncode is None for child in children), 'CPU_LOAD_ENDED_DURING_CLICK'
        value['synthetic_cpu_load'] = load
        value['load_controls'] = controls
        assert value['clicks'] == 1 and value['policy_reads'] == 1, value
        assert value['accepted'] is True and value['probes'] == 1, value
        assert value['task'] == 'TASK_RUNNING' and value['robot_state'] == 'UNKNOWN', value
        assert value['source_kind'] == 'WINDOWS_OS_ONLY', value
        assert value['heartbeat'] is None and value['trading'] is None, value
        assert value['streamlit_main'] is True, value
        assert value['server_isolated'] is True and value['server_no_bytecode'] is True, value
        async def page(name):
            await evaluate("Array.from(document.querySelectorAll('[data-testid=stRadio] label'))"
                           ".find(e=>e.textContent.includes(" + json.dumps(name) + ")).click()")
        await page('Управление')
        await until("document.querySelectorAll('[data-testid=stButton] button:disabled').length === 10")
        await page('Монитор H1')
        task = ("Array.from(document.querySelectorAll('[data-testid=stMarkdownContainer]'))"
                ".find(e=>e.innerText.replace(/\\s+/g,' ').includes('Windows Task: TASK_RUNNING'))")
        await until(f"Boolean({task})")
        await evaluate(f"({task}).scrollIntoView({{block:'center'}})")
        assert not await evaluate("document.body.innerText.includes('BLOCKED / UNKNOWN')")
        assert state(evidence)['policy_reads'] == 1
        assert state(evidence)['probes'] == 1
        screenshot = await call('Page.captureScreenshot', dict(format='png'))
        (evidence.parent / 'streamlit-click.png').write_bytes(base64.b64decode(screenshot['data']))
        value['real_browser_click'] = True
        value['navigation_zero_extra_reads'] = True
        value['disabled_trading_controls'] = 10
        value['rendered_task_running'] = True
        return value
    finally:
        if socket is not None:
            socket.close()
        subprocess.run(['taskkill.exe', '/PID', str(process.pid), '/T', '/F'],
                       capture_output=True, timeout=10)
        process.wait(10)


def main(sid):
    """Server side: remains on the actual standard ccpanel primary token."""
    assert os.name == 'nt' and os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted'
    root = Path(os.environ['CC03_CI_DISPOSABLE_ROOT'])
    logs = root / 'data/logs'
    done = logs / 'streamlit-browser.done'
    result = logs / 'streamlit-browser-result.json'
    if done.exists():
        assert json.loads(result.read_text())['real_browser_click'] is True
        return  # The second existing lifecycle probe must not click again.
    with (logs / 'streamlit-server.txt').open('w', encoding='utf-8') as log:
        # Match Start-Panel.ps1's -I -B interpreter flags. This trusted bootstrap
        # only imports the fixed CI fixture adapter before real Streamlit runs.
        bootstrap = ('import sys; sys.path.insert(0,sys.argv[1]); '
                     'from ci.streamlit_host import main; main(sys.argv[2])')
        server = subprocess.Popen([sys.executable, '-I', '-B', '-c', bootstrap,
                                   str(Path(__file__).parents[1]), sid],
                                  stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 100
            while not done.exists():
                assert server.poll() is None and time.monotonic() < deadline, 'BROWSER_COORDINATOR_TIMEOUT'
                if ((logs / 'streamlit-load.ready').exists()
                        and not (logs / 'streamlit-load.done').exists()):
                    try:
                        controls = load_controls(sid)
                    except Exception:
                        if not (logs / 'streamlit-load-controls.json').exists():
                            (logs / 'streamlit-load-controls.json').write_text('{}', encoding='utf-8')
                        raise
                    else:
                        (logs / 'streamlit-load-controls.json').write_text(json.dumps(controls), encoding='utf-8')
                    finally:
                        (logs / 'streamlit-load.done').write_text('done', encoding='ascii')
                time.sleep(.1)
            value = json.loads(result.read_text())
            assert value.get('real_browser_click') is True, value
            print('LOW_SID_REAL_STREAMLIT_CLICK=' + json.dumps(value), flush=True)
        finally:
            subprocess.run(['taskkill.exe', '/PID', str(server.pid), '/T', '/F'],
                           capture_output=True, timeout=10)
            server.wait(10)


def drive():
    """Runner-side browser; server/reader/helper continue under standard ccpanel."""
    assert os.name == 'nt' and os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted'
    logs = Path(os.environ['CC03_CI_DISPOSABLE_ROOT']) / 'data/logs'
    evidence = logs / 'streamlit-click.jsonl'
    edge = Path(os.environ['PROGRAMFILES(X86)']) / 'Microsoft/Edge/Application/msedge.exe'
    assert edge.is_file(), 'HOSTED_EDGE_REQUIRED'
    deadline = time.monotonic() + 90
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        while True:
            try:
                if evidence.exists() and state(evidence):
                    with opener.open('http://127.0.0.1:8502/_stcore/health', timeout=1) as response:
                        if response.read() == b'ok':
                            break
            except OSError:
                pass
            assert time.monotonic() < deadline, 'SERVER_HEALTH_TIMEOUT'
            time.sleep(.1)
        value = asyncio.run(browser_click(edge, logs / 'edge-profile', evidence))
        (logs / 'streamlit-browser-result.json').write_text(json.dumps(value, indent=2), encoding='utf-8')
    except BaseException:
        (logs / 'streamlit-browser-result.json').write_text('{"real_browser_click":false}', encoding='utf-8')
        raise
    finally:
        (logs / 'streamlit-browser.done').write_text('done', encoding='ascii')


if __name__ == '__main__':
    assert sys.argv[1:] == ['--browser-only']
    drive()
