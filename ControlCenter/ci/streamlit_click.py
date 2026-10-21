"""Real Edge DOM click against a real standard-SID Streamlit server, hosted only.

Uses the existing Tornado dependency for local CDP. No driver download, network
service, runtime dependency or product capability is added.
"""
import asyncio
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
from tornado.websocket import websocket_connect


def state(evidence):
    complete = evidence.read_bytes().split(b'\n')[:-1]
    return json.loads(complete[-1]) if complete else {}


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
        await until("document.body.innerText.includes('Control Center')")
        assert state(evidence)['policy_reads'] == 0
        button = "Array.from(document.querySelectorAll('button')).find(e=>e.textContent==='Обновить данные')"
        await until(f"Boolean(({button}) && !({button}).disabled)")
        assert state(evidence)['policy_reads'] == 0
        await evaluate(f"({button}).click()")
        deadline = time.monotonic() + 20
        while 'accepted' not in state(evidence):
            assert time.monotonic() < deadline, 'MANUAL_CLICK_TIMEOUT'
            await asyncio.sleep(.1)
        value = state(evidence)
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
        await until("document.body.innerText.includes('Управление ещё не подключено')")
        await page('Журнал')
        await until("document.body.innerText.includes('Последние 10 циклов H1')")
        await page('Главная')
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
        value['disabled_trading_controls'] = 'NOT_PRESENT_IN_UI'
        value['rendered_task_running'] = True
        return value
    except BaseException:
        if socket is not None:
            try:
                failed = await call('Page.captureScreenshot', dict(format='png'))
                (evidence.parent / 'streamlit-click.png').write_bytes(base64.b64decode(failed['data']))
            except Exception:
                pass  # The original failure remains authoritative.
        raise
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
