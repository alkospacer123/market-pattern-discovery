"""Real Edge DOM click against a real standard-SID Streamlit server, hosted only.

Uses the existing Tornado dependency for local CDP. No driver download, network
service, runtime dependency or product capability is added.
"""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
from tornado.websocket import websocket_connect


async def browser_click(edge, profile, evidence):
    process = subprocess.Popen([str(edge), '--headless=new', '--no-first-run',
        '--no-default-browser-check', '--disable-background-networking',
        '--remote-debugging-port=0', '--remote-debugging-address=127.0.0.1',
        '--user-data-dir=' + str(profile), 'about:blank'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    socket = None
    try:
        deadline = time.monotonic() + 20
        active = profile / 'DevToolsActivePort'
        while not active.exists():
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
        assert json.loads(evidence.read_text())['policy_reads'] == 0
        await evaluate("document.querySelector('[data-testid=stSelectbox] [role=combobox]').click()")
        await until("Array.from(document.querySelectorAll('[role=option]')).some(e=>e.textContent==='WINDOWS_OS_ONLY')")
        await evaluate("Array.from(document.querySelectorAll('[role=option]')).find(e=>e.textContent==='WINDOWS_OS_ONLY').click()")
        button = "Array.from(document.querySelectorAll('button')).find(e=>e.textContent==='Обновить данные')"
        await until(f"Boolean(({button}) && !({button}).disabled)")
        assert json.loads(evidence.read_text())['policy_reads'] == 0
        await evaluate(f"({button}).click()")
        deadline = time.monotonic() + 20
        while 'accepted' not in json.loads(evidence.read_text()):
            assert time.monotonic() < deadline, 'MANUAL_CLICK_TIMEOUT'
            await asyncio.sleep(.1)
        value = json.loads(evidence.read_text())
        assert value['clicks'] == 1 and value['policy_reads'] == 1, value
        # First commit deliberately records the baseline failure; the regression
        # expectation is tightened to TASK_RUNNING after native reproduction.
        assert value['accepted'] is False and value['probes'] == 0, value
        await until("document.body.innerText.includes('BLOCKED / UNKNOWN')")
        value['real_browser_click'] = True
        return value
    finally:
        if socket is not None:
            socket.close()
        subprocess.run(['taskkill.exe', '/PID', str(process.pid), '/T', '/F'],
                       capture_output=True, timeout=10)
        process.wait(10)


def main(sid):
    assert os.name == 'nt' and os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted'
    root = Path(os.environ['CC03_CI_DISPOSABLE_ROOT'])
    logs = root / 'data/logs'
    edge = Path(os.environ['PROGRAMFILES(X86)']) / 'Microsoft/Edge/Application/msedge.exe'
    assert edge.is_file(), 'HOSTED_EDGE_REQUIRED'
    with (logs / 'streamlit-server.txt').open('w', encoding='utf-8') as log:
        server = subprocess.Popen([sys.executable, '-m', 'ci.streamlit_host', sid],
                                  stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 20
            evidence = logs / 'streamlit-click.json'
            while not evidence.exists():
                assert server.poll() is None and time.monotonic() < deadline, 'SERVER_START_TIMEOUT'
                time.sleep(.1)
            value = asyncio.run(browser_click(edge, logs / 'edge-profile', evidence))
            print('LOW_SID_REAL_STREAMLIT_CLICK=' + json.dumps(value), flush=True)
            (logs / 'streamlit-browser-result.json').write_text(json.dumps(value, indent=2))
        finally:
            subprocess.run(['taskkill.exe', '/PID', str(server.pid), '/T', '/F'],
                           capture_output=True, timeout=10)
            server.wait(10)


if __name__ == '__main__':
    main(sys.argv[1])
