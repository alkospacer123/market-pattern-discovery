"""CI-only native File Create ETW audit; never imported by the panel/observer.

Captures kernel file-create events, including native PowerShell child opens.
Missing positive controls or any lost events is a failure, never a skipped test.
"""
from contextlib import contextmanager
import ctypes
from ctypes import wintypes as w
import os
from pathlib import Path
import subprocess
import uuid
import xml.etree.ElementTree as ET


def command(args):
    result = subprocess.run(args, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, (args[0:3], result.stdout, result.stderr)
    return result.stdout


def stop_trace(name):
    # Obtain FINAL kernel counters when stopping, rather than assuming that a
    # nonempty trace or two positive controls implies loss-free coverage.
    class Wnode(ctypes.Structure):
        _fields_=[('BufferSize',w.DWORD),('ProviderId',w.DWORD),('HistoricalContext',ctypes.c_ulonglong),
                  ('TimeStamp',ctypes.c_longlong),('Guid',ctypes.c_byte*16),
                  ('ClientContext',w.DWORD),('Flags',w.DWORD)]
    class Properties(ctypes.Structure):
        _fields_=[('Wnode',Wnode),*[(key,w.DWORD) for key in (
            'BufferSize','MinimumBuffers','MaximumBuffers','MaximumFileSize','LogFileMode',
            'FlushTimer','EnableFlags','AgeLimit','NumberOfBuffers','FreeBuffers','EventsLost',
            'BuffersWritten','LogBuffersLost','RealTimeBuffersLost')],
            ('LoggerThreadId',w.HANDLE),('LogFileNameOffset',w.DWORD),('LoggerNameOffset',w.DWORD)]
    raw=ctypes.create_string_buffer(ctypes.sizeof(Properties)+4096)
    stats=Properties.from_buffer(raw)
    stats.Wnode.BufferSize=len(raw)
    stats.LoggerNameOffset=ctypes.sizeof(Properties)
    stats.LogFileNameOffset=ctypes.sizeof(Properties)+2048
    adv=ctypes.WinDLL('advapi32',use_last_error=True)
    adv.ControlTraceW.argtypes=[ctypes.c_ulonglong,w.LPCWSTR,w.LPVOID,w.ULONG]
    adv.ControlTraceW.restype=w.ULONG
    code=adv.ControlTraceW(0,name,raw,1)  # EVENT_TRACE_CONTROL_STOP
    assert code==0, ('ETW_STOP_FAILED',code)
    result={key:getattr(stats,key) for key in ('EventsLost','LogBuffersLost','RealTimeBuffersLost')}
    assert all(v==0 for v in result.values()), ('ETW_EVENTS_LOST',result)
    return result


@contextmanager
def file_create_trace(root):
    assert os.name == 'nt' and os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted'
    name = 'CC03-FileOpen-' + uuid.uuid4().hex
    trace = Path(root) / (name + '.etl')
    # Microsoft-Windows-Kernel-File: filename + create. No production provider,
    # registry, account or ACL configuration is modified; ephemeral ETW only.
    command(['logman.exe','start',name,'-ets','-o',str(trace),'-p',
             'Microsoft-Windows-Kernel-File','0x90','5','-bs','64','-nb','16','256'])
    records = []
    try:
        yield records
    finally:
        counters=stop_trace(name)
        xml = trace.with_suffix('.xml')
        summary = trace.with_suffix('.summary.txt')
        command(['tracerpt.exe',str(trace),'-o',str(xml),'-of','XML','-summary',str(summary),'-y'])
        # EventTrace header exposes EventsLost/BuffersLost on the native ETL.
        # tracerpt XML also includes raw unnamed UserData on older manifests.
        text = xml.read_text(encoding='utf-16') if xml.read_bytes().startswith(b'\xff\xfe') else xml.read_text(encoding='utf-8-sig')
        document = ET.fromstring(text)
        ns = {'e':'http://schemas.microsoft.com/win/2004/08/events/event'}
        for event in document.findall('.//e:Event',ns):
            system = event.find('e:System',ns)
            if system is None:continue
            provider = system.find('e:Provider',ns)
            if provider is None:continue
            values = {item.get('Name'): item.text for item in event.findall('.//e:Data',ns)}
            for key in ('EventsLost','BuffersLost'):
                if key in values:assert int(values[key],0)==0, 'ETW_EVENTS_LOST'
            execution = system.find('e:Execution',ns)
            records.append(dict(provider=provider.get('Name'),id=system.findtext('e:EventID',namespaces=ns),
                pid=int(execution.get('ProcessID','0')) if execution is not None else 0,
                values=values, xml=ET.tostring(event,encoding='unicode')))
        assert records, 'ETW_EMPTY_TRACE'
        # Keep a compact report; raw trace stays in disposable RUNNER_TEMP.
        report = Path(os.environ['RUNNER_TEMP']) / 'cc03-evidence' / 'file-create-trace-summary.txt'
        with report.open('a',encoding='utf-8') as out:
            out.write(name+'\n'+str(counters)+'\n'+summary.read_text(errors='replace')+'\n')


def events_for(records, path):
    # Device paths and drive-letter paths have the same unique fixture suffix.
    suffix = '\\' + Path(path).parent.name.casefold() + '\\' + Path(path).name.casefold()
    return [r for r in records if r['id']=='12' and suffix in r['xml'].casefold()]
